"""Clone the saved composite index and embed internet acquisition in its nodes.

The output spec has no Curio dataset references or project-local imports. The
files in this folder are read only while constructing the spec; their full code
is embedded in it, so an imported copy needs none of these files at run time.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path('/home/renzo/Documents/GitHub/curio/.curio/users/3/projects/'
                      '4e6b8d2a-af2e-44f2-9ce9-32b1646553f3/spec.trill.json')
NAME = 'Composite urban index: internet-fetched methods A and B'
NS = uuid.UUID('a9056c15-6242-4d72-89e6-fc53129fca37')

ACQUISITIONS = {
    'units': ('acquire_units.py', 'Fetch and prepare reporting units', -2300, 1700),
    'places': ('acquire_overture.py', 'Fetch Overture places (2026-08-19.0)', -1100, 0),
    'dwellings': ('acquire_dwellings.py', 'Fetch IBGE CNEFE and Census blocks', -1100, 560),
    'gtfs': ('acquire_gtfs.py', 'Fetch CTA and SPTrans GTFS', -1100, 1120),
    'buildings': ('acquire_buildings.py', 'Fetch Overture building heights (2026-08-19.0)', -1100, 1680),
    'roads': ('acquire_overture.py', 'Fetch Overture road segments (2026-08-19.0)', -1100, 2240),
    'ghsl': ('acquire_ghsl.py', 'Fetch and crop GHSL height/volume rasters', -1100, 3920),
}
SELECTORS = {
    'C · commercial establishments': ('places', ('sp_units', 'chi_units', 'places_sp', 'places_chi')),
    'R · residential establishments (dwellings)': ('dwellings', ('sp_units', 'chi_units', 'cnefe_sp', 'chi_blocks')),
    'H · transportation hubs': ('gtfs', ('sp_units', 'chi_units', 'gtfs_sp', 'gtfs_chi')),
    'V · building height (Overture)': ('buildings', ('sp_units', 'chi_units', 'buildings_sp', 'buildings_chi')),
    'N, L · streets and their length': ('roads', ('sp_units', 'chi_units', 'segments_sp', 'segments_chi')),
    'V · building height (GHSL volume ÷ surface)': ('ghsl', ('sp_units_municipal', 'chi_units_geojson', 'ghsl_sp', 'ghsl_chi')),
    'Land area (unit minus hydrography)': ('units', ('sp_units', 'chi_units', 'chi_hydrography')),
}


def ident(*parts):
    return str(uuid.uuid5(NS, '/'.join(parts)))


def edge(source, target):
    return {'id': ident('edge', source, target), 'source': source,
            'target': target, 'sourceHandle': 'out', 'targetHandle': 'in'}


def source_code(filename, acquisition):
    body = (HERE / filename).read_text()
    if filename == 'acquire_overture.py':
        kind = 'place' if acquisition == 'places' else 'segment'
        body = body.replace('__KIND__', kind)
    return body


def build(source):
    spec = json.loads(Path(source).read_text())
    flow = spec['dataflow']
    original_nodes = flow['nodes']
    assert len(original_nodes) == 40, 'The source flow changed; review the copy before building'
    ids = {name: ident('acquisition', name) for name in ACQUISITIONS}
    for name, (filename, title, x, y) in ACQUISITIONS.items():
        flow['nodes'].append({
            'id': ids[name], 'type': ('curio.builtin/data-loading' if name == 'units'
                                   else 'curio.builtin/computation-analysis'),
            'x': x, 'y': y, 'width': 920, 'height': 520,
            'title': title, 'in': 'DEFAULT', 'out': 'DEFAULT',
            'content': source_code(filename, name), 'saveOutputDataset': False,
            'metadata': {'keywords': []},
        })
        if name != 'units':
            flow['edges'].append(edge(ids['units'], ids[name]))
    selectors_found = 0
    maps_found = 0
    for node in original_nodes:
        title = node['title']
        if ' · sources · ' in title:
            factor = title.split(' · sources · ', 1)[1]
            acquisition, keys = SELECTORS[factor]
            node['type'] = 'curio.builtin/computation-analysis'
            node['content'] = ('# Select paths produced by the public acquisition node.\n'
                               '# No Curio dataset or local project file is read.\n'
                               f'return {{key: arg[key] for key in {keys!r}}}\n')
            flow['edges'].append(edge(ids[acquisition], node['id']))
            selectors_found += 1
        elif title.endswith('Chicago areas by closeness to Brás (map data)'):
            node['content'] = (HERE / 'chicago_map.py').read_text()
            maps_found += 1
    assert selectors_found == 11 and maps_found == 2
    flow['name'] = NAME
    flow['task'] = ('Run the same method A and method B composite index, fetching and '
                    'preparing every input from published internet sources at run time.')
    flow['description'] = ('Exact copy of the original two calculation pipelines with '
                           'internet acquisition nodes. Public transit feeds may have newer '
                           'content than the original local snapshot. Requires a Curio '
                           'runtime with node network access.')
    flow['timestamp'] = int(datetime.now(timezone.utc).timestamp() * 1000)
    flow['provenance_id'] = ident('provenance')
    flow['datasets'] = []
    flow['categories']['tags'] = list(dict.fromkeys(flow['categories']['tags'] + ['internet fetched']))
    return spec


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    ap.add_argument('--output', type=Path, default=HERE / 'internet_dataflow.trill.json')
    args = ap.parse_args()
    spec = build(args.source)
    args.output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    print(args.output, len(spec['dataflow']['nodes']), 'nodes',
          len(spec['dataflow']['edges']), 'edges')
