"""Install four linked Vega views on the Chicago copy for interaction testing."""
import copy
import json
import uuid
from graphlib import TopologicalSorter
from pathlib import Path

from utk_curio.backend.app.projects import storage


USER = '3'
PROJECT = 'c2615775-fe6b-4615-951e-5c26204ab4a7'
HERE = Path(__file__).resolve().parent
DATA = 'a7c7d684-abf7-532f-9cc9-27bd42e134ca'
VIEW = '0deba6f0-28e2-4e81-a086-b8754b675352'
POOL = 'ca25d625-d3c8-470d-8f7d-2e81066b9590'


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, PROJECT + '/independent-views/' + label))


def edge(source, target, interaction=False):
    handle = 'in/out' if interaction else 'out'
    return {'id': uid('edge-' + source + '-' + target + '-' + handle),
            'source': source, 'target': target,
            'sourceHandle': handle,
            'targetHandle': 'in/out' if interaction else 'in',
            **({'type': 'Interaction'} if interaction else {})}


def chart_specs():
    unified = json.loads((HERE / 'viz_dashboard.json').read_text())
    scatter, bars = (copy.deepcopy(v) for v in unified['vconcat'][0]['hconcat'])
    city_map, radar = (copy.deepcopy(v) for v in unified['vconcat'][1]['hconcat'])
    base = [
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
    for chart in (scatter, bars, city_map, radar):
        chart['$schema'] = unified['$schema']
        chart['data'] = {'name': 'data'}
        chart['transform'] = copy.deepcopy(base) + chart.get('transform', [])
    # The area ID is a stable selection key, and the dropdown also works when
    # a point is hard to click at a small canvas zoom.
    pick = {'name': 'pick', 'select': {'type': 'point', 'fields': ['area_numbe'],
                                     'on': 'click', 'clear': False, 'toggle': False}}
    scatter['params'] = [{**copy.deepcopy(pick), 'bind': unified['params'][0]['bind']}]
    city_map['layer'][0]['params'] = [copy.deepcopy(pick)]
    scatter['transform'][len(base)]['calculate'] = 'datum.is_selected ? 1 : 0'
    bars['transform'][len(base)]['filter'] = '!datum.is_selected'
    bars['encoding']['y']['sort']['order'] = 'ascending'
    for layer in city_map['layer'][1:]:
        layer['transform'][0]['filter'] = 'datum.is_selected'
    radar['transform'][len(base)]['filter'] = 'datum.is_selected'
    return scatter, bars, city_map, radar


def mutate(spec):
    graph = spec['dataflow']
    nodes, edges = graph['nodes'], graph['edges']
    by_id = {node['id']: node for node in nodes}
    if DATA not in by_id or VIEW not in by_id or POOL in by_id:
        raise RuntimeError('Copy is missing the expected unified dashboard state')
    if not set(json.loads(by_id[VIEW]['content'])) >= {'vconcat', 'params'}:
        raise RuntimeError('Expected the original unified Vega dashboard')
    by_id[DATA]['content'] = (HERE / 'viz_dashboard_data.py').read_text()
    scatter, bars, city_map, radar = chart_specs()
    pool = {'id': POOL, 'type': 'curio.builtin/data-pool', 'x': 10100, 'y': 1050,
            'saveOutputDataset': False, 'content': '', 'out': 'DEFAULT', 'in': 'DEFAULT',
            'goal': 'Share the clicked Chicago Community Area across four Vega views.',
            'metadata': {'keywords': []}, 'title': 'Chicago copy · selected area'}
    nodes.append(pool)
    configs = [
        (VIEW, 'Chicago copy · PCA neighborhoods', scatter, 0, 0, 700, 650),
        (uid('bars'), 'Chicago copy · ten closest neighborhoods', bars, 720, 0, 700, 650),
        (uid('map'), 'Chicago copy · similarity map', city_map, 0, 670, 800, 780),
        (uid('radar'), 'Chicago copy · feature radar', radar, 820, 670, 700, 650),
    ]
    for index, (node_id, title, chart, dx, dy, width, height) in enumerate(configs):
        node = by_id[VIEW] if index == 0 else copy.deepcopy(by_id[VIEW])
        node.update(id=node_id, title=title, content=json.dumps(chart, indent=2),
                    x=11200 + dx, y=250 + dy, width=width, height=height,
                    dashboardX=dx, dashboardY=dy,
                    dashboardWidth=width, dashboardHeight=height)
        if index:
            nodes.append(node)
    edges[:] = [e for e in edges if not (e['source'] == DATA and e['target'] == VIEW)]
    edges.append(edge(DATA, POOL))
    for node_id, *_ in configs:
        edges.append(edge(POOL, node_id))
    for node_id in (VIEW, uid('map')):
        edges.append(edge(node_id, POOL, interaction=True))
    deps = {node['id']: set() for node in nodes}
    for item in edges:
        if item['sourceHandle'] != 'in/out':
            deps[item['target']].add(item['source'])
    list(TopologicalSorter(deps).static_order())
    return {'nodes': len(nodes), 'edges': len(edges),
            'visual_nodes': [item[0] for item in configs]}


def main():
    with storage.spec_write_lock(USER, PROJECT):
        revision = storage.spec_revision(USER, PROJECT)
        spec = storage.read_spec(USER, PROJECT)
        result = mutate(spec)
        backup = Path('/tmp') / f'backup_copy_spec_rev_{revision}_before_independent.json'
        if backup.exists():
            raise FileExistsError(backup)
        backup.write_text((storage.project_dir(USER, PROJECT) / 'spec.trill.json').read_text())
        storage.write_spec(USER, PROJECT, spec)
    print(json.dumps({'old_revision': revision,
                      'new_revision': storage.spec_revision(USER, PROJECT),
                      'backup': str(backup), **result}, indent=2))


if __name__ == '__main__':
    main()
