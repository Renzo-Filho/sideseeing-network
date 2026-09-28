"""Measure Overture motorway exposure around tile-contained land components."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
INPUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
OUT = A / "results/Chicago/chicago_m3_candidate_v1_2026_09_26"
SEGMENTS = A / "data/Chicago/overture_2026_08_19/segment/part_0000.parquet"
TO_WGS84 = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def main():
    tiles = json.loads((INPUT / "tile_selection.json").read_text())["tiles"]
    boxes = []
    for t in tiles:
        h = t["half_width_m"] + 100
        corners = [TO_WGS84(t["x"]+dx, t["y"]+dy) for dx in (-h,h) for dy in (-h,h)]
        boxes.append((min(p[0] for p in corners), min(p[1] for p in corners),
                      max(p[0] for p in corners), max(p[1] for p in corners)))
    table = pq.read_table(SEGMENTS, columns=["class", "geometry", "bbox"])
    classes = table["class"].to_pylist()
    bboxes = table["bbox"].to_pylist()
    select = np.array([c == "motorway" and b is not None and
                       any(b["xmin"] <= e and b["xmax"] >= w and b["ymin"] <= n and b["ymax"] >= s
                           for w,s,e,n in boxes) for c,b in zip(classes,bboxes)], dtype=bool)
    geoms = [transform(TO_METRIC, shapely.from_wkb(wkb)) for wkb, keep in
             zip(table["geometry"].to_pylist(),select) if keep and wkb is not None]
    highway = shapely.union_all(geoms)
    inventory = pd.read_csv(OUT / "component_inventory.csv")
    inventory = inventory.loc[inventory.diagnostic_candidate].copy()
    rows = []
    for r in inventory.itertuples():
        geom = shapely.from_wkt(r.geometry_wkt)
        row = {"component_id":r.component_id, "tile_id":r.tile_id,
               "area_m2":r.area_m2,
               "motorway_distance_m": geom.distance(highway)}
        for width in (15, 25, 40):
            corridor = highway.buffer(width)
            row[f"boundary_fraction_within_{width}m_motorway"] = geom.boundary.intersection(corridor).length / geom.length
            row[f"area_fraction_within_{width}m_motorway"] = geom.intersection(corridor).area / geom.area
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "motorway_context.csv", index=False)
    summary = {"overture_motorway_segments_near_tiles":len(geoms),
               "candidates":len(rows),
               "method":"Overture 2026-08-19 motorway/link centerline corridor; exposure diagnostic only, no exclusion threshold."}
    (OUT / "motorway_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
