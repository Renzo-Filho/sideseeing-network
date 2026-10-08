"""Create the separate internet-fetched Curio project through Curio's service.

Run from the Curio checkout with its venv and DATABASE_URL set to the running
instance's database. This never modifies the existing composite-index project.
"""
import argparse
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = 'Composite urban index: internet-fetched methods A and B'

parser = argparse.ArgumentParser()
parser.add_argument('--user', type=int, required=True)
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--update-id', help='Update this separate project after regenerating its spec')
args = parser.parse_args()
os.environ.setdefault('CURIO_LAUNCH_CWD', os.getcwd())
os.environ.setdefault('CURIO_SHARED_DATA', os.path.join(os.getcwd(), '.curio', 'data'))

from utk_curio.backend.app import create_app
from utk_curio.backend.extensions import db

app = create_app()
with app.app_context():
    from utk_curio.backend.app.projects.models import Project
    from utk_curio.backend.app.projects.schemas import ProjectCreate, ProjectUpdate
    from utk_curio.backend.app.projects.services import save_project, update_project
    from utk_curio.backend.app.users.models import User

    user = db.session.get(User, args.user)
    if user is None:
        raise SystemExit(f'No user {args.user} in {db.engine.url}')
    existing = db.session.query(Project).filter_by(user_id=user.id, name=NAME).first()
    if args.update_id:
        if existing is None or str(existing.id) != args.update_id:
            raise SystemExit('Update ID does not match this user’s separate internet project')
    elif existing is not None:
        raise SystemExit(f'A project named {NAME!r} already exists for user {args.user}')
    spec = json.loads((HERE / 'internet_dataflow.trill.json').read_text())
    flow = spec['dataflow']
    assert flow['name'] == NAME and not flow['datasets']
    print(json.dumps({'database': str(db.engine.url), 'user': user.id,
                      'name': NAME, 'nodes': len(flow['nodes']),
                      'edges': len(flow['edges']), 'datasets': len(flow['datasets'])}, indent=2))
    if not args.dry_run:
        if args.update_id:
            detail = update_project(user, args.update_id,
                                    ProjectUpdate(spec=spec, name=NAME,
                                                  description=flow['description']))
            print('updated project', detail.id if hasattr(detail, 'id') else detail)
        else:
            detail = save_project(user, ProjectCreate(name=NAME, spec=spec,
                                                     description=flow['description'],
                                                     thumbnail_accent='peach'))
            print('created project', detail.id if hasattr(detail, 'id') else detail)
