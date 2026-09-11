from . import common as C
import pandas as pd,numpy as np,geopandas as gpd,datetime as dt,math

def time_seconds(value):
 try:
  h,m,s=map(int,str(value).split(':'))
  if h<0 or not 0<=m<60 or not 0<=s<60:return np.nan
  return h*3600+m*60+s
 except (ValueError,TypeError):return np.nan

def expected_frequency(start,end,headway,offset,window_start,window_end):
 return np.maximum(0,np.minimum(end+offset,window_end)-np.maximum(start+offset,window_start))/headway

def transit():
 out=C.OUT/'N08';folder=C.RAW/'Socioeconomico/f-6gy-sptrans-latest'
 def load(n):return pd.read_csv(folder/(n+'.txt'),dtype=str,keep_default_na=False)
 trips=load('trips');routes=load('routes');stops=load('stops');st=load('stop_times');fr=load('frequencies');calendar=load('calendar');agency=load('agency')
 assert trips.trip_id.is_unique and routes.route_id.is_unique and stops.stop_id.is_unique and calendar.service_id.is_unique
 issues=[];bad=set()
 def reject(ids,reason):
  ids=set(ids);bad.update(ids);issues.extend({'trip_id':x,'reason':reason} for x in sorted(ids))
 reject(trips.loc[~trips.route_id.isin(routes.route_id),'trip_id'],'unknown_route');reject(trips.loc[~trips.service_id.isin(calendar.service_id),'trip_id'],'unknown_service')
 reject(st.loc[~st.trip_id.isin(trips.trip_id),'trip_id'],'unknown_trip_in_stop_times');reject(st.loc[~st.stop_id.isin(stops.stop_id),'trip_id'],'unknown_stop')
 reject(fr.loc[~fr.trip_id.isin(trips.trip_id),'trip_id'],'unknown_trip_in_frequencies')
 st['sequence']=pd.to_numeric(st.stop_sequence,errors='coerce');st['arrival_sec']=st.arrival_time.map(time_seconds);st['departure_sec']=st.departure_time.map(time_seconds)
 reject(st.loc[st[['sequence','arrival_sec','departure_sec']].isna().any(axis=1),'trip_id'],'invalid_stop_time_or_sequence');reject(st.loc[st.arrival_sec.gt(st.departure_sec),'trip_id'],'arrival_after_departure');reject(st.loc[st.duplicated(['trip_id','sequence'],keep=False),'trip_id'],'duplicate_stop_sequence')
 st=st.sort_values(['trip_id','sequence']);previous=st.groupby('trip_id').departure_sec.shift();reject(st.loc[st.arrival_sec.lt(previous),'trip_id'],'nonchronological_stop_times')
 reject(trips.loc[~trips.trip_id.isin(st.trip_id),'trip_id'],'trip_without_stop_times')
 fr['start_sec']=fr.start_time.map(time_seconds);fr['end_sec']=fr.end_time.map(time_seconds);fr['headway']=pd.to_numeric(fr.headway_secs,errors='coerce');fr['exact_times']=fr.get('exact_times',pd.Series('0',index=fr.index))
 reject(fr.loc[fr[['start_sec','end_sec','headway']].isna().any(axis=1)|fr.headway.le(0)|fr.end_sec.le(fr.start_sec)|~fr.exact_times.isin(['0','1','']),'trip_id'],'invalid_frequency_interval')
 fr=fr.sort_values(['trip_id','start_sec']);previous_end=fr.groupby('trip_id').end_sec.transform(lambda x:x.cummax().shift());reject(fr.loc[fr.start_sec.lt(previous_end),'trip_id'],'overlapping_frequency_intervals')
 # Source shapes are checked by key only; vehicle shapes are not walking-network geometry.
 c=C.con();c.read_csv(str(folder/'shapes.txt'),all_varchar=True).create_view('shapes');shape_ids=set(c.execute('select distinct shape_id from shapes').fetchnumpy()['shape_id']);c.close();reject(trips.loc[~trips.shape_id.isin(shape_ids),'trip_id'],'unknown_shape')
 lat=pd.to_numeric(stops.stop_lat,errors='coerce');lon=pd.to_numeric(stops.stop_lon,errors='coerce');invalid_stops=~lat.between(-90,90)|~lon.between(-180,180)
 reject(st.loc[st.stop_id.isin(stops.loc[invalid_stops,'stop_id']),'trip_id'],'invalid_stop_coordinates')
 stopgeo=gpd.GeoDataFrame(stops,geometry=gpd.points_from_xy(lon,lat),crs=4326).to_crs(C.CFG['metric_crs']);stopgeo['district_id']=C.point_assign(stopgeo,C.districts());C.write(stopgeo,out/'stops.parquet')
 pd.DataFrame(issues,columns=['trip_id','reason']).to_parquet(out/'trip_exclusions.parquet',index=False)
 st.to_parquet(out/'normalized_stop_times.parquet',index=False);fr.to_parquet(out/'normalized_frequencies.parquet',index=False);trips.to_parquet(out/'trips.parquet',index=False);calendar.to_parquet(out/'calendar.parquet',index=False)
 valid=trips.loc[~trips.trip_id.isin(bad)];sg={k:v for k,v in st.groupby('trip_id')};fg={k:v for k,v in fr.groupby('trip_id')};cal=calendar.set_index('service_id')
 days=['monday','tuesday','wednesday','thursday','friday','saturday','sunday'];events=[]
 for window in C.CFG['gtfs_windows']:
  date=dt.date.fromisoformat(window['date']);lo=time_seconds(window['start']);hi=time_seconds(window['end'])
  for tr in valid.itertuples(index=False):
   stops_for_trip=sg[tr.trip_id];offsets=stops_for_trip.departure_sec.values-stops_for_trip.departure_sec.iloc[0];freq=fg.get(tr.trip_id);service=cal.loc[tr.service_id];total=np.zeros(len(offsets))
   max_time=float(freq.end_sec.max()+offsets.max()) if freq is not None else float(stops_for_trip.departure_sec.max())
   lookback=max(1,int(math.ceil(max_time/86400)))
   for delta in range(-lookback,1):
    service_date=date+dt.timedelta(days=delta);stamp=service_date.strftime('%Y%m%d')
    if not(service.start_date<=stamp<=service.end_date and service[days[service_date.weekday()]]=='1'):continue
    shift=delta*86400
    if freq is None:
     departures=stops_for_trip.departure_sec.values+shift;total+=((departures>=lo)&(departures<hi)).astype(float)
    else:
     for f in freq.itertuples(index=False):
      if f.exact_times=='1':
       starts=np.arange(f.start_sec,f.end_sec,f.headway)+shift
       total+=((starts[:,None]+offsets>=lo)&(starts[:,None]+offsets<hi)).sum(axis=0)
      else:total+=expected_frequency(f.start_sec+shift,f.end_sec+shift,f.headway,offsets,lo,hi)
   for stop_id,seq,amount in zip(stops_for_trip.stop_id,stops_for_trip.sequence,total):
    if amount>0:events.append((window['label'],window['date'],tr.route_id,tr.direction_id,tr.trip_id,stop_id,int(seq),float(amount)))
 ev=pd.DataFrame(events,columns=['window','date','route_id','direction_id','trip_id','stop_id','stop_sequence','expected_departures']);ev.to_parquet(out/'stop_service_events.parquet',index=False)
 service=ev.groupby(['window','date','route_id','direction_id','stop_id'],as_index=False).expected_departures.sum();service.to_parquet(out/'stop_route_service.parquet',index=False)
 assert np.isfinite(service.expected_departures).all() and service.expected_departures.ge(0).all()
 C.dump(out/'service_method.json',{'time_windows':C.CFG['gtfs_windows'],'timezone':agency.agency_timezone.iloc[0],'expected_service':'continuous interval/headway exposure for exact_times=0; scheduled/exact rows counted discretely','spatial_method_for_later_attributes':{'primary':'Euclidean binary catchment','radius_m':400,'sensitivity_radius_m':800,'nearby_stop_same_route_direction':'take maximum reachable stop service rather than sum repeated boarding opportunities'},'scope':'bus feed only; no pedestrian routing or rail frequency inferred','calendar_exceptions':'not supplied; no holiday exception claim','attribute_index_computed':False})
 C.dump(out/'qa.json',{'trips':len(trips),'eligible_trips':len(valid),'excluded_trip_ids':len(set(trips.trip_id)&bad),'exclusion_reasons':pd.Series([r['reason'] for r in issues]).value_counts().to_dict(),'stops':len(stops),'invalid_stop_coordinates':int(invalid_stops.sum()),'frequency_rows':len(fr),'frequency_exact_times_default':'0 when omitted','service_rows':len(service),'event_rows':len(ev),'window_expected_stop_calls':service.groupby('window').expected_departures.sum().to_dict(),'reference_integrity':'checked routes/service/trips/stops/shapes; invalid trips retained in exclusions','calendar_range':[calendar.start_date.min(),calendar.end_date.max()],'calendar_exceptions':'not supplied','network_accessibility':'not computed; declared Euclidean catchment parameters are ready for later attribute construction'})
