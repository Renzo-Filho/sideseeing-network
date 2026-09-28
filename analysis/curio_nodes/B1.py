# B1: exact footprint union on hydrographic land and gross area.
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
water=gpd.read_file(arg[1]['hydrography']).to_crs(26916).geometry.union_all()
buildings=gpd.read_parquet(arg[2]['overture_buildings'],columns=['id','geometry']).to_crs(26916)
assert buildings.id.is_unique and buildings.geometry.is_valid.all()
rows=[]
for area in areas.itertuples():
    gross=area.geometry; land=gross.difference(water)
    gross_m2,land_m2=gross.area,land.area
    if gross_m2<=0 or land_m2<=0: raise ValueError(area.unit_id+' invalid land support')
    union_gross=union_land=summed=0.0
    xmin,ymin,xmax,ymax=gross.bounds
    for x in np.arange(np.floor(xmin/2000)*2000,xmax,2000):
        for y in np.arange(np.floor(ymin/2000)*2000,ymax,2000):
            tile=shapely.box(x,y,x+2000,y+2000).intersection(gross)
            if tile.area<=0: continue
            ids=buildings.sindex.query(tile,predicate='intersects')
            pieces=shapely.intersection(buildings.geometry.values[ids],tile)
            union=shapely.union_all(pieces)
            union_gross+=union.area; union_land+=union.intersection(land).area
            summed+=float(shapely.area(pieces).sum())
    if union_land>land_m2+.01 or union_gross>gross_m2+.01 or union_gross>summed+.01:
        raise ValueError(area.unit_id+' footprint bounds failed')
    rows.append({'unit_id':area.unit_id,'B1_coverage_land':union_land/land_m2,
                 'B1_coverage_gross':union_gross/gross_m2,'footprint_union_land_m2':union_land,
                 'footprint_union_gross_m2':union_gross,'summed_footprint_m2':summed,
                 'overlap_excess_fraction':(summed-union_gross)/summed if summed else 0,
                 'land_area_m2':land_m2,'gross_area_m2':gross_m2,'water_area_m2':gross_m2-land_m2,
                 'status':'constructed_chicago'})
return pd.DataFrame(rows)
