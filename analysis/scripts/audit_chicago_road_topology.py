"""Diagnose supplied road endpoints without promoting them to accepted intersections."""
from pathlib import Path
import geopandas as gpd
import shapely
import pandas as pd
import numpy as np
import json
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1'
OUT=ROOT/'analysis/results/Chicago/chi_local_2026_09_16_v1/validation'
def main():
    r=gpd.read_parquet(WORK/'eligible_roads.parquet');rows=[];excluded=0
    for i,v in r.iterrows():
        parts=shapely.get_parts(v.geometry)
        if len(parts)!=1 or parts[0].geom_type!='LineString' or parts[0].is_empty:
            excluded+=1;continue
        # Preserve original coordinate direction; do not line_merge/reverse before using node labels.
        g=parts[0]
        for end,node,z,p in [('f',v.fnode_id,v.f_zlev,g.coords[0]),('t',v.tnode_id,v.t_zlev,g.coords[-1])]:
            rows.append((i,end,str(node),str(z),p[0],p[1]))
    e=pd.DataFrame(rows,columns=['segment','end','node','z','x','y'])
    q=e.groupby(['node','z']).agg(arms=('segment','size'),xmin=('x','min'),xmax=('x','max'),ymin=('y','min'),ymax=('y','max'))
    q['bbox_diagonal_m']=np.hypot(q.xmax-q.xmin,q.ymax-q.ymin)
    a={'eligible_road_records':len(r),'empty_or_multipart_excluded':excluded,'node_level_groups':len(q),'groups_three_or_more_arms':int(q.arms.ge(3).sum()),'all_node_groups_spread_gt_1m':int(q.bbox_diagonal_m.gt(1).sum()),'max_endpoint_spread_m':float(q.bbox_diagonal_m.max()),'warning':'Original single-part coordinate direction retained. Source node IDs, level semantics, physical arm duplication and completeness require review. Not accepted M2 intersections.'}
    (OUT/'road_topology_diagnostic.json').write_text(json.dumps(a,indent=2)+'\n')
    q.to_csv(WORK/'road_node_level_diagnostics.csv')
    candidates=q[q.arms.ge(3)].reset_index()
    candidates=candidates[~candidates.node.isin(['0','None','nan',''])].copy()
    points=gpd.GeoDataFrame(candidates,geometry=gpd.points_from_xy(candidates.xmin,candidates.ymin),crs=r.crs)
    d=gpd.read_parquet(WORK/'districts.parquet')
    a_idx,b_idx=d.sindex.query(points.geometry,predicate='intersects')
    owners=pd.DataFrame({'point':a_idx,'district_id':d.district_id.values[b_idx]}).sort_values(['point','district_id']).drop_duplicates('point')
    counts=owners.district_id.value_counts()
    table=d[['district_id','unit_id','district_name','gross_area_m2']].copy()
    table['candidate_count']=table.district_id.map(counts).fillna(0).astype(int)
    table['candidate_density_km2']=table.candidate_count/(table.gross_area_m2/1e6)
    table['status']='experimental_source_graph_not_harmonized'
    table.to_csv(OUT.parent/'tables/m2_endpoint_candidates.csv',index=False)
    points.to_parquet(WORK/'m2_endpoint_candidates.parquet',index=False)
    a['candidates_after_nonzero_id_filter']=len(points)
    a['assigned_inside_city']=len(owners)
    a['outside_city']=len(points)-len(owners)
    (OUT/'road_topology_diagnostic.json').write_text(json.dumps(a,indent=2)+'\n')
    print(json.dumps(a,indent=2))
if __name__=='__main__':main()
