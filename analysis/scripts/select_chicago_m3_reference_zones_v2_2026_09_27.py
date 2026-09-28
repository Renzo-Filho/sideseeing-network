"""Freeze new candidate-blind Chicago M3/M4 reference zones and images."""
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
OUT = A / "results/Chicago/chicago_m3_reference_zones_v2_2026_09_27"
WORK = A / "work/chicago_m3_reference_zones_v2_2026_09_27"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
OLD = [
    A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26/tile_selection.json",
    A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26/tile_selection.json",
    A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/zone_selection.json",
    A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/motorway_zone_selection.json",
]
URL = "https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/exportImage"
UNITS = ["CHI:11", "CHI:32", "CHI:49", "CHI:57", "CHI:63", "CHI:76"]
SEED = 20260927
HALF_WIDTH_M = 350
IMAGE_SIZE = 1400
MIN_OLD_DISTANCE_M = 600


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_centers():
    centers = []
    for path in OLD:
        payload = json.loads(path.read_text())
        items = payload.get("tiles", payload.get("zones", [payload["zone"]] if "zone" in payload else []))
        for item in items:
            centers.append(Point(item["x"], item["y"]))
    return centers


def select():
    districts = gpd.read_parquet(DISTRICTS)
    prior = previous_centers()
    rng = np.random.default_rng(SEED)
    zones = []
    for unit in UNITS:
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        interior = district.buffer(-HALF_WIDTH_M - 30)
        west, south, east, north = interior.bounds
        for _ in range(100000):
            point = Point(rng.uniform(west, east), rng.uniform(south, north))
            if not interior.covers(point):
                continue
            if min(point.distance(other) for other in prior) < MIN_OLD_DISTANCE_M:
                continue
            zones.append({"zone_id": f"{unit.replace(':', '_')}_R2", "unit_id": unit,
                          "x": float(point.x), "y": float(point.y),
                          "half_width_m": HALF_WIDTH_M, "image_size_px": IMAGE_SIZE,
                          "reference_core_half_width_m": 200})
            break
        else:
            raise RuntimeError(f"No independent zone found in {unit}")
    return zones


def fetch(zone):
    WORK.mkdir(parents=True, exist_ok=True)
    file = WORK / f"{zone['zone_id']}_ortho.jpg"
    receipt = WORK / f"{zone['zone_id']}_ortho_receipt.json"
    if file.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        assert sha(file) == saved["sha256"]
        return saved
    x, y, h = zone["x"], zone["y"], zone["half_width_m"]
    params = {"bbox": f"{x-h:.3f},{y-h:.3f},{x+h:.3f},{y+h:.3f}",
              "bboxSR": "26916", "imageSR": "26916", "size": f"{IMAGE_SIZE},{IMAGE_SIZE}",
              "format": "jpg", "f": "image"}
    response = requests.get(URL, params=params, timeout=120,
                            headers={"User-Agent": "sideseeing-network Chicago M3 M4 independent reference v2"})
    response.raise_for_status()
    if not response.headers.get("content-type", "").startswith("image/"):
        raise RuntimeError(response.text[:300])
    file.write_bytes(response.content)
    saved = {"zone_id": zone["zone_id"], "source_url": response.url,
             "retrieved_utc": datetime.now(timezone.utc).isoformat(),
             "sha256": sha(file), "bytes": file.stat().st_size}
    receipt.write_text(json.dumps(saved, indent=2) + "\n")
    return saved


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    zones = select()
    payload = {"seed": SEED, "selection_basis": "district interiors and distance to older sample centers; no candidate geometry or imagery",
               "minimum_previous_center_distance_m": MIN_OLD_DISTANCE_M,
               "zones": zones,
               "input_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [DISTRICTS, *OLD]}}
    target = OUT / "zone_selection.json"
    if target.exists():
        assert json.loads(target.read_text()) == payload, "Frozen zone selection changed"
    else:
        target.write_text(json.dumps(payload, indent=2) + "\n")
    receipts = [fetch(zone) for zone in zones]
    (OUT / "imagery_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps({"zone_count": len(zones), "images": len(receipts)}, indent=2))


if __name__ == "__main__":
    main()
