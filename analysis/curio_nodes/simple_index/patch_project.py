"""Update an installed project in place: node code from nodes/*.py and loader code from dataflow.py (matched by node id),
and the dataset references. Positions, titles and everything else the user changed on the canvas are kept.
Holds Curio's spec lock and keeps a backup of the previous spec. Run like install_project.py:

  cd /path/to/curio && PYTHONPATH=$PWD venv/bin/python /path/to/patch_project.py --user 3 --project <id>
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dataflow  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--user', required=True)
ap.add_argument('--project', required=True)
ap.add_argument('--relayout', default='', help='title prefix of nodes to move to the module positions, e.g. "B · "')
args = ap.parse_args()
os.environ.setdefault('CURIO_LAUNCH_CWD', os.getcwd())
from utk_curio.backend.app.projects import storage  # noqa: E402

nodes, fresh_edges = dataflow.graph()
fresh = {n['id']: n for n in nodes}
now = dt.datetime.now(dt.timezone.utc).isoformat()
wanted = {r['datasetId']: r for r in dataflow.spec(now)['dataflow']['datasets']}
with storage.spec_write_lock(args.user, args.project):
    rev = storage.spec_revision(args.user, args.project)
    spec = storage.read_spec(args.user, args.project)
    backup = Path(__file__).parent / f'backup_spec_{args.project[:8]}_rev_{rev}.json'
    shutil.copy2(storage.project_dir(args.user, args.project) / 'spec.trill.json', backup)
    changed = []
    saved_ids = {n['id'] for n in spec['dataflow']['nodes']}
    for n in spec['dataflow']['nodes']:
        new = fresh.get(n['id'])
        if new and 'content' in new and n.get('content') != new['content']:
            n['content'] = new['content']
            changed.append(n.get('title', n['id']))
    retired = {dataflow.nid(*v) for v in dataflow.RETIRED.values()}
    removed = [n.get('title', n['id']) for n in spec['dataflow']['nodes'] if n['id'] in retired]
    spec['dataflow']['nodes'] = [n for n in spec['dataflow']['nodes'] if n['id'] not in retired]
    moved = []
    for n in spec['dataflow']['nodes']:  # nodes whose place the new structure changes take the module's position
        new = fresh.get(n['id'])
        if new and args.relayout and n.get('title', '').startswith(args.relayout) and (n['x'], n['y']) != (new['x'], new['y']):
            n['x'], n['y'] = new['x'], new['y']
            moved.append(n.get('title', n['id']))
    added = [n for i, n in fresh.items() if i not in saved_ids]
    spec['dataflow']['nodes'] += added
    old_edges = {e['id'] for e in spec['dataflow']['edges']}
    spec['dataflow']['edges'] = fresh_edges  # wiring is the module's; node positions and other node fields are kept
    new_edges = {e['id'] for e in fresh_edges}
    old = {r['datasetId']: r for r in spec['dataflow'].get('datasets', [])}
    spec['dataflow']['datasets'] = [old.get(d, r) for d, r in wanted.items()]
    storage.write_spec(args.user, args.project, spec)
print(json.dumps({'revision_before': rev, 'revision_after': storage.spec_revision(args.user, args.project), 'backup': backup.name,
                  'nodes_updated': changed, 'nodes_added': [n['title'] for n in added], 'nodes_removed': removed, 'nodes_moved': moved,
                  'edges_added': len(new_edges - old_edges), 'edges_removed': len(old_edges - new_edges), 'datasets_added': sorted(set(wanted) - set(old)), 'datasets_removed': sorted(set(old) - set(wanted))}, indent=1))
