# Fetch the current published CTA and SPTrans static GTFS feeds. They change
# over time; the four text tables used by method A/B are extracted at run time.
from pathlib import Path
from zipfile import ZipFile
import requests

ROOT = Path(arg['scratch'])
FEEDS = {
    'chi': 'https://www.transitchicago.com/downloads/sch_data/google_transit.zip',
    'sp': 'https://www.sptrans.com.br/umbraco/Surface/PerfilDesenvolvedor/BaixarGTFS',
}
TABLES = ('stops', 'routes', 'trips', 'stop_times')
out = dict(arg)
for city, url in FEEDS.items():
    archive_path = ROOT / f'gtfs_{city}.zip'
    with requests.get(url, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        with archive_path.open('wb') as target:
            for part in response.iter_content(1 << 20):
                target.write(part)
    paths = {}
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        for table in TABLES:
            matching = [name for name in names if name.split('/')[-1].lower() == table + '.txt']
            if len(matching) != 1:
                raise ValueError(f'{city}: expected one {table}.txt, found {matching}')
            path = ROOT / f'gtfs_{city}_{table}.txt'
            with archive.open(matching[0]) as source, path.open('wb') as target:
                while True:
                    part = source.read(1 << 20)
                    if not part:
                        break
                    target.write(part)
            paths[table] = str(path)
    archive_path.unlink()
    out['gtfs_' + city] = paths
return out
