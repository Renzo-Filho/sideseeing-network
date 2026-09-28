"""Queue named municipal streets that cross provisional faces outside Cook masks.

Alerts are review leads only. The 5 m allowance and 30 m run threshold match
the earlier bounded screen; they cannot prove a missing public-road boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_provisional_faces_2026_09_27"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
RAW_ROADS = A / "data/Chicago/steet_center_lines_20260915.geojson"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
ALIGN_M = 5
MIN_RUN_M = 30


def lines(geom):
    return [part for part in shapely.get_parts(shapely.make_valid(geom))
            if part.geom_type == "LineString" and part.length > 0]


def link_candidates(run, candidates):
    hits = candidates.iloc[candidates.sindex.query(run, predicate="intersects")]
    crossing = sorted(({"candidate_id": face.candidate_id,
                        "line_length_inside_face_m": round(run.intersection(face.geometry).length, 3)}
                       for face in hits.itertuples()
                       if run.intersection(face.geometry).length >= 10),
                      key=lambda x: -x["line_length_inside_face_m"])
    return (";".join(x["candidate_id"] for x in crossing),
            ";".join(str(x["line_length_inside_face_m"]) for x in crossing))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--relink-only", action="store_true")
    args = parser.parse_args()
    candidates = gpd.read_parquet(OUT / "global_provisional_faces.parquet")
    if args.relink_only:
        table = pd.read_csv(OUT / "named_street_gap_queue.csv", keep_default_na=False)
        table["candidate_intersection_m"] = table["candidate_intersection_m"].astype(str)
        for i, record in table.iterrows():
            ids, lengths = link_candidates(shapely.from_wkt(record.geometry_wkt), candidates)
            table.at[i, "candidate_ids"] = ids
            table.at[i, "candidate_intersection_m"] = lengths
        table.to_csv(OUT / "named_street_gap_queue.csv", index=False)
        summary_path = OUT / "named_street_gap_queue_summary.json"
        summary = json.loads(summary_path.read_text())
        summary["alerts_with_candidate_link"] = int(table.candidate_ids.ne("").sum())
        summary["candidate_geometry_sha256"] = hashlib.sha256(
            (OUT / "global_provisional_faces.parquet").read_bytes()).hexdigest()
        summary["candidate_link_status"] = "relinked to corrected candidate geometry; source-gap geometries unchanged"
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"alerts": len(table),
                          "with_candidate_link": summary["alerts_with_candidate_link"]}, indent=2))
        return
    names = {str(f["properties"].get("trans_id")): f["properties"]
             for f in json.loads(RAW_ROADS.read_text())["features"]}
    roads = gpd.read_parquet(ROADS)
    districts = gpd.read_parquet(DISTRICTS).sort_values("unit_id")
    alerts = []
    screened = 0
    for unit in districts.itertuples():
        area = unit.geometry.buffer(-40)
        if area.is_empty:
            continue
        row = source_geometries(unit.unit_id, "row", lambda p: p.get("ROWTYPE") in (1,4,5))
        edge = source_geometries(unit.unit_id, "road_edge", lambda p: p.get("TYPE") == 1)
        mask_with_alignment = shapely.union_all([row, edge]).buffer(ALIGN_M)
        subset = roads.iloc[roads.sindex.query(area, predicate="intersects")]
        count = 0
        for road in subset.itertuples():
            meta = names.get(str(road.trans_id), {})
            street = " ".join(str(meta.get(k) or "").strip()
                              for k in ("pre_dir", "street_nam", "street_typ", "suf_dir")).strip()
            if not street:
                continue
            interior = road.geometry.intersection(area)
            if interior.length < MIN_RUN_M:
                continue
            screened += 1
            uncovered = interior.difference(mask_with_alignment)
            runs = lines(uncovered)
            if not runs:
                continue
            run = max(runs, key=lambda r: r.length)
            if run.length < MIN_RUN_M:
                continue
            candidate_ids, candidate_lengths = link_candidates(run, candidates)
            alerts.append({"unit_id": unit.unit_id,
                           "trans_id": str(road.trans_id),
                           "street": street,
                           "road_class": str(road._asdict()["_4"]) if "_4" in road._asdict() else str(getattr(road, "class", "")),
                           "f_zlev": road.f_zlev, "t_zlev": road.t_zlev,
                           "longest_uncovered_run_m": run.length,
                           "uncovered_total_m": uncovered.length,
                           "candidate_ids": candidate_ids,
                           "candidate_intersection_m": candidate_lengths,
                           "geometry_wkt": run.wkt,
                           "status": "needs_road_status_and_property_side_review"})
            count += 1
        print(f"{unit.unit_id}: {count} gap alerts", flush=True)
    table = pd.DataFrame(alerts)
    table.to_csv(OUT / "named_street_gap_queue.csv", index=False)
    summary = {"screened_named_segments": screened, "alert_segments": len(table),
               "alerts_with_candidate_link": int(table.candidate_ids.ne("").sum()) if len(table) else 0,
               "alignment_tolerance_m": ALIGN_M, "minimum_uncovered_run_m": MIN_RUN_M,
               "candidate_geometry_sha256": hashlib.sha256(
                   (OUT / "global_provisional_faces.parquet").read_bytes()).hexdigest(),
               "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (ROADS, RAW_ROADS, DISTRICTS)},
               "status": "review queue only; no automated boundary repair"}
    (OUT / "named_street_gap_queue_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
