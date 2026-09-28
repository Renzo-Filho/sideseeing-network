# U4: population-weighted scheduled CTA bus departures, 400 m, Wed 2026-09-16 07–09.
# One stop per route/direction contributes its maximum nearby departure count.
import datetime as dt
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import duckdb
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
blocks=gpd.read_parquet(arg[1]['census_blocks_pop20_jobs'],columns=['GEOID20','POP20','geometry']).to_crs(26916)
blocks['GEOID20']=blocks.GEOID20.astype(str).str.zfill(15)
assert blocks.GEOID20.is_unique and blocks.POP20.ge(0).all()
whole=shapely.area(blocks.geometry.values)
a,b=areas.sindex.query(blocks.geometry,predicate='intersects')
piece_geom=shapely.intersection(blocks.geometry.values[a],areas.geometry.values[b])
positive=shapely.area(piece_geom)>0
pieces=gpd.GeoDataFrame({'GEOID20':blocks.GEOID20.values[a[positive]],
    'unit_id':areas.unit_id.values[b[positive]],'POP20':blocks.POP20.values[a[positive]],
    'block_area_m2':whole[a[positive]]},geometry=piece_geom[positive],crs=26916)
def read(name): return pd.read_parquet(arg[3]['cta_'+name]).fillna('')
routes,trips,stops,calendar,exceptions=[read(n) for n in ['routes','trips','stops','calendar','calendar_dates']]
assert routes.route_id.is_unique and trips.trip_id.is_unique and stops.stop_id.is_unique
assert set(trips.route_id).issubset(set(routes.route_id))
bus=trips.loc[trips.route_id.isin(routes.loc[routes.route_type.eq('3'),'route_id']),
              ['trip_id','service_id','route_id','direction_id']]
assert bus.direction_id.isin(['0','1']).all()
def active(date):
    stamp=date.strftime('%Y%m%d'); day=date.strftime('%A').lower()
    ids=set(calendar.loc[(calendar.start_date<=stamp)&(calendar.end_date>=stamp)&calendar[day].eq('1'),'service_id'])
    for row in exceptions.loc[exceptions.date.eq(stamp)].itertuples():
        if row.exception_type=='1':ids.add(row.service_id)
        elif row.exception_type=='2':ids.discard(row.service_id)
        else:raise ValueError('Unknown GTFS exception')
    return ids
con=duckdb.connect(); con.execute("SET memory_limit='2GB'")
con.register('bus',bus)
con.read_parquet(arg[3]['cta_stop_times']).create_view('times')
con.execute("""CREATE TEMP TABLE bus_times AS SELECT s.stop_id,t.route_id,t.direction_id,t.service_id,
    try_cast(split_part(s.departure_time,':',1) AS BIGINT)*3600+
    try_cast(split_part(s.departure_time,':',2) AS BIGINT)*60+
    try_cast(split_part(s.departure_time,':',3) AS BIGINT) AS sec,
    s.pickup_type FROM times s JOIN bus t USING(trip_id)""")
maxsec=con.execute('SELECT max(sec) FROM bus_times').fetchone()[0]
if con.execute('SELECT count(*) FROM bus_times WHERE sec IS NULL').fetchone()[0]:raise ValueError('Invalid GTFS time')
date=dt.date(2026,9,16); events=[]
for back in range(int(maxsec//86400)+1):
    service=pd.DataFrame({'service_id':sorted(active(date-dt.timedelta(days=back)))})
    con.register('active_service',service)
    events.append(con.execute("""SELECT stop_id,route_id,direction_id,count(*) AS departures
        FROM bus_times JOIN active_service USING(service_id)
        WHERE sec>=? AND sec<? AND coalesce(pickup_type,'')<>'1'
        GROUP BY stop_id,route_id,direction_id""",[25200+back*86400,32400+back*86400]).df())
service=pd.concat(events).groupby(['stop_id','route_id','direction_id'],as_index=False).departures.sum()
con.close()
stopgeo=gpd.GeoDataFrame(stops[['stop_id']],geometry=gpd.points_from_xy(
    pd.to_numeric(stops.stop_lon),pd.to_numeric(stops.stop_lat)),crs=4326).to_crs(26916)
rows=[]
for area in areas.itertuples():
    part=pieces.loc[pieces.unit_id.eq(area.unit_id)&pieces.POP20.gt(0)]
    point_geom=[]; weights=[]
    for piece in part.itertuples():
        xmin,ymin,xmax,ymax=piece.geometry.bounds
        xx,yy=np.meshgrid(np.arange(np.floor(xmin/250)*250,xmax,250),
                          np.arange(np.floor(ymin/250)*250,ymax,250))
        cells=shapely.box(xx.ravel(),yy.ravel(),xx.ravel()+250,yy.ravel()+250)
        clipped=shapely.intersection(cells,piece.geometry)
        size=shapely.area(clipped)
        for geom,area_m2 in zip(clipped[size>0],size[size>0]):
            point_geom.append(geom.representative_point())
            weights.append(piece.POP20*area_m2/piece.block_area_m2)
    if not weights:raise ValueError(area.unit_id+' no population support')
    points=gpd.GeoDataFrame({'point_id':range(len(weights)),'population_weight':weights},geometry=point_geom,crs=26916)
    numerator=0.0
    for start in range(0,len(points),500):
        chunk=points.iloc[start:start+500]
        pa,st=stopgeo.sindex.query(chunk.geometry,predicate='dwithin',distance=400)
        near=pd.DataFrame({'point_id':chunk.point_id.values[pa],'stop_id':stopgeo.stop_id.values[st]})
        joined=near.merge(service,on='stop_id',validate='many_to_many')
        maxima=joined.groupby(['point_id','route_id','direction_id']).departures.max()
        supply=maxima.groupby('point_id').sum()
        values=chunk.point_id.map(supply).fillna(0).to_numpy()
        numerator+=float(values@chunk.population_weight.to_numpy())
    pop=float(np.sum(weights))
    rows.append({'unit_id':area.unit_id,'U4_bus_supply_weekday_am_400m':numerator/pop,
                 'population_weight':pop,'weighted_departures':numerator,
                 'support_points':len(weights),'status':'constructed_chicago'})
return pd.DataFrame(rows)
