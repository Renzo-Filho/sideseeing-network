"""Bounded O'Hare check of the official DuPage parcel-block polygon layer."""
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
from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_row_land_2026_09_26"
WORK = A / "work/chicago_m3_row_land_2026_09_26"
LAYER = "https://gis.dupageco.org/arcgis/rest/services/ParcelSearch/DuPageAssessmentParcelViewer/MapServer/0"
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform


def request(params):
    response = requests.get(LAYER + "/query", params=params, timeout=90,
                            headers={"User-Agent": "sideseeing-network bounded Chicago M3 geometry pilot"})
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
    raw_path = WORK / "CHI_76_dupage_parcel_blocks.geojson"
    receipt_path = OUT / "dupage_parcel_block_receipt.json"
    if args.fetch and not raw_path.exists():
        bbox = transform(TO_LONLAT, ohare.buffer(250)).bounds
        query = {"where": "1=1", "geometry": ",".join(f"{v:.8f}" for v in bbox),
                 "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                 "spatialRel": "esriSpatialRelIntersects"}
        ids = sorted(request({**query, "returnIdsOnly": "true", "f": "json"})["objectIds"])
        features = []
        for start in range(0, len(ids), 150):
            result = request({"objectIds": ",".join(map(str, ids[start:start + 150])),
                              "outFields": "OBJECTID,PARCEL_BLOCK_PIN,Name", "f": "geojson"})
            features.extend(result["features"])
        unique = {int(f["properties"]["OBJECTID"]): f for f in features}
        if set(unique) != set(ids):
            raise RuntimeError("DuPage block retrieval incomplete")
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
        raise RuntimeError("DuPage block cache hash changed")
    features = json.loads(raw_path.read_text())["features"]
    blocks = gpd.GeoDataFrame([f["properties"] for f in features],
                              geometry=[shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                                        for f in features], crs=26916)
    blocks = blocks.loc[blocks.intersection(ohare).area.gt(0)].copy()
    parcels = gpd.read_parquet(A / "data/Chicago/chicago_cadastral_2026_09_18/dupage_parcels_current/part_00000.parquet")
    parcel_union = shapely.union_all(parcels.geometry.values)
    block_union = shapely.union_all(blocks.geometry.values)
    summary = {"source": LAYER, "retrieved_features": len(features),
               "positive_area_ohare_block_polygons": len(blocks),
               "dupage_chicago_parcels": len(parcels), "dupage_parcel_union_m2": parcel_union.area,
               "block_union_overlap_with_dupage_parcels_fraction": parcel_union.intersection(block_union).area / parcel_union.area,
               "block_union_ohare_area_m2": block_union.intersection(ohare).area,
               "block_pin_nonnull": int(blocks.PARCEL_BLOCK_PIN.notna().sum()),
               "block_pin_unique": int(blocks.PARCEL_BLOCK_PIN.nunique()),
               "status": "cadastral parcel blocks; physical street-block equivalence and airport relevance unverified"}
    (OUT / "dupage_parcel_block_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(summary)


if __name__ == "__main__":
    main()
