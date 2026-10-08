# Land area of each unit = unit minus municipal hydrography (km²). São Paulo: land_area_m2 of the prepared districts.
# Chicago: Community Area minus the union of the repaired Chicago hydrography polygons inside the city.
import geopandas as gpd
import pandas as pd
import shapely


def polygonal(geom):
    if geom is None or geom.is_empty:
        return shapely.Polygon()
    g = shapely.make_valid(geom)
    if g.geom_type in ('Polygon', 'MultiPolygon'):
        return g
    return shapely.union_all([p for p in shapely.get_parts(g) if p.geom_type in ('Polygon', 'MultiPolygon')])


sp = gpd.read_parquet(arg['sp_units'])
chi = gpd.read_parquet(arg['chi_units'])
hydro = gpd.read_file(arg['chi_hydrography']).to_crs(chi.crs)
water = shapely.union_all(hydro.geometry.map(polygonal)).intersection(chi.geometry.union_all())
chi_land = shapely.area(shapely.difference(chi.geometry.values, water))
return pd.concat([pd.DataFrame({'unit_id': 'SP:' + sp.district_id, 'land_km2': sp.land_area_m2 / 1e6}),
                  pd.DataFrame({'unit_id': chi.unit_id, 'land_km2': chi_land / 1e6})], ignore_index=True)
