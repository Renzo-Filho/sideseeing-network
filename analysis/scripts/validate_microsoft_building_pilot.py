"""Independent arithmetic and source-support checks for the paired pilot."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/SP_CHI/microsoft_footprints_2026_09_22_review/pilot"


def main():
    candidate = pd.read_csv(OUT / "paired_microsoft_pilot.csv")
    original = pd.read_csv(A / "results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv")
    tiles = json.loads((OUT / "tile_diagnostics.json").read_text())
    repairs = json.loads((OUT / "working_geometry_repairs.json").read_text())
    m = candidate.merge(original[["unit_id", "gross_area_m2", "land_area_m2", "B1_coverage_land", "B1_coverage_gross"]],
                        on="unit_id", how="left", validate="one_to_one", suffixes=("", "_reference"))
    checks = []

    def add(name, passed, detail=None):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    expected = {"CHI:24", "CHI:28", "CHI:30", "CHI:32", "CHI:76", "SP:10", "SP:30", "SP:35"}
    add("eight_expected_pilots", set(m.unit_id) == expected and len(m) == 8)
    add("no_missing_reference_or_pilot_values", m[["land_area_m2", "gross_area_m2", "microsoft_B1_coverage_land", "overture_B1_coverage_land"]].notna().all().all())
    for row in m.itertuples():
        add(f"{row.unit_id}_land_fraction_reconstructed",
            abs(row.microsoft_union_land_m2 / row.land_area_m2 - row.microsoft_B1_coverage_land) < 1e-10)
        add(f"{row.unit_id}_gross_fraction_reconstructed",
            abs(row.microsoft_union_gross_m2 / row.gross_area_m2 - row.microsoft_B1_coverage_gross) < 1e-10)
        add(f"{row.unit_id}_baseline_same_support",
            abs(row.overture_B1_coverage_land - row.B1_coverage_land) < 1e-12 and
            abs(row.overture_B1_coverage_gross - row.B1_coverage_gross) < 1e-12)
        add(f"{row.unit_id}_source_union_bounds",
            -0.01 <= row.microsoft_union_land_m2 <= row.land_area_m2 + 0.01 and
            -0.01 <= row.microsoft_union_gross_m2 <= min(row.gross_area_m2, row.microsoft_summed_gross_m2) + 0.01)
        add(f"{row.unit_id}_difference_reconstructed",
            abs(100 * (row.microsoft_B1_coverage_land - row.overture_B1_coverage_land) - row.B1_difference_percentage_points) < 1e-10)
        add(f"{row.unit_id}_height_support_bounds",
            0 <= row.microsoft_positive_height_count <= row.microsoft_building_count_intersecting and
            0 <= row.microsoft_positive_height_count_fraction <= 1 and
            0 <= row.microsoft_positive_height_summed_area_fraction <= 1)
    sp_tiles = [row for row in tiles if row["city"] == "SP"]
    add("all_SP_tile_heights_missing", len(sp_tiles) == 3 and
        sum(row["records"] for row in sp_tiles) == 2035929 and
        all(row["positive_height"] == 0 and row["height_missing_minus_one"] == row["records"] for row in sp_tiles))
    add("four_small_working_repairs", len(repairs) == 4 and all(abs(row["area_delta_m2"]) < 0.01 for row in repairs))
    result = {"passed": all(row["passed"] for row in checks), "checks": checks}
    (OUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"{sum(row['passed'] for row in checks)}/{len(checks)} checks passed")
    if not result["passed"]:
        raise ValueError("Pilot validation failed")


if __name__ == "__main__":
    main()
