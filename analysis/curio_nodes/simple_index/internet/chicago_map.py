# Map data: identical ranking and five-area highlight as the original flow.
# Fetch the Community Areas geometry here because this node has the index table
# as its only input and must not depend on a preinstalled Curio dataset.
from io import BytesIO
import geopandas as gpd
import requests
import shapely

bras = float(arg.set_index('unit_id').at['SP:10', 'index'])
chi = arg[arg.city == 'Chicago'][['unit_id', 'name', 'index']].copy()
chi['gap'] = (chi['index'] - bras).abs()
chi['gap_rank'] = chi.gap.rank(method='min').astype(int)
chi['top5'] = chi.gap_rank <= 5
url = 'https://data.cityofchicago.org/resource/igwz-8jzy.geojson?$limit=2147483647'
response = requests.get(url, timeout=(30, 180))
response.raise_for_status()
areas = gpd.read_file(BytesIO(response.content)).to_crs(26916)
areas.geometry = areas.geometry.map(shapely.make_valid)
areas['unit_id'] = 'CHI:' + areas.area_numbe.astype(int).astype(str).str.zfill(2)
g = areas[['unit_id', 'geometry']].merge(chi, on='unit_id', validate='one_to_one')
assert len(g) == 77
centre = g.geometry.representative_point().to_crs(4326)
g = g.to_crs(4326)
g['lon'], g['lat'] = centre.x.values, centre.y.values
g['index'], g['gap'] = g['index'].round(3), g['gap'].round(3)
return g.sort_values('gap_rank').reset_index(drop=True)
