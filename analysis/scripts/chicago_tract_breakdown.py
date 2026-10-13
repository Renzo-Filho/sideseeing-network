"""Chicago Community Areas broken down by 2020 census tract, for the explorer's Chicago tracts tab.

A sub-unit is a tract piece: the 2020 blocks of one tract inside one Community Area (block_district_pieces), so pieces
nest exactly in the 77 areas. Pieces under 5% of their tract's city land or under 0.05 km² (boundary slivers) are
computed but not published. The 21 columns of sp_chicago_model_v2 are recomputed for every piece with the accepted
family scripts' own functions and rules: U3, U2, U4 residents and U6 dwellings from the same block allocation; B1, BV,
M1, M6, M3, M4, M7, U1 and U6 places on the piece's land. Checks: summing the pieces' counts reproduces each area's
published counts, and the non-additive functions (BV, M3, M4, U4) reproduce the published area values.

    python analysis/scripts/chicago_tract_breakdown.py"""
import json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
from harmonization.geometry import polygonal
import evaluate_b1_step4 as b1
import evaluate_bv_step5 as bv
import evaluate_m1_m6_step6 as m1
import evaluate_m3_m4_m7_step8 as m8
import evaluate_u1_step7 as u1
import evaluate_u4_ptal_step2 as u4
import build_u6_activity as u6

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data/Chicago"
PREP = A / "work/prepared/Chicago/chi_functional_2026_09_16_v2"
OUT = A / "results/Chicago/chicago_tract_breakdown_2026_10_13"
R = A / "results"
NEIGHBOURHOODS = D / "Boundaries_-_Neighborhoods_20261013.geojson"     # City of Chicago bbvz-uum9, downloaded 2026-10-13
MIN_SHARE, MIN_LAND_M2 = 0.05, 50_000
CLR = [f"u6_clr_city_{k}" for k in u6.CLASSES]
checks = {}


def check(name, a, b, rtol=1e-6, atol=1e-6):
    """Pieces summed (or recomputed) per Community Area against the published value."""
    a, b = a.reindex(b.index), b.astype(float)
    bad = ~np.isclose(a, b, rtol=rtol, atol=atol)
    checks[name] = {"pass": bool(not bad.any()), "max_abs_diff": float((a - b).abs().max()), "areas_off": b.index[bad].tolist()}


def tract_name(code):
    return f"Tract {int(code[:4])}" + (f".{code[4:]}" if code[4:] != "00" else "")


def block_pieces(water):
    """Block pieces with the U3/U2/U6 allocations (same rules as evaluate_chicago_u3_step1, evaluate_u2_step3, build_u6_activity)."""
    p = gpd.read_parquet(PREP / "block_district_pieces.parquet")
    blocks = gpd.read_parquet(PREP / "blocks.parquet")
    p["geometry"] = shapely.difference(p.geometry.values, water)
    block_land = pd.Series(shapely.area(shapely.difference(blocks.geometry.values, water)), index=blocks.GEOID20)
    p["w"] = (p.geometry.area / block_land.reindex(p.GEOID20).to_numpy()).fillna(0)
    dbf = pyogrio.read_dataframe(D / "tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", read_geometry=False, columns=["GEOID20", "POP20", "HOUSING20"])
    bg = p.GEOID20.str[:12]

    def acs(table, col, by):                     # ACS block-group estimate -> 2020 blocks by `by` share -> piece by land share
        a = pd.read_csv(D / f"acs_2020_2024_5yr/acsdt5y2024-{table}.dat", sep="|", dtype=str)
        a = a[a.GEO_ID.str.startswith("1500000US")]
        a = pd.Series(pd.to_numeric(a[col]).to_numpy(), index=a.GEO_ID.str[9:].to_numpy())
        tot = dbf.groupby(dbf.GEOID20.str[:12])[by].sum()
        share = dbf.set_index("GEOID20")[by].reindex(p.GEOID20).to_numpy() / tot.reindex(bg).replace(0, np.nan).to_numpy()
        return a.reindex(bg).to_numpy() * np.nan_to_num(share) * p.w.to_numpy()

    p["residents"] = acs("b01003", "B01003_E001", "POP20")
    p["dwellings"] = acs("b25001", "B25001_E001", "HOUSING20")
    wac = pd.read_csv(D / "lodes_2023/il_wac_S000_JT00_2023.csv.gz", dtype={"w_geocode": str}, usecols=["w_geocode", "C000"]).set_index("w_geocode").C000
    p["jobs"] = wac.reindex(p.GEOID20).fillna(0).to_numpy() * p.w.to_numpy()
    p["sub_id"] = p.unit_id + "/" + p.GEOID20.str[5:11]
    return p


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    water = shapely.union_all(pyogrio.read_dataframe(D / "Hydro_20260916.geojson").to_crs(26916).geometry.map(polygonal).values)
    shapely.prepare(water)
    bp = block_pieces(water)
    gross = gpd.read_parquet(PREP / "block_district_pieces.parquet").assign(sub_id=bp.sub_id).dissolve("sub_id")[["geometry"]].reset_index()
    land = gross.assign(geometry=shapely.difference(gross.geometry.values, water)).rename(columns={"sub_id": "unit_id"})
    t = pd.DataFrame(index=pd.Index(gross.sub_id, name="sub_id"))
    t["unit_id"], t["tract"] = t.index.str[:6], t.index.str[7:]
    t["land_m2"] = land.set_index("unit_id").geometry.area
    land = land[land.area > 0].reset_index(drop=True)                     # 54 pieces are water only
    t["share_of_tract_land"] = t.land_m2 / t.groupby("tract").land_m2.transform("sum")
    ca = b1.land_units("CHI")
    ca_of = lambda s: s.groupby(s.index.str[:6]).sum()
    print("units", len(t), flush=True)

    # U3, U2, U6 dwellings: allocations summed by piece.
    g = bp.groupby("sub_id")
    for c in ("residents", "jobs", "dwellings"):
        t[c] = g[c].sum()
    u3 = pd.read_parquet(R / "Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id")
    u2 = pd.read_parquet(R / "SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.parquet").set_index("unit_id")
    u6t = pd.read_csv(R / "SP_CHI/u6_activity_2026_10_06/u6_by_unit.csv").set_index("unit_id")
    chi = u6t.index[u6t.index.str.startswith("CHI:")]
    check("U3_residents", ca_of(t.residents), u3.acs_residents_a)
    check("U2_jobs", ca_of(t.jobs), u2.jobs.dropna().loc[lambda s: s.index.str.startswith("CHI:")])
    check("U6_dwellings", ca_of(t.dwellings), u6t.dwellings.loc[chi])
    check("land", ca_of(t.land_m2), u3.land_m2, rtol=1e-3)
    t["u3_acs_land_km2"] = t.residents / (t.land_m2 / 1e6)
    t["u2_jobs_land_km2"] = t.jobs / (t.land_m2 / 1e6)

    # B1: exact footprint union on land (evaluate_b1_step4.coverage, the B1.py method).
    ov = gpd.read_parquet(D / "overture_2026_08_19/building/part_0000.parquet", columns=["geometry"]).to_crs(26916)
    cov = b1.coverage(land, ov, "b1").set_index("unit_id")
    t["B1_coverage_land"] = cov.b1
    cand = pd.read_csv(b1.CAND).set_index("unit_id")
    check("B1_footprint_m2", ca_of(cov.b1_footprint_m2), cand.footprint_union_land_m2.loc[lambda s: s.index.str.startswith("CHI:")], rtol=1e-4)
    print("B1", flush=True)

    # BV: GHSL cells weighted by land overlap.
    t["bv_height_built_m"] = bv.ghsl("CHI", land).set_index("unit_id").bv_height_built_m
    pub = pd.read_csv(R / "SP_CHI/bv_step5_2026_10_05/bv_step5_by_unit.csv").set_index("unit_id")
    check("BV_function_on_areas", bv.ghsl("CHI", ca).set_index("unit_id").bv_height_built_m, pub.bv_height_built_m.loc[ca.unit_id])
    print("BV", flush=True)

    # M1, M6: Overture ten-class streets clipped to land.
    o = m1.overture("Chicago", land, 26916)
    km = o.groupby("unit_id").km.sum()
    t["m1_km_per_km2"] = km / (t.land_m2 / 1e6)
    t["m6_major_share"] = o[o["class"].isin(m1.MAJOR)].groupby("unit_id").km.sum().reindex(t.index, fill_value=0) / km
    mm = pd.read_csv(R / "SP_CHI/m1_m6_step6_2026_10_06/m1_m6_by_unit.csv").set_index("unit_id")
    # The 2020 blocks stop short of the state line in East Side (a 642 m² strip holding 0.149 km of State Line Ave): 0.19%.
    check("M1_street_km", ca_of(km), mm.street_km.loc[ca.unit_id], rtol=2e-3)
    print("M1 M6", flush=True)

    # M3, M4: faces of the M1 network, area-weighted medians over the land in each unit; M7: ground parcels.
    f = m8.faces(m8.overture_lines("CHI"), m8.water("CHI"))
    s = m8.summarise(f, land, "ov")
    for c in ("ov_m3_wmedian_ln_m2", "ov_m4_wmedian_compactness", "ov_m4_wmedian_elongation"):
        t[c] = s[c]
    pub = pd.read_csv(R / "SP_CHI/m3_m4_m7_step8_2026_10_06/m3_m4_m7_by_unit.csv").set_index("unit_id")
    sa = m8.summarise(f, ca, "ov")
    for c in ("ov_m3_wmedian_ln_m2", "ov_m4_wmedian_compactness"):
        check(f"{c}_function_on_areas", sa[c], pub[c].loc[ca.unit_id])
    n, _, _ = m8.m7_chicago(gross.rename(columns={"sub_id": "unit_id"}).to_crs(26916))
    t["m7_parcels"] = n.reindex(t.index, fill_value=0)
    t["m7_parcels_per_km2"] = t.m7_parcels / (t.land_m2 / 1e6)
    check("M7_parcels", ca_of(t.m7_parcels), pub.m7_parcels.loc[ca.unit_id])
    print("M3 M4 M7", flush=True)

    # U1: CMAP LUI 2023 occupied-land shares; missing under 10% classified occupied land (S7-4).
    lui = pyogrio.read_dataframe(D / "LUI_2023_view_332920193481040239.gpkg", bbox=tuple(ca.to_crs(3857).total_bounds), columns=["LANDUSE"]).to_crs(26916)
    lui["geometry"] = shapely.make_valid(lui.geometry.values)
    lui["cls"] = lui.LANDUSE.map(u1.cmap_class)
    areas = u1.clip_areas(lui, land, ["cls"])
    s = u1.summarise(areas, land, "cls", "")
    t["occupied_coverage"] = s.occupied_coverage
    for c in ("p_residential", "p_commerce", "p_industrial", "p_institutional"):
        t[c] = s[c].where(s.occupied_coverage >= u1.MIN_COVERAGE)
    occ = areas[areas.cls.isin(u1.OCC)]
    pub = pd.read_csv(R / "SP_CHI/u1_step7_2026_10_06/u1_by_unit.csv").set_index("unit_id").loc[ca.unit_id]
    check("U1_commerce_share", (lambda a: a.commerce / a.sum(axis=1))(occ.assign(ca=occ.unit_id.str[:6]).pivot_table(index="ca", columns="cls", values="m2", aggfunc="sum")),
          pub.p_commerce, rtol=1e-3)
    print("U1", flush=True)

    # U6: classified Overture places on land, per 100 dwellings, and log-ratios centred on the Chicago areas' mean.
    xw = dict(pd.read_csv(u6.CFG / "overture_taxonomy.csv")[["key", "class"]].values)
    pl = pd.concat([gpd.read_parquet(p, columns=["id", "taxonomy", "operating_status", "geometry"]) for p in sorted((D / "overture_2026_08_19/place").glob("*.parquet"))], ignore_index=True)
    pl = pl[~pl.operating_status.isin(["permanently_closed", "temporarily_closed"])].to_crs(26916)
    pl["class"] = [u6.overture_class(x, xw) for x in pl.taxonomy]
    j = gpd.sjoin(pl[["class", "geometry"]], land, predicate="within")
    cnt = j[j["class"].isin(u6.CLASSES)].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(index=t.index, columns=u6.CLASSES, fill_value=0)
    check("U6_establishments", ca_of(cnt.sum(axis=1)), u6t.n_classified.loc[chi], atol=5)       # points on a piece boundary fall in neither piece
    t["establishments"] = cnt.sum(axis=1)
    t["u6_log_intensity"] = np.log(100 * t.establishments / t.dwellings)
    lg = np.log(cnt + 0.5)
    clr = lg.sub(lg.mean(axis=1), axis=0)
    for k in u6.CLASSES:
        t[f"clr_{k}"] = clr[k]                                                   # raw log-ratios (all-absolute scaling)
        t[f"u6_clr_city_{k}"] = clr[k] - u6t.loc[chi, f"clr_{k}"].mean()        # centred on the 77 areas (hybrid, all-relative)
    none = t.establishments == 0                                                 # no composition without establishments
    t.loc[none, [f"clr_{k}" for k in u6.CLASSES] + CLR] = np.nan
    print("U6", flush=True)

    # U4: PTAL Access Index at the same 100 m resident points as the published run, averaged by piece.
    cfg = u4.CITIES["CHI"]
    units, _ = u4.chicago_units_and_people()
    units = units.to_crs(cfg["crs"])
    polys = bp.loc[bp.residents > 0, ["sub_id", "residents", "geometry"]].rename(columns={"sub_id": "unit_id"})
    pts, _ = u4.grid_points(polys)
    area = units.union_all().buffer(2000)
    dep = pd.concat([u4.departures(path, modes, units)[0] for path, modes in cfg["feeds"]], ignore_index=True)
    dep = dep[dep.within(area)]
    G, nxy, main_, _ = u4.walk_graph(cfg["overture"], cfg["crs"], area, u4.NO_WALK)
    ai = u4.access_index(np.c_[pts.geometry.x, pts.geometry.y], dep, (G, nxy, main_))
    w, tot = pts.weight.to_numpy(), ai["total"]
    t["u4_ptai_avg_resident"] = pd.Series(w * tot).groupby(pts.unit_id.to_numpy()).sum() / pd.Series(w).groupby(pts.unit_id.to_numpy()).sum()
    by_ca = pts.unit_id.str[:6].to_numpy()
    pub = pd.read_parquet(R / "SP_CHI/u4_ptal_step2_2026_10_05/tables/u4_ptal.parquet").set_index("unit_id")
    check("U4_resident_weighted_areas", pd.Series(w * tot).groupby(by_ca).sum() / pd.Series(w).groupby(by_ca).sum(), pub.u4_ptai_avg_resident.loc[ca.unit_id])
    print("U4", flush=True)

    # Names: the tract, and the City neighbourhood holding the piece's representative point.
    nb = pyogrio.read_dataframe(NEIGHBOURHOODS, columns=["pri_neigh"]).to_crs(26916)
    rp = gpd.GeoDataFrame({"sub_id": gross.sub_id}, geometry=gross.representative_point(), crs=gross.crs)
    t["neighbourhood"] = gpd.sjoin(rp, nb, predicate="within").drop_duplicates("sub_id").set_index("sub_id").pri_neigh
    t["name"] = t.tract.map(tract_name)
    t["published"] = (t.share_of_tract_land >= MIN_SHARE) & (t.land_m2 >= MIN_LAND_M2)

    cols = ["unit_id", "tract", "name", "neighbourhood", "published", "land_m2", "share_of_tract_land", "residents", "jobs", "dwellings",
            "establishments", "occupied_coverage", "m7_parcels", "m1_km_per_km2", "ov_m3_wmedian_ln_m2", "ov_m4_wmedian_compactness",
            "ov_m4_wmedian_elongation", "m6_major_share", "m7_parcels_per_km2", "B1_coverage_land", "bv_height_built_m", "u2_jobs_land_km2",
            "u3_acs_land_km2", "u4_ptai_avg_resident", "u6_log_intensity", *CLR, *[f"clr_{k}" for k in u6.CLASSES],
            "p_residential", "p_commerce", "p_industrial", "p_institutional"]
    t[cols].to_csv(OUT / "tract_columns.csv")
    gross[gross.sub_id.isin(t.index[t.published])].to_parquet(OUT / "tract_pieces.parquet")
    pub = t[t.published]
    checks["summary"] = {"pieces": len(t), "published": int(len(pub)), "areas_covered": int(pub.unit_id.nunique()),
                         "published_land_share": float(pub.land_m2.sum() / t.land_m2.sum()),
                         "published_without_residents": int((pub.residents <= 0).sum()), "published_without_u1": int(pub.p_commerce.isna().sum()),
                         "published_under_100_establishments": int((pub.establishments < 100).sum())}
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float))
    print("FAILED:", [k for k, v in checks.items() if "pass" in v and not v["pass"]] or "none")


if __name__ == "__main__":
    main()
