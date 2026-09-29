"""Cross-artifact checks for local rail and matched M1/M6 scope review."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
BASE=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review'
OUT=BASE/'m1_m6_review'

def main():
    full=pd.read_csv(A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/roads/paired_road_candidates.csv')
    assert len(full)==173 and full.unit_id.nunique()==173
    share=[x for x in full if x.startswith('M6_share_')]
    assert len(share)==10 and np.allclose(full[share].sum(axis=1),1)
    assert np.allclose(full.road_length_m/1000/(full.gross_area_m2/1e6),
                       full.M1_mapped_street_density_km_km2)
    alignment=pd.read_csv(OUT/'paired_linework_alignment.csv')
    assert len(alignment)==30 and alignment.unit_id.nunique()==10
    for field in ['overture_near_local_fraction','local_near_overture_fraction']:
        assert alignment[field].between(0,1).all()
        wide=alignment.pivot(index='unit_id',columns='tolerance_m',values=field)
        assert ((wide[5]<=wide[15]) & (wide[15]<=wide[30])).all()
    local=pd.read_csv(OUT/'outlier_local_class_gaps.csv',keep_default_na=False)
    nearest=pd.read_csv(OUT/'outlier_nearest_raw_class.csv',keep_default_na=False)
    left=local.groupby(['unit_id','local_class']).local_length_m.sum().sort_index()
    right=nearest.groupby(['unit_id','local_class']).represented_local_length_m.sum().sort_index()
    assert left.index.equals(right.index) and np.allclose(left.values,right.values)
    ped=pd.read_csv(OUT/'pedestrian_boundary_sensitivity.csv')
    assert len(ped)==8 and ped.unit_id.nunique()==8
    rail=pd.read_csv(BASE/'blocks_v4_local_rail/paired_local_rail_envelope_sensitivity.csv')
    assert len(rail)==8 and rail.unit_id.nunique()==8
    assert (rail.all_candidate_count==rail.removed_mask_majority+rail.land_candidate_count).all()
    print('Validated 173 M1/M6 rows, 30 positional comparisons, class-gap mass, 8 pedestrian pilots and 8 local-rail pilots')

if __name__=='__main__':main()
