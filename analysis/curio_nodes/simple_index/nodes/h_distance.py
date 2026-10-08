# Harmonized model · distance between every pair of units (sp_chicago_model_v2, run R1; J-7, J-8).
# Each family is one block (U6 is two: intensity and composition, sharing its budget). For block b with columns j,
#   m_b(d,e) = Σ_j v_j (x_dj − x_ej)² / Σ_j v_j,   divided by β_b, its median positive value over all 14,878 pairs.
#   D(d,e)  = sqrt( Σ_b w_f s_b m_b/β_b  /  Σ_{b available for d,e} w_f s_b ).
# Pairs with a missing family (U1 for O'Hare, Marsilac, Parelheiros) use the families both units have.
# Output: one row per ordered pair (29,756 rows): the distance, the other unit's rank, and each family's part of D².

# Weights you can change. The published fit leaves both empty (every family and every column weighs 1).
FAMILY_WEIGHTS = {}   # a family's budget, e.g. {'U1': 2}: U1 counts twice as much as each other family
COLUMN_WEIGHTS = {}   # a column inside its family, e.g. {'p_commerce': 2}: commerce counts twice each other U1 share;
                      # 0 drops the column. β_b is recomputed on the reweighted block, so these change only the inner mix.
                      # The five U6 log-ratios are one Aitchison composition and are not reweighted.
import numpy as np
import pandas as pd

FAMILIES = {'M1': ['m1_km_per_km2'], 'M3': ['ov_m3_wmedian_ln_m2'], 'M4': ['ov_m4_wmedian_compactness', 'ov_m4_wmedian_elongation'],
            'M6': ['m6_major_share'], 'M7': ['m7_parcels_per_km2'], 'B1': ['B1_coverage_land'], 'BV': ['bv_height_built_m'],
            'U2': ['u2_jobs_land_km2'], 'U3': ['u3_acs_land_km2'], 'U4': ['u4_ptai_avg_resident'],
            'U6': [['u6_log_intensity'], ['u6_clr_city_food_drink', 'u6_clr_city_retail', 'u6_clr_city_services_offices',
                                          'u6_clr_city_making_storing', 'u6_clr_city_institutions']],
            'U1': ['p_residential', 'p_commerce', 'p_industrial', 'p_institutional']}
COMPOSITION = FAMILIES['U6'][1]

p = arg.sort_values('unit_id').reset_index(drop=True)
n = len(p)
num, den, part = np.zeros((n, n)), np.zeros((n, n)), {}
for fam, cols in FAMILIES.items():
    blocks = []
    for b in (cols if isinstance(cols[0], list) else [cols]):
        v = np.array([1.0 if c in COMPOSITION else float(COLUMN_WEIGHTS.get(c, 1)) for c in b])
        if v.sum() <= 0:
            continue                                                        # every column dropped: the block leaves
        X = p[[c for c, w in zip(b, v) if w > 0]].to_numpy(float)
        v = v[v > 0]
        m = (np.square(X[:, None, :] - X[None, :, :]) * v).sum(axis=2) / v.sum()   # NaN where either unit lacks the family
        upper = m[np.triu_indices(n, 1)]
        blocks.append(m / np.median(upper[~np.isnan(upper) & (upper > 0)]))
    part[fam] = np.zeros((n, n))
    for m in blocks:
        w = float(FAMILY_WEIGHTS.get(fam, 1)) / len(blocks)
        ok = ~np.isnan(m)
        num += w * np.where(ok, m, 0)
        den += w * ok
        part[fam] += w * np.where(ok, m, 0)
D = np.sqrt(num / den)
i, j = np.where(~np.eye(n, dtype=bool))
out = pd.DataFrame({'unit_id': p.unit_id.values[i], 'name': p.name.values[i], 'city': p.city.values[i],
                    'other_id': p.unit_id.values[j], 'other_name': p.name.values[j], 'other_city': p.city.values[j], 'distance': D[i, j]})
for fam in FAMILIES:
    out['d2_' + fam] = (part[fam] / den)[i, j]                             # family parts sum to distance²
out['rank'] = out.groupby('unit_id').distance.rank(method='min').astype(int)
out['rank_in_city'] = out.groupby(['unit_id', 'other_city']).distance.rank(method='min').astype(int)
return out.sort_values(['unit_id', 'distance']).reset_index(drop=True)
