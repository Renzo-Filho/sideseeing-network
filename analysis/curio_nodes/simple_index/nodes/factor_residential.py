# R · residential establishments (dwellings).
# São Paulo: IBGE CNEFE 2022 private dwellings (COD_ESPECIE 1), counted by COD_DISTRITO. The code → district
#   crosswalk is derived here: each code goes to the district holding most of its addresses with original census
#   coordinates (NV_GEO_COORD 1).
# Chicago: Census 2020 housing units (HOUSING20) of each block, split across Community Areas by area share:
#   R(u) = Σ_b HU_b · area(b ∩ u) / area(b).
import geopandas as gpd
import pandas as pd
import shapely

sp = gpd.read_parquet(arg['sp_units'])
sp['unit_id'] = 'SP:' + sp.district_id
chi = gpd.read_parquet(arg['chi_units'])


def assign(geom, u):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


c = pd.read_parquet(arg['cnefe_sp'], columns=['COD_DISTRITO', 'COD_ESPECIE', 'NV_GEO_COORD', 'LATITUDE', 'LONGITUDE'])
p = c[c.NV_GEO_COORD == 1]
pts = gpd.GeoSeries(gpd.points_from_xy(p.LONGITUDE, p.LATITUDE), index=p.index, crs=4674).to_crs(sp.crs)
x = pd.DataFrame({'cod': p.COD_DISTRITO, 'unit_id': assign(pts, sp)})
crosswalk = x.groupby(['cod', 'unit_id']).size().rename('n').reset_index().sort_values('n').groupby('cod').tail(1).set_index('cod').unit_id
assert len(crosswalk) == 96 and crosswalk.is_unique, 'CNEFE district codes must map one-to-one to the 96 districts'
r_sp = c[c.COD_ESPECIE == 1].COD_DISTRITO.map(crosswalk).value_counts()
assert int(r_sp.sum()) == int((c.COD_ESPECIE == 1).sum()), 'every private dwelling must reach a district'

b = gpd.read_parquet(arg['chi_blocks'], columns=['GEOID20', 'HOUSING20', 'geometry']).to_crs(chi.crs)
ia, ib = chi.sindex.query(b.geometry, predicate='intersects')
area = shapely.area(shapely.intersection(b.geometry.values[ia], chi.geometry.values[ib]))
keep = area > 0
weight = area[keep] / shapely.area(b.geometry.values[ia[keep]])
r_chi = pd.Series(b.HOUSING20.values[ia[keep]] * weight).groupby(chi.unit_id.values[ib[keep]]).sum()

return pd.concat([pd.DataFrame({'unit_id': sp.unit_id.values, 'R_count': sp.unit_id.map(r_sp).fillna(0).values}),
                  pd.DataFrame({'unit_id': chi.unit_id.values, 'R_count': chi.unit_id.map(r_chi).fillna(0).values})],
                 ignore_index=True)
