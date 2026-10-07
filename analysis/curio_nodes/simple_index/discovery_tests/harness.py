"""Drive Curio's Discovery Catalog service as a given user, the way its HTTP routes do, and record every call.

Usage (from the Curio checkout, Curio venv, same env as install_project.py):
  python harness.py search-all "<query>"
  python harness.py search <source_dir> "<query>"
  python harness.py describe <source_dir> <resource_id>
  python harness.py acquire <source_dir> <resource_id> '<json: {"format":..., "title":..., "parameters":...}>'
Each call appends {call, args, result or error, seconds} to results.jsonl next to this file.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
USER = int(os.environ.get('CURIO_TEST_USER', '3'))

from utk_curio.backend.app import create_app  # noqa: E402
from utk_curio.backend.extensions import db  # noqa: E402

app = create_app()


def record(entry):
    with open(HERE / 'results.jsonl', 'a') as f:
        f.write(json.dumps(entry, default=str, ensure_ascii=False) + '\n')


def main(cmd, *args):
    with app.app_context(), app.test_request_context():
        from utk_curio.backend.app.discovery.service import DiscoveryService
        from utk_curio.backend.app.projects.services import _user_dir_key
        from utk_curio.backend.app.users.models import User
        user = db.session.get(User, USER)
        svc = DiscoveryService(_user_dir_key(user), user=user, icon_url_for=lambda m: None)
        t = time.time()
        entry = {'call': cmd, 'args': args, 'at': time.strftime('%Y-%m-%dT%H:%M:%S')}
        try:
            if cmd == 'search-all':
                out = svc.search_all(q=args[0], fmt=None, limit=None, provider=None)
            elif cmd == 'search':
                out = svc.search_source(args[0], q=args[1], fmt=None, limit=None, cursor=None, rescan=len(args) > 2)
            elif cmd == 'describe':
                out = svc.describe_resource(args[0], args[1])
            elif cmd == 'acquire':
                body = json.loads(args[2]) if len(args) > 2 else {}
                out = svc.start_acquire(args[0], args[1], fmt=body.get('format'), title=body.get('title'), refresh=False,
                                        filters=body.get('filters'), files=body.get('files'), parameters=body.get('parameters'))
                job = dict(out)
                while job.get('jobId') and job.get('status') not in ('completed', 'failed', 'refused', 'cancelled'):
                    time.sleep(2)
                    job = svc.get_job(job['jobId'])
                    print('  job', job.get('status'), job.get('stageMessage'), job.get('bytesRead'), flush=True)
                out = {'start': out, 'final': job}
            else:
                raise SystemExit(f'unknown command {cmd}')
            entry['result'] = out
        except Exception as exc:  # recorded as evidence, then re-raised for the console
            entry['error'] = f'{type(exc).__name__}: {exc}'
            entry['traceback'] = traceback.format_exc()
        entry['seconds'] = round(time.time() - t, 1)
        record(entry)
        print(json.dumps({k: v for k, v in entry.items() if k != 'traceback'}, default=str, ensure_ascii=False, indent=1)[:6000])


if __name__ == '__main__':
    main(*sys.argv[1:])
