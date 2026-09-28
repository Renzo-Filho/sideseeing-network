"""Bounded Chicago block pilot from Cook road ROW polygons and land parcels.

Downloads only six Community Area envelopes. Raw county responses are cached in
analysis/work; no feature is promoted or citywide block table changed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapely
from pyproj import Transformer
from shapely.geometry import box, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_row_land_2026_09_26"
WORK = A / "work/chicago_m3_row_land_2026_09_26"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
CASES = A / "results/Chicago/chicago_m3_external_sources_2026_09_25"
UNITS = ["CHI:11", "CHI:49", "CHI:57", "CHI:63", "CHI:32", "CHI:76"]
SOURCES = {
    "row": ("https://gis.cookcountyil.gov/traditional/rest/services/RightOfWay_Cadastre/MapServer/2025", "OBJECTID,ROWTYPE"),
    "road_edge": ("https://gis.cookcountyil.gov/traditional/rest/services/planimetry/MapServer/7", "OBJECTID,TYPE,SURFACE"),
}
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
HEADERS = {"User-Agent": "sideseeing-network bounded academic Chicago block geometry pilot"}


def get_json(url, params):
    response = requests.get(url, params=params, headers=HEADERS, timeout=90)
    response.raise_for_status()
    value = response.json()
    if "error" in value:
        raise RuntimeError(f"ArcGIS response error: {value['error']}")
    return value


def fetch_area(unit, source, area):
    base, fields = SOURCES[source]
    path = WORK / f"{unit.replace(':', '_')}_{source}.geojson"
    receipt = WORK / f"{unit.replace(':', '_')}_{source}_receipt.json"
    if path.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != saved["sha256"]:
            raise RuntimeError(f"Cache hash changed: {path}")
        return saved
    bbox = transform(TO_LONLAT, area.envelope).bounds
    query = base + "/query"
    envelope = {"geometry": ",".join(f"{v:.8f}" for v in bbox),
                "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                "spatialRel": "esriSpatialRelIntersects"}
    ids_result = get_json(query, {"where": "1=1", **envelope, "returnIdsOnly": "true", "f": "json"})
    ids = sorted(ids_result.get("objectIds") or [])
    features = []
    for start in range(0, len(ids), 150):
        chunk = ids[start:start + 150]
        result = get_json(query, {"objectIds": ",".join(map(str, chunk)),
                                  "outFields": fields, "returnGeometry": "true", "f": "geojson"})
        features.extend(result.get("features", []))
    unique = {int(f["properties"]["OBJECTID"]): f for f in features}
    if set(unique) != set(ids):
        raise RuntimeError(f"Incomplete {source} retrieval for {unit}: {len(unique)} of {len(ids)}")
    payload = {"type": "FeatureCollection", "features": [unique[i] for i in ids]}
    path.write_text(json.dumps(payload, separators=(",", ":")))
    saved = {"unit_id": unit, "source": source, "service": base, "ids_url": query,
             "ids_query": {"where": "1=1", **envelope, "returnIdsOnly": "true", "f": "json"},
             "feature_count": len(ids), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
             "bytes": path.stat().st_size, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
             "raw_path": str(path.relative_to(ROOT))}
    receipt.write_text(json.dumps(saved, indent=2) + "\n")
    return saved


def load_area(unit, source):
    path = WORK / f"{unit.replace(':', '_')}_{source}.geojson"
    raw = json.loads(path.read_text())
    if not raw["features"]:
        return gpd.GeoDataFrame(geometry=[], crs=26916)
    props = [f["properties"] for f in raw["features"]]
    geometries = [shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                  for f in raw["features"]]
    return gpd.GeoDataFrame(props, geometry=geometries, crs=26916)


def case_records():
    records = []
    queue = pd.read_csv(A / "results/Chicago/chicago_m_sample_2026_09_25/m3_m4_annotation_queue.csv")
    queue_wkt = dict(zip(queue.candidate_id, queue.geometry_wkt))
    old_labels = []
    for directory in (A / "results/Chicago/chicago_m_physical_cases_2026_09_25",
                      A / "results/Chicago/chicago_m_holdout_2026_09_25"):
        selected = json.loads((directory / "case_selection.json").read_text())["cases"]
        for record in selected:
            if record["family"] == "M3/M4":
                record["geometry_wkt"] = queue_wkt[record["queue_id"]]
                records.append(record)
        old_labels.append(pd.read_csv(directory / "visual_case_labels.csv"))
    for name in ("new_case_selection.json", "challenge_case_selection.json"):
        records.extend(json.loads((CASES / name).read_text())["cases"])
    labels = pd.concat([*old_labels, pd.read_csv(CASES / "new_case_visual_labels.csv"),
                        pd.read_csv(CASES / "challenge_case_visual_labels.csv")])
    labels = dict(zip(labels.case_id, labels.provisional_label))
    for record in records:
        record["label"] = labels[record["case_id"]]
    return records


def polygon_parts(geometry):
    return [p for p in shapely.get_parts(shapely.make_valid(geometry))
            if p.geom_type == "Polygon" and p.area > 0]


def process(districts):
    rows, area_rows = [], []
    cases = case_records()
    for unit in UNITS:
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        extraction = district.buffer(250)
        row = load_area(unit, "row")
        edge = load_area(unit, "road_edge")
        row = row.loc[row.intersects(extraction)].copy()
        edge = edge.loc[edge.intersects(extraction)].copy()
        active_road = row.loc[row.ROWTYPE.isin([1, 4, 5])] if len(row) else row
        active_rail = row.loc[row.ROWTYPE.isin([2, 4])] if len(row) else row
        ordinary_edge = edge.loc[edge.TYPE.eq(1)] if len(edge) else edge
        alley_edge = edge.loc[edge.TYPE.eq(5)] if len(edge) else edge
        road_mask = shapely.union_all(active_road.geometry.values) if len(active_road) else shapely.GeometryCollection()
        rail_mask = shapely.union_all(active_rail.geometry.values) if len(active_rail) else shapely.GeometryCollection()
        edge_mask = shapely.union_all(ordinary_edge.geometry.values) if len(ordinary_edge) else shapely.GeometryCollection()
        alley_mask = shapely.union_all(alley_edge.geometry.values) if len(alley_edge) else shapely.GeometryCollection()
        # Topology variants reveal seams and alley splits. The alley-open variant
        # is diagnostic; old Road Edge alley polygons do not certify current ROW.
        components = {}
        masks = {"raw": road_mask, "seam_0_5m": road_mask.buffer(0.5),
                 "alley_open": road_mask.difference(alley_mask.buffer(1.0)),
                 "row_plus_road_edge": shapely.union_all([road_mask, edge_mask]),
                 "hybrid_alley_open": shapely.union_all([road_mask, edge_mask]).difference(alley_mask.buffer(1.0)),
                 "transport_hybrid_alley_open": shapely.union_all([road_mask, rail_mask, edge_mask]).difference(alley_mask.buffer(1.0))}
        for mode, mask in masks.items():
            components[mode] = polygon_parts(extraction.difference(mask))
        area_rows.append({"unit_id": unit, "row_features": len(row), "active_road_row_features": len(active_road),
                          "active_rail_row_features": len(active_rail), "road_edge_features": len(edge),
                          "ordinary_road_edge_features": len(ordinary_edge), "alley_edge_features": len(alley_edge),
                          "district_area_m2": district.area,
                          "active_road_row_district_fraction": road_mask.intersection(district).area / district.area,
                          "road_edge_district_fraction": edge_mask.intersection(district).area / district.area,
                          "road_edge_outside_row_fraction": edge_mask.difference(road_mask).intersection(district).area /
                                                            max(1.0, edge_mask.intersection(district).area),
                          "components_raw": len(components["raw"]),
                          "components_0_5m_seam": len(components["seam_0_5m"]),
                          "components_alley_open": len(components["alley_open"]),
                          "components_row_plus_road_edge": len(components["row_plus_road_edge"]),
                          "components_hybrid_alley_open": len(components["hybrid_alley_open"]),
                          "components_transport_hybrid_alley_open": len(components["transport_hybrid_alley_open"])})
        for case in [c for c in cases if c["unit_id"] == unit]:
            geom = shapely.from_wkt(case["geometry_wkt"])
            center = geom.representative_point()
            candidate_land = geom.difference(road_mask)
            item = {"case_id": case["case_id"], "unit_id": unit, "label": case["label"],
                    "polygon_fingerprint": hashlib.sha256(shapely.to_wkb(shapely.normalize(geom))).hexdigest(),
                    "centerline_area_m2": geom.area,
                    "centerline_compactness": 4 * math.pi * geom.area / geom.length**2,
                    "candidate_non_row_area_m2": candidate_land.area,
                    "road_row_overlap_fraction": geom.intersection(road_mask).area / geom.area,
                    "rail_row_overlap_fraction": geom.intersection(rail_mask).area / geom.area,
                    "transport_row_overlap_fraction": geom.intersection(shapely.union_all([road_mask, rail_mask])).area / geom.area,
                    "road_edge_overlap_fraction": geom.intersection(edge_mask).area / geom.area,
                    "alley_edge_overlap_fraction": geom.intersection(alley_mask).area / geom.area,
                    "center_in_active_road_row": bool(road_mask.covers(center)),
                    "center_in_active_rail_row": bool(rail_mask.covers(center))}
            for prefix, parts in components.items():
                scores = [p.intersection(geom).area for p in parts]
                best = parts[int(np.argmax(scores))] if scores and max(scores) > 0 else None
                item[f"{prefix}_best_land_overlap_fraction"] = max(scores) / geom.area if scores else 0.0
                item[f"{prefix}_best_land_component_area_m2"] = best.area if best is not None else np.nan
                item[f"{prefix}_best_land_component_iou_to_candidate_non_row"] = (
                    best.intersection(candidate_land).area / best.union(candidate_land).area
                    if best is not None and not candidate_land.is_empty else np.nan)
                item[f"{prefix}_best_land_component_compactness"] = (
                    4 * math.pi * best.area / best.length**2 if best is not None and best.length else np.nan)
                if best is not None:
                    rect = best.minimum_rotated_rectangle
                    coords = list(rect.exterior.coords)
                    sides = [math.dist(coords[i], coords[i + 1]) for i in range(4)]
                    item[f"{prefix}_best_land_component_elongation"] = max(sides) / min(sides) if min(sides) else np.nan
                    if prefix == "alley_open":
                        for tolerance in (1, 2, 5):
                            simplified = best.simplify(tolerance, preserve_topology=True)
                            item[f"alley_open_compactness_simplify_{tolerance}m"] = (
                                4 * math.pi * simplified.area / simplified.length**2)
                            item[f"alley_open_area_change_simplify_{tolerance}m"] = (
                                simplified.area / best.area - 1)
                else:
                    item[f"{prefix}_best_land_component_elongation"] = np.nan
                item[f"{prefix}_best_land_component_touches_extraction_edge"] = (
                    bool(best.boundary.intersects(extraction.boundary)) if best is not None else None)
                item[f"{prefix}_best_land_component_count"] = len(parts)
            rows.append(item)
    pd.DataFrame(rows).to_csv(OUT / "case_row_land_comparison.csv", index=False)
    pd.DataFrame(area_rows).to_csv(OUT / "area_row_coverage.csv", index=False)
    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    districts = gpd.read_parquet(DISTRICTS)
    assert districts.crs.to_epsg() == 26916
    receipts = []
    for unit in UNITS:
        district = districts.loc[districts.unit_id.eq(unit)].geometry.item()
        for source in SOURCES:
            path = WORK / f"{unit.replace(':', '_')}_{source}.geojson"
            if args.fetch:
                receipts.append(fetch_area(unit, source, district.buffer(250)))
            elif not path.exists():
                raise FileNotFoundError(f"Run --fetch to acquire {path}")
            else:
                saved = json.loads((WORK / f"{unit.replace(':', '_')}_{source}_receipt.json").read_text())
                if hashlib.sha256(path.read_bytes()).hexdigest() != saved["sha256"]:
                    raise RuntimeError(f"Cache hash changed: {path}")
                receipts.append(saved)
        print("source ready", unit, flush=True)
    (OUT / "source_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    count = process(districts)
    table = pd.read_csv(OUT / "case_row_land_comparison.csv")
    areas = pd.read_csv(OUT / "area_row_coverage.csv")
    unique = table.drop_duplicates("polygon_fingerprint")
    plausible = unique.loc[unique.label.str.startswith("plausible")]
    false = unique.loc[~unique.label.str.startswith("plausible")]
    checks = {"source_extracts": len(receipts), "case_rows": count,
              "unique_case_polygons": len(unique), "visually_plausible_unique": len(plausible),
              "visually_false_unique": len(false),
              "false_fully_in_active_road_row": false.loc[false.road_row_overlap_fraction >= .9999, "case_id"].tolist(),
              "false_inside_larger_land_component": false.loc[
                  (false.alley_open_best_land_overlap_fraction >= .5) &
                  (false.alley_open_best_land_component_area_m2 > 5 * false.centerline_area_m2), "case_id"].tolist(),
              "plausible_alley_open_iou_ge_0_9": int((plausible.alley_open_best_land_component_iou_to_candidate_non_row >= .9).sum()),
              "plausible_alley_open_iou_below_0_9": plausible.loc[
                  plausible.alley_open_best_land_component_iou_to_candidate_non_row < .9, "case_id"].tolist(),
              "plausible_centerline_compactness_median": float(plausible.centerline_compactness.median()),
              "plausible_land_component_compactness_median": float(plausible.alley_open_best_land_component_compactness.median()),
              "road_edge_outside_row_fraction_by_unit": dict(zip(areas.unit_id, areas.road_edge_outside_row_fraction)),
              "status": "bounded diagnostic; old polygon is not a surveyed reference; no accepted M3/M4 release"}
    (OUT / "validation_summary.json").write_text(json.dumps(checks, indent=2) + "\n")
    print("case rows", count)


if __name__ == "__main__":
    main()
