"""Acquire Cook ROW and Road Edge per Chicago Community Area with disk guards.

The published ArcGIS feature-ID query and each saved response's SHA-256 are
recorded by the existing bounded acquisition function. This script only adds
incremental citywide orchestration and storage limits; it does not delete data.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from pilot_chicago_m3_row_land_2026_09_26 import DISTRICTS, WORK, fetch_area

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = WORK / "citywide_source_acquisition_2026_09_27.json"
MIN_FREE = 8 * 2**30
MAX_RAW = 3 * 2**30


def size_raw():
    return sum(path.stat().st_size for path in WORK.glob("CHI_*.geojson"))


def guard():
    free = shutil.disk_usage(WORK).free
    raw = size_raw()
    if free < MIN_FREE or raw > MAX_RAW:
        raise RuntimeError(f"M3 source storage guard: free={free}, raw={raw}")
    return free, raw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-new-units", type=int, default=77)
    parser.add_argument("--units", nargs="*", default=None)
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    districts = gpd.read_parquet(DISTRICTS).sort_values("unit_id")
    if args.units:
        districts = districts.loc[districts.unit_id.isin(args.units)]
        if len(districts) != len(set(args.units)):
            raise ValueError("Unknown or duplicate requested unit")
    records = []
    new_units = 0
    for unit in districts.itertuples():
        stem = unit.unit_id.replace(":", "_")
        complete = all((WORK / f"{stem}_{layer}.geojson").exists() and
                       (WORK / f"{stem}_{layer}_receipt.json").exists()
                       for layer in ("row", "road_edge"))
        if not complete and new_units >= args.max_new_units:
            continue
        guard()
        print(f"{unit.unit_id}: {'verify cache' if complete else 'acquire'}", flush=True)
        for layer in ("row", "road_edge"):
            receipt = fetch_area(unit.unit_id, layer, unit.geometry)
            records.append({"unit_id": unit.unit_id, "layer": layer,
                            "sha256": receipt["sha256"],
                            "bytes": receipt["bytes"],
                            "feature_count": receipt["feature_count"]})
            guard()
        if not complete:
            new_units += 1
        free, raw = guard()
        print(f"  raw={raw / 2**20:.1f} MiB, free={free / 2**30:.2f} GiB", flush=True)
        MANIFEST.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
                                        "completed_layers_this_invocation": records,
                                        "new_units_this_invocation": new_units,
                                        "raw_bytes_all_cached": raw,
                                        "free_bytes": free,
                                        "minimum_free_bytes": MIN_FREE,
                                        "maximum_raw_bytes": MAX_RAW}, indent=2) + "\n")


if __name__ == "__main__":
    main()
