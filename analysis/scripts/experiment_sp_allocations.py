"""M2 approved proxy and U2 mass-conserving experiments; no model attributes."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,geopandas as gpd,duckdb
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'analysis/processed/SP/sp_prep_2026_09_10_v3';OUT=ROOT/'analysis/outputs/sp_allocation_experiments_2026_09_10'

def normalize(s,group):
 total=s.groupby(group).transform('sum')
 return s.div(total.where(total.gt(0))).fillna(0.)

def choose_weights(s,scenario):
 a=normalize(s.business_area,s.cep);b=normalize(s.establishment_addresses,s.cep);r=normalize(s.residential_area,s.cep);m=normalize(s.business_area+s.mixed_area,s.cep)
 has_a=s.business_area.groupby(s.cep).transform('sum').gt(0);has_b=s.establishment_addresses.groupby(s.cep).transform('sum').gt(0);has_r=s.residential_area.groupby(s.cep).transform('sum').gt(0)
 if scenario=='area_first':w=np.where(has_a,a,b);method=np.where(has_a,'business_area','establishment_addresses')
 elif scenario=='address_first':w=np.where(has_b,b,a);method=np.where(has_b,'establishment_addresses','business_area')
 elif scenario=='hybrid':w=np.where(has_a&has_b,.5*a+.5*b,np.where(has_a,a,b));method=np.where(has_a&has_b,'half_area_half_addresses',np.where(has_a,'business_area','establishment_addresses'))
 elif scenario=='equal_workplace':w=normalize((s.business_area.gt(0)|s.establishment_addresses.gt(0)).astype(float),s.cep);method=np.repeat('equal_workplace_districts',len(s))
 elif scenario=='residential_first':w=np.where(has_r,r,np.where(has_a,a,b));method=np.where(has_r,'residential_area',np.where(has_a,'business_area','establishment_addresses'))
 elif scenario=='area_mixed':has_m=(s.business_area+s.mixed_area).groupby(s.cep).transform('sum').gt(0);w=np.where(has_m,m,b);method=np.where(has_m,'business_plus_mixed_area','establishment_addresses')
 else:raise ValueError(scenario)
 # Same low-confidence residential fallback in workplace scenarios where both supports are absent.
 w=pd.Series(w,index=s.index);missing=w.groupby(s.cep).transform('sum').eq(0)&has_r
 w=w.where(~missing,r);method=np.where(missing,'residential_fallback',method)
 return w,method

def main():
 OUT.mkdir(exist_ok=True,parents=True);checks=[]
 def check(name,ok):
  checks.append({'check':name,'passed':bool(ok)})
  if not ok:raise AssertionError(name)
 inputs=[BASE/'N02/districts.parquet',BASE/'N05/crossing_candidates.parquet',BASE/'N05/structures.parquet',BASE/'N03/fiscal_records.parquet',BASE/'N07/cep_cnefe_candidates.parquet',BASE/'N07/formal_job_allocation.parquet']
 def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 initial={str(p.relative_to(ROOT)):sha(p) for p in inputs}
 d=gpd.read_parquet(inputs[0]);nodes=gpd.read_parquet(inputs[1]);st=gpd.read_parquet(inputs[2]);st=st.loc[st.tx_tipo_obra_arte.isin(['PONTE','VIADUTO','TUNEL'])]
 ix,_=st.sindex.query(nodes.geometry,predicate='dwithin',distance=5);nodes['near_bridge_tunnel_5m']=False;nodes.loc[nodes.index[np.unique(ix)],'near_bridge_tunnel_5m']=True
 nodes['selected_m2_proxy']=nodes.junction_candidate & nodes.district_id.notna() & ~nodes.near_bridge_tunnel_5m
 nodes['m2_method']='municipal_three_source_arms_exclude_bridge_viaduct_tunnel_within_5m'
 nodes.to_parquet(OUT/'m2_selection_overlay.parquet',index=False)
 eligible=nodes.loc[nodes.junction_candidate & nodes.district_id.notna()]
 check('M2 unique node IDs',nodes.node_id.is_unique);check('M2 5m approved counts',len(eligible)==107685 and nodes.selected_m2_proxy.sum()==106625)
 check('M2 Bras count',nodes.loc[nodes.district_id.eq('10'),'selected_m2_proxy'].sum()==244)
 eligible.groupby('district_id').agg(candidates=('node_id','size'),selected=('selected_m2_proxy','sum'),excluded=('near_bridge_tunnel_5m','sum')).to_csv(OUT/'m2_district_selection.csv')
 (OUT/'m2_method.json').write_text(json.dumps({'status':'user_approved','threshold_m':5,'excluded_types':['PONTE','VIADUTO','TUNEL'],'candidate_count':107685,'excluded_count':1060,'selected_count':106625,'reduction_fraction':1060/107685,'interpretation':'structure-buffer-excluded planar proxy; no certified physical connectivity or routing graph','join':'node_id; use selected_m2_proxy, not historical accepted_m2_junction','density_constructed':False},indent=2))
 print('M2 selection complete',flush=True)
 c=duckdb.connect(config={'memory_limit':'512MB','threads':1})
 c.read_parquet(str(inputs[3])).create_view('f');c.read_parquet(str(inputs[4])).create_view('cn')
 tax=c.execute("""select cep,district_id,
 sum(case when category not in ('residential','vacant','mixed/other') then greatest(constructed_area_m2,0) else 0 end) business_area,
 sum(case when category='residential' then greatest(constructed_area_m2,0) else 0 end) residential_area,
 sum(case when category='mixed/other' then greatest(constructed_area_m2,0) else 0 end) mixed_area
 from f where accepted_area_aggregation and district_id is not null and regexp_full_match(cep,'[0-9]{8}') and cep not in ('00000000','99999999') group by 1,2""").fetchdf()
 addresses=c.execute('select cep,district_id,sum(evidence_addresses) establishment_addresses from cn group by 1,2').fetchdf();c.close()
 support=tax.merge(addresses,on=['cep','district_id'],how='outer').fillna(0);support.to_parquet(OUT/'cep_district_support.parquet',index=False)
 jobs=pd.read_parquet(inputs[5]);check('Unique CEP job source',jobs.cep.is_unique and jobs.formal_jobs.sum()==5387474)
 fixed=jobs.loc[jobs.allocated_district_id.notna(),['cep','formal_jobs','allocated_district_id','allocation_status']].rename(columns={'allocated_district_id':'district_id'})
 fixed['weight']=1.;fixed['allocated_jobs']=fixed.formal_jobs;fixed['allocation_method']='v3_fixed_location';fixed['evidence_tier']='v3_located_proxy'
 unresolved=jobs.loc[jobs.allocated_district_id.isna(),['cep','formal_jobs','allocation_status']]
 s=support.merge(unresolved,on='cep',how='inner',validate='many_to_one');s['workplace_supported']=s.business_area.gt(0)|s.establishment_addresses.gt(0)
 diag=s.groupby('cep').agg(candidate_districts=('district_id','size'),business_sides=('business_area',lambda x:int(x.gt(0).sum())),address_sides=('establishment_addresses',lambda x:int(x.gt(0).sum())))
 diag['area_only_one_side_with_multiple_address_sides']=diag.business_sides.eq(1)&diag.address_sides.gt(1);diag.to_parquet(OUT/'support_asymmetry.parquet')
 all_results={};summaries=[]
 def save(name,alloc):
  totals=alloc.groupby('cep').allocated_jobs.sum().reindex(jobs.cep).to_numpy()
  check(name+' per-CEP mass',np.allclose(totals,jobs.formal_jobs,rtol=1e-12,atol=1e-6))
  check(name+' weights',np.isfinite(alloc.weight).all() and alloc.weight.between(0,1+1e-12).all() and np.allclose(alloc.groupby('cep').weight.sum(),1))
  check(name+' no duplicate CEP/district',not alloc.duplicated(['cep','district_id']).any())
  check(name+' fixed baseline preserved',np.isclose(alloc.loc[alloc.evidence_tier.eq('v3_located_proxy'),'allocated_jobs'].sum(),3194165))
  alloc['scenario']=name;alloc.to_parquet(OUT/(name+'_allocations.parquet'),index=False)
  totals=alloc.groupby(['district_id','evidence_tier']).allocated_jobs.sum().unstack(fill_value=0).reindex(list(d.district_id)+['UNLOCATED'],fill_value=0);totals['total_jobs']=totals.sum(axis=1);totals['scenario']=name;totals.reset_index().to_csv(OUT/(name+'_district_totals.csv'),index=False)
  mass=alloc.groupby('evidence_tier').allocated_jobs.sum().to_dict();summaries.append({'scenario':name,**mass,'total_jobs':float(alloc.allocated_jobs.sum())});all_results[name]=totals['total_jobs']
 for name in ['area_first','address_first','hybrid','equal_workplace','residential_first','area_mixed']:
  w,method=choose_weights(s,name);a=s[['cep','district_id','formal_jobs','allocation_status']].copy();a['weight']=w;a['allocation_method']=method;a=a.loc[a.weight.gt(0)];a['allocated_jobs']=a.formal_jobs*a.weight
  a['evidence_tier']=np.where(a.allocation_method.str.startswith('residential'),'residential_weighted_proxy','workplace_weighted_proxy')
  missing=unresolved.loc[~unresolved.cep.isin(a.cep)].copy();missing['district_id']='UNLOCATED';missing['weight']=1.;missing['allocated_jobs']=missing.formal_jobs;missing['allocation_method']='no_usable_CEP_support';missing['evidence_tier']='unlocated'
  alloc=pd.concat([fixed,a,missing],ignore_index=True);save(name,alloc)
  if name in ['area_first','address_first']:
   priors={'business_prior':tax.groupby('district_id').business_area.sum(),'located_jobs_prior':fixed.groupby('district_id').formal_jobs.sum()}
   for label,prior in priors.items():
    prior=prior.reindex(d.district_id,fill_value=0);prior=prior/prior.sum();u=missing[['cep','formal_jobs','allocation_status']].merge(prior.rename('weight').rename_axis('district_id').reset_index(),how='cross');u['allocated_jobs']=u.formal_jobs*u.weight;u['allocation_method']='citywide_'+label;u['evidence_tier']='citywide_imputed_proxy'
    save(name+'_'+label,pd.concat([fixed,a,u],ignore_index=True))
  print('U2 '+name+' complete',flush=True)
 pd.DataFrame(summaries).fillna(0).to_csv(OUT/'scenario_mass_summary.csv',index=False)
 comparison=pd.DataFrame(all_results);comparison.index.name='district_id';comparison.to_csv(OUT/'district_scenario_comparison.csv')
 delta=comparison.drop(index='UNLOCATED').copy();delta['area_address_difference']=delta.area_first-delta.address_first;delta['relative_difference_vs_address']=delta.area_address_difference/delta.address_first.replace(0,np.nan);delta['scenario_min']=delta[list(all_results)].min(axis=1);delta['scenario_max']=delta[list(all_results)].max(axis=1)
 delta.join(d.set_index('district_id')[['nm_distrito_municipal']]).sort_values('area_address_difference',key=abs,ascending=False).to_csv(OUT/'district_sensitivity.csv')
 check('Input files unchanged',all(sha(ROOT/k)==v for k,v in initial.items()))
 (OUT/'checks.json').write_text(json.dumps(checks,indent=2));(OUT/'manifest.json').write_text(json.dumps({'inputs':initial,'script_sha256':sha(Path(__file__)),'fixed_located_jobs':3194165,'source_jobs':5387474,'scenario_count':len(summaries),'attribute_construction':False,'U2_primary_selected':False,'fiscal_geography':'v3 largest-overlap whole-parcel district; no new parcel intersection splitting','residual_policy':'unlocated bucket in six base experiments; four explicitly citywide-imputed variants','footprint_experiment':'not executed: needs resolved building-parcel-CEP business attribution','hybrid':'50/50 normalized area and address weights when both available; experimental, not calibrated'},indent=2))
 print('All checks passed: '+str(len(checks)),flush=True)
if __name__=='__main__':main()
