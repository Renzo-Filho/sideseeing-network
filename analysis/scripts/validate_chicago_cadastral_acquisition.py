"""Independent read-only checks for downloaded Chicago-only candidates."""
import datetime as dt, gzip, hashlib, json, re
from pathlib import Path
import geopandas as gpd
import pandas as pd
import shapely

ROOT=Path(__file__).resolve().parents[2]
RUN='chicago_cadastral_2026_09_18'
OUT=ROOT/'analysis/data/Chicago'/RUN
RESULT=ROOT/'analysis/results/Chicago'/RUN
CACHE=ROOT/'analysis/work/evidence'/RUN

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 boundary=ROOT/'analysis/data/Chicago/Boundaries_-_Community_Areas_20260831.geojson'
 city=gpd.read_file(boundary).to_crs(26916).geometry.union_all();shapely.prepare(city)
 keys=set()
 for p in (OUT/'cook_parcels_2024').glob('*.parquet'):keys.update(pd.read_parquet(p,columns=['PIN10']).PIN10.astype(str).str.zfill(10))
 summaries=[];checks=[]
 def check(name,ok,detail):
  checks.append({'check':name,'passed':bool(ok),'detail':detail})
 for folder in sorted(OUT.iterdir()):
  mp=folder/'manifest.json'
  if not mp.exists():continue
  m=json.loads(mp.read_text());name=folder.name
  check(name+' boundary hash',m['boundary_sha256']==sha(boundary),m['boundary_sha256'])
  n=0;seen=set();duplicate=0;badgeometry=0;outsidearea=0.;nonpositive=0;badmatches=0;missingcoords=0;crossing=0;area=0.
  spatial=name in ['cook_parcels_2024','dupage_parcels_current','cook_buildings_2022']
  for rec in m['parts']:
   p=folder/rec['part'];check(name+'/'+p.name+' hash',sha(p)==rec['sha256'],rec['sha256'])
   d=gpd.read_parquet(p) if spatial else pd.read_parquet(p)
   check(name+'/'+p.name+' rows',len(d)==rec['rows'],len(d));n+=len(d)
   ids=d.OBJECTID if spatial else d.source_row_id
   duplicate+=sum(x in seen for x in ids);duplicate+=len(ids)-len(set(ids));seen.update(ids)
   if spatial:
    check(name+'/'+p.name+' CRS',d.crs.to_epsg()==26916,str(d.crs.to_epsg()))
    badgeometry+=int((~d.geometry.is_valid).sum());nonpositive+=int((d.geometry.area<=0).sum())
    covered=shapely.covers(city,d.geometry.values)
    if (~covered).any():outsidearea+=float(shapely.area(shapely.difference(d.geometry.values[~covered],city)).sum())
    crossing+=int(d.crosses_chicago_boundary.sum());area+=float(d.geometry.area.sum())
   elif name.startswith('cook_'):
    if name=='cook_commercial_2024':
     for value in d.chicago_matched_pins:
      matched=json.loads(value);badmatches+=not(matched and all(p[:10] in keys for p in matched))
    else:badmatches+=int((~d.pin.astype(str).str[:10].isin(keys)).sum())
   else:
    lon=pd.to_numeric(d.longitude,errors='coerce');lat=pd.to_numeric(d.latitude,errors='coerce')
    missingcoords+=int((lon.isna()|lat.isna()).sum());pts=gpd.GeoSeries.from_xy(lon,lat,crs=4326).to_crs(26916)
    badmatches+=int((~shapely.covers(city,pts.values)).sum())
  check(name+' total',n==m['rows'],n);check(name+' unique record IDs',duplicate==0,duplicate)
  if spatial:
   check(name+' valid geometries',badgeometry==0,badgeometry);check(name+' positive areas',nonpositive==0,nonpositive)
   check(name+' no outside geometry',outsidearea<0.0001,{'outside_area_m2':outsidearea,'tolerance_m2':0.0001})
  else:
   check(name+' Chicago membership',badmatches==0 and missingcoords==0,{'bad_matches':badmatches,'missing_coordinates':missingcoords})
   # Check unique source IDs across ALL cached pages, including rejected records,
   # so duplicate pagination cannot hide behind Chicago-only selection.
   sourceids=set();rawtotal=0;rawduplicates=0
   if m.get('method')=='bulk CSV':
    rawpath=ROOT/m['raw_csv'];check(name+' raw CSV hash',sha(rawpath)==m['raw_csv_sha256'],m['raw_csv_sha256'])
    cols=['source_row_id','keypin','pins'] if name=='cook_commercial_2024' else ['source_row_id','pin']
    iterator=pd.read_csv(rawpath,dtype=str,usecols=cols,chunksize=100000,keep_default_na=False)
    expected_city_ids=set()
    for chunk in iterator:
     ids=list(chunk.source_row_id);rawduplicates+=sum(i in sourceids for i in ids)+len(ids)-len(set(ids));sourceids.update(ids);rawtotal+=len(ids)
     if name=='cook_commercial_2024':
      for row in chunk.to_dict('records'):
       # Independent parser: split associated PIN list, then remove punctuation.
       tokens=re.split(r'[,;\s]+',row['pins'])+[row['keypin']]
       pins={re.sub(r'[^0-9]','',x) for x in tokens}
       if any(len(x)==14 and x[:10] in keys for x in pins):expected_city_ids.add(row['source_row_id'])
     else:
      selected=chunk.pin.str.zfill(14).str[:10].isin(keys)
      expected_city_ids.update(chunk.loc[selected,'source_row_id'])
    check(name+' independent complete Chicago selection',expected_city_ids==seen,{'expected':len(expected_city_ids),'actual':len(seen),'missing':len(expected_city_ids-seen),'extra':len(seen-expected_city_ids)})
   else:
    for p in sorted((CACHE/name).glob('page_*.json.gz')):
     with gzip.open(p,'rt') as f:rows=json.load(f)['data']
     ids=[r['source_row_id'] for r in rows];rawduplicates+=sum(i in sourceids for i in ids)+len(ids)-len(set(ids));sourceids.update(ids);rawtotal+=len(ids)
   check(name+' full source-export rows',rawtotal==m['source_slice_rows'],rawtotal)
   check(name+' full source-export unique IDs',rawduplicates==0,rawduplicates)
  summaries.append({'dataset':name,'rows':n,'unique_record_ids':len(seen),'crossing_features':crossing if spatial else None,'sum_feature_area_m2':area if spatial else None,'outside_area_m2':outsidearea if spatial else None,'sha256_manifest':sha(mp)})
  print('validated',name,n,flush=True)
 report={'run':RUN,'validated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'datasets':summaries,'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'limitations':['Geometry validity and containment do not establish cadastral completeness or resolve overlaps.','PIN10 is a parcel grouping key, not a validated building-parent ontology.','Socrata mutable-source pagination needs publisher update-time closure checks.']}
 (RESULT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('CHECKS',report['passed'],'passed',report['failed'],'failed',flush=True)
 assert report['failed']==0
if __name__=='__main__':main()
