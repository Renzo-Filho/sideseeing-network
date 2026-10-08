# Method A index (advisor's specification). Factors per unit: C, R and N are counts; H = stations + bus stops;
# V = mean Overture height; L = mean segment length. Each factor is min–max scaled over the 173 units pooled,
# x' = (x − min x) / (max x − min x), and the index is their equal-weight sum, I = C' + R' + H' + V' + N' + L' (0–6).
import pandas as pd

F = ['C', 'R', 'H', 'V', 'N', 'L']
comp = arg[0]
for part in arg[1:]:
    comp = comp.merge(part, on='unit_id', how='left', validate='one_to_one')
assert len(comp) == 173 and comp.unit_id.is_unique
raw = pd.DataFrame({'C': comp.C_count, 'R': comp.R_count, 'H': comp.H_stations + comp.H_bus,
                    'V': comp.V_A_sum / comp.V_A_n, 'N': comp.N_count, 'L': comp.L_sum / comp.N_count})
assert not raw.isna().any().any(), 'every unit needs every factor'
scaled = (raw - raw.min()) / (raw.max() - raw.min())
out = comp[['unit_id', 'name', 'city', 'gross_area_km2']].copy()
for f in F:
    out['raw_' + f], out['scaled_' + f] = raw[f], scaled[f]
out['index'] = scaled.sum(axis=1)
out['rank'] = out['index'].rank(ascending=False, method='min').astype(int)
out['method'] = 'A'
return out.sort_values('rank').reset_index(drop=True)
