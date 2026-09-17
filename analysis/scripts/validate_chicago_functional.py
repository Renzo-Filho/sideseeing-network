"""Independent release audit and publication of the Chicago functional extension."""
from pathlib import Path
import hashlib
import json
import sys
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

A=Path(__file__).resolve().parents[1]
ROOT=A.parent
RUN='chi_functional_2026_09_16_v2'
OUT=A/'results/Chicago'/RUN
WORK=A/'work/prepared/Chicago'/RUN
RAW=A/'data/Chicago'
checks=[]

def check(name,ok,detail=None):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    wide=pd.read_parquet(OUT/'tables/functional_attributes.parquet')
    access=pd.read_parquet(OUT/'tables/bus_service_access.parquet')
    blocks=gpd.read_parquet(WORK/'blocks.parquet')
    pieces=gpd.read_parquet(WORK/'block_district_pieces.parquet')
    districts=gpd.read_parquet(A/'work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet')
    residual=pd.read_parquet(OUT/'tables/border_block_accounting.parquet')
    expected={f'CHI:{i:02}' for i in range(1,78)}
    check('77 qualified unique units',wide.unit_id.is_unique and set(wide.unit_id)==expected)
    check('462 unique transit scenarios',len(access)==462 and not access.duplicated(['unit_id','window','radius_m']).any())
    check('all numeric outputs finite',np.isfinite(wide.select_dtypes('number')).all().all() and np.isfinite(access.select_dtypes('number')).all().all())
    check('population ratio',np.allclose(wide.population_density_2020_gross_km2,wide.population_allocated/wide.gross_area_m2*1e6))
    check('jobs ratio',np.allclose(wide.jobs_density_2022_gross_km2,wide.jobs_allocated/wide.gross_area_m2*1e6))
    check('gross land water',np.allclose(wide.gross_area_m2,wide.hydro_land_m2+wide.hydro_water_m2))
    check('transit weighted ratio',np.allclose(access.expected_departures_per_resident,access.weighted_departures/access.population_weight))
    check('reach ratio and range',np.allclose(access.reach_fraction,access.population_reached/access.population_weight) and access.reach_fraction.between(-1e-12,1+1e-12).all())
    check('population border conservation',np.isclose(wide.population_allocated.sum()+residual.outside_population.sum(),blocks.POP20.sum(),rtol=1e-10))
    check('jobs border conservation',np.isclose(wide.jobs_allocated.sum()+residual.outside_jobs.sum(),blocks.jobs.sum(),rtol=1e-10))
    check('Cook and DuPage positive support',set(pieces.GEOID20.str[2:5])=={'031','043'})
    city=districts.geometry.union_all()
    # Direct whole-city clip is independent of pairwise district allocation.
    fractions=blocks.geometry.intersection(city).area/blocks.geometry.area
    check('independent whole-city population',np.isclose((fractions*blocks.POP20).sum(),wide.population_allocated.sum(),rtol=1e-9))
    check('independent whole-city jobs',np.isclose((fractions*blocks.jobs).sum(),wide.jobs_allocated.sum(),rtol=1e-9))
    for name in ['functional_attributes','bus_service_access','border_block_accounting']:
        a=pd.read_csv(OUT/'tables'/f'{name}.csv',dtype={'GEOID20':str,'COUNTYFP20':str});b=pd.read_parquet(OUT/'tables'/f'{name}.parquet')
        check(name+' CSV/Parquet agreement',len(a)==len(b) and np.allclose(a.select_dtypes('number'),b.select_dtypes('number'),equal_nan=True))
    for window,part in access.groupby('window'):
        p=part.pivot(index='unit_id',columns='radius_m',values='expected_departures_per_resident')
        check(window+' radius monotonicity',(p[800]>=p[400]).all())
    stops=gpd.read_parquet(WORK/'stops.parquet')
    service=pd.read_parquet(WORK/'stop_route_service.parquet')
    service=service.loc[service.window.eq('weekday_am')]
    for unit in ['CHI:24','CHI:28','CHI:30','CHI:32','CHI:76']:
        points=gpd.read_parquet(WORK/'population_points'/(unit.replace(':','_')+'.parquet'))
        check(unit+' grid mass',np.isclose(points.population_weight.sum(),wide.set_index('unit_id').loc[unit,'population_allocated'],rtol=1e-10))
        geom=districts.set_index('unit_id').loc[unit].geometry
        check(unit+' grid points inside',points.geometry.map(geom.covers).all())
        # Reconstruct every point using Euclidean coordinate trees, no spatial-index join.
        from scipy.spatial import cKDTree
        tree=cKDTree(np.column_stack([stops.geometry.x,stops.geometry.y]))
        coords=np.column_stack([points.geometry.x,points.geometry.y])
        for radius in [400,800]:
            neighborhoods=tree.query_ball_point(coords,radius)
            lookup={k:list(zip(g.route_id,g.direction_id,g.departures)) for k,g in service.groupby('stop_id')}
            total=0.
            for weight,ids in zip(points.population_weight,neighborhoods):
                maxima={}
                for stopid in stops.stop_id.iloc[ids]:
                    for route,direction,count in lookup.get(stopid,[]):
                        key=(route,direction);maxima[key]=max(maxima.get(key,0),count)
                total+=weight*sum(maxima.values())
            stored=access.loc[access.unit_id.eq(unit)&access.window.eq('weekday_am')&access.radius_m.eq(radius)].weighted_departures.iloc[0]
            check(f'{unit} {radius}m independent service',np.isclose(total,stored,rtol=1e-10))
    manifest=json.loads((OUT/'validation/source_code_manifest.json').read_text())
    for row in manifest:check('source/code hash '+row['path'],sha(ROOT/row['path'])==row['sha256'])
    progress=json.loads((WORK/'progress.json').read_text())
    for stage,info in progress['stages'].items():
        check(stage+' completed with outputs',info['status']=='complete' and bool(info.get('outputs')))
        for path,h in info.get('outputs',{}).items():check('checkpoint '+path,sha(ROOT/path)==h)
    # Publish an explicit feature contract, retaining all original releases.
    rows=[]
    for r in wide.itertuples():
        for family,name,num,den,period,status in [
            ('U3','population_density_2020_gross_km2',r.population_allocated,r.gross_area_m2/1e6,'Census 2020 / TIGER 2022 block geography','constructed_gross_area_allocation'),
            ('U2','jobs_density_2022_gross_km2',r.jobs_allocated,r.gross_area_m2/1e6,'LODES WAC S000 JT00 2022','extended_business_sensitivity_pending')]:
            rows.append(dict(unit_id=r.unit_id,family=family,feature=name,value=num/den,numerator=num,denominator=den,units='residents/km2' if family=='U3' else 'jobs/km2',period=period,status=status,strict_cross_city_accepted=False))
    for r in access.itertuples():
        rows.append(dict(unit_id=r.unit_id,family='U4',feature=f'bus_service_access_{r.window}_{r.radius_m}m',value=r.expected_departures_per_resident,numerator=r.weighted_departures,denominator=r.population_weight,units='scheduled departures per 2h per resident',period='September 16/19/20 2026; Census 2020 support',status='constructed_CTA_bus_only_paired_acceptance_pending',strict_cross_city_accepted=False))
    long=pd.DataFrame(rows)
    long.to_csv(OUT/'tables/attributes_long.csv',index=False);long.to_parquet(OUT/'tables/attributes_long.parquet',index=False)
    matrix=long.pivot(index='unit_id',columns='feature',values='value').reset_index()
    matrix.to_csv(OUT/'tables/attributes_wide.csv',index=False);matrix.to_parquet(OUT/'tables/attributes_wide.parquet',index=False)
    dictionary=long[['family','feature','units','period','status','strict_cross_city_accepted']].drop_duplicates()
    dictionary.to_csv(OUT/'tables/attribute_dictionary.csv',index=False)
    old=pd.read_csv(A/'results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv')
    cmp=wide[['unit_id','population_allocated']].merge(old[['unit_id','population_density_acs_label2023','gross_area_m2']],on='unit_id',validate='one_to_one')
    cmp['supplied_acs_population']=cmp.population_density_acs_label2023*cmp.gross_area_m2/1e6
    cmp['census_minus_supplied_acs']=cmp.population_allocated-cmp.supplied_acs_population
    cmp['interpretation']='different period and support; ACS provenance unresolved; not equality test'
    cmp.to_csv(OUT/'tables/population_period_diagnostic.csv',index=False)
    spatial=districts[['unit_id','geometry']].merge(wide,on='unit_id').merge(matrix,on='unit_id',suffixes=('','_feature'))
    (OUT/'spatial').mkdir(exist_ok=True)
    spatial.to_file(OUT/'spatial/functional_attributes.gpkg',layer='community_attributes',driver='GPKG')
    reopened=gpd.read_file(OUT/'spatial/functional_attributes.gpkg')
    check('spatial roundtrip',len(reopened)==77 and reopened.crs.to_epsg()==26916 and np.allclose(reopened.jobs_allocated,wide.jobs_allocated))
    audit={'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks,'strict_cross_city_accepted':False}
    (OUT/'validation/independent_checks.json').write_text(json.dumps(audit,indent=2)+'\n')
    files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='release_checksums.json'}
    (OUT/'validation/release_checksums.json').write_text(json.dumps(files,indent=2)+'\n')
    print(json.dumps({'passed':audit['passed'],'failed':audit['failed']}))
    if audit['failed']:
        print([c for c in checks if not c['passed']]);sys.exit(1)

if __name__=='__main__':main()
