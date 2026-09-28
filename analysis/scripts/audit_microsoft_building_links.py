"""Locate Microsoft global building tiles for the paired city supports.

This reads only the link index. It makes no claim about feature completeness or
height coverage within a tile and downloads no building data.
"""

import argparse
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import geopandas as gpd
import pyarrow.parquet as pq
from shapely.geometry import box
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[2]
PREPARED = ROOT / "analysis/work/prepared"
BOUNDARIES = {
    "CHI": PREPARED / "Chicago/chi_local_2026_09_16_v1/districts.parquet",
    "SP": PREPARED / "SP/sp_prep_2026_09_10_v3/N02/districts.parquet",
}
REGIONS = {"CHI": "UnitedStates", "SP": "Brazil"}
SIZE_FACTORS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}


def quadkey_bounds(key):
    if len(key) != 9 or any(ch not in "0123" for ch in key):
        raise ValueError(f"Invalid level-9 quadkey: {key}")
    x = y = 0
    for digit in key:
        x = (x << 1) | (int(digit) & 1)
        y = (y << 1) | (int(digit) >> 1)
    n = 1 << len(key)

    def latitude(ty):
        return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))

    return box(x / n * 360 - 180, latitude(y + 1), (x + 1) / n * 360 - 180, latitude(y))


def bytes_from_size(value):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(B|KB|MB|GB)", value)
    if not match:
        raise ValueError(f"Invalid size: {value}")
    return round(float(match.group(1)) * SIZE_FACTORS[match.group(2)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--links", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.links.open("rb") as source:
        source_hash = hashlib.file_digest(source, "sha256").hexdigest()
    with args.links.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ["Location", "QuadKey", "Url", "Size", "UploadDate"]:
            raise ValueError(f"Unexpected index schema: {reader.fieldnames}")
        rows = list(reader)
    if len({row["Url"] for row in rows}) != len(rows):
        raise ValueError("Duplicate tile URLs")
    dates = sorted({row["UploadDate"] for row in rows})
    cities = {}
    selected = []
    for city, path in BOUNDARIES.items():
        districts = gpd.read_parquet(path, columns=["geometry"])
        if len(districts) != (77 if city == "CHI" else 96):
            raise ValueError(f"Unexpected reporting-unit count for {city}")
        support = districts.geometry.union_all()
        buffered = gpd.GeoSeries([support.buffer(1500)], crs=districts.crs).to_crs(4326).iloc[0]
        city_shape = gpd.GeoSeries([support], crs=districts.crs).to_crs(4326).iloc[0]
        regional = [row for row in rows if row["Location"] == REGIONS[city]]
        for row in regional:
            tile = quadkey_bounds(row["QuadKey"])
            if not tile.intersects(buffered):
                continue
            url = urlparse(row["Url"])
            if url.scheme != "https" or not url.netloc.endswith(".web.core.windows.net"):
                raise ValueError(f"Unexpected tile host: {row['Url']}")
            selected.append({
                "city": city,
                "location": row["Location"],
                "quadkey": row["QuadKey"],
                "url": row["Url"],
                "advertised_size_bytes_approx": bytes_from_size(row["Size"]),
                "intersects_city": tile.intersects(city_shape),
                "intersects_1500m_buffer": True,
            })
        city_rows = [row for row in selected if row["city"] == city]
        tiles_union = unary_union([quadkey_bounds(row["quadkey"]) for row in city_rows])
        uncovered = city_shape.difference(tiles_union)
        uncovered_metric = gpd.GeoSeries([uncovered], crs=4326).to_crs(districts.crs).iloc[0].area
        cities[city] = {
            "boundary_path": str(path.relative_to(ROOT)),
            "reporting_units": len(districts),
            "region_label": REGIONS[city],
            "regional_index_rows": len(regional),
            "selected_tiles": len(city_rows),
            "tiles_intersecting_city": sum(row["intersects_city"] for row in city_rows),
            "advertised_size_bytes_approx": sum(row["advertised_size_bytes_approx"] for row in city_rows),
            "unindexed_city_support_m2": round(uncovered_metric, 3),
        }
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "selected_tiles.csv").open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    audit = {
        "source_path": str(args.links),
        "source_sha256": source_hash,
        "index_rows": len(rows),
        "regions": len(set(row["Location"] for row in rows)),
        "quadkey_lengths": dict(Counter(len(row["QuadKey"]) for row in rows)),
        "upload_dates": dates,
        "cities": cities,
        "limitations": "Link-index intersection only; no building tiles fetched or feature-level coverage/height/accuracy verified.",
    }
    overture = ROOT / "analysis/data/Chicago/overture_2026_08_19/building/part_0000.parquet"
    if overture.exists():
        counts = Counter()
        for batch in pq.ParquetFile(overture).iter_batches(columns=["sources", "height", "num_floors"], batch_size=50000):
            sources = batch.column(0).to_pylist()
            heights = batch.column(1).to_pylist()
            floors = batch.column(2).to_pylist()
            for source_list, height, floor in zip(sources, heights, floors):
                counts["building_rows"] += 1
                if height is not None and height > 0:
                    counts["rows_with_positive_height"] += 1
                if floor is not None and floor > 0:
                    counts["rows_with_positive_num_floors"] += 1
                datasets = {item.get("dataset") for item in source_list or []}
                if "Microsoft ML Buildings" in datasets:
                    counts["rows_citing_microsoft_ml_buildings"] += 1
        audit["chicago_overture_provenance"] = {
            "path": str(overture.relative_to(ROOT)),
            **dict(counts),
            "interpretation": "Source overlap, not polygon identity or evidence that the Microsoft 2026-08-13 release adds no buildings.",
        }
    sp_overture = ROOT / "analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg"
    if sp_overture.exists():
        with sqlite3.connect(sp_overture) as connection:
            total, microsoft, heights, floors = connection.execute(
                "SELECT COUNT(*), "
                "SUM(CASE WHEN sources_json LIKE '%Microsoft ML Buildings%' THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN height_m > 0 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN floor_count > 0 THEN 1 ELSE 0 END) FROM buildings"
            ).fetchone()
        audit["sp_overture_provenance"] = {
            "path": str(sp_overture.relative_to(ROOT)),
            "building_rows": total,
            "rows_citing_microsoft_ml_buildings": microsoft,
            "rows_with_positive_height": heights,
            "rows_with_positive_floor_count": floors,
            "interpretation": "Legacy Overture source-lineage overlap; not proof of feature equivalence to the Microsoft 2026-08-13 tiles.",
        }
    (args.output / "links_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
