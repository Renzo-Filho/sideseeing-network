# N and L · Overture road segments (2026-08-19.0) in ten street classes, each counted whole in the unit containing
# its midpoint: N(u) = number of segments; L(u) = Σ length / N(u) (metres).
import geopandas as gpd
import pandas as pd
import shapely

M1 = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'living_street', 'pedestrian', 'unclassified', 'unknown']
sp = gpd.read_parquet(arg['sp_units'])
sp['unit_id'] = 'SP:' + sp.district_id
chi = gpd.read_parquet(arg['chi_units'])


def assign(geom, u):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


out = []
for city, u in (('SP', sp), ('Chicago', chi)):
    g = gpd.read_parquet(arg['segments_sp' if city == 'SP' else 'segments_chi'], columns=['subtype', 'class', 'geometry'])
    g = g[(g.subtype == 'road') & g['class'].isin(M1)].to_crs(u.crs).reset_index(drop=True)
    mid = gpd.GeoSeries(shapely.line_interpolate_point(g.geometry.values, 0.5, normalized=True), crs=u.crs)
    s = pd.Series(g.length.values).groupby(assign(mid, u).values).agg(['size', 'sum'])
    out.append(pd.DataFrame({'unit_id': u.unit_id.values, 'N_count': u.unit_id.map(s['size']).values, 'L_sum': u.unit_id.map(s['sum']).values}))
return pd.concat(out, ignore_index=True)
