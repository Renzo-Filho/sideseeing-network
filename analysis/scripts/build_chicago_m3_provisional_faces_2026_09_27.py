"""Build a lossless provisional Chicago land-face inventory from cached Cook masks.

This stage does not accept blocks, repair missing streets, or drop apparent
nonblocks. District-edge fragments are explicitly flagged for later stitching.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import Polygon, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
SOURCES = A / "work/chicago_m3_row_land_2026_09_26"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
OUT = A / "results/Chicago/chicago_m3_provisional_faces_2026_09_27"
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
GRID_M = 0.01
ALLEY_OPEN_M = 3.0
MIN_FREE_BYTES = 8 * 2**30
MAX_OUTPUT_BYTES = 3 * 2**30


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def source(unit: str, layer: str, accepted: set[int]):
    stem = f"{unit.replace(':', '_')}_{layer}"
    path = SOURCES / f"{stem}.geojson"
    receipt_path = SOURCES / f"{stem}_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    actual_hash = digest(path)
    if actual_hash != receipt["sha256"]:
        raise ValueError(f"Changed source cache: {path}")
    raw = json.loads(path.read_text())
    selected = []
    for feature in raw["features"]:
        field = "ROWTYPE" if layer == "row" else "TYPE"
        try:
            code = int(feature["properties"].get(field))
        except (TypeError, ValueError):
            continue
        if code not in accepted:
            continue
        geom = shapely.make_valid(transform(TO_METRIC, shape(feature["geometry"])))
        if not geom.is_empty:
            selected.append(shapely.set_precision(geom, GRID_M, mode="valid_output"))
    return shapely.union_all(selected), {"path": str(path.relative_to(ROOT)),
                                         "sha256": actual_hash,
                                         "features_all": len(raw["features"]),
                                         "features_selected": len(selected)}


def polygon_parts(geometry):
    return [part for part in shapely.get_parts(shapely.make_valid(geometry))
            if part.geom_type == "Polygon" and part.area > 0]


def build_unit(unit: str, district) -> dict:
    row, row_receipt = source(unit, "row", {1, 4, 5})
    edge, edge_receipt = source(unit, "road_edge", {1})
    alley, alley_receipt = source(unit, "road_edge", {5})
    # Preserve the shared administrative edges exactly. Independently rounding
    # neighboring districts can create overlapping face slivers at the seam.
    domain = shapely.make_valid(district)
    road_mask = shapely.union_all([row, edge])
    open_alley = shapely.set_precision(alley.buffer(ALLEY_OPEN_M), GRID_M,
                                      mode="valid_output")
    barrier = road_mask.difference(open_alley)
    faces = polygon_parts(domain.difference(barrier))
    rows = []
    for face in faces:
        face = shapely.normalize(face)
        exterior_area = Polygon(face.exterior).area
        perimeter = face.exterior.length
        hole_area = exterior_area - face.area
        # A district boundary is an artificial clip, not a physical block edge.
        touches_district = face.boundary.distance(domain.boundary) <= GRID_M
        geom_hash = hashlib.sha256(shapely.to_wkb(face)).hexdigest()[:16]
        rows.append({"candidate_id": f"M3C_{unit.replace(':', '_')}_{geom_hash}",
                     "unit_id": unit,
                     "stage": "provisional_unreviewed",
                     "requires_stitch": bool(touches_district),
                     "area_m2": face.area,
                     "outer_area_m2": exterior_area,
                     "hole_area_m2": hole_area,
                     "outer_perimeter_m": perimeter,
                     "raw_compactness": (4 * math.pi * exterior_area / perimeter**2
                                         if perimeter else None),
                     "geometry": face})
    table = gpd.GeoDataFrame(rows, geometry="geometry", crs=26916)
    if table.candidate_id.duplicated().any():
        raise ValueError(f"Duplicate candidate geometry in {unit}")
    table = table.sort_values("candidate_id").reset_index(drop=True)
    path = OUT / f"{unit.replace(':', '_')}_provisional_faces.parquet"
    table.to_parquet(path, index=False)
    recovered = sum(face.area for face in faces)
    target = domain.difference(barrier).area
    conservation_error = abs(recovered - target)
    if conservation_error > max(0.1, target * 1e-8):
        raise ValueError(f"Land-face area conservation failed in {unit}: {conservation_error}")
    if not all(shapely.is_valid(face) for face in faces):
        raise ValueError(f"Invalid face in {unit}")
    disk = shutil.disk_usage(OUT)
    output_bytes = sum(p.stat().st_size for p in OUT.glob("*_provisional_faces.parquet"))
    if disk.free < MIN_FREE_BYTES or output_bytes > MAX_OUTPUT_BYTES:
        raise RuntimeError(f"M3 storage guard: free={disk.free}, output={output_bytes}")
    return {"unit_id": unit, "face_count": len(faces),
            "requires_stitch_count": int(table.requires_stitch.sum()),
            "small_under_1000m2_count": int((table.area_m2 < 1000).sum()),
            "min_face_area_m2": float(table.area_m2.min()),
            "max_face_area_m2": float(table.area_m2.max()),
            "domain_area_m2": domain.area,
            "road_mask_area_in_domain_m2": domain.intersection(barrier).area,
            "face_area_sum_m2": recovered,
            "conservation_error_m2": conservation_error,
            "source": {"row": row_receipt, "road_edge_ordinary": edge_receipt,
                       "road_edge_alley": alley_receipt},
            "output_path": str(path.relative_to(ROOT)),
            "output_sha256": digest(path), "output_bytes": path.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--units", nargs="*", default=None,
                        help="Default: all units with both cached Cook polygon sources")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    districts = gpd.read_parquet(DISTRICTS).set_index("unit_id")
    cached = sorted(path.name[:6].replace("_", ":")
                    for path in SOURCES.glob("CHI_*_row.geojson")
                    if (SOURCES / path.name.replace("_row.geojson", "_road_edge.geojson")).exists())
    units = args.units or cached
    unknown = sorted(set(units) - set(districts.index))
    if unknown:
        raise ValueError(f"Unknown Community Areas: {unknown}")
    reports = []
    for unit in units:
        print(f"Building {unit}", flush=True)
        reports.append(build_unit(unit, districts.loc[unit].geometry))
        print(f"  {reports[-1]['face_count']} faces; "
              f"{reports[-1]['output_bytes'] / 2**20:.2f} MiB GeoParquet", flush=True)
    overview = {"stage": "provisional_unreviewed", "generated_utc": datetime.now(timezone.utc).isoformat(),
                "definition": "Cook ROW types 1/4/5 union Road Edge type 1, minus 3 m Road Edge type 5 alley buffer; source barrier 0.01 m precision, original district boundaries; no face deleted",
                "district_boundary_warning": "requires_stitch faces are district-clipped fragments, not whole blocks",
                "units": reports, "total_faces": sum(r["face_count"] for r in reports),
                "output_bytes": sum(r["output_bytes"] for r in reports),
                "free_bytes_after": shutil.disk_usage(OUT).free,
                "storage_guards": {"minimum_free_bytes": MIN_FREE_BYTES,
                                   "maximum_output_bytes": MAX_OUTPUT_BYTES},
                "input_sha256": {"districts": digest(DISTRICTS),
                                   "script": digest(Path(__file__))}}
    (OUT / "manifest.json").write_text(json.dumps(overview, indent=2) + "\n")
    inventory = []
    for unit in units:
        table = gpd.read_parquet(OUT / f"{unit.replace(':', '_')}_provisional_faces.parquet")
        inventory.append(pd.DataFrame(table.drop(columns="geometry")))
    inventory = pd.concat(inventory, ignore_index=True)
    inventory.to_csv(OUT / "candidate_inventory.csv", index=False)
    queue = inventory[["candidate_id", "unit_id", "area_m2", "requires_stitch"]].copy()
    queue["small_face_flag"] = inventory.area_m2 < 1000
    queue["large_face_flag"] = inventory.area_m2 > 100000
    queue["review_state"] = "unreviewed"
    queue["reason_codes"] = ""
    queue["evidence_paths"] = ""
    queue["reviewer"] = ""
    queue["reviewed_utc"] = ""
    queue.to_csv(OUT / "review_queue.csv", index=False)
    ledger = OUT / "repair_ledger.csv"
    if not ledger.exists():
        pd.DataFrame(columns=["operation_id", "timestamp_utc", "reviewer", "action",
                              "input_candidate_ids", "output_candidate_ids",
                              "geometry_file", "evidence_paths", "reason_code",
                              "notes"]).to_csv(ledger, index=False)
    print(f"Total {overview['total_faces']} provisional faces, "
          f"{overview['output_bytes'] / 2**20:.2f} MiB geometry files")


if __name__ == "__main__":
    main()
