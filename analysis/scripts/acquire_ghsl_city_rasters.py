"""Acquire public GHSL candidates; preserve native cells, no model fitting or audit suite."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import datetime as dt, hashlib, json, math, re, time, zipfile
from pathlib import Path
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask
import requests

ROOT=Path(__file__).resolve().parents[2]
RUN='ghsl_public_2026_09_21'
EVIDENCE=ROOT/'analysis/work/evidence/ghsl_2026_09_21'
RAW=ROOT/'analysis/data/shared'/RUN
RESULT=ROOT/'analysis/results/SP_CHI'/RUN
for p in [RAW,RESULT]:p.mkdir(parents=True,exist_ok=True)
BOUNDARIES={'Chicago':ROOT/'analysis/data/Chicago/Boundaries_-_Community_Areas_20260831.geojson','SP':ROOT/'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.part');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)
def download(url,path):
 rec=path.with_suffix(path.suffix+'.source.json')
 if path.exists() and rec.exists():
  d=json.loads(rec.read_text())
  if d['url']==url and path.stat().st_size==d['bytes']:return d
 for attempt in range(3):
  try:
   with requests.get(url,stream=True,timeout=(30,180)) as r:
    r.raise_for_status();tmp=path.with_suffix(path.suffix+'.part')
    with tmp.open('wb') as f:
     for b in r.iter_content(2**20):f.write(b)
    tmp.replace(path)
    d={'url':url,'file':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path),'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'last_modified':r.headers.get('Last-Modified'),'etag':r.headers.get('ETag')};save(rec,d);return d
  except Exception:
   if attempt==2:raise
   time.sleep(2**attempt)
def main():
 index=gpd.read_file('zip://'+str((EVIDENCE/'tile_index.zip').resolve()))
 shapes={};tiles={}
 for city,p in BOUNDARIES.items():
  d=gpd.read_parquet(p) if p.suffix=='.parquet' else gpd.read_file(p)
  shapes[city]=d.to_crs(index.crs).geometry.union_all()
  tiles[city]=sorted(index.loc[index.intersects(shapes[city]),'tile_id'])
 products=json.loads((EVIDENCE/'product_directories.json').read_text());all_receipts=[];outputs=[]
 for product in products:
  name=product['product'].strip('/').split('/')[-1];folder=RAW/name;folder.mkdir(exist_ok=True)
  url=product['version_url']+'tiles/';response=requests.get(url,timeout=90);response.raise_for_status();(EVIDENCE/(name+'_tiles.html')).write_text(response.text)
  links=re.findall('href="([^"]+)"',response.text);chosen={}
  for tile in set(sum(tiles.values(),[])):
   matches=[l for l in links if l.endswith('_'+tile+'.zip')]
   if len(matches)!=1:raise ValueError((name,tile,matches))
   chosen[tile]=matches[0]
  jobs=[(url+file,folder/file) for tile,file in sorted(chosen.items())]
  with ThreadPoolExecutor(max_workers=2) as pool:
   receipts=list(pool.map(lambda x:download(*x),jobs))
  all_receipts.extend(receipts)
  download(product['version_url']+'copyright.txt',folder/'copyright.txt')
  print('DOWNLOADED',name,[(d['bytes'],Path(d['file']).name) for d in receipts],flush=True)
  for city,shape in shapes.items():
   paths=[]
   for tile in tiles[city]:
    p=folder/chosen[tile]
    with zipfile.ZipFile(p) as z:
     members=[n for n in z.namelist() if n.lower().endswith('.tif')]
     if len(members)!=1:raise ValueError((p,members))
    paths.append('/vsizip/'+str(p.resolve())+'/'+members[0])
   with ExitStack() as stack:
    srcs=[stack.enter_context(rasterio.open(p)) for p in paths]
    source=srcs[0];bounds=shape.bounds;res=source.res[0]
    # Preserve native alignment and values; no interpolation or reprojection.
    left=source.transform.c+math.floor((bounds[0]-source.transform.c)/res)*res
    right=source.transform.c+math.ceil((bounds[2]-source.transform.c)/res)*res
    bottom=source.transform.f+math.floor((bounds[1]-source.transform.f)/res)*res
    top=source.transform.f+math.ceil((bounds[3]-source.transform.f)/res)*res
    nodata=source.nodata
    if nodata is None:raise ValueError('Source does not declare NoData; choose an explicit mask policy before proceeding.')
    data,transform=merge(srcs,bounds=(left,bottom,right,top),res=source.res,nodata=nodata)
    inside=geometry_mask([shape.__geo_interface__],data.shape[1:],transform,all_touched=True,invert=True)
    data[:,~inside]=nodata
    outdir=ROOT/'analysis/data'/city/RUN;outdir.mkdir(exist_ok=True)
    path=outdir/(name+'.tif');profile=source.profile.copy();profile.update(driver='GTiff',width=data.shape[2],height=data.shape[1],transform=transform,compress='deflate',tiled=True,blockxsize=256,blockysize=256)
    temp=path.with_suffix('.tif.part')
    with rasterio.open(temp,'w',**profile) as dst:
     dst.write(data);dst.update_tags(**source.tags());dst.update_tags(acquisition_scope=city,mask_policy='all_touched; full original values retained in boundary cells',source_release='R2023A')
    temp.replace(path)
    record={'city':city,'product':name,'epoch':2018 if '_H_' in name else 2020,'units':'metres' if '_H_' in name else 'cubic metres per source cell','path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'source_tiles':tiles[city],'source_crs':source.crs.to_string(),'resolution':list(source.res),'shape':list(data.shape),'nodata':nodata,'dtype':str(data.dtype),'source_scales':list(source.scales),'source_offsets':list(source.offsets),'city_mask_cells':int(inside.sum()),'source_nodata_inside_mask':int((inside & (data[0]==nodata)).sum()),'boundary_path':str(BOUNDARIES[city].relative_to(ROOT)),'boundary_sha256':sha(BOUNDARIES[city]),'mask_policy':'native 100m cells intersecting city; outside cells set to source NoData; boundary-cell values NOT fractionally allocated','scientific_validation':'not performed; acquisition only'}
    outputs.append(record);save(outdir/(name+'.json'),record);print('SAVED',city,name,data.shape,flush=True)
  save(RESULT/'progress.json',{'source_downloads':all_receipts,'outputs':outputs,'complete':False})
 manifest={'run':RUN,'source_release':'R2023A','height_epoch':2018,'volume_epoch':2020,'tiles':tiles,'source_downloads':all_receipts,'outputs':outputs,'complete':True,'scientific_validation':False,'model_modified':False}
 save(RESULT/'manifest.json',manifest);save(RESULT/'progress.json',manifest)
if __name__=='__main__':main()
