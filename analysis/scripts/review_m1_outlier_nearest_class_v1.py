"""Classify nearest raw Overture roads to sampled unmatched local M1 lines."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from review_m1_outlier_classes_v1 import SPECS,parts_for

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review'

def sample(line,spacing=20):
    count=max(1,int(np.ceil(line.length/spacing)))
    pts=shapely.line_interpolate_point(line,(np.arange(count)+.5)/count,normalized=True)
    return pts,np.full(count,line.length/count)

def main():
    rows=[]
    for city,id,dp,lp,group in SPECS:
        districts=gpd.read_parquet(A/'work/prepared'/dp)
        district=districts.loc[districts.district_id.astype(str).str.zfill(2).eq(id)].geometry.item()
        raw=gpd.read_parquet(A/'data'/city/'overture_2026_08_19/segment/part_0000.parquet',
                             columns=['geometry','subtype','class']).to_crs(districts.crs)
        raw=raw.loc[raw.subtype.eq('road')]
        raw=raw.iloc[raw.sindex.query(district.buffer(30),predicate='intersects')].reset_index(drop=True)
        tree=shapely.STRtree(raw.geometry.values)
        local=gpd.read_parquet(A/'work/prepared'/lp)
        if city=='SP':local=local.loc[local.canonical_edge]
        local=local.iloc[local.sindex.query(district,predicate='intersects')]
        for category,subset in local.groupby(group,dropna=False):
            points=[];weights=[]
            for line in parts_for(subset,district):
                pts,w=sample(line)
                points.extend(pts);weights.extend(w)
            if not points:continue
            indexes,distance=tree.query_nearest(np.asarray(points,dtype=object),all_matches=False,return_distance=True)
            nearest=raw['class'].to_numpy()[indexes[1]]
            nearest=np.where(distance<=15,nearest,'farther_than_15m')
            frame=pd.DataFrame({'nearest_class':nearest,'length_m':weights})
            for cls,g in frame.groupby('nearest_class'):
                rows.append({'unit_id':('CHI' if city=='Chicago' else 'SP')+':'+id,
                             'local_class':str(category),'nearest_overture_class':cls,
                             'represented_local_length_m':g.length_m.sum(),
                             'sample_spacing_max_m':20,'tolerance_m':15,
                             'reference_role':'city_specific_nearest_class_diagnostic_not_common_input'})
            print(city,id,category,len(points),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'outlier_nearest_raw_class.csv',index=False)

if __name__=='__main__':main()
