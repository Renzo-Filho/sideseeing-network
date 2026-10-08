"""Step 6: M1 street density (km per km² of land) and M6 major-class share, Overture ten-class streets, Chicago and São Paulo, with municipal validation."""
import glob, hashlib, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
import evaluate_b1_step4 as b1

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/m1_m6_step6_2026_10_06"
# Decisions S6-1 to S6-7 fixed by the user on 6 October 2026 before this run (MODEL_PLAN Step 6).
TEN = ["motorway", "trunk", "primary", "secondary", "tertiary", "residential", "living_street", "pedestrian", "unclassified", "unknown"]
MAJOR = ["motorway", "trunk", "primary", "secondary"]
LOCAL = ["residential", "living_street", "unclassified", "pedestrian", "unknown"]
CHI_LOCAL_CLASSES, CHI_MAJOR = {"1", "2", "3", "4", "7", "9"}, {"1", "2", "3", "9"}
SP_MAJOR = {"ARTERIAL", "COLETORA", "RODOVIA", "VTR"}
M1_SPEARMAN, M6_SPEARMAN, BAND = 0.95, 0.80, (0.80, 1.25)
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def clip_lengths(lines, units, keys):
    """Exact length of lines inside each unit's land, summed by unit and the given keys."""
    a, b = units.sindex.query(lines.geometry, predicate="intersects")
    seg = shapely.intersection(lines.geometry.values[a], units.geometry.values[b])
    df = pd.DataFrame({"unit_id": units.unit_id.values[b], "km": shapely.length(seg) / 1000})
    for k in keys:
        df[k] = lines[k].values[a]
    return df[df.km > 0]


def oneway(ar):
    if ar is None:
        return False
    return any(r.get("access_type") == "denied" and (r.get("when") or {}).get("heading") and (r.get("when") or {}).get("mode") is None for r in ar)


def overture(city, units, crs):
    s = gpd.read_parquet(next((D / f"{city}/overture_2026_08_19/segment").glob("*.parquet")),
                         columns=["subtype", "class", "subclass", "sources", "access_restrictions", "geometry"])
    s = s[s.subtype.eq("road") & s["class"].isin(TEN)].to_crs(crs).reset_index(drop=True)
    s["src"] = [x[0]["dataset"] if x is not None and len(x) else "none" for x in s.sources]
    s["link"] = s.subclass.eq("link")
    s["oneway"] = [oneway(x) for x in s.access_restrictions]
    return clip_lengths(s, units, ["class", "src", "link", "oneway"])


def municipal(city, units):
    if city == "CHI":
        c = pyogrio.read_dataframe(D / "Chicago/steet_center_lines_20260915.geojson", columns=["class", "status"]).to_crs(26916)
        c = c[c.status.eq("N") & c["class"].isin(CHI_LOCAL_CLASSES)].reset_index(drop=True)
        c["major"] = c["class"].isin(CHI_MAJOR)
        L = clip_lengths(c, units, ["major"])
        return L.groupby("unit_id").km.sum().rename("muni_km"), (L[L.major].groupby("unit_id").km.sum() / L.groupby("unit_id").km.sum()).rename("muni_major_share")
    lg = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg", columns=["lg_id"]).to_crs(31983)
    # 3 source lines carry one NaN vertex mid-line: drop that vertex, keep the street.
    xy, idx = shapely.get_coordinates(lg.geometry.values, return_index=True)
    bad = np.unique(idx[~np.isfinite(xy).all(axis=1)])
    for i in bad:
        c = shapely.get_coordinates(lg.geometry.values[i])
        lg.loc[i, "geometry"] = shapely.LineString(c[np.isfinite(c).all(axis=1)])
    checks["SP_logradouro_nan_vertices_removed"] = {"records": int(len(bad)), "of": len(lg)}
    km = clip_lengths(lg.assign(k=1), units, ["k"]).groupby("unit_id").km.sum().rename("muni_km")
    cv = pyogrio.read_dataframe(D / "SP/Cadastro e Vias/classvias.gpkg", layer="classvias", columns=["Classifica"]).to_crs(31983)
    cv = cv[cv.Classifica.notna()].reset_index(drop=True)
    cv["major"] = cv.Classifica.isin(SP_MAJOR)
    L = clip_lengths(cv, units, ["major"])
    return km, (L[L.major].groupby("unit_id").km.sum() / L.groupby("unit_id").km.sum()).rename("muni_major_share")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for city, crs in (("CHI", 26916), ("SP", 31983)):
        u = b1.land_units(city)
        o = overture("Chicago" if city == "CHI" else "SP", u, crs)
        g = o.groupby("unit_id")
        t = pd.DataFrame({"land_m2": u.set_index("unit_id").geometry.area})
        t["street_km"] = g.km.sum()
        t["m1_km_per_km2"] = t.street_km / (t.land_m2 / 1e6)
        by = o.pivot_table(index="unit_id", columns="class", values="km", aggfunc="sum", fill_value=0).reindex(columns=TEN, fill_value=0)
        for k in TEN:
            t[f"share_{k}"] = by[k] / t.street_km
        t["m6_major_share"] = by[MAJOR].sum(axis=1) / t.street_km
        t["m6_tertiary_share"] = by["tertiary"] / t.street_km
        t["m6_local_share"] = by[LOCAL].sum(axis=1) / t.street_km
        t["share_link"] = o[o.link].groupby("unit_id").km.sum().reindex(t.index, fill_value=0) / t.street_km
        t["share_oneway"] = o[o.oneway].groupby("unit_id").km.sum().reindex(t.index, fill_value=0) / t.street_km
        t["share_tomtom"] = o[o.src.eq("TomTom")].groupby("unit_id").km.sum().reindex(t.index, fill_value=0) / t.street_km
        km, maj = municipal(city, u)
        t["muni_km"], t["muni_major_share"] = km, maj
        t["muni_m1_km_per_km2"] = t.muni_km / (t.land_m2 / 1e6)
        t["ratio_overture_over_muni"] = t.street_km / t.muni_km
        t.insert(0, "city", city)
        rows.append(t)
        print(city, "done", flush=True)
    t = pd.concat(rows)
    t.index.name = "unit_id"
    u3c = pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id").u3_acs_land_km2
    u3s = pd.read_parquet(A / "results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet").set_index("unit_id").u3_land_km2
    cand = pd.read_csv(b1.CAND).set_index("unit_id")
    t["u3"] = pd.concat([u3c, u3s])
    t["b1"] = cand.B1_coverage_land
    checks["no_missing"] = {"pass": bool(t[["m1_km_per_km2", "m6_major_share"]].notna().all().all())}
    for city, c in t.groupby("city"):
        rho1 = c.m1_km_per_km2.corr(c.muni_m1_km_per_km2, method="spearman")
        out = c[(c.ratio_overture_over_muni < BAND[0]) | (c.ratio_overture_over_muni > BAND[1])]
        checks[f"S6-6_{city}_M1"] = {"pass": bool(rho1 >= M1_SPEARMAN), "spearman": float(rho1),
                                     "median_ratio": float(c.ratio_overture_over_muni.median()),
                                     "returned_outside_0.80_1.25": out.ratio_overture_over_muni.round(3).to_dict()}
        rho6 = c.m6_major_share.corr(c.muni_major_share, method="spearman")
        checks[f"S6-6_{city}_M6"] = {"pass": bool(rho6 >= M6_SPEARMAN), "spearman": float(rho6),
                                     "median_overture_major": float(c.m6_major_share.median()), "median_muni_major": float(c.muni_major_share.median())}
        checks[f"S6-7_{city}_descriptive"] = {
            "m1_median": float(c.m1_km_per_km2.median()), "m1_max": [c.m1_km_per_km2.idxmax(), float(c.m1_km_per_km2.max())],
            "m1_min": [c.m1_km_per_km2.idxmin(), float(c.m1_km_per_km2.min())], "m6_median": float(c.m6_major_share.median()),
            "spearman_m1_u3": float(c.m1_km_per_km2.corr(c.u3, method="spearman")), "spearman_m1_b1": float(c.m1_km_per_km2.corr(c.b1, method="spearman")),
            "spearman_m6_m1": float(c.m6_major_share.corr(c.m1_km_per_km2, method="spearman")),
            "median_share_link": float(c.share_link.median()), "median_share_oneway": float(c.share_oneway.median()),
            "median_share_tomtom": float(c.share_tomtom.median()), "max_share_tomtom": [c.share_tomtom.idxmax(), float(c.share_tomtom.max())]}
    t.to_csv(OUT / "m1_m6_by_unit.csv")
    reg = {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        next((D / "Chicago/overture_2026_08_19/segment").glob("*.parquet")), next((D / "SP/overture_2026_08_19/segment").glob("*.parquet")),
        D / "Chicago/steet_center_lines_20260915.geojson", D / "SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg", D / "SP/Cadastro e Vias/classvias.gpkg"]}
    (OUT / "source_register.json").write_text(json.dumps(reg, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()
