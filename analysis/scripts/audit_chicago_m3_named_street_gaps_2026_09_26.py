"""Screen municipal named streets absent from Cook ROW/Road Edge masks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
RAW_ROADS = A / "data/Chicago/steet_center_lines_20260915.geojson"
DISTRICTS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet"
UNITS = ["CHI:11", "CHI:32", "CHI:49", "CHI:57", "CHI:63"]
ALIGNMENT_TOLERANCE_M = 5
ALERT_MIN_UNCOVERED_RUN_M = 30


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_parts(geom) -> list:
    return [p for p in shapely.get_parts(shapely.make_valid(geom)) if p.geom_type == "LineString"]


def main() -> None:
    raw = json.loads(RAW_ROADS.read_text())
    names = {str(f["properties"].get("trans_id")): f["properties"] for f in raw["features"]}
    roads = gpd.read_parquet(ROADS)
    districts = gpd.read_parquet(DISTRICTS)
    rows = []
    for unit in UNITS:
        area = districts.loc[districts.unit_id.eq(unit)].geometry.item().buffer(-40)
        row = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        mask = shapely.union_all([row, edge]).buffer(ALIGNMENT_TOLERANCE_M)
        subset = roads.iloc[roads.sindex.query(area, predicate="intersects")]
        for _, record in subset.iterrows():
            meta = names.get(str(record["trans_id"]), {})
            street = " ".join(str(meta.get(k) or "").strip() for k in ("pre_dir", "street_nam", "street_typ", "suf_dir")).strip()
            if not street:
                continue
            inside = record.geometry.intersection(area)
            length = inside.length
            if length < ALERT_MIN_UNCOVERED_RUN_M:
                continue
            uncovered = inside.difference(mask)
            runs = sorted((p.length for p in line_parts(uncovered)), reverse=True)
            top = runs[0] if runs else 0
            rows.append({"unit_id": unit, "trans_id": record["trans_id"], "street": street,
                         "class": record["class"],
                         "line_length_in_inner_district_m": length,
                         "uncovered_length_m": uncovered.length,
                         "longest_uncovered_run_m": top,
                         "uncovered_fraction": uncovered.length / length,
                         "gap_alert": top >= ALERT_MIN_UNCOVERED_RUN_M,
                         "uncovered_wkt": uncovered.wkt if top >= ALERT_MIN_UNCOVERED_RUN_M else None})
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "named_street_gap_screen.csv", index=False)
    summary = {"units": UNITS,
               "municipal_named_segments_screened": len(table),
               "gap_alert_segments": int(table.gap_alert.sum()),
               "gap_alert_unique_streets": int(table.loc[table.gap_alert, "street"].nunique()),
               "alignment_tolerance_m": ALIGNMENT_TOLERANCE_M,
               "longest_uncovered_run_threshold_m": ALERT_MIN_UNCOVERED_RUN_M,
               "west_veterans": table.loc[table.street.str.contains("VETERANS", case=False),
                                          ["unit_id", "trans_id", "street", "longest_uncovered_run_m", "gap_alert"]].to_dict("records"),
               "by_unit": table.groupby("unit_id").gap_alert.agg(["sum", "count"]).to_dict("index"),
               "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (ROADS, RAW_ROADS, DISTRICTS)},
               "interpretation": "Screen only: a long line outside the county mask can reflect missing ROW, alignment, grade, private or inactive status. Each alert requires source and imagery adjudication before a repair."}
    (OUT / "named_street_gap_screen_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(table.loc[table.gap_alert, ["unit_id", "street", "longest_uncovered_run_m"]]
          .sort_values("longest_uncovered_run_m", ascending=False).head(20).to_string(index=False))


if __name__ == "__main__":
    main()
