"""Create the Curio project holding both lanes (method A on top, method B below) through Curio's own save_project,
so the database row, spec and manifest are written together. Run from the Curio checkout with its venv:

  cd /path/to/curio && venv/bin/python /path/to/install_project.py --user 3 [--dry-run]

--dry-run prints the database and user it would write to and the node count, and writes nothing.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dataflow  # noqa: E402

NAME = 'Composite urban index: method A and method B'

ap = argparse.ArgumentParser()
ap.add_argument('--user', type=int, required=True)
ap.add_argument('--dry-run', action='store_true')
args = ap.parse_args()
os.environ.setdefault('CURIO_LAUNCH_CWD', os.getcwd())
os.environ.setdefault('CURIO_SHARED_DATA', os.path.join(os.getcwd(), '.curio', 'data'))

from utk_curio.backend.app import create_app  # noqa: E402
from utk_curio.backend.extensions import db  # noqa: E402

app = create_app()
with app.app_context():
    from utk_curio.backend.app.projects.models import Project
    from utk_curio.backend.app.projects.schemas import ProjectCreate
    from utk_curio.backend.app.projects.services import save_project
    from utk_curio.backend.app.users.models import User

    user = db.session.get(User, args.user)
    if user is None:
        raise SystemExit(f'no user {args.user} in {db.engine.url}')
    if db.session.query(Project).filter_by(user_id=user.id, name=NAME).first():
        raise SystemExit(f'a project named "{NAME}" already exists for user {args.user}; refusing to duplicate')
    spec = dataflow.spec(dt.datetime.now(dt.timezone.utc).isoformat())
    store = Path(os.environ['CURIO_LAUNCH_CWD']) / '.curio' / 'users' / str(args.user) / 'datasets'
    missing = [d for d in dataflow.dataset_ids() if not (store / f'{d}@1' / 'manifest.json').exists()]
    print(json.dumps({'database': str(db.engine.url), 'user': user.id, 'nodes': len(spec['dataflow']['nodes']),
                      'edges': len(spec['dataflow']['edges']), 'datasets': len(spec['dataflow']['datasets']), 'missing_datasets': missing}, indent=1))
    if missing:
        raise SystemExit('register the missing datasets first (register_datasets.py)')
    if not args.dry_run:
        detail = save_project(user, ProjectCreate(name=NAME, spec=spec, description=spec['dataflow']['description'], thumbnail_accent='peach'))
        print('created project', detail.id if hasattr(detail, 'id') else detail)
