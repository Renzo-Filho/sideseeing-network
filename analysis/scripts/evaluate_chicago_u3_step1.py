"""Chicago model Step 1: U3 resident density (ACS 2020-2024 5-year) on land minus water, with the pre-registered checks."""
import hashlib, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
from harmonization.geometry import polygonal

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
RAW = A / "data/Chicago"
REL = A / "results/Chicago/chi_functional_2026_09_16_v2"
PREP = A / "work/prepared/Chicago/chi_functional_2026_09_16_v2"
BASE = A / "work/prepared/Chicago/chi_local_2026_09_16_v1"
OUT = A / "results/Chicago/chicago_u3_step1_2026_10_02"
TAB = OUT / "tables"
# Decision rules fixed by the user on 2 October 2026 (MODEL_PLAN.md, S1-3, S1-5, S1-7 to S1-9), before this script ran.
MAX_PCT, MAX_RANKS, ACS_FLAG = 5.0, 5, 10.0
MAX_CV, Z90 = 0.12, 1.645
ACS = RAW / "acs_2020_2024_5yr"
SPLIT_MIN = 0.01  # context only: a block is "split" if at least 1% of its land lies in another area or outside the city
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(name, ok, **detail):
    checks[name] = {"pass": bool(ok), **detail}


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    districts = gpd.read_parquet(BASE / "districts.parquet").sort_values("unit_id").reset_index(drop=True)
    assert len(districts) == 77 and districts.unit_id.is_unique and districts.crs.to_epsg() == 26916
    pieces = gpd.read_parquet(PREP / "block_district_pieces.parquet")
    blocks = gpd.read_parquet(PREP / "blocks.parquet")
    rel = pd.read_parquet(REL / "tables/functional_attributes.parquet").set_index("unit_id").loc[districts.unit_id]
    support = json.loads((REL / "validation/support_checks.json").read_text())

    # Land = Community Area minus municipal hydrography (C2, S1-1). Water is not clipped to the city,
    # so outside-city parts of edge blocks lose only the water the municipal layer happens to map.
    hydro = pyogrio.read_dataframe(RAW / "Hydro_20260916.geojson").to_crs(26916)
    water = shapely.union_all(hydro.geometry.map(polygonal).values)
    city = districts.geometry.union_all()
    land = shapely.area(shapely.difference(districts.geometry.values, water.intersection(city)))
    diff = np.abs(land - rel.hydro_land_m2.to_numpy()).max()
    check("land_matches_release", diff < 1.0, max_abs_diff_m2=float(diff))

    # Allocation (a) gross piece area (released); (b) land piece area (primary, S1-3).
    shapely.prepare(water)
    pieces["piece_land_m2"] = shapely.area(shapely.difference(pieces.geometry.values, water))
    block_land = pd.Series(shapely.area(shapely.difference(blocks.geometry.values, water)), index=blocks.GEOID20)
    pieces["block_land_m2"] = block_land.reindex(pieces.GEOID20).to_numpy()
    no_land = pieces.block_land_m2 <= 0
    check("no_populated_block_without_land", not (no_land & (pieces.POP20 > 0)).any(),
          populated_pieces_without_land=int((no_land & (pieces.POP20 > 0)).sum()))
    pieces["weight_b"] = np.where(no_land, 0.0, pieces.piece_land_m2 / pieces.block_land_m2.where(~no_land, 1))
    pieces["pop_a"] = pieces.POP20 * pieces.weight
    pieces["pop_b"] = pieces.POP20 * pieces.weight_b
    wsum = pieces.groupby("GEOID20").weight_b.sum()
    check("weights_b_at_most_one", (wsum <= 1 + 1e-8).all(), max_weight_sum=float(wsum.max()))

    # U3-3 mass conservation and coverage, recomputed for both allocations.
    total = blocks.POP20.sum()
    wb = wsum.reindex(blocks.GEOID20, fill_value=0).to_numpy()
    out_b = float((blocks.POP20 * (1 - wb)).sum())
    out_a = float(pd.read_parquet(REL / "tables/border_block_accounting.parquet").outside_population.sum())
    uncovered = city.area - pieces.geometry.area.sum()  # pieces do not overlap (weights sum <= 1 per block)
    check("U3-3_mass_a", np.isclose(pieces.pop_a.sum() + out_a, total), inside=float(pieces.pop_a.sum()), outside=out_a, block_total=int(total))
    check("U3-3_mass_b", np.isclose(pieces.pop_b.sum() + out_b, total), inside=float(pieces.pop_b.sum()), outside=out_b, block_total=int(total))
    check("U3-3_coverage", uncovered / city.area <= 1e-3, uncovered_m2=float(uncovered), share=float(uncovered / city.area),
          release_union_uncovered_m2=support["uncovered_city_m2"])
    check("allocation_a_matches_release", np.allclose(pieces.groupby("unit_id").pop_a.sum().loc[districts.unit_id], rel.population_allocated))

    t = pd.DataFrame({"unit_id": districts.unit_id, "district_name": rel.district_name.to_numpy(),
                      "gross_area_m2": rel.gross_area_m2.to_numpy(), "land_m2": land})
    g = pieces.groupby("unit_id")
    t["residents_b"] = g.pop_b.sum().reindex(t.unit_id).to_numpy()
    t["residents_a"] = g.pop_a.sum().reindex(t.unit_id).to_numpy()
    split = pieces.weight_b < 1 - SPLIT_MIN
    t["split_block_share_b"] = (pieces[split].groupby("unit_id").pop_b.sum().reindex(t.unit_id, fill_value=0).to_numpy() / t.residents_b)
    t["u3_land_km2"] = t.residents_b / (t.land_m2 / 1e6)                     # primary
    t["u3_alloc_a_land_km2"] = t.residents_a / (t.land_m2 / 1e6)             # U3-2 comparison
    t["u3_gross_km2"] = t.residents_b / (t.gross_area_m2 / 1e6)              # S1-2 sensitivity
    for c in ("u3_land_km2", "u3_alloc_a_land_km2", "u3_gross_km2"):
        t["rank_" + c] = t[c].rank(ascending=False)

    # U3-2: (a) vs (b), both on land. Immaterial if every area stays within 5% and moves fewer than 5 ranks.
    t["alloc_pct_change_a_vs_b"] = (t.u3_alloc_a_land_km2 / t.u3_land_km2 - 1) * 100
    t["alloc_rank_move_a_vs_b"] = t.rank_u3_alloc_a_land_km2 - t.rank_u3_land_km2
    over = t[(t.alloc_pct_change_a_vs_b.abs() > MAX_PCT) | (t.alloc_rank_move_a_vs_b.abs() >= MAX_RANKS)]
    check("U3-2_allocation_immaterial", over.empty, max_abs_pct=float(t.alloc_pct_change_a_vs_b.abs().max()),
          max_abs_rank_move=float(t.alloc_rank_move_a_vs_b.abs().max()), cases=over.unit_id.tolist(),
          spearman=float(t.u3_land_km2.corr(t.u3_alloc_a_land_km2, method="spearman")))

    # S1-2 sensitivity (reported, no rule).
    t["gross_pct_change"] = (t.u3_gross_km2 / t.u3_land_km2 - 1) * 100
    t["gross_rank_move"] = t.rank_u3_gross_km2 - t.rank_u3_land_km2
    checks["S1-2_gross_sensitivity"] = {"spearman": float(t.u3_land_km2.corr(t.u3_gross_km2, method="spearman")),
                                        "areas_moving_5_or_more_ranks": int((t.gross_rank_move.abs() >= 5).sum())}

    # U3-4 period diagnostic (descriptive): supplied ACS aggregate vs Census 2020 allocation (b).
    acs = pd.read_csv(REL / "tables/population_period_diagnostic.csv").set_index("unit_id").supplied_acs_population
    t["supplied_acs_population"] = acs.reindex(t.unit_id).to_numpy()
    t["census_vs_acs_pct"] = (t.residents_b / t.supplied_acs_population - 1) * 100
    flagged = t.loc[t.census_vs_acs_pct.abs() > ACS_FLAG, "unit_id"].tolist()
    checks["U3-4_acs_diagnostic"] = {"descriptive_only": True, "flag_pct": ACS_FLAG, "flagged_for_map_review": flagged,
                                     "missing_acs": int(t.supplied_acs_population.isna().sum())}

    # ---- ACS 2020-2024 5-year (primary residents source, user decision 2 October 2026) ----
    acs5 = pd.read_csv(ACS / "acsdt5y2024-b01003.dat", sep="|", dtype=str)
    acs5 = acs5[acs5.GEO_ID.str.startswith("1500000US")]
    acs5 = pd.DataFrame({"bg": acs5.GEO_ID.str[9:].to_numpy(), "E": pd.to_numeric(acs5.B01003_E001).to_numpy(),
                         "M": pd.to_numeric(acs5.B01003_M001).to_numpy()}).set_index("bg")
    bgs = pd.Index(blocks.GEOID20.str[:12].unique())
    check("acs_block_groups_present", bgs.isin(acs5.index).all(), block_groups=len(bgs), missing=int((~bgs.isin(acs5.index)).sum()))
    acs5 = acs5.loc[bgs]
    check("acs_moe_valid", (acs5.M >= 0).all() and (acs5.E >= 0).all(), special_or_negative=int((acs5.M < 0).sum()))
    # All statewide blocks of those block groups (edge block groups extend outside the city).
    bb = districts.to_crs(4269).total_bounds + np.array([-0.1, -0.1, 0.1, 0.1])
    allb = pyogrio.read_dataframe(RAW / "tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", bbox=tuple(bb), columns=["GEOID20", "POP20"])
    allb = allb[allb.GEOID20.str[:12].isin(bgs)].to_crs(26916)
    dbf = pyogrio.read_dataframe(RAW / "tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", read_geometry=False, columns=["GEOID20"])
    check("all_blocks_of_block_groups_read", len(allb) == dbf.GEOID20.str[:12].isin(bgs).sum(), blocks=len(allb))
    allb["bg"] = allb.GEOID20.str[:12]
    allb["land_m2"] = shapely.area(shapely.difference(allb.geometry.map(polygonal).values, water))
    bg_pop20 = allb.groupby("bg").POP20.sum()
    bg_land = allb.groupby("bg").land_m2.sum()
    # A block group with ACS residents must have 2020 residents to split them by; empty-in-both groups carry nothing.
    zero20 = bg_pop20.loc[bgs] == 0
    check("no_acs_residents_without_2020_blocks", not (zero20 & (acs5.E > 0)).any(),
          zero_in_both=int((zero20 & (acs5.E == 0)).sum()), acs_residents_unsplittable=float(acs5.E[zero20].sum()))
    pieces["bg"] = pieces.GEOID20.str[:12]
    # S1-7 (a) primary: 2020 block-population share within the block group x block land share in the area.
    pieces["w_acs_a"] = (pieces.POP20 / bg_pop20.reindex(pieces.bg).replace(0, np.nan).to_numpy()).fillna(0) * pieces.weight_b
    # S1-7 (b) sensitivity: land share of the block group.
    pieces["w_acs_b"] = pieces.piece_land_m2 / bg_land.reindex(pieces.bg).to_numpy()
    for k in ("a", "b"):
        w = pieces.groupby(["unit_id", "bg"])["w_acs_" + k].sum().rename("w").reset_index()
        w["E"], w["M"] = acs5.E.reindex(w.bg).to_numpy(), acs5.M.reindex(w.bg).to_numpy()
        wbg = w.groupby("bg").w.sum()
        check(f"acs_{k}_weights_at_most_one", (wbg <= 1 + 1e-8).all(), max=float(wbg.max()))
        est = (w.w * w.E).groupby(w.unit_id).sum().reindex(t.unit_id).to_numpy()
        outside = float((acs5.E * (1 - wbg.reindex(acs5.index, fill_value=0))).sum())
        check(f"acs_{k}_mass", np.isclose(est.sum() + outside, acs5.E.sum()), inside=float(est.sum()), outside=outside, block_group_total=int(acs5.E.sum()))
        t["acs_residents_" + k] = est
        if k == "a":
            # Census approximation for derived sums; ignores correlation between block groups, so it understates.
            t["acs_moe90_a"] = np.sqrt(((w.w * w.M) ** 2).groupby(w.unit_id).sum().reindex(t.unit_id).to_numpy())
    t["acs_cv_a"] = t.acs_moe90_a / Z90 / t.acs_residents_a
    t["u3_acs_land_km2"] = t.acs_residents_a / (t.land_m2 / 1e6)            # PRIMARY U3
    t["u3_acs_lo90"] = (t.acs_residents_a - t.acs_moe90_a) / (t.land_m2 / 1e6)
    t["u3_acs_hi90"] = (t.acs_residents_a + t.acs_moe90_a) / (t.land_m2 / 1e6)
    t["u3_acs_b_land_km2"] = t.acs_residents_b / (t.land_m2 / 1e6)
    t["rank_u3_acs"] = t.u3_acs_land_km2.rank(ascending=False)
    t["rank_u3_acs_b"] = t.u3_acs_b_land_km2.rank(ascending=False)
    # Ranks spanned by the 90% interval: other areas whose point estimate lies inside it, plus itself.
    pt = t.u3_acs_land_km2.to_numpy()
    t["rank_span_90"] = [int(((pt >= lo) & (pt <= hi)).sum()) for lo, hi in zip(t.u3_acs_lo90, t.u3_acs_hi90)]

    # S1-8 uncertainty gate: every area's coefficient of variation <= 12%.
    over_cv = t[t.acs_cv_a > MAX_CV]
    check("S1-8_cv_gate", over_cv.empty, max_cv=float(t.acs_cv_a.max()), median_cv=float(t.acs_cv_a.median()),
          cases=over_cv.unit_id.tolist(), median_rank_span=float(t.rank_span_90.median()), max_rank_span=int(t.rank_span_90.max()))

    # S1-7 rule: (a) vs (b) immaterial if every area within 5% and fewer than 5 ranks.
    t["acs_alloc_pct_b_vs_a"] = (t.u3_acs_b_land_km2 / t.u3_acs_land_km2 - 1) * 100
    t["acs_alloc_rank_move"] = t.rank_u3_acs_b - t.rank_u3_acs
    over = t[(t.acs_alloc_pct_b_vs_a.abs() > MAX_PCT) | (t.acs_alloc_rank_move.abs() >= MAX_RANKS)]
    check("S1-7_allocation_immaterial", over.empty, max_abs_pct=float(t.acs_alloc_pct_b_vs_a.abs().max()),
          max_abs_rank_move=float(t.acs_alloc_rank_move.abs().max()), cases=over.unit_id.tolist(),
          spearman=float(t.u3_acs_land_km2.corr(t.u3_acs_b_land_km2, method="spearman")))

    # S1-9 period comparison (descriptive): ACS 2020-2024 vs 2020 Census count, and the supplied aggregate vs ACS.
    t["acs_vs_census2020_pct"] = (t.acs_residents_a / t.residents_b - 1) * 100
    t["supplied_vs_acs_pct"] = (t.supplied_acs_population / t.acs_residents_a - 1) * 100
    checks["S1-9_period_comparison"] = {
        "descriptive_only": True, "flag_pct": ACS_FLAG,
        "flagged_for_map_review": t.loc[t.acs_vs_census2020_pct.abs() > ACS_FLAG, "unit_id"].tolist(),
        "city_acs_vs_census2020_pct": float((t.acs_residents_a.sum() / t.residents_b.sum() - 1) * 100),
        "spearman_u3_acs_vs_census2020": float(t.u3_acs_land_km2.corr(t.u3_land_km2, method="spearman")),
        "areas_moving_5_or_more_ranks": int(((t.rank_u3_acs - t.rank_u3_land_km2).abs() >= 5).sum()),
        "supplied_aggregate_vs_acs_2020_2024": {"median_abs_pct": float(t.supplied_vs_acs_pct.abs().median()),
                                                "max_abs_pct": float(t.supplied_vs_acs_pct.abs().max()),
                                                "city_pct": float((t.supplied_acs_population.sum() / t.acs_residents_a.sum() - 1) * 100)}}

    assert t.u3_acs_land_km2.notna().all() and (t.u3_acs_land_km2 > 0).all()
    assert t.u3_land_km2.notna().all() and (t.u3_land_km2 > 0).all()
    t.to_csv(TAB / "u3_step1.csv", index=False)
    t.to_parquet(TAB / "u3_step1.parquet", index=False)

    # C3 source register (S1-6): raw sources with release, period and hash; derived inputs hashed for lineage.
    tiger = sorted((RAW / "tl_2022_17_tabblock20").glob("tl_2022_17_tabblock20.*"))
    register = {
        "sources": [
            {"source": "US Census Bureau TIGER/Line 2022 tabulation blocks, Illinois (POP20 = 2020 Census, P.L. 94-171, Disclosure Avoidance applied)",
             "release": "tl_2022_17_tabblock20", "observation_period": "Census day, 1 April 2020",
             "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in tiger}},
            {"source": "City of Chicago Boundaries - Community Areas", "release": "download 2026-08-31",
             "observation_period": "current boundaries at download",
             "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in [RAW / "Boundaries_-_Community_Areas_20260831.geojson"]}},
            {"source": "City of Chicago Hydrography", "release": "download 2026-09-16",
             "observation_period": "publisher edit dates vary; completeness review pending (release config hydro_status)",
             "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in [RAW / "Hydro_20260916.geojson"]}},
            {"source": "US Census Bureau American Community Survey 5-year, table B01003 Total population, block groups (2020 geography); table-based Summary File",
             "release": "ACS 2020-2024 5-year", "observation_period": "pooled sample, 1 January 2020 to 31 December 2024",
             "url": "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/",
             "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in [ACS / "acsdt5y2024-b01003.dat", ACS / "ACS20245YR_Table_Shells.txt"]}}],
        "derived_inputs": {p.relative_to(ROOT).as_posix(): sha(p) for p in [
            BASE / "districts.parquet", PREP / "block_district_pieces.parquet", PREP / "blocks.parquet",
            REL / "tables/functional_attributes.parquet", REL / "tables/border_block_accounting.parquet",
            REL / "tables/population_period_diagnostic.csv"]}}
    (OUT / "source_register.json").write_text(json.dumps(register, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float))
    gates = [k for k, v in checks.items() if "pass" in v and not v["pass"]]
    print("FAILED:", gates or "none")


if __name__ == "__main__":
    main()
