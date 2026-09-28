"""Freeze one new CHI:11 motorway core before viewing candidates there."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from select_chicago_m3_independent_zones_2026_09_26 import A, DISTRICTS, OUT, SEED, fetch

SEGMENTS = A / "data/Chicago/overture_2026_08_19/segment/part_0000.parquet"
OLD = [A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26/tile_selection.json",
       A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26/tile_selection.json",
       OUT / "zone_selection.json"]
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
HALF_WIDTH_M = 300


def main() -> None:
    districts = gpd.read_parquet(DISTRICTS)
    inner = districts.loc[districts.unit_id.eq("CHI:11")].geometry.item().buffer(-HALF_WIDTH_M-30)
    table = pq.read_table(SEGMENTS, columns=["class", "geometry"])
    motorway = shapely.union_all([transform(TO_METRIC, shapely.from_wkb(wkb))
                                  for cls, wkb in zip(table["class"].to_pylist(), table["geometry"].to_pylist())
                                  if cls == "motorway" and wkb is not None])
    previous = [Point(t["x"], t["y"]) for p in OLD for t in
                json.loads(p.read_text()).get("tiles", json.loads(p.read_text()).get("zones", []))]
    rng = np.random.default_rng(SEED+17)
    west, south, east, north = inner.bounds
    for _ in range(100000):
        point = Point(rng.uniform(west, east), rng.uniform(south, north))
        if inner.covers(point) and point.distance(motorway) < 40 and min(point.distance(p) for p in previous) > 700:
            zone = {"zone_id": "CHI_11_MZ1", "unit_id": "CHI:11", "x": float(point.x),
                    "y": float(point.y), "half_width_m": HALF_WIDTH_M, "image_size_px": 1200,
                    "motorway_distance_m": point.distance(motorway)}
            break
    else:
        raise RuntimeError("No new motorway zone found under frozen criteria")
    path = OUT / "motorway_zone_selection.json"
    payload = {"seed": SEED+17,
               "selection_basis": "CHI:11 inner district, Overture motorway distance <40m, >700m from previous tile/zone centers; no ROW candidate or image viewed",
               "zone": zone}
    if path.exists():
        if json.loads(path.read_text()) != payload:
            raise RuntimeError("Frozen motorway zone changed")
    else:
        path.write_text(json.dumps(payload, indent=2) + "\n")
    receipt = fetch(zone)
    (OUT / "motorway_imagery_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(zone, indent=2))


if __name__ == "__main__":
    main()
