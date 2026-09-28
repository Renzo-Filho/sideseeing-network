"""Six bounded OSM XML tiles at previously sampled U1 diagnostic points.

Run with: .venv/bin/python analysis/scripts/pilot_u1_osm_tiles.py
The official OSM map API is used only for six ~400 m tiles. Raw XML receipts
are retained under analysis/work, never mistaken for a pinned historical dump.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
import requests
import shapely
from shapely.geometry import box, Point

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/results/SP_CHI/u1_osm_tiles_2026_09_23'
RAW = ROOT / 'analysis/work/u1_osm_tiles_2026_09_23'
SAMPLE = ROOT / 'analysis/results/SP_CHI/u1_source_samples_2026_09_22/sampled_land_points.csv'
LAND = {
    'SP': ROOT / 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet',
    'CHI': ROOT / 'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/district_land.parquet',
}
CENTERS = {'SP:10': 9, 'SP:02': 2, 'SP:95': 1,
           'CHI:32': 5, 'CHI:14': 3, 'CHI:23': 10}
TILE_WIDTH_M = 400
TAGS = {'landuse': True, 'shop': True, 'amenity': True, 'office': True,
        'craft': True, 'tourism': True}
DEST_AMENITY = {
    'restaurant', 'cafe', 'fast_food', 'pub', 'bar', 'food_court', 'ice_cream',
    'bank', 'atm', 'post_office', 'school', 'college', 'university', 'kindergarten',
    'library', 'hospital', 'clinic', 'doctors', 'dentist', 'pharmacy',
    'theatre', 'cinema', 'arts_centre', 'community_centre', 'social_facility',
    'place_of_worship', 'police', 'fire_station', 'townhall', 'marketplace',
    'ferry_terminal', 'bus_station', 'music_venue', 'nightclub',
}
DEST_TOURISM = {'hotel', 'hostel', 'guest_house', 'museum', 'gallery', 'attraction',
                'zoo', 'aquarium', 'theme_park'}


def destination_mask(frame):
    """Provisional venue filter; street furniture and parking are excluded."""
    for key in ['shop', 'amenity', 'office', 'craft', 'tourism']:
        if key not in frame:
            frame[key] = None
    return (
        (frame.shop.notna() & ~frame.shop.isin(['vacant', 'no', 'yes']))
        | frame.amenity.isin(DEST_AMENITY)
        | (frame.office.notna() & ~frame.office.isin(['no', 'yes']))
        | (frame.craft.notna() & ~frame.craft.isin(['no', 'yes']))
        | frame.tourism.isin(DEST_TOURISM)
    )
USE_MAP = {
    'residential': 'residential', 'commercial': 'commerce_services',
    'retail': 'commerce_services', 'industrial': 'industrial',
    'education': 'institutional', 'institutional': 'institutional',
    'railway': 'transport_utilities', 'highway': 'transport_utilities',
    'garages': 'transport_utilities', 'depot': 'transport_utilities',
    'brownfield': 'vacant', 'construction': 'vacant', 'greenfield': 'vacant',
    'grass': 'open_other', 'forest': 'open_other', 'meadow': 'open_other',
    'recreation_ground': 'open_other', 'cemetery': 'open_other',
    'farmland': 'open_other', 'orchard': 'open_other', 'allotments': 'open_other',
}


def tile(lon: float, lat: float):
    dy = TILE_WIDTH_M / 2 / 111_320
    dx = dy / math.cos(math.radians(lat))
    return box(lon-dx, lat-dy, lon+dx, lat+dy)


def fetch(unit: str, polygon):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f'{unit.replace(":", "_")}.osm.xml'
    url = 'https://api.openstreetmap.org/api/0.6/map'
    params = {'bbox': ','.join(f'{v:.8f}' for v in polygon.bounds)}
    timestamp = datetime.now(timezone.utc).isoformat()
    if not path.exists():
        with requests.get(url, params=params, stream=True, timeout=90,
                          headers={'User-Agent': 'sideseeing-network academic U1 bounded pilot (contact via project repository)'}) as response:
            response.raise_for_status()
            size = 0
            with path.open('wb') as fh:
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 30_000_000:
                        path.unlink(missing_ok=True)
                        raise RuntimeError(f'{unit}: XML exceeded 30 MB cap')
                    fh.write(chunk)
        time.sleep(1)
    return path, {'url': requests.Request('GET', url, params=params).prepare().url,
                  'retrieved_or_checked_utc': timestamp, 'bytes': path.stat().st_size,
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    points = pd.read_csv(SAMPLE).set_index(['unit_id', 'sample_no'])
    lands = {city: gpd.read_parquet(path).set_index('district_id').to_crs(4326)
             for city, path in LAND.items()}
    results, tags, receipts = [], [], {}
    for unit, sample_no in CENTERS.items():
        city, district = unit.split(':')
        point = points.loc[(unit, sample_no)]
        polygon = tile(float(point.lon), float(point.lat))
        land = lands[city].loc[district, 'geometry']
        core = polygon.intersection(land)
        path, receipt = fetch(unit, polygon)
        receipts[unit] = receipt | {'center_sample_no': sample_no,
                                    'center_source_status': point.land_source_status,
                                    'tile_bounds': polygon.bounds}
        feats = ox.features_from_xml(path, polygon=core, tags=TAGS).reset_index()
        projected = feats.to_crs(6933)
        core_m = gpd.GeoSeries([core], crs=4326).to_crs(6933).iloc[0]
        center_geom = Point(float(point.lon), float(point.lat))
        center_tags = sorted(set(feats.loc[feats.landuse.notna() & feats.geometry.map(lambda g: g.covers(center_geom)), 'landuse'].astype(str)))
        landuse = projected[projected.landuse.notna() & projected.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()
        landuse['clipped'] = landuse.geometry.map(lambda geom: geom.intersection(core_m))
        grouped = {}
        for label, group in landuse.groupby('landuse'):
            geometries = [g for g in group.clipped if not g.is_empty]
            grouped[label] = shapely.union_all(geometries) if geometries else shapely.GeometryCollection()
            tags.append({'unit_id': unit, 'landuse_tag': label, 'polygon_count': len(group),
                         'union_area_m2': grouped[label].area,
                         'crosswalk': USE_MAP.get(label, 'unmapped_tag')})
        union = shapely.union_all([g for g in grouped.values() if not g.is_empty]) if grouped else shapely.GeometryCollection()
        mapped_area = union.area
        # OSM features can carry several destination tags. Count objects once,
        # while reporting keys separately; no category entropy is implied.
        poi_keys = ['shop', 'amenity', 'office', 'craft', 'tourism']
        for key in poi_keys:
            if key not in projected:
                projected[key] = None
        poi = projected[projected[poi_keys].notna().any(axis=1)].copy()
        poi['point'] = poi.geometry.map(lambda geom: geom if geom.geom_type == 'Point' else geom.representative_point())
        poi = poi.loc[poi['point'].map(core_m.covers).astype(bool)]
        counts = {f'{key}_objects': int(poi[key].notna().sum()) for key in poi_keys}
        candidate = poi.loc[destination_mask(poi)]
        results.append({'unit_id': unit, 'center_sample_no': sample_no,
                        'center_source_status': point.land_source_status,
                        'center_osm_landuse_tags': '|'.join(center_tags),
                        'tile_land_m2': core_m.area, 'osm_features': len(feats),
                        'landuse_polygons': len(landuse),
                        'landuse_tagged_area_m2': mapped_area,
                        'landuse_tagged_fraction': mapped_area / core_m.area,
                        'landuse_uncovered_fraction': 1 - mapped_area / core_m.area,
                        'landuse_tags': len(grouped), 'poi_objects': len(poi),
                        'poi_named_objects': int(poi['name'].notna().sum()) if 'name' in poi else 0,
                        'poi_destination_candidates': len(candidate),
                        **counts})
        print(unit, 'xml_bytes', path.stat().st_size, 'mapped_share', round(mapped_area/core_m.area, 3), 'POIs', len(poi), flush=True)
    pd.DataFrame(results).to_csv(OUT/'tile_summary.csv', index=False)
    pd.DataFrame(tags).to_csv(OUT/'landuse_tags.csv', index=False)
    (OUT/'receipts.json').write_text(json.dumps({'scope': 'six 400 m tiles, one saved diagnostic point per unit',
        'osm_api': 'live current map API, not fixed historical snapshot', 'tag_filter': TAGS,
        'use_crosswalk': USE_MAP, 'tiles': receipts}, indent=2) + '\n')


if __name__ == '__main__':
    main()
