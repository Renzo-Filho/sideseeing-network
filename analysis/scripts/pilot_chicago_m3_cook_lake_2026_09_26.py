"""Bounded Cook Lake polygon check for fresh Loop and O'Hare water controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
import shapely
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
WORK = A / "work/chicago_m3_fresh_tiles_2026_09_26"
LAYER = "https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/8"
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def get(params):
    response = requests.get(LAYER + "/query", params=params, timeout=90,
                            headers={"User-Agent": "sideseeing-network bounded Chicago M3 water pilot"})
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    tiles = {t["tile_id"]: t for t in json.loads((OUT / "tile_selection.json").read_text())["tiles"]}
    refs = [r for r in json.loads((OUT / "visual_reference.json").read_text())["negative_points"]
            if r["tile_id"] in ["CHI_32_2", "CHI_76_2"]]
    summaries = []
    for ref in refs:
        tile = tiles[ref["tile_id"]]
        tile_id = ref["tile_id"]
        x, y, h = tile["x"], tile["y"], tile["half_width_m"]
        raw_path = WORK / f"{tile_id}_cook_lake.geojson"
        receipt_path = WORK / f"{tile_id}_cook_lake_receipt.json"
        if args.fetch and not raw_path.exists():
            bounds = transform(TO_LONLAT, shapely.box(x-h, y-h, x+h, y+h)).bounds
            query = {"where": "1=1", "geometry": ",".join(f"{v:.8f}" for v in bounds),
                     "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                     "spatialRel": "esriSpatialRelIntersects"}
            ids = sorted(get({**query, "returnIdsOnly": "true", "f": "json"}).get("objectIds") or [])
            features = []
            for start in range(0, len(ids), 150):
                result = get({"objectIds": ",".join(map(str, ids[start:start+150])),
                              "outFields": "OBJECTID,Type,Name,Source,Source_Year,County,WaterPresent",
                              "returnGeometry": "true", "f": "geojson"})
                features.extend(result.get("features", []))
            unique = {int(f["properties"]["OBJECTID"]): f for f in features}
            if set(unique) != set(ids):
                raise RuntimeError(f"Incomplete Cook Lake retrieval in {tile_id}")
            raw_path.write_text(json.dumps({"type": "FeatureCollection", "features": [unique[i] for i in ids]},
                                           separators=(",", ":")))
            receipt_path.write_text(json.dumps({"source": LAYER, "tile_id": tile_id,
                                                "ids_query": query, "features": len(ids),
                                                "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                                                "raw_path": str(raw_path.relative_to(ROOT)),
                                                "retrieved_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        if not raw_path.exists():
            raise FileNotFoundError("Run --fetch first")
        receipt = json.loads(receipt_path.read_text())
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != receipt["sha256"]:
            raise RuntimeError(f"Cache hash changed for {tile_id}")
        features = json.loads(raw_path.read_text())["features"]
        px, py = ref["pixel_xy"]
        point = Point(x-h+px*2*h/800, y+h-py*2*h/800)
        matching = [f["properties"] for f in features
                    if shapely.make_valid(transform(TO_METRIC, shape(f["geometry"]))).covers(point)]
        summaries.append({"reference_id": ref["id"], "tile_id": tile_id,
                          "retrieved_features": len(features), "cook_lake_contains": bool(matching),
                          "matching_features": matching})
    result = {"source": LAYER, "point_checks": summaries,
              "status": "bounded water control; no all-Chicago completeness claim"}
    (OUT / "cook_lake_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
