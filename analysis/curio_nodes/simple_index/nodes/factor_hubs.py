# H · transportation hubs = subway/metro stations + bus stops inside each unit.
# Chicago (CTA GTFS): stations = parent stations of the L platform stops (route_type 1); bus stops = stops served
#   by route_type 3. São Paulo (SPTrans GTFS): stations = metro stop records (route_type 1) grouped by name, placed at
#   their mean position; CPTM (route_type 2) is excluded; bus stops as listed.
import geopandas as gpd
import pandas as pd
import shapely

sp = gpd.read_parquet(arg['sp_units'])
sp['unit_id'] = 'SP:' + sp.district_id
chi = gpd.read_parquet(arg['chi_units'])


def assign(geom, u):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


out = []
for city, u, feed in (('SP', sp, arg['gtfs_sp']), ('Chicago', chi, arg['gtfs_chi'])):
    s, r, t, st = (pd.read_csv(feed[k], dtype=str) for k in ('stops', 'routes', 'trips', 'stop_times'))  # GTFS text tables
    m = (st[['trip_id', 'stop_id']].drop_duplicates().merge(t[['route_id', 'trip_id']], on='trip_id')
         .merge(r[['route_id', 'route_type']], on='route_id')[['stop_id', 'route_type']].drop_duplicates())
    g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon.astype(float), s.stop_lat.astype(float)), crs=4326).to_crs(u.crs)
    rail = g[g.stop_id.isin(m[m.route_type == '1'].stop_id)]
    if city == 'Chicago':
        stations = g[g.stop_id.isin(rail.parent_station)].geometry.reset_index(drop=True)
    else:
        stations = gpd.GeoSeries(rail.groupby('stop_name').geometry.apply(lambda p: shapely.Point(p.x.mean(), p.y.mean())).values, crs=u.crs)
    bus = g[g.stop_id.isin(m[m.route_type == '3'].stop_id)].geometry.reset_index(drop=True)
    n_st, n_bus = assign(stations, u).value_counts(), assign(bus, u).value_counts()
    out.append(pd.DataFrame({'unit_id': u.unit_id.values, 'H_stations': u.unit_id.map(n_st).fillna(0).values,
                             'H_bus': u.unit_id.map(n_bus).fillna(0).values}))
return pd.concat(out, ignore_index=True)
