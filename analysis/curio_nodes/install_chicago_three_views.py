"""Repair nested merge inputs and install three linked Curio visualization nodes."""
import copy
import json
import uuid
from graphlib import TopologicalSorter
from pathlib import Path

from utk_curio.backend.app.projects import storage

USER = '3'
PROJECT = 'b4a2907d-bf08-469f-a4d5-761f59c9f531'
HERE = Path(__file__).resolve().parent
MATRIX = '6492e1e6-1da4-497b-a5cb-f21f1236f1f4'
GROUPS = ['3ce15656-dc92-5f9b-b5e1-2924376fa41d',
          '9d7c54ab-b2cf-5e89-a8dd-676749b3cc97',
          '45a91220-4711-5814-87e7-ad9432f34434']
COLLECTOR = 'adf7b8d7-2dae-5a79-9aca-bd8f7722e618'
DATA = 'a7c7d684-abf7-532f-9cc9-27bd42e134ca'
PCA = '0deba6f0-28e2-4e81-a086-b8754b675352'
POOL = 'ca25d625-d3c8-470d-8f7d-2e81066b9590'


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, PROJECT + '/chicago-three-views-v1/' + label))


def edge(source, target, target_handle='in', source_handle='out', kind=None):
    item = {'id': uid('edge:' + source + ':' + target + ':' + target_handle),
            'source': source, 'target': target,
            'sourceHandle': source_handle, 'targetHandle': target_handle}
    if kind:
        item['type'] = kind
    return item


def specs():
    old = json.loads((HERE / 'viz_dashboard.json').read_text())
    scatter = copy.deepcopy(old['vconcat'][0]['hconcat'][0])
    bars = copy.deepcopy(old['vconcat'][0]['hconcat'][1])
    city_map = copy.deepcopy(old['vconcat'][1])
    base_transform = [
        {'calculate': "datum.interacted === '1' ? toNumber(datum.area_numbe) : 0",
         'as': 'selected_number'},
        {'joinaggregate': [{'op': 'max', 'field': 'selected_number',
                            'as': 'selected_max'}]},
        {'calculate': 'datum.selected_max > 0 ? datum.selected_max : 1',
         'as': 'focus_number'},
        {'calculate': "datum['d_' + (datum.focus_number < 10 ? '0' : '') + datum.focus_number]",
         'as': 'distance'},
        {'calculate': 'toNumber(datum.area_numbe) === datum.focus_number',
         'as': 'is_selected'},
    ]
    for chart in (scatter, bars, city_map):
        chart['$schema'] = old['$schema']
        chart['data'] = {'name': 'data'}
        chart['transform'] = copy.deepcopy(base_transform) + chart.get('transform', [])
    # A point selection is passed to Curio's Data Pool; it then marks the
    # selected row as interacted=1 and refreshes all three Vega nodes.
    pick = {'name': 'pick', 'select': {'type': 'point', 'on': 'click', 'clear': False}}
    scatter['params'] = [copy.deepcopy(pick)]
    city_map['layer'][0]['params'] = [copy.deepcopy(pick)]
    # The old dashboard used a local dropdown parameter named focus. All
    # filtering now follows the Data Pool's shared selected row.
    scatter['transform'][len(base_transform)]['calculate'] = 'datum.is_selected ? 1 : 0'
    bars['transform'][len(base_transform)]['filter'] = '!datum.is_selected'
    bars['encoding']['y']['sort']['order'] = 'ascending'
    for layer in city_map['layer'][1:]:
        layer['transform'][0]['filter'] = 'datum.is_selected'
    return scatter, bars, city_map


def mutate(spec):
    graph = spec['dataflow']
    nodes, edges = graph['nodes'], graph['edges']
    by_id = {node['id']: node for node in nodes}
    if not ({MATRIX, COLLECTOR, DATA, PCA} | set(GROUPS)) <= set(by_id):
        raise RuntimeError('Expected Chicago model nodes are missing')
    if POOL in by_id or uid('pca-scatter') in by_id:
        raise RuntimeError('Three-view repair was already installed')

    # An inline merge-of-merges is unsupported by Curio's input decoder. A
    # Python tuple is persisted as an artifact, so the final merge carries
    # artifact references that the worker can resolve normally.
    for index, group_id in enumerate(GROUPS):
        pack = copy.deepcopy(by_id[MATRIX])
        pack['id'] = uid('pack-domain-' + str(index))
        pack['title'] = ['Model input · morphology', 'Model input · built form',
                         'Model input · urban function'][index]
        pack['goal'] = 'Persist this selected feature group as one tuple artifact for the model matrix.'
        pack['content'] = 'return tuple(arg)'
        pack['x'], pack['y'] = 3650, [-1500, 800, 3300][index]
        nodes.append(pack)
        edges.append(edge(group_id, pack['id']))
        edges.append(edge(pack['id'], COLLECTOR, 'in_' + str(index)))
    edges[:] = [e for e in edges if not (e['target'] == COLLECTOR and
                                        e['source'] in GROUPS)]
    by_id[COLLECTOR]['title'] = 'Model inputs · persisted domains'

    old_spec = json.loads((HERE / 'viz_dashboard.json').read_text())
    if json.loads(by_id[PCA]['content']) != old_spec:
        raise RuntimeError('PCA dashboard changed since the last installation')
    scatter, bars, city_map = specs()
    pool = {'id': POOL, 'type': 'curio.builtin/data-pool',
            'x': 10100, 'y': 1050, 'saveOutputDataset': False,
            'content': '', 'out': 'DEFAULT', 'in': 'DEFAULT',
            'goal': 'Share one selected community area across the PCA plot, top-ten bars, and similarity map.',
            'metadata': {'keywords': []}, 'title': 'Chicago v1 · neighborhood selection'}
    nodes.append(pool)
    by_id[PCA]['title'] = 'Chicago v1 · 2D PCA neighborhoods'
    by_id[PCA]['goal'] = 'Click a neighborhood to choose the anchor; highlight its ten closest neighbors using retained PCA distance.'
    by_id[PCA]['content'] = json.dumps(scatter, indent=2)
    by_id[PCA]['x'], by_id[PCA]['y'] = 11200, 250
    by_id[PCA]['width'], by_id[PCA]['height'] = 700, 650
    by_id[PCA]['dashboardWidth'], by_id[PCA]['dashboardHeight'] = 700, 650
    bars_node = copy.deepcopy(by_id[PCA])
    bars_node['id'] = uid('top-ten-bars')
    bars_node['title'] = 'Chicago v1 · ten closest neighborhoods'
    bars_node['goal'] = 'Show the ten closest neighborhoods to the selected anchor, ordered by retained PCA distance.'
    bars_node['content'] = json.dumps(bars, indent=2)
    bars_node['x'], bars_node['y'] = 11200, 1000
    bars_node['width'], bars_node['height'] = 700, 650
    bars_node['dashboardX'], bars_node['dashboardY'] = 710, 0
    bars_node['dashboardWidth'], bars_node['dashboardHeight'] = 700, 650
    nodes.append(bars_node)
    map_node = copy.deepcopy(by_id[PCA])
    map_node['id'] = uid('similarity-map')
    map_node['title'] = 'Chicago v1 · similarity heatmap'
    map_node['goal'] = 'Click a community area boundary to select it; recolor all other boundaries by PCA distance and outline the selected area.'
    map_node['content'] = json.dumps(city_map, indent=2)
    map_node['x'], map_node['y'] = 11200, 1750
    map_node['width'], map_node['height'] = 800, 780
    map_node['dashboardX'], map_node['dashboardY'] = 1420, 0
    map_node['dashboardWidth'], map_node['dashboardHeight'] = 800, 780
    nodes.append(map_node)
    edges[:] = [e for e in edges if not (e['source'] == DATA and e['target'] == PCA)]
    edges.append(edge(DATA, POOL))
    for chart in (by_id[PCA], bars_node, map_node):
        edges.append(edge(POOL, chart['id']))
    for chart in (by_id[PCA], map_node):
        edges.append(edge(chart['id'], POOL, 'in/out', 'in/out', 'Interaction'))

    deps = {n['id']: set() for n in nodes}
    for e in edges:
        if e['source'] not in deps or e['target'] not in deps:
            raise RuntimeError('Broken edge endpoint')
        if e.get('sourceHandle') != 'in/out':
            deps[e['target']].add(e['source'])
    list(TopologicalSorter(deps).static_order())
    return {'nodes': len(nodes), 'edges': len(edges),
            'packing_nodes': [uid('pack-domain-' + str(i)) for i in range(3)],
            'visual_nodes': [PCA, bars_node['id'], map_node['id']]}


def main():
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
