# U2: LODES 2022 jobs, whole-block area allocation to Community Areas.
import geopandas as gpd
import pandas as pd
import shapely
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
blocks=gpd.read_parquet(arg[1]['census_blocks_pop20_jobs'],columns=['GEOID20','jobs','geometry']).to_crs(26916)
blocks['GEOID20']=blocks.GEOID20.astype(str).str.zfill(15)
assert blocks.GEOID20.is_unique and blocks.GEOID20.str.fullmatch(r'\d{15}').all()
assert blocks.jobs.notna().all() and blocks.jobs.ge(0).all()
whole=shapely.area(blocks.geometry.values)
assert (whole>0).all()
a,b=areas.sindex.query(blocks.geometry,predicate='intersects')
weights=shapely.area(shapely.intersection(blocks.geometry.values[a],areas.geometry.values[b]))/whole[a]
keep=weights>0
q=pd.DataFrame({'GEOID20':blocks.GEOID20.values[a[keep]],'unit_id':areas.unit_id.values[b[keep]],
                'jobs':blocks.jobs.values[a[keep]],'weight':weights[keep]})
if q.groupby('GEOID20').weight.sum().gt(1+1e-8).any(): raise ValueError('Block allocation exceeds whole area')
q['allocated_jobs']=q.jobs*q.weight
agg=q.groupby('unit_id').agg(allocated_jobs=('allocated_jobs','sum'),contributing_blocks=('GEOID20','nunique'))
result=areas[['unit_id']].join(agg,on='unit_id')
if result.allocated_jobs.isna().any(): raise ValueError('Missing population support')
result['gross_area_km2']=areas.geometry.area.to_numpy()/1e6
result['U2_jobs_density_gross_km2']=result.allocated_jobs/result.gross_area_km2
result['status']='constructed_chicago'
return result
