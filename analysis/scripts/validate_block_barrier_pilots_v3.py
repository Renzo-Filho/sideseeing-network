"""Independent arithmetic and lineage checks for paired barrier diagnostics."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
BASE=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review'
OUT=BASE/'blocks_v3_barriers'

def main():
    p=pd.read_csv(OUT/'paired_barrier_sensitivity.csv')
    l=pd.read_csv(OUT/'land_only_sensitivity.csv')
    r=pd.read_csv(OUT/'rail_corridor_sensitivity.csv')
    prior=pd.read_csv(BASE/'blocks_v2/paired_boundary_sensitivity.csv')
    assert len(p)==32 and p.unit_id.nunique()==8 and p.groupby('unit_id').boundary_mode.nunique().eq(4).all()
    assert len(l)==16 and l.unit_id.nunique()==8 and l.groupby('unit_id').boundary_mode.nunique().eq(2).all()
    assert len(r)==12 and r.unit_id.nunique()==4 and r.groupby('unit_id').corridor_width_m.nunique().eq(3).all()
    current=p.loc[p.boundary_mode.eq('no_links')].set_index('unit_id').candidate_count
    old=prior.loc[prior.boundary_mode.eq('without_links')].set_index('unit_id').whole_enclosures_owned
    assert current.equals(old.reindex(current.index))
    assert (l.source_polygon_count==l.candidate_count+l.removed_majority_water).all()
    assert (r.all_candidate_count==r.land_candidate_count+r.excluded_corridor_majority).all()
    for frame in (p,l,r):
        for col in ['candidate_share_best_iou_ge_050','reference_share_best_iou_ge_050']:
            assert frame[col].between(0,1).all()
    for row in l.itertuples():
        path=OUT/f'{row.unit_id.replace(":","_")}_{row.boundary_mode}.parquet'
        d=gpd.read_parquet(path)
        assert len(d)==row.candidate_count
        assert d.water_overlap_fraction.le(.5).all()
        assert np.isfinite(d.geometry.area).all()
    print('Validated 32 barrier rows, 16 land-only rows, 12 corridor rows, original no-link counts and saved land polygons')

if __name__=='__main__':main()
