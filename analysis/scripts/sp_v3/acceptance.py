"""Preparation acceptance only: integrity, conservation, coverage and resumable handoff."""
from . import common as C
import json,math,platform,importlib.metadata
import geopandas as gpd,numpy as np,pandas as pd,pyogrio,shapely

def acceptance():
 out=C.OUT/'N09';checks=[]
 C.dump(out/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),'packages':dict(sorted((x.metadata['Name'],x.version) for x in importlib.metadata.distributions() if x.metadata['Name']))})
 def check(name,passed,detail=None):
  checks.append({'check':name,'passed':bool(passed),'detail':detail})
  if not passed: C.dump(out/'failed_checks.json',checks);raise AssertionError(name)
 qa={n:json.loads((C.OUT/n/'qa.json').read_text()) for n in ['N02','N03','N04','N05','N06','N07','N08']}
 d=C.districts();check('96 unique valid metric districts',len(d)==96 and d.district_id.is_unique and d.is_valid.all() and d.crs.to_epsg()==31983)
 check('positive land and exact gross partition',d.land_area_m2.gt(0).all() and np.allclose(d.land_area_m2+d.water_area_m2,d.gross_area_m2,atol=.01))
 coverage=pd.DataFrame(json.loads((C.OUT/'N04/coverage.json').read_text()))
 check('96 street coverage rows conserve length',len(coverage)==96 and coverage.district_id.is_unique and np.allclose(coverage[['observed_fraction','imputed_fraction','unresolved_fraction']].sum(axis=1),1))
 blocks=gpd.read_parquet(C.OUT/'N06/blocks.parquet')
 check('normalized blocks valid and metric',blocks.crs.to_epsg()==31983 and blocks.is_valid.all() and (~blocks.is_empty).all() and blocks.area.gt(0).all())
 del blocks
 c=C.con()
 def view(name,path): c.read_parquet(str(C.OUT/path)).create_view(name)
 view('tax','N03/fiscal_records.parquet');view('identity','N03/parcel_identity.parquet')
 tax=c.execute('select count(*),count(distinct taxpayer_id),sum(constructed_area_m2),sum(case when accepted_area_aggregation then constructed_area_m2 else 0 end),count(*) filter(where accepted_area_aggregation and exact_condo_disagreement) from tax').fetchone()
 check('fiscal unique units and source mass',tax[0]==tax[1]==qa['N03']['records'] and math.isclose(tax[2],qa['N03']['raw_area_m2']))
 check('competing links never accepted',tax[4]==0)
 check('accepted tax area within raw area',0<=tax[3]<=tax[2])
 check('accepted fiscal locations have unique geometry and district',c.execute("select count(*) from tax where accepted_area_aggregation and (district_id is null or geometry_status!='unique_geometry_candidate')").fetchone()[0]==0)
 view('edges','N04/edges.parquet')
 edge=c.execute('select count(*),count(distinct edge_id),count(*) filter(where canonical_edge) from edges').fetchone()
 check('edge identity and geometry deduplication',edge[0]==edge[1]==qa['N04']['valid_source_edges'] and edge[0]-edge[2]==qa['N04']['duplicate_geometry_excess'])
 view('jobs','N07/formal_job_allocation.parquet')
 jobs=c.execute('select count(*),count(distinct cep),sum(formal_jobs),sum(case when allocated_district_id is not null then formal_jobs else 0 end) from jobs').fetchone()
 check('unique postal jobs and conservation',jobs[0]==jobs[1]==29594 and jobs[2]==5387474 and jobs[3]==qa['N07']['employment']['allocated_jobs'])
 p=qa['N07']['population'];check('census population conservation',math.isclose(p['allocated_population']+p['outside_residual_population'],p['source_population'],abs_tol=.01))
 view('service','N08/stop_route_service.parquet');bad=c.execute('select count(*) from service where expected_departures is null or not isfinite(expected_departures) or expected_departures<0').fetchone()[0]
 check('finite nonnegative service',bad==0)
 view('buildings','N06/buildings/*/buildings_*.parquet');view('links','N06/buildings/*/parcel_links_*.parquet')
 b=c.execute('select count(*),count(distinct building_id),count(*) filter(where inside_city_area_m2<=0) from buildings').fetchone()
 check('unique municipal buildings with positive overlap',b[0]==b[1]==qa['N06']['buildings']['records'] and b[2]==0)
 link=c.execute('select count(*),count(*) filter(where accepted_tax_transfer),count(*) filter(where overlap_area_m2<=0 or footprint_overlap_fraction<=0 or footprint_overlap_fraction>1.000001) from links').fetchone()
 check('building parcel candidates do not duplicate tax mass',link[1]==0 and link[2]==0,{'pairs':link[0]})
 # Independent municipal scan, rather than summing the same district extraction counters.
 city=shapely.union_all(d.geometry.values);shapely.prepare(city);source_count=0;boundary_count=0
 source=C.RAW/'Edificacoes/sao_paulo_building_morphology.gpkg'
 with pyogrio.open_arrow(source,layer='buildings',columns=['building_id'],bbox=tuple(city.bounds),batch_size=25000,use_pyarrow=True) as (meta,reader):
  for batch in reader:
   g=shapely.from_wkb(batch.column(meta['geometry_name']).to_numpy(zero_copy_only=False));inside=shapely.covers(city,g);source_count+=int(inside.sum())
   boundary=g[~inside & shapely.intersects(city,g)];boundary_count+=len(boundary)
   if len(boundary): source_count+=int((shapely.area(shapely.intersection(city,boundary))>0).sum())
 check('independent source scan equals municipal unique IDs',source_count==b[0],{'source_count':source_count,'boundary_candidates':boundary_count})
 for code in C.CFG['pilot_districts']:
  f=next((C.OUT/'N06/buildings'/code).glob('buildings_*.parquet'));g=gpd.read_parquet(f)
  check('pilot '+code+' stored footprint area matches metric geometry',g.is_valid.all() and np.allclose(g.area,g.footprint_area_m2,rtol=1e-7,atol=.001))
 for n in ['N02','N03','N04','N05','N06','N07','N08']:
  cp=json.loads((C.OUT/n/'checkpoint.json').read_text());check(n+' output hashes',all(C.sha(C.OUT/k)==v for k,v in cp['outputs'].items()))
 manifest=json.loads((C.OUT/'N01/manifest.json').read_text())
 check('raw sources unchanged',all(C.sha(C.ROOT/x['path'])==x['sha256'] for x in manifest['sources']))
 check('v2 baseline unchanged',all(C.sha(C.BASE/k)==v for k,v in manifest['baseline_hashes'].items()))
 # This is an input availability table; no densities, entropy, shape summaries or model values.
 coverage=coverage.merge(pd.DataFrame(qa['N06']['by_district'])[['district_id','buildings','buildings_with_overlap_candidate']],on='district_id',validate='one_to_one')
 taxdistrict=c.execute('select district_id,count(*) located_tax_accounts,sum(constructed_area_m2) located_tax_area_m2 from tax where accepted_area_aggregation group by district_id').fetchdf()
 jobdistrict=c.execute('select allocated_district_id district_id,sum(formal_jobs) allocated_job_mass from jobs where allocated_district_id is not null group by allocated_district_id').fetchdf()
 coverage=coverage.merge(taxdistrict,on='district_id',how='left',validate='one_to_one').merge(jobdistrict,on='district_id',how='left',validate='one_to_one')
 coverage.to_parquet(out/'district_input_coverage.parquet',index=False);coverage.to_csv(out/'district_input_coverage.csv',index=False);c.close()
 families={
 'M1':('ready_for_construction','Canonical source street geometry; retain declared carriageway/source-universe sensitivity.'),
 'M2':('blocked','Crossings are candidates only; edge-level, approach and divided-carriageway decisions are unresolved.'),
 'M3':('ready_for_construction','Normalized eligible blocks; shape calculations and pilot distribution checks belong to N10.'),
 'M4':('ready_for_construction','Normalized eligible blocks; shape calculations and pilot distribution checks belong to N10.'),
 'M6':('provisional','Observed, imputed and unresolved classes retained; citywide hierarchy comparison requires residual review and no-imputation sensitivity.'),
 'M7':('provisional','Canonical cadastral entity candidates available; noncadastral completeness and parcel-type semantics remain limitations.'),
 'B1':('ready_for_construction','Municipal building subset and land mask validated; footprint union, source/imagery checks and ratios belong to N10.'),
 'B2':('provisional','One positive floor report per accepted cadastral entity; ancillary garage/storage excluded, floor conflicts withheld.'),
 'B3':('provisional','Declared unique-fiscal-unit area proxy passes citywide 95% mass gate; common-area semantics not independently certified and district completeness varies.'),
 'U1':('provisional','38 labels mapped, entity use profiles available; parcel-type semantics and unknown/mixed coverage must accompany construction.'),
 'U2':('blocked','Only 59.29% of saved RAIS job mass geolocated; below 95% gate. Resolve multi-district, tax-only and unmatched CEPs; reconcile upstream null-CEP loss.'),
 'U3':('ready_for_construction','Area-weighted census allocation conserves population with explicit outside residual.'),
 'U4':('ready_for_construction','Validated expected bus service; 400m binary Euclidean catchment, 800m sensitivity, maximum stop supply per reachable route/direction; population overlay still to construct.')}
 readiness={'run_id':C.CFG['run_id'],'preparation_execution':'N01-N09 executed; acceptance is family-specific','attribute_construction_started':False,'model_fitted':False,'full_13_family_model_ready':False,'next_step':'Start N10 for ready families and declared provisional proxies only after authorization; resolve M2 and U2 before claiming a complete model. M6 remains incomplete.', 'street_length_coverage':{k:float((coverage[k]*coverage.source_length_m).sum()/coverage.source_length_m.sum()) for k in ['observed_fraction','imputed_fraction','unresolved_fraction']},'families':{k:{'status':v[0],'reason':v[1]} for k,v in families.items()},'tax_area_coverage':tax[3]/tax[2],'employment_mass_coverage':jobs[3]/jobs[2],'municipal_buildings':b[0],'passed_integrity_checks':len(checks)}
 C.dump(out/'checks.json',checks);C.dump(out/'readiness.json',readiness)
 C.dump(out/'qa.json',{'checks_passed':len(checks),'all_integrity_checks_passed':True,'all_model_families_ready':False,'attribute_construction':False})
