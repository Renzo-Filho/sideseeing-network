"""Paired Microsoft footprint/height pilots, with unchanged Overture B1 reference."""

import csv
import gzip
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import orjson
import pandas as pd
import shapely

from harmonization.geometry import union_coverage, polygonal


ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
REVIEW = A / "results/SP_CHI/microsoft_footprints_2026_09_22_review"
OUT = REVIEW / "pilot"
PILOTS = {"Chicago": ["24", "28", "30", "32", "76"], "SP": ["10", "30", "35"]}
INPUTS = {
    "Chicago": ("CHI", "Chicago/chi_local_2026_09_16_v1/districts.parquet", "Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet"),
    "SP": ("SP", "SP/sp_prep_2026_09_10_v3/N02/districts.parquet", "SP/sp_prep_2026_09_10_v3/N02/district_land.parquet"),
}


def batches(source, size=20000):
    while True:
        lines = [source.readline() for _ in range(size)]
        lines = [line for line in lines if line]
        if not lines:
            return
        yield lines


def inspect_city(city, manifest, baseline):
    prefix, district_path, land_path = INPUTS[city]
    districts = gpd.read_parquet(A / "work/prepared" / district_path)
    land = gpd.read_parquet(A / "work/prepared" / land_path)
    if city == "SP":
        districts["unit_id"] = "SP:" + districts.district_id.astype(str).str.zfill(2)
        land["unit_id"] = "SP:" + land.district_id.astype(str).str.zfill(2)
    ids = [f"{prefix}:{i}" for i in PILOTS[city]]
    pilot = districts.loc[districts.unit_id.isin(ids)].copy()
    pilot_wgs84 = pilot.to_crs(4326).geometry.union_all()
    city_wgs84 = districts.to_crs(4326).geometry.union_all()
    shapely.prepare(pilot_wgs84)
    shapely.prepare(city_wgs84)
    city_bounds = city_wgs84.bounds
    pilot_bounds = pilot_wgs84.bounds
    selected = []
    diagnostics = []
    for row in manifest:
        if row["city"] != prefix:
            continue
        tile = A / "data" / city / "microsoft_buildings_2026_08_13/raw_tiles" / f"{row['quadkey']}.geojsonl.gz"
        source_hash = hashlib.file_digest(tile.open("rb"), "sha256").hexdigest()
        if source_hash != row["sha256"]:
            raise ValueError(f"Source tile hash changed: {tile}")
        counts = {"records": 0, "positive_height": 0, "height_missing_minus_one": 0,
                  "confidence_missing_minus_one": 0, "invalid_geometry": 0,
                  "intersect_city": 0, "intersect_pilots": 0}
        with gzip.open(tile, "rb") as source:
            for lines in batches(source):
                records = [orjson.loads(line) for line in lines]
                geometry = shapely.from_geojson([line.decode() for line in lines])
                properties = [record["properties"] for record in records]
                counts["records"] += len(records)
                counts["positive_height"] += sum(p["height"] > 0 for p in properties)
                counts["height_missing_minus_one"] += sum(p["height"] == -1 for p in properties)
                counts["confidence_missing_minus_one"] += sum(p["confidence"] == -1 for p in properties)
                counts["invalid_geometry"] += int((~shapely.is_valid(geometry)).sum())
                bounds = shapely.bounds(geometry)
                city_box = ((bounds[:, 0] <= city_bounds[2]) & (bounds[:, 2] >= city_bounds[0]) &
                            (bounds[:, 1] <= city_bounds[3]) & (bounds[:, 3] >= city_bounds[1]))
                in_city = np.zeros(len(geometry), dtype=bool)
                in_city[city_box] = shapely.intersects(geometry[city_box], city_wgs84)
                counts["intersect_city"] += int(in_city.sum())
                pilot_box = ((bounds[:, 0] <= pilot_bounds[2]) & (bounds[:, 2] >= pilot_bounds[0]) &
                             (bounds[:, 1] <= pilot_bounds[3]) & (bounds[:, 3] >= pilot_bounds[1]))
                in_pilot = np.zeros(len(geometry), dtype=bool)
                in_pilot[pilot_box] = shapely.intersects(geometry[pilot_box], pilot_wgs84)
                counts["intersect_pilots"] += int(in_pilot.sum())
                if in_pilot.any():
                    g = gpd.GeoSeries(geometry[in_pilot], crs=4326).to_crs(districts.crs).array
                    selected.extend(zip(g, (properties[i]["height"] for i in np.flatnonzero(in_pilot)),
                                        (properties[i]["confidence"] for i in np.flatnonzero(in_pilot))))
        if counts["records"] != row["record_lines"]:
            raise ValueError(f"Record count changed: {tile}")
        diagnostics.append({"city": prefix, "quadkey": row["quadkey"], **counts})
        print(prefix, row["quadkey"], counts, flush=True)
    buildings = gpd.GeoDataFrame({"height_m": [x[1] for x in selected],
                                  "confidence": [x[2] for x in selected]},
                                 geometry=[x[0] for x in selected], crs=districts.crs)
    repairs = []
    for index in np.flatnonzero(~buildings.is_valid.to_numpy()):
        source_geometry = buildings.geometry.iloc[index]
        fixed = polygonal(source_geometry)
        if fixed.is_empty or not fixed.is_valid or fixed.area <= 0:
            raise ValueError(f"Microsoft pilot geometry cannot be repaired: {city} index {index}")
        repairs.append({"city": prefix, "pilot_record_index": int(index),
                        "reason": shapely.is_valid_reason(source_geometry),
                        "area_before_m2": source_geometry.area, "area_after_m2": fixed.area,
                        "area_delta_m2": fixed.area - source_geometry.area})
        buildings.at[index, "geometry"] = fixed
    output = []
    for z in pilot.sort_values("unit_id").itertuples():
        support = land.loc[land.unit_id.eq(z.unit_id)].geometry.item().intersection(z.geometry)
        indexes = buildings.sindex.query(z.geometry, predicate="intersects")
        subset = buildings.iloc[indexes].copy()
        gross, on_land, summed = union_coverage(subset, z.geometry, support)
        pieces = shapely.intersection(subset.geometry.values, z.geometry)
        area = shapely.area(pieces)
        positive = subset.height_m.to_numpy() > 0
        count = len(subset)
        valid_count = int(positive.sum())
        valid_area = float(area[positive].sum())
        total_area = float(area.sum())
        original = baseline.loc[baseline.unit_id.eq(z.unit_id)].iloc[0]
        output.append({
            "unit_id": z.unit_id, "microsoft_building_count_intersecting": count,
            "microsoft_positive_height_count": valid_count,
            "microsoft_positive_height_count_fraction": valid_count / count if count else None,
            "microsoft_positive_height_summed_area_fraction": valid_area / total_area if total_area else None,
            "microsoft_positive_height_median_m": float(np.median(subset.height_m.to_numpy()[positive])) if valid_count else None,
            "microsoft_union_gross_m2": gross,
            "microsoft_union_land_m2": on_land,
            "microsoft_summed_gross_m2": summed,
            "microsoft_B1_coverage_land": on_land / support.area,
            "overture_B1_coverage_land": float(original.B1_coverage_land),
            "B1_difference_percentage_points": 100 * (on_land / support.area - original.B1_coverage_land),
            "microsoft_B1_coverage_gross": gross / z.geometry.area,
            "overture_B1_coverage_gross": float(original.B1_coverage_gross),
            "strict_cross_city_accepted": False,
        })
        print(z.unit_id, "pilot union complete", flush=True)
    return diagnostics, output, repairs


def main():
    manifest = json.loads((REVIEW / "organized_inventory.json").read_text())["tiles"]
    baseline = pd.read_csv(A / "results/SP_CHI/harmonization_2026_09_22_h1_h3/footprints/footprint_candidates.csv")
    diagnostics, rows, repairs = [], [], []
    for city in INPUTS:
        d, r, x = inspect_city(city, manifest, baseline)
        diagnostics.extend(d)
        rows.extend(r)
        repairs.extend(x)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "paired_microsoft_pilot.csv", index=False)
    (OUT / "tile_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (OUT / "working_geometry_repairs.json").write_text(json.dumps(repairs, indent=2) + "\n")


if __name__ == "__main__":
    main()
