"""Refresh installed Curio node code from the reviewed per-feature files."""
import json
from pathlib import Path
from utk_curio.backend.app.projects import storage
pid='b4a2907d-bf08-469f-a4d5-761f59c9f531'
here=Path(__file__).resolve().parent
with storage.spec_write_lock('3',pid):
    spec=storage.read_spec('3',pid)
    changes=[]
    for node in spec['dataflow']['nodes']:
        title=node.get('title','')
        if title.startswith('Feature '):
            feature=title.split()[-1]
            code=(here/(feature+'.py')).read_text()
            if node['content']!=code:
                node['content']=code;changes.append(feature)
    if changes:storage.write_spec('3',pid,spec)
print(json.dumps({'updated':changes,'revision':storage.spec_revision('3',pid)}))
