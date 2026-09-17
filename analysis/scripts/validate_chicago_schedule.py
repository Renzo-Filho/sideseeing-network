from pathlib import Path
import datetime as dt,json
import pandas as pd
r=Path('analysis/data/Chicago/google_transit')
load=lambda n:pd.read_csv(r/(n+'.txt'),dtype=str,keep_default_na=False)
c=load('calendar');ex=load('calendar_dates');t=load('trips');routes=load('routes')
bus=set(routes.loc[routes.route_type.eq('3'),'route_id']);t=t.loc[t.route_id.isin(bus)]
windows=[('weekday_am','2026-09-16',7*3600,9*3600),('saturday_am','2026-09-19',9*3600,11*3600),('sunday_am','2026-09-20',9*3600,11*3600)]
sets=[];counts={k:0 for k,_,_,_ in windows}
for label,stamp,lo,hi in windows:
 for back in [0,1]:
  date=dt.date.fromisoformat(stamp)-dt.timedelta(days=back);ds=date.strftime('%Y%m%d');day=date.strftime('%A').lower()
  active={row.service_id for row in c.itertuples() if row.start_date<=ds<=row.end_date and getattr(row,day)=='1'}
  for row in ex.itertuples():
   if row.date==ds:
    if row.exception_type=='1':active.add(row.service_id)
    elif row.exception_type=='2':active.discard(row.service_id)
  sets.append((label,set(t.loc[t.service_id.isin(active),'trip_id']),lo+back*86400,hi+back*86400))
for chunk in pd.read_csv(r/'stop_times.txt',dtype=str,keep_default_na=False,usecols=['trip_id','departure_time','pickup_type'],chunksize=400000):
 # pandas timedelta independently preserves 24+ hours.
 sec=pd.to_timedelta(chunk.departure_time).dt.total_seconds()
 for label,ids,lo,hi in sets:
  counts[label]+=int((chunk.trip_id.isin(ids)&sec.ge(lo)&sec.lt(hi)&chunk.pickup_type.ne('1')).sum())
expected=json.loads(Path('analysis/results/Chicago/chi_functional_2026_09_16_v2/validation/transit_checks.json').read_text())['scheduled_stop_calls']
assert counts==expected,(counts,expected)
out={'independent_pandas_raw_schedule_counts':counts,'matches_constructed_duckdb_counts':True,'checked_prior_service_day':True}
Path('analysis/results/Chicago/chi_functional_2026_09_16_v2/validation/raw_schedule_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
