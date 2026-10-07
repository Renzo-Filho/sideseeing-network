# Harmonized model · distance between every pair of units (run R1: equal family budgets; J-7, J-8).
# Each family is one block (U6 is two: intensity and composition, half its budget each). For block b with c_b columns,
#   m_b(d,e) = (1/c_b) Σ_j (x_dj − x_ej)²,   divided by β_b, its median positive value over all 14,878 pairs.
#   D(d,e)  = sqrt( Σ_b w_f s_b m_b/β_b  /  Σ_{b available for d,e} w_f s_b ),   w_f = 1/12.
# Pairs with a missing family (U1 for O'Hare, Marsilac, Parelheiros) use the families both units have.
# Output: one row per ordered pair (29,756 rows): the distance, the other unit's rank, and each family's part of D².
import numpy as np
import pandas as pd

FAMILIES = {'M1': ['m1_km_per_km2'], 'M3': ['ov_m3_wmedian_ln_m2'], 'M4': ['ov_m4_wmedian_compactness', 'ov_m4_wmedian_elongation'],
            'M6': ['m6_major_share'], 'M7': ['m7_parcels_per_km2'], 'B1': ['B1_coverage_land'], 'BV': ['bv_height_built_m'],
            'U2': ['u2_jobs_land_km2'], 'U3': ['u3_acs_land_km2'], 'U4': ['u4_ptai_avg_resident'],
            'U6': [['u6_log_intensity'], ['u6_clr_city_food_drink', 'u6_clr_city_retail', 'u6_clr_city_services_offices',
                                          'u6_clr_city_making_storing', 'u6_clr_city_institutions']],
            'U1': ['p_residential', 'p_industrial', 'p_institutional']}
BUDGET = 1 / len(FAMILIES)

p = arg.sort_values('unit_id').reset_index(drop=True)
n = len(p)
num, den, part = np.zeros((n, n)), np.zeros((n, n)), {}
for fam, cols in FAMILIES.items():
    blocks = cols if isinstance(cols[0], list) else [cols]
    part[fam] = np.zeros((n, n))
    for b in blocks:
        X = p[b].to_numpy(float)
        m = np.square(X[:, None, :] - X[None, :, :]).mean(axis=2)          # NaN where either unit lacks the family
        upper = m[np.triu_indices(n, 1)]
        beta = np.median(upper[~np.isnan(upper) & (upper > 0)])
        w = BUDGET / len(blocks)
        ok = ~np.isnan(m)
        num += w * np.where(ok, m / beta, 0)
        den += w * ok
        part[fam] += w * np.where(ok, m / beta, 0)
D = np.sqrt(num / den)
i, j = np.where(~np.eye(n, dtype=bool))
out = pd.DataFrame({'unit_id': p.unit_id.values[i], 'name': p.name.values[i], 'city': p.city.values[i],
                    'other_id': p.unit_id.values[j], 'other_name': p.name.values[j], 'other_city': p.city.values[j], 'distance': D[i, j]})
for fam in FAMILIES:
    out['d2_' + fam] = (part[fam] / den)[i, j]                             # family parts sum to distance²
out['rank'] = out.groupby('unit_id').distance.rank(method='min').astype(int)
out['rank_in_city'] = out.groupby(['unit_id', 'other_city']).distance.rank(method='min').astype(int)
return out.sort_values(['unit_id', 'distance']).reset_index(drop=True)
