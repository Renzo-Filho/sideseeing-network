"""Inspect the C_M3_01 ROW merge against parcels and the cached orthophoto."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq
import shapely
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
OUT = A / "results/Chicago/chicago_m3_row_land_2026_09_26"
WORK = A / "work/chicago_m3_row_land_2026_09_26"
PLOTS = OUT / "maps"
TO_METRIC = Transformer.from_crs(4326, 26916, always_xy=True).transform
TO_LONLAT = Transformer.from_crs(26916, 4326, always_xy=True).transform


def geoms(source):
    features = json.loads((WORK / f"CHI_11_{source}.geojson").read_text())["features"]
    return gpd.GeoDataFrame([f["properties"] for f in features],
                            geometry=[shapely.make_valid(transform(TO_METRIC, shape(f["geometry"])))
                                      for f in features], crs=26916)


def draw_geom(ax, geom, **kw):
    for part in shapely.get_parts(shapely.make_valid(geom)):
        if part.geom_type == "Polygon":
            coords = shapely.get_coordinates(transform(TO_LONLAT, part.exterior))
            ax.plot(coords[:, 0], coords[:, 1], **kw)


def main():
    receipt = json.loads((A / "results/Chicago/chicago_m3_external_sources_2026_09_25/imagery_receipts.json").read_text())
    case = next(c for c in receipt["cases"] if c["case_id"] == "C_M3_01")
    candidate = shapely.from_wkt(case["geometry_wkt"])
    roi = candidate.buffer(150)
    files = sorted((A / "data/Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024").glob("part_*.parquet"))
    retained = []
    for file in files:
        table = pq.read_table(file, columns=["geometry", "PIN10", "PARCELTYPE", "OBJECTID"])
        gs = shapely.from_wkb(table["geometry"].to_pylist())
        keep = np.asarray(shapely.intersects(gs, roi), dtype=bool)
        if keep.any():
            props = table.select(["PIN10", "PARCELTYPE", "OBJECTID"]).to_pandas().loc[keep].copy()
            props["geometry"] = gs[keep]
            retained.append(props)
    import pandas as pd
    parcels = gpd.GeoDataFrame(pd.concat(retained, ignore_index=True), geometry="geometry", crs=26916)
    base = parcels.loc[parcels.PARCELTYPE.eq("BaseParcel")].copy()
    base["tax_group"] = base.PIN10.str[:7]
    row = geoms("row")
    road = row.loc[row.ROWTYPE.isin([1, 4, 5])]
    edge = geoms("road_edge")
    ordinary = edge.loc[edge.TYPE.eq(1)]
    alley = edge.loc[edge.TYPE.eq(5)]
    road_mask = shapely.union_all(road.geometry.values)
    ordinary_mask = shapely.union_all(ordinary.geometry.values)
    alley_mask = shapely.union_all(alley.geometry.values)
    municipal = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet")
    veterans = municipal.loc[municipal.trans_id.eq("154550")].geometry.item()
    nonparcel = roi.difference(shapely.union_all(base.geometry.values))
    gap_sensitivity = []
    for width in (6, 8, 10, 12, 15, 20):
        missing_street = nonparcel.intersection(veterans.buffer(width)).difference(road_mask)
        mask = shapely.union_all([road_mask, missing_street]).difference(alley_mask.buffer(1))
        components = [p for p in shapely.get_parts(roi.difference(mask))
                      if p.geom_type == "Polygon" and p.area > 0]
        best = max(components, key=lambda p: p.intersection(candidate).area)
        candidate_land = candidate.difference(mask)
        gap_sensitivity.append({"municipal_centerline_search_width_m": width,
                                "inferred_gap_area_m2": missing_street.area,
                                "best_component_area_m2": best.area,
                                "best_component_iou_to_candidate_land":
                                    best.intersection(candidate_land).area / best.union(candidate_land).area,
                                "best_component_touches_roi_edge": best.boundary.intersects(roi.boundary)})
    candidate_parcels = base.loc[base.intersection(candidate).area.gt(0)]
    north = base.loc[base.intersection(candidate.buffer(70)).area.gt(0)]
    north = north.loc[north.intersection(candidate).area.le(0.01)]
    selected = base.loc[base.intersects(roi)]
    image = Image.open(ROOT / case["raw_path"])
    e = case["returned_extent"]
    fig, ax = plt.subplots(figsize=(10, 10), dpi=140)
    ax.imshow(image, extent=[e["xmin"], e["xmax"], e["ymin"], e["ymax"]], origin="upper")
    for g in road.geometry:
        if g.intersects(roi): draw_geom(ax, g, color="magenta", linewidth=1.3, alpha=.8)
    for g in ordinary.geometry:
        if g.intersects(roi): draw_geom(ax, g, color="cyan", linewidth=.9, alpha=.8)
    for g in alley.geometry:
        if g.intersects(roi): draw_geom(ax, g, color="orange", linewidth=.7, alpha=.8)
    for g in selected.geometry: draw_geom(ax, g, color="yellow", linewidth=1.1, alpha=.85)
    draw_geom(ax, candidate, color="red", linewidth=2.5)
    for _, p in selected.loc[selected.intersects(candidate.buffer(35))].iterrows():
        x, y = transform(TO_LONLAT, p.geometry.representative_point()).coords[0]
        if e["xmin"] <= x <= e["xmax"] and e["ymin"] <= y <= e["ymax"]:
            ax.text(x, y, str(p.PIN10), fontsize=5, color="black",
                    bbox={"facecolor": "white", "alpha": .7, "pad": .2})
    ax.set_xlim(e["xmin"], e["xmax"])
    ax.set_ylim(e["ymin"], e["ymax"])
    ax.set_title("C_M3_01: red candidate, magenta road ROW, cyan road edge, yellow parcels, orange alleys")
    ax.set_axis_off()
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(PLOTS / "C_M3_01_parcel_orthophoto.png")
    plt.close(fig)
    summary = {
        "candidate_area_m2": candidate.area,
        "candidate_base_parcel_count": len(candidate_parcels),
        "candidate_parcel_pin10": sorted(candidate_parcels.PIN10.dropna().unique().tolist()),
        "candidate_parcel_tax_groups": sorted(candidate_parcels.tax_group.dropna().unique().tolist()),
        "adjacent_70m_parcel_count": len(north),
        "adjacent_70m_tax_groups": sorted(north.tax_group.dropna().unique().tolist()),
        "candidate_road_row_overlap_m2": candidate.intersection(road_mask).area,
        "candidate_ordinary_road_edge_overlap_m2": candidate.intersection(ordinary_mask).area,
        "road_row_features_near_candidate": int(road.intersects(roi).sum()),
        "ordinary_road_edge_features_near_candidate": int(ordinary.intersects(roi).sum()),
        "alley_features_near_candidate": int(alley.intersects(roi).sum()),
        "municipal_veterans_place_trans_id": "154550",
        "municipal_centerline_length_within_north_8m_band_m":
            veterans.intersection(shapely.LineString([(436878, 4646625), (436960, 4646679)]).buffer(8)).length,
        "street_gap_sensitivity": gap_sensitivity,
    }
    (OUT / "c_m3_01_parcel_orthophoto_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
