"""Bounded M7 source-cardinality audit for five Chicago Community Areas.

The four units are selected by the companion M2-M4 pilot; Loop is an explicit
condominium stress fixture. This tests source-key relations, not physical entity
identity. Only a few PIN10 groups per property stratum are joined to parcels.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m_sample_2026_09_25"
CAD = A / "data/Chicago/chicago_cadastral_2026_09_18"


def parquet_glob(name):
    return str(CAD / name / "part_*.parquet")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sample = pd.read_csv(OUT / "sample_selection.csv")
    units = [int(x.split(":")[1]) for x in sample.unit_id] + [32]
    con = duckdb.connect()
    universe = con.execute(
        "SELECT pin, pin10, class, TRY_CAST(chicago_community_area_num AS INTEGER) AS unit_num "
        "FROM read_parquet(?) WHERE TRY_CAST(chicago_community_area_num AS INTEGER) IN (SELECT UNNEST(?))",
        [parquet_glob("cook_universe_2024"), units],
    ).df()
    assert universe.pin.notna().all() and universe.pin10.notna().all()
    universe["is_condo"] = universe["class"].astype(str).eq("299")
    universe["is_commercial"] = universe["class"].astype(str).str.match(r"^[57]")
    universe["is_exempt"] = universe["class"].astype(str).eq("EX")
    grouped = universe.groupby(["unit_num", "pin10"], as_index=False).agg(
        assessor_tax_pins=("pin", "nunique"), condo_tax_pins=("is_condo", "sum"),
        commercial_tax_pins=("is_commercial", "sum"), exempt_tax_pins=("is_exempt", "sum"),
    )
    grouped["stratum"] = np.select(
        [grouped.condo_tax_pins.gt(0), grouped.commercial_tax_pins.gt(0),
         grouped.exempt_tax_pins.gt(0)],
        ["condominium", "commercial", "exempt"], default="other",
    )
    rng = np.random.default_rng(20260925)
    selected = []
    for unit in units:
        unit_groups = grouped.loc[grouped.unit_num.eq(unit)]
        for stratum in ["condominium", "commercial", "exempt", "other"]:
            choices = unit_groups.loc[unit_groups.stratum.eq(stratum)]
            if len(choices):
                indices = rng.choice(choices.index.to_numpy(), min(3, len(choices)), replace=False)
                selected.extend(indices)
    # Oversample the known stress case separately rather than claiming it is random.
    loop_condo = grouped.loc[grouped.unit_num.eq(32) & grouped.stratum.eq("condominium")]
    selected.extend(loop_condo.nlargest(5, "assessor_tax_pins").index.to_list())
    selected = grouped.loc[sorted(set(selected))].copy().reset_index(drop=True)
    selected["unit_id"] = selected.unit_num.map(lambda x: f"CHI:{x:02d}")
    selected["sampling_role"] = np.where(
        selected.unit_num.eq(32) & selected.pin10.isin(loop_condo.nlargest(5, "assessor_tax_pins").pin10),
        "targeted_Loop_high_cardinality_stress", "seeded_property_stratum",
    )
    keys = selected[["pin10"]].drop_duplicates()
    con.register("sample_keys", keys)
    parcels = con.execute(
        "SELECT p.PIN10 AS pin10, p.OBJECTID, p.PARCELTYPE, p.crosses_chicago_boundary "
        "FROM read_parquet(?) p JOIN sample_keys k ON p.PIN10=k.pin10",
        [parquet_glob("cook_parcels_2024")],
    ).df()
    condo = con.execute(
        "SELECT c.pin10, c.pin, c.tieback_key_pin, c.char_building_pins, "
        "c.is_parking_space, c.is_common_area "
        "FROM read_parquet(?) c JOIN sample_keys k ON c.pin10=k.pin10",
        [parquet_glob("cook_condo_2024")],
    ).df()
    residential = con.execute(
        "SELECT r.pin, LEFT(r.pin,10) AS pin10, r.tieback_key_pin, r.card "
        "FROM read_parquet(?) r JOIN sample_keys k ON LEFT(r.pin,10)=k.pin10",
        [parquet_glob("cook_residential_2024")],
    ).df()
    rows = []
    for row in selected.itertuples():
        p = parcels.loc[parcels.pin10.eq(row.pin10)]
        c = condo.loc[condo.pin10.eq(row.pin10)]
        r = residential.loc[residential.pin10.eq(row.pin10)]
        tiebacks = c.tieback_key_pin.fillna("").astype(str)
        tiebacks = tiebacks.loc[tiebacks.ne("")]
        rows.append({
            "unit_id": row.unit_id, "pin10": row.pin10, "stratum": row.stratum,
            "sampling_role": row.sampling_role,
            "assessor_tax_pins": row.assessor_tax_pins,
            "condo_tax_pins": row.condo_tax_pins,
            "commercial_tax_pins": row.commercial_tax_pins,
            "exempt_tax_pins": row.exempt_tax_pins,
            "parcel_features": len(p),
            "parcel_types": "|".join(sorted(p.PARCELTYPE.dropna().astype(str).unique())),
            "parcel_crosses_city": bool(p.crosses_chicago_boundary.fillna(False).any()),
            "condo_characteristic_rows": len(c),
            "distinct_condo_tiebacks": tiebacks.nunique(),
            "condo_tieback_examples": "|".join(sorted(tiebacks.unique())[:3]),
            "residential_cards": len(r),
            "physical_entity_count": None,
            "review_status": "source_key_diagnostic_not_entity_decision",
        })
    detail = pd.DataFrame(rows)
    detail.to_csv(OUT / "m7_sample_key_relations.csv", index=False)
    full_summary = grouped.groupby(["unit_num", "stratum"], as_index=False).agg(
        pin10_groups=("pin10", "size"),
        assessor_tax_pins=("assessor_tax_pins", "sum"),
        multi_pin10_groups=("assessor_tax_pins", lambda x: int((x > 1).sum())),
    )
    full_summary["unit_id"] = full_summary.unit_num.map(lambda x: f"CHI:{x:02d}")
    full_summary.to_csv(OUT / "m7_selected_unit_source_counts.csv", index=False)
    # DuPage scope is only 81 records; take class-stratified fixtures, not a
    # fabricated physical-entity count from county-qualified parcel keys.
    dupage = pq.read_table(CAD / "dupage_parcels_current/part_00000.parquet").to_pandas()
    class_col = "REA017_PROP_CLASS"
    dupage["source_class"] = dupage[class_col].fillna("missing").astype(str)
    drows = []
    for source_class, group in dupage.groupby("source_class", dropna=False):
        chosen = group.sample(min(3, len(group)), random_state=20260925)
        for item in chosen.itertuples():
            drows.append({"source_class": source_class, "source_row": item.Index,
                          "review_status": "DuPage_parcel_only_no_parent_or_improvement_identity"})
    pd.DataFrame(drows).to_csv(OUT / "m7_dupage_stratified_queue.csv", index=False)
    print("Cook units", units, "sample PIN10 groups", len(detail),
          "DuPage class fixtures", len(drows), flush=True)


if __name__ == "__main__":
    main()
