"""Acquire matched, buffered Overture sources with STAC pruning and atomic partitions."""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time
import duckdb
import geopandas as gpd
import pyarrow.parquet as pq
import requests

ROOT=Path(__file__).resolve().parents[2]
RELEASE='2026-08-19.0'
CACHE=ROOT/'analysis/work/prepared/shared/overture_2026_08_19'
CACHE.mkdir(parents=True,exist_ok=True)

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()

def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.json.part');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)

def fetch(url,path):
    if path.exists():return json.loads(path.read_text())
    for attempt in range(3):
        try:
            r=requests.get(url,timeout=45);r.raise_for_status();d=r.json();save(path,d);return d
        except requests.RequestException:
            if attempt==2:raise
            time.sleep(2**attempt)

def quote(s):return "'"+str(s).replace("'","''")+"'"

def main(city,kind):
    source=ROOT/('analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet' if city=='Chicago' else 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet')
    districts=gpd.read_parquet(source)
    region=gpd.GeoSeries([districts.geometry.union_all().buffer(2000)],crs=districts.crs).to_crs(4326)
    west,south,east,north=map(float,region.total_bounds)
    theme='buildings' if kind=='building' else 'transportation'
    folder=CACHE/kind;folder.mkdir(exist_ok=True)
    base=f'https://stac.overturemaps.org/{RELEASE}/{theme}/{kind}'
    collection=fetch(base+'/collection.json',folder/'collection.json')
    urls=[x['href'] for x in collection['links'] if x['rel']=='item']
    def item(url):return fetch(url,folder/'items'/(url.split('/')[-2]+'.json'))
    with ThreadPoolExecutor(max_workers=8) as pool:items=list(pool.map(item,urls))
    chosen=[x for x in items if x['bbox'][0]<=east and x['bbox'][2]>=west and x['bbox'][1]<=north and x['bbox'][3]>=south]
    paths=[x['assets']['aws']['alternate']['s3']['href'] for x in chosen]
    out=ROOT/'analysis/data'/city/'overture_2026_08_19'/kind;out.mkdir(parents=True,exist_ok=True)
    ext=ROOT/'analysis/cache/overture_sp/duckdb_extensions'
    con=duckdb.connect(config={'memory_limit':'2GB','threads':4,'temp_directory':str(CACHE/'temp')})
    for name in ['httpfs','spatial']:con.execute('LOAD '+quote(ext/(name+'.duckdb_extension')))
    con.execute("SET s3_region='us-west-2'");con.execute('SET http_timeout=60');con.execute('SET http_retries=3')
    query_filter=f'bbox.xmin <= {east} AND bbox.xmax >= {west} AND bbox.ymin <= {north} AND bbox.ymax >= {south}'
    manifest={'release':RELEASE,'city':city,'kind':kind,'buffer_m':2000,'bbox':[west,south,east,north],
              'source_boundary_sha256':sha(source),'code_sha256':sha(Path(__file__)),'items_total':len(items),'selected_assets':paths,
              'access_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'license':'ODbL for transportation; buildings per source attribution retained',
              'exact_city_filter':'pending downstream; whole objects intersecting buffered bbox retained','partitions':[]}
    for i,path in enumerate(paths):
        target=out/f'part_{i:04}.parquet';record=target.with_suffix('.json')
        query=f'SELECT * FROM read_parquet({quote(path)}) WHERE {query_filter}'
        sig=hashlib.sha256((query+sha(Path(__file__))).encode()).hexdigest()
        if target.exists() and record.exists():
            old=json.loads(record.read_text())
            if old['signature']!=sig or sha(target)!=old['sha256']:raise ValueError('Existing partition signature mismatch')
            manifest['partitions'].append(old);continue
        schema=con.execute('DESCRIBE '+query).fetchall()
        partial=target.with_suffix('.parquet.part')
        con.execute(f'COPY ({query}) TO {quote(partial)} (FORMAT PARQUET, COMPRESSION ZSTD)')
        count=pq.ParquetFile(partial).metadata.num_rows
        partial.replace(target)
        rec={'source':path,'query':query,'schema':schema,'rows':count,'sha256':sha(target),'bytes':target.stat().st_size,'signature':sig}
        save(record,rec);manifest['partitions'].append(rec)
        print(city,kind,i+1,'/',len(paths),count,flush=True)
    listing='['+','.join(quote(p) for p in sorted(out.glob('*.parquet')))+']'
    total,unique=con.execute(f'SELECT count(*),count(DISTINCT id) FROM read_parquet({listing})').fetchone()
    assert total==unique
    manifest.update(rows=total,unique_ids=unique,complete=True)
    save(out/'manifest.json',manifest)
    con.close()
    print('complete',city,kind,total,flush=True)

if __name__=='__main__':main(*sys.argv[1:])
