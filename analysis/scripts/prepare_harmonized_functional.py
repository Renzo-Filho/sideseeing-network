"""Paired U3/U4 companions from frozen support; explicit U1/U2 semantic gates."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,geopandas as gpd
from harmonization.functional import supply
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';OUT=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/functional'
SP=A/'work/prepared/SP/sp_prep_2026_09_10_v3';CHI=A/'work/prepared/Chicago/chi_functional_2026_09_16_v2';INTER=A/'work/runs/sp_attributes_2026_09_11_v1/intermediates'

def main():
 OUT.mkdir(parents=True,exist_ok=True);receipts=[];checks=[];pops=[];buses=[]
 def read(path,geo=False):
  receipts.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()})
  return gpd.read_parquet(path) if geo else pd.read_parquet(path)
 def check(label,ok):checks.append({'check':label,'passed':bool(ok)})
 d=read(SP/'N02/districts.parquet',True);alloc=read(SP/'N07/census_district_allocation.parquet');sectors=read(SP/'N07/census_sectors.parquet',True)
 totals=alloc.groupby('district_id').population_allocated.sum();weights=alloc.groupby('sector_id').allocation_weight.sum()
 check('SP no sector overallocated',(weights<=1+1e-8).all())
 for z in d.itertuples():
  pop=float(totals.loc[z.district_id]);pops.append({'unit_id':'SP:'+str(z.district_id).zfill(2),'population':pop,'gross_area_m2':z.geometry.area,'U3_population_density_km2':pop/(z.geometry.area/1e6),'population_year':2022})
 source_sp=float(sectors.qt_populacao.sum());outside_sp=source_sp-float(totals.sum())
 check('SP source mass retained',outside_sp>=-1e-6)
 cf=read(A/'results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.parquet');parts=read(CHI/'block_district_pieces.parquet');blocks=read(CHI/'blocks.parquet')
 ct=parts.groupby('unit_id').population_allocated.sum();cw=parts.groupby('GEOID20').weight.sum()
 check('CHI no block overallocated',(cw<=1+1e-8).all())
 for z in cf.itertuples():
  pop=float(ct.loc[z.unit_id]);check(z.unit_id+' population reconstruction',np.isclose(pop,z.population_allocated,rtol=1e-10))
  pops.append({'unit_id':z.unit_id,'population':pop,'gross_area_m2':z.gross_area_m2,'U3_population_density_km2':pop/(z.gross_area_m2/1e6),'population_year':2020})
 source_chi=float(blocks.POP20.sum());outside_chi=source_chi-float(ct.sum())
 check('CHI source mass retained',outside_chi>=-1e-6)
 sp_bus_path=OUT/'sp_bus_only_recomputed.csv'
 receipts.append({'path':str(sp_bus_path.relative_to(ROOT)),'sha256':hashlib.file_digest(sp_bus_path.open('rb'),'sha256').hexdigest()})
 spbus=pd.read_csv(sp_bus_path)
 for z in spbus.itertuples():
  check(z.unit_id+' '+z.window+str(z.radius_m)+' population',np.isclose(z.population_weight,totals.loc[z.unit_id.split(':')[1]],rtol=1e-9,atol=.01))
  check(z.unit_id+' '+z.window+str(z.radius_m)+' supply ratio',np.isclose(z.U4_bus_supply,z.weighted_departures/z.population_weight,rtol=1e-10))
  buses.append({k:getattr(z,k) for k in ['unit_id','window','radius_m','population_weight','weighted_departures','U4_bus_supply','service_date','population_year','operator']})
 cb=read(A/'results/Chicago/chi_functional_2026_09_16_v2/tables/bus_service_access.parquet')
 for z in cb.itertuples():
  check(z.unit_id+' '+z.window+str(z.radius_m)+' bus population',np.isclose(z.population_weight,ct.loc[z.unit_id],rtol=1e-9,atol=.01))
  check(z.unit_id+' '+z.window+str(z.radius_m)+' bus ratio',np.isclose(z.expected_departures_per_resident,z.weighted_departures/z.population_weight,rtol=1e-10))
  buses.append({'unit_id':z.unit_id,'window':z.window,'radius_m':int(z.radius_m),'population_weight':z.population_weight,'weighted_departures':z.weighted_departures,'U4_bus_supply':z.expected_departures_per_resident,'service_date':{'weekday_am':'2026-09-16','saturday_am':'2026-09-19','sunday_am':'2026-09-20'}[z.window],'population_year':2020,'operator':'CTA'})
 # Audit raw SP bus-only/pickup scope before reusing service products.
 raw=A/'data/SP/Socioeconomico/f-6gy-sptrans-latest'
 for name in ['routes','stop_times']:
  p=raw/(name+'.txt');receipts.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
 routes=pd.read_csv(raw/'routes.txt',dtype=str);st=pd.read_csv(raw/'stop_times.txt',dtype=str,keep_default_na=False)
 bus_ids=set(routes.loc[routes.route_type.eq('3'),'route_id'])
 check('SP bus-only filtered route universe',len(bus_ids)>0 and len(spbus)==576)
 pickup=st.pickup_type if 'pickup_type' in st else pd.Series('',index=st.index)
 check('SP no prohibited pickup rows included',not pickup.eq('1').any())
 # Recompute primary supply with shared implementation on all Chicago pilot points,
 # and full SP pilot points against the new bus-only companion.
 for city,pilots,base in [('SP',['10','30','35'],SP/'N08'),('CHI',['24','28','30','32','76'],CHI)]:
  stops=read(base/'stops.parquet',True);svc=read(base/'stop_route_service.parquet')
  svc=svc.loc[svc.window.eq('weekday_am')].copy()
  if city=='SP':
   svc=svc.loc[svc.route_id.isin(bus_ids)].rename(columns={'expected_departures':'departures'})
   check('SP service contains only bus routes',set(svc.route_id)<=bus_ids)
  for did in pilots:
   points=read(INTER/f'population_points_{did}.parquet',True) if city=='SP' else read(CHI/'population_points'/f'CHI_{did}.parquet',True)
   vals=np.concatenate([supply(points.iloc[i:i+500],stops,svc,400) for i in range(0,len(points),500)])
   if city=='SP':
    old=spbus.loc[spbus.unit_id.eq('SP:'+did)&spbus.window.eq('weekday_am')&spbus.radius_m.eq(400)].iloc[0]
    check(city+did+' independent bus-only pilot aggregate',np.isclose(float(vals@points.population_weight.to_numpy()),old.weighted_departures,rtol=1e-10))
   else:
    old=cb.loc[cb.unit_id.eq('CHI:'+did)&cb.window.eq('weekday_am')&cb.radius_m.eq(400)].iloc[0]
    check(city+did+' independent pilot aggregate',np.isclose(float(vals@points.population_weight.to_numpy()),old.weighted_departures,rtol=1e-10))
 pd.DataFrame(pops).to_csv(OUT/'population_candidates.csv',index=False)
 bus=pd.DataFrame(buses);bus.to_csv(OUT/'bus_candidates.csv',index=False)
 check('173 population rows',len(pops)==173)
 check('1038 unique bus scenarios',len(bus)==173*6 and not bus.duplicated(['unit_id','window','radius_m']).any())
 wide=bus.pivot(index=['unit_id','window'],columns='radius_m',values='U4_bus_supply');check('bus radius monotonicity',(wide[800]+1e-9>=wide[400]).all())
 (OUT/'population_mass.json').write_text(json.dumps({'SP':{'source_population':source_sp,'inside':float(totals.sum()),'outside':outside_sp},'CHI':{'whole_intersecting_block_population':source_chi,'inside':float(ct.sum()),'outside':outside_chi}},indent=2))
 (OUT/'checks.json').write_text(json.dumps(checks,indent=2));(OUT/'source_receipts.json').write_text(json.dumps(receipts,indent=2))
 (OUT/'semantic_gates.json').write_text(json.dumps({'U3':'candidate common gross-area density; census2020 vs2022 retained; source-area allocation uncertainty','U4':'candidate comparable bus supply; valid local weekdays/weekends one week apart; SP frequency estimates vs CTA scheduled departures; no pedestrian routing or rail','U1':'withheld: CMAP polygon-area domain and SP cadastral-use entities do not yet share observed-use domain/ontology; no forced crosswalk','U2':'extended diagnostics only: RAIS/LODES coverage not equivalent; completed Chicago business allocation sensitivity must not imply universe equivalence','strict_cross_city_accepted':False},indent=2))
 if not all(c['passed'] for c in checks):raise RuntimeError('Functional checks failed; inspect checks.json')
 print('Functional complete',len(pops),len(bus),'checks',len(checks),flush=True)
if __name__=='__main__':main()
