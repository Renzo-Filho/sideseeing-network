"""Diagnostic only: intersect Overture buildings with saved motorway candidates."""
from __future__ import annotations
import json
from pathlib import Path
import duckdb
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.ops import transform

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/Chicago/chicago_m3_complete_zone_pilot_v1_2026_09_26'
SOURCE=ROOT/'analysis/data/Chicago/overture_2026_08_19/building/part_0000.parquet'
TO_WGS=Transformer.from_crs(26916,4326,always_xy=True).transform
TO_METRIC=Transformer.from_crs(4326,26916,always_xy=True).transform

def fetch_buildings(bounds):
    west,south=TO_WGS(bounds[0],bounds[1]); east,north=TO_WGS(bounds[2],bounds[3])
    query=f"SELECT geometry FROM read_parquet('{SOURCE}') WHERE bbox.xmax >= {west} AND bbox.xmin <= {east} AND bbox.ymax >= {south} AND bbox.ymin <= {north}"
    records=duckdb.query(query).df()['geometry']
    geometries=[transform(TO_METRIC,shapely.from_wkb(bytes(w))) for w in records]
    return geometries,shapely.STRtree(geometries)

def audit(frame, label, buildings, tree):
    rows=[]
    for _,r in frame.iterrows():
        g=shapely.from_wkt(r.geometry_wkt) if 'geometry_wkt' in frame else None
        if g is None: continue
        hits=tree.query(g,predicate='intersects')
        area=sum(g.intersection(buildings[int(i)]).area for i in hits)
        rows.append({'sample':label,'candidate_id':str(r.candidate_index) if label=='complete_motorway_core' else str(r.candidate_id),
                     'area_m2':r.area_m2,'motorway_exposure':r.motorway_exposure,
                     'building_count':len(hits),'building_area_m2':area,'building_fraction':area/g.area})
    return rows

def main():
    selection=json.loads((OUT/'motorway_zone_selection.json').read_text())['zone'];x,y=selection['x'],selection['y']
    buildings,tree=fetch_buildings((x-500,y-500,x+500,y+500))
    complete=pd.read_csv(OUT/'motorway_complete_candidate_inventory.csv')
    complete=complete[complete.method=='cook_row_edge_alley_open_3m']
    rows=audit(complete,'complete_motorway_core',buildings,tree)
    # Earlier saved candidates have no WKT; reproduce their clipped face geometry.
    from evaluate_chicago_m3_fresh_tiles_2026_09_26 import components,source_geometries
    from evaluate_chicago_m3_alley_3m_motorway_stress_2026_09_26 import motorway_corridor
    source=ROOT/'analysis/results/Chicago/chicago_m3_motorway_holdout_2026_09_26'
    tiles={t['tile_id']:t for t in json.loads((source/'tile_selection.json').read_text())['tiles']}
    road=source_geometries('CHI:49','row',lambda p:p.get('ROWTYPE') in (1,4,5))
    edge=source_geometries('CHI:49','road_edge',lambda p:p.get('TYPE')==1)
    alley=source_geometries('CHI:49','road_edge',lambda p:p.get('TYPE')==5)
    mask=shapely.union_all([road,edge]).difference(alley.buffer(3))
    prior=pd.read_csv(OUT/'motorway_3m_candidates.csv')
    bx=[v['x'] for v in tiles.values()];by=[v['y'] for v in tiles.values()]
    buildings,tree=fetch_buildings((min(bx)-300,min(by)-300,max(bx)+300,max(by)+300))
    for tile_id,tile in tiles.items():
        extent,pieces=components({**tile,'half_width_m':240},mask)
        for j,g in enumerate(sorted(pieces,key=lambda p:p.area,reverse=True),1):
            if g.area<1000 or g.boundary.intersects(extent.boundary):continue
            cid=f'{tile_id}_P{j:02d}'
            v=prior.loc[prior.candidate_id.eq(cid)].iloc[0]
            hits=tree.query(g,predicate='intersects');area=sum(g.intersection(buildings[int(i)]).area for i in hits)
            rows.append({'sample':'prior_motorway_spots','candidate_id':cid,'area_m2':g.area,
                         'motorway_exposure':v.motorway_exposure,'building_count':len(hits),
                         'building_area_m2':area,'building_fraction':area/g.area})
    out=pd.DataFrame(rows);out.to_csv(OUT/'motorway_building_support.csv',index=False)
    summary={}
    for sample,q in out.groupby('sample'):
        high=q.motorway_exposure>=.3
        summary[sample]={
            'candidate_count':len(q),
            'motorway_exposure_ge_0_3':int(high.sum()),
            'high_exposure_without_buildings':int((high & q.building_count.eq(0)).sum()),
            'high_exposure_with_buildings':int((high & q.building_count.gt(0)).sum()),
            'fully_exposed_under_1000_m2_without_buildings':int(((q.motorway_exposure>=.99)&(q.area_m2<1000)&q.building_count.eq(0)).sum())}
    (OUT/'motorway_building_support_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(out.groupby('sample').agg(candidates=('candidate_id','size'),with_buildings=('building_count',lambda x:int((x>0).sum()))).to_string())
    for sample,q in out.groupby('sample'):
        print('\n',sample);print(q[['candidate_id','motorway_exposure','building_count','building_fraction']].to_string(index=False))
if __name__=='__main__':main()
