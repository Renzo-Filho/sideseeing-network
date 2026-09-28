"""Quantify a parcel-gap repair at W Veterans Place without accepting it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
from PIL import Image

from review_chicago_m3_c_m3_01_2026_09_26 import geoms

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_veterans_repair_2026_09_27"
PARCELS = A / "data/Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024"
ROADS = A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet"
CASE = A / "results/Chicago/chicago_m3_external_sources_2026_09_25/challenge_case_selection.json"
IMAGE = A / "work/chicago_m3_external_sources_2026_09_25/imagery/C_M3_01_raw.jpg"
PIN10 = {"1309323015", "1309323016", "1309323017", "1309323018", "1309323019", "1309323020"}


def local_parcels(roi):
    selected = []
    for file in sorted(PARCELS.glob("part_*.parquet")):
        table = pq.read_table(file, columns=["geometry", "PIN10", "PARCELTYPE"])
        geometry = shapely.from_wkb(table["geometry"].to_pylist())
        hit = np.asarray(shapely.intersects(geometry, roi), dtype=bool)
        if hit.any():
            frame = table.select(["PIN10", "PARCELTYPE"]).to_pandas().loc[hit].copy()
            frame["geometry"] = geometry[hit]
            selected.append(frame)
    return gpd.GeoDataFrame(pd.concat(selected, ignore_index=True), geometry="geometry", crs=26916)


def faces(roi, mask):
    return [g for g in shapely.get_parts(shapely.make_valid(roi.difference(mask)))
            if g.geom_type == "Polygon" and g.area > 1]


def score(roi, mask, parcel_core, visual, label, search_m=None):
    components = faces(roi, mask)
    best = max(components, key=lambda g: g.intersection(parcel_core).area)
    visual_best = max(components, key=lambda g: g.intersection(visual).area)
    covered = best.intersection(parcel_core).area / parcel_core.area
    return {"variant": label, "search_width_m": search_m,
            "face_count_roi": len(components), "core_face_area_m2": best.area,
            "parcel_core_area_m2": parcel_core.area,
            "parcel_core_coverage": covered,
            "iou_to_parcel_union": best.intersection(parcel_core).area / best.union(parcel_core).area,
            "iou_to_visual_outline": best.intersection(visual).area / best.union(visual).area,
            "core_face_touches_roi_edge": best.boundary.intersects(roi.boundary),
            "visual_best_same_as_parcel_anchored": best.equals(visual_best),
            "visual_best_area_m2": visual_best.area,
            "core_face_wkt": best.wkt}, best


def draw(ax, geom, **style):
    for part in shapely.get_parts(shapely.make_valid(geom)):
        if part.geom_type == "Polygon":
            ax.plot(*part.exterior.xy, **style)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    case = next(c for c in json.loads(CASE.read_text())["cases"] if c["case_id"] == "C_M3_01")
    visual = shapely.from_wkt(case["geometry_wkt"])
    roi = visual.buffer(150)
    parcels = local_parcels(roi)
    base = parcels.loc[parcels.PARCELTYPE.eq("BaseParcel")]
    core = base.loc[base.PIN10.isin(PIN10)]
    assert set(core.PIN10) == PIN10
    parcel_core = shapely.union_all(core.geometry.values)
    nonparcel = roi.difference(shapely.union_all(base.geometry.values))
    row = geoms("row")
    edge = geoms("road_edge")
    row_only = shapely.union_all(row.loc[row.ROWTYPE.isin([1, 4, 5])].geometry.values)
    county = shapely.union_all([row_only, shapely.union_all(edge.loc[edge.TYPE.eq(1)].geometry.values)])
    alley = shapely.union_all(edge.loc[edge.TYPE.eq(5)].geometry.values)
    roads = gpd.read_parquet(ROADS)
    roads.trans_id = roads.trans_id.astype(str)
    line = roads.loc[roads.trans_id.eq("154550")].geometry.item()
    assert 95 < line.length < 101

    output, shapes = [], {}
    for source_name, source in (("row_only", row_only), ("row_plus_road_edge", county)):
        for alley_open_m in (1, 3):
            baseline = source.difference(alley.buffer(alley_open_m))
            datum, face = score(roi, baseline, parcel_core, visual, "baseline")
            datum["alley_open_m"] = alley_open_m
            datum["source_mask"] = source_name
            datum["operation_order"] = "baseline"
            shapes[(source_name, alley_open_m, "baseline")] = face
            output.append(datum)
            for width in (6, 8, 10, 12, 15, 20):
                corridor = nonparcel.intersection(line.buffer(width))
                mask = shapely.union_all([baseline, corridor])
                datum, face = score(roi, mask, parcel_core, visual, "parcel_gap", width)
                datum["alley_open_m"] = alley_open_m
                datum["source_mask"] = source_name
                datum["operation_order"] = "reopen_alley_before_repair"
                datum["added_corridor_area_m2"] = corridor.difference(baseline).area
                datum["corridor_parcel_overlap_m2"] = corridor.intersection(parcel_core).area
                shapes[(source_name, alley_open_m, str(width))] = face
                output.append(datum)
                reopened_repair = shapely.union_all([source, corridor]).difference(alley.buffer(alley_open_m))
                datum, _ = score(roi, reopened_repair, parcel_core, visual, "parcel_gap", width)
                datum["alley_open_m"] = alley_open_m
                datum["source_mask"] = source_name
                datum["operation_order"] = "reopen_alley_after_repair"
                datum["added_corridor_area_m2"] = corridor.difference(baseline).area
                datum["corridor_parcel_overlap_m2"] = corridor.intersection(parcel_core).area
                output.append(datum)
                old_gap = corridor.difference(source)
                old_mask = shapely.union_all([source, old_gap]).difference(alley.buffer(alley_open_m))
                datum, _ = score(roi, old_mask, parcel_core, visual, "parcel_gap", width)
                datum["alley_open_m"] = alley_open_m
                datum["source_mask"] = source_name
                datum["operation_order"] = "subtract_existing_road_then_reopen_alley"
                datum["added_corridor_area_m2"] = old_gap.area
                datum["corridor_parcel_overlap_m2"] = corridor.intersection(parcel_core).area
                datum["mask_difference_from_direct_union_m2"] = old_mask.symmetric_difference(reopened_repair).area
                output.append(datum)
                for grid_m in (0.01, 0.1):
                    snapped_mask = shapely.set_precision(old_mask, grid_m)
                    datum, _ = score(roi, snapped_mask, parcel_core, visual, "parcel_gap", width)
                    datum["alley_open_m"] = alley_open_m
                    datum["source_mask"] = source_name
                    datum["operation_order"] = "subtract_existing_road_then_snap_mask"
                    datum["precision_grid_m"] = grid_m
                    output.append(datum)

    full = pd.DataFrame(output)
    full.to_csv(OUT / "repair_sensitivity.csv", index=False)
    compact = json.loads(full.drop(columns=["core_face_wkt"]).to_json(orient="records"))
    geojson = A / "work/chicago_m3_row_land_2026_09_26"
    summary = {"case_id": "C_M3_01", "municipal_trans_id": "154550",
               "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in (CASE, ROADS, geojson / "CHI_11_row.geojson",
                                              geojson / "CHI_11_road_edge.geojson")},
               "parcel_core_sha256_wkb": hashlib.sha256(parcel_core.wkb).hexdigest(),
               "reference_status": "six BaseParcels and one previously viewed rough visual outline; diagnostic, not independent validation",
               "method_status": "width sweep is not a frozen general repair rule",
               "results": compact}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    x, y, h = case["x"], case["y"], case["half_width_m"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 6), dpi=160)
    for ax, key, title in zip(axes, ("baseline", "6", "15"),
                              ("Current ROW + Road Edge", "Parcel gap: 6 m search", "Parcel gap: 15 m search")):
        ax.imshow(Image.open(IMAGE), extent=(x-h, x+h, y-h, y+h))
        draw(ax, shapes[("row_plus_road_edge", 3, key)], color="red", linewidth=1.5)
        draw(ax, parcel_core, color="yellow", linewidth=1.1)
        for segment in shapely.get_parts(line):
            if segment.geom_type == "LineString":
                ax.plot(*segment.xy, color="cyan", linewidth=1)
        ax.set(xlim=(x-h, x+h), ylim=(y-h, y+h), title=title)
        ax.set_aspect("equal")
        ax.set_axis_off()
    fig.suptitle("W Veterans Place: red = candidate land face, yellow = six parcel union, cyan = street line")
    fig.tight_layout()
    fig.savefig(OUT / "repair_sensitivity_overlay.png")
    plt.close(fig)
    print(full.drop(columns=["core_face_wkt"]).to_string(index=False))


if __name__ == "__main__":
    main()
