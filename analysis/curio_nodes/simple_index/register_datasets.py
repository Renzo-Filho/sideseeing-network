"""Register the simplified-index inputs that Curio does not have yet, in a Curio user's dataset store.

Large files are hard-linked (no copy; the Curio sandbox refuses symlinks); GTFS text tables are converted to
all-string Parquet like the CTA tables already registered. Existing dataset IDs are never overwritten.

Usage (Curio venv): python register_datasets.py /path/to/curio/.curio/users/<user>/datasets
"""
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / 'analysis/data'
W = ROOT / 'analysis/work/prepared'
GHSL = 'ghsl_public_2026_09_21/GHS_BUILT_{p}_GLOBE_R2023A_54009_100.tif'

DATASETS = [
    ('data.sideseeing.sp-districts-prepared', 'São Paulo districts (prepared)', W / 'SP/sp_prep_2026_09_10_v3/N02/districts.parquet', 'parquet',
     'SideSeeing', '96 municipal districts, EPSG:31983, with land_area_m2 (hydrography removed).'),
    ('data.sideseeing.chicago-community-areas-prepared', 'Chicago Community Areas (prepared)', W / 'Chicago/chi_local_2026_09_16_v1/districts.parquet', 'parquet',
     'SideSeeing', '77 Community Areas, EPSG:26916, repaired geometry.'),
    ('data.sideseeing.sp-districts-municipal', 'São Paulo districts (municipal source)', D / 'SP/Cadastro e Vias/distrito_municipal_v2.gpkg', 'gpkg_to_geoparquet',
     'Prefeitura de São Paulo (GeoSampa)', 'Unprepared municipal district layer (GeoParquet copy of the GeoPackage), used for the GHSL cell overlap as in the BV evaluation.'),
    ('data.overture.places-chicago', 'Overture Places, Chicago (2026-08-19.0)', D / 'Chicago/overture_2026_08_19/place/part_0000.parquet', 'parquet',
     'Overture Maps', 'Places theme, 2 km-buffered city bounding box.'),
    ('data.overture.places-sao-paulo', 'Overture Places, São Paulo (2026-08-19.0)', D / 'SP/overture_2026_08_19/place/part_0000.parquet', 'parquet',
     'Overture Maps', 'Places theme, 2 km-buffered city bounding box.'),
    ('data.ibge.cnefe-2022-sao-paulo', 'IBGE CNEFE 2022, São Paulo addresses', D / 'SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv', 'csv',
     'IBGE', 'National address file for statistical purposes, Census 2022; semicolon-separated; COD_ESPECIE 1 = private dwelling.'),
    ('data.overture.building-heights-sao-paulo', 'Overture building heights, São Paulo metropolitan bbox (2026-08-19.0)', D / 'SP/Edificacoes/sao_paulo_building_morphology.gpkg', 'gpkg_heights',
     'Overture Maps', 'One row per building with an Overture height (height_m > 0): height_m and the centre of its bounding box (x, y, EPSG:31983) from the GeoPackage R-tree. Curio does not read GeoPackage datasets.'),
    ('data.overture.transportation-segments-sao-paulo', 'Overture road segments, São Paulo (2026-08-19.0)', D / 'SP/overture_2026_08_19/segment/part_0000.parquet', 'parquet',
     'Overture Maps', 'Transportation segments, 2 km-buffered city bounding box.'),
    ('data.ghsl.chicago-h-agbh-e2018', 'GHSL gross building height 2018, Chicago', D / ('Chicago/' + GHSL.format(p='H_AGBH_E2018')), 'geotiff', 'European Commission JRC', 'GHS-BUILT-H R2023A, 100 m, ESRI:54009.'),
    ('data.ghsl.chicago-v-e2020', 'GHSL built volume 2020, Chicago', D / ('Chicago/' + GHSL.format(p='V_E2020')), 'geotiff', 'European Commission JRC', 'GHS-BUILT-V R2023A, 100 m, ESRI:54009.'),
    ('data.ghsl.sao-paulo-h-anbh-e2018', 'GHSL net building height 2018, São Paulo', D / ('SP/' + GHSL.format(p='H_ANBH_E2018')), 'geotiff', 'European Commission JRC', 'GHS-BUILT-H R2023A, 100 m, ESRI:54009.'),
    ('data.ghsl.sao-paulo-h-agbh-e2018', 'GHSL gross building height 2018, São Paulo', D / ('SP/' + GHSL.format(p='H_AGBH_E2018')), 'geotiff', 'European Commission JRC', 'GHS-BUILT-H R2023A, 100 m, ESRI:54009.'),
    ('data.ghsl.sao-paulo-v-e2020', 'GHSL built volume 2020, São Paulo', D / ('SP/' + GHSL.format(p='V_E2020')), 'geotiff', 'European Commission JRC', 'GHS-BUILT-V R2023A, 100 m, ESRI:54009.'),
] + [('data.sptrans.gtfs-sao-paulo-' + n.replace('_', '-'), 'SPTrans GTFS ' + n.replace('_', ' '), D / f'SP/Socioeconomico/f-6gy-sptrans-latest/{n}.txt',
      'gtfs', 'SPTrans', 'SPTrans static GTFS table, all columns as text (bus, metro and CPTM routes).') for n in ('stops', 'routes', 'trips', 'stop_times')]


# Lane H (harmonized model): the accepted family tables, hard-linked unchanged so their SHA-256 still matches the contract.
import dataflow  # noqa: E402
DATASETS += [(d, f'Accepted feature table ({d.split("feature-")[1].upper()})', ROOT / path, path.rsplit('.', 1)[1], 'SideSeeing',
              f'Accepted family table of contract sp_chicago_model_v1 ({path}); 173 units unless one city per table.')
             for path, d in dataflow.H_TABLES.items()]


def register(store, dataset_id, name, source, fmt, publisher, description):
    folder = store / f'{dataset_id}@1'
    if (folder / 'manifest.json').exists():
        print('SKIP existing', dataset_id)
        return
    (folder / 'data').mkdir(parents=True, exist_ok=True)
    if fmt == 'gpkg_to_geoparquet':
        import geopandas as gpd
        target = folder / 'data' / (source.stem + '.parquet')
        gpd.read_file(source).to_parquet(target)
        fmt = 'parquet'
    elif fmt == 'gpkg_heights':
        import sqlite3
        import pyarrow as pa
        import pyarrow.parquet as pq
        target = folder / 'data' / 'building_heights.parquet'
        con = sqlite3.connect(f'file:{source}?mode=ro', uri=True)
        rows = con.execute('SELECT b.height_m, (r.minx + r.maxx) / 2, (r.miny + r.maxy) / 2 FROM buildings b '
                           'JOIN rtree_buildings_geom r ON b.fid = r.id WHERE b.height_m > 0').fetchall()
        con.close()
        h, x, y = zip(*rows)
        pq.write_table(pa.table({'height_m': h, 'x': x, 'y': y}), target, compression='zstd')
        fmt = 'parquet'
    elif fmt == 'gtfs':
        import duckdb
        target = folder / 'data' / (source.stem + '.parquet')
        con = duckdb.connect()
        con.read_csv(str(source), all_varchar=True, header=True).write_parquet(str(target), compression='zstd')
        con.close()
        fmt = 'parquet'
    else:
        target = folder / 'data' / source.name
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)
    manifest = {'id': dataset_id, 'name': name, 'version': '1.0.0', 'compatibility': {'curioRuntime': '>=0.5.0', 'major': 1},
                'format': fmt, 'dataFile': f'data/{target.name}', 'description': description, 'publisher': publisher,
                'sourceLabel': publisher, 'license': 'See source publisher terms', 'tags': ['sideseeing', 'simple-index'],
                'createdAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'sourcePath': str(source.relative_to(ROOT))}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('ADD', dataset_id, target.stat().st_size, 'bytes')


if __name__ == '__main__':
    store = Path(sys.argv[1])
    for spec in DATASETS:
        register(store, *spec)
