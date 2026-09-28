"""Freeze small held-out Chicago M2/M3/M4 controls before imagery review."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
QUEUE = A / "results/Chicago/chicago_m_sample_2026_09_25"
PREVIOUS = A / "results/Chicago/chicago_m_physical_cases_2026_09_25/case_selection.json"
OUT = A / "results/Chicago/chicago_m_holdout_2026_09_25/case_selection.json"
FIXTURES = A / "results/SP_CHI/harmonization_2026_09_22_full_scope_review/junctions_v2/fixture_source_evidence.json"

# Predeclared contrasts from the existing queues, excluding the first audit.
M2_PAIRS = [
    "6539401a-5e67-44e0-bee4-3f64fae8a368",  # Archer Heights
    "1e189525-f66f-4590-b4d7-2716609d10c5",  # Roseland
    "37875fe8-73f3-46b6-81ea-d58ab2349d41",  # Jefferson Park
]
M2_ISOLATED = [
    "02b920d6-bf7c-4bde-8b16-bf35f0f369bf",  # Gage Park source 3-arm
    "008d2db7-d6bc-4dae-81c0-c781faa0bde0",  # Roseland source 3-arm
]
M3_IDS = [
    "CHI:57:no_links:83", "CHI:57:no_links:68",
    "CHI:63:no_links:117", "CHI:63:no_links_rail_row:105",
    "CHI:49:no_links:291", "CHI:49:no_links_rail_row:302",
    "CHI:11:no_links:136",
]


def main():
    m2 = pd.read_csv(QUEUE / "m2_annotation_queue.csv").set_index("connector_a")
    m3 = pd.read_csv(QUEUE / "m3_m4_annotation_queue.csv").set_index("candidate_id")
    connectors = gpd.read_parquet(A / "work/runs/sp_chicago_harmonization_2026_09_22/roads/Chicago_connector_candidates.parquet").set_index("id")
    roads = gpd.read_parquet(A / "work/prepared/Chicago/overture_2026_08_19_review_v1/selected_roads.parquet")
    prior = json.loads(PREVIOUS.read_text())["cases"]
    prior_ids = {x["queue_id"] for x in prior}
    assert not (set(M2_PAIRS + M3_IDS) & prior_ids)
    cases = []
    for i, key in enumerate(M2_PAIRS, 1):
        row = m2.loc[key]
        cases.append({"case_id": f"H_M2_{i:02d}", "family": "M2", "queue_id": key,
                      "unit_id": row.unit_id, "category": row.category,
                      "x": float(row.x_mid), "y": float(row.y_mid), "half_width_m": 90,
                      "rule_prediction": "merge_if_same_grade_and_one_visible_crossing"})
    for i, key in enumerate(M2_ISOLATED, 4):
        row = connectors.loc[key]
        assert int(row.arms) == 3
        unit_connectors = connectors.loc[connectors.unit_id.eq(row.unit_id)]
        coords = np.column_stack([unit_connectors.geometry.x, unit_connectors.geometry.y])
        nearest = cKDTree(coords).query([row.geometry.x, row.geometry.y], k=2)[0][1]
        local_roads = roads.iloc[roads.sindex.query(row.geometry.buffer(28), predicate="intersects")]
        assert nearest > 50 and len(local_roads) >= 3
        assert local_roads.subclass.eq("link").sum() == 0 and local_roads.road_flags.isna().all()
        cases.append({"case_id": f"H_M2_{i:02d}", "family": "M2", "queue_id": f"isolated:{key}",
                      "unit_id": row.unit_id, "category": "isolated_source_three_arm_control",
                      "connector_a": key, "connector_b": None,
                      "x": float(row.geometry.x), "y": float(row.geometry.y),
                      "half_width_m": 90, "rule_prediction": "one_three_arm_junction"})
    stack = next(x for x in json.loads(FIXTURES.read_text()) if x["label"] == "loop_stacked_roads")
    a, b = stack["connector_ids"]
    xa, ya = stack["coordinates_metric"][a]
    xb, yb = stack["coordinates_metric"][b]
    cases.append({"case_id": "H_M2_06", "family": "M2", "queue_id": "loop_stacked_roads",
                  "unit_id": "CHI:32", "category": "known_grade_separated_negative_control",
                  "connector_a": a, "connector_b": b,
                  "x": (xa + xb) / 2, "y": (ya + yb) / 2,
                  "half_width_m": 90, "rule_prediction": "do_not_merge_distinct_levels"})
    for i, key in enumerate(M3_IDS, 1):
        row = m3.loc[key]
        geom = wkt.loads(row.geometry_wkt)
        x, y = geom.representative_point().coords[0]
        minx, miny, maxx, maxy = geom.bounds
        half = min(200, max(90, 0.65 * max(maxx - minx, maxy - miny) + 20))
        # Explicit provisional rule derived from the first six annotated cases.
        simple_rule = row.area_m2 >= 1000 and row.min_width_m >= 15
        cases.append({"case_id": f"H_M3_{i:02d}", "family": "M3/M4", "queue_id": key,
                      "unit_id": row.unit_id, "category": row["mode"],
                      "x": x, "y": y, "half_width_m": round(half, 2),
                      "area_m2": float(row.area_m2), "min_width_m": float(row.min_width_m),
                      "reference_iou": float(row.best_reference_iou),
                      "rule_prediction": "retain" if simple_rule else "exclude"})
    assert len(cases) == 13
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "selection_policy": "Three unused near-pair queue cases; two isolated source-three-arm controls prefiltered for >50m nearest connector and no local link/bridge flags; one prior Loop stacked negative control; seven unused block-queue contrasts. Fixed before imagery. Block rule area>=1000 m2 and width>=15 m is a test hypothesis, not accepted ontology.",
        "cases": cases,
    }
    if OUT.exists():
        assert json.loads(OUT.read_text()) == payload, "Frozen held-out selection changed"
    else:
        OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
