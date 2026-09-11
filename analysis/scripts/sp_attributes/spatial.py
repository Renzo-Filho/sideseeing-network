from . import core as C
import geopandas as gpd,pandas as pd,numpy as np,shapely,pyogrio

def building_coverage(code):
 d=C.districts().set_index('district_id').loc[code];land=gpd.read_parquet(C.BASE/'N02/district_land.parquet').set_index('district_id').loc[code].geometry
 source=C.ROOT/'analysis/data/SP/Edificacoes/sao_paulo_building_morphology.gpkg'
 g=pyogrio.read_dataframe(source,layer='buildings',columns=['building_id'],bbox=tuple(d.geometry.bounds));assert g.crs.to_epsg()==31983
 step=C.CFG['b1_tile_m'];xmin,ymin,xmax,ymax=d.geometry.bounds;gross=0.;land_area=0.;summed=0.;count=set()
 for x in np.arange(np.floor(xmin/step)*step,xmax,step):
  for y in np.arange(np.floor(ymin/step)*step,ymax,step):
   tile=shapely.intersection(shapely.box(x,y,x+step,y+step),d.geometry)
   if tile.is_empty or tile.area==0:continue
   ids=g.sindex.query(tile,predicate='intersects')
   if not len(ids):continue
   pieces=shapely.intersection(g.geometry.values[ids],tile);a=shapely.area(pieces);valid=a>0;pieces=pieces[valid];count.update(g.building_id.iloc[ids[valid]])
   if not len(pieces):continue
   union=shapely.union_all(pieces);gross+=union.area;land_area+=union.intersection(land).area;summed+=a.sum()
 assert gross<=d.gross_area_m2+.01 and land_area<=d.land_area_m2+.01 and gross<=summed+.01
 F=C.Features();F.add(code,'B1','building_coverage_land',land_area/d.land_area_m2,'fraction',num=land_area,den=d.land_area_m2,n=len(count),primary=True,status='mapped_footprint_proxy',coverage_basis='all intersecting records in provided release; real building completeness unknown',method='exact footprint union in disjoint 2km tiles; intersect district land')
 F.add(code,'B1','building_coverage_gross',gross/d.gross_area_m2,'fraction',num=gross,den=d.gross_area_m2,n=len(count),status='sensitivity',method='same tile union on gross district area')
 F.add(code,'B1','footprint_overlap_excess_fraction',(summed-gross)/summed if summed else 0,'fraction',num=summed-gross,den=summed,n=len(count),status='diagnostic')
 C.dump(C.OUT/'intermediates'/f'buildings_{code}.json',{'unique_intersecting_buildings':len(count),'summed_individual_area_m2':summed,'union_gross_area_m2':gross,'union_land_area_m2':land_area})
 return F.frame()

def population_points(code):
 d=C.districts().set_index('district_id').loc[code].geometry;s=gpd.read_parquet(C.BASE/'N07/census_sectors.parquet',columns=['sector_id','qt_populacao','geometry']);s=s.iloc[s.sindex.query(d,predicate='intersects')]
 step=C.CFG['u4_grid_m'];rows=[];geoms=[]
 for row in s.itertuples():
  if row.qt_populacao<=0:continue
  piece=row.geometry.intersection(d)
  if piece.area<=0:continue
  xmin,ymin,xmax,ymax=piece.bounds
  xs=np.arange(np.floor(xmin/step)*step,xmax,step);ys=np.arange(np.floor(ymin/step)*step,ymax,step)
  xx,yy=np.meshgrid(xs,ys);cells=shapely.box(xx.ravel(),yy.ravel(),xx.ravel()+step,yy.ravel()+step);parts=shapely.intersection(cells,piece);area=shapely.area(parts);keep=area>0
  for geom,ar,x,y in zip(parts[keep],area[keep],xx.ravel()[keep],yy.ravel()[keep]):rows.append((row.sector_id,int(x/step),int(y/step),row.qt_populacao*ar/row.geometry.area));geoms.append(geom.representative_point())
 g=gpd.GeoDataFrame(rows,columns=['sector_id','cell_x','cell_y','population_weight'],geometry=geoms,crs=31983);g['point_id']=np.arange(len(g));g['district_id']=code
 target=pd.read_parquet(C.BASE/'N07/census_district_allocation.parquet');target=target.loc[target.district_id.eq(code)].population_allocated.sum()
 assert np.isclose(g.population_weight.sum(),target,rtol=1e-9,atol=.01)
 return g

def transit_access(code):
 points=population_points(code);stops=gpd.read_parquet(C.BASE/'N08/stops.parquet');service=pd.read_parquet(C.BASE/'N08/stop_route_service.parquet');windows=sorted(service.window.unique());radii=C.CFG['u4_radii_m'];results=[]
 for start in range(0,len(points),500):
  p=points.iloc[start:start+500].reset_index(drop=True);ai,bi=stops.sindex.query(p.geometry,predicate='dwithin',distance=max(radii))
  pairs=pd.DataFrame({'point_id':p.point_id.values[ai],'stop_id':stops.stop_id.values[bi],'distance':shapely.distance(p.geometry.values[ai],stops.geometry.values[bi])})
  joined=pairs.merge(service,on='stop_id',how='inner',validate='many_to_many')
  for radius in radii:
   hit=joined.loc[joined.distance.le(radius)]
   maxima=hit.groupby(['point_id','window','route_id','direction_id']).expected_departures.max()
   sums=maxima.groupby(['point_id','window']).sum();served=hit.groupby(['point_id','window']).size()
   for w in windows:
    values=sums.xs(w,level='window') if w in sums.index.get_level_values('window') else pd.Series(dtype=float)
    for point in p.itertuples():results.append((point.point_id,w,radius,float(values.get(point.point_id,0))))
 q=pd.DataFrame(results,columns=['point_id','window','radius_m','expected_route_direction_supply']);q=q.merge(points[['point_id','population_weight']],on='point_id',validate='many_to_one')
 assert np.isfinite(q.expected_route_direction_supply).all() and q.expected_route_direction_supply.ge(0).all()
 wide=q.pivot(index=['point_id','window'],columns='radius_m',values='expected_route_direction_supply');assert (wide[800]+1e-9>=wide[400]).all()
 points.to_parquet(C.OUT/'intermediates'/f'population_points_{code}.parquet',index=False);q.to_parquet(C.OUT/'intermediates'/f'point_service_{code}.parquet',index=False)
 F=C.Features();pop=points.population_weight.sum()
 for (window,radius),part in q.groupby(['window','radius_m']):
  num=float((part.population_weight*part.expected_route_direction_supply).sum());access=num/pop;reached=float(part.loc[part.expected_route_direction_supply.gt(0),'population_weight'].sum())
  F.add(code,'U4',f'bus_service_access_{window}_{radius}m',access,'expected departures per 2h per resident',num=num,den=pop,n=len(points),primary=window==C.CFG['u4_primary_window'] and radius==400,status='population_and_service_proxy',method=C.CFG['u4_population_support']+'; '+C.CFG['u4_service'])
  F.add(code,'U4',f'population_bus_service_reach_{window}_{radius}m',reached/pop,'fraction',num=reached,den=pop,n=len(points),status='diagnostic',method='population at support points with positive reachable service')
 C.dump(C.OUT/'intermediates'/f'transit_{code}.json',{'population_points':len(points),'population_weight':float(pop),'population_conserved':True,'radius_monotonicity':True})
 return F.frame()
