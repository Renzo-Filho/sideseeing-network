# Fetch and prepare the reporting units used by both methods. All source URLs and
# preparation rules live in this node; the returned paths are run-time scratch files.
from pathlib import Path
import tempfile
import requests
import geopandas as gpd
import pandas as pd
import shapely

root = Path(tempfile.mkdtemp(prefix='curio-composite-internet-'))


def fetch(name, url):
    path = root / name
    with requests.get(url, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        with path.open('wb') as target:
            for part in response.iter_content(1 << 20):
                target.write(part)
    return path


def polygonal(geometry):
    if geometry is None or geometry.is_empty:
        return shapely.Polygon()
    fixed = shapely.make_valid(geometry)
    if fixed.geom_type in ('Polygon', 'MultiPolygon'):
        return fixed
    return shapely.union_all([part for part in shapely.get_parts(fixed)
                              if part.geom_type in ('Polygon', 'MultiPolygon')])


chicago_url = 'https://data.cityofchicago.org/resource/igwz-8jzy.geojson?$limit=2147483647'
hydro_url = 'https://data.cityofchicago.org/resource/knfe-65pw.geojson?$limit=2147483647'
wfs = 'https://wms.geosampa.prefeitura.sp.gov.br/geoserver/ows'
params = '?service=WFS&request=GetFeature&version=2.0.0&outputFormat=application%2Fjson&srsName=EPSG:4326&count=1000000&typeName='
sp_url = wfs + params + 'geoportal%3Adistrito_municipal'
water_url = wfs + params + 'geoportal%3Amassa_d_agua'

chi_raw = fetch('chicago_areas.geojson', chicago_url)
chi_hydro = fetch('chicago_hydro.geojson', hydro_url)
sp_raw = fetch('sao_paulo_districts.geojson', sp_url)
sp_water = fetch('sao_paulo_water.geojson', water_url)

chi = gpd.read_file(chi_raw).to_crs(26916)
chi.geometry = chi.geometry.map(polygonal)
chi['district_id'] = chi.area_numbe.astype(int).map(lambda value: f'{value:02d}')
assert len(chi) == 77 and set(chi.district_id) == {f'{i:02d}' for i in range(1, 78)}
assert (chi.area_numbe.astype(int) == chi.area_num_1.astype(int)).all()
chi = chi.sort_values('district_id').reset_index(drop=True)
chi = chi[['district_id', 'community', 'geometry']].rename(columns={'community': 'district_name'})
chi['unit_id'] = 'CHI:' + chi.district_id
chi['gross_area_m2'] = chi.area
chi_path = root / 'chicago_units.parquet'
chi.to_parquet(chi_path, index=False)

sp = gpd.read_file(sp_raw).to_crs(31983)
sp['district_id'] = sp.cd_distrito_municipal.astype(str).str.zfill(2)
assert len(sp) == 96 and sp.district_id.nunique() == 96
sp.geometry = sp.geometry.map(polygonal)
sp = sp.sort_values('district_id').reset_index(drop=True)
sp_municipal = root / 'sao_paulo_municipal.parquet'
sp.to_parquet(sp_municipal, index=False)
covered = shapely.Polygon()
for i in sp.index:
    geometry = polygonal(sp.geometry.iloc[i].difference(covered))
    sp.at[i, 'geometry'] = geometry
    covered = shapely.union_all([covered, geometry])
water = gpd.read_file(sp_water).to_crs(sp.crs)
water_union = shapely.union_all(water.geometry.map(polygonal).values)
sp['gross_area_m2'] = sp.area
sp['water_area_m2'] = shapely.area(shapely.intersection(sp.geometry.values, water_union))
sp['land_area_m2'] = shapely.area(shapely.difference(sp.geometry.values, water_union))
assert sp.land_area_m2.gt(0).all()
sp_path = root / 'sao_paulo_units.parquet'
sp.to_parquet(sp_path, index=False)

return {'scratch': str(root), 'sp_units': str(sp_path), 'chi_units': str(chi_path),
        'sp_units_municipal': str(sp_raw), 'chi_units_geojson': str(chi_raw),
        'chi_hydrography': str(chi_hydro)}
