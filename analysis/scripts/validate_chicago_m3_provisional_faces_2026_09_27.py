"""Check source, geometry, overlap and storage invariants for the M3 inventory."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_provisional_faces_2026_09_27"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads((OUT / "manifest.json").read_text())
    summary = json.loads((OUT / "stitch_summary.json").read_text())
    assert len(manifest["units"]) == 77
    assert manifest["total_faces"] == summary["fragment_count"]
    for item in manifest["units"]:
        path = ROOT / item["output_path"]
        assert digest(path) == item["output_sha256"], path
        assert item["conservation_error_m2"] <= 0.1, item["unit_id"]
        for source in item["source"].values():
            assert digest(ROOT / source["path"]) == source["sha256"]
    faces = gpd.read_parquet(OUT / "global_provisional_faces.parquet")
    assert len(faces) == summary["global_face_count"]
    assert faces.candidate_id.is_unique
    assert faces.geometry.is_valid.all()
    assert not faces.geometry.is_empty.any()
    assert all(faces.area_m2.gt(0))
    assert abs(faces.geometry.area.sum() - faces.area_m2.sum()) < 0.1
    geoms = faces.geometry.to_numpy()
    tree = shapely.STRtree(geoms)
    overlaps = []
    for i, j in tree.query(geoms, predicate="intersects").T:
        if j <= i:
            continue
        area = geoms[i].intersection(geoms[j]).area
        if area > 0.01:
            overlaps.append((str(faces.candidate_id.iloc[i]),
                             str(faces.candidate_id.iloc[j]), area))
    assert not overlaps, f"Overlapping candidate faces: {overlaps[:5]}"
    queue = OUT / "global_review_queue.csv"
    if queue.exists():
        import pandas as pd
        q = pd.read_csv(queue)
        assert len(q) == len(faces) and set(q.candidate_id) == set(faces.candidate_id)
    free = shutil.disk_usage(OUT).free
    assert free >= 8 * 2**30
    report = {"status": "passed computational QA; physical block truth remains unreviewed",
              "units": 77, "faces": len(faces), "overlaps_over_0_01_m2": len(overlaps),
              "stitch_area_error_m2": summary["area_error_m2"],
              "free_gib": free / 2**30}
    (OUT / "validation_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
