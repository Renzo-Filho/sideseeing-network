"""Screen frozen named-street gap alerts for parcel-guided repair effects.

This is a triage audit. It does not adjudicate street status or approve splits.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from evaluate_chicago_m3_fresh_tiles_2026_09_26 import source_geometries
from pilot_chicago_m3_veterans_repair_2026_09_27 import local_parcels

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_named_gap_repair_2026_09_27"
GAPS = A / "results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26/named_street_gap_screen.csv"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"


def pieces(geom, roi):
    return [part for part in shapely.get_parts(shapely.make_valid(roi.difference(geom)))
            if part.geom_type == "Polygon" and part.area > 1]


def isolated(components, roi):
    return [part for part in components if not part.boundary.intersects(roi.boundary)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    alerts = pd.read_csv(GAPS).loc[lambda d: d.gap_alert].copy()
    assert len(alerts) == 11
    roads = gpd.read_parquet(ROADS)
    roads.trans_id = roads.trans_id.astype(str)
    rows = []
    for unit, group in alerts.groupby("unit_id"):
        source = source_geometries(unit, "row", lambda p: p.get("ROWTYPE") in (1, 4, 5))
        edge = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 1)
        alley = source_geometries(unit, "road_edge", lambda p: p.get("TYPE") == 5)
        mask = shapely.union_all([source, edge]).difference(alley.buffer(3))
        lines = {}
        for _, alert in group.iterrows():
            matched = roads.loc[roads.trans_id.eq(str(alert.trans_id))]
            assert len(matched) == 1, (unit, alert.trans_id, len(matched))
            lines[int(alert.trans_id)] = matched.geometry.item()
        whole_roi = shapely.union_all([line.buffer(120) for line in lines.values()])
        parcels = local_parcels(whole_roi)
        base = parcels.loc[parcels.PARCELTYPE.eq("BaseParcel")]
        print(unit, "alerts", len(group), "local BaseParcels", len(base), flush=True)
        for _, alert in group.iterrows():
            line = lines[int(alert.trans_id)]
            roi = line.buffer(120)
            near = base.loc[base.intersects(roi)]
            nonparcel = roi.difference(shapely.union_all(near.geometry.values))
            corridor = nonparcel.intersection(line.buffer(10))
            repaired = shapely.union_all([mask, corridor])
            baseline_faces = pieces(mask, roi)
            repaired_faces = pieces(repaired, roi)
            before = isolated(baseline_faces, roi)
            after = isolated(repaired_faces, roi)
            line_length = line.length
            rows.append({"unit_id": unit, "trans_id": int(alert.trans_id),
                         "street": alert.street, "street_class": int(alert["class"]),
                         "uncovered_run_m": float(alert.longest_uncovered_run_m),
                         "full_line_length_m": line_length,
                         "line_inside_baseparcels_fraction": line.intersection(shapely.union_all(near.geometry.values)).length/line_length,
                         "local_baseparcel_count": len(near),
                         "new_corridor_area_m2": corridor.difference(mask).area,
                         "baseline_closed_faces": len(before),
                         "repaired_closed_faces": len(after),
                         "closed_face_count_delta": len(after)-len(before),
                         "baseline_closed_face_areas_m2": sorted(round(p.area, 1) for p in before),
                         "repaired_closed_face_areas_m2": sorted(round(p.area, 1) for p in after),
                         "screen_status": "requires road-grade/status and property-side review"})
    data = pd.DataFrame(rows).sort_values(["unit_id", "street", "trans_id"])
    data.to_csv(OUT / "named_gap_repair_screen.csv", index=False)
    geojson = A / "work/chicago_m3_row_land_2026_09_26"
    source_files = [GAPS, ROADS] + [geojson / f"{unit.replace(':', '_')}_{kind}.geojson"
                                    for unit in sorted(data.unit_id.unique()) for kind in ("row", "road_edge")]
    summary = {"alert_count": len(data), "street_names": int(data.street.nunique()),
               "units": sorted(data.unit_id.unique().tolist()),
               "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_files},
               "closed_face_delta_counts": data.closed_face_count_delta.value_counts().sort_index().to_dict(),
               "status": "topology and source-support screen only; none of the 11 alerts is an accepted repair"}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(data.drop(columns=["baseline_closed_face_areas_m2", "repaired_closed_face_areas_m2", "screen_status"]).to_string(index=False))


if __name__ == "__main__":
    main()
