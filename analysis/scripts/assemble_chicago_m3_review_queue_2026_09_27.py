"""Join citywide face diagnostics into an exhaustive, non-destructive review queue."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/results/Chicago/chicago_m3_provisional_faces_2026_09_27"


def main():
    faces = gpd.read_parquet(OUT / "global_provisional_faces.parquet")
    gaps = pd.read_csv(OUT / "named_street_gap_queue.csv", dtype={"road_class": str})
    gap_counts = {}
    ordinary_counts = {}
    special_counts = {}
    for gap in gaps.itertuples():
        ids = str(gap.candidate_ids).split(";") if pd.notna(gap.candidate_ids) else []
        for cid in ids:
            if not cid:
                continue
            gap_counts[cid] = gap_counts.get(cid, 0) + 1
            bucket = special_counts if str(gap.road_class) == "99" else ordinary_counts
            bucket[cid] = bucket.get(cid, 0) + 1
    q = pd.DataFrame(faces.drop(columns="geometry"))
    q["small_face_flag"] = q.area_m2 < 1000
    q["large_face_flag"] = q.area_m2 > 100000
    q["low_raw_compactness_flag"] = q.raw_compactness < 0.2
    q["named_street_alert_count"] = q.candidate_id.map(gap_counts).fillna(0).astype(int)
    q["nonclass99_street_alert_count"] = q.candidate_id.map(ordinary_counts).fillna(0).astype(int)
    q["class99_special_alert_count"] = q.candidate_id.map(special_counts).fillna(0).astype(int)
    q["review_priority"] = "routine_full_census"
    high = (q.small_face_flag | q.large_face_flag | q.low_raw_compactness_flag |
            q.touches_city_edge | q.unjoined_internal_district_edge |
            q.nonclass99_street_alert_count.gt(0) | q.class99_special_alert_count.gt(0))
    q.loc[high, "review_priority"] = "flagged_first"
    q["review_state"] = "unreviewed"
    q["reason_codes"] = ""
    q["evidence_paths"] = ""
    q["reviewer"] = ""
    q["reviewed_utc"] = ""
    if not q.candidate_id.is_unique or len(q) != len(faces):
        raise ValueError("Incomplete or duplicated review queue")
    q.to_csv(OUT / "global_review_queue.csv", index=False)
    summary = {"all_provisional_candidates": len(q),
               "flagged_first": int(high.sum()),
               "routine_full_census": int((~high).sum()),
               "small_under_1000_m2": int(q.small_face_flag.sum()),
               "large_over_100000_m2": int(q.large_face_flag.sum()),
               "low_raw_compactness_under_0_2": int(q.low_raw_compactness_flag.sum()),
               "faces_with_nonclass99_street_alerts": int(q.nonclass99_street_alert_count.gt(0).sum()),
               "faces_with_class99_special_alerts": int(q.class99_special_alert_count.gt(0).sum()),
               "street_alert_rows": len(gaps),
               "status": "unreviewed queue only; flags do not reject or accept faces"}
    (OUT / "global_review_queue_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
