# C · commercial establishments. Overture Places (2026-08-19.0) whose taxonomy top level is in K, counted inside
# each unit (point in polygon). No filter on operating status or confidence: one rule for both cities.
# Output: one row per unit (96 São Paulo districts + 77 Chicago Community Areas) with names and gross area.
import geopandas as gpd
import pandas as pd

K = ['shopping', 'food_and_drink', 'services_and_business', 'lifestyle_services', 'lodging']

sp = gpd.read_parquet(arg['sp_units'])
sp['unit_id'], sp['name'], sp['city'] = 'SP:' + sp.district_id, sp.nm_distrito_municipal, 'SP'
chi = gpd.read_parquet(arg['chi_units'])
chi['name'], chi['city'] = chi.district_name, 'Chicago'
cols = ['unit_id', 'name', 'city', 'gross_area_m2', 'geometry']
units = {'SP': sp[cols], 'Chicago': chi[cols]}


def assign(geom, u):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


out = []
for city, u in units.items():
    g = gpd.read_parquet(arg['places_sp' if city == 'SP' else 'places_chi'], columns=['geometry', 'taxonomy']).to_crs(u.crs)
    top = g.taxonomy.map(lambda t: t['hierarchy'][0] if t is not None and t['hierarchy'] is not None and len(t['hierarchy']) else None)
    g = g[top.isin(K)]
    counts = assign(g.geometry, u).value_counts()
    out.append(pd.DataFrame({'unit_id': u.unit_id.values, 'name': u.name.values, 'city': city,
                             'gross_area_km2': u.gross_area_m2.values / 1e6,
                             'C_count': u.unit_id.map(counts).fillna(0).astype(int).values}))
return pd.concat(out, ignore_index=True)
