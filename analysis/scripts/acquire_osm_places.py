"""Extract named OpenStreetMap place elements (shop/amenity/office/craft/healthcare/tourism) for one city.

Source: Geofabrik regional extracts (illinois / brazil-sudeste) in analysis/data/shared/osm_geofabrik, read with the
DuckDB spatial extension's ST_ReadOSM. Nodes keep their coordinates; ways are located at the mean of their node
coordinates; relations are not used. Exact city filtering and amenity exclusions happen downstream
(evaluate_places_against_cnefe.py). The public Overpass servers timed out repeatedly on 2026-10-01, so this replaced
an Overpass-tile version. Usage: acquire_osm_places.py Chicago|SP
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import duckdb
import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parents[2]
KEYS = ['shop', 'amenity', 'office', 'craft', 'healthcare', 'tourism']
SRC = ROOT / 'analysis/data/shared/osm_geofabrik'
CITY = {'Chicago': ('analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet',
                    'https://download.geofabrik.de/north-america/us/illinois-latest.osm.pbf'),
        'SP': ('analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet',
               'https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf')}
EXT = ROOT / 'analysis/cache/overture_sp/duckdb_extensions/spatial.duckdb_extension'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(2**22), b''):
            h.update(chunk)
    return h.hexdigest()


def main(city):
    districts, url = CITY[city]
    pbf = SRC / url.rsplit('/', 1)[1]
    w, s, e, n = gpd.read_parquet(ROOT / districts).to_crs(4326).total_bounds
    w, s, e, n = w - 0.01, s - 0.01, e + 0.01, n + 0.01
    out = ROOT / 'analysis/data' / city / 'osm_2026_10_01'
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(config={'memory_limit': '4GB', 'threads': 4, 'temp_directory': str(out / 'duckdb_tmp')})
    con.execute(f"LOAD '{EXT}'")
    place = "map_contains(tags, 'name') AND (" + ' OR '.join(f"map_contains(tags, '{k}')" for k in KEYS) + ')'
    read = f"st_readosm('{pbf}')"
    con.execute(f"""CREATE TABLE nodes AS SELECT 'node' AS osm_type, id AS osm_id, lat, lon, tags FROM {read}
                    WHERE kind = 'node' AND {place} AND lat BETWEEN {s} AND {n} AND lon BETWEEN {w} AND {e}""")
    con.execute(f"CREATE TABLE ways AS SELECT id, refs, tags FROM {read} WHERE kind = 'way' AND {place}")
    con.execute('CREATE TABLE refs AS SELECT DISTINCT unnest(refs) AS ref FROM ways')
    con.execute(f"""CREATE TABLE coords AS SELECT id, lat, lon FROM {read}
                    WHERE kind = 'node' AND id IN (SELECT ref FROM refs)""")
    con.execute(f"""CREATE TABLE way_pts AS
                    SELECT 'way' AS osm_type, w.id AS osm_id, avg(c.lat) AS lat, avg(c.lon) AS lon, any_value(w.tags) AS tags
                    FROM (SELECT id, tags, unnest(refs) AS ref FROM ways) w JOIN coords c ON c.id = w.ref
                    GROUP BY w.id HAVING lat BETWEEN {s} AND {n} AND lon BETWEEN {w} AND {e}""")
    df = con.execute("""SELECT osm_type, osm_id, lat, lon, tags['name'] AS name, to_json(tags)::VARCHAR AS tags
                        FROM (SELECT * FROM nodes UNION ALL SELECT * FROM way_pts)""").df()
    con.close()
    target = out / 'places.parquet'
    df.to_parquet(target, index=False)
    try:
        last_modified = requests.head(url, allow_redirects=True, timeout=60,
                                      headers={'User-Agent': 'sideseeing-network-research/1.0'}).headers.get('Last-Modified')
    except requests.RequestException:
        last_modified = None  # server date unavailable; the file's SHA-256 and MD5 still identify it
    manifest = dict(city=city, source_url=url, source_file=str(pbf.relative_to(ROOT)), source_sha256=sha(pbf),
                    source_md5_file=(pbf.parent / (pbf.name + '.md5')).read_text().split()[0],
                    source_last_modified_http=last_modified, bbox_wsen=[w, s, e, n],
                    keys=KEYS, rule='named nodes and ways with any key; way location = mean node coordinate; relations not used',
                    access_utc=dt.datetime.now(dt.timezone.utc).isoformat(), rows=len(df),
                    rows_by_type=df.osm_type.value_counts().to_dict(), sha256=sha(target),
                    license='ODbL 1.0, © OpenStreetMap contributors', exact_city_filter='pending downstream',
                    code_sha256=sha(Path(__file__)))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('complete', city, len(df), manifest['rows_by_type'], flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
