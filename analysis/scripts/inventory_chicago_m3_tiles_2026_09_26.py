"""Inventory tile-contained ROW land components under a declared diagnostic rule."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import shapely
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape, box
from shapely.ops import transform

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries, components

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
INPUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
WORK = A / "work/chicago_m3_fresh_tiles_2026_09_26"
OUT = A / "results/Chicago/chicago_m3_candidate_v1_2026_09_26"
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def lake_shape(tile_id):
    path = WORK / f"{tile_id}_cook_lake.geojson"
    if not path.exists():
        return shapely.GeometryCollection()
    return shapely.union_all([shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                              for f in json.loads(path.read_text())["features"]])


def main():
    tiles = json.loads((INPUT / "tile_selection.json").read_text())["tiles"]
    rows = []
    OUT.mkdir(parents=True, exist_ok=True)
    for tile in tiles:
        tile_id, unit = tile["tile_id"], tile["unit_id"]
        row = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        alley = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 5)
        lake = lake_shape(tile_id)
        mask = shapely.union_all([shapely.union_all([row, edge]).difference(alley.buffer(1)), lake])
        area, parts = components(tile, mask)
        h = tile["half_width_m"]
        fig, ax = plt.subplots(figsize=(8, 8), dpi=115)
        ax.imshow(Image.open(WORK / f"{tile_id}_raw.jpg"),
                  extent=[tile["x"]-h, tile["x"]+h, tile["y"]-h, tile["y"]+h])
        for ix, part in enumerate(sorted(parts, key=lambda p: p.area, reverse=True), 1):
            is_closed = not part.boundary.intersects(area.boundary)
            eligible = is_closed and part.area >= 1000
            rows.append({"tile_id": tile_id, "component_id": f"{tile_id}_P{ix:02d}",
                         "area_m2": part.area, "perimeter_m": part.length,
                         "compactness": 4*math.pi*part.area/part.length**2,
                         "tile_contained": is_closed, "diagnostic_candidate": eligible,
                         "centroid_x": part.centroid.x, "centroid_y": part.centroid.y,
                         "geometry_wkt": part.wkt})
            if eligible:
                xx, yy = part.exterior.xy
                ax.plot(xx, yy, color="cyan", linewidth=1.1)
                ax.text(part.representative_point().x, part.representative_point().y, str(ix),
                        color="black", ha="center", va="center", fontsize=8,
                        bbox={"facecolor":"yellow", "alpha":.85, "pad":1})
        ax.set(xlim=(tile["x"]-h,tile["x"]+h), ylim=(tile["y"]-h,tile["y"]+h),
               title=f"{tile_id}: tile-contained ≥1000 m² components")
        ax.set_axis_off()
        fig.savefig(OUT / f"{tile_id}_inventory.png", bbox_inches="tight")
        plt.close(fig)
    data = pd.DataFrame(rows)
    data.to_csv(OUT / "component_inventory.csv", index=False)
    summary = {"tiles":len(tiles), "all_components":len(data),
               "tile_contained_components":int(data.tile_contained.sum()),
               "diagnostic_candidates":int(data.diagnostic_candidate.sum()),
               "candidate_counts_by_tile":data.groupby("tile_id").diagnostic_candidate.sum().astype(int).to_dict(),
               "declared_rule":"Cook active ROW + ordinary Road Edge + available Cook Lake masks; remove mapped alley buffer 1m; retain tile-contained land polygons >=1000 m². This is a diagnostic rule, not final Chicago construction."}
    (OUT / "inventory_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
