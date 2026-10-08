"""Step 5: BV built-surface-weighted GHSL height on land, BI (descriptive), and height validation in both cities."""
import glob, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, rasterio, shapely
from rasterio.windows import Window, from_bounds
import evaluate_b1_step4 as b1

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/bv_step5_2026_10_05"
PROD = str(ROOT / "analysis/data/{c}/ghsl_public_2026_09_21/GHS_BUILT_{p}_E{y}_GLOBE_R2023A_54009_100.tif")
# Rules fixed by the user on 5 October 2026 before this run (MODEL_PLAN Step 5).
MIN_SPEARMAN = 0.80
FT = 0.3048006            # Cook `Height` is in US survey feet
CLASSES = [0, 8, 15, 25, 1e9]
checks = {}


def wq(x, w, q):
    i = np.argsort(x); x, w = x[i], w[i]; c = np.cumsum(w)
    return float(np.interp(q * c[-1], c, x))


def ghsl(city, units):
    """Per unit on land: built-surface-weighted height, built fraction, volume per land m², built-weighted P90.
    Same cell arithmetic as evaluate_bv_built_form_2026_09_30.ghsl_cells (copied: that module runs on import), on land support."""
    rows = []
    folder = "Chicago" if city == "CHI" else "SP"
    with rasterio.open(PROD.format(c=folder, p="H_ANBH", y=2018)) as a, rasterio.open(PROD.format(c=folder, p="H_AGBH", y=2018)) as g, \
         rasterio.open(PROD.format(c=folder, p="V", y=2020)) as v:
        u = units.to_crs(a.crs)
        cell_area = abs(a.res[0] * a.res[1])
        for r in u.itertuples():
            raw = from_bounds(*r.geometry.bounds, transform=a.transform)
            win = Window(int(np.floor(raw.col_off)), int(np.floor(raw.row_off)), int(np.ceil(raw.width)) + 1,
                         int(np.ceil(raw.height)) + 1).intersection(Window(0, 0, a.width, a.height))
            An, Ag, V = (x.read(1, window=win, masked=True) for x in (a, g, v))
            tr = a.window_transform(win)
            rr, cc = np.indices(An.shape)
            x0, y1 = tr * (cc, rr); x1, y0 = tr * (cc + 1, rr + 1)
            boxes = shapely.box(x0.ravel(), np.minimum(y0, y1).ravel(), x1.ravel(), np.maximum(y0, y1).ravel())
            ov = shapely.area(shapely.intersection(boxes, r.geometry)).reshape(An.shape)
            ok = ~np.ma.getmaskarray(An) & ~np.ma.getmaskarray(Ag) & ~np.ma.getmaskarray(V) & (ov > 0)
            w, an, ag, vol = ov[ok], An.data[ok].astype(float), Ag.data[ok].astype(float), V.data[ok].astype(float)
            frac = np.where(an > 0, ag / np.where(an > 0, an, 1), 0.0)
            bw = w * frac
            rows.append({"unit_id": r.unit_id, "valid_fraction": float(w.sum() / ov.sum()),
                         "bv_height_built_m": float((w * ag).sum() / bw.sum()) if bw.sum() > 0 else np.nan,
                         "bv_p90_built_m": wq(an[bw > 0], bw[bw > 0], .9) if bw.sum() > 0 else np.nan,
                         "ghsl_built_fraction": float(bw.sum() / w.sum()),
                         "bi_volume_per_land_m": float((w * vol / cell_area).sum() / w.sum()),
                         "bv_frozen_incl_empty_m": float((w * an).sum() / w.sum())})
    return pd.DataFrame(rows)


def ref_height(units, pts, label):
    """Footprint-area-weighted building height per unit, buildings assigned by centroid."""
    j = gpd.sjoin(pts, units, predicate="within")
    s = j.groupby("unit_id").apply(lambda x: (x.h * x.a).sum() / x.a.sum(), include_groups=False).rename(label)
    n = j.groupby("unit_id").size().rename(label + "_n")
    return pd.concat([s, n], axis=1)


def chicago_ref(units):
    parts = []
    for f in sorted(glob.glob(str(D / "Chicago/chicago_cadastral_2026_09_18/cook_buildings_2022/part_*.parquet"))):
        g = gpd.read_parquet(f, columns=["geometry", "Height"]).to_crs(26916)
        g = g[g.Height > 0]
        parts.append(gpd.GeoDataFrame({"h": g.Height * FT, "a": g.geometry.area}, geometry=g.geometry.centroid, crs=26916))
    return ref_height(units, pd.concat(parts, ignore_index=True), "cook2022_lidar_height_m")


def sp_refs(units):
    parts = []
    for f in sorted(glob.glob(str(D / "SP/geosampa_edificacao_2026_10_05/page_*.zip"))):
        g = gpd.read_file(f"zip://{f}", columns=["qt_altura_"])
        g = (g.set_crs(31983, allow_override=True) if g.crs is None else g.to_crs(31983))
        g = g[g.qt_altura_ > 0]
        parts.append(gpd.GeoDataFrame({"h": g.qt_altura_, "a": g.geometry.area}, geometry=g.geometry.centroid, crs=31983))
    gs = ref_height(units, pd.concat(parts, ignore_index=True), "geosampa_height_m")
    f, step, parts = D / "SP/Edificacoes/sao_paulo_building_morphology.gpkg", 500_000, []
    total = pyogrio.read_info(f, layer="buildings")["features"]
    for start in range(0, total, step):     # chunked: the full file exhausts memory
        ch = pyogrio.read_dataframe(f, layer="buildings", columns=["height_m"], skip_features=start, max_features=step)
        ch = ch[ch.height_m > 0]
        parts.append(gpd.GeoDataFrame({"h": ch.height_m, "a": ch.geometry.area}, geometry=ch.geometry.centroid, crs=ch.crs))
    osm = ref_height(units, pd.concat(parts, ignore_index=True), "overture_osm_height_m")
    return gs.join(osm, how="outer")


def bias(t, ref):
    """GHSL ÷ reference height by reference height class (units binned by the reference)."""
    k = pd.cut(t[ref], CLASSES, right=False, labels=["<8 m", "8-15 m", "15-25 m", ">=25 m"])
    r = t.bv_height_built_m / t[ref]
    return r.groupby(k, observed=True).agg(["size", "median"]).round(3).to_dict(orient="index")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = []
    for city in ("CHI", "SP"):
        u = b1.land_units(city)
        t = ghsl(city, u).set_index("unit_id")
        t = t.join(chicago_ref(u) if city == "CHI" else sp_refs(u))
        t.insert(0, "city", city)
        out.append(t)
        print(city, "done", flush=True)
    t = pd.concat(out)
    t.to_csv(OUT / "bv_step5_by_unit.csv")
    old = pd.read_csv(A / "results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/tables/bv_variants_with_b1.csv").set_index("unit_id")
    cand = pd.read_csv(b1.CAND).set_index("unit_id")
    checks["no_missing_bv"] = {"pass": bool(t.bv_height_built_m.notna().all()), "missing": t.index[t.bv_height_built_m.isna()].tolist()}
    for city, ref, key in [("CHI", "cook2022_lidar_height_m", "S5-5_CHI_vs_cook2022_lidar"), ("SP", "geosampa_height_m", "S5-6_SP_vs_geosampa")]:
        c = t[t.city == city]
        rho = c.bv_height_built_m.corr(c[ref], method="spearman")
        checks[key] = {"pass": bool(rho >= MIN_SPEARMAN), "spearman": float(rho), "units_with_reference": int(c[ref].notna().sum()),
                       "median_ratio_ghsl_over_ref": float((c.bv_height_built_m / c[ref]).median())}
        checks[f"S5-7_{city}_bias_by_height_class"] = bias(c, ref)
        checks[f"{city}_descriptive"] = {
            "spearman_bv_vs_B1": float(c.bv_height_built_m.corr(cand.B1_coverage_land.reindex(c.index), method="spearman")),
            "spearman_frozen_bv_vs_B1": float(c.bv_frozen_incl_empty_m.corr(cand.B1_coverage_land.reindex(c.index), method="spearman")),
            "spearman_bi_vs_B1": float(c.bi_volume_per_land_m.corr(cand.B1_coverage_land.reindex(c.index), method="spearman")),
            "spearman_bi_vs_bv": float(c.bi_volume_per_land_m.corr(c.bv_height_built_m, method="spearman")),
            "spearman_bi_vs_bv_x_builtfraction": float(c.bi_volume_per_land_m.corr(c.bv_height_built_m * c.ghsl_built_fraction, method="spearman")),
            "spearman_land_vs_gross_support": float(c.bv_height_built_m.corr(old.height_built_weighted.reindex(c.index), method="spearman")),
            "median_bv_m": float(c.bv_height_built_m.median()),
            "max": [c.bv_height_built_m.idxmax(), float(c.bv_height_built_m.max())], "min": [c.bv_height_built_m.idxmin(), float(c.bv_height_built_m.min())]}
        if city == "SP":
            checks["SP_descriptive"]["spearman_vs_overture_osm_height"] = float(c.bv_height_built_m.corr(c.overture_osm_height_m, method="spearman"))
            checks["SP_descriptive"]["spearman_geosampa_vs_osm_height"] = float(c.geosampa_height_m.corr(c.overture_osm_height_m, method="spearman"))
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()
