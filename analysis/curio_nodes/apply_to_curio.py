"""Install one Chicago feature per Curio node, preserving agent sessions and source loaders."""
import copy
import json
import pathlib
import shutil
import uuid
from utk_curio.backend.app.projects import storage

PROJECT='b4a2907d-bf08-469f-a4d5-761f59c9f531'
USER='3'
HERE=pathlib.Path(__file__).resolve().parent
features=['M1','M2','M3','M4','M6','M7','B1','B2','B3','BV','U1','U2','U3','U4']
existing={'M1':'42600ba3-f1c7-4d26-8f6e-3c3aac08e3b6',
          'M6':'250573c1-83bc-43e3-86aa-f8e142769dc8',
          'B1':'99dc0682-7fd3-4815-abb4-91e4c6df4f7f',
          'U3':'f3b61f7b-a438-4b5a-87ee-e43798cded98'}
source_merge='b5167303-6bfe-4386-a2c0-6cc4f06acbb8'
collector='33369274-e6e8-4701-8097-899096858126'
future_model='6492e1e6-1da4-497b-a5cb-f21f1236f1f4'
position={
 'M1':(760,-1200),'M2':(760,-600),'M3':(760,0),'M4':(1850,0),'M6':(1850,-1200),
 'M7':(760,600),'B1':(760,1200),'B2':(760,1800),'B3':(760,2400),'BV':(760,3000),
 'U1':(1850,600),'U2':(1850,1200),'U3':(1850,1800),'U4':(1850,2400)}
with storage.spec_write_lock(USER,PROJECT):
    base=storage.project_dir(USER,PROJECT)
    rev=storage.spec_revision(USER,PROJECT)
    spec=storage.read_spec(USER,PROJECT)
    if spec is None:raise RuntimeError('Project missing')
    graph=spec['dataflow']; nodes=graph['nodes']
    byid={n['id']:n for n in nodes}
    if any(i not in byid for i in list(existing.values())+[source_merge,collector,future_model]):
        raise RuntimeError('Project graph changed; inspect before applying')
    if any(n.get('title','').startswith('Feature ') for n in nodes):
        raise RuntimeError('Feature nodes already installed; refusing to duplicate')
    backup=HERE/f'backup_spec_rev_{rev}.json'
    if backup.exists():raise RuntimeError('Backup file already exists; inspect before applying')
    shutil.copy2(base/'spec.trill.json',backup)
    prototype=copy.deepcopy(byid[existing['U3']])
    ids={}
    for feature in features:
        if feature in existing:
            node=byid[existing[feature]]
        else:
            node=copy.deepcopy(prototype)
            node['id']=str(uuid.uuid4())
            nodes.append(node)
        ids[feature]=node['id']
        node['title']='Feature '+feature
        node['content']=(HERE/(feature+'.py')).read_text()
        node['goal']='Construct Chicago '+feature+' only; scientific evaluation and model fitting are later stages.'
        node['x'],node['y']=position[feature]
        node['width']=850;node['height']=425
    byid[collector]['title']='Collect individual Chicago feature outputs'
    byid[collector]['x']=3020;byid[collector]['y']=800
    byid[future_model]['title']='Future model assembly — unconfigured'
    # Source loaders stay connected to source merge. The rest is rebuilt explicitly.
    source_ids={n['id'] for n in nodes if n['type']=='curio.builtin/data-loading'}
    edges=[e for e in graph['edges'] if e['source'] in source_ids and e['target']==source_merge]
    def connect(source,target,handle):
        edges.append({'id':str(uuid.uuid4()),'source':source,'target':target,
                      'sourceHandle':'out','targetHandle':handle})
    for feature in features:
        if feature=='M6':connect(ids['M1'],ids['M6'],'in')
        elif feature=='M4':connect(ids['M3'],ids['M4'],'in')
        else:connect(source_merge,ids[feature],'in')
    for i,feature in enumerate(features):connect(ids[feature],collector,f'in_{i}')
    graph['edges']=edges
    # Explicitly attach the existing catalog raster required by BV.
    if not any(d.get('datasetId')=='data.ghsl.chicago-h-anbh-e2018' for d in graph['datasets']):
        graph['datasets'].append({'datasetId':'data.ghsl.chicago-h-anbh-e2018',
            'dirName':'data.ghsl.chicago-h-anbh-e2018@1','origin':'imported',
            'producerNodeId':None,'consumerNodeIds':[],
            'installedAt':'2026-09-28T16:00:00+00:00'})
    built_loader=next(n for n in nodes if n.get('title','').startswith('Built form and parcel sources'))
    if "'ghsl_anbh_2018'" not in built_loader['content']:
        built_loader['content']=built_loader['content'].replace("    'overture_buildings':", 
            "    'ghsl_anbh_2018': curio_dataset_path(\"data.ghsl.chicago-h-anbh-e2018\"),\n    'overture_buildings':")
    # Keep remaining metadata and old agent chats untouched.
    storage.write_spec(USER,PROJECT,spec)
print(json.dumps({'old_revision':rev,'new_revision':storage.spec_revision(USER,PROJECT),
                  'backup':str(backup),'feature_nodes':ids,'edges':len(edges)},indent=2))
