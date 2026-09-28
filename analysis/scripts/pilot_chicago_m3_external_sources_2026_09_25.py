"""Bounded Chicago physical-block source test on frozen cases.

Fetch small OSM API map tiles with --fetch, then run locally without it.
This is a diagnostic, not a 77-area block release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
import requests
import shapely
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import transform, unary_union

from harmonization.geometry import largest_overlap

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/results/Chicago/chicago_m3_external_sources_2026_09_25"
RAW = ROOT / "analysis/work/chicago_m3_external_sources_2026_09_25"
HOLD = ROOT / "analysis/results/Chicago/chicago_m_holdout_2026_09_25"
EARLIER = ROOT / "analysis/results/Chicago/chicago_m_physical_cases_2026_09_25"
QUEUE = ROOT / "analysis/results/Chicago/chicago_m_sample_2026_09_25/m3_m4_annotation_queue.csv"
LUI = ROOT / "analysis/data/Chicago/LUI_2023_view_332920193481040239.gpkg"
BLOCKS = ROOT / "analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2/blocks.parquet"
DISTRICTS = ROOT / "analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
EARLIER_IDS = ["M3_01", "M3_02", "M3_03", "M3_04", "M3_05", "M3_06"]
HOLD_IDS = ["H_M2_06", "H_M3_01", "H_M3_02", "H_M3_03", "H_M3_04", "H_M3_05", "H_M3_06", "H_M3_07"]
CASE_IDS = EARLIER_IDS + HOLD_IDS
NEW_SELECTION = OUT / "new_case_selection.json"
CHALLENGE_SELECTION = OUT / "challenge_case_selection.json"
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
OSM_URL = "https://api.openstreetmap.org/api/0.6/map"
PUBLIC_HIGHWAYS = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street", "pedestrian"}
# Frozen screening hypothesis, to be evaluated against the saved labels.
PUBLIC_BOUNDARY_THRESHOLD = 0.65
AREA_THRESHOLD_M2 = 1000
WIDTH_THRESHOLD_M = 15


def tile_for(case):
    half = min(240.0, max(115.0, float(case["half_width_m"]) + 20.0))
    metric = box(case["x"] - half, case["y"] - half, case["x"] + half, case["y"] + half)
    lonlat = transform(TO_LONLAT, metric)
    return metric, ",".join(f"{v:.7f}" for v in lonlat.bounds)


def fetch(case, path):
    _, bbox = tile_for(case)
    params = {"bbox": bbox}
    if not path.exists():
        with requests.get(OSM_URL, params=params, timeout=90, stream=True,
                          headers={"User-Agent": "sideseeing-network bounded Chicago M3 source review"}) as response:
            response.raise_for_status()
            size = 0
            partial = path.with_suffix(".part")
            with partial.open("wb") as writer:
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 30_000_000:
                        partial.unlink(missing_ok=True)
                        raise RuntimeError(f"{case['case_id']}: OSM XML exceeds 30 MB cap")
                    writer.write(chunk)
            partial.replace(path)
        time.sleep(1)
    return {"case_id": case["case_id"], "url": requests.Request("GET", OSM_URL, params=params).prepare().url,
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "checked_utc": datetime.now(timezone.utc).isoformat()}


def osm_geometries(path):
    root = ET.parse(path).getroot()
    nodes = {n.attrib["id"]: (float(n.attrib["lon"]), float(n.attrib["lat"])) for n in root.findall("node")}
    ways = []
    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        refs = [nd.attrib["ref"] for nd in way.findall("nd")]
        coords = [nodes[r] for r in refs if r in nodes]
        if len(coords) < 2:
            continue
        geometry = transform(TO_METRIC, LineString(coords))
        ways.append((tags, geometry, coords))
    return ways, len(nodes), len(root.findall("relation"))


def fraction_near(line, geometries, metres=8.0):
    if not geometries or line.length == 0:
        return 0.0
    return float(line.intersection(unary_union([g.buffer(metres) for g in geometries])).length / line.length)


def safe_union(polygons):
    return unary_union(polygons) if polygons else Polygon()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch only the frozen small OSM tiles")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    earlier_selection = json.loads((EARLIER / "case_selection.json").read_text())
    hold_selection = json.loads((HOLD / "case_selection.json").read_text())
    cases = [c for c in earlier_selection["cases"] if c["case_id"] in EARLIER_IDS]
    cases += [c for c in hold_selection["cases"] if c["case_id"] in HOLD_IDS]
    assert [c["case_id"] for c in cases] == CASE_IDS
    if NEW_SELECTION.exists():
        cases += json.loads(NEW_SELECTION.read_text())["cases"]
    if CHALLENGE_SELECTION.exists():
        cases += json.loads(CHALLENGE_SELECTION.read_text())["cases"]
    queue = pd.read_csv(QUEUE)
    labels = pd.concat([pd.read_csv(EARLIER / "visual_case_labels.csv"),
                        pd.read_csv(HOLD / "visual_case_labels.csv"),
                        *[pd.read_csv(p) for p in (OUT / "new_case_visual_labels.csv",
                                                   OUT / "challenge_case_visual_labels.csv") if p.exists()]], ignore_index=True)
    blocks = gpd.read_parquet(BLOCKS)
    districts = gpd.read_parquet(DISTRICTS)
    receipts = []
    rows = []
    for case in cases:
        cid = case["case_id"]
        path = RAW / f"{cid}.osm.xml"
        if args.fetch:
            receipts.append(fetch(case, path))
        elif not path.exists():
            raise FileNotFoundError(f"Fetch {path} with --fetch first")
        else:
            receipts.append({"case_id": cid, "bytes": path.stat().st_size,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        ways, node_count, relation_count = osm_geometries(path)
        metric_tile, _ = tile_for(case)
        public = [g for t, g, _ in ways if t.get("highway") in PUBLIC_HIGHWAYS and t.get("area") != "yes"]
        service = [g for t, g, _ in ways if t.get("highway") == "service"]
        rail = [g for t, g, _ in ways if t.get("railway") in {"rail", "light_rail", "tram"}]
        grade = [(t, g) for t, g, _ in ways if any(k in t for k in ("bridge", "tunnel", "layer")) and g.intersects(metric_tile)]
        road_areas = []
        islands = []
        for tags, _, coords in ways:
            if "area:highway" not in tags or len(coords) < 4 or coords[0] != coords[-1]:
                continue
            polygon = transform(TO_METRIC, Polygon(coords))
            if not polygon.is_valid:
                polygon = shapely.make_valid(polygon)
            if polygon.is_empty:
                continue
            road_areas.append(polygon)
            if tags["area:highway"] == "traffic_island":
                islands.append(polygon)
        bbox_3857 = gpd.GeoSeries([metric_tile], crs=26916).to_crs(3857).total_bounds
        cmap = pyogrio.read_dataframe(LUI, where="LANDUSE IN ('1511','1512')", bbox=tuple(bbox_3857),
                                      columns=["LANDUSE"]).to_crs(26916)
        rail_row = safe_union(cmap.loc[cmap.LANDUSE.eq("1511"), "geometry"].tolist())
        road_row = safe_union(cmap.loc[cmap.LANDUSE.eq("1512"), "geometry"].tolist())
        row = {"case_id": cid, "unit_id": case["unit_id"], "category": case["category"],
               "osm_nodes": node_count, "osm_ways": len(ways), "osm_relations": relation_count,
               "osm_public_road_ways": len(public), "osm_service_ways": len(service),
               "osm_rail_ways": len(rail), "osm_grade_tagged_ways": len(grade),
               "osm_grade_ways_within_30m": sum(g.distance(Point(case["x"], case["y"])) <= 30 for _, g in grade),
               "osm_road_area_polygons": len(road_areas), "osm_traffic_island_polygons": len(islands),
               "cmap_rail_row_polygons": int(cmap.LANDUSE.eq("1511").sum()),
               "cmap_road_row_polygons": int(cmap.LANDUSE.eq("1512").sum()),
               "cmap_rail_row_tile_area_m2": float(rail_row.intersection(metric_tile).area),
               "cmap_road_row_tile_area_m2": float(road_row.intersection(metric_tile).area),
               "osm_road_area_tile_m2": float(safe_union(road_areas).intersection(metric_tile).area),
               "osm_traffic_island_tile_m2": float(safe_union(islands).intersection(metric_tile).area),
               "osm_grade_tags": json.dumps([{"highway": t.get("highway"), "railway": t.get("railway"),
                                              "bridge": t.get("bridge"), "tunnel": t.get("tunnel"),
                                              "layer": t.get("layer")} for t, _ in grade], sort_keys=True)}
        if case["family"] == "M3/M4":
            if "geometry_wkt" in case:
                polygon = shapely.from_wkt(case["geometry_wkt"])
                min_width_m = float(case["min_width_m"])
            else:
                candidate = queue.loc[queue.candidate_id.eq(case["queue_id"])].iloc[0]
                polygon = shapely.from_wkt(candidate.geometry_wkt)
                min_width_m = float(candidate.min_width_m)
            district = districts.loc[districts.unit_id.eq(case["unit_id"])].geometry.item()
            reference = blocks.loc[blocks.intersects(district)].copy()
            owned = largest_overlap(reference, districts).astype(str).eq(case["unit_id"].split(":")[1])
            reference = reference.loc[owned.to_numpy()]
            nearby_blocks = reference.loc[reference.intersects(polygon)]
            if len(nearby_blocks):
                intersections = nearby_blocks.geometry.intersection(polygon).area
                unions = nearby_blocks.geometry.area + polygon.area - intersections
                best_iou = float((intersections / unions).max())
            else:
                best_iou = 0.0
            public_fraction = fraction_near(polygon.boundary, public)
            public_fraction_3m = fraction_near(polygon.boundary, public, 3.0)
            public_fraction_5m = fraction_near(polygon.boundary, public, 5.0)
            public_fraction_12m = fraction_near(polygon.boundary, public, 12.0)
            rectangle_coords = list(polygon.minimum_rotated_rectangle.exterior.coords)
            side_lengths = [math.dist(rectangle_coords[i], rectangle_coords[i + 1]) for i in range(4)]
            row.update({"candidate_id": case["queue_id"], "area_m2": polygon.area,
                        "polygon_fingerprint": hashlib.sha256(shapely.to_wkb(shapely.normalize(polygon))).hexdigest(),
                        "min_width_m": min_width_m, "census_best_iou": best_iou,
                        "compactness": float(4 * 3.141592653589793 * polygon.area / polygon.length**2),
                        "rectangle_elongation": float(max(side_lengths) / min(side_lengths)),
                        "osm_public_boundary_fraction_8m": public_fraction,
                        "osm_public_boundary_fraction_3m": public_fraction_3m,
                        "osm_public_boundary_fraction_5m": public_fraction_5m,
                        "osm_public_boundary_fraction_12m": public_fraction_12m,
                        "osm_service_boundary_fraction_8m": fraction_near(polygon.boundary, service),
                        "osm_rail_boundary_fraction_8m": fraction_near(polygon.boundary, rail),
                        "cmap_rail_row_overlap_fraction": float(polygon.intersection(rail_row).area / polygon.area),
                        "cmap_road_row_overlap_fraction": float(polygon.intersection(road_row).area / polygon.area),
                        "osm_road_area_overlap_fraction": float(polygon.intersection(safe_union(road_areas)).area / polygon.area),
                        "old_size_width_prediction": "retain" if polygon.area >= AREA_THRESHOLD_M2 and min_width_m >= WIDTH_THRESHOLD_M else "exclude",
                        "new_public_edge_prediction": "retain" if polygon.area >= AREA_THRESHOLD_M2 and min_width_m >= WIDTH_THRESHOLD_M and public_fraction >= PUBLIC_BOUNDARY_THRESHOLD else "exclude",
                        "saved_visual_label": labels.loc[labels.case_id.eq(cid), "provisional_label"].item()
                        if labels.case_id.eq(cid).any() else None})
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "case_source_comparison.csv", index=False)
    (OUT / "osm_receipts.json").write_text(json.dumps(receipts, indent=2))
    (OUT / "pilot_contract.json").write_text(json.dumps({"case_ids": [c["case_id"] for c in cases],
        "osm_public_highways": sorted(PUBLIC_HIGHWAYS), "boundary_buffer_m": 8,
        "public_boundary_fraction_threshold": PUBLIC_BOUNDARY_THRESHOLD,
        "area_threshold_m2": AREA_THRESHOLD_M2, "width_threshold_m": WIDTH_THRESHOLD_M,
        "note": "Frozen screening hypothesis; falsified as a sufficient physical-block rule by subsequently selected low-Census-overlap challenge cases"}, indent=2))
    labeled = table.loc[table.saved_visual_label.notna() & table.candidate_id.notna()].copy()
    checks = {"osm_tiles": len(table), "labeled_block_case_rows": len(labeled),
              "source_accuracy_estimate": False,
              "reason": "Small purposive cases, one visual reviewer; challenge cases deliberately selected for low Census overlap.",
              "cohorts": {}}
    for name, mask in {"previously_labeled": labeled.case_id.str.match("^(M3_|H_M3_)"),
                       "new_source_blind": labeled.case_id.str.startswith("V_M3_"),
                       "low_census_challenge": labeled.case_id.str.startswith("C_M3_")}.items():
        group = labeled.loc[mask].drop_duplicates("polygon_fingerprint")
        actual = group.saved_visual_label.str.startswith("plausible")
        item = {"case_rows": int(mask.sum()), "unique_polygons": len(group),
                "visual_plausible": int(actual.sum()), "visual_exclude": int((~actual).sum()),
                "old_rule_agreements": int(((group.old_size_width_prediction == "retain") == actual).sum()),
                "new_rule_agreements": int(((group.new_public_edge_prediction == "retain") == actual).sum()),
                "new_false_retained": group.loc[(group.new_public_edge_prediction == "retain") & ~actual, "case_id"].tolist(),
                "boundary_buffer_sensitivity": {}}
        for distance in (3, 5, 8, 12):
            predicted = ((group.area_m2 >= AREA_THRESHOLD_M2)
                         & (group.min_width_m >= WIDTH_THRESHOLD_M)
                         & (group[f"osm_public_boundary_fraction_{distance}m"] >= PUBLIC_BOUNDARY_THRESHOLD))
            item["boundary_buffer_sensitivity"][str(distance)] = int((predicted == actual).sum())
        checks["cohorts"][name] = item
    (OUT / "validation_summary.json").write_text(json.dumps(checks, indent=2))
    print(f"Saved {len(rows)} case comparisons")


if __name__ == "__main__":
    main()
