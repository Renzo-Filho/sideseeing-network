"""Link frozen visual sketches and obvious highway islands to the inventory."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import shapely
from shapely.geometry import Polygon

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import pixel_point

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
INPUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
OUT = A / "results/Chicago/chicago_m3_candidate_v1_2026_09_26"
HIGHWAY_ISLANDS = {f"CHI_49_1_P{i:02d}" for i in range(5,14)}


def main():
    tiles = {t["tile_id"]:t for t in json.loads((INPUT / "tile_selection.json").read_text())["tiles"]}
    refs = json.loads((INPUT / "visual_reference.json").read_text())
    candidates = pd.read_csv(OUT / "component_inventory.csv")
    candidates = candidates.loc[candidates.diagnostic_candidate].copy()
    shapes = {r.component_id:shapely.from_wkt(r.geometry_wkt) for r in candidates.itertuples()}
    match = {}
    for ref in refs["positive_polygons"]:
        geom = Polygon([pixel_point(tiles[ref["tile_id"]], xy).coords[0] for xy in ref["pixel_ring"]])
        available = [(key,g) for key,g in shapes.items() if key.startswith(ref["tile_id"] + "_")]
        best, best_geom = max(available, key=lambda item:item[1].intersection(geom).area)
        assert best_geom.intersection(geom).area > 0
        assert best not in match, f"two sketches matched {best}"
        match[best] = ref["id"]
    assert not HIGHWAY_ISLANDS.intersection(match)
    review = []
    for r in candidates.itertuples():
        if r.component_id in match:
            status, basis = "sketched_positive", "frozen imagery sketch; rough boundary"
        elif r.component_id in HIGHWAY_ISLANDS:
            status, basis = "nonblock_highway_island", "image review: grassy or wooded land within freeway/ramp complex"
        else:
            status, basis = "unadjudicated", "requires independent street-boundary review"
        review.append({"component_id":r.component_id, "tile_id":r.tile_id,
                       "status":status, "reference_id":match.get(r.component_id),
                       "area_m2":r.area_m2, "basis":basis})
    pd.DataFrame(review).to_csv(OUT / "inventory_review.csv", index=False)
    summary = {"tile_contained_candidates":len(review),
               "matched_frozen_positive_sketches":len(match),
               "visually_obvious_highway_islands":len(HIGHWAY_ISLANDS),
               "unadjudicated_candidates":sum(r["status"] == "unadjudicated" for r in review),
               "minimum_obvious_false_candidate_fraction":len(HIGHWAY_ISLANDS)/len(review),
               "interpretation":"Targeted candidate audit, not precision/recall: positive sketches are incomplete, same analyst reviewed highway islands after seeing candidate outlines, and no complete missed-block inventory exists."}
    (OUT / "inventory_review_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
