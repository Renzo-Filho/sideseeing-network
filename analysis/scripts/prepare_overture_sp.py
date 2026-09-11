"""Discover official metropolitan geography and pinned Overture release inputs."""
from pathlib import Path
import json
import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'analysis/cache/overture_sp'
CACHE.mkdir(parents=True, exist_ok=True)


def fetch(url, filename):
    target = CACHE / filename
    if target.exists():
        return json.loads(target.read_text())
    print('GET', url, flush=True)
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    data = r.json()
    target.write_text(json.dumps(data, ensure_ascii=False))
    return data


if __name__ == '__main__':
    catalog = fetch('https://stac.overturemaps.org/catalog.json', 'catalog.json')
    release = catalog['latest']
    print('Release:', release, flush=True)
    cat = fetch(f'https://stac.overturemaps.org/{release}/catalog.json', 'release_catalog.json')
    buildings = fetch(f'https://stac.overturemaps.org/{release}/buildings/catalog.json', 'buildings_catalog.json')
    collection = fetch(f'https://stac.overturemaps.org/{release}/buildings/building/collection.json', 'building_collection.json')
    print('Building Parquet assets:', sum(x['rel']=='item' for x in collection['links']), flush=True)
    rms = fetch('https://servicodados.ibge.gov.br/api/v1/localidades/regioes-metropolitanas/04901', 'rmsp_membership.json')
    print('Metropolitan municipalities:', len(rms[0]['municipios']), flush=True)
    mesh = fetch('https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=maxima&intrarregiao=municipio', 'sp_municipalities.geojson')
    print('Mesh features:', len(mesh['features']), 'first properties:', mesh['features'][0]['properties'], flush=True)
