"""Bounded H4 readiness review. Produces a proposed matrix, never fits or ranks."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3';OUT=ROOT/'analysis/results/SP_CHI/harmonization_2026_09_22_h4_review'

def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 path=BASE/'tables/candidate_attributes_wide.parquet';manifest=json.loads((BASE/'publication_manifest.json').read_text())
 assert sha(path)==manifest['output_sha256'][str(path.relative_to(BASE))], 'Published candidate matrix changed'
 data=pd.read_parquet(path)
 classes=['motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown']
 families={
 'M1':{'columns':['mapped_street_density_km_km2'],'type':'scalar','transform':'log'},
 'M6':{'columns':['M6_share_'+c for c in classes],'type':'composition','transform':'joint_sqrt_hellinger'},
 'B1':{'columns':['footprint_coverage_land'],'type':'scalar','transform':'identity'},
 'BV':{'columns':['net_grid_height_land'],'type':'scalar','transform':'log1p'},
 'U3':{'columns':['population_density_gross_km2'],'type':'scalar','transform':'log'},
 'U4':{'columns':['bus_supply_weekday_am_400m'],'type':'scalar','transform':'log1p'}}
 for f in families.values():f['weight']=1/6
 cols=[c for f in families.values() for c in f['columns']];matrix=data[cols].copy()
 expected={f'SP:{i:02}' for i in range(1,97)}|{f'CHI:{i:02}' for i in range(1,78)}
 checks=[]
 def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
 ck('published source hash',True);ck('exact173 unique IDs',set(matrix.index)==expected and matrix.index.is_unique)
 ck('15 feature columns',len(cols)==15 and len(set(cols))==15)
 ck('all selected values finite',np.isfinite(matrix.to_numpy()).all());ck('no selected missing',not matrix.isna().any().any())
 ck('composition sums1',np.allclose(matrix[families['M6']['columns']].sum(axis=1),1,rtol=0,atol=1e-8))
 ck('composition bounded',matrix[families['M6']['columns']].ge(0).all().all() and matrix[families['M6']['columns']].le(1).all().all())
 ck('B1 bounded',matrix.footprint_coverage_land.between(0,1).all())
 for family,f in families.items():
  if f['transform']=='log':ck(family+' positive log domain',(matrix[f['columns']]>0).all().all())
  elif f['transform']=='log1p':ck(family+' nonnegative domain',(matrix[f['columns']]>=0).all().all())
 ck('equal family weights sum1',np.isclose(sum(f['weight'] for f in families.values()),1))
 rows=[];sp=matrix.loc[matrix.index.str.startswith('SP:')];chi=matrix.loc[matrix.index.str.startswith('CHI:')]
 for col in cols:
  for city,d in [('SP',sp),('CHI',chi)]:
   v=d[col];rows.append({'city':city,'feature':col,'n':len(v),'missing':int(v.isna().sum()),'min':v.min(),'p25':v.quantile(.25),'median':v.median(),'p75':v.quantile(.75),'max':v.max(),'unique_values':v.nunique(),'outside_SP_observed_range':int(((v<sp[col].min())|(v>sp[col].max())).sum())})
 pd.DataFrame(rows).to_csv(OUT/'raw_domain_review.csv',index=False)
 # Raw correlations describe shared information; no distances or neighbor selection.
 correlations=[]
 for city,d in [('SP',data.loc[sp.index]),('CHI',data.loc[chi.index])]:
  for a,b in [('net_grid_height_land','volume_density_land'),('footprint_coverage_land','net_grid_height_land'),('footprint_coverage_land','volume_density_land')]:
   correlations.append({'city':city,'feature_a':a,'feature_b':b,'spearman_rho':d[[a,b]].corr(method='spearman').iloc[0,1]})
 pd.DataFrame(correlations).to_csv(OUT/'built_form_correlations.csv',index=False)
 matrix.to_csv(OUT/'proposed_matrix.csv');matrix.to_parquet(OUT/'proposed_matrix.parquet')
 contract={'status':'technical_readiness_passed_scope_approval_pending','fit_authorized':False,'families':families,'cohort':{'SP':96,'CHI':77,'target':'SP:10'},'fit_reference':'harmonized SP only; apply unchanged to CHI','scaling':'SP median/IQR with documented SD fallback','family_calibration':'SP positive-pair median distances','excluded':['M2','M3','M4','M7','B2','B3','U1','U2'],'excluded_reason':'M2/M3/M4 physical semantics unaccepted; M7/B2/B3 unavailable common fiscal definitions; U1 incompatible use domain; U2 extended-only','qualifications':['mapped roads regardless of access; source completeness differs','local hydrography coverage/vintage differ','GHSL height2018 and volume2020 use related estimates','population SP2022/CHI2020','bus-only service dates one week apart; frequency vs scheduled supply'],'required_sensitivities':['core_without_BV','volume_instead_of_height_same_BV_budget','gross_denominators_for_B1_BV','M6_omission','bus800m_and_weekend','family_weight_and_city_balanced_fit'],'source_matrix':str(path.relative_to(ROOT)),'source_sha256':sha(path),'no_ranking_inspected':True}
 (OUT/'proposed_contract.json').write_text(json.dumps(contract,indent=2))
 result={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'fit_performed':False,'scope_approval_pending':True}
 (OUT/'readiness_checks.json').write_text(json.dumps(result,indent=2))
 assert not result['failed'], 'Readiness gate failed'
 (OUT/'progress.json').write_text(json.dumps({'status':'bounded_H4_readiness_review_complete','next':'approve reduced six-family scope or reopen physical junction/block work before H5','running_jobs':[],'fit_performed':False},indent=2))
 print(json.dumps({'units':len(matrix),'columns':len(cols),'checks_passed':result['passed'],'fit_performed':False}))
if __name__=='__main__':main()
