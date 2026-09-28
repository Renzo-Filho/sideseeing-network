"""Freeze new motorway and near-motorway tiles without block candidates or imagery."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyarrow.parquet as pq
import requests
import shapely
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from pilot_chicago_m3_row_land_2026_09_26 import case_records

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26"
WORK = A / "work/chicago_m3_motorway_holdout_2026_09_26"
PREVIOUS = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26/tile_selection.json"
SEGMENTS = A / "data/Chicago/overture_2026_08_19/segment/part_0000.parquet"
IMAGE_URL = "https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/exportImage"
TO_METRIC = Transformer.from_crs(4326,26916,always_xy=True).transform
SEED = 20260927


def select():
    district = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    district = district.loc[district.unit_id.eq("CHI:49")].geometry.item().buffer(-160)
    table = pq.read_table(SEGMENTS, columns=["class", "geometry"])
    motorway = shapely.union_all([transform(TO_METRIC,shapely.from_wkb(wkb)) for c,wkb in
                                  zip(table["class"].to_pylist(),table["geometry"].to_pylist())
                                  if c == "motorway" and wkb is not None])
    old_tiles = [Point(t["x"],t["y"]) for t in json.loads(PREVIOUS.read_text())["tiles"]]
    old_cases = [shapely.from_wkt(c["geometry_wkt"]).centroid for c in case_records() if c["unit_id"] == "CHI:49"]
    rng = np.random.default_rng(SEED)
    selected = []
    for stratum,low,high in (("motorway_core",0,30),("motorway_core",0,30),
                             ("motorway_neighbor",90,180),("motorway_neighbor",90,180)):
        found = None
        for _ in range(30000):
            w,s,e,n = district.bounds
            point = Point(rng.uniform(w,e),rng.uniform(s,n))
            if not district.covers(point):
                continue
            distance = point.distance(motorway)
            if not low <= distance < high:
                continue
            if any(point.distance(p) < 500 for p in old_tiles):
                continue
            if any(point.distance(p) < 280 for p in old_cases):
                continue
            if any(point.distance(Point(t["x"],t["y"])) < 550 for t in selected):
                continue
            found = {"tile_id":f"CHI_49_H{len(selected)+1}","unit_id":"CHI:49",
                     "x":point.x,"y":point.y,"half_width_m":160,
                     "stratum":stratum,"motorway_distance_m":distance}
            break
        if found is None:
            raise RuntimeError(f"Could not select {stratum} tile with fixed constraints")
        selected.append(found)
    return selected


def fetch(tile, *, wide=False):
    WORK.mkdir(parents=True,exist_ok=True)
    suffix = "wide" if wide else "raw"
    path = WORK / f"{tile['tile_id']}_{suffix}.jpg"
    receipt = WORK / f"{tile['tile_id']}_{suffix}_receipt.json"
    if path.exists() and receipt.exists():
        r=json.loads(receipt.read_text())
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r["sha256"]
        return r
    x,y,h=tile["x"],tile["y"],240 if wide else tile["half_width_m"]
    query={"bbox":f"{x-h:.3f},{y-h:.3f},{x+h:.3f},{y+h:.3f}","bboxSR":"26916",
           "imageSR":"26916","size":"1000,1000" if wide else "800,800","format":"jpg","f":"image"}
    response=requests.get(IMAGE_URL,params=query,timeout=90,
                          headers={"User-Agent":"sideseeing-network Chicago M3 motorway holdout"})
    response.raise_for_status()
    if not response.headers.get("content-type","").startswith("image/"):
        raise RuntimeError(response.text[:200])
    path.write_bytes(response.content)
    r={"tile_id":tile["tile_id"],"url":response.url,"sha256":hashlib.sha256(response.content).hexdigest(),
       "bytes":len(response.content)}
    receipt.write_text(json.dumps(r,indent=2)+"\n")
    return r


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"tile_selection.json"
    tiles=select()
    if path.exists():
        if json.loads(path.read_text())["tiles"] != tiles:
            raise RuntimeError("Frozen selection changed")
    else:
        path.write_text(json.dumps({"seed":SEED,"selection_basis":"CHI:49 district and Overture motorway distances only; 500m from previous tiles, 280m from old cases, 550m from each other; no ROW candidate or imagery used","tiles":tiles},indent=2)+"\n")
    receipts=[fetch(t) for t in tiles]
    (OUT/"imagery_receipts.json").write_text(json.dumps(receipts,indent=2)+"\n")
    wide_receipts=[fetch(t,wide=True) for t in tiles]
    (OUT/"wide_imagery_receipts.json").write_text(json.dumps(wide_receipts,indent=2)+"\n")
    print("frozen and cached",len(tiles),"tiles at two extents")


if __name__=="__main__":
    main()
