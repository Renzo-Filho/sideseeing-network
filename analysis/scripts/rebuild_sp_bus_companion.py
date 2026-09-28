"""Rebuild SP bus-only supply, preserving the historic multimodal-contaminated release."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,geopandas as gpd
from harmonization.functional import supply_windows
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'analysis';BASE=A/'work/prepared/SP/sp_prep_2026_09_10_v3/N08';INTER=A/'work/runs/sp_attributes_2026_09_11_v1/intermediates';OUT=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/functional';WORK=A/'work/runs/sp_chicago_harmonization_2026_09_22/sp_bus_only'

def main():
 WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 routepath=A/'data/SP/Socioeconomico/f-6gy-sptrans-latest/routes.txt';routes=pd.read_csv(routepath,dtype=str)
 service=pd.read_parquet(BASE/'stop_route_service.parquet');stops=gpd.read_parquet(BASE/'stops.parquet')
 bus_ids=set(routes.loc[routes.route_type.eq('3'),'route_id']);removed=service.loc[~service.route_id.isin(bus_ids)]
 service=service.loc[service.route_id.isin(bus_ids)].rename(columns={'expected_departures':'departures'})
 signature=hashlib.sha256(''.join(hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in [routepath,BASE/'stop_route_service.parquet',BASE/'stops.parquet',Path(__file__),A/'scripts/harmonization/functional.py']).encode()).hexdigest()
 rows=[];checks=[];receipts=[]
 for did in [f'{i:02}' for i in range(1,97)]:
  pp=INTER/f'population_points_{did}.parquet';digest=hashlib.file_digest(pp.open('rb'),'sha256').hexdigest();receipts.append({'path':str(pp.relative_to(ROOT)),'sha256':digest})
  target=WORK/f'{did}.json'
  if target.exists():
   saved=json.loads(target.read_text())
   if saved['signature']!=signature or saved['point_sha256']!=digest:raise ValueError('Changed resume inputs')
   rows.extend(saved['rows']);checks.extend(saved['checks']);continue
  points=gpd.read_parquet(pp);pop=float(points.population_weight.sum());nums={};reached={}
  for start in range(0,len(points),500):
   p=points.iloc[start:start+500];values=supply_windows(p,stops,service)
   for key,arr in values.items():
    nums[key]=nums.get(key,0.)+float(arr@p.population_weight.to_numpy());reached[key]=reached.get(key,0.)+float(p.loc[arr>0,'population_weight'].sum())
   for win in service.window.unique():
    if not np.all(values[(win,800)]+1e-10>=values[(win,400)]):raise ValueError('Nonmonotone bus catchment')
  old=pd.read_parquet(INTER/f'point_service_{did}.parquet');local=[];ck=[]
  for (window,radius),num in nums.items():
   part=old.loc[old.window.eq(window)&old.radius_m.eq(radius)];prev=float((part.population_weight*part.expected_route_direction_supply).sum()/part.population_weight.sum())
   val=num/pop;row={'unit_id':'SP:'+did,'window':window,'radius_m':radius,'population_weight':pop,'weighted_departures':num,'U4_bus_supply':val,'legacy_unfiltered_supply':prev,'removed_nonbus_supply':prev-val,'service_date':{'weekday_am':'2026-09-09','saturday_am':'2026-09-12','sunday_am':'2026-09-13'}[window],'population_year':2022,'operator':'SP feed route_type=3 only','reach_fraction':reached[(window,radius)]/pop}
   local.append(row);ck.append({'check':'SP:'+did+' '+window+str(radius)+' bus_only_not_greater_than_legacy','passed':bool(val<=prev+1e-7)})
  target.write_text(json.dumps({'signature':signature,'point_sha256':digest,'rows':local,'checks':ck},indent=2));rows.extend(local);checks.extend(ck)
  print('SP bus-only',did,flush=True)
 pd.DataFrame(rows).to_csv(OUT/'sp_bus_only_recomputed.csv',index=False)
 (OUT/'sp_bus_only_checks.json').write_text(json.dumps(checks,indent=2));(OUT/'sp_bus_only_receipts.json').write_text(json.dumps(receipts,indent=2))
 (OUT/'sp_bus_only_scope.json').write_text(json.dumps({'signature':signature,'route_types':routes.route_type.value_counts().to_dict(),'removed_service_rows':len(removed),'removed_expected_stop_calls':removed.groupby('window').expected_departures.sum().to_dict(),'source_legacy_unchanged':True},indent=2))
 if not all(x['passed'] for x in checks):raise RuntimeError('Bus-only checks failed')
 print('SP bus-only complete',len(rows),flush=True)
if __name__=='__main__':main()
