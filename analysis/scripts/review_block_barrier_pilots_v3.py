"""Test rail and water line additions on paired no-link road block pilots.

This is a diagnostic of polygonization and local-reference coverage. Rail
centerlines/shorelines alone are not an accepted physical-block ontology.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyogrio
import shapely

from harmonization.road_intervals import boundary_parts
from review_block_reference_fixtures_v2 import PILOTS, match_best, owned_polygons

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers"
REF = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures"
WATER = {
    "Chicago": A / "data/Chicago/Hydro_20260916.geojson",
    "SP": A / "data/SP/Meio Ambiente/massa_d_agua.gpkg",
}
MODES = ("no_links", "no_links_rail", "no_links_water", "no_links_rail_water")


def rail_source(city, target_crs):
    source = A / "data" / city / "overture_2026_08_19/segment/part_0000.parquet"
    rows = []
    for batch in pq.ParquetFile(source).iter_batches(
        columns=["id", "subtype", "class", "geometry", "level_rules", "rail_flags"],
        batch_size=30000,
    ):
        for row in batch.to_pylist():
            if row["subtype"] == "rail" and row["class"] == "standard_gauge":
                rows.append(row)
    geographic = gpd.GeoDataFrame(rows, geometry=shapely.from_wkb([x["geometry"] for x in rows]), crs=4326)
    metric = geographic.to_crs(target_crs)
    return geographic, metric


def rail_parts(geographic, metric, extraction, target_crs):
    indices = metric.sindex.query(extraction, predicate="intersects")
    parts = []
    for row in geographic.iloc[indices].itertuples():
        parts.extend(boundary_parts(row.geometry, level_rules=row.level_rules, road_flags=row.rail_flags))
    if not parts:
        return []
    return list(gpd.GeoSeries(parts, crs=4326).to_crs(target_crs).geometry.values)


def water_source(city, target_crs):
    return pyogrio.read_dataframe(WATER[city]).to_crs(target_crs)


def water_edges(water, extraction):
    subset = water.iloc[water.sindex.query(extraction, predicate="intersects")]
    if subset.empty:
        return [], shapely.GeometryCollection()
    valid = shapely.make_valid(subset.geometry.values)
    union = shapely.union_all(valid)
    return list(shapely.get_parts(union.boundary)), union


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    for city in ("Chicago", "SP"):
        roads = gpd.read_parquet(A / "work/prepared" / city / "overture_2026_08_19_review_v1/selected_roads.parquet")
        geo_rail, metric_rail = rail_source(city, roads.crs)
        water = water_source(city, roads.crs)
        district_path = next(x[3] for x in PILOTS if x[0] == city)
        districts = gpd.read_parquet(A / "work/prepared" / district_path)
        if city == "SP":
            districts["unit_id"] = "SP:" + districts.district_id.astype(str).str.zfill(2)
        for _, unit, local_id, _, _, _, _ in (x for x in PILOTS if x[0] == city):
            district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
            extraction = district.buffer(250)
            selected = roads.iloc[roads.sindex.query(extraction, predicate="intersects")]
            street = list(selected.loc[selected.subclass.ne("link")].geometry.values)
            rail = rail_parts(geo_rail, metric_rail, extraction, roads.crs)
            shore, water_geometry = water_edges(water, extraction)
            reference = gpd.read_parquet(REF / f"{unit.replace(':', '_')}_reference.parquet")
            variants = {
                "no_links": street,
                "no_links_rail": street + rail,
                "no_links_water": street + shore,
                "no_links_rail_water": street + rail + shore,
            }
            for mode in MODES:
                candidate = owned_polygons(variants[mode], district, extraction, districts, local_id)
                candidate["candidate_id"] = [f"{unit}:{mode}:{i:04d}" for i in range(len(candidate))]
                match_ids, forward = match_best(candidate, reference, "reference_id")
                candidate["best_reference_id"] = match_ids
                candidate["best_reference_iou"] = forward
                _, backward = match_best(reference, candidate, "candidate_id")
                candidate["area_m2"] = candidate.geometry.area
                candidate["water_overlap_fraction"] = [
                    g.intersection(water_geometry).area / g.area if g.area else 0
                    for g in candidate.geometry
                ]
                candidate.to_parquet(OUT / f"{unit.replace(':', '_')}_{mode}.parquet")
                summaries.append({
                    "unit_id": unit, "boundary_mode": mode,
                    "candidate_count": len(candidate), "reference_count": len(reference),
                    "candidate_share_best_iou_ge_050": float(np.mean(forward >= .5)),
                    "reference_share_best_iou_ge_050": float(np.mean(backward >= .5)),
                    "candidate_median_best_iou": float(np.median(forward)),
                    "reference_median_best_iou": float(np.median(backward)),
                    "candidate_water_majority_count": int((candidate.water_overlap_fraction > .5).sum()),
                    "rail_boundary_part_count": len(rail),
                    "rail_boundary_length_m": sum(g.length for g in rail),
                    "water_edge_part_count": len(shore),
                    "water_edge_length_m": sum(g.length for g in shore),
                    "status": "diagnostic_only_not_accepted_M3_M4",
                })
                print(unit, mode, len(candidate), flush=True)
    pd.DataFrame(summaries).to_csv(OUT / "paired_barrier_sensitivity.csv", index=False)


if __name__ == "__main__":
    main()
