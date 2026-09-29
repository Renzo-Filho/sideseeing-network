# Prepare one compact table for Curio's linked PCA, ranking, and map dashboard.
# arg is (raw, pca_pairs, pca_parameters, pca_distance_matrix,
#        pca_scores, pca_loadings) from the PCA model application node.
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import orient_polygons
from shapely.geometry import mapping


ids = [f'CHI:{number:02d}' for number in range(1, 78)]
if not isinstance(arg, (tuple, list)) or len(arg) != 6:
    raise ValueError('Expected the six-part PCA model application output')
raw, pca_pairs, _pca_parameters, matrix, scores, _pca_loadings = arg

if not isinstance(raw, pd.DataFrame) or raw.unit_id.tolist() != ids:
    raise ValueError('Raw model rows must be ordered CHI:01–CHI:77')
if not isinstance(scores, pd.DataFrame) or not {'unit_id', 'PC1', 'PC2'}.issubset(scores):
    raise ValueError('PCA scores must contain unit_id, PC1, and PC2')
if scores.unit_id.tolist() != ids:
    raise ValueError('PCA score rows must be ordered CHI:01–CHI:77')
coordinates = scores[['PC1', 'PC2']].to_numpy(dtype=float)
if not np.isfinite(coordinates).all():
    raise ValueError('PCA plot coordinates must be finite')

if not isinstance(matrix, pd.DataFrame) or matrix.shape != (77, 78):
    raise ValueError('Expected a 77-by-77 PCA distance matrix with explicit IDs')
if matrix.unit_id.tolist() != ids or matrix.columns.tolist() != ['unit_id'] + ids:
    raise ValueError('PCA distance matrix must be ordered CHI:01–CHI:77 on both axes')
matrix = matrix.set_index('unit_id')
distance_values = matrix.to_numpy(dtype=float)
if not np.isfinite(distance_values).all() or (distance_values < -1e-10).any():
    raise ValueError('PCA distances must be finite and nonnegative')
if not np.allclose(distance_values, distance_values.T, rtol=0, atol=1e-10):
    raise ValueError('PCA distance matrix must be symmetric')
if not np.allclose(np.diag(distance_values), 0, rtol=0, atol=1e-10):
    raise ValueError('PCA self-distances must be zero')

if not isinstance(pca_pairs, pd.DataFrame) or len(pca_pairs) != 2926:
    raise ValueError('Expected 2,926 unordered PCA pair distances')
if not {'unit_id_a', 'unit_id_b', 'distance'}.issubset(pca_pairs):
    raise ValueError('PCA pairs must contain both unit IDs and distance')
lookup = {unit_id: index for index, unit_id in enumerate(ids)}
try:
    row_a = pca_pairs.unit_id_a.map(lookup).to_numpy(dtype=int)
    row_b = pca_pairs.unit_id_b.map(lookup).to_numpy(dtype=int)
except (TypeError, ValueError) as exc:
    raise ValueError('PCA pairs contain an unknown Community Area ID') from exc
if not np.array_equal(row_a, np.triu_indices(77, 1)[0]) or not np.array_equal(
        row_b, np.triu_indices(77, 1)[1]):
    raise ValueError('PCA pairs must follow strict upper-triangle ID order')
if not np.allclose(pca_pairs.distance.to_numpy(dtype=float),
                   distance_values[row_a, row_b], rtol=1e-10, atol=1e-10):
    raise ValueError('PCA pairs disagree with the distance matrix')

areas = gpd.read_file(curio_dataset_path('data.cityofchicago.community-areas-sideseeing'))
if len(areas) != 77 or not {'area_numbe', 'community', 'geometry'}.issubset(areas):
    raise ValueError('Expected the 77 Community Area polygons with IDs and names')
if areas.crs is None:
    raise ValueError('Community Area boundaries have no coordinate reference system')
numbers = pd.to_numeric(areas.area_numbe, errors='raise').astype(int)
if numbers.isna().any() or set(numbers.tolist()) != set(range(1, 78)):
    raise ValueError('Community Area boundaries must have IDs 1–77 exactly once')
areas = areas.assign(_number=numbers).sort_values('_number').reset_index(drop=True)
areas = areas.to_crs(4326)
if areas.geometry.isna().any() or areas.geometry.is_empty.any() or not areas.geometry.is_valid.all():
    raise ValueError('Community Area boundaries contain empty or invalid polygons')
if areas.community.isna().any() or areas.community.astype(str).str.strip().eq('').any():
    raise ValueError('Community Area boundaries contain a blank name')

# A plain DataFrame is deliberate: Curio's Vega adapter drops active geometry
# when its input is a GeoDataFrame. GeoJSON geometry in an object column survives
# Curio's DataFrame codec and is rendered by Vega-Lite's geoshape mark.
dashboard = pd.DataFrame({
    'type': ['Feature'] * 77,
    'geometry': [mapping(orient_polygons(geom, exterior_cw=False)) for geom in areas.geometry],
    'unit_id': ids,
    'area_numbe': [f'{number:02d}' for number in range(1, 78)],
    'community': areas.community.astype(str).str.strip().tolist(),
    'PC1': coordinates[:, 0],
    'PC2': coordinates[:, 1],
})
for number, unit_id in enumerate(ids, start=1):
    dashboard[f'd_{number:02d}'] = distance_values[:, number - 1]

if dashboard.shape != (77, 84):
    raise ValueError('Dashboard payload must have 77 rows and 84 columns')
return dashboard
