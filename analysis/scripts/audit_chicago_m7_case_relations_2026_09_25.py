"""Targeted Cook M7 key/geometry audit; no full-cohort entity computation."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import duckdb
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
CAD = A / "data/Chicago/chicago_cadastral_2026_09_18"
PREV = A / "results/Chicago/chicago_m_sample_2026_09_25/m7_sample_key_relations.csv"
OUT = A / "results/Chicago/chicago_m_physical_cases_2026_09_25"
PIN10 = ["1308208021", "1308311047", "1716238028", "1710400048",
         "1710318058", "1709419111", "1903201036"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = pd.read_csv(PREV, dtype={"pin10": str}).set_index("pin10")
    assert set(PIN10).issubset(prior.index)
    con = duckdb.connect()
    con.register("keys", pd.DataFrame({"pin10": PIN10}))
    parcels = con.execute(
        "SELECT p.PIN10 AS pin10, p.OBJECTID, p.PARCELTYPE, p.geometry "
        "FROM read_parquet(?) p JOIN keys k ON p.PIN10=k.pin10",
        [str(CAD / "cook_parcels_2024/part_*.parquet")],
    ).df()
    condo = con.execute(
        "SELECT c.pin10, c.pin, c.tieback_key_pin, c.char_building_pins "
        "FROM read_parquet(?) c JOIN keys k ON c.pin10=k.pin10",
        [str(CAD / "cook_condo_2024/part_*.parquet")],
    ).df()
    rows, pairs = [], []
    for key in PIN10:
        p, c, base = parcels.loc[parcels.pin10.eq(key)], condo.loc[condo.pin10.eq(key)], prior.loc[key]
        assert len(p) == base.parcel_features
        for left, right in combinations(p.itertuples(), 2):
            a, b = shapely.from_wkb(bytes(left.geometry)), shapely.from_wkb(bytes(right.geometry))
            overlap = a.intersection(b).area
            pairs.append({"pin10": key, "objectid_a": left.OBJECTID, "type_a": left.PARCELTYPE,
                          "objectid_b": right.OBJECTID, "type_b": right.PARCELTYPE,
                          "overlap_m2": round(overlap, 3),
                          "iou": round(overlap / a.union(b).area, 5),
                          "distance_m": round(a.distance(b), 3)})
        nonnull = c.char_building_pins.dropna()
        rows.append({"unit_id": base.unit_id, "pin10": key, "stratum": base.stratum,
                     "assessor_tax_pins": int(base.assessor_tax_pins),
                     "parcel_features": len(p),
                     "parcel_type_sequence": "|".join("NULL" if pd.isna(v) else str(v) for v in p.PARCELTYPE),
                     "condo_rows": len(c), "distinct_condo_tieback_keys": c.tieback_key_pin.nunique(),
                     "distinct_building_pin_count_values": nonnull.nunique(),
                     "building_pin_count_min": nonnull.min() if len(nonnull) else None,
                     "building_pin_count_max": nonnull.max() if len(nonnull) else None,
                     "physical_entity_count": None,
                     "interpretation": "key_cardinality_and_geometry_only"})
    pd.DataFrame(rows).to_csv(OUT / "m7_case_key_relations.csv", index=False)
    pd.DataFrame(pairs).to_csv(OUT / "m7_case_parcel_pairs.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(pd.DataFrame(pairs).to_string(index=False))


if __name__ == "__main__":
    main()
