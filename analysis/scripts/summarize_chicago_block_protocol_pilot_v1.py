"""Consolidate frozen Chicago M3/M4 pilots into an auditable gate assessment.

This script deliberately does not report precision or recall: neither imagery
reference is a complete independently adjudicated block inventory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
FRESH = A / "results/Chicago/chicago_m3_fresh_tiles_2026_09_26"
DEV = A / "results/Chicago/chicago_m3_candidate_v1_2026_09_26"
HOLD = A / "results/Chicago/chicago_m3_motorway_holdout_2026_09_26"
OUT = A / "results/Chicago/chicago_block_protocol_pilot_v1_2026_09_26"
CONFIG = A / "config/chicago_m3_motorway_candidate_v1.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    fresh = pd.read_csv(FRESH / "positive_reference_comparison.csv")
    inventory = pd.read_csv(DEV / "component_inventory.csv")
    review = pd.read_csv(DEV / "inventory_review.csv")
    motorway = pd.read_csv(DEV / "motorway_context.csv")
    parcel = pd.read_csv(DEV / "parcel_candidate_support.csv")
    parcel_positive = pd.read_csv(DEV / "parcel_positive_comparison.csv")
    hold_candidates = pd.read_csv(HOLD / "holdout_candidates.csv")
    hold_positive = pd.read_csv(HOLD / "positive_comparison.csv")
    hold_negative = pd.read_csv(HOLD / "negative_comparison.csv")
    hold_review = json.loads((HOLD / "reference_review.json").read_text())
    established = pd.read_csv(OUT / "momepy_baseline_positive_comparison.csv")
    rule = json.loads(CONFIG.read_text())
    assert rule["motorway_corridor_width_m"] == 40
    assert rule["flag_if_candidate_area_in_motorway_corridor_fraction_ge"] == .3

    selected = inventory.loc[inventory.diagnostic_candidate]
    assert len(selected) == len(review) == len(motorway) == len(parcel) == 26
    assert set(selected.component_id) == set(review.component_id) == set(motorway.component_id)
    assert not selected.component_id.duplicated().any()
    dev = selected.merge(review[["component_id", "status"]], on="component_id", validate="one_to_one")
    dev = dev.merge(motorway[["component_id", "area_fraction_within_40m_motorway"]],
                    on="component_id", validate="one_to_one")
    dev["motorway_flag"] = dev.area_fraction_within_40m_motorway.ge(.3)
    assert dev.status.value_counts().to_dict() == {
        "sketched_positive": 11, "nonblock_highway_island": 9, "unadjudicated": 6}
    assert len(hold_candidates) == 35 and hold_candidates.motorway_flag.sum() == 22
    assert len(hold_positive) == 7 and len(hold_negative) == 8
    assert len(established) == 11 and set(established.reference_id) == set(fresh.reference_id)

    fresh_medians = fresh.groupby("mode").best_component_iou.median().to_dict()
    assert fresh.reference_id.nunique() == 11
    assert parcel_positive.loc[parcel_positive.reference_id.isin(["R10", "R11"]),
                               "dominant_group"].nunique() == 1
    known_false = dev.status.eq("nonblock_highway_island")
    known_true = dev.status.eq("sketched_positive")
    uncertain_hold = {r["reference_id"] for r in hold_review["cases"]}
    clear_hold = hold_positive.loc[~hold_positive.reference_id.isin(uncertain_hold)]

    rows = [
        {"stage":"raw Cook ROW", "sample":"fresh 12 tiles", "metric":"positive sketch median IoU",
         "value":fresh_medians["cook_row_raw"], "denominator":11, "interpretation":"diagnostic"},
        {"stage":"ROW with mapped alleys reopened", "sample":"fresh 12 tiles",
         "metric":"positive sketch median IoU", "value":fresh_medians["cook_row_alley_open"],
         "denominator":11, "interpretation":"diagnostic"},
        {"stage":"ROW + ordinary Road Edge, alleys reopened", "sample":"fresh 12 tiles",
         "metric":"positive sketch median IoU",
         "value":fresh_medians["cook_row_plus_road_edge_alley_open"],
         "denominator":11, "interpretation":"diagnostic"},
        {"stage":"momepy.enclosures municipal centerline baseline", "sample":"same 11 rough sketches",
         "metric":"positive sketch median IoU", "value":float(established.momepy_iou.median()),
         "denominator":11, "interpretation":"direct established-method baseline, not independent superiority test"},
        {"stage":"momepy.enclosures municipal centerline baseline", "sample":"same 11 rough sketches",
         "metric":"positive sketches IoU >= 0.5", "value":int(established.momepy_iou.ge(.5).sum()),
         "denominator":11, "interpretation":"diagnostic"},
        {"stage":"ROW with mapped alleys reopened", "sample":"same 11 rough sketches",
         "metric":"positive sketches IoU >= 0.5", "value":int(established.row_alley_open_iou.ge(.5).sum()),
         "denominator":11, "interpretation":"diagnostic"},
        {"stage":"candidate inventory", "sample":"development 12 tiles",
         "metric":"tile-contained candidates", "value":len(dev), "denominator":12,
         "interpretation":"not a citywide block count"},
        {"stage":"candidate inventory", "sample":"development 12 tiles",
         "metric":"known freeway-island false candidates", "value":int(known_false.sum()),
         "denominator":len(dev), "interpretation":"lower bound in selected tiles"},
        {"stage":"frozen motorway rule", "sample":"development 12 tiles",
         "metric":"known false islands flagged", "value":int((known_false & dev.motorway_flag).sum()),
         "denominator":int(known_false.sum()), "interpretation":"threshold selected on these tiles"},
        {"stage":"frozen motorway rule", "sample":"development 12 tiles",
         "metric":"sketched positives flagged", "value":int((known_true & dev.motorway_flag).sum()),
         "denominator":int(known_true.sum()), "interpretation":"threshold selected on these tiles"},
        {"stage":"candidate inventory", "sample":"development 12 tiles",
         "metric":"median candidate area m2 before motorway flag", "value":float(dev.area_m2.median()),
         "denominator":len(dev), "interpretation":"selected tiles, not Chicago M3"},
        {"stage":"frozen motorway rule", "sample":"development 12 tiles",
         "metric":"median candidate area m2 after motorway flag", "value":float(dev.loc[~dev.motorway_flag,"area_m2"].median()),
         "denominator":int((~dev.motorway_flag).sum()), "interpretation":"selected tiles, not Chicago M3"},
        {"stage":"frozen motorway rule", "sample":"new CHI:49 tiles",
         "metric":"all candidates flagged", "value":int(hold_candidates.motorway_flag.sum()),
         "denominator":len(hold_candidates), "interpretation":"new centers, same Community Area"},
        {"stage":"candidate inventory", "sample":"new CHI:49 tiles",
         "metric":"median candidate area m2 before motorway flag", "value":float(hold_candidates.area_m2.median()),
         "denominator":len(hold_candidates), "interpretation":"selected tiles, not Chicago M3"},
        {"stage":"frozen motorway rule", "sample":"new CHI:49 tiles",
         "metric":"median candidate area m2 after motorway flag", "value":float(hold_candidates.loc[~hold_candidates.motorway_flag,"area_m2"].median()),
         "denominator":int((~hold_candidates.motorway_flag).sum()), "interpretation":"selected tiles, not Chicago M3"},
        {"stage":"frozen motorway rule", "sample":"new CHI:49 tiles",
         "metric":"negative controls inside kept candidates",
         "value":int(((hold_negative.candidate_at_point.notna()) &
                      (hold_negative.motorway_flag == False)).sum()),
         "denominator":len(hold_negative), "interpretation":"point controls, not full false-candidate census"},
        {"stage":"frozen motorway rule", "sample":"new CHI:49 tiles",
         "metric":"clear positive sketches flagged", "value":int((clear_hold.motorway_flag == True).sum()),
         "denominator":len(clear_hold), "interpretation":"two other sketches unresolved"},
        {"stage":"frozen motorway rule", "sample":"new CHI:49 tiles",
         "metric":"clear positive sketches IoU >= 0.5", "value":int(clear_hold.best_iou.ge(.5).sum()),
         "denominator":len(clear_hold), "interpretation":"rough imagery outlines, not surveyed truth"},
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "stage_metrics.csv", index=False)
    dev_decisions = dev[["component_id", "tile_id", "area_m2", "compactness", "status",
                         "area_fraction_within_40m_motorway", "motorway_flag"]].copy()
    dev_decisions["provisional_action"] = dev_decisions.motorway_flag.map(
        {True:"review_as_motorway_land", False:"review_as_possible_block"})
    dev_decisions.to_csv(OUT / "development_candidate_queue.csv", index=False)
    hold_decisions = hold_candidates[["component_id", "tile_id", "area_m2", "compactness",
                                      "motorway_area_fraction_40m", "motorway_flag"]].copy()
    hold_decisions["provisional_action"] = hold_decisions.motorway_flag.map(
        {True:"review_as_motorway_land", False:"review_as_possible_block"})
    hold_decisions.to_csv(OUT / "new_location_candidate_queue.csv", index=False)
    inputs = [
        FRESH / "positive_reference_comparison.csv", FRESH / "visual_reference.json",
        DEV / "component_inventory.csv", DEV / "inventory_review.csv",
        DEV / "motorway_context.csv", DEV / "parcel_candidate_support.csv",
        DEV / "parcel_positive_comparison.csv", HOLD / "holdout_candidates.csv",
        HOLD / "positive_comparison.csv", HOLD / "negative_comparison.csv",
        HOLD / "visual_reference.json", HOLD / "reference_review.json", CONFIG,
        OUT / "momepy_baseline_positive_comparison.csv", OUT / "momepy_baseline_summary.json",
    ]
    assessment = {
        "scope":"Chicago-only physical street blocks; existing development and small new-location pilot",
        "source_inputs":{str(path.relative_to(ROOT)):sha(path) for path in inputs},
        "gates":{
            "ordinary_alley_reconnection":{
                "status":"pilot_support", "evidence":"11 fresh rough sketches improve from raw ROW median IoU 0.386 to alley-open median 0.827"},
            "established_method_comparison":{
                "status":"pilot_tested_not_decisive", "evidence":"momepy.enclosures municipal centerlines median IoU 0.758 versus ROW/alley 0.827 on 11 rough sketches; momepy wins 5 individual sketches"},
            "motorway_island_filter":{
                "status":"pilot_support_only", "evidence":"9/9 known development islands flagged; in four new CHI:49 tiles, 22/35 candidates flagged, 0/5 clear positives flagged, 0/8 negative controls inside kept candidates"},
            "parcel_block_identity":{
                "status":"rejected", "evidence":"two distinct Loop sketches share a PIN group; false freeway islands have high parcel support"},
            "street_gap_repair":{
                "status":"failed_open", "evidence":"West Veterans Place is named in municipal/OSM linework but absent from Cook ROW/Road Edge; current land candidate merges"},
            "complete_independent_reference":{
                "status":"not_met", "evidence":"fresh sketches are selected positives, holdout omits visible full blocks and has two uncertain outlines"},
            "citywide_m3_m4_release":{
                "status":"not_authorized_by_evidence", "evidence":"gap, context and independent precision/recall gates open"},
        },
        "not_estimated":["citywide precision", "citywide recall", "boundary displacement",
                         "M4 shape error distribution", "77-area block totals"],
    }
    (OUT / "assessment.json").write_text(json.dumps(assessment, indent=2) + "\n")
    print(json.dumps({"stages":len(rows),"gates":{k:v["status"] for k,v in assessment["gates"].items()}}, indent=2))


if __name__ == "__main__":
    main()
