"""Read-only input review supporting documentation; no feature construction."""
from pathlib import Path
import json,hashlib
import duckdb,pyogrio,openpyxl
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'analysis/data/SP';OUT=ROOT/'analysis/outputs/sp_resolution_review_2026_09_10'
OUT.mkdir(exist_ok=True)
def rows(c,q):return json.loads(c.execute(q).fetchdf().to_json(orient='records'))
def main():
 r={'scope':'Source review only; no integration or attributes executed'}
 for key,rel in [('classes','Cadastro e Vias/classvias.gpkg'),('structures','Cadastro e Vias/obra_arte.gpkg'),('water','Meio Ambiente/massa_d_agua.gpkg')]:
  p=RAW/rel;g=pyogrio.read_dataframe(p,layer=p.stem)
  r[key]={'path':str(p.relative_to(ROOT)),'rows':len(g),'crs':str(g.crs),'fields':list(g.columns),'invalid':int((~g.is_valid).sum()),'empty':int(g.is_empty.sum()),'null_geometry':int(g.geometry.isna().sum()),'geometry_types':g.geom_type.value_counts().to_dict()}
  field={'classes':'Classifica','structures':'tx_tipo_obra_arte','water':'cd_tipo_acidente'}[key]
  r[key]['categories']=g[field].fillna('<null>').value_counts().to_dict()
  if key=='classes':r[key]['unique_codlog']=int(g.Lg_codlog.nunique())
  if key=='structures':r[key]['reference_years']=g.tx_ano_referencia.str.strip().value_counts().to_dict()
  print(key,r[key]['rows'],flush=True)
 w=openpyxl.load_workbook(RAW/'Cadastro e Vias/Dicionario_dados_IPTU.xlsx',read_only=True,data_only=True)
 r['iptu_dictionary']=[{'field':row[0],'definition':row[1]} for row in w.active.values if row[0] is not None]
 c=duckdb.connect(config={'memory_limit':'512MB','threads':2,'preserve_insertion_order':False})
 c.read_csv(str(RAW/'Socioeconomico/rais_empregos_sp_2022.csv'),all_varchar=True).create_view('jobs')
 r['jobs']=rows(c,"select count(*) n_rows,count(distinct cep) unique_ceps,sum(try_cast(empregos as bigint)) total_jobs,count(*) filter(where not regexp_full_match(cep,'[0-9]{8}') or cep is null) invalid_cep,count(*) filter(where try_cast(empregos as bigint)<=0 or try_cast(empregos as bigint) is null) invalid_jobs from jobs")[0]
 r['jobs_top_ceps']=rows(c,'select cep,try_cast(empregos as bigint) jobs from jobs order by jobs desc limit 10')
 r['cep_district_crosswalk_status']='not_constructed; requires validated postal geography or address allocation'
 folder=RAW/'Socioeconomico/f-6gy-sptrans-latest';r['gtfs']={}
 for p in sorted(folder.glob('*.txt')):
  c.read_csv(str(p),all_varchar=True).create_view('feed')
  info={'rows':c.execute('select count(*) from feed').fetchone()[0],'fields':c.execute('select * from feed limit 0').fetchdf().columns.tolist(),'bytes':p.stat().st_size}
  if p.stem in ['calendar','agency','frequencies']:info['sample']=rows(c,'select * from feed limit 3')
  if p.stem=='calendar':info['date_range']=rows(c,'select min(start_date) start_date,max(end_date) end_date from feed')
  r['gtfs'][p.name]=info
 r['new_source_files']=[]
 files=[RAW/'Cadastro e Vias/Dicionario_dados_IPTU.xlsx',RAW/'Cadastro e Vias/classvias.gpkg',RAW/'Cadastro e Vias/obra_arte.gpkg',RAW/'Meio Ambiente/massa_d_agua.gpkg',RAW/'Socioeconomico/rais_empregos_sp_2022.csv']+sorted(folder.glob('*.txt'))
 for p in files:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  r['new_source_files'].append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':h.hexdigest()})
 (OUT/'evidence.json').write_text(json.dumps(r,indent=2,ensure_ascii=False,default=str))
 print(json.dumps({'jobs':r['jobs'],'gtfs':{k:v['rows'] for k,v in r['gtfs'].items()}},indent=2))
if __name__=='__main__':main()
