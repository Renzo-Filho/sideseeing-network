"""Small, predeclared imagery audit of Chicago M2 and M3/M4 sample queues.

Cook County orthophotos can show surface form. They cannot establish legal
parcel identity or reliably prove whether an apparent crossing is grade-separated.
Images are cached under analysis/work; result receipts keep source URLs/hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely import wkt
from shapely.geometry import LineString, MultiLineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
QUEUE = A / "results/Chicago/chicago_m_sample_2026_09_25"
OUT = A / "results/Chicago/chicago_m_physical_cases_2026_09_25"
WORK = A / "work/chicago_m_physical_cases_2026_09_25"
IMAGE_URL = "https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/exportImage"
TO_GEO = Transformer.from_crs(26916, 4326, always_xy=True)
HEADERS = {"User-Agent": "sideseeing-network bounded academic morphology audit"}

# Fixed before viewing imagery. Each ID is a row in the already frozen queues.
M2_IDS = [
    "2e54fe9f-715c-483b-9bfa-ad80da121ad0",
    "09969acb-7fc6-428b-bb95-4043fd98996d",
    "27f91440-9e48-4367-aed0-ff8908b20dfa",
    "b0370867-8a9a-4499-ac65-b430e79796d2",
]
M3_IDS = [
    "CHI:57:all_streets:90",           # tiny low-IoU street-network sliver
    "CHI:63:no_links:39",              # large high-IoU ordinary reference case
    "CHI:49:no_links_rail_row:27",     # narrow rail-ROW case
    "CHI:11:all_streets:14",           # high-IoU reference case
    "CHI:11:no_links:22",              # low-IoU non-link case
    "CHI:49:no_links:285",             # low-IoU Roseland case
]


def selected_cases():
    m2 = pd.read_csv(QUEUE / "m2_annotation_queue.csv")
    m3 = pd.read_csv(QUEUE / "m3_m4_annotation_queue.csv")
    assert len(M2_IDS) == len(set(M2_IDS)) and len(M3_IDS) == len(set(M3_IDS))
    a = m2.set_index("connector_a").loc[M2_IDS]
    b = m3.set_index("candidate_id").loc[M3_IDS]
    assert len(a) == len(M2_IDS) and len(b) == len(M3_IDS)
    cases = []
    for i, (key, row) in enumerate(a.iterrows(), 1):
        cases.append({"case_id": f"M2_{i:02d}", "family": "M2", "queue_id": key,
                      "unit_id": row.unit_id, "category": row.category,
                      "x": float(row.x_mid), "y": float(row.y_mid),
                      "half_width_m": 90})
    for i, (key, row) in enumerate(b.iterrows(), 1):
        geom = wkt.loads(row.geometry_wkt)
        x, y = geom.representative_point().coords[0]
        box = geom.bounds
        half = min(200, max(90, 0.65 * max(box[2] - box[0], box[3] - box[1]) + 20))
        cases.append({"case_id": f"M3_{i:02d}", "family": "M3/M4", "queue_id": key,
                      "unit_id": row.unit_id, "category": row["mode"], "x": x, "y": y,
                      "half_width_m": round(half, 2), "area_m2": float(row.area_m2),
                      "reference_iou": float(row.best_reference_iou)})
    return cases


def points_of(geom):
    if isinstance(geom, (LineString, Polygon)):
        return [list(geom.exterior.coords)] if isinstance(geom, Polygon) else [list(geom.coords)]
    if isinstance(geom, MultiLineString):
        return [list(g.coords) for g in geom.geoms]
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--select-only", action="store_true")
    parser.add_argument("--case-file", type=Path,
                        help="Previously frozen JSON case selection for a separate audit")
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--work-dir", type=Path, default=WORK)
    args = parser.parse_args()
    out_dir, work_dir = args.out_dir.resolve(), args.work_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = json.loads(args.case_file.read_text())["cases"] if args.case_file else selected_cases()
    selection = out_dir / "case_selection.json"
    if args.case_file and args.case_file.resolve() in {
        (out_dir / "new_case_selection.json").resolve(),
        (out_dir / "challenge_case_selection.json").resolve(),
    }:
        pass  # Independently frozen cases live beside their output under a distinct name.
    elif selection.exists():
        assert json.loads(selection.read_text())["cases"] == cases, "Frozen selection changed"
    else:
        assert not args.case_file, "External case selection must already exist in out_dir"
        selection.write_text(json.dumps({"selection_policy": "Four M2 near pairs across three areas including the only unlinked pair; six M3/M4 contrasts across four areas. Selected before imagery review.", "cases": cases}, indent=2) + "\n")
    if args.select_only:
        print(selection)
        return

    m2 = pd.read_csv(QUEUE / "m2_annotation_queue.csv").set_index("connector_a")
    m3 = pd.read_csv(QUEUE / "m3_m4_annotation_queue.csv").set_index("candidate_id")
    connectors = gpd.read_parquet(A / "work/runs/sp_chicago_harmonization_2026_09_22/roads/Chicago_connector_candidates.parquet").set_index("id")
    roads = gpd.read_parquet(A / "work/prepared/Chicago/overture_2026_08_19_review_v1/selected_roads.parquet")
    receipts = []
    work_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        x, y, half = case["x"], case["y"], case["half_width_m"]
        lon0, lat0 = TO_GEO.transform(x - half, y - half)
        lon1, lat1 = TO_GEO.transform(x + half, y + half)
        bounds = (lon0, lat0, lon1, lat1)
        params = {"bbox": ",".join(f"{v:.8f}" for v in bounds), "bboxSR": 4326,
                  "imageSR": 4326, "size": "800,800", "format": "jpg", "f": "image"}
        url = requests.Request("GET", IMAGE_URL, params=params).prepare().url
        metadata_url = requests.Request("GET", IMAGE_URL, params={**params, "f": "json"}).prepare().url
        metadata_cache = work_dir / f"{case['case_id']}_extent.json"
        if metadata_cache.exists():
            metadata = json.loads(metadata_cache.read_text())
        else:
            response = requests.get(metadata_url, headers=HEADERS, timeout=50)
            response.raise_for_status()
            metadata = response.json()
            assert metadata.get("extent", {}).get("spatialReference", {}).get("wkid") == 4326
            metadata_cache.write_text(json.dumps(metadata, indent=2) + "\n")
        extent = metadata["extent"]
        assert metadata["width"] == metadata["height"] == 800
        raw = work_dir / f"{case['case_id']}_raw.jpg"
        if raw.exists():
            content = raw.read_bytes()
        else:
            response = requests.get(url, headers=HEADERS, timeout=50)
            response.raise_for_status()
            assert response.headers.get("Content-Type", "").startswith("image/"), response.headers.get("Content-Type")
            content = response.content
            assert len(content) < 4_000_000
            raw.write_bytes(content)
        image = Image.open(io.BytesIO(content)).convert("RGB")
        draw = ImageDraw.Draw(image)

        def pix(px, py):
            lon, lat = TO_GEO.transform(px, py)
            return ((lon - extent["xmin"]) / (extent["xmax"] - extent["xmin"]) * 800,
                    (extent["ymax"] - lat) / (extent["ymax"] - extent["ymin"]) * 800)

        if case["family"] == "M2":
            row = None if "connector_a" in case else m2.loc[case["queue_id"]]
            local_roads = roads.iloc[roads.sindex.query(Point(x, y).buffer(half), predicate="intersects")]
            for geom in local_roads.geometry:
                for line in points_of(geom):
                    draw.line([pix(*v) for v in line], fill=(0, 255, 255), width=2)
            connector_a = case.get("connector_a", case["queue_id"])
            connector_b = case.get("connector_b", row.connector_b if row is not None else None)
            for label, key, color in [("A", connector_a, (255, 20, 20)),
                                      ("B", connector_b, (255, 255, 0))]:
                if key is None:
                    continue
                p = connectors.loc[key].geometry
                cx, cy = pix(p.x, p.y)
                draw.ellipse((cx-7, cy-7, cx+7, cy+7), outline=color, width=4)
                draw.text((cx+8, cy+8), label, fill=color, stroke_width=2, stroke_fill=(0, 0, 0))
        else:
            geom = wkt.loads(case["geometry_wkt"]) if "geometry_wkt" in case else wkt.loads(m3.loc[case["queue_id"]].geometry_wkt)
            for line in points_of(geom):
                draw.line([pix(*v) for v in line], fill=(255, 20, 20), width=4)
            cx, cy = pix(x, y)
            draw.ellipse((cx-4, cy-4, cx+4, cy+4), fill=(255, 255, 0))
        annotated = work_dir / f"{case['case_id']}_overlay.png"
        image.save(annotated)
        receipts.append({**case, "source": "Cook County 2025 orthophoto ImageServer",
                         "url": url, "metadata_url": metadata_url, "returned_extent": extent,
                         "image_sha256": hashlib.sha256(content).hexdigest(),
                         "raw_path": str(raw.relative_to(ROOT)),
                         "overlay_path": str(annotated.relative_to(ROOT)),
                         "overlay_sha256": hashlib.sha256(annotated.read_bytes()).hexdigest()})
        print(case["case_id"], case["queue_id"], flush=True)
    receipt_path = out_dir / "imagery_receipts.json"
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())["cases"]
        receipts = list({item["case_id"]: item for item in previous + receipts}.values())
    receipt_path.write_text(json.dumps({
        "run_utc": datetime.now(timezone.utc).isoformat(), "epsg": 26916,
        "source_year": 2025, "cases": receipts}, indent=2) + "\n")


if __name__ == "__main__":
    main()
