"""Paired M1 linework proximity against each city's independent local baseline.

Sample each clipped line at <=20 m spacing and weight sample points by the
represented line length. The 5/15/30 m tolerances are positional sensitivities,
not acceptance cutoffs or exact overlap geometry.
"""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from harmonization.roads import CLASSES

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review'
PILOTS={'Chicago':['24','28','30','32','76','33'],'SP':['10','30','35','52']}
DISTRICTS={'Chicago':'Chicago/chi_local_2026_09_16_v1/districts.parquet',
           'SP':'SP/sp_prep_2026_09_10_v3/N02/districts.parquet'}
LOCAL={'Chicago':'Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet',
       'SP':'SP/sp_prep_2026_09_10_v3/N04/edges.parquet'}
TOLERANCES=(5,15,30)


def clipped(frame,area):
    selected=frame.iloc[frame.sindex.query(area,predicate='intersects')]
    pieces=shapely.get_parts(shapely.intersection(selected.geometry.values,area))
    return [p for p in pieces if p.geom_type=='LineString' and p.length>0]


def sampled_near_fractions(lines,other,spacing_m=20):
    if not lines or not other:raise ValueError('Empty comparison network')
    points=[];weights=[]
    for line in lines:
        count=max(1,int(np.ceil(line.length/spacing_m)))
        positions=(np.arange(count)+.5)/count
        points.extend(shapely.line_interpolate_point(line,positions,normalized=True))
        weights.extend([line.length/count]*count)
    tree=shapely.STRtree(other)
    _,distance=tree.query_nearest(np.asarray(points,dtype=object),all_matches=False,return_distance=True)
    weight=np.asarray(weights)
    return {t:float(weight[distance<=t].sum()/weight.sum()) for t in TOLERANCES}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for city,ids in PILOTS.items():
        districts=gpd.read_parquet(A/'work/prepared'/DISTRICTS[city])
        source=A/'data'/city/'overture_2026_08_19/segment/part_0000.parquet'
        overture=gpd.read_parquet(source,columns=['id','geometry','subtype','class']).to_crs(districts.crs)
        overture=overture.loc[overture.subtype.eq('road') & overture['class'].isin(CLASSES)].reset_index(drop=True)
        local=gpd.read_parquet(A/'work/prepared'/LOCAL[city])
        if city=='SP':local=local.loc[local.canonical_edge].reset_index(drop=True)
        if local.crs!=districts.crs:raise ValueError('CRS mismatch')
        for id in ids:
            unit=('CHI' if city=='Chicago' else 'SP')+':'+id
            district=districts.loc[districts.district_id.astype(str).str.zfill(2).eq(id)].geometry.item()
            src=clipped(overture,district)
            loc=clipped(local,district)
            src_len=sum(x.length for x in src);loc_len=sum(x.length for x in loc)
            src_near=sampled_near_fractions(src,loc)
            loc_near=sampled_near_fractions(loc,src)
            for tol in TOLERANCES:
                records.append({'unit_id':unit,'tolerance_m':tol,
                                'overture_length_m':src_len,'local_length_m':loc_len,
                                'overture_near_local_fraction':src_near[tol],
                                'local_near_overture_fraction':loc_near[tol],
                                'overture_unmatched_approx_m':src_len*(1-src_near[tol]),
                                'local_unmatched_approx_m':loc_len*(1-loc_near[tol]),
                                'sample_spacing_max_m':20,
                                'reference_role':'city_specific_linework_diagnostic_not_common_input'})
            print(unit,'source',round(src_len),'local',round(loc_len),flush=True)
    pd.DataFrame(records).to_csv(OUT/'paired_linework_alignment.csv',index=False)

if __name__=='__main__':main()
