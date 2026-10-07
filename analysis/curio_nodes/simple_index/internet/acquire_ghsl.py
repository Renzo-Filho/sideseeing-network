# Fetch the pinned GHSL R2023A 100 m tiles and recreate the city-clipped
# rasters used by method B. Tile IDs were verified against both city outlines.
from contextlib import ExitStack
from pathlib import Path
from zipfile import ZipFile
import math
import requests
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask

ROOT = Path(arg['scratch'])
TILES = {'sp': ('R12_C14',), 'chi': ('R4_C11', 'R5_C11')}
PRODUCTS = {'anbh': ('H', 'H_ANBH_E2018'),
            'agbh': ('H', 'H_AGBH_E2018'),
            'volume': ('V', 'V_E2020')}
out = dict(arg)
archives = set()
for city, unit_key in (('sp', 'sp_units'), ('chi', 'chi_units')):
    units = gpd.read_parquet(arg[unit_key])
    paths = {}
    for key, (family, product) in PRODUCTS.items():
        stem = f'GHS_BUILT_{product}_GLOBE_R2023A_54009_100'
        base = (f'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/'
                f'GHS_BUILT_{family}_GLOBE_R2023A/{stem}/V1-0/tiles/')
        sources = []
        for tile in TILES[city]:
            name = f'{stem}_V1_0_{tile}.zip'
            archive_path = ROOT / name
            if not archive_path.exists():
                with requests.get(base + name, stream=True, timeout=(30, 180)) as response:
                    response.raise_for_status()
                    with archive_path.open('wb') as target:
                        for part in response.iter_content(1 << 20):
                            target.write(part)
            with ZipFile(archive_path) as archive:
                tiffs = [member for member in archive.namelist()
                         if member.lower().endswith('.tif')]
                if len(tiffs) != 1:
                    raise ValueError(f'Expected one TIFF in {name}, found {tiffs}')
            sources.append('/vsizip/' + str(archive_path) + '/' + tiffs[0])
            archives.add(archive_path)
        with ExitStack() as stack:
            rasters = [stack.enter_context(rasterio.open(source)) for source in sources]
            source = rasters[0]
            shape = units.to_crs(source.crs).geometry.union_all()
            left, bottom, right, top = shape.bounds
            resolution = source.res[0]
            left = source.transform.c + math.floor((left - source.transform.c) / resolution) * resolution
            right = source.transform.c + math.ceil((right - source.transform.c) / resolution) * resolution
            bottom = source.transform.f + math.floor((bottom - source.transform.f) / resolution) * resolution
            top = source.transform.f + math.ceil((top - source.transform.f) / resolution) * resolution
            if source.nodata is None:
                raise ValueError(f'{product} has no declared NoData value')
            data, transform = merge(rasters, bounds=(left, bottom, right, top),
                                    res=source.res, nodata=source.nodata)
            inside = geometry_mask([shape.__geo_interface__], data.shape[1:],
                                   transform, all_touched=True, invert=True)
            data[:, ~inside] = source.nodata
            target_path = ROOT / f'ghsl_{city}_{key}.tif'
            profile = source.profile.copy()
            profile.update(driver='GTiff', width=data.shape[2], height=data.shape[1],
                           transform=transform, compress='deflate', tiled=True,
                           blockxsize=256, blockysize=256)
            with rasterio.open(target_path, 'w', **profile) as target:
                target.write(data)
            paths[key] = str(target_path)
    out['ghsl_' + city] = paths
for archive_path in archives:
    archive_path.unlink()
return out
