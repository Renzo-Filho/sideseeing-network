# Chicago-only model application: the Sao Paulo 90%-variance PCA distance rule.
# arg is (raw, baseline_pairs, baseline_parameters, baseline_matrix, embedding).
import numpy as np
import pandas as pd

if not isinstance(arg, (tuple, list)) or len(arg) != 5:
    raise ValueError('Expected five outputs from the weighted distance node')
raw, baseline_pairs, baseline_parameters, baseline_matrix, embedding = arg
ids = [f'CHI:{i:02d}' for i in range(1, 78)]
if not isinstance(raw, pd.DataFrame) or raw.unit_id.tolist() != ids:
    raise ValueError('Raw model identities differ from the PCA cohort')
if not isinstance(embedding, pd.DataFrame) or embedding.unit_id.tolist() != ids:
    raise ValueError('Expected the ordered 77-area weighted embedding')
if not baseline_matrix.index.tolist() == ids or not baseline_matrix.columns.tolist() == ids:
    raise ValueError('Baseline matrix identities differ from the embedding')
if not isinstance(baseline_pairs, pd.DataFrame) or len(baseline_pairs) != 2926:
    raise ValueError('Expected 2,926 baseline pairs')
if not isinstance(baseline_parameters, pd.DataFrame) or len(baseline_parameters) != 16:
    raise ValueError('Expected the fitted transforms and family calibrations')
coordinate_names = [name for name in embedding if name.startswith('coord_')]
if len(coordinate_names) != 17:
    raise ValueError('Expected 17 weighted coordinates from eight families')
x = embedding[coordinate_names].to_numpy(dtype=float)
if x.shape != (77, 17) or not np.isfinite(x).all():
    raise ValueError('Weighted embedding is malformed or nonfinite')

# Identical to model_analysis.py: center the calibrated embedding, use SVD,
# retain the fewest *unwhitened* PC scores that explain at least 90% variance.
center = x.mean(axis=0)
centered = x - center
u, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
scores_array = u * singular_values

# SVD axes are sign-indeterminate. Orient each by its largest-magnitude loading
# so a rerun does not flip the displayed map/scatter axes gratuitously.
for component in range(vt.shape[0]):
    pivot = int(np.argmax(np.abs(vt[component])))
    if vt[component, pivot] < 0:
        vt[component] *= -1
        scores_array[:, component] *= -1

eigenvalues = singular_values ** 2 / (len(ids) - 1)
total_variance = float(eigenvalues.sum())
if not np.isfinite(total_variance) or total_variance <= 0:
    raise ValueError('PCA embedding has no positive variance')
explained = eigenvalues / total_variance
cumulative = np.cumsum(explained)
retained = int(np.searchsorted(cumulative, 0.90, side='left') + 1)
if not 1 <= retained <= len(coordinate_names):
    raise ValueError('Invalid 90%-variance component count')

full_distance = np.sqrt(np.square(scores_array[:, None, :] -
                                  scores_array[None, :, :]).sum(axis=2))
if not np.allclose(full_distance, baseline_matrix.to_numpy(dtype=float),
                   rtol=1e-9, atol=1e-9):
    raise ValueError('Full PCA distances do not reproduce weighted baseline')
retained_scores = scores_array[:, :retained]
distance = np.sqrt(np.square(retained_scores[:, None, :] -
                             retained_scores[None, :, :]).sum(axis=2))
np.fill_diagonal(distance, 0)
if not np.isfinite(distance).all() or not np.allclose(distance, distance.T, atol=1e-12):
    raise ValueError('Retained PCA distances are invalid')
if (distance - full_distance > 1e-9).any():
    raise ValueError('Truncated PCA distance exceeds the full-space distance')

model_id = 'chicago_only_8_family_pca90_v1'
upper = np.triu_indices(len(ids), 1)
if (baseline_pairs.unit_id_a.tolist() != np.asarray(ids)[upper[0]].tolist() or
        baseline_pairs.unit_id_b.tolist() != np.asarray(ids)[upper[1]].tolist() or
        not np.allclose(baseline_pairs.distance.to_numpy(dtype=float),
                        full_distance[upper], rtol=1e-9, atol=1e-9)):
    raise ValueError('Baseline pair rows do not match the PCA fitting cohort')
pca_pairs = pd.DataFrame({
    'model_id': model_id,
    'unit_id_a': np.asarray(ids)[upper[0]],
    'unit_id_b': np.asarray(ids)[upper[1]],
    'distance': distance[upper],
    'baseline_distance': full_distance[upper],
})
if len(pca_pairs) != 2926 or (pca_pairs['distance'] < 0).any():
    raise ValueError('Expected 2,926 valid unordered PCA pairs')
pca_distance_matrix = pd.DataFrame(distance, index=ids, columns=ids)
pca_distance_matrix.index.name = 'unit_id'

pca_scores = pd.DataFrame({'unit_id': ids})
for component in range(scores_array.shape[1]):
    pca_scores[f'PC{component + 1}'] = scores_array[:, component]
pca_scores['retained_components'] = retained
pca_scores['retained_variance'] = float(cumulative[retained - 1])

pca_loadings = pd.DataFrame({'coordinate': coordinate_names})
pca_loadings['family'] = [name.removeprefix('coord_z_')
                          if name.startswith('coord_z_') else 'M6'
                          for name in coordinate_names]
for component in range(vt.shape[0]):
    pca_loadings[f'PC{component + 1}'] = vt[component]

pca_parameters = pd.DataFrame({
    'model_id': model_id,
    'component': np.arange(1, len(explained) + 1),
    'eigenvalue': eigenvalues,
    'explained_variance': explained,
    'cumulative_variance': cumulative,
    'retained': np.arange(1, len(explained) + 1) <= retained,
    'retained_components': retained,
    'variance_threshold': 0.90,
})
return (raw, pca_pairs, pca_parameters, pca_distance_matrix,
        pca_scores, pca_loadings)
