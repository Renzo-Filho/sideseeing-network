# V (method A) · mean Overture building height of the buildings with a height (> 0) whose bounding-box centre lies
# in the unit: V(u) = (1/n_u) Σ_k h_k. São Paulo's buildings arrive as height + bounding-box centre (from the GeoPackage R-tree).
import geopandas as gpd
import pandas as pd
import pyproj

sp = gpd.read_parquet(arg['sp_units'])
sp['unit_id'] = 'SP:' + sp.district_id
chi = gpd.read_parquet(arg['chi_units'])


def assign(geom, u):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


b = pd.read_parquet(arg['buildings_chi'], columns=['height', 'bbox'])
b = b[b.height > 0].reset_index(drop=True)
bb = pd.json_normalize(b.pop('bbox'))
x, y = pyproj.Transformer.from_crs(4326, chi.crs, always_xy=True).transform(((bb.xmin + bb.xmax) / 2).values, ((bb.ymin + bb.ymax) / 2).values)
uid = assign(gpd.GeoSeries(gpd.points_from_xy(x, y), crs=chi.crs), chi)
h_chi = pd.Series(b.height.values).groupby(uid.values).agg(['sum', 'size'])

b = pd.read_parquet(arg['buildings_sp'])  # height_m > 0 with bounding-box centre (x, y), EPSG:31983
parts = []
for start in range(0, len(b), 500_000):
    c = b.iloc[start:start + 500_000]
    uid = assign(gpd.GeoSeries(gpd.points_from_xy(c.x, c.y), crs=sp.crs, index=c.index), sp)
    parts.append(c.height_m.groupby(uid.values).agg(['sum', 'size']))
h_sp = pd.concat(parts).groupby(level=0).sum()

h = pd.concat([h_sp, h_chi])
units = pd.concat([sp.unit_id, chi.unit_id], ignore_index=True)
return pd.DataFrame({'unit_id': units.values, 'V_A_sum': units.map(h['sum']).values, 'V_A_n': units.map(h['size']).values})
