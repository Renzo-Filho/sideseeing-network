"""Execute the generated graph against acquisitions already fetched to scratch.

This is a builder-side verification utility, not a dependency of the dataflow.
Use after independently running each acquisition node into one scratch folder.
"""
import argparse
import json
from pathlib import Path
import textwrap
import time

HERE = Path(__file__).resolve().parent


def cached_paths(root):
    p = lambda name: str(root / name)
    out = {'scratch': str(root),
           'sp_units': p('sao_paulo_units.parquet'),
           'chi_units': p('chicago_units.parquet'),
           'sp_units_municipal': p('sao_paulo_districts.geojson'),
           'chi_units_geojson': p('chicago_areas.geojson'),
           'chi_hydrography': p('chicago_hydro.geojson'),
           'places_sp': p('overture_place_sp.parquet'),
           'places_chi': p('overture_place_chi.parquet'),
           'cnefe_sp': p('cnefe_sao_paulo.parquet'),
           'chi_blocks': p('chicago_blocks.parquet'),
           'segments_sp': p('overture_segment_sp.parquet'),
           'segments_chi': p('overture_segment_chi.parquet'),
           'buildings_sp': p('overture_buildings_sp_heights.parquet'),
           'buildings_chi': p('overture_buildings_chi.parquet')}
    for city in ('sp', 'chi'):
        out['gtfs_' + city] = {key: p(f'gtfs_{city}_{key}.txt')
                               for key in ('stops', 'routes', 'trips', 'stop_times')}
        out['ghsl_' + city] = {key: p(f'ghsl_{city}_{key}.tif')
                               for key in ('anbh', 'agbh', 'volume')}
    return out


def run(root):
    flow = json.loads((HERE / 'internet_dataflow.trill.json').read_text())['dataflow']
    nodes = {node['id']: node for node in flow['nodes']}
    inputs = {}
    for edge in flow['edges']:
        inputs.setdefault(edge['target'], []).append(edge)
    outputs = {}
    cached = cached_paths(root)
    while len(outputs) < len(nodes):
        ready = [node for node in nodes.values() if node['id'] not in outputs
                 and all(edge['source'] in outputs for edge in inputs.get(node['id'], []))]
        if not ready:
            raise ValueError('Cycle or missing graph input')
        for node in ready:
            node_id = node['id']
            incoming = sorted(inputs.get(node_id, []), key=lambda edge: edge['targetHandle'])
            if node['title'].startswith('Fetch '):
                outputs[node_id] = cached
            elif node['type'] == 'curio.builtin/merge-flow':
                outputs[node_id] = [outputs[edge['source']] for edge in incoming]
            elif node['type'] in ('curio.builtin/vis-simple', 'curio.builtin/vis-vega'):
                outputs[node_id] = outputs[incoming[0]['source']]
            else:
                argument = outputs[incoming[0]['source']] if incoming else None
                namespace = {}
                exec('def userCode(arg):\n' + textwrap.indent(node['content'], '    '), namespace)
                started = time.monotonic()
                outputs[node_id] = namespace['userCode'](argument)
                print(f'{time.monotonic()-started:6.1f}s {node["title"]}', flush=True)
    for lane in 'AB':
        index = next(outputs[node['id']] for node in nodes.values()
                     if node['title'] == f'{lane} · index (scale and sum)')
        assert len(index) == 173 and index.unit_id.is_unique
        print(lane, 'index rows', len(index), 'top',
              index.sort_values('rank').iloc[0][['unit_id', 'index']].to_dict(), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('scratch', type=Path)
    run(parser.parse_args().scratch)
