# Chicago-only eight-family candidate model: assemble the selected raw matrix.
# arg is [morphology, built form, urban function] from the three selective merges.
import numpy as np
import pandas as pd

ids = [f'CHI:{i:02d}' for i in range(1, 78)]
classes = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary',
           'residential', 'living_street', 'pedestrian', 'unclassified', 'unknown']
m6_columns = ['M6_share_' + name for name in classes]
columns = {
    'M1': ['M1_mapped_street_density_km_km2'],
    'M6': m6_columns,
    'B1': ['B1_coverage_land'],
    'BV': ['BV_net_grid_height_land_m'],
    'U1': ['U1_land_use_entropy_cmap_area8'],
    'U2': ['U2_jobs_density_gross_km2'],
    'U3': ['U3_population_density_gross_km2'],
    'U4': ['U4_bus_supply_weekday_am_400m'],
}
if len(arg) != 3 or [len(group) for group in arg] != [2, 2, 4]:
    raise ValueError('Expected selected model inputs [M1,M6], [B1,BV], [U1,U2,U3,U4]')
if not isinstance(arg[0][0], (tuple, list)) or len(arg[0][0]) != 2:
    raise ValueError('M1 must return (summary, class_lengths)')
sources = {
    'M1': arg[0][0][0], 'M6': arg[0][1],
    'B1': arg[1][0], 'BV': arg[1][1],
    'U1': arg[2][0], 'U2': arg[2][1],
    'U3': arg[2][2], 'U4': arg[2][3],
}
raw = pd.DataFrame({'unit_id': ids})
for family, frame in sources.items():
    required = ['unit_id', 'status'] + columns[family]
    if not isinstance(frame, pd.DataFrame) or not set(required).issubset(frame.columns):
        raise ValueError(f'{family}: expected DataFrame with {required}')
    if len(frame) != 77 or frame.unit_id.isna().any() or frame.unit_id.duplicated().any():
        raise ValueError(f'{family}: expected 77 unique non-null IDs')
    if set(frame.unit_id) != set(ids):
        raise ValueError(f'{family}: Community Area IDs do not match CHI:01–CHI:77')
    if not frame.status.astype(str).str.startswith('constructed_chicago').all():
        raise ValueError(f'{family}: selected feature has non-constructed status')
    selected = frame[['unit_id'] + columns[family]].copy()
    try:
        numeric = selected[columns[family]].astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{family}: selected value is not numeric') from exc
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f'{family}: selected value is null or nonfinite')
    selected[columns[family]] = numeric
    raw = raw.merge(selected, on='unit_id', how='left', validate='one_to_one', sort=False)

if len(raw) != 77 or raw.unit_id.tolist() != ids:
    raise ValueError('Raw matrix is not ordered CHI:01–CHI:77')
if (raw[m6_columns].to_numpy() < 0).any() or not np.allclose(
        raw[m6_columns].sum(axis=1), 1, rtol=0, atol=1e-8):
    raise ValueError('M6 shares must be nonnegative and sum to one')
for family in ['M1', 'BV', 'U2', 'U3', 'U4']:
    if (raw[columns[family][0]] < 0).any():
        raise ValueError(f'{family}: log1p input is negative')
for family in ['B1', 'U1']:
    if not raw[columns[family][0]].between(0, 1).all():
        raise ValueError(f'{family}: fraction must lie in [0,1]')
return raw
