# Harmonized model · standardized profile: the 20 columns of the 12 families as the distance sees them
# (contract sp_chicago_model_v1, primary C6 hybrid scaling; docs/harmonization/MODEL_REPORT.md §3–4).
#  1. Transform (J-5): natural log for ratio-scale amounts, identity for shares, indices and log-ratios.
#  2. Scale (C6 hybrid): z = (t − mean) / SD (population SD), capped at ±3. Same-instrument families are compared on
#     absolute levels (mean and SD over all 173 units); families whose instruments differ by city are compared by
#     position within their own city (mean and SD per city).
#  3. U6 composition: the five city-centred log-ratios pass through unscaled (Aitchison geometry).
import numpy as np
import pandas as pd

LOG = ['m1_km_per_km2', 'ov_m4_wmedian_elongation', 'm7_parcels_per_km2', 'bv_height_built_m', 'u2_jobs_land_km2',
       'u3_acs_land_km2', 'u4_ptai_avg_resident']
ABSOLUTE = ['m1_km_per_km2', 'ov_m3_wmedian_ln_m2', 'ov_m4_wmedian_compactness', 'ov_m4_wmedian_elongation',   # same instrument
            'm6_major_share', 'm7_parcels_per_km2', 'B1_coverage_land', 'u3_acs_land_km2']
RELATIVE = ['u2_jobs_land_km2', 'u4_ptai_avg_resident', 'bv_height_built_m', 'u6_log_intensity',                 # instruments differ
            'p_residential', 'p_industrial', 'p_institutional']
COMPOSITION = ['u6_clr_city_food_drink', 'u6_clr_city_retail', 'u6_clr_city_services_offices', 'u6_clr_city_making_storing',
               'u6_clr_city_institutions']

df = arg[0]
for part in arg[1:]:
    df = df.merge(part, on='unit_id', how='left', validate='one_to_one')
assert len(df) == 173 and set(ABSOLUTE + RELATIVE + COMPOSITION) <= set(df.columns)
df['city'] = np.where(df.unit_id.str.startswith('SP:'), 'SP', 'Chicago')


def z(t):
    return ((t - t.mean()) / t.std(ddof=0)).clip(-3, 3)


out = df[['unit_id', 'city']].copy()
for c in ABSOLUTE + RELATIVE:
    t = np.log(df[c]) if c in LOG else df[c].astype(float)
    out[c] = z(t) if c in ABSOLUTE else t.groupby(df.city).transform(z)
out[COMPOSITION] = df[COMPOSITION]

# Unit names as the other lanes show them (prepared reporting units).
sp = pd.read_parquet(curio_dataset_path("data.sideseeing.sp-districts-prepared"), columns=['district_id', 'nm_distrito_municipal'])
chi = pd.read_parquet(curio_dataset_path("data.sideseeing.chicago-community-areas-prepared"), columns=['unit_id', 'district_name'])
names = {**dict(zip('SP:' + sp.district_id, sp.nm_distrito_municipal)), **dict(zip(chi.unit_id, chi.district_name))}
out.insert(1, 'name', out.unit_id.map(names))
assert out.name.notna().all()
return out.sort_values('unit_id').reset_index(drop=True)
