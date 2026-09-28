"""Sensitivity of physical-block pilots to dissolved rail corridor widths."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from review_block_barrier_pilots_v3 import rail_source, rail_parts
from review_block_reference_fixtures_v2 import PILOTS, owned_polygons, match_best

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers'
REF=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures'
UNITS={'CHI:28','CHI:32','SP:10','SP:30'}
WIDTHS=(10,20,30)

def main():
    rows=[]
    for city in ('Chicago','SP'):
        roads=gpd.read_parquet(A/'work/prepared'/city/'overture_2026_08_19_review_v1/selected_roads.parquet')
        geo_rail,metric_rail=rail_source(city,roads.crs)
        district_path=next(x[3] for x in PILOTS if x[0]==city)
        districts=gpd.read_parquet(A/'work/prepared'/district_path)
        if city=='SP':districts['unit_id']='SP:'+districts.district_id.astype(str).str.zfill(2)
        for _,unit,local_id,*_ in (x for x in PILOTS if x[0]==city and x[1] in UNITS):
            district=districts.loc[districts.unit_id.eq(unit)].geometry.item()
            extraction=district.buffer(250)
            selected=roads.iloc[roads.sindex.query(extraction,predicate='intersects')]
            street=list(selected.loc[selected.subclass.ne('link')].geometry.values)
            rail=rail_parts(geo_rail,metric_rail,extraction,roads.crs)
            reference=gpd.read_parquet(REF/f'{unit.replace(":","_")}_reference.parquet')
            for width in WIDTHS:
                corridor=shapely.union_all([line.buffer(width/2,cap_style='flat') for line in rail])
                boundary=list(shapely.get_parts(corridor.boundary))
                candidate=owned_polygons(street+boundary,district,extraction,districts,local_id)
                fraction=np.asarray([g.intersection(corridor).area/g.area for g in candidate.geometry])
                land=candidate.loc[fraction<=.5].copy().reset_index(drop=True)
                land['candidate_id']=[f'{unit}:rail_corridor_{width}m:{i:04d}' for i in range(len(land))]
                _,forward=match_best(land,reference,'reference_id')
                _,reverse=match_best(reference,land,'candidate_id')
                land['best_reference_iou']=forward
                land.to_parquet(OUT/f'{unit.replace(":","_")}_rail_corridor_{width}m.parquet')
                rows.append({'unit_id':unit,'corridor_width_m':width,'all_candidate_count':len(candidate),
                             'excluded_corridor_majority':len(candidate)-len(land),'land_candidate_count':len(land),
                             'candidate_share_best_iou_ge_050':float(np.mean(forward>=.5)),
                             'reference_share_best_iou_ge_050':float(np.mean(reverse>=.5)),
                             'status':'diagnostic_only_not_accepted_M3_M4'})
                print(unit,width,len(candidate),len(land),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'rail_corridor_sensitivity.csv',index=False)

if __name__=='__main__':main()
