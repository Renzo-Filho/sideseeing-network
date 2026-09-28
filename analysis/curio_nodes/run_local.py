"""Construct one feature from Curio's installed catalog files, outside the UI."""
import pathlib
import sys
import textwrap
import time

BASE=pathlib.Path('/home/renzo/Documents/GitHub/curio')
CATALOG=BASE/'datasets'
HERE=pathlib.Path(__file__).resolve().parent
ids={
 'community_areas':'data.cityofchicago.community-areas-sideseeing',
 'overture_segments':'data.overture.transportation-segments-chicago',
 'overture_connectors':'data.overture.transportation-connectors-chicago',
 'street_centerlines':'data.cityofchicago.street-center-lines',
 'hydrography':'data.cityofchicago.hydrography-sideseeing',
 'overture_buildings':'data.overture.building-layers-chicago',
 'ghsl_anbh_2018':'data.ghsl.chicago-h-anbh-e2018',
 'census_blocks_pop20_jobs':'data.census.chicago-blocks-pop20-lodes-2022',
 'cmap_land_use_2023':'data.cmap.land-use-inventory-chicago',
 'cta_routes':'data.cta.gtfs-chicago-routes',
 'cta_trips':'data.cta.gtfs-chicago-trips',
 'cta_stops':'data.cta.gtfs-chicago-stops',
 'cta_stop_times':'data.cta.gtfs-chicago-stop-times',
 'cta_calendar':'data.cta.gtfs-chicago-calendar',
 'cta_calendar_dates':'data.cta.gtfs-chicago-calendar-dates'}
paths={}
for key,did in ids.items():
    files=list((CATALOG/(did+'@1')/'data').iterdir())
    assert len(files)==1,(did,files)
    paths[key]=str(files[0])
ca={'community_areas':paths['community_areas']}
morph=[ca,{key:paths[key] for key in ['overture_segments','overture_connectors']},
       {'street_centerlines':paths['street_centerlines']}]
built=[ca,{'hydrography':paths['hydrography']},
       {key:paths[key] for key in ['overture_buildings','ghsl_anbh_2018']},{}]
urban=[ca,{'census_blocks_pop20_jobs':paths['census_blocks_pop20_jobs']},
       {'cmap_land_use_2023':paths['cmap_land_use_2023']},
       {key:paths[key] for key in ids if key.startswith('cta_')}]

def module(name):
    src='def run(arg):\n'+textwrap.indent((HERE/(name+'.py')).read_text(),'    ')
    ns={};exec(compile(src,name,'exec'),ns)
    return ns['run']
if __name__=='__main__':
    name=sys.argv[1]
    start=time.time()
    if name=='M6':result=module(name)(module('M1')(morph))
    elif name=='M4':result=module(name)(module('M3')(morph))
    else:
        lane=morph if name.startswith('M') and name!='M7' else built if name in ('M7','B1','B2','B3','BV') else urban
        result=module(name)(lane)
    if isinstance(result,tuple):result=result[0]
    print(name,len(result),'rows',round(time.time()-start,1),'seconds')
    print(result.head(1).to_string(index=False))
    if 'status' in result:print('status_counts',result.status.value_counts().to_dict())
