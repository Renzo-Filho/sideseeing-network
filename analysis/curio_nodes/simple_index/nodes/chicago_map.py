# Map data: the 77 Chicago Community Areas with their index gap to Brás (SP:10), gap(u) = |I(u) − I(Brás)|,
# ranked smallest first; the five closest are flagged for the map. Returned in lon/lat (EPSG:4326).
import geopandas as gpd

bras = float(arg.set_index('unit_id').at['SP:10', 'index'])
chi = arg[arg.city == 'Chicago'][['unit_id', 'name', 'index']].copy()
chi['gap'] = (chi['index'] - bras).abs()
chi['gap_rank'] = chi.gap.rank(method='min').astype(int)
chi['top5'] = chi.gap_rank <= 5
areas = gpd.read_parquet(curio_dataset_path("data.sideseeing.chicago-community-areas-prepared"), columns=['unit_id', 'geometry'])
g = areas.merge(chi, on='unit_id', validate='one_to_one')
assert len(g) == 77
centre = g.geometry.representative_point().to_crs(4326)
g = g.to_crs(4326)
g['lon'], g['lat'] = centre.x.values, centre.y.values
g['index'], g['gap'] = g['index'].round(3), g['gap'].round(3)
return g.sort_values('gap_rank').reset_index(drop=True)
