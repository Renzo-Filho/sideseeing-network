# The installer replaces __KIND__ with place or segment before saving this
# complete program in each Curio acquisition node. No repository code is used
# when the saved dataflow runs.
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import duckdb
import geopandas as gpd

KIND = '__KIND__'
assert KIND in ('place', 'segment')
THEME = {'place': 'places', 'segment': 'transportation'}[KIND]
RELEASE = '2026-08-19.0'
ROOT = Path(arg['scratch'])
BASE = f'https://stac.overturemaps.org/{RELEASE}/{THEME}/{KIND}'


def get_json(url):
    response = requests.get(url, timeout=(30, 90))
    response.raise_for_status()
    return response.json()


collection = get_json(BASE + '/collection.json')
item_urls = [link['href'] for link in collection['links'] if link['rel'] == 'item']
with ThreadPoolExecutor(max_workers=8) as pool:
    items = list(pool.map(get_json, item_urls))

con = duckdb.connect(config={'threads': 4, 'memory_limit': '2GB',
                             'temp_directory': str(ROOT)})
for extension in ('httpfs', 'spatial'):
    try:
        con.execute('LOAD ' + extension)
    except duckdb.Error:
        con.execute('INSTALL ' + extension)
        con.execute('LOAD ' + extension)
con.execute("SET s3_region='us-west-2'")
con.execute('SET http_timeout=180')
con.execute('SET http_retries=3')

out = dict(arg)
for city, unit_key, suffix in (('SP', 'sp_units', 'sp'), ('Chicago', 'chi_units', 'chi')):
    units = gpd.read_parquet(arg[unit_key])
    area = gpd.GeoSeries([units.geometry.union_all().buffer(2000)], crs=units.crs).to_crs(4326)
    west, south, east, north = map(float, area.total_bounds)
    chosen = [item['assets']['aws']['alternate']['s3']['href'] for item in items
              if item['bbox'][0] <= east and item['bbox'][2] >= west
              and item['bbox'][1] <= north and item['bbox'][3] >= south]
    if not chosen:
        raise ValueError(f'No {KIND} assets overlap {city}')
    paths = '[' + ','.join("'" + path.replace("'", "''") + "'" for path in chosen) + ']'
    target = ROOT / f'overture_{KIND}_{suffix}.parquet'
    sql = (f'SELECT * FROM read_parquet({paths}, hive_partitioning=true) '
           f'WHERE bbox.xmin <= {east} AND bbox.xmax >= {west} '
           f'AND bbox.ymin <= {north} AND bbox.ymax >= {south}')
    escaped_target = str(target).replace("'", "''")
    con.execute(f"COPY ({sql}) TO '{escaped_target}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    out[('places_' if KIND == 'place' else 'segments_') + suffix] = str(target)
con.close()
return out
