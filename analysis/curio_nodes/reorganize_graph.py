"""Rebuild the Chicago Curio canvas as three source/feature/result lanes.

Run with --dry-run first. The write path takes Curio's project lock and saves the
exact prior spec beside this script. Existing feature IDs and agent chats survive.
"""
import argparse
import copy
import json
import pathlib
import uuid
from collections import Counter
from graphlib import TopologicalSorter
from utk_curio.backend.app.projects import storage

PROJECT='b4a2907d-bf08-469f-a4d5-761f59c9f531'
USER='3'
HERE=pathlib.Path(__file__).resolve().parent

# Within each lane, the merge input order is the feature code's arg contract.
SOURCE_GROUPS={
 'morph':[
  ('Morphology · community areas',-2250,-1950,{'community_areas':'data.cityofchicago.community-areas-sideseeing'}),
  ('Morphology · Overture roads',-2250,-1500,{'overture_segments':'data.overture.transportation-segments-chicago','overture_connectors':'data.overture.transportation-connectors-chicago'}),
  ('Morphology · municipal streets',-2250,-1050,{'street_centerlines':'data.cityofchicago.street-center-lines'}),
 ],
 'built':[
  ('Built form · community areas',-2250,0,{'community_areas':'data.cityofchicago.community-areas-sideseeing'}),
  ('Built form · hydrography',-2250,450,{'hydrography':'data.cityofchicago.hydrography-sideseeing'}),
  ('Built form · footprints and height',-2250,900,{
   'city_building_footprints':'data.cityofchicago.building-footprints',
   'overture_buildings':'data.overture.building-layers-chicago',
   'ghsl_anbh_2018':'data.ghsl.chicago-h-anbh-e2018'}),
  ('Built form · Cook parcel records',-2250,1350,{
   'cook_buildings_2022':'data.sideseeing.cook-buildings-2022',
   'cook_parcels_2024':'data.sideseeing.cook-parcels-2024',
   'cook_universe_2024':'data.sideseeing.cook-universe-2024',
   'cook_residential_2024':'data.sideseeing.cook-residential-2024',
   'cook_condo_2024':'data.sideseeing.cook-condo-2024',
   'cook_commercial_2024':'data.sideseeing.cook-commercial-2024',
   'cook_commercial_details_2024':'data.sideseeing.cook-commercial-workbook-details-2024'}),
 ],
 'urban':[
  ('Urban function · community areas',-2250,2700,{'community_areas':'data.cityofchicago.community-areas-sideseeing'}),
  ('Urban function · Census support',-2250,3150,{
   'census_blocks_pop20_jobs':'data.census.chicago-blocks-pop20-lodes-2022',
   'illinois_lodes_wac_2022':'data.census.illinois-lodes-wac-2022',
   'acs_community_areas_diagnostic':'data.sideseeing.chicago-acs-community-areas'}),
  ('Urban function · CMAP land use',-2250,3600,{'cmap_land_use_2023':'data.cmap.land-use-inventory-chicago'}),
  ('Urban function · CTA GTFS',-2250,4050,{
   'cta_agency':'data.cta.gtfs-chicago-agency',
   'cta_routes':'data.cta.gtfs-chicago-routes',
   'cta_trips':'data.cta.gtfs-chicago-trips',
   'cta_stops':'data.cta.gtfs-chicago-stops',
   'cta_stop_times':'data.cta.gtfs-chicago-stop-times',
   'cta_calendar':'data.cta.gtfs-chicago-calendar',
   'cta_calendar_dates':'data.cta.gtfs-chicago-calendar-dates'}),
 ],
}
FEATURE_GROUPS={'morph':['M1','M2','M3','M4','M6'],
                'built':['M7','B1','B2','B3','BV'],
                'urban':['U1','U2','U3','U4']}
FEATURE_POSITIONS={
 'M1':(0,-2200),'M2':(0,-1700),'M3':(0,-1200),'M4':(1100,-1200),'M6':(1100,-2200),
 'M7':(0,0),'B1':(0,500),'B2':(0,1000),'B3':(0,1500),'BV':(0,2000),
 'U1':(0,2700),'U2':(0,3200),'U3':(0,3700),'U4':(0,4200)}
SOURCE_MERGE_POS={'morph':(-950,-1500),'built':(-950,650),'urban':(-950,3350)}
RESULT_MERGE_POS={'morph':(2200,-1500),'built':(2200,1000),'urban':(2200,3450)}
OLD_SOURCE_IDS={
 'Morphology · community areas':'e1db5491-2b61-4f9a-a5a2-7721f6fa19e7',
 'Morphology · Overture roads':'188f31a1-79f4-4520-8725-b547d01f109b',
 'Built form · footprints and height':'31f94f60-1042-4bfc-ad7e-010575a3a973',
 'Urban function · CTA GTFS':'1bc2b71f-2dc5-4274-90a5-4ae647d35109'}
MORPH_SOURCE_MERGE='b5167303-6bfe-4386-a2c0-6cc4f06acbb8'
FINAL='33369274-e6e8-4701-8097-899096858126'

def stable_id(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,PROJECT+'/graph-v2/'+label))

def loader_code(name, datasets):
    lines=['# '+name+'. Paths only: each feature opens the data it needs.','return {']
    lines.extend("    "+repr(key)+': curio_dataset_path('+json.dumps(dataset)+'),' for key,dataset in datasets.items())
    lines.append('}')
    return '\n'.join(lines)+'\n'

def old_code_from_new(feature, code):
    reverse={
      'M3':("arg[2]['street_centerlines']","arg[1]['street_centerlines']"),
      'B1':("arg[1]['hydrography']","arg[0]['hydrography']"),
      'BV':("arg[1]['hydrography']","arg[0]['hydrography']"),
      'U1':("arg[2]['cmap_land_use_2023']","arg[3]['cmap_land_use_2023']"),
      'U2':("arg[1]['census_blocks_pop20_jobs']","arg[0]['census_blocks_pop20_jobs']"),
      'U3':("arg[1]['census_blocks_pop20_jobs']","arg[0]['census_blocks_pop20_jobs']"),
      'U4':("arg[1]['census_blocks_pop20_jobs']","arg[0]['census_blocks_pop20_jobs']")}
    if feature in reverse:
        newer,older=reverse[feature]
        assert code.count(newer)==1
        code=code.replace(newer,older)
    if feature=='M1':
        code=code.replace('arg is the morphology lane: area, Overture roads, municipal streets.',
                          'arg is four path dictionaries.')
    return code

def build(spec):
    graph=spec['dataflow']; nodes=graph['nodes']; byid={n['id']:n for n in nodes}
    if len(nodes)!=24:raise RuntimeError('Unexpected node count; inspect concurrent edits')
    if MORPH_SOURCE_MERGE not in byid or FINAL not in byid:raise RuntimeError('Expected merges missing')
    feature_nodes={n['title'].split()[-1]:n for n in nodes if n.get('title','').startswith('Feature ')}
    if set(feature_nodes)!={x for v in FEATURE_GROUPS.values() for x in v}:
        raise RuntimeError('Feature set changed; inspect before rewriting')
    for feature,node in feature_nodes.items():
        new=(HERE/(feature+'.py')).read_text()
        if node['content']!=old_code_from_new(feature,new):
            raise RuntimeError('Feature '+feature+' changed since the graph review; preserve user edit')
    installed={d['datasetId'] for d in graph['datasets'] if d.get('datasetId')}
    for group in SOURCE_GROUPS.values():
        for _,_,_,data in group:
            missing=set(data.values())-installed
            if missing:raise RuntimeError('Catalog inputs not attached: '+str(missing))
    loader_prototype=copy.deepcopy(byid[OLD_SOURCE_IDS['Morphology · community areas']])
    merge_prototype=copy.deepcopy(byid[MORPH_SOURCE_MERGE])
    source_ids={}; source_merge_ids={}; result_merge_ids={}
    for family,entries in SOURCE_GROUPS.items():
        for name,x,y,data in entries:
            node=byid[OLD_SOURCE_IDS[name]] if name in OLD_SOURCE_IDS else copy.deepcopy(loader_prototype)
            if name not in OLD_SOURCE_IDS:
                node['id']=stable_id('source:'+name);nodes.append(node)
            source_ids[name]=node['id']
            node['title']=name;node['x']=x;node['y']=y
            node['width']=800;node['height']=420 if len(data)>4 else 300
            node['content']=loader_code(name,data)
            node['goal']='Provide catalog paths for the '+family+' feature lane.'
        node=byid[MORPH_SOURCE_MERGE] if family=='morph' else copy.deepcopy(merge_prototype)
        if family!='morph':node['id']=stable_id('source-merge:'+family);nodes.append(node)
        node['title']=family.title()+' source bundle'
        node['x'],node['y']=SOURCE_MERGE_POS[family]
        node['goal']='Merge only '+family+' source paths in the input order used by this lane.'
        source_merge_ids[family]=node['id']
        out=copy.deepcopy(merge_prototype)
        out['id']=stable_id('result-merge:'+family)
        out['title']=family.title()+' feature outputs'
        out['x'],out['y']=RESULT_MERGE_POS[family]
        out['goal']='Collect '+family+' feature node outputs; no model evaluation here.'
        nodes.append(out);result_merge_ids[family]=out['id']
    for feature,node in feature_nodes.items():
        node['content']=(HERE/(feature+'.py')).read_text()
        node['x'],node['y']=FEATURE_POSITIONS[feature]
        node['width']=850;node['height']=425
    final=byid[FINAL]
    final['title']='Collect three feature families'
    final['x']=3150;final['y']=1000
    final['goal']='Collect morphology, built form, and urban function outputs; model fitting is later.'
    # Keep the old model/visualization placeholders visible as a future section.
    future={
      '6492e1e6-1da4-497b-a5cb-f21f1236f1f4':('Future model assembly (unconfigured)',3150,5150),
      '2ae62559-ca57-4a48-a17c-6bf3d179f81c':('Future map (unconfigured)',4050,4900),
      '0deba6f0-28e2-4e81-a086-b8754b675352':('Future chart (unconfigured)',4050,5500),
      'ca25d625-d3c8-470d-8f7d-2e81066b9590':('Future output pool (unconfigured)',5000,5200)}
    for node_id,(title,x,y) in future.items():
        if node_id in byid:
            n=byid[node_id];n['title']=title;n['x']=x;n['y']=y
    edges=[]
    def connect(source,target,handle):
        edges.append({'id':stable_id('edge:'+source+':'+target+':'+handle),
                      'source':source,'target':target,'sourceHandle':'out','targetHandle':handle})
    for family,entries in SOURCE_GROUPS.items():
        for index,(name,_,_,_) in enumerate(entries):
            connect(source_ids[name],source_merge_ids[family],f'in_{index}')
    for family,features in FEATURE_GROUPS.items():
        for feature in features:
            if feature in ('M4','M6'):continue
            connect(source_merge_ids[family],feature_nodes[feature]['id'],'in')
        for index,feature in enumerate(features):
            connect(feature_nodes[feature]['id'],result_merge_ids[family],f'in_{index}')
    connect(feature_nodes['M1']['id'],feature_nodes['M6']['id'],'in')
    connect(feature_nodes['M3']['id'],feature_nodes['M4']['id'],'in')
    for index,family in enumerate(['morph','built','urban']):
        connect(result_merge_ids[family],FINAL,f'in_{index}')
    graph['edges']=edges
    deps={n['id']:set() for n in nodes}
    for edge in edges:deps[edge['target']].add(edge['source'])
    tuple(TopologicalSorter(deps).static_order())
    out_degree=Counter(e['source'] for e in edges)
    in_degree=Counter(e['target'] for e in edges)
    return {'nodes':len(nodes),'edges':len(edges),'max_out':max(out_degree.values()),
            'max_in':max(in_degree.values()),'source_loaders':sum(n['type']=='curio.builtin/data-loading' for n in nodes),
            'source_merges':source_merge_ids,'result_merges':result_merge_ids,
            'final_inputs':in_degree[FINAL]}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
    if args.dry_run:
        rev=storage.spec_revision(USER,PROJECT)
        spec=storage.read_spec(USER,PROJECT)
        result=build(copy.deepcopy(spec))
        print(json.dumps({'revision':rev,'dry_run':True,**result},indent=2))
        return
    with storage.spec_write_lock(USER,PROJECT):
        rev=storage.spec_revision(USER,PROJECT)
        spec=storage.read_spec(USER,PROJECT)
        backup=HERE/f'backup_spec_rev_{rev}.json'
        if backup.exists():raise RuntimeError('Backup path already exists')
        result=build(spec)
        backup.write_text((storage.project_dir(USER,PROJECT)/'spec.trill.json').read_text())
        storage.write_spec(USER,PROJECT,spec)
    print(json.dumps({'old_revision':rev,'new_revision':storage.spec_revision(USER,PROJECT),
                      'backup':str(backup),**result},indent=2))
if __name__=='__main__':main()
