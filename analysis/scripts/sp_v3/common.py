from pathlib import Path
import hashlib,json,time
import duckdb,geopandas as gpd,numpy as np,pandas as pd,pyogrio,shapely
ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'analysis/data/SP'
CFG={};OUT=None;BASE=None

def initialize(path):
 global CFG,OUT,BASE
 CFG=json.loads(Path(path).read_text())
 assert CFG['attribute_construction_authorized'] is False
 assert set(CFG['active_families'])==set(['M1','M2','M3','M4','M6','M7','B1','B2','B3','U1','U2','U3','U4'])
 dest=ROOT/'analysis/processed/SP';OUT=(dest/CFG['run_id']).resolve();BASE=(dest/CFG['baseline_run_id']).resolve()
 if OUT.parent!=dest.resolve() or OUT==BASE or CFG['run_id']=='sp_prep_2026_09_09_v2':raise ValueError('Refusing to overwrite baseline or escape output directory')
 OUT.mkdir(parents=True,exist_ok=True)

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
 tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str,allow_nan=False));tmp.replace(p)

def log(s): print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),s,flush=True)
def con():return duckdb.connect(config={'memory_limit':CFG['duckdb_memory_limit'],'threads':CFG['duckdb_threads'],'preserve_insertion_order':False,'temp_directory':str(OUT/'temp')})
def records(c,q):return json.loads(c.execute(q).fetchdf().to_json(orient='records'))
def copy(c,q,p):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 c.execute("COPY ("+q+") TO '"+str(p).replace("'","''")+"' (FORMAT PARQUET, COMPRESSION ZSTD)")
def read(p,**kwargs):
 g=pyogrio.read_dataframe(p,**kwargs)
 if g.crs is None:raise ValueError(f'Unknown CRS {p}')
 return g.to_crs(CFG['metric_crs'])
def write(g,p):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);g.to_parquet(p,index=False)
def polygon_only(g):
 if g.geom_type in ('Polygon','MultiPolygon'):return g
 return shapely.union_all([polygon_only(x) for x in shapely.get_parts(g) if x.geom_type in ('Polygon','MultiPolygon','GeometryCollection')])
def districts():return gpd.read_parquet(OUT/'N02/districts.parquet')
def assign(g,d):
 # Vectorized intersection candidates and area; deterministic ID resolves equal maximum overlap.
 li,ri=d.sindex.query(g.geometry,predicate='intersects')
 if not len(li):return pd.DataFrame({'district_id':[None]*len(g),'inside_area_m2':np.zeros(len(g)),'district_candidates':np.zeros(len(g),dtype=int)})
 inter=shapely.intersection(g.geometry.values[li],d.geometry.values[ri]);area=shapely.area(inter)
 pairs=pd.DataFrame({'row':li,'district_id':d.district_id.values[ri],'area':area})
 pairs=pairs.loc[pairs.area.gt(0)]
 best=pairs.sort_values(['row','area','district_id'],ascending=[True,False,True]).drop_duplicates('row').set_index('row')
 out=pd.DataFrame(index=range(len(g)));out['district_id']=best.district_id;out['inside_area_m2']=pairs.groupby('row').area.sum();out['district_candidates']=pairs.groupby('row').size()
 return out.fillna({'inside_area_m2':0,'district_candidates':0})
def point_assign(g,d):
 li,ri=d.sindex.query(g.geometry,predicate='intersects')
 p=pd.DataFrame({'row':li,'district_id':d.district_id.values[ri]}).sort_values(['row','district_id']).drop_duplicates('row').set_index('row')
 return p.district_id.reindex(range(len(g)))
