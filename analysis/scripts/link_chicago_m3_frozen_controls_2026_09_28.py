"""Link candidate-blind visual controls to the stitched citywide face IDs.

The linkage is a review aid. A point or rough four-corner outline is not an
independent, complete block boundary; this script never changes candidate geometry.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "analysis/results/Chicago/chicago_m3_provisional_faces_2026_09_27"
REFS = ROOT / "analysis/results/Chicago/chicago_m3_reference_zones_v2_2026_09_27"
IMAGES = ROOT / "analysis/work/chicago_m3_reference_zones_v2_2026_09_27"
OUT = RESULTS / "frozen_control_review"


def world_point(zone, xy):
    x, y, h, n = (zone[k] for k in ("x", "y", "half_width_m", "image_size_px"))
    return Point(x - h + xy[0] * 2 * h / n, y + h - xy[1] * 2 * h / n)


def pixel_xy(zone, point):
    x, y, h, n = (zone[k] for k in ("x", "y", "half_width_m", "image_size_px"))
    return ((point[0] - x + h) * n / (2 * h), (y + h - point[1]) * n / (2 * h))


def rings(geom):
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for part in parts:
        if part.geom_type == "Polygon":
            yield part.exterior.coords
            for inner in part.interiors:
                yield inner.coords


def main():
    source = RESULTS / "global_provisional_faces.parquet"
    reference_path = REFS / "visual_reference_v2.json"
    freeze = json.loads((REFS / "reference_v2_freeze.json").read_text())
    assert hashlib.sha256(reference_path.read_bytes()).hexdigest() == freeze["sha256"]
    reference = json.loads(reference_path.read_text())
    zones = json.loads((REFS / "zone_selection.json").read_text())["zones"]
    candidates = gpd.read_parquet(source)
    OUT.mkdir(exist_ok=True)
    rows = []
    for zone in zones:
        zid = zone["zone_id"]
        x, y, h = (zone[k] for k in ("x", "y", "half_width_m"))
        core = box(x - 200, y - 200, x + 200, y + 200)
        halo = box(x - h, y - h, x + h, y + h)
        subset = candidates.iloc[candidates.sindex.query(halo, predicate="intersects")]
        refs = [(r["id"], Polygon([world_point(zone, xy).coords[0] for xy in r["pixel_ring"]]))
                for r in reference["positive_polygons"] if r["zone_id"] == zid]
        controls = [(r["id"], r["reason"], world_point(zone, r["pixel_xy"]))
                    for kind in ("special_context_points", "negative_points")
                    for r in reference[kind] if r["zone_id"] == zid]
        image = Image.open(IMAGES / f"{zid}_ortho.jpg").convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=21)
        draw.rectangle((300, 300, 1100, 1100), outline="#ffff00", width=4)
        core_faces = 0
        for face in subset.itertuples():
            hits = [(rid, reason) for rid, reason, point in controls if face.geometry.covers(point)]
            representative_in_core = core.covers(face.geometry.representative_point())
            if not representative_in_core and not hits:
                continue
            core_faces += 1
            matched = []
            for rid, geom in refs:
                intersection = face.geometry.intersection(geom).area
                iou = intersection / face.geometry.union(geom).area if intersection else 0
                if iou >= .5:
                    matched.append((rid, round(iou, 3)))
            rows.append({"zone_id": zid, "candidate_id": face.candidate_id,
                         "representative_in_core": representative_in_core,
                         "area_m2": round(face.area_m2, 2),
                         "raw_compactness": round(face.raw_compactness, 3),
                         "frozen_positive_refs_iou_ge_0_5": ";".join(f"{rid}:{iou}" for rid, iou in matched),
                         "frozen_special_or_negative_points": ";".join(rid for rid, _ in hits),
                         "visual_review_status": "unreviewed",
                         "road_status_review": "required_if_ambiguous"})
            for ring in rings(face.geometry.intersection(halo)):
                draw.line([pixel_xy(zone, pt) for pt in ring], fill="#ff38ed", width=5, joint="curve")
            rp = face.geometry.representative_point()
            px, py = pixel_xy(zone, (rp.x, rp.y))
            label = face.candidate_id[-8:]
            bbox = draw.textbbox((px, py), label, font=font, anchor="mm")
            draw.rectangle(bbox, fill="#161616")
            draw.text((px, py), label, fill="white", font=font, anchor="mm")
        for rid, reason, point in controls:
            px, py = pixel_xy(zone, (point.x, point.y))
            draw.ellipse((px-9, py-9, px+9, py+9), fill="red", outline="white", width=2)
            draw.text((px+14, py), rid, fill="white", stroke_width=3, stroke_fill="black", font=font)
        image.save(OUT / f"{zid}_overlay.jpg", quality=88)
        print(f"{zid}: {core_faces} core faces, {len(refs)} positive references, {len(controls)} point controls")
    with (OUT / "core_face_linkage.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "manifest.json").write_text(json.dumps({
        "source_geometry_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "frozen_reference_sha256": freeze["sha256"],
        "core_face_rows": len(rows),
        "status": "review aid only; no final M3/M4 acceptance or candidate geometry edits",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
