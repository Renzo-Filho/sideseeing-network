"""Summarize unresolved M2/M3/M4 fixture pressure in both cities.

Near connector pairs are flags for inspection, not deduplicated intersections.
"""

from pathlib import Path
import csv

import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis/work/runs/sp_chicago_harmonization_2026_09_22/roads"
OUTPUT = ROOT / "analysis/results/SP_CHI/harmonization_2026_09_22_full_scope_review"
PILOTS = {"Chicago": ["24", "28", "30", "32", "76"], "SP": ["10", "30", "35"]}


def main():
    rows = []
    for city, ids in PILOTS.items():
        connectors = gpd.read_parquet(SOURCE / f"{city}_connector_candidates.parquet")
        blocks = gpd.read_parquet(SOURCE / f"{city}_enclosure_candidates.parquet")
        prefix = "CHI" if city == "Chicago" else city
        for local_id in ids:
            unit_id = f"{prefix}:{local_id}"
            c = connectors.loc[connectors.unit_id.eq(unit_id)]
            b = blocks.loc[blocks.unit_id.eq(unit_id)]
            points = np.column_stack([c.geometry.x.to_numpy(), c.geometry.y.to_numpy()])
            pairs = cKDTree(points).query_pairs(10) if len(points) else set()
            involved = {i for pair in pairs for i in pair}
            rows.append({
                "unit_id": unit_id,
                "connector_candidates": len(c),
                "connector_pairs_within_10m": len(pairs),
                "connectors_in_near_pairs": len(involved),
                "enclosure_candidates": len(b),
                "enclosures_touching_extraction_edge": int(b.extraction_edge.sum()),
                "enclosures_narrow_under_6m": int(b.narrow_under_6m.sum()),
                "enclosures_large_over_1km2": int(b.large_over_1km2.sum()),
            })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "paired_m2_m3_m4_pilot_flags.csv").open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
