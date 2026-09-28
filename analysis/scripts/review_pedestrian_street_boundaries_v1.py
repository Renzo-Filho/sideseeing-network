"""Measure the omitted Overture pedestrian class in diagnostic M3/M4 pilots.

H1-H3 M1 includes designated pedestrian streets, whereas the earlier prepared
nine-class road layer used by morphology pilots omits them.
"""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from harmonization.roads import shape_metrics
from review_block_reference_fixtures_v2 import PILOTS, owned_polygons, match_best

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
BASE=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review'
OUT=BASE/'m1_m6_review'
REF=BASE/'blocks_v2/reference_fixtures'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for city in ('Chicago','SP'):
        prepared=gpd.read_parquet(A/'work/prepared'/city/'overture_2026_08_19_review_v1/selected_roads.parquet')
        raw=gpd.read_parquet(A/'data'/city/'overture_2026_08_19/segment/part_0000.parquet',
                             columns=['id','geometry','subtype','class']).to_crs(prepared.crs)
        pedestrian=raw.loc[raw.subtype.eq('road') & raw['class'].eq('pedestrian')].reset_index(drop=True)
        district_path=next(x[3] for x in PILOTS if x[0]==city)
        districts=gpd.read_parquet(A/'work/prepared'/district_path)
        if city=='SP':districts['unit_id']='SP:'+districts.district_id.astype(str).str.zfill(2)
        for _,unit,local_id,*_ in (x for x in PILOTS if x[0]==city):
            district=districts.loc[districts.unit_id.eq(unit)].geometry.item()
            extraction=district.buffer(250)
            src=prepared.iloc[prepared.sindex.query(extraction,predicate='intersects')]
            pedestrian_src=pedestrian.iloc[pedestrian.sindex.query(extraction,predicate='intersects')]
            selected=list(src.loc[src.subclass.ne('link')].geometry.values)
            lines=selected+list(pedestrian_src.geometry.values)
            candidate=owned_polygons(lines,district,extraction,districts,local_id)
            candidate['candidate_id']=[f'{unit}:no_links_plus_pedestrian:{i:04d}' for i in range(len(candidate))]
            reference=gpd.read_parquet(REF/f'{unit.replace(":","_")}_reference.parquet')
            _,forward=match_best(candidate,reference,'reference_id')
            _,reverse=match_best(reference,candidate,'candidate_id')
            metrics=shape_metrics(candidate.geometry.values)
            candidate['best_reference_iou']=forward
            candidate.to_parquet(OUT/f'{unit.replace(":","_")}_no_links_plus_pedestrian.parquet')
            clipped=shapely.intersection(pedestrian_src.geometry.values,district)
            rows.append({'unit_id':unit,'pedestrian_source_segments_in_extraction':len(pedestrian_src),
                         'pedestrian_length_in_unit_m':float(shapely.length(clipped).sum()),
                         'candidate_count':len(candidate),
                         'narrow_under_6m':int((metrics.rectangle_min_width_m<6).sum()),
                         'candidate_share_best_iou_ge_050':float(np.mean(forward>=.5)),
                         'reference_share_best_iou_ge_050':float(np.mean(reverse>=.5)),
                         'status':'diagnostic_only_not_accepted_M3_M4'})
            print(unit,len(pedestrian_src),len(candidate),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'pedestrian_boundary_sensitivity.csv',index=False)

if __name__=='__main__':main()
