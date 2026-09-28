"""Inspect nearby pinned Overture records for selected OSM-only POIs.

This tests whether the exact-name/30 m unmatched label is a genuine absence
or a name/point-placement artifact. Reads only the two already selected tiles.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Point, box

from pilot_u1_poi_samples import LAND, PARTITIONS, source_url

ROOT = Path(__file__).resolve().parents[2]
TILES = ROOT / 'analysis/results/SP_CHI/u1_osm_tiles_2026_09_23'
OUT = ROOT / 'analysis/results/SP_CHI/u1_independent_cases_2026_09_23'


def main():
    selected = pd.read_csv(OUT/'selected_poi_cases.csv').query('case_type == "osm_only"')
    receipts = json.loads((TILES/'receipts.json').read_text())['tiles']
    con = duckdb.connect()
    con.execute('LOAD httpfs')
    con.execute('SET threads=1')
    con.execute("SET memory_limit='512MB'")
    urls = {city: source_url(partition) for city, partition in PARTITIONS.items()}
    lands = {city: gpd.read_parquet(path).set_index('district_id').to_crs(4326)
             for city, path in LAND.items()}
    rows = []
    for case in selected.itertuples():
        city = case.unit_id.split(':')[0]
        west, south, east, north = receipts[case.unit_id]['tile_bounds']
        sql = '''SELECT id, geometry, names.primary AS name, confidence,
                 taxonomy.hierarchy AS hierarchy FROM read_parquet(?)
                 WHERE bbox.xmin BETWEEN ? AND ? AND bbox.ymin BETWEEN ? AND ?'''
        df = con.execute(sql, [urls[city], west, east, south, north]).fetchdf()
        pts = shapely.from_wkb(df.geometry.map(bytes).to_numpy())
        core = box(west, south, east, north).intersection(lands[city].loc[case.unit_id.split(':')[1], 'geometry'])
        inside = shapely.intersects(pts, core)
        geo = gpd.GeoDataFrame(df.loc[inside].drop(columns='geometry').reset_index(drop=True),
            geometry=pts[inside], crs=4326)
        crs = 32723 if city == 'SP' else 26916
        point = gpd.GeoSeries([Point(case.lon, case.lat)], crs=4326).to_crs(crs).iloc[0]
        metric = geo.to_crs(crs)
        metric['distance_m'] = metric.geometry.distance(point)
        near = metric.nsmallest(8, 'distance_m')
        for item in near.itertuples():
            rows.append({'case_id': case.case_id, 'osm_name': case.name, 'overture_id': item.id,
                         'overture_name': item.name, 'distance_m': item.distance_m,
                         'overture_confidence': item.confidence})
        print(case.case_id, 'nearest', near[['name','distance_m']].head(3).to_dict('records'), flush=True)
    pd.DataFrame(rows).to_csv(OUT/'poi_nearest_overture.csv', index=False)
    con.close()


if __name__ == '__main__':
    main()
