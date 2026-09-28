# M3: experimental mapped-street enclosures. These are not accepted physical blocks.
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
streets=gpd.read_file(arg[2]['street_centerlines'])
streets=streets.loc[streets.status.eq('N')&streets['class'].isin(['1','2','3','4','7','9','99'])]
streets=streets.to_crs(26916)
city=areas.geometry.union_all()
streets=streets.iloc[streets.sindex.query(city.buffer(1500),predicate='intersects')]
merged=shapely.union_all(streets.geometry.values)
faces=shapely.get_parts(shapely.polygonize(shapely.get_parts(merged)))
faces=np.array([g for g in faces if g.area>0 and g.intersects(city) and not g.boundary.intersects(city.boundary)],dtype=object)
face_frame=gpd.GeoDataFrame({'face_id':range(len(faces))},geometry=faces,crs=26916)
a,b=areas.sindex.query(face_frame.geometry,predicate='intersects')
overlap=shapely.area(shapely.intersection(face_frame.geometry.values[a],areas.geometry.values[b]))
q=pd.DataFrame({'face_id':a,'unit_id':areas.unit_id.values[b],'overlap_m2':overlap})
q=q.loc[q.overlap_m2.gt(0)].sort_values(['face_id','overlap_m2','unit_id'],ascending=[True,False,True]).drop_duplicates('face_id')
face_frame=face_frame.merge(q[['face_id','unit_id']],on='face_id',validate='one_to_one')
face_frame['area_m2']=face_frame.geometry.area
face_frame['log_area']=np.log(face_frame.area_m2)
agg=face_frame.groupby('unit_id').log_area.agg(['median',lambda x:x.quantile(.75)-x.quantile(.25),'size'])
agg.columns=['M3_log_area_median','M3_log_area_iqr','enclosure_candidates']
result=areas[['unit_id']].join(agg,on='unit_id')
result['status']='experimental_enclosures_not_accepted_blocks'
return (result,face_frame[['unit_id','area_m2','geometry']])
