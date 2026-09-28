"""Bounded independent physical-cover audit of saved U1 diagnostic points.

Downloads imagery chips around seven frozen sample coordinates and measures
distance to municipal street centerlines. Images remain under analysis/work.
Visual case labels are recorded separately in the dated result report.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from PIL import Image, ImageDraw
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'analysis/work/u1_independent_cases_2026_09_23'
OUT = ROOT / 'analysis/results/SP_CHI/u1_independent_cases_2026_09_23'
POINTS = ROOT / 'analysis/results/SP_CHI/u1_source_samples_2026_09_22/sampled_land_points.csv'
CASES = [('SP:10', 9), ('SP:10', 20), ('SP:02', 2), ('SP:95', 7),
         ('CHI:32', 5), ('CHI:14', 3), ('CHI:23', 10)]
CHICAGO_IMAGE = 'https://gis.cookcountyil.gov/imagery/rest/services/CookOrtho2025/ImageServer/exportImage'
SP_IMAGE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile'
HEADERS = {'User-Agent': 'sideseeing-network bounded academic image audit (project repository)'}


def get_bytes(url: str, *, params: dict | None = None) -> tuple[bytes, str]:
    prepared_url = requests.Request('GET', url, params=params).prepare().url
    cache = WORK / 'raw' / (hashlib.sha256(prepared_url.encode()).hexdigest() + '.img')
    if cache.exists():
        return cache.read_bytes(), prepared_url
    with requests.get(prepared_url, timeout=45, headers=HEADERS) as response:
        response.raise_for_status()
        assert response.headers.get('Content-Type', '').startswith('image/'), response.headers.get('Content-Type')
        content = response.content
        assert len(content) < 4_000_000
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(content)
        return content, response.url


def chicago_image(lon: float, lat: float):
    half_lat = 70 / 111_320
    half_lon = half_lat / math.cos(math.radians(lat))
    bounds = [lon-half_lon, lat-half_lat, lon+half_lon, lat+half_lat]
    content, url = get_bytes(CHICAGO_IMAGE, params={
        'bbox': ','.join(f'{v:.8f}' for v in bounds), 'bboxSR': 4326,
        'imageSR': 4326, 'size': '800,800', 'format': 'jpg', 'f': 'image'})
    image = Image.open(io.BytesIO(content)).convert('RGB')
    return image, (400, 400), [{'url': url, 'sha256': hashlib.sha256(content).hexdigest()}]


def sp_image(lon: float, lat: float):
    z = 19
    px = (lon+180) / 360 * 2**z * 256
    py = (1-math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**z * 256
    tx, ty = math.floor(px/256), math.floor(py/256)
    x0, y0 = tx-1, ty-1
    canvas = Image.new('RGB', (768, 768))
    items = []
    for dy in range(3):
        for dx in range(3):
            url = f'{SP_IMAGE}/{z}/{y0+dy}/{x0+dx}'
            content, final_url = get_bytes(url)
            image = Image.open(io.BytesIO(content)).convert('RGB')
            canvas.paste(image, (dx*256, dy*256))
            items.append({'url': final_url, 'sha256': hashlib.sha256(content).hexdigest()})
    return canvas, (round(px-x0*256), round(py-y0*256)), items


def street_distance(city: str, lon: float, lat: float) -> tuple[float | None, str | None]:
    if city == 'SP':
        point = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(31983).iloc[0]
        layer = ROOT / 'analysis/data/SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg'
        roads = gpd.read_file(layer, bbox=point.buffer(100).bounds, columns=['lg_tipo', 'lg_nome', 'geometry'])
        metric = roads
        label = lambda r: f'{r.lg_tipo} {r.lg_nome}'
    else:
        point = gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(26916).iloc[0]
        layer = ROOT / 'analysis/data/Chicago/steet_center_lines_20260915.geojson'
        deg = 150 / 111_320
        roads = gpd.read_file(layer, bbox=(lon-deg, lat-deg, lon+deg, lat+deg),
                              columns=['street_nam', 'street_typ', 'geometry'])
        metric = roads.to_crs(26916)
        label = lambda r: f'{r.street_nam} {r.street_typ}'
    if metric.empty:
        return None, None
    distances = metric.geometry.distance(point)
    closest = metric.iloc[distances.argmin()]
    return float(distances.min()), label(closest)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    sampled = pd.read_csv(POINTS).set_index(['unit_id', 'sample_no'])
    rows, receipts = [], {}
    for unit, sample_no in CASES:
        point = sampled.loc[(unit, sample_no)]
        city = unit.split(':')[0]
        lon, lat = float(point.lon), float(point.lat)
        image, marker, sources = (chicago_image(lon, lat) if city == 'CHI' else sp_image(lon, lat))
        draw = ImageDraw.Draw(image)
        x, y = marker
        draw.ellipse((x-7, y-7, x+7, y+7), outline='red', width=3)
        draw.line((x-15, y, x+15, y), fill='red', width=3)
        draw.line((x, y-15, x, y+15), fill='red', width=3)
        key = f'{unit.replace(":", "_")}_{sample_no:02d}'
        local = WORK / f'{key}_annotated.png'
        image.save(local)
        distance, street = street_distance(city, lon, lat)
        receipts[key] = {'image_source': 'Cook County 2025 orthophoto' if city=='CHI' else 'Esri World Imagery, capture date unverified',
                         'urls_and_sha256': sources, 'annotated_local_path': str(local.relative_to(ROOT)),
                         'annotated_sha256': hashlib.sha256(local.read_bytes()).hexdigest()}
        rows.append({'case_id': key, 'unit_id': unit, 'sample_no': sample_no,
                     'lon': lon, 'lat': lat, 'prior_source_status': point.land_source_status,
                     'nearest_municipal_street_m': distance, 'nearest_street_name': street,
                     'image_source': receipts[key]['image_source']})
        print(key, 'street_m', round(distance, 2) if distance is not None else None, flush=True)
    pd.DataFrame(rows).to_csv(OUT/'land_case_geometry.csv', index=False)
    (OUT/'imagery_receipts.json').write_text(json.dumps({
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'cases_predeclared': CASES, 'method': 'small imagery chip and local municipal street centerline distance; visual labels stored separately',
        'source_layers': {'SP_streets': 'analysis/data/SP/Cadastro e Vias/SIRGAS_GPKG_logradouronbl.gpkg',
                          'CHI_streets': 'analysis/data/Chicago/steet_center_lines_20260915.geojson'},
        'cases': receipts}, indent=2)+'\n')


if __name__ == '__main__':
    main()
