"""Evaluate Chicago M7 as distinct ground tax-map pieces: type profile, overlap, per-area candidates, redundancy and 2008-2024 assembly."""
import glob, hashlib, io, json, sys, time
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, requests, shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "analysis/data/Chicago/chicago_cadastral_2026_09_18/"
OUT = ROOT / "analysis/results/Chicago/chicago_m7_ground_pieces_2026_09_30"
WORK = ROOT / "analysis/work/chicago_m7_2026_09_30"
TAB = OUT / "tables"
HIST = "https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/8/query"  # Parcels 2008
CODES = {"BaseParcel": 1, "ElevatedParcel": 2, "CondominiumParcel": 3, "NoPIN": 4, "ElevatedCondo": 5,
         "Leasehold": 6, "ElevatedLeasehold": 7, "ROWOverlap": 8, "CondominiumLeashold": 9}
ELEV = {2, 5, 7}
THR = 0.9          # primary collapse: overlap >= 90% of the smaller feature
SAMPLE_UNITS = (32, 8, 6, 15, 57, 28, 49)  # contrasting areas for the 2008 comparison
checks = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pieces(g, thr=THR, drop=ELEV):
    """Collapse overlapping ground features (elevated layers dropped) to one dissolved geometry per piece."""
    g = g[~g.code.isin(drop)].reset_index(drop=True)
    g["geometry"] = shapely.make_valid(g.geometry.values)
    i, j = g.sindex.query(g.geometry, predicate="intersects")
    m = i < j; i, j = i[m], j[m]
    ov = shapely.area(shapely.intersection(g.geometry.values[i], g.geometry.values[j]))
    a = g.geometry.area.values
    k = (ov > 1.0) & (ov / np.minimum(a[i], a[j]) >= thr)
    _, lab = connected_components(coo_matrix((np.ones(k.sum()), (i[k], j[k])), shape=(len(g), len(g))), directed=False)
    g["lab"] = lab
    d = g.dissolve("lab"); d["geometry"] = shapely.make_valid(d.geometry.values)
    return d[["geometry"]], lab


def rank_r2(df, y, xs):
    Z = df[xs + [y]].rank(); A = np.c_[np.ones(len(Z)), Z[xs].values]
    b = np.linalg.lstsq(A, Z[y].values, rcond=None)[0]
    return 1 - (Z[y].values - A @ b).var() / Z[y].var()


def main():
    TAB.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    ca = gpd.read_file(ROOT / "analysis/data/Chicago/Boundaries_-_Community_Areas_20260831.geojson").to_crs(26916)
    ca["unit"] = "CHI:" + ca.area_numbe.astype(int).astype(str).str.zfill(2); ca["km2"] = ca.area / 1e6
    assert len(ca) == 77

    # 1. Cook 2024 layer profile
    g = pd.concat([gpd.read_parquet(f) for f in sorted(glob.glob(str(D / "cook_parcels_2024/*.parquet")))], ignore_index=True)
    assert g.crs.to_epsg() == 26916 and len(g) == 613802
    g["type"] = g.PARCELTYPE.fillna("<null>"); g["code"] = g.PARCELTYPE.map(CODES).fillna(0).astype(int); g["a"] = g.geometry.area
    prof = g.groupby("type").a.agg(rows="size", area_km2=lambda s: s.sum() / 1e6, median_m2="median")
    prof.to_csv(TAB / "parcel_type_profile.csv")
    checks["rows_613802"] = True; checks["pin14_unique"] = int(g.Name.nunique()); checks["pin10_unique"] = int(g.PIN10.nunique())

    # 2. Overlaps by type pair (> 1 m2)
    gv = g.copy(); gv["geometry"] = shapely.make_valid(gv.geometry.values)
    i, j = gv.sindex.query(gv.geometry, predicate="intersects"); m = i < j; i, j = i[m], j[m]
    ov = shapely.area(shapely.intersection(gv.geometry.values[i], gv.geometry.values[j])); k = ov > 1.0
    pr = pd.DataFrame({"ov": ov[k], "share_small": ov[k] / np.minimum(g.a.values[i[k]], g.a.values[j[k]]),
                       "pair": [" | ".join(sorted(x)) for x in zip(g.type.values[i[k]], g.type.values[j[k]])]})
    pr.groupby("pair").agg(pairs=("ov", "size"), overlap_km2=("ov", lambda s: s.sum() / 1e6),
                           median_share_of_smaller=("share_small", "median")).sort_values("pairs", ascending=False).to_csv(TAB / "overlap_by_type_pair.csv")
    del gv

    # 3. Ground pieces: variants
    rows = []
    for name, drop, thr in [("all rows", set(), None), ("no Elevated*, 0.99", ELEV, .99), ("no Elevated*, 0.90 (primary)", ELEV, .90),
                            ("no Elevated*, 0.50", ELEV, .50), ("Base+Condo only, 0.90", set(range(10)) - {1, 3}, .90)]:
        if thr is None: rows.append(dict(variant=name, features=len(g), pieces=len(g))); continue
        p, _ = pieces(g.copy(), thr, drop); rows.append(dict(variant=name, features=int((~g.code.isin(drop)).sum()), pieces=len(p)))
    pd.DataFrame(rows).to_csv(TAB / "ground_piece_variants.csv", index=False)

    # 4. Per-area candidates (primary variant)
    p24, _ = pieces(g.copy())
    p24["a"] = p24.geometry.area; ground_union = shapely.union_all(p24.geometry.values)
    pt = gpd.GeoDataFrame({"a": p24.a.values}, geometry=p24.representative_point().values, crs=26916)
    pt = gpd.sjoin(pt, ca[["unit", "geometry"]], predicate="within")
    checks["pieces_total"] = int(len(p24)); checks["pieces_assigned"] = int(len(pt)); assert len(pt) == len(p24)
    agg = pt.groupby("unit").a.agg(pieces="size", log_area_median=lambda s: np.log(s).median(),
                                   log_area_iqr=lambda s: np.log(s).quantile(.75) - np.log(s).quantile(.25))
    u = pd.concat([pd.read_parquet(f, columns=["pin", "chicago_community_area_num"]) for f in glob.glob(str(D / "cook_universe_2024/*.parquet"))])
    cnum = pd.to_numeric(u.chicago_community_area_num, errors="coerce")
    checks["universe_pins"] = int(u.pin.nunique()); checks["universe_pins_without_area"] = int(u.pin[cnum.isna()].nunique())
    pins = u.groupby(cnum.astype("Int64")).pin.nunique(); pins.index = "CHI:" + pins.index.astype(str).str.zfill(2)
    cov = gpd.overlay(ca[["unit", "geometry"]], gpd.GeoDataFrame(geometry=[ground_union], crs=26916).explode(index_parts=False), how="intersection", keep_geom_type=True)
    cov = cov.dissolve("unit").area
    t = ca.set_index("unit")[["community", "km2"]].join(agg).join(pins.rename("pins")).join(cov.rename("parcel_m2")).fillna(0)
    t["pieces_km2"] = t.pieces / t.km2; t["pins_km2"] = t.pins / t.km2; t["pins_per_piece"] = t.pins / t.pieces
    t["parcelled_share"] = t.parcel_m2 / 1e6 / t.km2; t = t.drop(columns="parcel_m2"); t.to_csv(TAB / "community_area_m7_candidates.csv")

    # 5. Redundancy: Chicago and SP
    c = pd.read_csv(ROOT / "analysis/results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv", index_col=0)
    f = pd.read_csv(ROOT / "analysis/results/Chicago/chi_functional_2026_09_16_v2/tables/attributes_wide.csv", index_col=0)
    X = t[["pieces_km2", "pins_km2", "log_area_median", "log_area_iqr", "parcelled_share"]].join(
        c[["street_density_municipal_km_km2", "building_coverage_municipal_gross", "block_log_area_median_experimental"]]).join(
        f[["population_density_2020_gross_km2", "jobs_density_2022_gross_km2"]])
    R = X.corr(method="spearman").round(3); R.to_csv(TAB / "redundancy_chicago_spearman.csv")
    base = ["street_density_municipal_km_km2", "building_coverage_municipal_gross", "population_density_2020_gross_km2"]
    red = [dict(city="Chicago", target=y, predictors="M1,B1,U3", r2_rank=rank_r2(X, y, base)) for y in ("pieces_km2", "log_area_median", "log_area_iqr")]
    red += [dict(city="Chicago", target=y, predictors="M1,B1,U3,M3(experimental)", r2_rank=rank_r2(X, y, base + ["block_log_area_median_experimental"])) for y in ("pieces_km2", "log_area_median")]
    w = pd.read_csv(ROOT / "analysis/results/SP/tables/attributes_wide.csv", index_col=0)
    sb = ["street_density_km_km2", "building_coverage_gross", "population_density_km2"]
    red += [dict(city="SP", target=y, predictors="M1,B1,U3", r2_rank=rank_r2(w, y, sb)) for y in ("cadastral_parcel_density_km2", "parcel_log_area_median", "parcel_log_area_iqr")]
    pd.DataFrame(red).round(3).to_csv(TAB / "redundancy_r2.csv", index=False)
    sp_sp = w[sb + ["cadastral_parcel_density_km2", "parcel_log_area_median", "parcel_log_area_iqr"]].corr(method="spearman").round(3)
    sp_sp.to_csv(TAB / "redundancy_sp_spearman.csv")

    # 6. 2008 vs 2024 assembly in sample areas
    receipts, arows = [], []
    for un in SAMPLE_UNITS:
        poly = ca[ca.unit == f"CHI:{un:02d}"].geometry.iloc[0]; cache = WORK / f"hist_8_{un:02d}.parquet"
        if not cache.exists():
            b = gpd.GeoSeries([poly], crs=26916).to_crs(4326).total_bounds
            ids = requests.post(HIST, data=dict(where="1=1", geometry=",".join(map(str, b)), geometryType="esriGeometryEnvelope", inSR=4326,
                                                spatialRel="esriSpatialRelIntersects", returnIdsOnly="true", f="json"), timeout=120).json()["objectIds"] or []
            parts = []
            for s in range(0, len(ids), 500):
                r = requests.post(HIST, data=dict(objectIds=",".join(map(str, ids[s:s + 500])), outFields="OBJECTID,PIN14,PIN10,PARCELTYPE,JOB_NO", outSR=26916, f="geojson"), timeout=180)
                parts.append(gpd.read_file(io.BytesIO(r.content))); time.sleep(.2)
            h = pd.concat(parts, ignore_index=True).set_crs(26916, allow_override=True); h.to_parquet(cache)
        h = gpd.read_parquet(cache); receipts.append(dict(unit=un, features_bbox=len(h), sha256=sha(cache), url=HIST))
        h["code"] = h.PARCELTYPE.fillna(0).astype(int); h = h[h.representative_point().within(poly)]
        x = g[g.representative_point().within(poly)]
        a8, _ = pieces(h.copy()); a24, _ = pieces(x.copy()); r8, r24 = a8.representative_point(), a24.representative_point()
        j = gpd.sjoin(gpd.GeoDataFrame(geometry=r8, crs=26916), a24.reset_index(names="k"), predicate="within").groupby("k").size()
        j2 = gpd.sjoin(gpd.GeoDataFrame(geometry=r24, crs=26916), a8.reset_index(names="k"), predicate="within").groupby("k").size()
        arows.append(dict(unit=f"CHI:{un:02d}", pieces_2008=len(a8), pieces_2024=len(a24), pct_change=100 * (len(a24) / len(a8) - 1),
                          merged_2024_pieces=int((j >= 2).sum()), old_pieces_absorbed=int(j[j >= 2].sum()), pct_2024_merged=100 * (j >= 2).sum() / len(a24),
                          split_2008_pieces=int((j2 >= 2).sum()), new_pieces_from_splits=int(j2[j2 >= 2].sum())))
    pd.DataFrame(arows).round(2).to_csv(TAB / "assembly_2008_2024.csv", index=False)
    (OUT / "hist_receipts.json").write_text(json.dumps(receipts, indent=1))

    checks["output_sha256"] = {p.name: sha(p) for p in sorted(TAB.glob("*.csv"))}
    (OUT / "validation.json").write_text(json.dumps(checks, indent=1, default=str))
    print(json.dumps({k: v for k, v in checks.items() if k != "output_sha256"}, indent=1))
    print(pd.read_csv(TAB / "ground_piece_variants.csv").to_string()); print(pd.read_csv(TAB / "assembly_2008_2024.csv").to_string())
    print(pd.read_csv(TAB / "redundancy_r2.csv").to_string())


if __name__ == "__main__":
    main()
