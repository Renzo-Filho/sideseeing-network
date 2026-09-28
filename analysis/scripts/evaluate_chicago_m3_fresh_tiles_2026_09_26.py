"""Compare frozen visual tile references with polygon-first ROW variants."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import shapely
from PIL import Image
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
WORK = A / "work/chicago_m3_fresh_tiles_2026_09_26"
SOURCE = A / "work/chicago_m3_row_land_2026_09_26"
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def source_geometries(unit, source, predicate):
    file = SOURCE / f"{unit.replace(':', '_')}_{source}.geojson"
    features = json.loads(file.read_text())["features"]
    return shapely.union_all([shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                              for f in features if predicate(f["properties"])])


def pixel_point(tile, point):
    x, y, h = tile["x"], tile["y"], tile["half_width_m"]
    return Point(x - h + point[0] * (2*h/800), y + h - point[1] * (2*h/800))


def components(tile, mask):
    h = tile["half_width_m"]
    area = box(tile["x"]-h, tile["y"]-h, tile["x"]+h, tile["y"]+h)
    parts = [p for p in shapely.get_parts(shapely.make_valid(area.difference(mask)))
             if p.geom_type == "Polygon" and p.area > 0]
    return area, parts


def main():
    tiles = {t["tile_id"]: t for t in json.loads((OUT / "tile_selection.json").read_text())["tiles"]}
    reference = json.loads((OUT / "visual_reference.json").read_text())
    states = {}
    for tile_id, tile in tiles.items():
        unit = tile["unit_id"]
        road = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        alley = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 5)
        masks = {"cook_row_raw": road,
                 "cook_row_alley_open": road.difference(alley.buffer(1)),
                 "cook_row_plus_road_edge_alley_open": shapely.union_all([road, edge]).difference(alley.buffer(1))}
        states[tile_id] = {}
        for mode, mask in masks.items():
            area, parts = components(tile, mask)
            states[tile_id][mode] = (area, mask, parts)
    positive_rows = []
    for ref in reference["positive_polygons"]:
        tile_id = ref["tile_id"]
        tile = tiles[tile_id]
        ref_geom = Polygon([pixel_point(tile, xy).coords[0] for xy in ref["pixel_ring"]])
        for mode, (area, mask, parts) in states[tile_id].items():
            best = max(parts, key=lambda p: p.intersection(ref_geom).area)
            overlap = best.intersection(ref_geom).area
            positive_rows.append({"reference_id": ref["id"], "tile_id": tile_id,
                                  "context": ref["context"], "mode": mode,
                                  "reference_area_m2": ref_geom.area,
                                  "best_component_area_m2": best.area,
                                  "best_component_iou": overlap / best.union(ref_geom).area,
                                  "reference_area_covered_fraction": overlap / ref_geom.area,
                                  "component_touches_tile_edge": best.boundary.intersects(area.boundary),
                                  "component_compactness": 4*math.pi*best.area/(best.length**2)})
    negative_rows = []
    for ref in reference["negative_points"]:
        tile_id = ref["tile_id"]
        point = pixel_point(tiles[tile_id], ref["pixel_xy"])
        for mode, (area, mask, parts) in states[tile_id].items():
            match = next((p for p in parts if p.covers(point)), None)
            negative_rows.append({"reference_id": ref["id"], "tile_id": tile_id,
                                  "context": ref["context"], "mode": mode,
                                  "inside_road_mask": mask.covers(point),
                                  "land_component_area_m2": match.area if match is not None else None,
                                  "land_component_touches_tile_edge":
                                      match.boundary.intersects(area.boundary) if match is not None else None})
    pd.DataFrame(positive_rows).to_csv(OUT / "positive_reference_comparison.csv", index=False)
    pd.DataFrame(negative_rows).to_csv(OUT / "negative_reference_comparison.csv", index=False)
    for tile_id in sorted(set(r["tile_id"] for r in reference["positive_polygons"])):
        tile = tiles[tile_id]
        h = tile["half_width_m"]
        extent = [tile["x"]-h, tile["x"]+h, tile["y"]-h, tile["y"]+h]
        im = Image.open(WORK / f"{tile_id}_raw.jpg")
        fig, axes = plt.subplots(1, 2, figsize=(12, 6), dpi=120)
        for ax, mode in zip(axes, ["cook_row_raw", "cook_row_plus_road_edge_alley_open"]):
            ax.imshow(im, extent=extent)
            for ref in reference["positive_polygons"]:
                if ref["tile_id"] != tile_id:
                    continue
                geom = Polygon([pixel_point(tile, xy).coords[0] for xy in ref["pixel_ring"]])
                coords = list(geom.exterior.coords)
                ax.plot([p[0] for p in coords], [p[1] for p in coords], color="red", lw=1.4)
                best = max(states[tile_id][mode][2], key=lambda p: p.intersection(geom).area)
                for p in shapely.get_parts(best):
                    if p.geom_type == "Polygon":
                        coords = list(p.exterior.coords)
                        ax.plot([q[0] for q in coords], [q[1] for q in coords], color="lime", lw=1)
            ax.set(xlim=extent[:2], ylim=extent[2:], title=mode)
            ax.set_axis_off()
        fig.suptitle(tile_id + ": red independent sketch, green best ROW land component")
        fig.savefig(OUT / f"{tile_id}_comparison.png")
        plt.close(fig)
    pos = pd.DataFrame(positive_rows)
    summary = {"reference_positive_polygons": len(reference["positive_polygons"]),
               "reference_negative_points": len(reference["negative_points"]),
               "positive_median_iou_by_mode": pos.groupby("mode").best_component_iou.median().to_dict(),
               "positive_iou_ge_0_5_by_mode": pos.assign(pass_iou=pos.best_component_iou.ge(.5)).groupby("mode").pass_iou.sum().to_dict(),
               "status": "single-analyst rough imagery sketches; small source-blind diagnostic, not citywide acceptance"}
    (OUT / "validation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
