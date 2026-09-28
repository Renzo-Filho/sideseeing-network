"""Fetch and compare official DuPage deeded ROW in the O'Hare pilot envelope."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import requests
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_row_land_2026_09_26"
WORK = A / "work/chicago_m3_row_land_2026_09_26"
LAYER = "https://gis.dupageco.org/arcgis/rest/services/OpenData/ROW/MapServer/0"
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def get(params):
    response = requests.get(LAYER + "/query", params=params, timeout=90,
                            headers={"User-Agent": "sideseeing-network bounded Chicago M3 pilot"})
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
    districts = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    ohare = districts.loc[districts.unit_id.eq("CHI:76")].geometry.item()
    raw_path = WORK / "CHI_76_dupage_row.geojson"
    receipt_path = OUT / "dupage_row_receipt.json"
    if args.fetch and not raw_path.exists():
        bbox = transform(TO_LONLAT, ohare.buffer(250)).bounds
        query = {"where": "1=1", "geometry": ",".join(f"{v:.8f}" for v in bbox),
                 "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                 "spatialRel": "esriSpatialRelIntersects"}
        ids = sorted(get({**query, "returnIdsOnly": "true", "f": "json"}).get("objectIds") or [])
        features = []
        for start in range(0, len(ids), 150):
            batch = ids[start:start + 150]
            response = get({"objectIds": ",".join(map(str, batch)),
                            "outFields": "OBJECTID,ROW_TYPE,ROW_DOC,Street_Name,Name,Notes",
                            "returnGeometry": "true", "f": "geojson"})
            features.extend(response.get("features", []))
        unique = {int(f["properties"]["OBJECTID"]): f for f in features}
        if set(unique) != set(ids):
            raise RuntimeError(f"Incomplete DuPage ROW retrieval: {len(unique)} of {len(ids)}")
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
        raise RuntimeError("DuPage ROW cache hash changed")
    features = json.loads(raw_path.read_text())["features"]
    row = gpd.GeoDataFrame([f["properties"] for f in features],
                           geometry=[shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                                     for f in features], crs=26916)
    row["area_in_ohare_m2"] = row.intersection(ohare).area
    row = row.loc[row.area_in_ohare_m2.gt(0)].copy()
    row_type_counts = Counter(row.ROW_TYPE.fillna("<null>"))
    type_areas = {str(k): float(v.geometry.intersection(ohare).union_all().area)
                  for k, v in row.groupby("ROW_TYPE", dropna=False)}
    # The county describes this as deeded ROW, with no guaranteed active-road code.
    all_dupage_row = shapely.union_all(row.geometry.values)
    cook_features = json.loads((WORK / "CHI_76_row.geojson").read_text())["features"]
    cook_active = shapely.union_all([
        shapely.make_valid(transform(TO_METRIC, shape(f["geometry"]))) for f in cook_features
        if f["properties"].get("ROWTYPE") in [1, 4, 5]])
    edge_features = json.loads((WORK / "CHI_76_road_edge.geojson").read_text())["features"]
    ordinary_edge = shapely.union_all([
        shapely.make_valid(transform(TO_METRIC, shape(f["geometry"]))) for f in edge_features
        if f["properties"].get("TYPE") == 1])
    edge_area = ordinary_edge.intersection(ohare).area
    combined = shapely.union_all([cook_active, all_dupage_row])
    parcels = gpd.read_parquet(A / "data/Chicago/chicago_cadastral_2026_09_18/dupage_parcels_current/part_00000.parquet")
    parcel_union = shapely.union_all(parcels.geometry.values)
    result = {
        "source": LAYER, "retrieved_features": len(features), "positive_area_ohare_features": len(row),
        "row_type_counts_positive_ohare": dict(row_type_counts), "row_type_union_area_in_ohare_m2": type_areas,
        "dupage_row_union_area_in_ohare_m2": all_dupage_row.intersection(ohare).area,
        "cook_active_road_row_area_in_ohare_m2": cook_active.intersection(ohare).area,
        "dupage_row_overlap_with_held_dupage_parcels_m2": all_dupage_row.intersection(parcel_union).area,
        "ordinary_road_edge_area_in_ohare_m2": edge_area,
        "road_edge_outside_cook_row_fraction": ordinary_edge.difference(cook_active).intersection(ohare).area / edge_area,
        "road_edge_outside_combined_row_fraction": ordinary_edge.difference(combined).intersection(ohare).area / edge_area,
        "status": "deeded ROW source; ROW_TYPE semantics and physical-road coverage require review"
    }
    (OUT / "dupage_row_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
