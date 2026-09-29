"""One end-to-end Curio executor check using the last successful feature outputs."""
import json
import textwrap
from pathlib import Path

from utk_curio.backend.app.projects import storage
from utk_curio.sandbox.app.worker import execute_code
from utk_curio.sandbox.util.parsers import load_from_duckdb

USER = '3'
PROJECT = 'b4a2907d-bf08-469f-a4d5-761f59c9f531'
ROOT = Path('/home/renzo/Documents/GitHub/curio')
RUNTIME = ROOT / '.curio/users' / USER / 'projects' / PROJECT / 'runtime'
FEATURES = [
    ['42600ba3-f1c7-4d26-8f6e-3c3aac08e3b6', '250573c1-83bc-43e3-86aa-f8e142769dc8'],
    ['99dc0682-7fd3-4815-abb4-91e4c6df4f7f', '07c52621-ceca-4eaa-86f4-969e5d6fb367'],
    ['f9379c07-8f65-4f7e-b477-1d4176200472', '3b90cf06-0905-4dda-bbfe-78d6105c9e9a',
     'f3b61f7b-a438-4b5a-87ee-e43798cded98', '52e0cf25-8189-45bc-9dc1-3d4d35d8a8aa'],
]
PIPELINE = [
    '6492e1e6-1da4-497b-a5cb-f21f1236f1f4',
    'e9f41666-e27d-5850-96e9-764499915c39',
    '62d4456c-b150-5f86-9814-fe85cc7420e7',
    '6ebb9193-4bc9-59d2-81e1-9ef7560d44d1',
    'a7c7d684-abf7-532f-9cc9-27bd42e134ca',
]


def run(code, refs, dataset_paths=None):
    merged = isinstance(refs, list)
    result = execute_code(
        textwrap.indent(code.rstrip(), '    ') + '\n',
        repr(refs) if merged else refs['path'],
        'curio.builtin/computation-analysis@1', 'outputs' if merged else 'file',
        launch_dir=str(ROOT), session_id=None, save_dataset=False,
        dataset_paths=dataset_paths or {},
    )
    if result.get('stderr') or not result.get('output', {}).get('path'):
        raise RuntimeError(result.get('stderr') or result)
    return result['output']


def main():
    graph = storage.read_spec(USER, PROJECT)['dataflow']
    nodes = {n['id']: n for n in graph['nodes']}
    groups = []
    for family in FEATURES:
        refs = [json.loads((RUNTIME / (node_id + '.json')).read_text())['output']
                for node_id in family]
        assert all(ref.get('path') for ref in refs)
        groups.append(run('return tuple(arg)', refs))
    result = run(nodes[PIPELINE[0]]['content'], groups)
    frame = load_from_duckdb(result['path'])
    assert frame.shape == (77, 18)
    print('matrix:', frame.shape, flush=True)
    for node_id in PIPELINE[1:]:
        code = nodes[node_id]['content']
        datasets = {}
        if node_id == PIPELINE[-1]:
            dataset_id = 'data.cityofchicago.community-areas-sideseeing'
            files = list((ROOT / 'datasets' / (dataset_id + '@1') / 'data').iterdir())
            assert len(files) == 1
            datasets[dataset_id] = str(files[0])
        result = run(code, result, datasets)
        value = load_from_duckdb(result['path'])
        print(nodes[node_id]['title'], result['dataType'], flush=True)
        if node_id == PIPELINE[-2]:
            assert value[3].shape == (77, 78)
    assert value.shape == (77, 84)
    assert value['geometry'].map(lambda item: item['type'] in ('Polygon', 'MultiPolygon')).all()
    Path('/tmp/chicago_dashboard_rows.json').write_text(
        value.to_json(orient='records'))
    print('Curio executor completed matrix, transform, weighted distance, PCA, and chart data', flush=True)


if __name__ == '__main__':
    main()
