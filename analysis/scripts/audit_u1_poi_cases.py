"""Preselect seven named POI cases from the six-tile OSM/Overture comparison.

The SHA-256 ordering is fixed before external reference searches. No claim of
source completeness or random district representativeness follows.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
import shapely
from osmnx._errors import InsufficientResponseError
from shapely.geometry import box

from pilot_u1_osm_tiles import destination_mask
from pilot_u1_poi_samples import LAND, PARTITIONS, norm_name, source_url

ROOT = Path(__file__).resolve().parents[2]
TILES = ROOT / 'analysis/results/SP_CHI/u1_osm_tiles_2026_09_23'
RAW = ROOT / 'analysis/work/u1_osm_tiles_2026_09_23'
OUT = ROOT / 'analysis/results/SP_CHI/u1_independent_cases_2026_09_23'
SEED = '20260923-u1-case-audit-v1'
REQUESTED = {'SP:10': ['matched', 'osm_only'],
             'SP:02': ['overture_only'], 'SP:95': ['overture_only'],
             'CHI:32': ['matched', 'osm_only', 'overture_only']}
TAGS = {'shop': True, 'amenity': True, 'office': True, 'craft': True, 'tourism': True}


def rank(row):
    key = f'{SEED}:{row["unit_id"]}:{row["case_type"]}:{row["source_id"]}'
    return hashlib.sha256(key.encode()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipts = json.loads((TILES/'receipts.json').read_text())['tiles']
    land = {city: gpd.read_parquet(path).set_index('district_id').to_crs(4326)
            for city, path in LAND.items()}
    con = duckdb.connect()
    con.execute('LOAD httpfs')
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    urls = {city: source_url(partition) for city, partition in PARTITIONS.items()}
    selected, counts = [], []
    for unit, kinds in REQUESTED.items():
        city, district = unit.split(':')
        core = box(*receipts[unit]['tile_bounds']).intersection(land[city].loc[district, 'geometry'])
        path = RAW / f'{unit.replace(":", "_")}.osm.xml'
        try:
            osm = ox.features_from_xml(path, polygon=core, tags=TAGS).reset_index()
        except InsufficientResponseError:
            osm = gpd.GeoDataFrame({'element': [], 'id': [], 'name': []},
                                   geometry=gpd.GeoSeries([], crs=4326), crs=4326)
        for key in TAGS:
            if key not in osm:
                osm[key] = None
        osm = osm.loc[destination_mask(osm)].copy()
        osm['geometry'] = osm.geometry.map(lambda g: g if g.geom_type == 'Point' else g.representative_point())
        osm = osm.loc[osm.geometry.map(core.covers).astype(bool)].copy().reset_index(drop=True)
        if 'name' not in osm:
            osm['name'] = None
        osm['name_key'] = osm['name'].map(norm_name)
        metric_crs = 32723 if city == 'SP' else 26916
        osm_m = gpd.GeoDataFrame(osm, geometry='geometry', crs=4326).to_crs(metric_crs)
        west, south, east, north = receipts[unit]['tile_bounds']
        sql = '''SELECT id, geometry, names.primary AS name, confidence,
                 taxonomy.hierarchy AS hierarchy, taxonomy.primary AS taxonomy_primary
                 FROM read_parquet(?) WHERE bbox.xmin BETWEEN ? AND ?
                 AND bbox.ymin BETWEEN ? AND ?'''
        ov = con.execute(sql, [urls[city], west, east, south, north]).fetchdf()
        pts = shapely.from_wkb(ov.geometry.map(bytes).to_numpy())
        inside = shapely.intersects(pts, core)
        ov = gpd.GeoDataFrame(ov.loc[inside].drop(columns='geometry').reset_index(drop=True),
                              geometry=pts[inside], crs=4326)
        ov['name_key'] = ov['name'].map(norm_name)
        ov['top_category'] = ov.hierarchy.map(lambda h: h[0] if isinstance(h, np.ndarray) and len(h) else None)
        ov_m = ov.to_crs(metric_crs)
        by_name = {key: part for key, part in ov_m.loc[ov_m.name_key.ne('')].groupby('name_key')}
        osm_pairs, ov_pairs = {}, set()
        for i, item in osm_m.loc[osm_m.name_key.ne('')].iterrows():
            candidates = by_name.get(item.name_key)
            if candidates is None:
                continue
            distances = candidates.geometry.distance(item.geometry)
            if not distances.empty and distances.min() <= 30:
                j = int(distances.idxmin())
                osm_pairs[i] = j
                ov_pairs.add(j)
        pools = {'matched': [], 'osm_only': [], 'overture_only': []}
        for i, row in osm.iterrows():
            if not row.name_key:
                continue
            geom = row.geometry
            base = {'unit_id': unit, 'name': row['name'], 'source_id': f'{row.element}/{row.id}',
                    'lon': geom.x, 'lat': geom.y, 'osm_tag': next((f'{k}={row[k]}' for k in TAGS if pd.notna(row[k])), ''),
                    'overture_category': None, 'overture_primary': None, 'overture_confidence': None}
            if i in osm_pairs:
                match = ov.iloc[osm_pairs[i]]
                pools['matched'].append(base | {'case_type': 'matched', 'other_id': match.id,
                    'overture_category': match.top_category, 'overture_primary': match.taxonomy_primary, 'overture_confidence': match.confidence})
            else:
                pools['osm_only'].append(base | {'case_type': 'osm_only', 'other_id': None})
        for j, row in ov.iterrows():
            if not row.name_key or j in ov_pairs:
                continue
            pools['overture_only'].append({'unit_id': unit, 'name': row['name'],
                'source_id': row.id, 'lon': row.geometry.x, 'lat': row.geometry.y,
                'osm_tag': None, 'overture_category': row.top_category, 'overture_primary': row.taxonomy_primary,
                'overture_confidence': row.confidence, 'case_type': 'overture_only', 'other_id': None})
        for kind in kinds:
            pool = pools[kind]
            counts.append({'unit_id': unit, 'case_type': kind, 'eligible_named_records': len(pool)})
            if pool:
                chosen = min(pool, key=rank)
                selected.append(chosen | {'selection_hash': rank(chosen),
                                          'case_id': f'{unit.replace(":", "_")}_{kind}'})
        print(unit, {kind: len(pools[kind]) for kind in kinds}, flush=True)
    pd.DataFrame(selected).to_csv(OUT/'selected_poi_cases.csv', index=False)
    pd.DataFrame(counts).to_csv(OUT/'poi_case_frames.csv', index=False)
    (OUT/'poi_selection_receipt.json').write_text(json.dumps({
        'seed': SEED, 'units_and_strata': REQUESTED,
        'eligibility': 'named OSM venue candidates and named Overture records within same clipped tile; exact normalized name and <=30m marks matched',
        'selection': 'minimum SHA-256 of seed:unit:case_type:source_id in each requested stratum',
        'overture_release': '2026-08-19.0', 'remote_partitions': PARTITIONS}, indent=2)+'\n')
    con.close()


if __name__ == '__main__':
    main()
