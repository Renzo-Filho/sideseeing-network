# Overture 2026-08-19.0 buildings. Chicago keeps the original GeoParquet
# columns; São Paulo is reduced to the same height/bounding-box-centre table
# that the original method A factor reads.
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import duckdb
import geopandas as gpd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely

RELEASE = '2026-08-19.0'
ROOT = Path(arg['scratch'])
BASE = f'https://stac.overturemaps.org/{RELEASE}/buildings/building'


def get_json(url):
    response = requests.get(url, timeout=(30, 90))
    response.raise_for_status()
    return response.json()


def polygonal(geometry):
    fixed = shapely.make_valid(geometry)
    if fixed.geom_type in ('Polygon', 'MultiPolygon'):
        return fixed
    return shapely.union_all([part for part in shapely.get_parts(fixed)
                              if part.geom_type in ('Polygon', 'MultiPolygon')])


collection = get_json(BASE + '/collection.json')
urls = [link['href'] for link in collection['links'] if link['rel'] == 'item']
with ThreadPoolExecutor(max_workers=8) as pool:
    items = list(pool.map(get_json, urls))
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
for city, unit_key, suffix in (('Chicago', 'chi_units', 'chi'), ('SP', 'sp_units', 'sp')):
    units = gpd.read_parquet(arg[unit_key])
    area = gpd.GeoSeries([units.geometry.union_all().buffer(2000)], crs=units.crs).to_crs(4326)
    west, south, east, north = map(float, area.total_bounds)
    chosen = [item['assets']['aws']['alternate']['s3']['href'] for item in items
              if item['bbox'][0] <= east and item['bbox'][2] >= west
              and item['bbox'][1] <= north and item['bbox'][3] >= south]
    if not chosen:
        raise ValueError(f'No building assets overlap {city}')
    paths = '[' + ','.join("'" + path.replace("'", "''") + "'" for path in chosen) + ']'
    source = (f'FROM read_parquet({paths}, hive_partitioning=true) '
              f'WHERE bbox.xmin <= {east} AND bbox.xmax >= {west} '
              f'AND bbox.ymin <= {north} AND bbox.ymax >= {south}')
    if suffix == 'chi':
        target = ROOT / 'overture_buildings_chi.parquet'
        con.execute(f"COPY (SELECT * {source}) TO '{target}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        out['buildings_chi'] = str(target)
    else:
        stage = ROOT / 'overture_buildings_sp_stage.parquet'
        con.execute(f"COPY (SELECT height, geometry {source} AND height > 0) "
                    f"TO '{stage}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        target = ROOT / 'overture_buildings_sp_heights.parquet'
        writer = pq.ParquetWriter(target, pa.schema([('height_m', pa.float64()),
                                                     ('x', pa.float64()), ('y', pa.float64())]),
                                  compression='zstd')
        try:
            for batch in pq.ParquetFile(stage).iter_batches(batch_size=100_000):
                frame = batch.to_pandas()
                geometry = gpd.GeoSeries.from_wkb(frame.geometry, crs=4326)
                bad = ~geometry.is_valid
                if bad.any():
                    geometry.loc[bad] = geometry.loc[bad].map(polygonal)
                bounds = geometry.to_crs(31983).bounds
                writer.write_table(pa.table({'height_m': frame.height.astype(float).to_numpy(),
                                             'x': ((bounds.minx + bounds.maxx) / 2).to_numpy(),
                                             'y': ((bounds.miny + bounds.maxy) / 2).to_numpy()}))
        finally:
            writer.close()
        stage.unlink()
        out['buildings_sp'] = str(target)
con.close()
return out
