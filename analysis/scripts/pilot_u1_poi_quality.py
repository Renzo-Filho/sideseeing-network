"""Bounded Overture Places quality/provenance check for Brás and Loop only."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from pilot_u1_poi_samples import DESTINATION_CATEGORIES, LAND, PARTITIONS, RELEASE, source_url

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_developed_area_2026_09_22'
ANCHORS = {'SP': '10', 'CHI': '32'}


def provider_key(sources: object) -> str:
    if not isinstance(sources, (list, np.ndarray)):
        return 'unknown'
    providers = sorted({str(item.get('provider') or item.get('dataset') or 'unknown')
        for item in sources if isinstance(item, dict) and item.get('property') in ('', None)
        and str(item.get('provider') or '').lower() != 'overture'})
    return '|'.join(providers) if providers else 'unknown'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute('LOAD httpfs')
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    rows, summaries, receipts = [], [], {}
    for city, district in ANCHORS.items():
        land = gpd.read_parquet(LAND[city]).set_index('district_id').loc[district, 'geometry']
        land = gpd.GeoSeries([land], crs=31983 if city == 'SP' else 26916).to_crs(4326).iloc[0]
        west, south, east, north = land.bounds
        url = source_url(PARTITIONS[city])
        query = '''SELECT id,geometry,taxonomy.hierarchy AS hierarchy,
            confidence,sources FROM read_parquet(?)
            WHERE bbox.xmin BETWEEN ? AND ? AND bbox.ymin BETWEEN ? AND ?'''
        records = con.execute(query, [url, west, east, south, north]).fetchdf()
        points = shapely.from_wkb(records.geometry.map(bytes).to_numpy())
        inside = shapely.intersects(points, land)
        local = records.loc[inside].copy().reset_index(drop=True)
        assert len(local) > 1000
        local['top_category'] = local.hierarchy.map(lambda x: x[0] if isinstance(x, np.ndarray) and len(x)>0 else None)
        local['category_known'] = local.top_category.notna()
        local['provider_key'] = local.sources.map(provider_key)
        local['low_confidence'] = local.confidence.lt(0.5)
        for (provider, known), part in local.groupby(['provider_key', 'category_known'], dropna=False):
            eligible = part.top_category.isin(DESTINATION_CATEGORIES)
            counts = part.loc[eligible, 'top_category'].value_counts()
            shares = counts / counts.sum() if len(counts) else counts
            entropy = float(-(shares * np.log(shares)).sum() / np.log(12)) if len(shares) else None
            rows.append({'city': city, 'unit_id': f'{city}:{district}',
                'provider_key': provider, 'category_known': bool(known),
                'records': len(part), 'classified_destination_records': int(eligible.sum()),
                'entropy_12': entropy, 'median_confidence': float(part.confidence.median()),
                'confidence_below_050': int(part.low_confidence.sum())})
        for known, part in local.groupby('category_known'):
            summaries.append({'city': city, 'unit_id': f'{city}:{district}',
                'category_known': bool(known), 'records': len(part),
                'median_confidence': float(part.confidence.median()),
                'confidence_below_050': int(part.low_confidence.sum()),
                'confidence_ge_075': int(part.confidence.ge(0.75).sum())})
        receipts[city] = {'partition': PARTITIONS[city], 'bbox_rows': len(records),
            'exact_unit_records': len(local), 'bbox': [west,south,east,north], 'source_url': url}
        print(city, 'bbox', len(records), 'exact', len(local), flush=True)
    con.close()
    pd.DataFrame(rows).to_csv(OUT/'poi_provider_profile.csv', index=False)
    pd.DataFrame(summaries).to_csv(OUT/'poi_quality_summary.csv', index=False)
    (OUT/'poi_quality_checks.json').write_text(json.dumps({'release': RELEASE,
        'scope': 'Brás and Loop only, one geographic partition/bbox each; one thread',
        'receipts': receipts, 'independent_truth_labels': False,
        'confidence_calibrated_across_providers': False}, indent=2)+'\n')


if __name__ == '__main__':
    main()
