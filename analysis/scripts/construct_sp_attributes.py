"""Checkpointed N10 attribute construction, pilots before municipal release. No model fit."""
import argparse,json,hashlib,fcntl,time
import pandas as pd,numpy as np,geopandas as gpd,shapely,pyogrio
from sp_attributes import core as C,tabular,spatial

def log(s):print(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),s,flush=True)
def validate(df,codes):
 assert set(df.district_id)==set(codes) and not df.duplicated(['district_id','feature_name']).any()
 assert set(df.family_id)==set(C.CFG['active_families'])
 assert np.isfinite(df.value.dropna()).all()
 assert df.loc[df.unit.eq('fraction'),'value'].dropna().between(-1e-9,1+1e-9).all()
 assert df.loc[df.unit.eq('normalized entropy'),'value'].dropna().between(0,1+1e-9).all()
 assert df.loc[df.denominator.notna(),'denominator'].gt(0).all()
 assert df.loc[df.coverage_fraction.notna(),'coverage_fraction'].between(0,1+1e-9).all()
 assert df.loc[df.primary_feature,'value'].notna().all()
 for kind in ['count','land_area']:
  shares=df.loc[df.feature_name.str.startswith('land_use_'+kind+'_share_')].groupby('district_id').value.sum();assert np.allclose(shares,1)
 shares=df.loc[df.feature_name.str.startswith('street_class_model_share_')].groupby('district_id').value.sum();assert np.allclose(shares,1)
 return {'districts':len(codes),'rows':len(df),'features':df.feature_name.nunique(),'primary_columns':df.loc[df.primary_feature].feature_name.nunique(),'families':13,'checks':'identities, full family coverage, finite values, fraction/entropy bounds, positive denominators, primary completeness, U1/M6 composition sums','passed':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['pilots','all','both'],default='both');a=p.parse_args()
 C.OUT.mkdir(parents=True,exist_ok=True);lock=(C.OUT/'runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert C.CFG['attribute_construction_authorized'] and not C.CFG['model_fitting_authorized']
 deps=[*sorted(C.BASE.glob('N*/checkpoint.json')),C.ROOT/C.CFG['m6_overlay'],C.ROOT/C.CFG['m2_overlay'],C.ROOT/C.CFG['u2_directory']/'artifact_inventory.json',C.OLD/'02_parcels_tax/parcel_identity_status.parquet']
 inputs={str(p.relative_to(C.ROOT)):C.sha(p) for p in deps};fingerprint=hashlib.sha256(json.dumps([inputs,C.CFG],sort_keys=True).encode()).hexdigest();manifest=C.OUT/'manifest.json'
 if manifest.exists():assert json.loads(manifest.read_text())['input_fingerprint']==fingerprint,'Inputs changed: new run ID required'
 else:
  # Verify actual baseline outputs against their frozen checkpoints, not just checkpoint filenames.
  for f in C.BASE.glob('N*/checkpoint.json'):
   q=json.loads(f.read_text());assert all(C.sha(C.BASE/k)==v for k,v in q['outputs'].items()),'Prepared source hash mismatch'
  C.dump(manifest,{'config':C.CFG,'input_fingerprint':fingerprint,'inputs':inputs,'prepared_inputs_verified':True,'attribute_construction':True,'model_fitted':False})
 progress={'run_id':C.CFG['run_id'],'attribute_construction_started':True,'model_fitted':False,'phase':'preparing_parcel_metrics'};C.dump(C.OUT/'progress.json',progress)
 log('Preparing canonical parcel areas');tabular.prepare();allcodes=list(C.districts().district_id)
 signature=hashlib.sha256((fingerprint+C.sha(spatial.__file__)+C.sha(C.__file__)).encode()).hexdigest()
 def cached(fn,code):
  path=C.OUT/'parts'/fn/code;path.mkdir(parents=True,exist_ok=True);cp=path/'checkpoint.json';file=path/'features.parquet'
  if cp.exists():
   old=json.loads(cp.read_text())
   if old['signature']==signature and C.sha(file)==old['sha256']:return pd.read_parquet(file)
  log(fn+' '+code+' starting');result=getattr(spatial,fn)(code);result.to_parquet(file,index=False);C.dump(cp,{'signature':signature,'sha256':C.sha(file)});log(fn+' '+code+' done');return result
 phases=['pilots','all'] if a.phase=='both' else [a.phase]
 for phase in phases:
  if phase=='all':assert (C.OUT/'pilot_validation.json').exists(),'Run pilot construction first'
  codes=C.CFG['pilots'] if phase=='pilots' else allcodes;progress['phase']=phase;C.dump(C.OUT/'progress.json',progress)
  log(phase+' tabular attributes');frames=[tabular.run(codes)]
  for code in codes:
   progress['district_id']=code;C.dump(C.OUT/'progress.json',progress)
   frames.extend([cached('building_coverage',code),cached('transit_access',code)])
  df=pd.concat(frames,ignore_index=True);qa=validate(df,codes)
  if phase=='pilots':
   df.to_parquet(C.OUT/'pilot_attributes_long.parquet',index=False);C.dump(C.OUT/'pilot_validation.json',qa);log('Pilot feature invariants passed');continue
  df.to_parquet(C.OUT/'attributes_long.parquet',index=False);df.to_csv(C.OUT/'attributes_long.csv',index=False)
  names=C.districts()[['district_id','nm_distrito_municipal']].rename(columns={'nm_distrito_municipal':'district_name'})
  wide=df.pivot(index='district_id',columns='feature_name',values='value').reset_index().merge(names,on='district_id',validate='one_to_one');wide.to_parquet(C.OUT/'attributes_wide.parquet',index=False);wide.to_csv(C.OUT/'attributes_wide.csv',index=False)
  primary=df.loc[df.primary_feature].pivot(index='district_id',columns='feature_name',values='value').reset_index().merge(names,on='district_id');primary.to_csv(C.OUT/'attributes_primary.csv',index=False)
  dictionary=df.drop_duplicates('feature_name')[['family_id','feature_name','unit','primary_feature','method','observation_period','coverage_definition']];dictionary.to_csv(C.OUT/'attribute_dictionary.csv',index=False)
  geo=C.districts()[['district_id','geometry']].merge(wide,on='district_id',validate='one_to_one');pyogrio.write_dataframe(geo,C.OUT/'sao_paulo_district_attributes.gpkg',layer='district_attributes',driver='GPKG')
  # Reopen the delivered spatial artifact and reconcile citywide extensive numerators.
  export=pyogrio.read_dataframe(C.OUT/'sao_paulo_district_attributes.gpkg');assert len(export)==96 and export.crs.to_epsg()==31983 and export.is_valid.all()
  primaryrows=df.loc[df.primary_feature].set_index('feature_name')
  totals={name:float(df.loc[df.feature_name.eq(name),'numerator'].sum()) for name in ['cadastral_floor_area_density','formal_job_density_area_first_km2','population_density_km2','intersection_density_proxy_5m_km2']}
  assert np.isclose(totals['cadastral_floor_area_density'],581313100) and np.isclose(totals['formal_job_density_area_first_km2'],4878630) and np.isclose(totals['population_density_km2'],11446054.473149512) and totals['intersection_density_proxy_5m_km2']==106625
  streets=gpd.read_parquet(C.BASE/'N04/edges.parquet');streets=streets.loc[streets.canonical_edge]
  # Polygon intersection nodes self-retraced lines. Normalize each source edge
  # independently so the independent audit uses that same geometric measure;
  # retain separate carriageways and do not dissolve different source edges.
  non_simple=~shapely.is_simple(streets.geometry.values)
  raw_length=float(streets.length.sum())
  streets.loc[non_simple,'geometry']=[shapely.union_all([g]) for g in streets.geometry.values[non_simple]]
  normalized_loss=raw_length-float(streets.length.sum())
  city=shapely.union_all(C.districts().geometry.values);shapely.prepare(city)
  inside=shapely.covers(city,streets.geometry.values);boundary=(~inside)&shapely.intersects(city,streets.geometry.values)
  expected_length=float(shapely.length(streets.geometry.values[inside]).sum()+shapely.length(shapely.intersection(streets.geometry.values[boundary],city)).sum())
  measured_length=float(df.loc[df.feature_name.eq('street_density_km_km2'),'numerator'].sum()*1000)
  assert np.isclose(expected_length,measured_length,rtol=1e-9,atol=.01),(expected_length,measured_length)
  qa['street_length_conservation']={'independent_city_clip_m':expected_length,'district_sum_m':measured_length,'source_self_retrace_removed_m':normalized_loss,'normalization':'union within each non-simple source edge; separate source edges retained'}
  qa['citywide_numerators']=totals;qa['source_jobs_unlocated']=508844;qa['no_model_fitted']=True;C.dump(C.OUT/'validation.json',qa)
  progress.update(phase='complete',district_id=None,completed_families=C.CFG['active_families']);C.dump(C.OUT/'progress.json',progress);log('Municipal attribute release complete')
 if a.phase=='pilots':progress['phase']='pilots_complete';C.dump(C.OUT/'progress.json',progress)
if __name__=='__main__':main()
