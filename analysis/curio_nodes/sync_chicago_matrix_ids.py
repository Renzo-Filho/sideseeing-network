"""Install explicit matrix IDs after Curio's Parquet index round-trip check."""
import json
from pathlib import Path

from utk_curio.backend.app.projects import storage

USER = '3'
PROJECT = 'b4a2907d-bf08-469f-a4d5-761f59c9f531'
HERE = Path(__file__).resolve().parent
SOURCES = {
    '62d4456c-b150-5f86-9814-fe85cc7420e7': 'model_distances.py',
    '6ebb9193-4bc9-59d2-81e1-9ef7560d44d1': 'model_pca.py',
    'a7c7d684-abf7-532f-9cc9-27bd42e134ca': 'viz_dashboard_data.py',
}


with storage.spec_write_lock(USER, PROJECT):
    revision = storage.spec_revision(USER, PROJECT)
    spec = storage.read_spec(USER, PROJECT)
    found = set()
    for node in spec['dataflow']['nodes']:
        if node['id'] in SOURCES:
            node['content'] = (HERE / SOURCES[node['id']]).read_text()
            found.add(node['id'])
    if found != set(SOURCES):
        raise RuntimeError('Expected Chicago model nodes are missing')
    backup = HERE / f'backup_spec_rev_{revision}.json'
    if backup.exists():
        raise RuntimeError(f'Backup already exists: {backup}')
    backup.write_text((storage.project_dir(USER, PROJECT) / 'spec.trill.json').read_text())
    storage.write_spec(USER, PROJECT, spec)
print(json.dumps({'old_revision': revision,
                  'new_revision': storage.spec_revision(USER, PROJECT),
                  'backup': str(backup)}, indent=2))
