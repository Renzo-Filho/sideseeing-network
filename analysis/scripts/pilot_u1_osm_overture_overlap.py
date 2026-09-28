"""Compare bounded OSM tile destinations with pinned Overture Places points.

Requires pilot_u1_osm_tiles.py output and network for six small Parquet bbox reads.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import osmnx as ox
from osmnx._errors import InsufficientResponseError
import pandas as pd
import shapely
from shapely.geometry import box

from pilot_u1_poi_samples import DESTINATION_CATEGORIES, LAND, PARTITIONS, norm_name, source_url
from pilot_u1_osm_tiles import destination_mask

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_osm_tiles_2026_09_23'
RAW = ROOT / 'analysis/work/u1_osm_tiles_2026_09_23'
TAGS = {'shop': True, 'amenity': True, 'office': True, 'craft': True, 'tourism': True}


def main():
    receipts = json.loads((OUT/'receipts.json').read_text())['tiles']
    land = {city: gpd.read_parquet(path).set_index('district_id').to_crs(4326)
            for city, path in LAND.items()}
    con = duckdb.connect()
    con.execute('LOAD httpfs')
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    urls = {city: source_url(partition) for city, partition in PARTITIONS.items()}
    rows, examples = [], []
    for unit, receipt in receipts.items():
        city, district = unit.split(':')
        core = box(*receipt['tile_bounds']).intersection(land[city].loc[district, 'geometry'])
        xml = RAW / f'{unit.replace(":", "_")}.osm.xml'
        try:
            osm = ox.features_from_xml(xml, polygon=core, tags=TAGS).reset_index()
        except InsufficientResponseError:
            osm = gpd.GeoDataFrame({'element': [], 'id': [], 'name': []},
                                   geometry=gpd.GeoSeries([], crs=4326), crs=4326)
        keys = list(TAGS)
        for key in keys:
            if key not in osm:
                osm[key] = None
        osm = osm.loc[osm[keys].notna().any(axis=1)].copy()
        osm['geometry'] = osm.geometry.map(lambda g: g if g.geom_type == 'Point' else g.representative_point())
        osm = osm.loc[osm.geometry.map(core.covers).astype(bool)]
        raw_osm_objects = len(osm)
        osm = osm.loc[destination_mask(osm)].copy()
        if 'name' not in osm:
            osm['name'] = None
        osm['name_key'] = osm['name'].map(norm_name)
        west, south, east, north = receipt['tile_bounds']
        sql = '''SELECT id, geometry, names.primary AS name, confidence,
                 taxonomy.hierarchy AS hierarchy
                 FROM read_parquet(?) WHERE bbox.xmin BETWEEN ? AND ?
                 AND bbox.ymin BETWEEN ? AND ?'''
        ov = con.execute(sql, [urls[city], west, east, south, north]).fetchdf()
        pts = shapely.from_wkb(ov.geometry.map(bytes).to_numpy())
        ov = ov.loc[shapely.intersects(pts, core)].copy()
        ov = gpd.GeoDataFrame(ov.drop(columns='geometry'), geometry=pts[shapely.intersects(pts, core)], crs=4326)
        ov['name_key'] = ov['name'].map(norm_name)
        ov['top_category'] = ov.hierarchy.map(lambda h: h[0] if isinstance(h, np.ndarray) and len(h) else None)
        metric_crs = 32723 if city == 'SP' else 26916
        osm_m = gpd.GeoDataFrame(osm, geometry='geometry', crs=4326).to_crs(metric_crs)
        ov_m = ov.to_crs(metric_crs)
        ov_by_name = {key: part for key, part in ov_m.loc[ov_m.name_key.ne('')].groupby('name_key')}
        osm_matches = 0
        matched_ov_ids = set()
        for item in osm_m.loc[osm_m.name_key.ne('')].itertuples():
            candidates = ov_by_name.get(item.name_key)
            if candidates is None:
                continue
            distances = candidates.geometry.distance(item.geometry)
            if distances.empty or distances.min() > 30:
                continue
            best = candidates.loc[distances.idxmin()]
            osm_matches += 1
            matched_ov_ids.add(best.id)
            if len([x for x in examples if x['unit_id'] == unit]) < 10:
                examples.append({'unit_id': unit, 'osm_name': item.name,
                                 'overture_name': best['name'], 'distance_m': float(distances.min()),
                                 'osm_type': item.element, 'osm_id': item.id, 'overture_id': best.id})
        rows.append({'unit_id': unit, 'osm_tagged_objects': raw_osm_objects,
                     'osm_pois': len(osm), 'osm_named': int(osm.name_key.ne('').sum()),
                     'overture_pois': len(ov), 'overture_named': int(ov.name_key.ne('').sum()),
                     'overture_destinations_12': int(ov.top_category.isin(DESTINATION_CATEGORIES).sum()),
                     'overture_unclassified_12': int((~ov.top_category.isin(DESTINATION_CATEGORIES)).sum()),
                     'osm_named_with_exact_name_30m': osm_matches,
                     'overture_named_with_exact_name_30m': len(matched_ov_ids)})
        print(unit, 'OSM', len(osm), 'Overture', len(ov), 'exact_name_30m', osm_matches, flush=True)
    pd.DataFrame(rows).to_csv(OUT/'osm_overture_overlap.csv', index=False)
    pd.DataFrame(examples).to_csv(OUT/'name_match_examples.csv', index=False)
    (OUT/'overture_receipt.json').write_text(json.dumps({'release': '2026-08-19.0',
        'partitions': PARTITIONS, 'remote_urls': urls, 'match_rule': 'normalized exact name and <=30 m; diagnostic only',
        'source_scope': 'six bounded tile bbox queries, exact district/tile point filter'}, indent=2)+'\n')
    con.close()


if __name__ == '__main__':
    main()
