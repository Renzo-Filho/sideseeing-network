"""Apply frozen 3m alley opening to prior CHI:49 motorway challenge tiles."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import components, source_geometries
from evaluate_chicago_m3_motorway_holdout_2026_09_26 import point

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
SOURCE = A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26"
OUT = A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
SEGMENTS = A / "data/Chicago/overture_2026_08_19/segment/part_0000.parquet"
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
TO_WGS84 = Transformer.from_crs(26916, 4326, always_xy=True).transform


def motorway_corridor(tiles: dict) -> object:
    corners = [TO_WGS84(t["x"]+dx, t["y"]+dy) for t in tiles.values()
               for dx in (-300, 300) for dy in (-300, 300)]
    west, south, east, north = (min(p[0] for p in corners), min(p[1] for p in corners),
                                max(p[0] for p in corners), max(p[1] for p in corners))
    table = pq.read_table(SEGMENTS, columns=["class", "geometry", "bbox"])
    geoms = [transform(TO_METRIC, shapely.from_wkb(geom))
             for cls, geom, bbox in zip(table["class"].to_pylist(),
                                        table["geometry"].to_pylist(), table["bbox"].to_pylist())
             if cls == "motorway" and geom is not None and bbox is not None
             and bbox["xmin"] <= east and bbox["xmax"] >= west
             and bbox["ymin"] <= north and bbox["ymax"] >= south]
    return shapely.union_all(geoms).buffer(40)


def main() -> None:
    cfg = json.loads((A / "config/chicago_m3_alley_repair_v2.json").read_text())
    assert cfg["chosen_alley_buffer_m"] == 3
    tiles = {t["tile_id"]: t for t in json.loads((SOURCE / "tile_selection.json").read_text())["tiles"]}
    refs = json.loads((SOURCE / "visual_reference.json").read_text())
    ambiguous = {r["reference_id"] for r in json.loads((SOURCE / "reference_review.json").read_text())["cases"]}
    road = source_geometries("CHI:49", "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
    edge = source_geometries("CHI:49", "road_edge", lambda p: p.get("TYPE") == 1)
    alley = source_geometries("CHI:49", "road_edge", lambda p: p.get("TYPE") == 5)
    mask = shapely.union_all([road, edge]).difference(alley.buffer(3))
    motorway = motorway_corridor(tiles)
    candidate_rows = []
    shapes = {}
    for tile_id, tile in tiles.items():
        extent, pieces = components({**tile, "half_width_m": 240}, mask)
        for j, g in enumerate(sorted(pieces, key=lambda p: p.area, reverse=True), 1):
            if g.area < 1000 or g.boundary.intersects(extent.boundary):
                continue
            cid = f"{tile_id}_P{j:02d}"
            exposure = g.intersection(motorway).area/g.area
            candidate_rows.append({"candidate_id": cid, "tile_id": tile_id, "area_m2": g.area,
                                   "motorway_exposure": exposure, "motorway_flag": exposure >= .3})
            shapes[cid] = g
    candidates = pd.DataFrame(candidate_rows)
    positive = []
    for ref in refs["positive_polygons"]:
        tile_id = ref["tile_id"]
        geom = Polygon([point(tiles[tile_id], pixel).coords[0] for pixel in ref["pixel_ring"]])
        matches = [(k, g) for k, g in shapes.items() if k.startswith(tile_id + "_")]
        if matches:
            cid, g = max(matches, key=lambda item: item[1].intersection(geom).area)
            iou = g.intersection(geom).area/g.union(geom).area
            flag = bool(candidates.loc[candidates.candidate_id.eq(cid), "motorway_flag"].item())
        else:
            cid, iou, flag = None, 0, None
        positive.append({"reference_id": ref["id"], "status": "ambiguous" if ref["id"] in ambiguous else "clear",
                         "matched_candidate": cid, "iou": iou, "motorway_flag": flag})
    negative = []
    for ref in refs["negative_points"]:
        p = point(tiles[ref["tile_id"]], ref["pixel_xy"])
        match = next((k for k, g in shapes.items() if k.startswith(ref["tile_id"] + "_") and g.covers(p)), None)
        flag = bool(candidates.loc[candidates.candidate_id.eq(match), "motorway_flag"].item()) if match else None
        negative.append({"reference_id": ref["id"], "candidate_at_point": match, "motorway_flag": flag})
    pd.DataFrame(candidate_rows).to_csv(OUT / "motorway_3m_candidates.csv", index=False)
    pd.DataFrame(positive).to_csv(OUT / "motorway_3m_positive_comparison.csv", index=False)
    pd.DataFrame(negative).to_csv(OUT / "motorway_3m_negative_comparison.csv", index=False)
    clear = [r for r in positive if r["status"] == "clear"]
    summary = {"tile_count": len(tiles), "candidate_count": len(candidates),
               "motorway_flagged_count": int(candidates.motorway_flag.sum()),
               "clear_positive_count": len(clear),
               "clear_positive_iou_ge_half": sum(r["iou"] >= .5 for r in clear),
               "clear_positive_flagged": sum(r["motorway_flag"] is True for r in clear),
               "negative_point_count": len(negative),
               "negative_points_in_candidates": sum(r["candidate_at_point"] is not None for r in negative),
               "negative_points_in_kept_candidates": sum(r["motorway_flag"] is False for r in negative),
               "status": "selected earlier motorway stress points, not complete reference inventory"}
    (OUT / "motorway_3m_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
