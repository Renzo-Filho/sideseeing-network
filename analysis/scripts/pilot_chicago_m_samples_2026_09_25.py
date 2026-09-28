"""Bounded, reproducible Chicago M2/M3/M4 diagnostic sample.

Four new Community Areas are selected by seeded sampling, one per quartile of
the released municipal M1. This processes only those geometries. Census blocks
are diagnostic references, not certified physical blocks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from scipy.spatial import cKDTree

from harmonization.geometry import largest_overlap
from harmonization.junctions_v2 import linked_components, short_connector_links
from harmonization.roads import shape_metrics
from review_block_reference_fixtures_v2 import match_best, owned_polygons


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m_sample_2026_09_25"
PREVIOUS = {"CHI:24", "CHI:28", "CHI:30", "CHI:32", "CHI:76"}


def select_units():
    wide = pd.read_csv(A / "results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv")
    wide["m1_quartile"] = pd.qcut(wide.street_density_municipal_km_km2, 4, labels=False)
    rows = []
    for quartile in range(4):
        eligible = wide.loc[(wide.m1_quartile == quartile) & ~wide.unit_id.isin(PREVIOUS)]
        row = eligible.sample(1, random_state=20260925 + quartile).iloc[0]
        rows.append({"unit_id": row.unit_id, "district_name": row.district_name,
                     "m1_quartile": quartile,
                     "street_density_municipal_km_km2": row.street_density_municipal_km_km2,
                     "selection": "one seeded draw per full-cohort M1 quartile; prior pilot units excluded"})
    return pd.DataFrame(rows)


def m1_m6_source_diagnostic(selection):
    """Read existing released rows only; no road geometry rebuild."""
    local = pd.read_csv(A / "results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv")
    overture = pd.read_csv(A / "results/Chicago/harmonized_candidates_2026_09_22/candidate_attributes_wide.csv")
    result = selection[["unit_id"]].merge(local, on="unit_id").merge(overture, on="unit_id")
    municipal_shares = [f"road_share_code_{x}" for x in (1, 2, 3, 4, 7, 9, 99)]
    overture_shares = [x for x in result.columns if x.startswith("M6_share_")]
    out = pd.DataFrame({
        "unit_id": result.unit_id,
        "municipal_m1_km_per_km2": result.street_density_municipal_km_km2,
        "overture_m1_km_per_km2": result.mapped_street_density_km_km2,
        "overture_to_municipal_m1_ratio": result.mapped_street_density_km_km2 / result.street_density_municipal_km_km2,
        "municipal_code_99_share": result.road_share_code_99,
        "overture_unknown_share": result.M6_share_unknown,
        "municipal_m6_share_sum": result[municipal_shares].sum(axis=1),
        "overture_m6_share_sum": result[overture_shares].sum(axis=1),
        "status": "source_scope_diagnostic_not_common_class_equivalence",
    })
    assert np.allclose(out.municipal_m6_share_sum, 1) and np.allclose(out.overture_m6_share_sum, 1)
    out.to_csv(OUT / "m1_m6_source_diagnostic.csv", index=False)


def junction_diagnostics(unit, roads, candidates, district, rng):
    c = candidates.loc[candidates.unit_id.eq(unit)].copy()
    r = roads.iloc[roads.sindex.query(district.buffer(25), predicate="intersects")].copy()
    links = short_connector_links(r, c, max_link_m=20)
    components = linked_components(c, links, max_diameter_m=35)
    points = np.column_stack([c.geometry.x.to_numpy(), c.geometry.y.to_numpy()])
    near = cKDTree(points).query_pairs(10)
    ids = c.id.to_numpy()
    near_keys = {tuple(sorted((ids[i], ids[j]))) for i, j in near}
    linked = {(x["connector_a"], x["connector_b"]): x for x in links}
    index = c.set_index("id")
    fixtures = []
    for category, keys in [
        ("near_with_short_source_link", sorted(near_keys & linked.keys())),
        ("near_without_short_source_link", sorted(near_keys - linked.keys())),
    ]:
        if not keys:
            continue
        chosen = rng.choice(len(keys), size=min(5, len(keys)), replace=False)
        for pos in sorted(chosen):
            a, b = keys[pos]
            ga, gb = index.loc[a].geometry, index.loc[b].geometry
            fixtures.append({"unit_id": unit, "category": category, "connector_a": a,
                             "connector_b": b, "straight_m": ga.distance(gb),
                             "road_id": linked.get((a, b), {}).get("road_id"),
                             "a_arms_source": int(index.loc[a].arms),
                             "b_arms_source": int(index.loc[b].arms),
                             "x_mid": (ga.x + gb.x) / 2, "y_mid": (ga.y + gb.y) / 2,
                             "physical_junction_label": "unreviewed"})
    summary = {"unit_id": unit, "candidate_connectors": len(c),
               "near_pairs_10m": len(near_keys),
               "near_pairs_with_short_source_link": len(near_keys & linked.keys()),
               "short_source_links_20m": len(links),
               "linked_components": len(components),
               "components_over_35m": sum(not x["within_diameter_cap"] for x in components),
               "status": "diagnostic_only_no_physical_arm_labels"}
    return summary, fixtures


def block_diagnostics(unit, local_id, district, districts, roads, census, rail):
    extraction = district.buffer(250)
    r = roads.iloc[roads.sindex.query(extraction, predicate="intersects")]
    ref = census.iloc[census.sindex.query(district, predicate="intersects")].copy()
    owners = largest_overlap(ref, districts)
    ref = ref.loc[owners.astype(str).eq(local_id).to_numpy()].reset_index(drop=True)
    ref["reference_id"] = ref.GEOID20.astype(str)
    nearby_rail = rail.iloc[rail.sindex.query(extraction, predicate="intersects")]
    rail_union = shapely.union_all(shapely.make_valid(nearby_rail.geometry.values)) if len(nearby_rail) else shapely.GeometryCollection()
    base = list(r.loc[r.subclass.ne("link")].geometry.values)
    rail_edges = list(shapely.get_parts(rail_union.boundary))
    modes = {
        "all_streets": list(r.geometry.values),
        "no_links": base,
        "no_links_rail_row": base + rail_edges,
    }
    summaries, fixtures = [], []
    for mode, lines in modes.items():
        candidate = owned_polygons(lines, district, extraction, districts, local_id)
        before_rail_filter = len(candidate)
        if mode == "no_links_rail_row" and len(candidate) and not rail_union.is_empty:
            rail_fraction = [g.intersection(rail_union).area / g.area for g in candidate.geometry]
            candidate = candidate.loc[np.asarray(rail_fraction) <= .5].reset_index(drop=True)
        candidate["candidate_id"] = [f"{unit}:{mode}:{i}" for i in range(len(candidate))]
        if len(candidate):
            _, forward = match_best(candidate, ref, "reference_id")
            metrics = shape_metrics(candidate.geometry.values)
            candidate["best_reference_iou"] = forward
            candidate["area_m2"] = metrics.area_m2.to_numpy()
            candidate["min_width_m"] = metrics.rectangle_min_width_m.to_numpy()
            _, reverse = match_best(ref, candidate, "candidate_id")
        else:
            forward, reverse = np.array([]), np.zeros(len(ref))
            metrics = pd.DataFrame()
        summaries.append({
            "unit_id": unit, "mode": mode, "roads_in_extraction": len(r),
            "rail_row_polygons_in_extraction": len(nearby_rail),
            "candidate_count_before_rail_filter": before_rail_filter,
            "candidate_count": len(candidate), "census_reference_count": len(ref),
            "narrow_under_6m": int((metrics.rectangle_min_width_m < 6).sum()) if len(metrics) else 0,
            "candidate_share_iou_ge_050": float(np.mean(forward >= .5)) if len(forward) else None,
            "reference_share_iou_ge_050": float(np.mean(reverse >= .5)) if len(reverse) else None,
            "median_area_m2": float(metrics.area_m2.median()) if len(metrics) else None,
            "median_log_area": float(metrics.log_area.median()) if len(metrics) else None,
            "iqr_log_area": float(metrics.log_area.quantile(.75) - metrics.log_area.quantile(.25)) if len(metrics) else None,
            "median_compactness": float(metrics.compactness.median()) if len(metrics) else None,
            "iqr_compactness": float(metrics.compactness.quantile(.75) - metrics.compactness.quantile(.25)) if len(metrics) else None,
            "median_elongation": float(metrics.elongation.median()) if len(metrics) else None,
            "iqr_elongation": float(metrics.elongation.quantile(.75) - metrics.elongation.quantile(.25)) if len(metrics) else None,
            "status": "census_reference_is_diagnostic_not_physical_block_truth",
        })
        if len(candidate):
            # Balanced small inspection packet: lowest and highest overlaps,
            # plus narrow objects. Duplicates are removed by candidate ID.
            picks = pd.concat([
                candidate.nsmallest(3, "best_reference_iou"),
                candidate.nlargest(3, "best_reference_iou"),
                candidate.nsmallest(3, "min_width_m"),
            ]).drop_duplicates("candidate_id")
            for row in picks.itertuples():
                fixtures.append({"unit_id": unit, "mode": mode,
                                 "candidate_id": row.candidate_id,
                                 "best_reference_iou": row.best_reference_iou,
                                 "area_m2": row.area_m2, "min_width_m": row.min_width_m,
                                 "geometry_wkt": row.geometry.wkt,
                                 "physical_block_label": "unreviewed"})
        print(unit, mode, len(candidate), "candidate blocks", flush=True)
    return summaries, fixtures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-m1-m6", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    selection = select_units()
    selection.to_csv(OUT / "sample_selection.csv", index=False)
    m1_m6_source_diagnostic(selection)
    if args.only_m1_m6:
        return
    roads = gpd.read_parquet(A / "work/prepared/Chicago/overture_2026_08_19_review_v1/selected_roads.parquet")
    candidates = gpd.read_parquet(A / "work/runs/sp_chicago_harmonization_2026_09_22/roads/Chicago_connector_candidates.parquet")
    districts = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    census = gpd.read_parquet(A / "work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet")
    rail = pyogrio.read_dataframe(A / "data/Chicago/LUI_2023_view_332920193481040239.gpkg",
                                   where="LANDUSE = '1511'", columns=["LANDUSE", "FAC_NAME"]).to_crs(roads.crs)
    assert roads.crs == candidates.crs == districts.crs == census.crs == rail.crs
    rng = np.random.default_rng(20260925)
    junction_rows, junction_fixtures, block_rows, block_fixtures = [], [], [], []
    for unit in selection.unit_id:
        local_id = unit.split(":")[1]
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        js, jf = junction_diagnostics(unit, roads, candidates, district, rng)
        bs, bf = block_diagnostics(unit, local_id, district, districts, roads, census, rail)
        junction_rows.append(js)
        junction_fixtures.extend(jf)
        block_rows.extend(bs)
        block_fixtures.extend(bf)
    pd.DataFrame(junction_rows).to_csv(OUT / "m2_sample_summary.csv", index=False)
    pd.DataFrame(junction_fixtures).to_csv(OUT / "m2_annotation_queue.csv", index=False)
    pd.DataFrame(block_rows).to_csv(OUT / "m3_m4_sample_summary.csv", index=False)
    pd.DataFrame(block_fixtures).to_csv(OUT / "m3_m4_annotation_queue.csv", index=False)


if __name__ == "__main__":
    main()
