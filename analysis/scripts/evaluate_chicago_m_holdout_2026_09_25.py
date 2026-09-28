"""Evaluate frozen Chicago M holdout predictions against provisional labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m_holdout_2026_09_25"
QUEUE = A / "results/Chicago/chicago_m_sample_2026_09_25/m2_annotation_queue.csv"


def main():
    cases = json.loads((OUT / "case_selection.json").read_text())["cases"]
    labels = pd.read_csv(OUT / "visual_case_labels.csv", keep_default_na=False).set_index("case_id")
    receipts = json.loads((OUT / "imagery_receipts.json").read_text())["cases"]
    assert len(cases) == len(labels) == len(receipts) == 13
    assert {x["case_id"] for x in cases} == set(labels.index)
    for receipt in receipts:
        raw = ROOT / receipt["raw_path"]
        overlay = ROOT / receipt["overlay_path"]
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == receipt["image_sha256"]
        assert hashlib.sha256(overlay.read_bytes()).hexdigest() == receipt["overlay_sha256"]

    near = pd.read_csv(QUEUE).set_index("connector_a")
    rows = []
    for case in cases:
        key = case["case_id"]
        label = labels.loc[key]
        row = {"case_id": key, "family": case["family"],
               "prediction": case["rule_prediction"], "provisional_label": label.provisional_label,
               "physical_arms": label.physical_arms, "confidence": label.confidence}
        if case["family"] == "M3/M4":
            observed = "retain" if label.provisional_label.startswith("plausible_") else "exclude"
            row.update({"observed_class": observed,
                        "rule_agrees": case["rule_prediction"] == observed})
        elif case["queue_id"] in near.index:
            q = near.loc[case["queue_id"]]
            formula = int(q.a_arms_source) + int(q.b_arms_source) - 2
            row.update({"source_a_arms": int(q.a_arms_source),
                        "source_b_arms": int(q.b_arms_source),
                        "linked_pair_arm_formula": formula,
                        "formula_matches_tentative_visual_arms": formula == int(str(label.physical_arms).split("_")[0])})
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "heldout_rule_checks.csv", index=False)
    blocks = table.loc[table.family.eq("M3/M4")]
    near_pairs = table.loc[table.linked_pair_arm_formula.notna()]
    summary = {
        "case_count": len(cases),
        "image_hashes_verified": 2 * len(receipts),
        "block_cases": len(blocks),
        "block_simple_rule_agreements": int(blocks.rule_agrees.sum()),
        "block_false_retain_case_ids": blocks.loc[blocks.prediction.eq("retain") & blocks.observed_class.eq("exclude"), "case_id"].tolist(),
        "linked_near_pair_cases": len(near_pairs),
        "tentative_arm_formula_matches": int(near_pairs.formula_matches_tentative_visual_arms.sum()),
        "scope": "purposive held-out queue contrasts; not an error-rate estimate or accepted method",
    }
    (OUT / "validation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
