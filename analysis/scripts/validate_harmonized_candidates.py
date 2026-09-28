"""Independent table-level audit of H1–H3 candidates; no family acceptance."""
from pathlib import Path
import json,zipfile
import rasterio
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3'

def main():
 checks=[]
 def ck(name,passed):checks.append({'check':name,'passed':bool(passed)})
 expected={f'SP:{i:02}' for i in range(1,97)}|{f'CHI:{i:02}' for i in range(1,78)}
 r=pd.read_csv(O/'roads/paired_road_candidates.csv');b=pd.read_csv(O/'footprints/footprint_candidates.csv');g=pd.read_csv(O/'ghsl/ghsl_attributes.csv');p=pd.read_csv(O/'functional/population_candidates.csv');u=pd.read_csv(O/'functional/bus_candidates.csv')
 for name,frame in [('roads',r),('footprints',b),('population',p)]:ck(name+' exact unique cohort',set(frame.unit_id)==expected and frame.unit_id.is_unique)
 ck('road density numerator',np.allclose(r.M1_mapped_street_density_km_km2,r.road_length_m*1000/r.gross_area_m2))
 ck('class composition',np.allclose(r.filter(like='M6_share_').sum(axis=1),1) and (r.filter(like='M6_share_')>=0).all().all())
 ck('intersection diagnostic formula',np.allclose(r.M2_connector_candidate_density_km2,r.connector_candidates*1e6/r.gross_area_m2))
 for support in ['land','gross']:
  ck('footprint '+support+' ratio',np.allclose(b['B1_coverage_'+support],b['footprint_union_'+support+'_m2']/b[support+'_area_m2']))
  ck('footprint '+support+' bounded',b['B1_coverage_'+support].between(0,1+1e-9).all())
 ck('water decomposition',np.allclose(b.land_area_m2+b.water_area_m2,b.gross_area_m2))
 ck('GHSL unique173x6',len(g)==1038 and set(g.unit_id)==expected and not g.duplicated(['unit_id','product','support']).any())
 ck('GHSL support balance',np.allclose(g.valid_area_m2+g.nodata_area_m2+g.outside_raster_area_m2,g.support_area_m2,rtol=1e-8,atol=.01))
 ck('GHSL coverage ratio',np.allclose(g.valid_area_fraction,g.valid_area_m2/g.support_area_m2))
 vol=g.loc[g['product']=='VOLUME'];observed=vol.dropna(subset=['value'])
 ck('volume density',np.allclose(observed.value,observed.observed_allocated_mass_m3/observed.support_area_m2))
 ck('population density',np.allclose(p.U3_population_density_km2,p.population*1e6/p.gross_area_m2))
 ck('bus ratios',np.allclose(u.U4_bus_supply,u.weighted_departures/u.population_weight))
 ck('bus cohorts',len(u)==1038 and set(u.unit_id)==expected and not u.duplicated(['unit_id','window','radius_m']).any())
 long=pd.read_parquet(O/'tables/candidate_attributes_long.parquet');wide=pd.read_parquet(O/'tables/candidate_attributes_wide.parquet')
 ck('long unique keys',not long.duplicated(['unit_id','feature']).any())
 rebuilt=long.pivot(index='unit_id',columns='feature',values='value')
 ck('wide long replay',wide.equals(rebuilt))
 ck('no premature acceptance',not long.strict_cross_city_accepted.any())
 ck('U1 explicit missing',long.loc[long.family.eq('U1'),'value'].isna().all() and long.loc[long.family.eq('U1'),'missing_reason'].notna().all())
 ck('M2-M4 withheld',long.loc[long.family.isin(['M2','M3','M4']),'status'].str.startswith('withheld').all())
 ck('excluded fiscal families absent',not long.family.isin(['M7','B2','B3']).any())
 ledger=json.loads((O/'family_acceptance_ledger.json').read_text());ck('U2 not promoted',ledger['U2'].startswith('extended-only'))
 for name in ['ghsl','footprints','functional']:
  q=json.loads((O/name/'checks.json').read_text());ck(name+' all stage checks pass',all(v['passed'] for v in q))
 recovery=json.loads((O/'ghsl/source_cell_recovery.json').read_text())
 for i,row in enumerate(recovery):
  archive=ROOT/row['source_archive']
  with zipfile.ZipFile(archive) as package:member=next(n for n in package.namelist() if n.endswith('.tif'))
  with rasterio.open('/vsizip/'+str(archive)+'/'+member) as ds:
   rr,cc=ds.index(row['x'],row['y']);raw=ds.read(1,window=rasterio.windows.Window(cc,rr,1,1),masked=True)
   ck('source cell recovery '+str(i),not np.ma.getmaskarray(raw)[0,0] and float(raw[0,0])==row['source_value'])
 summary={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'strict_cross_city_accepted':False,'checks':checks}
 (O/'independent_table_checks.json').write_text(json.dumps(summary,indent=2))
 if summary['failed']:raise RuntimeError('Candidate audit failed')
 print(json.dumps({k:v for k,v in summary.items() if k!='checks'}))
if __name__=='__main__':main()
