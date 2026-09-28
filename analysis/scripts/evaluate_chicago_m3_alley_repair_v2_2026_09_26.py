"""Diagnostic alley-opening width sweep on the frozen valid development cores."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import box

from evaluate_chicago_m3_complete_zones_v1_2026_09_26 import (
    OUT, ROADS, core_polygon, match_reference, parts, pixel_polygon,
)
from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries

WIDTHS = [0, 1, 2, 3, 4, 5, 6, 8, 10, 15]
VALID_ZONES = ["CHI_11_Z1", "CHI_32_Z1"]
HALO_M = 450


def main() -> None:
    selection = {z["zone_id"]: z for z in json.loads((OUT / "zone_selection.json").read_text())["zones"]}
    reference = json.loads((OUT / "visual_reference_v1.json").read_text())
    cores = {c["zone_id"]: c for c in reference["cores"]}
    rows = []
    cases = []
    for zone_id in VALID_ZONES:
        zone = selection[zone_id]
        x, y = zone["x"], zone["y"]
        halo = box(x-HALO_M, y-HALO_M, x+HALO_M, y+HALO_M)
        core = core_polygon(zone, cores[zone_id]["bounds_px"])
        refs = [{**r, "geometry": pixel_polygon(zone, r["pixel_ring"])}
                for r in reference["positive_polygons"] if r["zone_id"] == zone_id]
        unit = zone["unit_id"]
        row = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        alley = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 5)
        for edge_mode, original_mask in (("row", row), ("row_plus_edge", shapely.union_all([row, edge]))):
            for width in WIDTHS:
                mask = original_mask.difference(alley.buffer(width)) if width else original_mask
                geoms = parts(halo.difference(mask))
                match, summary = match_reference(refs, geoms, halo, core)
                rows.append({"zone_id": zone_id, "edge_mode": edge_mode, "alley_buffer_m": width,
                             "removed_mask_area_in_core_m2": original_mask.intersection(core).area-mask.intersection(core).area,
                             **summary})
                for item in match:
                    cases.append({"zone_id": zone_id, "edge_mode": edge_mode, "alley_buffer_m": width,
                                  **item})
    pd.DataFrame(rows).to_csv(OUT / "alley_repair_sweep_summary.csv", index=False)
    pd.DataFrame(cases).to_csv(OUT / "alley_repair_sweep_cases.csv", index=False)
    print(pd.DataFrame(rows)[["zone_id", "edge_mode", "alley_buffer_m", "candidate_faces_in_core",
                              "matched_reference_count", "unmatched_candidate_count"]].to_string(index=False))


if __name__ == "__main__":
    main()
