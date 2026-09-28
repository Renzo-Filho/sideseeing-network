"""Freeze candidate-blind Chicago block reference zones and fetch orthophotos.

Zone selection uses only Community Area boundaries and distances to past tile
centers. It must run before viewing any block candidates at these centers.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import requests
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
WORK = A / "work/chicago_m3_complete_zone_pilot_v1_2026_09_26"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
FRESH = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26/tile_selection.json"
HOLD = A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26/tile_selection.json"
URL = "https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/exportImage"
SEED = 20260926
HALF_WIDTH_M = 300
IMAGE_SIZE = 1200
UNITS = ["CHI:11", "CHI:32", "CHI:49", "CHI:57"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_zones() -> list[dict]:
    districts = gpd.read_parquet(DISTRICTS)
    previous = [Point(t["x"], t["y"]) for path in (FRESH, HOLD)
                for t in json.loads(path.read_text())["tiles"]]
    rng = np.random.default_rng(SEED)
    zones = []
    for unit in UNITS:
        interior = districts.loc[districts.unit_id.eq(unit)].geometry.item().buffer(-HALF_WIDTH_M - 30)
        west, south, east, north = interior.bounds
        for _ in range(100000):
            point = Point(rng.uniform(west, east), rng.uniform(south, north))
            if not interior.covers(point):
                continue
            if min(point.distance(p) for p in previous) < 700:
                continue
            zones.append({"zone_id": f"{unit.replace(':', '_')}_Z1", "unit_id": unit,
                          "x": float(point.x), "y": float(point.y),
                          "half_width_m": HALF_WIDTH_M, "image_size_px": IMAGE_SIZE})
            break
        else:
            raise RuntimeError(f"Could not select an independent zone in {unit}")
    return zones


def fetch(zone: dict) -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    path = WORK / f"{zone['zone_id']}_ortho.jpg"
    receipt = WORK / f"{zone['zone_id']}_ortho_receipt.json"
    if path.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        if digest(path) != saved["sha256"]:
            raise RuntimeError(f"Cached image changed: {path}")
        return saved
    x, y, h = zone["x"], zone["y"], zone["half_width_m"]
    params = {"bbox": f"{x-h:.3f},{y-h:.3f},{x+h:.3f},{y+h:.3f}",
              "bboxSR": "26916", "imageSR": "26916", "size": f"{IMAGE_SIZE},{IMAGE_SIZE}",
              "format": "jpg", "f": "image"}
    response = requests.get(URL, params=params, timeout=90,
                            headers={"User-Agent": "sideseeing-network Chicago physical-block reference pilot"})
    response.raise_for_status()
    if not response.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(response.text[:300])
    path.write_bytes(response.content)
    saved = {"zone_id": zone["zone_id"], "source_url": response.url,
             "retrieved_utc": datetime.now(timezone.utc).isoformat(),
             "sha256": digest(path), "bytes": path.stat().st_size}
    receipt.write_text(json.dumps(saved, indent=2) + "\n")
    return saved


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "zone_selection.json"
    zones = select_zones()
    payload = {"seed": SEED,
               "selection_basis": "Community Area interiors and >=700 m distance from old tile centers; no candidate geometry, imagery or labels",
               "zones": zones,
               "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (DISTRICTS, FRESH, HOLD)}}
    if path.exists():
        if json.loads(path.read_text()) != payload:
            raise RuntimeError("Frozen zone selection changed")
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n")
    receipts = [fetch(zone) for zone in zones]
    (OUT / "imagery_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps({"zones": zones, "image_count": len(receipts)}, indent=2))


if __name__ == "__main__":
    main()
