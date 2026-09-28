"""Install the PCA application and linked Chicago dashboard in Curio's saved graph."""
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
BASELINE = '62d4456c-b150-5f86-9814-fe85cc7420e7'
OLD_MAP = '2ae62559-ca57-4a48-a17c-6bf3d179f81c'
DASHBOARD = '0deba6f0-28e2-4e81-a086-b8754b675352'
OLD_POOL = 'ca25d625-d3c8-470d-8f7d-2e81066b9590'


def stable_id(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, PROJECT + '/chicago-pca-dashboard-v1/' + label))


def mutate(spec):
    graph = spec['dataflow']
    nodes, edges = graph['nodes'], graph['edges']
    by_id = {node['id']: node for node in nodes}
    if not {BASELINE, OLD_MAP, DASHBOARD, OLD_POOL} <= set(by_id):
        raise RuntimeError('Expected saved model and visualization placeholders are missing')
    baseline = by_id[BASELINE]
    if not baseline['content'].rstrip().endswith(
            'return (raw, pairwise, parameters, distance_matrix)'):
        raise RuntimeError('Baseline model code changed; inspect before overwriting')
    for node_id in (OLD_MAP, DASHBOARD, OLD_POOL):
        if any(e['source'] == node_id or e['target'] == node_id for e in edges):
            raise RuntimeError('Visualization placeholder is already wired')
    if by_id[DASHBOARD]['content'].strip():
        raise RuntimeError('Dashboard placeholder has authored content')

    baseline['content'] = (HERE / 'model_distances.py').read_text()
    baseline['title'] = 'Chicago v1 · calibrated weighted embedding'
    baseline['goal'] = (
        'Apply three equal domain budgets, calibrate eight feature families, '
        'and emit the exact weighted Euclidean embedding for PCA.')

    pca = copy.deepcopy(baseline)
    pca['id'] = stable_id('pca-application')
    pca['title'] = 'Chicago v1 · PCA-90 application'
    pca['x'], pca['y'] = 8150, 1050
    pca['goal'] = (
        'Fit PCA on all 77 weighted Chicago areas; retain the smallest '
        'component count explaining at least 90% variance; calculate all '
        '77x77 retained-space distances and PC1/PC2 coordinates.')
    pca['content'] = (HERE / 'model_pca.py').read_text()
    nodes.append(pca)

    prepared = copy.deepcopy(baseline)
    prepared['id'] = stable_id('dashboard-data')
    prepared['title'] = 'Chicago v1 · dashboard data'
    prepared['x'], prepared['y'] = 9150, 1050
    prepared['goal'] = (
        'Join all 77 PCA distances and Chicago Community Area names and '
        'boundaries into one compact, chart-ready table.')
    prepared['content'] = (HERE / 'viz_dashboard_data.py').read_text()
    nodes.append(prepared)

    dashboard = by_id[DASHBOARD]
    dashboard['title'] = 'Chicago v1 · interactive similarity dashboard'
    dashboard['x'], dashboard['y'] = 10150, 1050
    dashboard['width'], dashboard['height'] = 1100, 1150
    dashboard['dashboardPinned'] = True
    dashboard['dashboardX'], dashboard['dashboardY'] = 0, 0
    dashboard['dashboardWidth'], dashboard['dashboardHeight'] = 1100, 1150
    dashboard['goal'] = (
        'Select one Chicago Community Area to update its PC1/PC2 nearest '
        'neighbors, top-ten PCA distances, and high-contrast boundary map.')
    dashboard['content'] = (HERE / 'viz_dashboard.json').read_text()

    # The old Autark sample used an unrelated OSM Loop layer. Autark's stock
    # Curio behavior cannot recolor the other 76 areas when the anchor changes.
    nodes[:] = [node for node in nodes if node['id'] not in (OLD_MAP, OLD_POOL)]

    def connect(source, target):
        edges.append({'id': stable_id('edge:' + source + ':' + target),
                      'source': source, 'target': target,
                      'sourceHandle': 'out', 'targetHandle': 'in'})

    connect(BASELINE, pca['id'])
    connect(pca['id'], prepared['id'])
    connect(prepared['id'], DASHBOARD)

    if len({node['id'] for node in nodes}) != len(nodes):
        raise RuntimeError('Duplicate node ID')
    if len({edge['id'] for edge in edges}) != len(edges):
        raise RuntimeError('Duplicate edge ID')
    dependencies = {node['id']: set() for node in nodes}
    for edge in edges:
        if edge['source'] not in dependencies or edge['target'] not in dependencies:
            raise RuntimeError('Edge endpoint is missing')
        dependencies[edge['target']].add(edge['source'])
    list(TopologicalSorter(dependencies).static_order())
    incoming = Counter(edge['target'] for edge in edges)
    outgoing = Counter(edge['source'] for edge in edges)
    return {'nodes': len(nodes), 'edges': len(edges),
            'max_in': max(incoming.values()), 'max_out': max(outgoing.values()),
            'pca_node': pca['id'], 'dashboard_data_node': prepared['id'],
            'dashboard_node': DASHBOARD}


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
