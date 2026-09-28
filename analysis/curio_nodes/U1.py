# U1: eight primary CMAP land-use groups, normalized area entropy.
# CMAP water, nonparcel, and unknown classes do not enter the use mix.
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
lui=gpd.read_parquet(arg[2]['cmap_land_use_2023'],columns=['LANDUSE','LANDUSE2','GlobalID','geometry']).to_crs(26916)
lui=lui.iloc[lui.sindex.query(areas.geometry.union_all(),predicate='intersects')].reset_index(drop=True)
lui.geometry=shapely.make_valid(lui.geometry.values)
assert lui.GlobalID.notna().all() and lui.GlobalID.is_unique
water=shapely.union_all(lui.loc[lui.LANDUSE.astype(str).eq('5000'),'geometry'])
groups=['residential','commercial','institutional','industrial','transport_utilities','agriculture','open_space','vacant_construction']
prefixes={'11':'residential','12':'commercial','13':'institutional','14':'industrial','15':'transport_utilities','2':'agriculture','3':'open_space','4':'vacant_construction'}
def category(code):
    return next((v for k,v in prefixes.items() if str(code).startswith(k)),None)
lui['category']=lui.LANDUSE.map(category)
rows=[]
for area in areas.itertuples():
    land=area.geometry.difference(water)
    q=lui.iloc[lui.sindex.query(area.geometry,predicate='intersects')]
    pieces=shapely.intersection(q.geometry.values,area.geometry)
    labels=q.category.to_numpy()
    unions={g:shapely.union_all(pieces[labels==g]) for g in groups}
    ambiguous=shapely.union_all([unions[a].intersection(unions[b]) for i,a in enumerate(groups) for b in groups[i+1:]])
    masses=np.array([unions[g].difference(ambiguous).intersection(land).area if not unions[g].is_empty else 0.0 for g in groups])
    support=masses.sum()
    if support<=0 or support>land.area+.01: raise ValueError(area.unit_id+' invalid classified land support')
    p=masses[masses>0]/support
    row={'unit_id':area.unit_id,'U1_land_use_entropy_cmap_area8':float(-(p*np.log(p)).sum()/np.log(8)),
         'classified_land_m2':support,'ambiguous_area_m2':ambiguous.area,
         'land_area_m2':land.area,'status':'constructed_chicago_only'}
    row.update({'U1_share_'+g:float(v/support) for g,v in zip(groups,masses)})
    rows.append(row)
return pd.DataFrame(rows)
