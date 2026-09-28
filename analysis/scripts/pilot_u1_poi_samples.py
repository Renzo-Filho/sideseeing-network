"""Bounded Overture Places screen for six previously selected U1 districts.

Only two release partitions and geographic row groups are read remotely. The
query returns fields for the combined bounding boxes of three units per city;
exact district membership is checked locally. No citywide POI extraction.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_source_samples_2026_09_22'
RELEASE = '2026-08-19.0'
SEED = 20260922
DESTINATION_CATEGORIES = (
    'arts_and_entertainment', 'community_and_government', 'cultural_and_historic',
    'education', 'food_and_drink', 'health_care', 'lifestyle_services', 'lodging',
    'services_and_business', 'shopping', 'sports_and_recreation',
    'travel_and_transportation',
)
UNITS = {'SP': ['10', '02', '95'], 'CHI': ['32', '14', '23']}
PARTITIONS = {'SP': 4, 'CHI': 3}
LAND = {
    'SP': ROOT / 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet',
    'CHI': ROOT / 'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/district_land.parquet',
}


def source_url(partition: int) -> str:
    item = f'https://stac.overturemaps.org/{RELEASE}/places/place/{partition:05d}/{partition:05d}.json'
    with urllib.request.urlopen(item, timeout=20) as response:
        return json.load(response)['assets']['aws']['href']


def fetch_bbox(con: duckdb.DuckDBPyConnection, url: str, bounds: np.ndarray) -> pd.DataFrame:
    west, south, east, north = map(float, bounds)
    query = '''SELECT id, geometry, bbox, basic_category,
        taxonomy.primary AS taxonomy_primary,
        taxonomy.hierarchy AS hierarchy,
        names.primary AS name, confidence, operating_status
        FROM read_parquet(?) WHERE bbox.xmin BETWEEN ? AND ?
        AND bbox.ymin BETWEEN ? AND ?'''
    return con.execute(query, [url, west, east, south, north]).fetchdf()


def norm_name(name: object) -> str:
    if not isinstance(name, str):
        return ''
    return re.sub(r'[^a-z0-9]+', '', name.casefold())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    con = duckdb.connect()
    con.execute('LOAD httpfs')
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    summaries, samples, category_counts, receipts = [], [], [], {}
    for city, ids in UNITS.items():
        land = gpd.read_parquet(LAND[city])
        land = land.loc[land.district_id.isin(ids), ['district_id', 'geometry']].to_crs(4326)
        assert len(land) == 3
        url = source_url(PARTITIONS[city])
        bbox = land.total_bounds
        records = fetch_bbox(con, url, bbox)
        # Overture Places are points; geometry is the precise location, while
        # GeoParquet bbox is used only for inexpensive remote row-group pruning.
        points = shapely.from_wkb(records.geometry.map(bytes).to_numpy())
        assert bool(np.all(shapely.get_type_id(points) == 0))
        receipts[city] = {'stac_partition': PARTITIONS[city], 'source_url': url,
                          'combined_bbox': bbox.tolist(), 'bbox_rows': len(records)}
        print(city, 'bbox_rows', len(records), flush=True)
        for district in ids:
            geom = land.set_index('district_id').loc[district, 'geometry']
            local = records.loc[shapely.intersects(points, geom)].copy().reset_index(drop=True)
            local_points = points[shapely.intersects(points, geom)]
            local['top_category'] = local.hierarchy.map(
                lambda h: h[0] if isinstance(h, np.ndarray) and len(h) else None)
            local['name_key'] = local.name.map(norm_name)
            local['x_round'] = np.round(shapely.get_x(local_points), 4)
            local['y_round'] = np.round(shapely.get_y(local_points), 4)
            candidate_duplicates = local.duplicated(
                ['name_key', 'x_round', 'y_round'], keep=False) & local.name_key.ne('')
            counts = local.top_category.value_counts(dropna=False)
            valid = local.top_category.isin(DESTINATION_CATEGORIES)
            summary = {'city': city, 'unit_id': f'{city}:{district}',
                'bbox_rows_city_batch': len(records), 'poi_records_in_unit': len(local),
                'with_destination_category': int(valid.sum()),
                'without_destination_category': int((~valid).sum()),
                'geographic_entities': int(local.top_category.eq('geographic_entities').sum()),
                'candidate_duplicate_records': int(candidate_duplicates.sum()),
                'confidence_median': float(local.confidence.median()) if len(local) else None}
            for threshold, label in [(0.0, 'all'), (0.5, 'ge_050'), (0.75, 'ge_075')]:
                scoped = local.loc[local.confidence.ge(threshold)]
                selected = scoped.top_category.isin(DESTINATION_CATEGORIES)
                n = int(selected.sum())
                summary[f'{label}_records'] = len(scoped)
                summary[f'{label}_classified_destination_records'] = n
                if n:
                    dist = scoped.loc[selected, 'top_category'].value_counts() / n
                    summary[f'{label}_entropy_12'] = float(-(dist * np.log(dist)).sum() / np.log(12))
                else:
                    summary[f'{label}_entropy_12'] = None
            summaries.append(summary)
            for cat, count in counts.items():
                category_counts.append({'city': city, 'unit_id': f'{city}:{district}',
                    'top_category': cat if pd.notna(cat) else 'unclassified', 'record_count': int(count)})
            if len(local):
                chosen = rng.choice(len(local), size=min(20, len(local)), replace=False)
                for n, index in enumerate(chosen, 1):
                    record = local.iloc[index]
                    point = local_points[index]
                    samples.append({'city': city, 'unit_id': f'{city}:{district}',
                        'sample_no': n, 'id': record.id, 'lon': float(point.x),
                        'lat': float(point.y), 'name': record['name'],
                        'basic_category': record.basic_category,
                        'taxonomy_primary': record.taxonomy_primary,
                        'top_category': record.top_category,
                        'confidence': record.confidence,
                        'candidate_duplicate': bool(candidate_duplicates.iloc[index])})
            print(city, district, 'unit_pois', len(local), 'top_known', int(local.top_category.notna().sum()), flush=True)
    con.close()
    pd.DataFrame(summaries).to_csv(OUT/'poi_summary.csv', index=False)
    pd.DataFrame(samples).to_csv(OUT/'sampled_pois.csv', index=False)
    pd.DataFrame(category_counts).to_csv(OUT/'poi_category_counts.csv', index=False)
    checks = {'release': RELEASE, 'seed': SEED, 'units': UNITS,
        'remote_scope': 'two geographic Places partitions, one combined bbox per city; one DuckDB thread',
        'max_sampled_pois_per_unit': 20, 'fixed_destination_categories': DESTINATION_CATEGORIES, 'city_receipts': receipts,
        'independent_truth_labels': False, 'semantic_accepted': False}
    (OUT/'poi_checks.json').write_text(json.dumps(checks, indent=2)+'\n')


if __name__ == '__main__':
    main()
