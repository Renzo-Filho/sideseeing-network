"""Publish H1–H3 candidate companions, preserving all model acceptance gates."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';OUT=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3'

def main():
 rows=[];receipts=[]
 def csv(path):
  receipts.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()});return pd.read_csv(path)
 def add(unit,family,feature,value,units,source,period,status='candidate_H4_review',numerator=None,denominator=None,reason=None):
  rows.append(dict(unit_id=unit,city=unit.split(':')[0],family=family,feature=feature,value=value,units=units,numerator=numerator,denominator=denominator,source=source,period=period,status=status,missing_reason=reason,strict_cross_city_accepted=False))
 roads=csv(OUT/'roads/paired_road_candidates.csv')
 for z in roads.itertuples():
  source='Overture2026-08-19 paired physical mapped streets; legal access not inferred'
  add(z.unit_id,'M1','mapped_street_density_km_km2',z.M1_mapped_street_density_km_km2,'km/km2',source,'2026 release',numerator=z.road_length_m/1000,denominator=z.gross_area_m2/1e6)
  for c in roads.filter(like='M6_share_').columns:add(z.unit_id,'M6',c,getattr(z,c),'fraction',source,'2026 release',numerator=getattr(z,c)*z.road_length_m,denominator=z.road_length_m)
  add(z.unit_id,'M2','connector_candidate_density_km2',z.M2_connector_candidate_density_km2,'candidates/km2',source,'2026 release','withheld_physical_junction_gate',numerator=z.connector_candidates,denominator=z.gross_area_m2/1e6)
  for field in ['log_area','compactness','elongation']:
   for stat in ['median','iqr']:
    c='enclosure_'+field+'_'+stat;val=getattr(z,c)
    add(z.unit_id,'M3' if field=='log_area' else 'M4',c,val,'ln(m2)' if field=='log_area' else 'dimensionless',source,'2026 release','withheld_physical_block_gate',reason='No eligible enclosure' if pd.isna(val) else None)
 footprint=csv(OUT/'footprints/footprint_candidates.csv')
 for z in footprint.itertuples():
  for support in ['land','gross']:
   num=getattr(z,'footprint_union_'+support+'_m2');den=getattr(z,support+'_area_m2')
   add(z.unit_id,'B1','footprint_coverage_'+support,num/den,'fraction','Overture2026-08-19 exact footprint union; local hydro masks','2026 release',numerator=num,denominator=den)
 ghsl=csv(OUT/'ghsl/ghsl_attributes.csv')
 for z in ghsl.itertuples():
  key={'ANBH':'net_grid_height','AGBH':'gross_grid_height','VOLUME':'volume_density'}[z.product]+'_'+z.support
  add(z.unit_id,'BV',key,z.value,'m3/m2' if z.product=='VOLUME' else 'm','GHSL R2023A V1-0 native100m',str(z.epoch),status='candidate_H4_review' if z.product in ['ANBH','VOLUME'] else 'diagnostic_only',numerator=z.observed_allocated_mass_m3 if z.product=='VOLUME' else z.value*z.valid_area_m2,denominator=z.support_area_m2 if z.product=='VOLUME' else z.valid_area_m2,reason='Missing raster support' if pd.isna(z.value) else None)
 pop=csv(OUT/'functional/population_candidates.csv');bus=csv(OUT/'functional/bus_candidates.csv')
 for z in pop.itertuples():add(z.unit_id,'U3','population_density_gross_km2',z.U3_population_density_km2,'people/km2','Census whole-sector/block area allocation',str(z.population_year),numerator=z.population,denominator=z.gross_area_m2/1e6)
 for z in bus.itertuples():add(z.unit_id,'U4',f'bus_supply_{z.window}_{z.radius_m}m',z.U4_bus_supply,'expected departures per resident per2h',z.operator,z.service_date,numerator=z.weighted_departures,denominator=z.population_weight)
 sp_path=A/'results/SP/tables/attributes_long.parquet';receipts.append({'path':str(sp_path.relative_to(ROOT)),'sha256':hashlib.file_digest(sp_path.open('rb'),'sha256').hexdigest()});sp=pd.read_parquet(sp_path)
 for z in sp.loc[sp.feature_name.eq('formal_job_density_area_first_km2')].itertuples():add('SP:'+z.district_id,'U2','jobs_density_area_baseline',z.value,'jobs/km2','RAIS CEP area-first; 508844 jobs unlocated','2022','extended_only_universe_gate',z.numerator,z.denominator)
 chi=csv(A/'results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.csv')
 for z in chi.itertuples():add(z.unit_id,'U2','jobs_density_area_baseline',z.jobs_density_2022_gross_km2,'jobs/km2','LODES WAC all jobs whole-block allocation','2022','extended_only_universe_gate',z.jobs_allocated,z.gross_area_m2/1e6)
 emp=csv(A/'results/Chicago/chi_employment_sensitivity_2026_09_22_v2/tables/district_job_sensitivity.csv')
 for z in emp.itertuples():add(z.unit_id,'U2','jobs_density_'+z.scenario,z.jobs_density_km2,'jobs/km2','LODES CMAP business-support allocation with recorded fallback','jobs2022/use2023','city_specific_sensitivity',z.jobs_allocated,z.gross_area_km2)
 ids=sorted(set(pop.unit_id))
 for unit in ids:add(unit,'U1','common_land_use_entropy',None,'normalized entropy','CMAP vs SP cadastral domains unresolved','mixed','withheld_common_use_gate',reason='No accepted common ontology and observed-use weighting/domain')
 long=pd.DataFrame(rows)
 expected={f'SP:{i:02}' for i in range(1,97)}|{f'CHI:{i:02}' for i in range(1,78)}
 if set(long.unit_id)!=expected or long.duplicated(['unit_id','feature']).any():raise ValueError('Candidate key contract failed')
 nonnull=long.value.dropna();assert np.isfinite(nonnull).all()
 tables=OUT/'tables';tables.mkdir(exist_ok=True)
 long.to_csv(tables/'candidate_attributes_long.csv',index=False);long.to_parquet(tables/'candidate_attributes_long.parquet',index=False)
 wide=long.pivot(index='unit_id',columns='feature',values='value');wide.to_csv(tables/'candidate_attributes_wide.csv');wide.to_parquet(tables/'candidate_attributes_wide.parquet')
 dictionary=long[['family','feature','units','status']].drop_duplicates().sort_values(['family','feature']);dictionary.to_csv(tables/'candidate_dictionary.csv',index=False)
 for city,label in [('SP','SP'),('CHI','Chicago')]:
  dest=A/'results'/label/'harmonized_candidates_2026_09_22';dest.mkdir(exist_ok=True)
  long.loc[long.city.eq(city)].to_parquet(dest/'candidate_attributes_long.parquet',index=False)
  wide.loc[wide.index.str.startswith(city+':')].to_csv(dest/'candidate_attributes_wide.csv')
  (dest/'README.md').write_text(f'# {label} harmonized candidate companion\n\nH1–H3 candidate attributes; no accepted common matrix or fitted model. Original releases preserved. Definitions, gates and receipts: `analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/`. U1 is withheld, M2/M3/M4 remain diagnostic, U2 extended-only. SP bus supply explicitly filters route_type=3.\n')
 ledger={f:'candidate_H4_review' for f in ['M1','M6','B1','BV','U3','U4']};ledger.update({'M2':'withheld: connector graph does not establish consolidated physical junctions','M3':'withheld: planar enclosures are not accepted physical blocks','M4':'withheld: same enclosure gate as M3','M7':'excluded_by_approved_plan','B2':'excluded_by_approved_plan','B3':'excluded_by_approved_plan','U1':'withheld: use ontology/domain differs','U2':'extended-only: RAIS/LODES universe equivalence unresolved'})
 (OUT/'family_acceptance_ledger.json').write_text(json.dumps(ledger,indent=2))
 (OUT/'assembly_receipts.json').write_text(json.dumps(receipts,indent=2))
 # H4 decisions deliberately remain open; construction completion is not model acceptance.
 (OUT/'progress.json').write_text(json.dumps({'status':'H1_H3_candidate_construction_complete_with_open_semantic_gates','units':len(wide),'long_rows':len(long),'features':len(wide.columns),'H1':'paired arithmetic pilots complete; M2/M3/M4 semantic gates fail readiness','H2':'full paired candidate physical tables complete','H3':'paired U3 and corrected bus-only U4; U2 sensitivity complete; U1 withheld','H4':'pending review of failed gates and reduced common-set scope','H5':'not started','H6':'not started','strict_cross_city_accepted':False,'running_jobs':[]},indent=2))
 print('Assembled',len(wide),'units',len(long),'long rows',len(wide.columns),'features',flush=True)
if __name__=='__main__':main()
