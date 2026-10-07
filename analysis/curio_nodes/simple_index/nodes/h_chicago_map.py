# Map data: the 77 Chicago Community Areas with their harmonized-model distance to Brás (SP:10), ranked smallest
# first; the five closest are flagged for the map. Returned in lon/lat (EPSG:4326).
import geopandas as gpd

chi = arg[(arg.unit_id == 'SP:10') & (arg.other_city == 'Chicago')][['other_id', 'other_name', 'distance', 'rank_in_city']]
chi = chi.rename(columns={'other_id': 'unit_id', 'other_name': 'name', 'rank_in_city': 'distance_rank'})
chi['top5'] = chi.distance_rank <= 5
areas = gpd.read_parquet(curio_dataset_path("data.sideseeing.chicago-community-areas-prepared"), columns=['unit_id', 'geometry'])
g = areas.merge(chi, on='unit_id', validate='one_to_one')
assert len(g) == 77
centre = g.geometry.representative_point().to_crs(4326)
g = g.to_crs(4326)
g['lon'], g['lat'] = centre.x.values, centre.y.values
g['distance'] = g['distance'].round(3)
return g.sort_values('distance_rank').reset_index(drop=True)
