"""Generate review diagnostics from executed allocation experiments."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'analysis/outputs/sp_allocation_experiments_2026_09_10';B=ROOT/'analysis/processed/SP/sp_prep_2026_09_10_v3'
a=pd.read_parquet(R/'area_first_allocations.parquet');b=pd.read_parquet(R/'address_first_allocations.parquet')
p=a[['cep','district_id','allocated_jobs']].merge(b[['cep','district_id','allocated_jobs']],on=['cep','district_id'],how='outer',suffixes=('_area','_address')).fillna(0)
p['absolute_difference']=(p.allocated_jobs_area-p.allocated_jobs_address).abs();tv=p.groupby('cep').absolute_difference.sum()/2
j=pd.read_parquet(B/'N07/formal_job_allocation.parquet');diag=j.merge(tv.rename('job_mass_moved'),on='cep',how='left');diag['fraction_moved']=diag.job_mass_moved/diag.formal_jobs;diag.sort_values('job_mass_moved',ascending=False).to_csv(R/'cep_allocation_disagreement.csv',index=False)
miss=a.loc[a.district_id.eq('UNLOCATED')];miss.groupby('allocation_status').agg(ceps=('cep','size'),jobs=('allocated_jobs','sum')).to_csv(R/'unlocated_by_original_status.csv')
asym=pd.read_parquet(R/'support_asymmetry.parquet');asym=asym.loc[asym.area_only_one_side_with_multiple_address_sides];mass=j.loc[j.cep.isin(asym.index),'formal_jobs'].sum()
d=pd.read_csv(R/'district_sensitivity.csv',dtype={'district_id':str});n=int(j.formal_jobs.sum());located=float(a.loc[a.district_id.ne('UNLOCATED'),'allocated_jobs'].sum());mixed=pd.read_parquet(R/'area_mixed_allocations.parquet');mixed_located=float(mixed.loc[mixed.district_id.ne('UNLOCATED'),'allocated_jobs'].sum())
summary={'source_jobs':n,'base_located_jobs':located,'base_located_fraction':located/n,'base_unlocated_jobs':float(miss.allocated_jobs.sum()),'mixed_inclusive_located_jobs':mixed_located,'mixed_inclusive_located_fraction':mixed_located/n,'area_address_job_mass_redistributed':float(tv.sum()),'area_address_ceps_differing':int(tv.gt(1e-6).sum()),'one_business_side_multiple_address_sides_ceps':len(asym),'one_business_side_multiple_address_sides_jobs':int(mass),'districts_area_address_difference_exceeds_10pct':int(d.relative_difference_vs_address.abs().gt(.1).sum()),'pilot_results':d.loc[d.district_id.isin(['10','30','35'])].to_dict('records'),'U2_primary_selected':False,'validation_limit':'Sensitivity and conservation, not accuracy against establishment-level job counts'}
(R/'experiment_findings.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='pilot_results'},indent=2))
