# M1: mapped street length per gross square kilometre. arg is the morphology lane: area, Overture roads, municipal streets.
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
classes=['motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown']
roads=gpd.read_parquet(arg[1]['overture_segments'],columns=['id','subtype','class','geometry'])
roads=roads.loc[roads.subtype.eq('road')&roads['class'].isin(classes)].to_crs(26916).reset_index(drop=True)
assert roads.id.is_unique and roads.geometry.is_valid.all()
roads=roads.iloc[roads.sindex.query(areas.geometry.union_all(),predicate='intersects')].reset_index(drop=True)
rows=[]; class_rows=[]
for area in areas.itertuples():
    ids=roads.sindex.query(area.geometry,predicate='intersects')
    geom=roads.geometry.values[ids]
    inside=shapely.covers(area.geometry,geom)
    clipped=np.array(geom,copy=True)
    clipped[~inside]=shapely.intersection(geom[~inside],area.geometry)
    prior=areas.loc[areas.unit_id.lt(area.unit_id)]
    neighbors=prior.iloc[prior.sindex.query(area.geometry,predicate='intersects')]
    shared=shapely.union_all([area.geometry.boundary.intersection(g.boundary) for g in neighbors.geometry])
    if not shared.is_empty: clipped=shapely.difference(clipped,shared)
    lengths=shapely.length(clipped)
    total=float(lengths.sum()); gross=float(area.geometry.area)
    if total<=0 or gross<=0: raise ValueError(area.unit_id+' empty road or area support')
    rows.append({'unit_id':area.unit_id,'M1_mapped_street_density_km_km2':total/1000/(gross/1e6),
                 'eligible_road_length_m':total,'gross_area_m2':gross,'status':'constructed_chicago'})
    for category in classes:
        class_rows.append({'unit_id':area.unit_id,'class':category,
                           'length_m':float(lengths[roads['class'].iloc[ids].eq(category).to_numpy()].sum())})
summary=pd.DataFrame(rows); class_lengths=pd.DataFrame(class_rows)
assert np.allclose(summary.set_index('unit_id').eligible_road_length_m,
                   class_lengths.groupby('unit_id').length_m.sum().reindex(summary.unit_id),atol=.01)
return (summary,class_lengths)
