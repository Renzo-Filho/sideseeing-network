"""Download Chicago-only cadastral candidates; no model attributes are constructed.

Public ArcGIS spatial ID selection is an over-inclusive, verified enclosing mask.
Every final geometry is clipped to the exact project boundary. Assessor records
are retained only through PIN10 matches to positive-area Cook parcel intersections.
Raw response caches are local, ignored evidence, not Chicago deliverables.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse, datetime as dt, gzip, hashlib, json, time, threading
from pathlib import Path
import geopandas as gpd
import pandas as pd
import requests
import shapely
from shapely.geometry import MultiPolygon

ROOT=Path(__file__).resolve().parents[2]
RUN='chicago_cadastral_2026_09_18'
OUT=ROOT/'analysis/data/Chicago'/RUN
CACHE=ROOT/'analysis/work/evidence'/RUN
RESULT=ROOT/'analysis/results/Chicago'/RUN
BOUNDARY=ROOT/'analysis/data/Chicago/Boundaries_-_Community_Areas_20260831.geojson'
for p in [OUT,CACHE,RESULT]:p.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.part');t.write_text(json.dumps(d,indent=2));t.replace(p)
def fetch(url,params,path,post=False):
 sig=hashlib.sha256(json.dumps([url,params],sort_keys=True).encode()).hexdigest()
 if path.exists():
  with gzip.open(path,'rt') as f: box=json.load(f)
  assert box['signature']==sig, str(path)
  return box['data']
 for attempt in range(5):
  try:
   r=requests.post(url,data=params,timeout=180) if post else requests.get(url,params=params,timeout=180)
   r.raise_for_status();d=r.json()
   if isinstance(d,dict) and ('error' in d or 'errorCode' in d):raise RuntimeError(str(d)[:1500])
   path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.part')
   with gzip.open(tmp,'wt') as f:json.dump({'signature':sig,'url':url,'params':params,'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'data':d},f)
   tmp.replace(path);return d
  except Exception:
   if attempt==4:raise
   time.sleep(min(2**attempt,16))
def polygonal(g):
 if g.geom_type in ['Polygon','MultiPolygon']:return g
 pieces=[]
 for x in getattr(g,'geoms',[]):
  p=polygonal(x)
  if p.geom_type=='Polygon':pieces.append(p)
  else:pieces.extend(p.geoms)
 return MultiPolygon(pieces)
def clip_frame(frame,city):
 invalid=~frame.geometry.is_valid
 frame=frame.copy();frame.geometry=shapely.make_valid(frame.geometry.values)
 if not frame.geometry.geom_type.isin(['Polygon','MultiPolygon']).all():frame.geometry=frame.geometry.map(polygonal)
 frame['source_geometry_area_m2']=frame.geometry.area
 inside=shapely.contains(city,frame.geometry.values)
 crossing=~inside
 if crossing.any():frame.loc[crossing,'geometry']=shapely.intersection(frame.geometry.values[crossing],city)
 frame['chicago_intersection_m2']=frame.geometry.area
 frame=frame[frame.chicago_intersection_m2>0].copy()
 if not frame.geometry.geom_type.isin(['Polygon','MultiPolygon']).all():frame.geometry=frame.geometry.map(polygonal)
 frame['crosses_chicago_boundary']=frame.chicago_intersection_m2 < frame.source_geometry_area_m2-1e-6
 return frame,int(invalid.sum())

CITY=gpd.read_file(BOUNDARY).to_crs(26916).geometry.union_all()
CITY_WKB=CITY.wkb
LOCAL=threading.local()
def thread_city():
 if not hasattr(LOCAL,"city"):
  LOCAL.city=shapely.from_wkb(CITY_WKB);shapely.prepare(LOCAL.city)
 return LOCAL.city
BASE={'run':RUN,'boundary':str(BOUNDARY.relative_to(ROOT)),'boundary_sha256':sha(BOUNDARY),'metric_crs':26916,'modeling':False}
ARCS={
 'cook_parcels_2024':('https://gis.cookcountyil.gov/traditional/rest/services/parcelHistorical/MapServer/2024','OBJECTID,Name,PIN10,PARCELTYPE,AssessorBLDGclass,PoliticalTownship,MUNICIPALITY'),
 'dupage_parcels_current':('https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/FeatureServer/0','OBJECTID,PIN,ACREAGE,ACRE_SOURCE,MUNICIPALITY,REA017_PROP_CLASS,GIS_Prop_Class,PARCEL_STATUS'),
 'cook_buildings_2022':('https://gis.cookcountyil.gov/traditional/rest/services/buildingFootprint_2022/MapServer/0','OBJECTID,Area_SQFT,Year,Ground_Z,Max_Point,Height,GlobalID')}

def arc(name):
 url,fields=ARCS[name];folder=OUT/name;folder.mkdir(exist_ok=True)
 metadata=fetch(url,{'f':'json'},CACHE/name/'metadata.json.gz');save(folder/'source_metadata.json',metadata)
 # Buffer and simplify only for remote selection; verified covers exact boundary.
 mask=CITY.buffer(20).simplify(5);assert mask.covers(CITY)
 mask=gpd.GeoSeries([mask],crs=26916).to_crs(4326).iloc[0]
 polys=list(mask.geoms) if mask.geom_type=='MultiPolygon' else [mask]
 rings=[list(shapely.geometry.polygon.orient(p,sign=-1).exterior.coords) for p in polys]
 query={'f':'json','where':'1=1','geometry':json.dumps({'rings':rings,'spatialReference':{'wkid':4326}}),'geometryType':'esriGeometryPolygon','inSR':4326,'spatialRel':'esriSpatialRelIntersects','returnIdsOnly':'true'}
 data=fetch(url+'/query',query,CACHE/name/'ids.json.gz',True);ids=sorted(data['objectIds']);assert len(ids)==len(set(ids))
 print(name,'candidate IDs',len(ids),flush=True)
 n=1000; batches=[ids[i:i+n] for i in range(0,len(ids),n)]
 def batch(arg):
  i,keys=arg;path=folder/f'part_{i:05d}.parquet';record=folder/f'part_{i:05d}.json'
  if record.exists():
   d=json.loads(record.read_text());assert d['boundary_sha256']==BASE['boundary_sha256'] and d['sha256']==sha(path);return d
  q={'f':'geojson','objectIds':','.join(map(str,keys)),'outFields':fields,'returnGeometry':'true','outSR':26916}
  d=fetch(url+'/query',q,CACHE/name/f'batch_{i:05d}.json.gz',True)
  fs=d['features'];assert len(fs)==len(keys),(name,i,len(fs),len(keys))
  g=gpd.GeoDataFrame.from_features(fs,crs=26916)
  assert set(g.OBJECTID)==set(keys)
  g,invalid=clip_frame(g,thread_city())
  tmp=path.with_suffix('.parquet.part');g.to_parquet(tmp,index=False);tmp.replace(path)
  rec={'part':path.name,'boundary_sha256':BASE['boundary_sha256'],'candidate_rows':len(keys),'rows':len(g),'source_invalid_geometries':invalid,'sha256':sha(path),'bytes':path.stat().st_size,'city_area_m2':float(g.geometry.area.sum()),'crossing_rows':int(g.crosses_chicago_boundary.sum())}
  save(record,rec);return rec
 records=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for i,r in enumerate(pool.map(batch,enumerate(batches))):
   records.append(r)
   if i%20==0:print(name,i+1,'/',len(batches),'retained',sum(x['rows'] for x in records),flush=True)
 manifest={**BASE,'dataset':name,'source':url,'source_schema_sha256':sha(folder/'source_metadata.json'),'remote_candidates':len(ids),'rows':sum(r['rows'] for r in records),'filter':'positive-area intersection with exact Chicago community-area union; geometries clipped; original area retained separately','parts':records,'complete':True}
 assert sum(r['candidate_rows'] for r in records)==len(ids)
 save(folder/'manifest.json',manifest);save(RESULT/(name+'.json'),manifest)
 print('COMPLETE',name,manifest['rows'],flush=True)

def commercial_pins(row):
 import re
 text=str(row.get('pins',''))+' '+str(row.get('keypin',''))
 values=re.findall(r'(?<![0-9])(?:[0-9]{2}-[0-9]{2}-[0-9]{3}-[0-9]{3}-[0-9]{4}|[0-9]{14})(?![0-9])',text)
 return {v.replace('-','') for v in values}

def parcel_keys():
 folder=OUT/'cook_parcels_2024';assert json.loads((folder/'manifest.json').read_text())['complete']
 keys=set()
 for p in sorted(folder.glob('*.parquet')):
  d=pd.read_parquet(p,columns=['PIN10']);keys.update(d.PIN10.dropna().astype(str).str.zfill(10))
 assert all(len(x)==10 and x.isdigit() for x in keys)
 return keys
SOC={
 'cook_universe_2024':('datacatalog.cookcountyil.gov','nj4t-kc8j','year=2024','pin,pin10,year,class,township_code,township_name,lon,lat,chicago_community_area_num,chicago_community_area_name,row_id','row_id'),
 'cook_residential_2024':('datacatalog.cookcountyil.gov','x54s-btds','year=2024','*','row_id'),
 'cook_condo_2024':('datacatalog.cookcountyil.gov','3r7i-mrz4','year=2024','*','row_id'),
 'cook_commercial_2024':('datacatalog.cookcountyil.gov','csik-bsws','year=2024','keypin,pins,year,township,class_es,sheet,model,bldgsf,gross_building_area,netrentablesf,stories,property_type_use,subclass2,aprx_comm_sf,landsf,tot_units,yearbuilt','keypin,sheet,model'),
 'benchmarking_2023':('data.cityofchicago.org','xq83-jr8c','data_year=2023','*','id'),
 'benchmarking_covered_current':('data.cityofchicago.org','g5i5-yz37','1=1','*','building_id')}

def soc(name):
 import re
 host,id,where,select,order=SOC[name];order=':id';select=select+',:id as source_row_id';url=f'https://{host}/resource/{id}.json';folder=OUT/name;folder.mkdir(exist_ok=True)
 keys=parcel_keys() if name.startswith('cook_') else None
 meta=fetch(f'https://{host}/api/views/{id}.json',{},CACHE/name/'metadata.json.gz');save(folder/'source_metadata.json',meta)
 count=int(fetch(url,{'$select':'count(*) as n','$where':where},CACHE/name/'count.json.gz')[0]['n'])
 print(name,'source-year rows',count,flush=True)
 # Source slice is frozen into cached pages. No out-of-city records enter final files.
 step=10000
 def page(i):
  path=folder/f'part_{i:05d}.parquet';record=folder/f'part_{i:05d}.json'
  if record.exists():
   d=json.loads(record.read_text());assert d['sha256']==sha(path) and d['boundary_sha256']==BASE['boundary_sha256'];return d
  q={'$select':select,'$where':where,'$order':order,'$limit':step,'$offset':i*step}
  data=fetch(url,q,CACHE/name/f'page_{i:05d}.json.gz');assert len(data)==min(step,count-i*step)
  df=pd.DataFrame(data);extra={}
  if keys is not None:
   if name=='cook_commercial_2024':
    def matches(row):
     candidates=commercial_pins(row)
     return sorted(p for p in candidates if p[:10] in keys)
    matched=[matches(row) for row in data]
    keep=[bool(x) for x in matched];df['chicago_matched_pins']=[json.dumps(x) for x in matched]
    df['entity_may_span_city_boundary']=True
   else:
    pin=df['pin'].astype(str).str.zfill(14);keep=pin.str[:10].isin(keys)
   df=df.loc[keep].copy()
   if 'pin' in df:df['pin']=df['pin'].astype(str).str.zfill(14)
  else:
   lon=pd.to_numeric(df.get('longitude'),errors='coerce');lat=pd.to_numeric(df.get('latitude'),errors='coerce');ok=lon.notna()&lat.notna()
   points=gpd.GeoSeries.from_xy(lon[ok],lat[ok],crs=4326).to_crs(26916)
   keep=pd.Series(False,index=df.index);keep.loc[ok]=shapely.covers(thread_city(),points.values)
   extra['missing_coordinates']=int((~ok).sum());df=df.loc[keep].copy()
  # Serialize nested Socrata location objects uniformly for stable tabular storage.
  for col in df.columns:
   if df[col].map(lambda x:isinstance(x,(dict,list))).any():df[col]=df[col].map(lambda x:json.dumps(x) if isinstance(x,(dict,list)) else x)
  tmp=path.with_suffix('.parquet.part');df.to_parquet(tmp,index=False);tmp.replace(path)
  rec={**extra,'part':path.name,'candidate_rows':len(data),'rows':len(df),'boundary_sha256':BASE['boundary_sha256'],'sha256':sha(path),'bytes':path.stat().st_size};save(record,rec);return rec
 records=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for i,r in enumerate(pool.map(page,range((count+step-1)//step))):
   records.append(r)
   if i%10==0:print(name,i+1,'pages; retained',sum(x['rows'] for x in records),flush=True)
 manifest={**BASE,'dataset':name,'source':url,'where':where,'order':order,'source_slice_rows':count,'rows':sum(x['rows'] for x in records),'filter':'Cook PIN10 matches positive-area Chicago parcels' if keys else 'reported coordinates covered by exact Chicago boundary','parts':records,'complete':True,'limitations':'Commercial entity attributes may describe an entity spanning the boundary; area not allocated. Source updates during paging remain a snapshot-consistency risk.'}
 save(folder/'manifest.json',manifest);save(RESULT/(name+'.json'),manifest);print('COMPLETE',name,manifest['rows'],flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('datasets',nargs='+',choices=list(ARCS)+list(SOC));args=parser.parse_args()
 for name in args.datasets:
  (arc if name in ARCS else soc)(name)
