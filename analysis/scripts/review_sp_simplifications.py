"""Read-only scenario counts; no attribute construction or frozen-run mutation."""
from pathlib import Path
import json
import geopandas as gpd,pandas as pd
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'analysis/processed/SP/sp_prep_2026_09_10_v3';O=ROOT/'analysis/outputs/sp_simplification_review_2026_09_10'
O.mkdir(exist_ok=True)
n=gpd.read_parquet(R/'N05/crossing_candidates.parquet');s=gpd.read_parquet(R/'N05/structures.parquet');d=gpd.read_parquet(R/'N02/districts.parquet')
n=n.loc[n.junction_candidate & n.district_id.notna()].copy();rows=[];summaries=[]
for group,types in [('bridge_tunnel',['PONTE','VIADUTO','TUNEL']),('all_structures',list(s.tx_tipo_obra_arte.unique()))]:
 sub=s.loc[s.tx_tipo_obra_arte.isin(types)]
 for distance in [0,5,10,20]:
  a,b=sub.sindex.query(n.geometry,predicate='dwithin',distance=distance);near=pd.Series(False,index=n.index);near.iloc[pd.unique(a)]=True
  table=n.assign(near=near).groupby('district_id').agg(all_candidates=('node_id','size'),near=('near','sum')).reset_index();table['far']=table.all_candidates-table.near;table['exclusion_fraction']=table.near/table.all_candidates;table['structure_group']=group;table['distance_m']=distance;rows.append(table)
  summaries.append({'structure_group':group,'distance_m':distance,'all_candidates':len(n),'near':int(near.sum()),'far':int((~near).sum()),'exclusion_fraction':float(near.mean()),'structure_records_associated':int(len(pd.unique(b)))})
t=pd.concat(rows,ignore_index=True);t.to_csv(O/'m2_district_scenarios.csv',index=False)
q={'structure_source_records':s.tx_tipo_obra_arte.value_counts().to_dict(),'municipal_three_arm_candidates':len(n),'outside_or_unassigned_three_arm_candidates':int(gpd.read_parquet(R/'N05/crossing_candidates.parquet').query('junction_candidate and district_id.isna()').shape[0]),'scenarios':summaries,'pilot_5m_bridge_tunnel':t.loc[t.district_id.isin(['10','35','30']) & t.distance_m.eq(5) & t.structure_group.eq('bridge_tunnel')].to_dict('records'),'largest_relative_exclusions_5m':t.loc[t.distance_m.eq(5)&t.structure_group.eq('bridge_tunnel')].nlargest(10,'exclusion_fraction').to_dict('records'),'interpretation':'Candidate counts only. Structure features are records, not necessarily unique physical structures. No connectivity or model attribute accepted.'}
(O/'evidence.json').write_text(json.dumps(q,indent=2));print(json.dumps(q,indent=2))
# Accepted M6 preparation overlay: preserve frozen v3 evidence and observed class.
e=pd.read_parquet(R/'N04/edges.parquet',columns=['edge_id','class_observed','class_model','class_imputed','conflicting_classes','canonical_edge'])
e['class_model_previous']=e.class_model;e['new_local_assignment']=e.class_model.isna();e['class_model']=e.class_model.fillna('LOCAL');e['class_imputed']=e.class_observed.isna();e['method']='all_unclassified_local_user_decision_2026_09_10';e.to_parquet(O/'m6_classification_overlay.parquet',index=False)
cov=pd.DataFrame(json.loads((R/'N04/coverage.json').read_text()));cov['previous_imputed_fraction']=cov.imputed_fraction;cov['new_local_fraction']=cov.unresolved_fraction;cov['imputed_fraction']=cov.imputed_fraction+cov.unresolved_fraction;cov['unresolved_fraction']=0.;cov.to_csv(O/'m6_coverage_overlay.csv',index=False)
assert e.edge_id.is_unique and e.class_model.notna().all() and int(e.new_local_assignment.sum())==23764
assert ((cov.observed_fraction+cov.imputed_fraction-1).abs()<1e-9).all()
(O/'m6_method.json').write_text(json.dumps({'status':'user_accepted','rule':'retain observed matches; retain prior Local imputation; assign all remaining unclassified records LOCAL, including conflict-quarantined records, while preserving conflict flags','new_local_assignments':int(e.new_local_assignment.sum()),'total_imputed_records':int(e.class_imputed.sum()),'observed_records':int(e.class_observed.notna().sum()),'attribute_construction':False,'frozen_base_run':str(R.relative_to(ROOT)),'overlay_join':'one-to-one on edge_id before later feature construction; canonical_edge remains authoritative for duplicates'},indent=2))
# Quantify availability of weighting evidence, without allocating any jobs.
import duckdb
c=duckdb.connect(config={'memory_limit':'512MB','threads':1});c.read_parquet(str(R/'N03/fiscal_records.parquet')).create_view('f');c.read_parquet(str(R/'N07/formal_job_allocation.parquet')).create_view('j')
availability=c.execute("""with w as (select cep,count(distinct district_id) districts,sum(constructed_area_m2) area from f where accepted_area_aggregation and category not in ('residential','vacant','mixed/other') and constructed_area_m2>0 group by cep) select allocation_status,count(*) ceps,sum(formal_jobs) jobs,count(*) filter(where area>0) ceps_with_business_area,coalesce(sum(formal_jobs) filter(where area>0),0) jobs_with_business_area from j left join w using(cep) group by 1""").fetchdf();availability.to_csv(O/'u2_weight_evidence_availability.csv',index=False);c.close()
# Extra diagnostics: geographic scope, residential fallback support and nongeographic residual.
import shapely,hashlib
municipal=s.loc[s.intersects(shapely.union_all(d.geometry.values))]
q['structure_records_intersecting_municipality']=municipal.tx_tipo_obra_arte.value_counts().to_dict()
q['largest_relative_exclusions_5m']=[{**x,'district_name':d.set_index('district_id').loc[x['district_id'],'nm_distrito_municipal']} for x in q['largest_relative_exclusions_5m']]
(O/'evidence.json').write_text(json.dumps(q,indent=2))
c=duckdb.connect(config={'memory_limit':'512MB','threads':1})
for name,path in [('f','N03/fiscal_records.parquet'),('j','N07/formal_job_allocation.parquet'),('a','N07/address_reference.parquet')]:c.read_parquet(str(R/path)).create_view(name)
res=c.execute("""with tx as (select cep,count(distinct district_id) districts from f where accepted_area_aggregation and category='residential' group by 1),cn as(select cep,count(*) addresses from a where species in ('1','2') and geolevel in ('1','2') and lat between -24.2 and -23.1 and lon between -47.3 and -45.6 group by 1) select j.allocation_status,count(*) ceps,sum(formal_jobs) jobs,count(*) filter(where tx.districts>0) residential_tax_ceps,coalesce(sum(formal_jobs) filter(where tx.districts>0),0) residential_tax_job_mass,count(*) filter(where cn.addresses>0) dwelling_address_ceps,coalesce(sum(formal_jobs) filter(where cn.addresses>0),0) dwelling_address_job_mass from j left join tx using(cep) left join cn using(cep) where allocated_district_id is null group by 1""").fetchdf();res.to_csv(O/'u2_residential_evidence_availability.csv',index=False)
unmatched=c.execute("select cep,formal_jobs,allocation_status from j where allocation_status='unmatched' order by formal_jobs desc").fetchdf();unmatched.head(20).to_csv(O/'u2_unmatched_priority.csv',index=False)
sentinel=int(unmatched.loc[unmatched.cep.eq('99999999'),'formal_jobs'].sum());(O/'u2_residual_summary.json').write_text(json.dumps({'unmatched_jobs':int(unmatched.formal_jobs.sum()),'unmatched_top10_jobs':int(unmatched.formal_jobs.head(10).sum()),'cep_99999999_jobs':sentinel,'cep_99999999_total_job_fraction':sentinel/5387474,'geographic_evidence':'No match for 99999999 in current geographic supports; official coding semantics require upstream verification','maximum_located_fraction_if_only_99999999_remained_unlocated':1-sentinel/5387474,'jobs_allocated_in_this_review':False},indent=2));c.close()
(O/'reproduction.json').write_text(json.dumps({'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_checkpoint_sha256':{k:hashlib.sha256((R/k/'checkpoint.json').read_bytes()).hexdigest() for k in ['N02','N03','N04','N05','N07']},'frozen_outputs_modified':False,'model_attributes_constructed':False},indent=2))
