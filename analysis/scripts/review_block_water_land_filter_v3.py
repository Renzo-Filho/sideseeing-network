"""Evaluate excluding majority-water polygons from saved shoreline variants."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from review_block_reference_fixtures_v2 import match_best, PILOTS

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'analysis'
OUT = A / 'results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v3_barriers'
REF = A / 'results/SP_CHI/harmonization_2026_09_22_full_scope_review/blocks_v2/reference_fixtures'

def main():
    rows=[]
    for _,unit,*_ in PILOTS:
        reference=gpd.read_parquet(REF/f'{unit.replace(":","_")}_reference.parquet')
        for mode in ['no_links_water','no_links_rail_water']:
            source=gpd.read_parquet(OUT/f'{unit.replace(":","_")}_{mode}.parquet')
            land=source.loc[source.water_overlap_fraction.le(.5)].copy().reset_index(drop=True)
            if not len(land):
                raise ValueError(f'{unit}/{mode}: no land candidates')
            _, reverse=match_best(reference,land,'candidate_id')
            scores=land.best_reference_iou.to_numpy()
            rows.append({'unit_id':unit,'boundary_mode':mode+'_land_only',
                         'source_polygon_count':len(source),'removed_majority_water':len(source)-len(land),
                         'candidate_count':len(land),'reference_count':len(reference),
                         'candidate_share_best_iou_ge_050':float(np.mean(scores>=.5)),
                         'reference_share_best_iou_ge_050':float(np.mean(reverse>=.5)),
                         'status':'diagnostic_only_not_accepted_M3_M4'})
            land.to_parquet(OUT/f'{unit.replace(":","_")}_{mode}_land_only.parquet')
    pd.DataFrame(rows).to_csv(OUT/'land_only_sensitivity.csv',index=False)

if __name__=='__main__':main()
