"""Independent arithmetic and scope checks for the bounded Chicago M pilot."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import shapely


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/results/Chicago/chicago_m_sample_2026_09_25"


def main():
    checks = {}
    selection = pd.read_csv(OUT / "sample_selection.csv")
    assert len(selection) == 4 and selection.unit_id.is_unique
    assert sorted(selection.m1_quartile.tolist()) == [0, 1, 2, 3]
    assert not set(selection.unit_id) & {"CHI:24", "CHI:28", "CHI:30", "CHI:32", "CHI:76"}
    checks["quartile_scope"] = True

    m1 = pd.read_csv(OUT / "m1_m6_source_diagnostic.csv")
    assert set(m1.unit_id) == set(selection.unit_id)
    assert np.allclose(m1.municipal_m6_share_sum, 1)
    assert np.allclose(m1.overture_m6_share_sum, 1)
    assert np.allclose(m1.overture_m1_km_per_km2 / m1.municipal_m1_km_per_km2,
                       m1.overture_to_municipal_m1_ratio)
    checks["m1_m6_reconciliation"] = True

    m2 = pd.read_csv(OUT / "m2_sample_summary.csv")
    pairs = pd.read_csv(OUT / "m2_annotation_queue.csv")
    assert set(m2.unit_id) == set(selection.unit_id)
    assert pairs.straight_m.between(0, 10).all()
    assert pairs.physical_junction_label.eq("unreviewed").all()
    assert not pairs.duplicated(["unit_id", "connector_a", "connector_b"]).any()
    assert m2.near_pairs_with_short_source_link.le(m2.near_pairs_10m).all()
    checks["m2_fixture_scope"] = True

    blocks = pd.read_csv(OUT / "m3_m4_sample_summary.csv")
    fixtures = pd.read_csv(OUT / "m3_m4_annotation_queue.csv")
    assert len(blocks) == 12 and set(blocks.unit_id) == set(selection.unit_id)
    assert set(blocks.groupby("unit_id").size()) == {3}
    assert blocks.candidate_count.le(blocks.candidate_count_before_rail_filter).all()
    assert blocks.candidate_share_iou_ge_050.between(0, 1).all()
    assert blocks.reference_share_iou_ge_050.between(0, 1).all()
    assert blocks.median_compactness.between(0, 1).all()
    assert blocks.median_elongation.ge(1).all()
    for row in fixtures.itertuples():
        geometry = shapely.from_wkt(row.geometry_wkt)
        assert geometry.is_valid and geometry.area > 0
        assert np.isclose(geometry.area, row.area_m2, rtol=1e-9, atol=1e-6)
    assert fixtures.physical_block_label.eq("unreviewed").all()
    checks["m3_m4_geometry_and_scope"] = True

    m7 = pd.read_csv(OUT / "m7_sample_key_relations.csv", dtype={"pin10": str})
    source_counts = pd.read_csv(OUT / "m7_selected_unit_source_counts.csv")
    dupage = pd.read_csv(OUT / "m7_dupage_stratified_queue.csv")
    assert len(m7) <= 5 * 4 * 3 + 5
    assert not m7.duplicated(["unit_id", "pin10"]).any()
    assert m7.physical_entity_count.isna().all()
    assert m7.assessor_tax_pins.ge(m7.condo_tax_pins).all()
    assert m7.assessor_tax_pins.ge(1).all()
    assert set(source_counts.unit_id) == set(selection.unit_id) | {"CHI:32"}
    assert len(dupage) <= 12
    checks["m7_bounded_source_cardinality"] = True

    payload = {"status": "passed", "checks": checks,
               "sample_units": selection.unit_id.tolist(),
               "m2_pairs_for_review": len(pairs),
               "m3_m4_polygons_for_review": len(fixtures),
               "m7_cook_pin10_groups_for_review": len(m7),
               "m7_dupage_rows_for_review": len(dupage)}
    (OUT / "validation.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
