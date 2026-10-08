# Method B index (corrected). Counts are divided by land area: C/Land, R/Land, H/Land, N/Land per km²;
# V = GHSL built volume / built surface; L = mean segment length (as in A). Scaling and equal-weight sum as in A.
import pandas as pd

F = ['C', 'R', 'H', 'V', 'N', 'L']
comp = arg[0]
for part in arg[1:]:
    comp = comp.merge(part, on='unit_id', how='left', validate='one_to_one')
assert len(comp) == 173 and comp.unit_id.is_unique
land = comp.land_km2
raw = pd.DataFrame({'C': comp.C_count / land, 'R': comp.R_count / land, 'H': (comp.H_stations + comp.H_bus) / land,
                    'V': comp.V_B_num / comp.V_B_den, 'N': comp.N_count / land, 'L': comp.L_sum / comp.N_count})
assert not raw.isna().any().any(), 'every unit needs every factor'
scaled = (raw - raw.min()) / (raw.max() - raw.min())
out = comp[['unit_id', 'name', 'city', 'land_km2']].copy()
for f in F:
    out['raw_' + f], out['scaled_' + f] = raw[f], scaled[f]
out['index'] = scaled.sum(axis=1)
out['rank'] = out['index'].rank(ascending=False, method='min').astype(int)
out['method'] = 'B'
return out.sort_values('rank').reset_index(drop=True)
