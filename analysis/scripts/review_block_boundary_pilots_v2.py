"""Compare paired M3/M4 boundary-network sensitivities on eight pilots.

Includes whole-segment and interval-aware source-rule diagnostics. The outputs
are not accepted physical blocks.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq
import shapely

from harmonization.roads import enclosure_polygons, shape_metrics
from harmonization.geometry import largest_overlap
from harmonization.road_intervals import boundary_parts


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2"
PILOTS = {
    "Chicago": ("CHI", ["24", "28", "30", "32", "76"],
                "Chicago/chi_local_2026_09_16_v1/districts.parquet"),
    "SP": ("SP", ["10", "30", "35"],
           "SP/sp_prep_2026_09_10_v3/N02/districts.parquet"),
}


def has_bridge_or_tunnel(flags):
    return any("is_bridge" in item.get("values", []) or "is_tunnel" in item.get("values", [])
               for item in flags) if flags is not None else False


def source_properties(city, ids):
    """Read source interval rules for selected streets only."""
    source = A / "data" / city / "overture_2026_08_19/segment/part_0000.parquet"
    result = {}
    for batch in pq.ParquetFile(source).iter_batches(
        columns=["id", "subclass", "subclass_rules", "level_rules", "road_flags"],
        batch_size=30000,
    ):
        for row in batch.to_pylist():
            if row["id"] in ids:
                result[row["id"]] = row
    missing = ids - result.keys()
    if missing:
        raise ValueError(f"{city}: {len(missing)} selected roads absent from source")
    return result


def main():
    output = []
    for city, (prefix, ids, district_path) in PILOTS.items():
        roads = gpd.read_parquet(A / "work/prepared" / city / "overture_2026_08_19_review_v1/selected_roads.parquet")
        props = source_properties(city, set(roads.id))
        districts = gpd.read_parquet(A / "work/prepared" / district_path)
        if city == "SP":
            districts["unit_id"] = "SP:" + districts.district_id.astype(str).str.zfill(2)
        for local_id in ids:
            unit_id = f"{prefix}:{local_id}"
            geometry = districts.loc[districts.unit_id.eq(unit_id)].geometry.item()
            extraction = geometry.buffer(250)
            selected = roads.iloc[roads.sindex.query(extraction, predicate="intersects")].copy()
            variants = {
                "all_mapped_streets": selected,
                "without_links": selected.loc[selected.subclass.ne("link")],
            }
            variants["without_links_bridges_tunnels"] = variants["without_links"].loc[
                ~variants["without_links"].road_flags.map(has_bridge_or_tunnel)
            ]
            parts = []
            for row in selected.itertuples():
                raw = props[row.id]
                parts.extend(boundary_parts(
                    row.geometry, subclass=raw["subclass"],
                    subclass_rules=raw["subclass_rules"],
                    level_rules=raw["level_rules"], road_flags=raw["road_flags"],
                ))
            variants["interval_aware_candidate"] = gpd.GeoDataFrame(
                geometry=parts, crs=roads.crs
            )
            for mode, lines in variants.items():
                polygons = enclosure_polygons(lines.geometry.values)
                if len(polygons):
                    polygons = polygons[shapely.intersects(polygons, geometry) &
                                        shapely.covers(extraction, polygons)]
                intersecting_count = len(polygons)
                if len(polygons):
                    objects = gpd.GeoDataFrame(geometry=polygons, crs=districts.crs)
                    owners = largest_overlap(objects, districts)
                    polygons = polygons[owners.astype(str).eq(str(local_id)).to_numpy()]
                metrics = shape_metrics(polygons) if len(polygons) else pd.DataFrame()
                output.append({
                    "unit_id": unit_id, "boundary_mode": mode,
                    "road_segments_in_extraction": len(lines),
                    "source_road_segments_in_extraction": len(selected),
                    "whole_enclosures_intersecting": intersecting_count,
                    "whole_enclosures_owned": len(metrics),
                    "narrow_under_6m": int((metrics.rectangle_min_width_m < 6).sum()) if len(metrics) else 0,
                    "large_over_1km2": int((metrics.area_m2 > 1e6).sum()) if len(metrics) else 0,
                    "median_area_m2": metrics.area_m2.median() if len(metrics) else None,
                    "median_compactness": metrics.compactness.median() if len(metrics) else None,
                    "median_elongation": metrics.elongation.median() if len(metrics) else None,
                    "status": "diagnostic_only_not_accepted_M3_M4",
                })
            print(unit_id, "four boundary modes complete", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output).to_csv(OUT / "paired_boundary_sensitivity.csv", index=False)
    municipal = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N06/blocks.parquet")
    references = []
    for local_id in PILOTS["SP"][1]:
        q = municipal.loc[municipal.district_id.eq(local_id) & municipal.eligible_type]
        references.append({"unit_id": f"SP:{local_id}", "municipal_quadra_count": len(q),
                           "municipal_quadra_median_area_m2": q.geometry.area.median(),
                           "reference_role": "city_specific_diagnostic_not_common_input"})
    pd.DataFrame(references).to_csv(OUT / "sp_quadra_reference.csv", index=False)


if __name__ == "__main__":
    main()
