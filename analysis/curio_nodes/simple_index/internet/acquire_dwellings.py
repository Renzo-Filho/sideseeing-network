# Recreate the two residential source tables from public Census and IBGE files.
# The Chicago index uses HOUSING20, so its previous optional LODES enrichment
# is intentionally omitted: LODES contributes no value to either method.
from pathlib import Path
from zipfile import ZipFile
import requests
import geopandas as gpd
import pandas as pd
import shapely
import pyogrio

ROOT = Path(arg['scratch'])


def fetch(name, url):
    path = ROOT / name
    with requests.get(url, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        with path.open('wb') as target:
            for part in response.iter_content(1 << 20):
                target.write(part)
    return path


def polygonal(geometry):
    fixed = shapely.make_valid(geometry)
    if fixed.geom_type in ('Polygon', 'MultiPolygon'):
        return fixed
    return shapely.union_all([part for part in shapely.get_parts(fixed)
                              if part.geom_type in ('Polygon', 'MultiPolygon')])


ibge_url = ('https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/'
            'Censo_Demografico_2022/Arquivos_CNEFE/CSV/Municipio/35_SP/3550308_SAO_PAULO.zip')
census_url = 'https://www2.census.gov/geo/tiger/TIGER2022/TABBLOCK20/tl_2022_17_tabblock20.zip'
ibge = fetch('cnefe_sao_paulo.zip', ibge_url)
with ZipFile(ibge) as archive:
    names = [name for name in archive.namelist() if name.lower().endswith('.csv')]
    if len(names) != 1:
        raise ValueError(f'Expected one CNEFE CSV, found {names}')
    with archive.open(names[0]) as source:
        cnefe = pd.read_csv(source, sep=';', low_memory=False,
                            usecols=['COD_DISTRITO', 'COD_ESPECIE', 'NV_GEO_COORD',
                                     'LATITUDE', 'LONGITUDE'])
cnefe_path = ROOT / 'cnefe_sao_paulo.parquet'
cnefe.to_parquet(cnefe_path, index=False)
ibge.unlink()

census = fetch('illinois_blocks_2022.zip', census_url)
with ZipFile(census) as archive:
    names = [name for name in archive.namelist() if name.lower().endswith('.shp')]
    if len(names) != 1:
        raise ValueError(f'Expected one block shapefile, found {names}')
    shp = names[0]
chi = gpd.read_parquet(arg['chi_units'])
bounds = tuple(chi.to_crs(4269).total_bounds)
blocks = pyogrio.read_dataframe('/vsizip/' + str(census) + '/' + shp, bbox=bounds)
blocks = blocks.to_crs(chi.crs)
blocks.geometry = blocks.geometry.map(polygonal)
city = chi.geometry.union_all()
blocks = blocks.loc[blocks.intersects(city) & blocks.geometry.area.gt(0)].reset_index(drop=True)
assert blocks.GEOID20.is_unique and blocks.HOUSING20.notna().all()
blocks_path = ROOT / 'chicago_blocks.parquet'
blocks.to_parquet(blocks_path, index=False)
census.unlink()

out = dict(arg)
out.update(cnefe_sp=str(cnefe_path), chi_blocks=str(blocks_path))
return out
