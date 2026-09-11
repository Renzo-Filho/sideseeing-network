from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,geopandas as gpd,shapely
ROOT=Path(__file__).resolve().parents[3]
CFG=json.loads((ROOT/'analysis/config/sp_attributes_2026_09_11.json').read_text());BASE=ROOT/CFG['base_run'];OLD=ROOT/CFG['baseline_run'];OUT=ROOT/'analysis/outputs/sp_attributes'/CFG['run_id']

def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,default=str,allow_nan=False));tmp.replace(p)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def districts():return gpd.read_parquet(BASE/'N02/districts.parquet').sort_values('district_id').reset_index(drop=True)
def entropy(weights):
 w=np.asarray(weights,float);w=w[w>0]
 return float(-np.sum((w/w.sum())*np.log(w/w.sum()))/np.log(len(CFG['u1_categories']))) if len(w) else np.nan
def block_metrics(geom):
 area=shapely.area(geom);perimeter=shapely.length(geom);compact=4*np.pi*area/(perimeter**2);rect=shapely.minimum_rotated_rectangle(geom);elong=[]
 for p in rect:
  if p.geom_type!='Polygon':elong.append(np.nan);continue
  xy=np.asarray(p.exterior.coords);s=np.sqrt(((xy[1:]-xy[:-1])**2).sum(axis=1));elong.append(s.max()/s.min() if s.min()>0 else np.nan)
 return area,compact,np.array(elong)
class Features:
 def __init__(self):self.rows=[]
 def add(self,code,family,name,value,unit,*,num=None,den=None,coverage=1.,n=0,missing=0,status='computed',primary=False,method='',period='',coverage_basis='eligible source records',source=''):
  if value is not None and not np.isfinite(value):value=None
  self.rows.append(dict(run_id=CFG['run_id'],district_id=code,family_id=family,feature_name=name,value=value,unit=unit,numerator=num,denominator=den,source_version=source or CFG['base_run'],observation_period=period or {'U2':'RAIS 2022; tax/address supports mixed vintage','U3':'census 2022','U4':'2022 population; September 2026 GTFS scenarios','B1':'Overture 2026-08-19.0','B2':'IPTU 2026','B3':'IPTU 2026','U1':'IPTU 2026'}.get(family,'source-specific mixed vintage; see frozen source manifest'),coverage_fraction=coverage,coverage_definition=coverage_basis,n_entities=int(n),n_missing=int(missing),method_version=CFG['method_version'],quality_status=status,missing_reason='no usable source mass' if value is None else None,primary_feature=primary,method=method))
 def frame(self):return pd.DataFrame(self.rows)
