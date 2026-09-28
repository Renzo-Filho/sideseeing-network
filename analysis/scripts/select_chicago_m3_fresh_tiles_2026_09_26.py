"""Freeze independent Chicago block review locations and cache orthophoto tiles."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import requests
import shapely
from shapely.geometry import Point
from pilot_chicago_m3_row_land_2026_09_26 import case_records

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
WORK = A / "work/chicago_m3_fresh_tiles_2026_09_26"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
UNITS = ["CHI:11", "CHI:49", "CHI:57", "CHI:63", "CHI:32", "CHI:76"]
SEED = 20260926
HALF_WIDTH_M = 160
SIZE = 800
IMAGE_SERVICE = "https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer"


def select():
    rng = np.random.default_rng(SEED)
    districts = gpd.read_parquet(DISTRICTS)
    selected = []
    for unit in UNITS:
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        interior = district.buffer(-HALF_WIDTH_M)
        if interior.is_empty:
            interior = district
        earlier = [shapely.from_wkt(c["geometry_wkt"]).centroid
                   for c in case_records() if c["unit_id"] == unit]
        picks = []
        for _ in range(10000):
            bounds = interior.bounds
            point = Point(rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3]))
            if not interior.covers(point):
                continue
            if any(point.distance(p) < 500 for p in picks):
                continue
            if any(point.distance(p) < 280 for p in earlier):
                continue
            picks.append(point)
            if len(picks) == 2:
                break
        if len(picks) != 2:
            raise RuntimeError(f"Could not select two independent points in {unit}")
        for n, point in enumerate(picks, 1):
            selected.append({"tile_id": f"{unit.replace(':', '_')}_{n}", "unit_id": unit,
                             "x": point.x, "y": point.y, "half_width_m": HALF_WIDTH_M,
                             "selection_rule": "fixed-seed uniform district interior; >=500m apart; >=280m from prior saved case centers; no block candidate, reference polygon, OSM or imagery used"})
    return selected


def fetch(tile):
    name = tile["tile_id"]
    image_path = WORK / f"{name}_raw.jpg"
    receipt_path = WORK / f"{name}_receipt.json"
    if image_path.exists() and receipt_path.exists():
        r = json.loads(receipt_path.read_text())
        if hashlib.sha256(image_path.read_bytes()).hexdigest() != r["sha256"]:
            raise RuntimeError(f"Cache hash changed: {image_path}")
        return r
    x, y, h = tile["x"], tile["y"], tile["half_width_m"]
    query = {"bbox": f"{x-h:.3f},{y-h:.3f},{x+h:.3f},{y+h:.3f}",
             "bboxSR": "26916", "imageSR": "26916", "size": f"{SIZE},{SIZE}",
             "format": "jpg", "f": "image"}
    response = requests.get(IMAGE_SERVICE + "/exportImage", params=query, timeout=90,
                            headers={"User-Agent": "sideseeing-network Chicago M3 independent block reference pilot"})
    response.raise_for_status()
    if not response.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(f"Unexpected image response: {response.text[:200]}")
    image_path.write_bytes(response.content)
    r = {"tile_id": name, "source": IMAGE_SERVICE, "query": query,
         "retrieved_utc": datetime.now(timezone.utc).isoformat(),
         "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
         "bytes": image_path.stat().st_size, "raw_path": str(image_path.relative_to(ROOT))}
    receipt_path.write_text(json.dumps(r, indent=2) + "\n")
    return r


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    path = OUT / "tile_selection.json"
    if path.exists():
        saved = json.loads(path.read_text())
        if saved["tiles"] != select():
            raise RuntimeError("Frozen tile selection differs from code")
    else:
        saved = {"seed": SEED, "source_blind_to": ["block candidates", "Census blocks", "imagery", "OSM"],
                 "tiles": select()}
        path.write_text(json.dumps(saved, indent=2) + "\n")
    if args.fetch:
        receipts = [fetch(tile) for tile in saved["tiles"]]
        (OUT / "imagery_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print("frozen tiles", len(saved["tiles"]))


if __name__ == "__main__":
    main()
