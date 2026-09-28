"""Construct selected installed-Curio features and execute the three model stages."""
import time

from run_local import built, module, morph, urban, paths


def timed(name, func, arg):
    start = time.time()
    result = func(arg)
    first = result[0] if isinstance(result, tuple) else result
    print(name, len(first), 'rows', round(time.time() - start, 1), 'seconds', flush=True)
    return result


m1 = timed('M1', module('M1'), morph)
m6 = timed('M6', module('M6'), m1)
b1 = timed('B1', module('B1'), built)
bv = timed('BV', module('BV'), built)
u1 = timed('U1', module('U1'), urban)
u2 = timed('U2', module('U2'), urban)
u3 = timed('U3', module('U3'), urban)
u4 = timed('U4', module('U4'), urban)
matrix = timed('Model matrix', module('model_matrix'), [[m1, m6], [b1, bv], [u1, u2, u3, u4]])
fitted = timed('Fit transforms', module('model_fit'), matrix)
raw, pairs, parameters, distances, embedding = timed('Pairwise distances', module('model_distances'), fitted)
assert raw.shape == (77, 18)
assert pairs.shape == (2926, 12)
assert distances.shape == (77, 77)
assert embedding.shape == (77, 18)
assert len(parameters) == 16
print('CHI:01 to CHI:02', pairs.loc[(pairs.unit_id_a == 'CHI:01') &
                                   (pairs.unit_id_b == 'CHI:02'), 'distance'].iat[0])
pca = timed('PCA-90 model application', module('model_pca'),
            (raw, pairs, parameters, distances, embedding))
pca_raw, pca_pairs, pca_parameters, pca_distances, pca_scores, pca_loadings = pca
assert pca_raw.shape == (77, 18)
assert pca_pairs.shape == (2926, 5)
assert pca_distances.shape == (77, 77)
assert pca_scores.shape == (77, 20)
assert pca_loadings.shape == (17, 19)
k = int(pca_parameters.retained_components.iat[0])
variance = float(pca_parameters.cumulative_variance.iat[k-1])
assert variance >= .90
if k > 1:
    assert pca_parameters.cumulative_variance.iat[k-2] < .90
print('PCA retained', k, 'components and', round(variance, 6), 'variance')
print('CHI:01 to CHI:02 PCA distance',
      pca_pairs.loc[(pca_pairs.unit_id_a == 'CHI:01') &
                    (pca_pairs.unit_id_b == 'CHI:02'), 'distance'].iat[0])
viz_prep = module('viz_dashboard_data')
viz_prep.__globals__['curio_dataset_path'] = lambda dataset_id: (
    paths['community_areas'] if dataset_id ==
    'data.cityofchicago.community-areas-sideseeing' else
    (_ for _ in ()).throw(ValueError(f'Unexpected dataset ID: {dataset_id}')))
dashboard = timed('Dashboard data', viz_prep, pca)
assert dashboard.shape == (77, 84)
assert dashboard.unit_id.tolist() == [f'CHI:{i:02d}' for i in range(1, 78)]
assert dashboard.loc[0, 'community'] == 'ROGERS PARK'
assert abs(dashboard.loc[1, 'd_01'] -
           pca_distances.loc['CHI:02', 'CHI:01']) < 1e-12
assert dashboard.geometry.map(lambda value: value['type'] in ('Polygon', 'MultiPolygon')).all()
print('model construction complete', flush=True)
