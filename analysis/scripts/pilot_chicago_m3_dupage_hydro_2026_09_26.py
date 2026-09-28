"""Bounded DuPage hydrography check for O'Hare water false-block control."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import requests
import shapely
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
WORK = A / "work/chicago_m3_fresh_tiles_2026_09_26"
LAYER = "https://gis.dupageco.org/arcgis/rest/services/Hydrography/DPMS_LakesPonds_Service/MapServer/0"
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def get(params):
    response = requests.get(LAYER + "/query", params=params, timeout=90,
                            headers={"User-Agent": "sideseeing-network bounded O'Hare hydro pilot"})
    response.raise_for_status()
    value = response.json()
    if "error" in value:
        raise RuntimeError(value["error"])
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    district = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    ohare = district.loc[district.unit_id.eq("CHI:76")].geometry.item()
    raw_path = WORK / "CHI_76_dupage_hydro.geojson"
    receipt_path = OUT / "dupage_hydro_receipt.json"
    if args.fetch and not raw_path.exists():
        bbox = transform(TO_LONLAT, ohare.buffer(250)).bounds
        query = {"where": "1=1", "geometry": ",".join(f"{v:.8f}" for v in bbox),
                 "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                 "spatialRel": "esriSpatialRelIntersects"}
        ids = sorted(get({**query, "returnIdsOnly": "true", "f": "json"}).get("objectIds") or [])
        features = []
        for start in range(0, len(ids), 150):
            result = get({"objectIds": ",".join(map(str, ids[start:start+150])),
                          "outFields": "OBJECTID,Name,Surface,County,ImageYear,ImageVerified,Notes",
                          "returnGeometry": "true", "f": "geojson"})
            features.extend(result.get("features", []))
        unique = {int(f["properties"]["OBJECTID"]): f for f in features}
        if set(unique) != set(ids):
            raise RuntimeError("Incomplete DuPage hydro retrieval")
        raw_path.write_text(json.dumps({"type": "FeatureCollection", "features": [unique[i] for i in ids]},
                                       separators=(",", ":")))
        receipt_path.write_text(json.dumps({"source": LAYER, "ids_query": query,
                                            "features": len(ids), "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                                            "raw_path": str(raw_path.relative_to(ROOT)),
                                            "retrieved_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
    if not raw_path.exists():
        raise FileNotFoundError("Run --fetch first")
    receipt = json.loads(receipt_path.read_text())
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != receipt["sha256"]:
        raise RuntimeError("DuPage hydro cache hash changed")
    features = json.loads(raw_path.read_text())["features"]
    polygons = [(f["properties"], shapely.make_valid(transform(TO_METRIC, shape(f["geometry"]))))
                for f in features]
    relevant = [(p, g) for p, g in polygons if g.intersection(ohare).area > 0]
    tiles = {t["tile_id"]: t for t in json.loads((OUT / "tile_selection.json").read_text())["tiles"]}
    refs = json.loads((OUT / "visual_reference.json").read_text())["negative_points"]
    checks = []
    for ref in refs:
        if ref["tile_id"] not in ["CHI_76_1", "CHI_76_2"]:
            continue
        tile = tiles[ref["tile_id"]]
        x, y = ref["pixel_xy"]
        h = tile["half_width_m"]
        point = Point(tile["x"]-h+x*2*h/800, tile["y"]+h-y*2*h/800)
        matches = [p for p, g in relevant if g.covers(point)]
        checks.append({"reference_id": ref["id"], "tile_id": ref["tile_id"],
                       "dupage_hydro_contains": bool(matches), "matched_properties": matches})
    result = {"source": LAYER, "retrieved_features": len(features),
              "positive_area_ohare_features": len(relevant),
              "hydro_union_area_in_ohare_m2": shapely.union_all([g for _,g in relevant]).intersection(ohare).area,
              "negative_point_checks": checks,
              "status": "hydrographic source with documented older imagery and updates; case diagnostic"}
    (OUT / "dupage_hydro_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
