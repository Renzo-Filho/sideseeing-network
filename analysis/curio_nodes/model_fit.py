# Fit Chicago-only v0 transforms on the 77 Community Areas.
# arg is the selected raw DataFrame from the preceding node.
import numpy as np
import pandas as pd

raw = arg.copy()
ids = [f'CHI:{i:02d}' for i in range(1, 78)]
if not isinstance(raw, pd.DataFrame) or raw.unit_id.tolist() != ids:
    raise ValueError('Expected ordered 77-area raw feature matrix')
scalar = {
    'M1': ('M1_mapped_street_density_km_km2', 'log1p'),
    'B1': ('B1_coverage_land', 'identity'),
    'BV': ('BV_net_grid_height_land_m', 'log1p'),
    'U1': ('U1_land_use_entropy_cmap_area8', 'identity'),
    'U2': ('U2_jobs_density_gross_km2', 'log1p'),
    'U3': ('U3_population_density_gross_km2', 'log1p'),
    'U4': ('U4_bus_supply_weekday_am_400m', 'log1p'),
}
scaled = pd.DataFrame({'unit_id': ids})
parameters = []
for family, (column, transform) in scalar.items():
    x = raw[column].to_numpy(dtype=float)
    if not np.isfinite(x).all() or (transform == 'log1p' and (x < 0).any()):
        raise ValueError(f'{family}: invalid input for {transform}')
    t = np.log1p(x) if transform == 'log1p' else x
    center = float(np.median(t))
    iqr = float(np.quantile(t, .75) - np.quantile(t, .25))
    sd = float(np.std(t, ddof=0))
    fallback = iqr <= 1e-12
    scale = sd if fallback else iqr
    if not np.isfinite(scale) or scale <= 1e-12:
        raise ValueError(f'{family}: zero or invalid fitted scale')
    scaled['z_' + family] = (t - center) / scale
    parameters.append({'kind': 'scalar', 'family': family, 'column': column,
                       'transform': transform, 'center': center, 'iqr': iqr,
                       'sd_ddof0': sd, 'scale': scale, 'sd_fallback': fallback})

m6_columns = ['M6_share_' + name for name in
              ['motorway', 'trunk', 'primary', 'secondary', 'tertiary',
               'residential', 'living_street', 'pedestrian', 'unclassified', 'unknown']]
shares = raw[m6_columns].to_numpy(dtype=float)
if not np.isfinite(shares).all() or (shares < 0).any() or not np.allclose(
        shares.sum(axis=1), 1, rtol=0, atol=1e-8):
    raise ValueError('Invalid M6 composition')
for i, column in enumerate(m6_columns):
    scaled['sqrt_' + column] = np.sqrt(shares[:, i])
parameters.append({'kind': 'composition', 'family': 'M6',
                   'column': ','.join(m6_columns), 'transform': 'square_root'})
if not np.isfinite(scaled.drop(columns='unit_id').to_numpy()).all():
    raise ValueError('Nonfinite fitted coordinates')
return (raw, scaled, pd.DataFrame(parameters))
