"""Compare Chicago physical-block candidates with frozen complete small-zone refs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import momepy
import numpy as np
import pandas as pd
import shapely
from PIL import Image
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Polygon, box

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
WORK = A / "work/chicago_m3_complete_zone_pilot_v1_2026_09_26"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
ALLEY_CONFIG = A / "config/chicago_m3_alley_repair_v2.json"
HALO_M = 450
IOU_CUTOFF = .5
HOLDOUT = "CHI_49_Z1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_polygon(zone: dict, ring: list[list[int]]) -> Polygon:
    x, y, h, n = zone["x"], zone["y"], zone["half_width_m"], zone["image_size_px"]
    return Polygon([(x-h+px*2*h/n, y+h-py*2*h/n) for px, py in ring])


def core_polygon(zone: dict, bounds: list[int]) -> Polygon:
    left, top, right, bottom = bounds
    return pixel_polygon(zone, [[left, top], [right, top], [right, bottom], [left, bottom]])


def parts(geom) -> list:
    return [p for p in shapely.get_parts(shapely.make_valid(geom))
            if p.geom_type == "Polygon" and p.area > 0]


def compactness(geom) -> float:
    return 4*math.pi*geom.area/geom.length**2


def prepare_faces(zone: dict, road_lines: gpd.GeoDataFrame, masks: dict) -> tuple[dict, Polygon]:
    x, y = zone["x"], zone["y"]
    halo = box(x-HALO_M, y-HALO_M, x+HALO_M, y+HALO_M)
    subset = road_lines.iloc[road_lines.sindex.query(halo, predicate="intersects")]
    faces = {"municipal_momepy": [p for p in momepy.enclosures(subset.geometry, limit=halo).geometry
                                 if p.geom_type == "Polygon" and p.area > 0]}
    for method, mask in masks.items():
        faces[method] = parts(halo.difference(mask))
    return faces, halo


def match_reference(refs: list[dict], geoms: list, halo: Polygon, core: Polygon) -> tuple[list[dict], dict]:
    usable = [(j, g) for j, g in enumerate(geoms)
              if g.intersects(core) and not g.boundary.intersects(halo.boundary)]
    overlap = np.zeros((len(refs), len(usable)))
    for i, ref in enumerate(refs):
        for jj, (_, candidate) in enumerate(usable):
            area = ref["geometry"].intersection(candidate).area
            if area > 0:
                overlap[i, jj] = area/ref["geometry"].union(candidate).area
    matched = {}
    if overlap.size:
        for i, jj in zip(*linear_sum_assignment(-overlap)):
            if overlap[i, jj] >= IOU_CUTOFF:
                matched[i] = (usable[jj][0], float(overlap[i, jj]))
    rows = []
    for i, ref in enumerate(refs):
        best_jj = int(overlap[i].argmax()) if len(usable) else None
        best_index = usable[best_jj][0] if best_jj is not None else None
        match = matched.get(i)
        rows.append({"reference_id": ref["id"], "matched": match is not None,
                     "matched_candidate_index": match[0] if match else None,
                     "matched_iou": match[1] if match else None,
                     "best_usable_candidate_index": best_index,
                     "best_usable_iou": float(overlap[i, best_jj]) if best_jj is not None else 0,
                     "reference_area_m2": ref["geometry"].area,
                     "reference_compactness": compactness(ref["geometry"]),
                     "matched_area_m2": geoms[match[0]].area if match else None,
                     "matched_compactness": compactness(geoms[match[0]]) if match else None,
                     "candidate_overlap_ge_0_1_count": int((overlap[i] >= .1).sum())})
    in_core = {j for j, g in usable if core.covers(g.representative_point())}
    matched_indices = {value[0] for value in matched.values()}
    unmatched_in_core = in_core - matched_indices
    summary = {"reference_count": len(refs), "candidate_faces_in_core": len(in_core),
               "matched_reference_count": len(matched), "unmatched_reference_count": len(refs)-len(matched),
               "unmatched_candidate_count": len(unmatched_in_core),
               "provisional_recall": len(matched)/len(refs) if refs else None,
               "provisional_precision": len(matched_indices & in_core)/len(in_core) if in_core else None,
               "unmatched_candidate_indices": sorted(unmatched_in_core)}
    return rows, summary


def plot_zone(zone: dict, core: Polygon, refs: list[dict], faces: list, halo: Polygon, method: str) -> None:
    x, y, h = zone["x"], zone["y"], zone["half_width_m"]
    fig, ax = plt.subplots(figsize=(9, 9), dpi=115)
    ax.imshow(Image.open(WORK / f"{zone['zone_id']}_ortho.jpg"), extent=(x-h, x+h, y-h, y+h))
    bx, by = core.exterior.xy
    ax.plot(bx, by, color="cyan", linestyle="--", linewidth=1.3)
    for g in faces:
        if not g.intersects(core) or g.boundary.intersects(halo.boundary):
            continue
        line = g.exterior.intersection(box(x-h, y-h, x+h, y+h))
        for seg in shapely.get_parts(line):
            if seg.geom_type in ("LineString", "LinearRing"):
                xx, yy = seg.xy
                ax.plot(xx, yy, color="yellow", linewidth=.8)
    for ref in refs:
        xx, yy = ref["geometry"].exterior.xy
        ax.plot(xx, yy, color="magenta", linewidth=1.2)
    ax.set(xlim=(x-h, x+h), ylim=(y-h, y+h), title=f"{zone['zone_id']} {method}: magenta reference, yellow candidate")
    ax.set_axis_off()
    fig.savefig(OUT / f"{zone['zone_id']}_{method}_overlay.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdout-only", action="store_true")
    args = parser.parse_args()
    selection = json.loads((OUT / "zone_selection.json").read_text())
    alley_config = json.loads(ALLEY_CONFIG.read_text())
    assert alley_config["chosen_alley_buffer_m"] == 3
    reference_path = OUT / "visual_reference_v1.json"
    freeze = json.loads((OUT / "reference_freeze.json").read_text())
    assert digest(reference_path) == freeze["sha256"][str(reference_path.relative_to(ROOT))]
    reference = json.loads(reference_path.read_text())
    zones = {z["zone_id"]: z for z in selection["zones"]}
    cores = {c["zone_id"]: c for c in reference["cores"]}
    roads = gpd.read_parquet(ROADS)
    result_rows, inventory_rows, method_rows = [], [], []
    for zone_id, zone in zones.items():
        if (zone_id == HOLDOUT) != args.holdout_only:
            continue
        core = core_polygon(zone, cores[zone_id]["bounds_px"])
        refs = [{**r, "geometry": pixel_polygon(zone, r["pixel_ring"])}
                for r in reference["positive_polygons"] if r["zone_id"] == zone_id]
        unit = zone["unit_id"]
        row = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        alley = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 5)
        masks = {"cook_row_raw": row,
                 "cook_row_alley_open": row.difference(alley.buffer(1)),
                 "cook_row_edge_alley_open": shapely.union_all([row, edge]).difference(alley.buffer(1)),
                 "cook_row_alley_open_3m": row.difference(alley.buffer(3)),
                 "cook_row_edge_alley_open_3m": shapely.union_all([row, edge]).difference(alley.buffer(3))}
        faces, halo = prepare_faces(zone, roads, masks)
        for method, geoms in faces.items():
            matched_rows, summary = match_reference(refs, geoms, halo, core)
            for item in matched_rows:
                result_rows.append({"zone_id": zone_id, "method": method, **item})
            method_rows.append({"zone_id": zone_id, "method": method, **summary})
            for j, g in enumerate(geoms):
                if core.covers(g.representative_point()) and not g.boundary.intersects(halo.boundary):
                    inventory_rows.append({"zone_id": zone_id, "method": method, "candidate_index": j,
                                           "area_m2": g.area, "compactness": compactness(g),
                                           "geometry_wkt": g.wkt})
            plot_zone(zone, core, refs, geoms, halo, method)
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = "holdout" if args.holdout_only else "development"
    pd.DataFrame(result_rows).to_csv(OUT / f"{prefix}_reference_matches.csv", index=False)
    pd.DataFrame(inventory_rows).to_csv(OUT / f"{prefix}_candidate_inventory.csv", index=False)
    pd.DataFrame(method_rows).to_csv(OUT / f"{prefix}_method_summary.csv", index=False)
    output = {"zone_ids": sorted(set(r["zone_id"] for r in result_rows)),
              "reference_count": len({r["reference_id"] for r in result_rows}),
              "iou_match_cutoff": IOU_CUTOFF, "halo_half_width_m": HALO_M,
              "reference_sha256": digest(reference_path),
              "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (ROADS, OUT / "zone_selection.json", ALLEY_CONFIG)},
              "method_summary": method_rows,
              "status": "single-analyst candidate-blind but rough small-core reference; diagnostic only",
              "holdout_only": args.holdout_only}
    (OUT / f"{prefix}_summary.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"zones": output["zone_ids"], "references": output["reference_count"],
                      "method_summary": method_rows}, indent=2))


if __name__ == "__main__":
    main()
