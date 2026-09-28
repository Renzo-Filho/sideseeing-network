"""Reproducible paired M1/M6 scope and local-baseline audit."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'analysis'
OUT=A/'results/SP_CHI/harmonization_2026_09_22_full_scope_review/m1_m6_review'
SOURCE=A/'results/SP_CHI/harmonization_2026_09_22_h1_h3/roads/paired_road_candidates.csv'
LOCAL={
 'CHI':(A/'results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv','street_density_municipal_km_km2'),
 'SP':(A/'results/SP/tables/attributes_wide.csv','street_density_km_km2'),
}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=pd.read_csv(SOURCE)
    if len(source)!=173 or source.unit_id.nunique()!=173:raise ValueError('Incomplete paired source table')
    share_cols=[x for x in source if x.startswith('M6_share_')]
    if len(share_cols)!=10:raise ValueError('Unexpected M6 class count')
    if not np.allclose(source[share_cols].sum(axis=1),1,atol=1e-12):raise ValueError('Class shares do not sum to one')
    if not np.allclose(source.road_length_m/1000/(source.gross_area_m2/1e6),
                       source.M1_mapped_street_density_km_km2,atol=1e-12):
        raise ValueError('M1 density not reconstructed')
    units=[];summary=[]
    for city,(path,col) in LOCAL.items():
        local=pd.read_csv(path)
        if city=='SP':local['unit_id']='SP:'+local.district_id.astype(str).str.zfill(2)
        paired=source.loc[source.unit_id.str.startswith(city+':')].merge(local[['unit_id',col]],on='unit_id',validate='one_to_one')
        paired['local_density_km_km2']=paired[col]
        paired['overture_to_local_ratio']=paired.M1_mapped_street_density_km_km2/paired.local_density_km_km2
        paired['outside_15pct_local_baseline_band']=~paired.overture_to_local_ratio.between(.85,1.15)
        paired[['unit_id','M1_mapped_street_density_km_km2','local_density_km_km2',
                'overture_to_local_ratio','outside_15pct_local_baseline_band','M6_share_unknown',
                'M6_share_unclassified','access_rule_length_share']].to_csv(OUT/f'{city}_unit_scope.csv',index=False)
        units.append(paired)
        summary.append({'city':city,'units':len(paired),
                        'm1_pearson_local':paired.M1_mapped_street_density_km_km2.corr(paired.local_density_km_km2),
                        'm1_spearman_local':paired.M1_mapped_street_density_km_km2.corr(paired.local_density_km_km2,method='spearman'),
                        'm1_median_overture_to_local_ratio':paired.overture_to_local_ratio.median(),
                        'm1_ratio_p10':paired.overture_to_local_ratio.quantile(.1),
                        'm1_ratio_p90':paired.overture_to_local_ratio.quantile(.9),
                        'm1_units_outside_15pct_band':int(paired.outside_15pct_local_baseline_band.sum()),
                        'm6_unknown_length_share_city':np.average(paired.M6_share_unknown,weights=paired.road_length_m),
                        'm6_unclassified_length_share_city':np.average(paired.M6_share_unclassified,weights=paired.road_length_m),
                        'm6_unknown_max_unit':paired.M6_share_unknown.max(),
                        'm6_unclassified_max_unit':paired.M6_share_unclassified.max(),
                        'access_rule_presence_median_unit':paired.access_rule_length_share.median(),
                        'status':'candidate_semantic_review_no_model_fit'})
    pd.DataFrame(summary).to_csv(OUT/'paired_m1_m6_scope_summary.csv',index=False)
    print(pd.DataFrame(summary)[['city','units','m1_spearman_local','m1_median_overture_to_local_ratio',
                                 'm1_units_outside_15pct_band']].to_string(index=False))

if __name__=='__main__':main()
