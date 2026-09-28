"""Update the three unresolved feature descriptions in the saved Curio graph."""
import json
from pathlib import Path

from utk_curio.backend.app.projects import storage

USER = '3'
PROJECT = 'b4a2907d-bf08-469f-a4d5-761f59c9f531'
HERE = Path(__file__).resolve().parent
OLD = {
    'M7': 'Parcel density: Cook parcel, PIN, condo and assessment records do not yet define one citywide parcel entity without duplicate tax interests.',
    'B2': 'Building height distribution: a complete building-level height source linked to the footprint universe is not installed.',
    'B3': 'FAR proxy: parcel-floor-area and footprint entities are not reconciled across all building and condo types.',
}

with storage.spec_write_lock(USER, PROJECT):
    revision = storage.spec_revision(USER, PROJECT)
    spec = storage.read_spec(USER, PROJECT)
    nodes = spec['dataflow']['nodes']
    for feature, old_reason in OLD.items():
        matches = [node for node in nodes if node.get('title') == f'Feature {feature}']
        if len(matches) != 1 or matches[0]['content'].count(old_reason) != 1:
            raise RuntimeError(f'{feature} changed in Curio; inspect before updating')
        code = matches[0]['content']
        new_code = (HERE / f'{feature}.py').read_text()
        if code.replace(old_reason, new_code.split("'reason':['", 1)[1].split("']*77", 1)[0]) != new_code:
            raise RuntimeError(f'{feature} has other edits in Curio; inspect before updating')
        matches[0]['content'] = new_code
    backup = HERE / f'backup_spec_rev_{revision}.json'
    if backup.exists():
        raise RuntimeError(f'Backup already exists: {backup}')
    backup.write_text((storage.project_dir(USER, PROJECT) / 'spec.trill.json').read_text())
    storage.write_spec(USER, PROJECT, spec)

print(json.dumps({'old_revision': revision, 'new_revision': storage.spec_revision(USER, PROJECT),
                  'updated': list(OLD), 'backup': str(backup)}))
