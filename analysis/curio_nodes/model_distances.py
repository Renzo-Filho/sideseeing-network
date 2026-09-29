# Chicago-only eight-family candidate distances; three domains have equal budgets.
# arg is (raw_features, fitted_coordinates, scalar_parameters).
import numpy as np
import pandas as pd

if not isinstance(arg, (tuple, list)) or len(arg) != 3:
    raise ValueError('Expected (raw_features, fitted_coordinates, parameters)')
raw, scaled, scalar_parameters = arg
ids = [f'CHI:{i:02d}' for i in range(1, 78)]
if raw.unit_id.tolist() != ids or scaled.unit_id.tolist() != ids:
    raise ValueError('Raw and scaled rows must have identical CHI:01–CHI:77 order')
weights = {'M1': 1/6, 'M6': 1/6, 'B1': 1/6, 'BV': 1/6,
           'U1': 1/12, 'U2': 1/12, 'U3': 1/12, 'U4': 1/12}
if not np.isclose(sum(weights.values()), 1):
    raise ValueError('Family weights do not sum to one')
upper = np.triu_indices(77, 1)
squared = {}
for family in weights:
    if family == 'M6':
        columns = [name for name in scaled if name.startswith('sqrt_M6_share_')]
        if len(columns) != 10:
            raise ValueError('M6 must have ten square-root composition columns')
        x = scaled[columns].to_numpy(dtype=float)
        squared[family] = .5 * np.square(x[:, None, :] - x[None, :, :]).sum(axis=2)
    else:
        x = scaled['z_' + family].to_numpy(dtype=float)
        squared[family] = np.square(x[:, None] - x[None, :])

contributions = {}
family_rows = []
calibrations = {}
for family, weight in weights.items():
    positive = squared[family][upper]
    positive = positive[positive > 1e-15]
    if not len(positive):
        raise ValueError(f'{family}: no positive pair distances')
    calibration = float(np.median(positive))
    if not np.isfinite(calibration) or calibration <= 1e-15:
        raise ValueError(f'{family}: invalid pair-distance calibration')
    calibrations[family] = calibration
    contributions[family] = weight * squared[family] / calibration
    family_rows.append({'kind': 'family_calibration', 'family': family,
                        'weight': weight, 'calibration': calibration})

total_squared = sum(contributions.values())
if not np.isfinite(total_squared).all() or (total_squared < -1e-12).any():
    raise ValueError('Invalid total squared distances')
distances = np.sqrt(np.maximum(total_squared, 0))
np.fill_diagonal(distances, 0)
if not np.allclose(distances, distances.T, rtol=0, atol=1e-12):
    raise ValueError('Distance matrix is not symmetric')
if not np.allclose(sum(contributions.values())[upper], distances[upper]**2,
                   rtol=1e-10, atol=1e-10):
    raise ValueError('Family contributions do not reconstruct squared distance')
pairwise = pd.DataFrame({'unit_id_a': np.asarray(ids)[upper[0]],
                         'unit_id_b': np.asarray(ids)[upper[1]],
                         'distance': distances[upper]})
for family in weights:
    pairwise['squared_contribution_' + family] = contributions[family][upper]
pairwise.insert(0, 'model_id', 'chicago_only_8_family_candidate_v0')
if len(pairwise) != 2926:
    raise ValueError('Expected 2,926 unordered Community Area pairs')
parameters = pd.concat([scalar_parameters, pd.DataFrame(family_rows)],
                       ignore_index=True, sort=False)
parameters.insert(0, 'model_id', 'chicago_only_8_family_candidate_v0')
distance_matrix = pd.DataFrame(distances, index=ids, columns=ids)
distance_matrix.index.name = 'unit_id'
distance_matrix.insert(0, 'unit_id', ids)

# This is the exact weighted Euclidean embedding used by the Sao Paulo PCA
# calculation. Its full-space distances must reproduce the family metric.
embedding = pd.DataFrame({'unit_id': ids})
for family, weight in weights.items():
    if family == 'M6':
        columns = [name for name in scaled if name.startswith('sqrt_M6_share_')]
        factor = .5
    else:
        columns = ['z_' + family]
        factor = 1.
    multiplier = np.sqrt(weight * factor / calibrations[family])
    for column in columns:
        embedding['coord_' + column] = scaled[column].to_numpy(dtype=float) * multiplier
coordinates = embedding.drop(columns='unit_id').to_numpy(dtype=float)
full_embedding_distance = np.sqrt(np.square(
    coordinates[:, None, :] - coordinates[None, :, :]).sum(axis=2))
if not np.allclose(full_embedding_distance, distances, rtol=1e-10, atol=1e-10):
    raise ValueError('Weighted embedding does not reproduce family distances')
return (raw, pairwise, parameters, distance_matrix, embedding)
