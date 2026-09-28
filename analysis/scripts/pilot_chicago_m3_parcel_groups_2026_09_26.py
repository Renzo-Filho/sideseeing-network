"""Check Cook ground-parcel continuity and tax-block groups in frozen M3 cases."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
from pilot_chicago_m3_row_land_2026_09_26 import case_records

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
PARCELS = A / "data/Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024"
CASES = A / "results/Chicago/chicago_m3_external_sources_2026_09_25"
OUT = A / "results/Chicago/chicago_m3_row_land_2026_09_26"


def main():
    cases = case_records()
    roi = shapely.union_all([shapely.from_wkt(c["geometry_wkt"]).buffer(300).envelope for c in cases])
    chunks = []
    files = sorted(PARCELS.glob("part_*.parquet"))
    for file in files:
        table = pq.read_table(file, columns=["geometry", "PIN10", "PARCELTYPE", "OBJECTID"])
        geoms = shapely.from_wkb(table["geometry"].to_pylist())
        selected = np.asarray(shapely.intersects(geoms, roi), dtype=bool)
        if selected.any():
            rows = table.select(["PIN10", "PARCELTYPE", "OBJECTID"]).to_pandas().loc[selected].copy()
            rows["geometry"] = geoms[selected]
            chunks.append(rows)
    if not chunks:
        raise RuntimeError("No parcels in pilot areas")
    parcels = gpd.GeoDataFrame(pd.concat(chunks, ignore_index=True), geometry="geometry", crs=26916)
    base = parcels.loc[parcels.PARCELTYPE.eq("BaseParcel")].copy()
    base["tax_group"] = base.PIN10.str[:7]
    rows = []
    for case in cases:
        geom = shapely.from_wkt(case["geometry_wkt"])
        nearby = base.loc[base.intersects(geom)].copy()
        nearby["overlap_m2"] = nearby.geometry.intersection(geom).area
        nearby = nearby.loc[nearby.overlap_m2.gt(0)]
        if nearby.empty:
            rows.append({"case_id": case["case_id"], "label": case["label"],
                         "base_parcel_count": 0, "base_parcel_coverage_fraction": 0,
                         "dominant_tax_group": None})
            continue
        group_coverage = nearby.groupby("tax_group").overlap_m2.sum()
        dominant = group_coverage.idxmax()
        group = base.loc[base.tax_group.eq(dominant)]
        group_union = shapely.union_all(group.geometry.values)
        inside_fraction = [g.intersection(geom).area / g.area for g in nearby.geometry if g.area]
        rows.append({"case_id": case["case_id"], "label": case["label"],
                     "base_parcel_count": len(nearby),
                     "base_parcel_coverage_fraction": shapely.union_all(nearby.geometry.values).intersection(geom).area / geom.area,
                     "tax_groups_intersecting": len(group_coverage),
                     "dominant_tax_group": dominant,
                     "dominant_group_parcels_in_roi": len(group),
                     "dominant_group_union_area_m2": group_union.area,
                     "candidate_to_group_area_ratio": geom.area / group_union.area if group_union.area else np.nan,
                     "candidate_group_iou": geom.intersection(group_union).area / geom.union(group_union).area,
                     "intersecting_parcel_min_contained_fraction": min(inside_fraction),
                     "intersecting_parcel_median_contained_fraction": float(np.median(inside_fraction))})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "case_parcel_group_comparison.csv", index=False)
    (OUT / "parcel_scan_contract.json").write_text(json.dumps({
        "source": str(PARCELS.relative_to(ROOT)), "part_files_scanned": len(files),
        "parcel_rows_in_case_300m_envelopes": len(parcels),
        "base_parcel_rows": len(base),
        "method": "positive-area case intersections; dominant first-seven-digit PIN10 tax grouping as diagnostic, not certified physical block; group may extend beyond 300m ROI"
    }, indent=2) + "\n")
    print("scanned", len(files), "files; retained", len(base), "base parcels; cases", len(rows))


if __name__ == "__main__":
    main()
