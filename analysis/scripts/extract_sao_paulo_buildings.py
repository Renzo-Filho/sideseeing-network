"""Cloud-native Overture building morphology extraction for metropolitan São Paulo.

Run prepare_overture_sp.py once, then run this file with the project Python.
Dependencies: duckdb, pyarrow, geopandas, pyogrio, shapely, pandas, requests.
Remote Parquet is filtered by STAC file extents and Parquet bbox statistics.
Only selected columns/rows are staged locally; GeoPandas processes bounded batches.
The completed GeoPackage is published by atomic rename after validation.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import sqlite3
import time

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyogrio
import requests
import shapely
from shapely.geometry import MultiPolygon, box

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'analysis/cache/overture_sp'
OUT = ROOT / 'analysis/data/SP/Edificacoes'
FINAL = OUT / 'sao_paulo_building_morphology.gpkg'
METRIC_CRS = 'EPSG:31983'


def log(message):
    print(f'{datetime.now(timezone.utc).isoformat(timespec="seconds")} {message}', flush=True)


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def load_json(path):
    return json.loads(path.read_text())


def get_item(url):
    name = url.rsplit('/', 1)[1]
    path = CACHE / 'items' / name
    if path.exists():
        return load_json(path)
    for attempt in range(4):
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            result = response.json()
            path.write_text(json.dumps(result))
            return result
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def scope():
    membership = load_json(CACHE / 'rmsp_membership.json')[0]
    codes = {str(m['id']): m['nome'] for m in membership['municipios']}
    municipalities = gpd.read_file(CACHE / 'sp_municipalities.geojson')
    municipalities = municipalities.loc[municipalities.codarea.isin(codes)].to_crs(4326)
    if len(municipalities) != 39 or not municipalities.is_valid.all():
        raise ValueError('Expected 39 valid RMSP municipality polygons from IBGE.')
    bounds = municipalities.total_bounds
    # Outward rounding avoids truncating the official boundary extent.
    bbox = [math.floor(bounds[0]*100)/100, math.floor(bounds[1]*100)/100,
            math.ceil(bounds[2]*100)/100, math.ceil(bounds[3]*100)/100]
    municipalities['municipality_name'] = municipalities.codarea.map(codes)
    return bbox, municipalities


def intersects_bbox(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def select_assets(bbox):
    collection = load_json(CACHE / 'building_collection.json')
    links = [x['href'] for x in collection['links'] if x['rel'] == 'item']
    (CACHE / 'items').mkdir(exist_ok=True)
    items = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(get_item, url) for url in links]
        for i, future in enumerate(as_completed(futures), 1):
            items.append(future.result())
            if i % 100 == 0:
                log(f'Inspected {i}/{len(links)} STAC file extents')
    selected = [x for x in items if intersects_bbox(x['bbox'], bbox)]
    selected.sort(key=lambda x: x['id'])
    if not selected:
        raise ValueError('No cloud assets intersect the extraction box.')
    log(f'STAC pruning: {len(selected)} of {len(items)} Parquet files intersect bbox')
    return selected


def remote_extract(bbox, release):
    stage = CACHE / f'buildings_{release}_bbox.parquet'
    manifest_file = CACHE / 'extraction_manifest.json'
    signature = {'release': release, 'bbox': bbox, 'schema_version': 1}
    if stage.exists() and manifest_file.exists():
        old = load_json(manifest_file)
        if old['signature'] != signature:
            raise ValueError('Existing cache has different scope; use a fresh cache directory.')
        log(f'Reusing completed filtered Parquet ({pq.ParquetFile(stage).metadata.num_rows:,} rows)')
        return stage, old
    items = select_assets(bbox)
    assets = [x['assets']['aws']['alternate']['s3']['href'] for x in items]
    ext = CACHE / 'duckdb_extensions'
    ext.mkdir(exist_ok=True)
    con = duckdb.connect(config={'memory_limit': '2GB', 'threads': 4,
                                 'extension_directory': str(ext),
                                 'temp_directory': str(CACHE / 'duckdb_temp')})
    # Fetch signed official binaries over HTTPS with requests. This avoids
    # bootstrapping HTTPS INSTALL through the not-yet-installed httpfs extension.
    platform = con.execute('PRAGMA platform').fetchone()[0]
    for extension in ('httpfs', 'spatial'):
        log(f'Loading DuckDB {extension}')
        binary = ext / f'{extension}.duckdb_extension'
        if not binary.exists():
            url = f'https://extensions.duckdb.org/v{duckdb.__version__}/{platform}/{extension}.duckdb_extension.gz'
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            binary.write_bytes(gzip.decompress(response.content))
        con.execute(f'INSTALL {quote(binary)}')
        con.execute(f'LOAD {extension}')
    con.execute("SET s3_region='us-west-2'")
    con.execute('SET preserve_insertion_order=false')
    con.execute('SET http_timeout=180')
    paths = '[' + ','.join(quote(x) for x in assets) + ']'
    west, south, east, north = bbox
    query = f'''
        SELECT id AS building_id, ST_AsWKB(geometry) AS geometry_wkb,
               height AS height_m, num_floors AS floor_count,
               num_floors_underground AS underground_floor_count,
               has_parts, is_underground,
               CAST(sources AS JSON)::VARCHAR AS sources_json
        FROM read_parquet({paths}, hive_partitioning=true)
        WHERE bbox.xmin <= {east} AND bbox.xmax >= {west}
          AND bbox.ymin <= {north} AND bbox.ymax >= {south}
          AND ST_Intersects(geometry, ST_MakeEnvelope({west},{south},{east},{north}))
    '''
    (CACHE / 'extraction.sql').write_text(query)
    partial = stage.with_suffix('.partial.parquet')
    log('Querying S3 with bbox pushdown and exact footprint intersection')
    con.execute(f'COPY ({query}) TO {quote(partial)} (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 25000)')
    count = pq.ParquetFile(partial).metadata.num_rows
    if not count:
        raise ValueError('Extraction returned no buildings; refusing an empty deliverable.')
    partial.replace(stage)
    manifest = {'signature': signature, 's3_assets': assets, 'stac_items_total':
                len([x for x in load_json(CACHE/'building_collection.json')['links'] if x['rel']=='item']),
                'selected_assets': len(assets), 'source_rows': count,
                'extracted_at_utc': datetime.now(timezone.utc).isoformat(),
                'staging_geometry_crs': 'EPSG:4326', 'staging_geometry_encoding': 'WKB'}
    manifest_file.write_text(json.dumps(manifest, indent=2))
    con.close()
    log(f'Cloud extraction complete: {count:,} buildings')
    return stage, manifest


def polygonal(geom):
    """Retain all polygon components after make_valid, without inventing geometry."""
    if geom.geom_type in ('Polygon', 'MultiPolygon'):
        return geom
    if geom.geom_type == 'GeometryCollection':
        parts = []
        for child in geom.geoms:
            p = polygonal(child)
            if p is not None:
                parts.extend(p.geoms if p.geom_type == 'MultiPolygon' else [p])
        if parts:
            return shapely.union_all(parts)
    return None


def transform(df, metro):
    geometry = gpd.GeoSeries.from_wkb(df.pop('geometry_wkb'), crs=4326)
    g = gpd.GeoDataFrame(df, geometry=geometry, crs=4326)
    if g.geometry.isna().any() or g.geometry.is_empty.any():
        raise ValueError('Missing/empty source geometry; no buildings silently dropped.')
    repaired = ~g.is_valid
    if repaired.any():
        g.loc[repaired, 'geometry'] = g.loc[repaired, 'geometry'].make_valid().map(polygonal)
    g = g.to_crs(METRIC_CRS)
    projected_bad = ~g.is_valid
    repaired |= projected_bad
    if projected_bad.any():
        g.loc[projected_bad, 'geometry'] = g.loc[projected_bad, 'geometry'].make_valid().map(polygonal)
    if g.geometry.isna().any() or not g.is_valid.all() or not g.geom_type.isin(['Polygon','MultiPolygon']).all():
        raise ValueError('A geometry cannot be repaired as a valid polygon.')
    g.geometry = g.geometry.map(lambda x: MultiPolygon([x]) if x.geom_type == 'Polygon' else x)
    g['geometry_repaired'] = repaired.astype(bool)
    g['footprint_area_m2'] = g.area
    g['height_m'] = pd.to_numeric(g.height_m).astype('float64')
    g['floor_count'] = pd.to_numeric(g.floor_count).astype('Int32')
    g['underground_floor_count'] = pd.to_numeric(g.underground_floor_count).astype('Int32')
    if (g.footprint_area_m2 <= 0).any() or not np.isfinite(g.footprint_area_m2).all():
        raise ValueError('Nonpositive/nonfinite projected footprint area.')
    if g.height_m.dropna().le(0).any() or g.floor_count.dropna().le(0).any():
        raise ValueError('Invalid source height/floor count; investigate instead of silently imputing.')
    g['floor_count_imputed'] = g.floor_count.isna()
    g['floors_used_for_gfa'] = g.floor_count.fillna(1).astype('int32')
    g['gross_floor_area_m2'] = g.footprint_area_m2 * g.floors_used_for_gfa
    # Representative-point assignment preserves complete footprints at boundaries.
    g['in_rmsp'] = g.representative_point().intersects(metro)
    return g


def write_package(stage, manifest, bbox, municipalities, batch_size):
    OUT.mkdir(parents=True, exist_ok=True)
    partial = OUT / 'sao_paulo_building_morphology.partial.gpkg'
    if FINAL.exists() or partial.exists():
        raise FileExistsError('Output exists; refusing to overwrite. Move the previous output to rerun.')
    metro = municipalities.to_crs(METRIC_CRS).geometry.union_all()
    release = manifest['signature']['release']
    summary = {'building_count': 0, 'height_present': 0, 'floor_count_present': 0,
               'floor_count_imputed': 0, 'geometry_repaired': 0, 'in_rmsp': 0,
               'has_parts': 0, 'footprint_area_m2_sum': 0.0, 'gross_floor_area_m2_sum': 0.0}
    for batch in pq.ParquetFile(stage).iter_batches(batch_size=batch_size):
        g = transform(batch.to_pandas(), metro)
        g['overture_release'] = release
        pyogrio.write_dataframe(g, partial, layer='buildings', driver='GPKG',
                                append=summary['building_count'] > 0,
                                geometry_type='MultiPolygon',
                                layer_options={'SPATIAL_INDEX': 'YES'})
        summary['building_count'] += len(g)
        summary['height_present'] += int(g.height_m.notna().sum())
        summary['floor_count_present'] += int(g.floor_count.notna().sum())
        for key in ('floor_count_imputed', 'geometry_repaired', 'in_rmsp', 'has_parts'):
            summary[key] += int(g[key].fillna(False).sum())
        summary['footprint_area_m2_sum'] += float(g.footprint_area_m2.sum())
        summary['gross_floor_area_m2_sum'] += float(g.gross_floor_area_m2.sum())
        log(f'GeoPackage: {summary["building_count"]:,}/{manifest["source_rows"]:,} buildings written')
    if summary['building_count'] != manifest['source_rows']:
        raise ValueError('Written count does not reconcile to source extraction.')
    boundary = gpd.GeoDataFrame({'name':['RMSP (IBGE municipal union)']}, geometry=[metro], crs=METRIC_CRS)
    boundary.to_file(partial, layer='rmsp_boundary', driver='GPKG')
    extent = gpd.GeoDataFrame({'name':['Extraction bounding box']}, geometry=[box(*bbox)], crs=4326).to_crs(METRIC_CRS)
    extent.to_file(partial, layer='extraction_bbox', driver='GPKG')
    metadata = {
        'title': 'São Paulo metropolitan bounding-box building morphology',
        'bbox_wgs84_west_south_east_north': bbox,
        'output_crs': METRIC_CRS,
        'selection': 'All Overture building footprints intersecting the bbox, not clipped. in_rmsp uses a representative point within the IBGE municipality union.',
        'floor_count_definition': 'Overture num_floors: ABOVE-GROUND floors; basement count preserved separately. No height-to-floors inference.',
        'gross_floor_area_definition': 'Estimated footprint_area_m2 * COALESCE(floor_count,1), not surveyed actual GFA. All floors assumed to have footprint extent.',
        'height_definition': 'Overture height in metres when present; source observations/estimates are not independently measured here.',
        'completeness': 'All matching records in the pinned Overture release, not a guarantee that every physical building is mapped.',
        'source_attribution': 'Overture Maps Foundation; individual contributors, provenance and license fields retained in sources_json. See https://docs.overturemaps.org/attribution/',
        'ibge_membership_url': 'https://servicodados.ibge.gov.br/api/v1/localidades/regioes-metropolitanas/04901',
        'ibge_boundary_url': 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=maxima&intrarregiao=municipio',
        'boundary_limitations': 'IBGE API generalized cartography at maximum API quality; in_rmsp is an analytical assignment, not a cadastral boundary adjudication.',
        'municipalities': load_json(CACHE/'rmsp_membership.json')[0]['municipios'],
        'extraction': manifest, 'quality_summary': summary,
        'software': {'duckdb': duckdb.__version__, 'geopandas': gpd.__version__, 'pyogrio': pyogrio.__version__, 'shapely': shapely.__version__},
    }
    with sqlite3.connect(partial) as db:
        db.execute('CREATE UNIQUE INDEX buildings_unique_id ON buildings(building_id)')
        if db.execute('SELECT count(*) FROM buildings WHERE building_id IS NULL OR building_id=""').fetchone()[0]:
            raise ValueError('Missing building identifiers.')
        if db.execute('SELECT count(*) FROM buildings WHERE abs(gross_floor_area_m2-footprint_area_m2*coalesce(floor_count,1)) > 0.00001').fetchone()[0]:
            raise ValueError('Stored GFA does not match the requested formula.')
        db.execute('CREATE TABLE morphology_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.executemany('INSERT INTO morphology_metadata VALUES (?,?)',
                       [(k,json.dumps(v,ensure_ascii=False)) for k,v in metadata.items()])
        db.execute("INSERT INTO gpkg_contents(table_name,data_type,identifier,description,srs_id) VALUES ('morphology_metadata','attributes','Morphology metadata','Provenance, field definitions and quality summary',NULL)")
        db.commit()
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('GeoPackage SQLite integrity check failed.')
    info = pyogrio.read_info(partial, layer='buildings')
    if info['crs'] != METRIC_CRS or info['features'] != summary['building_count']:
        raise ValueError('Final geometry CRS/count validation failed.')
    # Re-read a deterministic sample independently of the writer.
    check = pyogrio.read_dataframe(partial, layer='buildings', max_features=1000)
    if not np.allclose(check.area, check.footprint_area_m2, rtol=1e-10, atol=1e-6):
        raise ValueError('Stored footprint area disagrees with exported geometry.')
    partial.replace(FINAL)
    metadata['file_size_bytes'] = FINAL.stat().st_size
    (OUT/'sao_paulo_building_morphology.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    log(f'Validated GeoPackage: {FINAL} ({FINAL.stat().st_size/1e9:.2f} GB)')
    log(json.dumps(summary))


def self_test():
    # A true 10m square transformed into source CRS checks projection and units.
    metric = gpd.GeoSeries([box(330000,7390000,330010,7390010)]*2, crs=METRIC_CRS)
    df = pd.DataFrame({'building_id':['test-1','test-2'], 'geometry_wkb':metric.to_crs(4326).to_wkb(),
                       'height_m':[9.,None], 'floor_count':[3,None], 'underground_floor_count':[None,None]})
    g = transform(df, box(329000,7389000,331000,7391000))
    assert np.allclose(g.footprint_area_m2,[100,100],atol=1e-5)
    assert np.allclose(g.gross_floor_area_m2,[300,100],atol=1e-5)
    assert g.floor_count.isna().tolist() == [False,True]
    assert g.floor_count_imputed.tolist() == [False,True]
    assert g.in_rmsp.all() and g.crs.to_epsg() == 31983
    assert intersects_bbox([0,0,2,2],[1,1,3,3])
    assert not intersects_bbox([0,0,1,1],[2,2,3,3])
    log('Synthetic metric-area, null fallback and bbox tests passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--batch-size', type=int, default=25000)
    args = parser.parse_args()
    self_test()
    if not args.self_test:
        bbox, municipalities = scope()
        release = load_json(CACHE/'catalog.json')['latest']
        log(f'Pinned release {release}; bbox {bbox}')
        stage, manifest = remote_extract(bbox, release)
        write_package(stage, manifest, bbox, municipalities, args.batch_size)
