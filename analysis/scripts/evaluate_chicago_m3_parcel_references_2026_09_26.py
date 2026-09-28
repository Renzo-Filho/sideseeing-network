"""Compare Cook BaseParcel PIN groups with frozen, rough imagery references."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
from shapely.geometry import Polygon, box

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import pixel_point

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
INPUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
OUT = A / "results/Chicago/chicago_m3_candidate_v1_2026_09_26"
PARCELS = A / "data/Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024"


def main():
    tiles = {t["tile_id"]: t for t in json.loads((INPUT / "tile_selection.json").read_text())["tiles"]}
    refs = json.loads((INPUT / "visual_reference.json").read_text())
    # The tile boxes plus a 50 m margin avoid cutting nearby PIN groups at the tile edge.
    roi = shapely.union_all([box(t["x"]-210, t["y"]-210, t["x"]+210, t["y"]+210)
                             for t in tiles.values()])
    chunks = []
    files = sorted(PARCELS.glob("part_*.parquet"))
    for file in files:
        table = pq.read_table(file, columns=["geometry", "PIN10", "PARCELTYPE", "OBJECTID"])
        attrs = table.select(["PIN10", "PARCELTYPE", "OBJECTID"]).to_pandas()
        is_base = attrs.PARCELTYPE.eq("BaseParcel").to_numpy()
        if not is_base.any():
            continue
        geoms = shapely.from_wkb(table["geometry"].to_pylist())
        selected = is_base & np.asarray(shapely.intersects(geoms, roi), dtype=bool)
        if selected.any():
            part = attrs.loc[selected].copy()
            part["geometry"] = geoms[selected]
            chunks.append(part)
    parcels = pd.concat(chunks, ignore_index=True)
    parcels["tax_group"] = parcels.PIN10.str[:7]
    group_shapes = {key: shapely.union_all(group.geometry.values)
                    for key, group in parcels.groupby("tax_group") if isinstance(key, str)}
    rows = []
    for ref in refs["positive_polygons"]:
        tile = tiles[ref["tile_id"]]
        geom = Polygon([pixel_point(tile, xy).coords[0] for xy in ref["pixel_ring"]])
        overlaps = {key: g.intersection(geom).area for key, g in group_shapes.items()
                    if g.intersects(geom)}
        overlaps = {key: a for key, a in overlaps.items() if a > 0}
        dominant = max(overlaps, key=overlaps.get) if overlaps else None
        group = group_shapes.get(dominant)
        rows.append({
            "reference_id": ref["id"], "tile_id": ref["tile_id"], "context": ref["context"],
            "reference_area_m2": geom.area, "groups_with_positive_overlap": len(overlaps),
            "dominant_group": dominant, "dominant_group_overlap_m2": overlaps.get(dominant, 0),
            "dominant_group_coverage_of_reference": overlaps.get(dominant, 0) / geom.area,
            "all_group_coverage_of_reference": sum(overlaps.values()) / geom.area,
            "dominant_group_iou": geom.intersection(group).area / geom.union(group).area if group is not None else 0,
            "dominant_group_area_m2": group.area if group is not None else None,
            "reference_to_group_area_ratio": geom.area / group.area if group is not None and group.area else None,
        })
    negative = []
    for ref in refs["negative_points"]:
        point = pixel_point(tiles[ref["tile_id"]], ref["pixel_xy"])
        matches = [key for key, g in group_shapes.items() if g.covers(point)]
        negative.append({"reference_id": ref["id"], "context": ref["context"],
                         "tax_group_at_point": matches[0] if matches else None,
                         "tax_group_area_m2": group_shapes[matches[0]].area if matches else None})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "parcel_positive_comparison.csv", index=False)
    pd.DataFrame(negative).to_csv(OUT / "parcel_negative_comparison.csv", index=False)
    candidate_rows = []
    inventory = pd.read_csv(OUT / "component_inventory.csv")
    for candidate in inventory.loc[inventory.diagnostic_candidate].itertuples():
        geom = shapely.from_wkt(candidate.geometry_wkt)
        overlaps = {key:g.intersection(geom).area for key,g in group_shapes.items() if g.intersects(geom)}
        overlaps = {key:a for key,a in overlaps.items() if a > 0}
        best = max(overlaps, key=overlaps.get) if overlaps else None
        candidate_rows.append({"component_id":candidate.component_id,
                               "tax_groups":len(overlaps), "dominant_tax_group":best,
                               "dominant_group_coverage_of_candidate":overlaps.get(best,0)/geom.area,
                               "all_group_coverage_of_candidate":sum(overlaps.values())/geom.area})
    pd.DataFrame(candidate_rows).to_csv(OUT / "parcel_candidate_support.csv", index=False)
    summary = {"part_files_scanned": len(files), "base_parcels_retained": len(parcels),
               "tax_groups_retained": len(group_shapes),
               "reference_count": len(rows),
               "median_dominant_group_coverage": float(pd.DataFrame(rows).dominant_group_coverage_of_reference.median()),
               "median_dominant_group_iou": float(pd.DataFrame(rows).dominant_group_iou.median()),
               "negative_points_with_tax_group": sum(bool(n["tax_group_at_point"]) for n in negative),
               "caveat": "Group union is truncated to parcels in 50 m expanded reference tiles; seven-digit PIN may denote tax block or quarter section."}
    (OUT / "parcel_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
