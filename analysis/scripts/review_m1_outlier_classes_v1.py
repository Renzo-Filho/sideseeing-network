"""Attribute city-local M1 linework gaps by published local road class."""
from pathlib import Path
import geopandas as gpd
import pandas as pd
import shapely
from harmonization.roads import CLASSES
from review_m1_geometry_alignment_v1 import sampled_near_fractions

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review'
SPECS=[('Chicago','76','Chicago/chi_local_2026_09_16_v1/districts.parquet',
        'Chicago/chi_local_2026_09_16_v1/eligible_roads.parquet','class'),
       ('SP','52','SP/sp_prep_2026_09_10_v3/N02/districts.parquet',
        'SP/sp_prep_2026_09_10_v3/N04/edges.parquet','class_model')]

def parts_for(frame,area):
    g=shapely.get_parts(shapely.intersection(frame.geometry.values,area))
    return [x for x in g if x.geom_type=='LineString' and x.length>0]

def main():
    rows=[]
    for city,id,dp,lp,group in SPECS:
        d=gpd.read_parquet(A/'work/prepared'/dp)
        district=d.loc[d.district_id.astype(str).str.zfill(2).eq(id)].geometry.item()
        source=gpd.read_parquet(A/'data'/city/'overture_2026_08_19/segment/part_0000.parquet',columns=['geometry','subtype','class']).to_crs(d.crs)
        source=source.loc[source.subtype.eq('road') & source['class'].isin(CLASSES)]
        source=source.iloc[source.sindex.query(district,predicate='intersects')]
        source_lines=parts_for(source,district)
        local=gpd.read_parquet(A/'work/prepared'/lp)
        if city=='SP':local=local.loc[local.canonical_edge]
        local=local.iloc[local.sindex.query(district,predicate='intersects')]
        for category,subset in local.groupby(group,dropna=False):
            lines=parts_for(subset,district)
            if not lines:continue
            total=sum(x.length for x in lines)
            near=sampled_near_fractions(lines,source_lines)[15]
            rows.append({'unit_id':('CHI' if city=='Chicago' else 'SP')+':'+id,
                         'local_class':str(category),'local_length_m':total,
                         'local_near_overture_15m_fraction':near,
                         'local_unmatched_approx_m':total*(1-near),
                         'sample_spacing_max_m':20,
                         'reference_role':'city_specific_class_diagnostic_not_common_input'})
            print(city,id,category,round(total),round(near,3),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'outlier_local_class_gaps.csv',index=False)

if __name__=='__main__':main()
