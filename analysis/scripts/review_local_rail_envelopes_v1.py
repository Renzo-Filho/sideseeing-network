"""Use city-local rail polygons as validation of paired block boundary candidates.

Chicago CMAP LUI 1511 is rail ROW; São Paulo's area_influencia_trem is
labelled influence/domain and is not assumed to be an equivalent ROW layer.
Neither local mask enters a common model measurement.
"""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from harmonization.roads import shape_metrics
from review_block_reference_fixtures_v2 import PILOTS, owned_polygons, match_best

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
BASE=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review'
OUT=BASE/'blocks_v4_local_rail'
REF=BASE/'blocks_v2/reference_fixtures'

def local_rail(city,crs):
    if city=='Chicago':
        p=A/'data/Chicago/LUI_2023_view_332920193481040239.gpkg'
        g=pyogrio.read_dataframe(p,where="LANDUSE = '1511'",columns=['LANDUSE','FAC_NAME'])
    else:
        p=A/'data/SP/Cadastro e Vias/area_influencia_trem.gpkg'
        g=pyogrio.read_dataframe(p)
    return g.to_crs(crs),p

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for city in ('Chicago','SP'):
        roads=gpd.read_parquet(A/'work/prepared'/city/'overture_2026_08_19_review_v1/selected_roads.parquet')
        masks,source=local_rail(city,roads.crs)
        district_path=next(x[3] for x in PILOTS if x[0]==city)
        districts=gpd.read_parquet(A/'work/prepared'/district_path)
        if city=='SP':districts['unit_id']='SP:'+districts.district_id.astype(str).str.zfill(2)
        for _,unit,local_id,*_ in (x for x in PILOTS if x[0]==city):
            district=districts.loc[districts.unit_id.eq(unit)].geometry.item()
            extraction=district.buffer(250)
            selected=roads.iloc[roads.sindex.query(extraction,predicate='intersects')]
            street=list(selected.loc[selected.subclass.ne('link')].geometry.values)
            nearby=masks.iloc[masks.sindex.query(extraction,predicate='intersects')]
            rail=shapely.union_all(shapely.make_valid(nearby.geometry.values)) if len(nearby) else shapely.GeometryCollection()
            boundary=list(shapely.get_parts(rail.boundary))
            candidate=owned_polygons(street+boundary,district,extraction,districts,local_id)
            rail_fraction=np.asarray([g.intersection(rail).area/g.area for g in candidate.geometry])
            land=candidate.loc[rail_fraction<=.5].copy().reset_index(drop=True)
            land['candidate_id']=[f'{unit}:local_rail_envelope:{i:04d}' for i in range(len(land))]
            reference=gpd.read_parquet(REF/f'{unit.replace(":","_")}_reference.parquet')
            _,forward=match_best(land,reference,'reference_id')
            _,reverse=match_best(reference,land,'candidate_id')
            land['best_reference_iou']=forward
            land.to_parquet(OUT/f'{unit.replace(":","_")}_candidate.parquet')
            metrics=shape_metrics(land.geometry.values)
            rows.append({'unit_id':unit,'local_mask_source':str(source.relative_to(ROOT)),
                         'local_mask_role':'CMAP_1511_rail_ROW' if city=='Chicago' else 'SP_rail_influence_or_domain_ambiguous',
                         'mask_features_in_extraction':len(nearby),
                         'mask_area_in_unit_m2':rail.intersection(district).area,
                         'mask_boundary_parts':len(boundary),
                         'all_candidate_count':len(candidate),
                         'removed_mask_majority':len(candidate)-len(land),
                         'land_candidate_count':len(land),
                         'narrow_under_6m':int((metrics.rectangle_min_width_m<6).sum()),
                         'candidate_share_best_iou_ge_050':float(np.mean(forward>=.5)),
                         'reference_share_best_iou_ge_050':float(np.mean(reverse>=.5)),
                         'status':'city_specific_validation_only_not_common_M3_M4_input'})
            print(unit,len(nearby),len(candidate),len(land),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'paired_local_rail_envelope_sensitivity.csv',index=False)

if __name__=='__main__':main()
