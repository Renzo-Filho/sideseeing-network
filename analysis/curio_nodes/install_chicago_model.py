"""Install the selected eight-feature Chicago model path in the saved Curio graph."""
import argparse
import copy
import json
import uuid
from collections import Counter
from graphlib import TopologicalSorter
from pathlib import Path

from utk_curio.backend.app.projects import storage

USER = '3'
PROJECT = 'b4a2907d-bf08-469f-a4d5-761f59c9f531'
HERE = Path(__file__).resolve().parent
ASSEMBLY = '6492e1e6-1da4-497b-a5cb-f21f1236f1f4'
FULL_COLLECTOR = '33369274-e6e8-4701-8097-899096858126'
FEATURES = {
    'M1': '42600ba3-f1c7-4d26-8f6e-3c3aac08e3b6',
    'M6': '250573c1-83bc-43e3-86aa-f8e142769dc8',
    'B1': '99dc0682-7fd3-4815-abb4-91e4c6df4f7f',
    'BV': '07c52621-ceca-4eaa-86f4-969e5d6fb367',
    'U1': 'f9379c07-8f65-4f7e-b477-1d4176200472',
    'U2': '3b90cf06-0905-4dda-bbfe-78d6105c9e9a',
    'U3': 'f3b61f7b-a438-4b5a-87ee-e43798cded98',
    'U4': '52e0cf25-8189-45bc-9dc1-3d4d35d8a8aa',
}
LANES = {'morph': ['M1', 'M6'], 'built': ['B1', 'BV'],
         'urban': ['U1', 'U2', 'U3', 'U4']}
POSITIONS = {'morph': (3100, -1500), 'built': (3100, 800),
             'urban': (3100, 3300)}


def stable_id(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, PROJECT + '/chicago-model-v0/' + label))


def mutate(spec):
    graph = spec['dataflow']
    nodes = graph['nodes']
    edges = graph['edges']
    by_id = {node['id']: node for node in nodes}
    if not set(FEATURES.values()) | {ASSEMBLY, FULL_COLLECTOR} <= set(by_id):
        raise RuntimeError('Expected feature or assembly node is missing')
    assembly = by_id[ASSEMBLY]
    if assembly['content'].strip():
        raise RuntimeError('Assembly node now has saved code; inspect before overwriting')
    direct = [edge for edge in edges if edge['target'] == ASSEMBLY]
    if len(direct) != 1 or direct[0]['source'] != FULL_COLLECTOR:
        raise RuntimeError('Assembly incoming edge changed; inspect before editing')
    edges.remove(direct[0])

    merge_prototype = copy.deepcopy(by_id[FULL_COLLECTOR])
    for lane, names in LANES.items():
        node = copy.deepcopy(merge_prototype)
        node['id'] = stable_id('select-' + lane)
        node['title'] = 'Model inputs · ' + lane.title()
        node['x'], node['y'] = POSITIONS[lane]
        node['goal'] = 'Select only ' + ', '.join(names) + ' for the Chicago-only candidate model.'
        node['content'] = ''
        nodes.append(node)
        by_id[node['id']] = node
    selected = copy.deepcopy(merge_prototype)
    selected['id'] = stable_id('selected-collector')
    selected['title'] = 'Model inputs · three domains'
    selected['x'], selected['y'] = (4100, 1050)
    selected['goal'] = 'Merge selected morphology, built-form and urban-function outputs.'
    selected['content'] = ''
    nodes.append(selected)
    by_id[selected['id']] = selected

    full = by_id[FULL_COLLECTOR]
    full['title'] = 'All feature outputs · construction'
    full['x'], full['y'] = (3150, 4900)
    full['goal'] = 'Collect all constructed and diagnostic feature outputs; not a model input.'
    assembly['title'] = 'Chicago v0 · selected feature matrix'
    assembly['x'], assembly['y'] = (5100, 1050)
    assembly['goal'] = 'Join the eight selected 77-area features with explicit source and domain checks.'
    assembly['content'] = (HERE / 'model_matrix.py').read_text()

    fit = copy.deepcopy(assembly)
    fit['id'] = stable_id('fit')
    fit['title'] = 'Chicago v0 · fit transforms'
    fit['x'], fit['y'] = (6100, 1050)
    fit['goal'] = 'Fit seven scalar transforms and M6 composition on Chicago only.'
    fit['content'] = (HERE / 'model_fit.py').read_text()
    nodes.append(fit)
    by_id[fit['id']] = fit
    distance = copy.deepcopy(assembly)
    distance['id'] = stable_id('distances')
    distance['title'] = 'Chicago v0 · pairwise distances'
    distance['x'], distance['y'] = (7100, 1050)
    distance['goal'] = 'Calculate domain-balanced Chicago pairwise distances and family contributions.'
    distance['content'] = (HERE / 'model_distances.py').read_text()
    nodes.append(distance)
    by_id[distance['id']] = distance
    for node in nodes:
        if node['title'] == 'Future map (unconfigured)':
            node['x'], node['y'] = (8150, 500)
        elif node['title'] == 'Future chart (unconfigured)':
            node['x'], node['y'] = (8150, 1500)
        elif node['title'] == 'Future output pool (unconfigured)':
            node['x'], node['y'] = (9150, 1000)

    def connect(source, target, handle='in'):
        edges.append({'id': stable_id('edge:' + source + ':' + target + ':' + handle),
                      'source': source, 'target': target,
                      'sourceHandle': 'out', 'targetHandle': handle})

    for lane, names in LANES.items():
        for index, name in enumerate(names):
            connect(FEATURES[name], stable_id('select-' + lane), f'in_{index}')
    for index, lane in enumerate(LANES):
        connect(stable_id('select-' + lane), selected['id'], f'in_{index}')
    connect(selected['id'], ASSEMBLY)
    connect(ASSEMBLY, fit['id'])
    connect(fit['id'], distance['id'])

    if len({edge['id'] for edge in edges}) != len(edges):
        raise RuntimeError('Duplicate edge ID')
    dependencies = {node['id']: set() for node in nodes}
    for edge in edges:
        dependencies[edge['target']].add(edge['source'])
    list(TopologicalSorter(dependencies).static_order())
    incoming = Counter(edge['target'] for edge in edges)
    outgoing = Counter(edge['source'] for edge in edges)
    return {'nodes': len(nodes), 'edges': len(edges), 'max_in': max(incoming.values()),
            'max_out': max(outgoing.values()), 'model_node': distance['id']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.dry_run:
        result = mutate(copy.deepcopy(storage.read_spec(USER, PROJECT)))
        print(json.dumps({'dry_run': True, **result}, indent=2))
        return
    with storage.spec_write_lock(USER, PROJECT):
        revision = storage.spec_revision(USER, PROJECT)
        spec = storage.read_spec(USER, PROJECT)
        result = mutate(spec)
        backup = HERE / f'backup_spec_rev_{revision}.json'
        if backup.exists():
            raise RuntimeError(f'Backup already exists: {backup}')
        backup.write_text((storage.project_dir(USER, PROJECT) / 'spec.trill.json').read_text())
        storage.write_spec(USER, PROJECT, spec)
    print(json.dumps({'old_revision': revision,
                      'new_revision': storage.spec_revision(USER, PROJECT),
                      'backup': str(backup), **result}, indent=2))


if __name__ == '__main__':
    main()
