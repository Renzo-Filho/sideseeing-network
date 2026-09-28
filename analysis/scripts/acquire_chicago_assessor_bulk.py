"""Stream source-year CSV exports and retain only Chicago parcel-linked rows.

Bulk CSVs are transient local evidence, never final Chicago data. Their row counts
and source IDs are independently checked before publication of the manifest.
"""
import argparse, datetime as dt, json, re, time
import pandas as pd
import requests
from acquire_chicago_cadastral import ROOT,OUT,CACHE,RESULT,BASE,SOC,fetch,sha,save,parcel_keys,commercial_pins

def run(name):
 host,id,where,select,_=SOC[name];assert name.startswith('cook_')
 url=f'https://{host}/resource/{id}.csv';folder=OUT/name;folder.mkdir(exist_ok=True)
 if (folder/'manifest.json').exists():
  m=json.loads((folder/'manifest.json').read_text());assert m.get('method')=='bulk CSV'
  for part in m['parts']:assert sha(folder/part['part'])==part['sha256']
  print('verified complete',name,m['rows'],flush=True);return
 keys=parcel_keys();cache=CACHE/name;cache.mkdir(exist_ok=True)
 meta=fetch(f'https://{host}/api/views/{id}.json',{},cache/'metadata.json.gz');save(folder/'source_metadata.json',meta)
 count=int(fetch(url.replace('.csv','.json'),{'$select':'count(*) as n','$where':where},cache/'count.json.gz')[0]['n'])
 params={'$where':where,'$select':select+',:id as source_row_id','$limit':count+1}
 path=cache/'bulk.csv';receipt=cache/'bulk_receipt.json'
 if path.exists():
  rec=json.loads(receipt.read_text());assert rec['where']==where and sha(path)==rec['sha256']
 else:
  for attempt in range(4):
   try:
    temp=path.with_suffix('.csv.part');started=dt.datetime.now(dt.timezone.utc).isoformat()
    r=requests.get(url,params=params,timeout=(30,180),stream=True);r.raise_for_status()
    with temp.open('wb') as f:
     for block in r.iter_content(2**20):f.write(block)
    temp.replace(path);save(receipt,{'url':url,'params':params,'where':where,'started_utc':started,'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'sha256':sha(path)});break
   except Exception:
    if attempt==3:raise
    time.sleep(2**attempt)
 total=0;seen=set();duplicates=0;records=[];rejected=0
 for i,df in enumerate(pd.read_csv(path,dtype=str,chunksize=50000,keep_default_na=False)):
  total+=len(df);ids=df.source_row_id
  duplicates+=sum(x in seen for x in ids)+len(ids)-len(set(ids));seen.update(ids)
  if name=='cook_commercial_2024':
   def matches(row):
    pins=commercial_pins(row);assert pins, 'Unparseable commercial PIN';return sorted(p for p in pins if p[:10] in keys)
   matched=[matches(r) for r in df.to_dict('records')];keep=pd.Series([bool(x) for x in matched],index=df.index)
   df['chicago_matched_pins']=[json.dumps(x) for x in matched]
   df['entity_may_span_city_boundary']=True
  else:keep=df.pin.str.zfill(14).str[:10].isin(keys)
  rejected+=int((~keep).sum());d=df.loc[keep].copy()
  if 'pin' in d:d['pin']=d.pin.str.zfill(14)
  target=folder/f'part_{i:05d}.parquet';tmp=target.with_suffix('.parquet.part');d.to_parquet(tmp,index=False);tmp.replace(target)
  records.append({'part':target.name,'candidate_rows':len(df),'rows':len(d),'boundary_sha256':BASE['boundary_sha256'],'sha256':sha(target),'bytes':target.stat().st_size})
  if i%5==0:print(name,'source rows processed',total,'retained',sum(x['rows'] for x in records),flush=True)
 assert total==count,(name,total,count)
 assert duplicates==0,(name,duplicates)
 m={**BASE,'dataset':name,'source':url,'where':where,'method':'bulk CSV','source_slice_rows':count,'source_unique_ids':len(seen),'source_duplicate_ids':duplicates,'rejected_outside_chicago':rejected,'raw_csv':str(path.relative_to(ROOT)),'raw_csv_sha256':sha(path),'rows':sum(x['rows'] for x in records),'filter':'PIN10 matches Cook parcels with positive-area intersection inside exact Chicago boundary; commercial any associated PIN matches','parts':records,'complete':True,'limitations':'Commercial entities can cross the city boundary. Source area is not allocated; PIN10 does not prove physical building identity.'}
 save(folder/'manifest.json',m);save(RESULT/(name+'.json'),m);print('COMPLETE',name,m['rows'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('datasets',nargs='+',choices=[n for n in SOC if n.startswith('cook_')]);a=p.parse_args()
 for name in a.datasets:run(name)
