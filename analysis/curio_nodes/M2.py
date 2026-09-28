# M2: candidate graph connector density only. Physical intersection consolidation is unresolved.
import geopandas as gpd
import pandas as pd
import numpy as np
areas=gpd.read_file(arg[0]['community_areas']).to_crs(26916)
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
classes=['motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown']
roads=gpd.read_parquet(arg[1]['overture_segments'],columns=['id','subtype','class','connectors','geometry'])
roads=roads.loc[roads.subtype.eq('road')&roads['class'].isin(classes)]
assert roads.id.is_unique
arms={}
for row in roads.itertuples():
    for link in row.connectors:
        at=float(link['at']); key=link['connector_id']
        if not np.isfinite(at) or not 0<=at<=1:raise ValueError('Bad connector position')
        bucket=arms.setdefault(key,set())
        if at>0:bucket.add((row.id,at,'before'))
        if at<1:bucket.add((row.id,at,'after'))
connectors=gpd.read_parquet(arg[1]['overture_connectors'],columns=['id','geometry']).to_crs(26916)
connectors=connectors.loc[connectors.id.map(lambda x:len(arms.get(x,()))>=3)].reset_index(drop=True)
own=np.full(len(connectors),'',dtype=object)
for area in areas.itertuples():
    ids=connectors.sindex.query(area.geometry,predicate='intersects')
    own[ids[own[ids]=='']]=area.unit_id
counts=pd.Series(own[own!='']).value_counts()
result=areas[['unit_id']].copy()
result['M2_connector_candidate_density_km2']=result.unit_id.map(counts).fillna(0).to_numpy()/(areas.geometry.area.to_numpy()/1e6)
result['status']='diagnostic_only_not_physical_intersections'
return result
