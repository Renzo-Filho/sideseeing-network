"""Versioned functional extension; resume only when input/code/output hashes match."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys
import traceback
import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from harmonization.functional import active_services, allocate, population_grid, supply
from harmonization.geometry import polygonal

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'analysis'
RAW = A / 'data/Chicago'
CONFIG = A / 'config/chicago_functional_v2.json'
CFG = json.loads(CONFIG.read_text())
RUN = CFG['release_id']
WORK = A / 'work/prepared/Chicago' / RUN
OUT = A / 'results/Chicago' / RUN
BASE = A / 'work/prepared/Chicago/chi_local_2026_09_16_v1'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + '.part')
    part.write_text(json.dumps(value, indent=2, default=str) + '\n')
    part.replace(path)


def table(frame, name):
    frame.to_csv(OUT / 'tables' / (name + '.csv'), index=False)
    frame.to_parquet(OUT / 'tables' / (name + '.parquet'), index=False)


def support():
    districts = gpd.read_parquet(BASE / 'districts.parquet')
    source = RAW / 'tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp'
    # Statewide read establishes WAC key completeness before spatial selection.
    blocks = pyogrio.read_dataframe(source)
    assert blocks.GEOID20.is_unique and blocks.GEOID20.str.fullmatch(r'\d{15}').all()
    assert blocks.POP20.notna().all() and blocks.POP20.ge(0).all()
    wac = pd.read_csv(RAW / 'il_wac_S000_JT00_2022.csv', dtype={'w_geocode': str})
    assert wac.w_geocode.is_unique and wac.w_geocode.str.fullmatch(r'\d{15}').all()
    assert wac.C000.notna().all() and wac.C000.ge(0).all()
    unmatched = wac.loc[~wac.w_geocode.isin(blocks.GEOID20)]
    table(unmatched, 'unmatched_workplace_blocks')
    state_population = int(blocks.POP20.sum())
    matched_jobs = int(wac.loc[wac.w_geocode.isin(blocks.GEOID20), 'C000'].sum())
    bounds = districts.to_crs(blocks.crs).total_bounds
    blocks = blocks.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]].copy().to_crs(CFG['metric_crs'])
    invalid = int((~blocks.is_valid).sum())
    blocks.geometry = blocks.geometry.map(polygonal)
    city = districts.geometry.union_all()
    blocks = blocks.loc[blocks.intersects(city)].copy()
    blocks = blocks.loc[blocks.geometry.area > 0].reset_index(drop=True)
    blocks = blocks.merge(wac[['w_geocode','C000']], left_on='GEOID20', right_on='w_geocode', how='left', validate='one_to_one')
    # WAC is sparse: absent rows represent no published jobs, not missing population joins.
    blocks['wac_row_present'] = blocks.C000.notna()
    blocks['jobs'] = blocks.C000.fillna(0)
    pieces = allocate(blocks, districts)
    covered = pieces.geometry.union_all()
    uncovered = city.difference(covered).area
    # Report boundary-vintage gaps explicitly; never invent population in uncovered slivers.
    gaps = gpd.GeoDataFrame({'reason':['Census/Community Area boundary mismatch']},
                            geometry=[city.difference(covered)], crs=districts.crs)
    gaps.to_parquet(WORK / 'census_coverage_gaps.parquet', index=False)
    assert uncovered < city.area * 1e-3, 'Substantial geography coverage gap' 
    pieces.to_parquet(WORK / 'block_district_pieces.parquet', index=False)
    blocks.to_parquet(WORK / 'blocks.parquet', index=False)
    weights = pieces.groupby('GEOID20').weight.sum().reindex(blocks.GEOID20, fill_value=0).to_numpy()
    residual = blocks[['GEOID20','COUNTYFP20','POP20','jobs','wac_row_present']].copy()
    residual['inside_weight'] = weights
    residual['outside_population'] = residual.POP20 * (1-weights)
    residual['outside_jobs'] = residual.jobs * (1-weights)
    table(residual, 'border_block_accounting')
    totals = pieces.groupby('unit_id')[['population_allocated','jobs_allocated']].sum()
    result = districts[['unit_id','district_name','gross_area_m2','water_area_m2']].merge(totals, on='unit_id', validate='one_to_one')
    result = result.rename(columns={'water_area_m2':'cmap_proxy_water_m2'})
    hydro = pyogrio.read_dataframe(RAW / 'Hydro_20260916.geojson').to_crs(CFG['metric_crs'])
    hydro_invalid = int((~hydro.is_valid).sum())
    water = shapely.union_all(hydro.geometry.map(polygonal)).intersection(city)
    land = districts[['unit_id','geometry']].copy()
    land.geometry = shapely.difference(land.geometry.values, water)
    land.to_parquet(WORK / 'district_hydro_land.parquet', index=False)
    result['hydro_water_m2'] = shapely.area(shapely.intersection(districts.geometry.values, water))
    result['hydro_land_m2'] = land.geometry.area.to_numpy()
    assert np.allclose(result.gross_area_m2, result.hydro_water_m2 + result.hydro_land_m2)
    result['population_density_2020_gross_km2'] = result.population_allocated / (result.gross_area_m2 / 1e6)
    result['jobs_density_2022_gross_km2'] = result.jobs_allocated / (result.gross_area_m2 / 1e6)
    old = pd.read_csv(A / 'results/Chicago/chi_local_2026_09_16_v1/tables/attributes_wide.csv')
    popcols = [c for c in old if 'population' in c]
    dump(OUT/'validation/acs_comparison_columns.json', popcols)
    table(result, 'functional_attributes')
    pop_in, jobs_in = pieces[['population_allocated','jobs_allocated']].sum()
    assert np.isclose(pop_in+residual.outside_population.sum(), blocks.POP20.sum())
    assert np.isclose(jobs_in+residual.outside_jobs.sum(), blocks.jobs.sum())
    audit = {'state_blocks': pyogrio.read_info(source)['features'], 'state_population':state_population,
             'wac_rows':len(wac), 'state_jobs':int(wac.C000.sum()), 'unmatched_job_rows':len(unmatched),
             'unmatched_jobs':int(unmatched.C000.sum()), 'matched_jobs':matched_jobs,
             'city_intersecting_blocks':len(blocks), 'positive_overlap_blocks':pieces.GEOID20.nunique(),
             'counties':sorted(pieces.GEOID20.str[2:5].unique()), 'uncovered_city_m2':uncovered,
             'repaired_blocks':invalid, 'repaired_hydro':hydro_invalid,
             'population_inside':pop_in, 'population_border_outside':residual.outside_population.sum(),
             'jobs_inside':jobs_in, 'jobs_border_outside':residual.outside_jobs.sum(),
             'jobs_matched_outside_city':matched_jobs-jobs_in,
             'hydro_water_km2':result.hydro_water_m2.sum()/1e6,
             'cmap_proxy_water_km2':result.cmap_proxy_water_m2.sum()/1e6,
             'strict_cross_city_accepted':False}
    dump(OUT/'validation/support_checks.json', audit)
    return audit


def transit():
    feed = RAW / 'google_transit'
    def read(name):
        return pd.read_csv(feed / (name+'.txt'), dtype=str, keep_default_na=False)
    calendar, exceptions, trips, routes, stops = [read(n) for n in ['calendar','calendar_dates','trips','routes','stops']]
    assert all(x[k].is_unique for x,k in [(calendar,'service_id'),(trips,'trip_id'),(routes,'route_id'),(stops,'stop_id')])
    assert trips.route_id.isin(routes.route_id).all()
    assert trips.service_id.isin(set(calendar.service_id)|set(exceptions.service_id)).all()
    assert read('agency').agency_timezone.eq('America/Chicago').all()
    # This supplied feed is fully scheduled. Fail explicitly if future input adds templates.
    assert read('frequencies').empty, 'Frequency templates require a separate validated stage implementation'
    bus = trips.loc[trips.route_id.isin(routes.loc[routes.route_type.eq('3'), 'route_id'])].copy()
    assert bus.direction_id.isin(['0','1']).all()
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    con.read_csv(str(feed/'stop_times.txt'), all_varchar=True).create_view('raw_times')
    con.register('all_trips', trips)
    con.register('all_stops', stops)
    badrefs = con.execute('SELECT count(*) FROM raw_times s LEFT JOIN all_trips t USING(trip_id) LEFT JOIN all_stops p USING(stop_id) WHERE t.trip_id IS NULL OR p.stop_id IS NULL').fetchone()[0]
    assert badrefs == 0
    con.register('bus_trips', bus)
    con.execute("""CREATE TABLE bus_times AS SELECT s.*, t.route_id,t.direction_id,t.service_id,
        try_cast(split_part(departure_time,':',1) AS BIGINT)*3600+
        try_cast(split_part(departure_time,':',2) AS BIGINT)*60+
        try_cast(split_part(departure_time,':',3) AS BIGINT) AS sec
        FROM raw_times s JOIN bus_trips t USING(trip_id)""")
    invalid = con.execute("SELECT count(*) FROM bus_times WHERE NOT regexp_full_match(departure_time, '[0-9]+:[0-5][0-9]:[0-5][0-9]') OR sec IS NULL OR try_cast(stop_sequence AS BIGINT) IS NULL").fetchone()[0]
    duplicate = con.execute('SELECT count(*) FROM (SELECT trip_id,stop_sequence FROM bus_times GROUP BY ALL HAVING count(*)>1)').fetchone()[0]
    reversed_times = con.execute('SELECT count(*) FROM (SELECT sec,lag(sec) OVER(PARTITION BY trip_id ORDER BY cast(stop_sequence AS BIGINT)) AS prev FROM bus_times) WHERE sec<prev').fetchone()[0]
    absent = con.execute('SELECT count(*) FROM bus_trips WHERE trip_id NOT IN (SELECT trip_id FROM bus_times)').fetchone()[0]
    assert invalid == duplicate == reversed_times == absent == 0, (invalid,duplicate,reversed_times,absent)
    maxsec = con.execute('SELECT max(sec) FROM bus_times').fetchone()[0]
    events = []
    for win in CFG['windows']:
        date = dt.date.fromisoformat(win['date'])
        for back in range(int(maxsec//86400)+1):
            active = active_services(calendar, exceptions, date-dt.timedelta(days=back))
            services = pd.DataFrame({'service_id':sorted(active)})
            con.register('active', services)
            q = con.execute('SELECT stop_id,route_id,direction_id,count(*) AS departures FROM bus_times JOIN active USING(service_id) WHERE sec>=? AND sec<? AND coalesce(pickup_type,\'\')<>\'1\' GROUP BY ALL', [win['start']+back*86400,win['end']+back*86400]).df()
            q['window'] = win['label']
            events.append(q)
    service = pd.concat(events).groupby(['window','stop_id','route_id','direction_id'],as_index=False).departures.sum()
    assert set(service.window)=={w['label'] for w in CFG['windows']}
    service.to_parquet(WORK/'stop_route_service.parquet', index=False)
    lon, lat = pd.to_numeric(stops.stop_lon), pd.to_numeric(stops.stop_lat)
    assert lon.between(-180,180).all() and lat.between(-90,90).all()
    stopgeo = gpd.GeoDataFrame(stops, geometry=gpd.points_from_xy(lon,lat),crs=4326).to_crs(CFG['metric_crs'])
    # Preserve all feed stops, including those outside city boundaries.
    stopgeo.to_parquet(WORK/'stops.parquet',index=False)
    dump(OUT/'validation/transit_checks.json', {'bus_routes':int(routes.route_type.eq('3').sum()),
         'bus_trips':len(bus),'all_stops':len(stops),'stop_time_rows':con.execute('SELECT count(*) FROM raw_times').fetchone()[0],
         'bus_stop_time_rows':con.execute('SELECT count(*) FROM bus_times').fetchone()[0],
         'max_departure_seconds':int(maxsec),'invalid_references':badrefs,'invalid_times':invalid,
         'duplicate_sequences':duplicate,'nonmonotonic_times':reversed_times,'trips_without_times':absent,
         'calendar_range':[calendar.start_date.min(),calendar.end_date.max()],
         'exceptions_applied':True,'frequency_rows':0,'windows':CFG['windows'],
         'scheduled_stop_calls':service.groupby('window').departures.sum().to_dict(),
         'pickup_policy':'pickup_type=1 excluded; conditional pickup types retained if present'})
    con.close()


def access():
    pieces = gpd.read_parquet(WORK/'block_district_pieces.parquet')
    stops = gpd.read_parquet(WORK/'stops.parquet')
    service = pd.read_parquet(WORK/'stop_route_service.parquet')
    result = []
    point_dir = WORK/'population_points'
    point_dir.mkdir(exist_ok=True)
    for unit, part in pieces.groupby('unit_id',sort=True):
        print('U4',unit,flush=True)
        points = population_grid(part, CFG['grid_m'])
        points.to_parquet(point_dir/(unit.replace(':','_')+'.parquet'),index=False)
        pop = points.population_weight.sum()
        for window, svc in service.groupby('window'):
            numerators = {r:0. for r in CFG['radii_m']}
            reached = {r:0. for r in CFG['radii_m']}
            for start in range(0,len(points),500):
                p = points.iloc[start:start+500]
                previous = None
                for radius in CFG['radii_m']:
                    values = supply(p,stops,svc,radius)
                    assert np.isfinite(values).all() and (values>=0).all()
                    if previous is not None:
                        assert (values>=previous).all()
                    previous=values
                    numerators[radius] += float(values @ p.population_weight.to_numpy())
                    reached[radius] += float(p.loc[values>0,'population_weight'].sum())
            for radius in CFG['radii_m']:
                result.append({'unit_id':unit,'window':window,'radius_m':radius,
                    'population_weight':pop,'weighted_departures':numerators[radius],
                    'expected_departures_per_resident':numerators[radius]/pop,
                    'population_reached':reached[radius],'reach_fraction':reached[radius]/pop,
                    'support_points':len(points),'strict_cross_city_accepted':False})
    q=pd.DataFrame(result)
    assert len(q)==77*6
    table(q,'bus_service_access')
    dump(OUT/'validation/access_checks.json',{'rows':len(q),'units':q.unit_id.nunique(),
        'pointwise_radius_monotonicity':True,'population_grid_conservation':True,
        'population_support':'gross block area, 250m origin-zero grid intersections, representative points'})


def main():
    for d in [WORK,OUT/'tables',OUT/'validation']:
        d.mkdir(parents=True,exist_ok=True)
    sources = [RAW/'Hydro_20260916.geojson', RAW/'il_wac_S000_JT00_2022.csv',BASE/'districts.parquet']
    sources += sorted((RAW/'tl_2022_17_tabblock20').glob('*')) + sorted((RAW/'google_transit').glob('*'))
    codes = [Path(__file__),CONFIG,A/'scripts/harmonization/functional.py',A/'scripts/harmonization/geometry.py']
    manifest = [{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources+codes]
    signature = hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    path=WORK/'progress.json'
    progress=json.loads(path.read_text()) if path.exists() else {'signature':signature,'stages':{}}
    if progress['signature'] != signature:
        raise RuntimeError('Input/code signature changed. Create a new release or explicitly retire the unfinished run.')
    dump(OUT/'validation/source_code_manifest.json',manifest)
    stages={'support':support,'transit':transit,'access':access}
    stage_files = {
        'support': [WORK/n for n in ['block_district_pieces.parquet','blocks.parquet','census_coverage_gaps.parquet','district_hydro_land.parquet']] +
                   [OUT/'tables'/(n+ext) for n in ['unmatched_workplace_blocks','border_block_accounting','functional_attributes'] for ext in ['.csv','.parquet']] +
                   [OUT/'validation'/n for n in ['acs_comparison_columns.json','support_checks.json']],
        'transit': [WORK/'stop_route_service.parquet',WORK/'stops.parquet',OUT/'validation/transit_checks.json'],
        'access': [OUT/'tables'/('bus_service_access'+ext) for ext in ['.csv','.parquet']] + [OUT/'validation/access_checks.json']
    }
    selected=sys.argv[1:] or list(stages)
    for name in selected:
        if name not in stages:
            raise ValueError(name)
        checkpoint=progress['stages'].get(name,{})
        if checkpoint.get('status')=='complete' and all((ROOT/p).exists() and sha(ROOT/p)==h for p,h in checkpoint['outputs'].items()):
            print('resume verified',name,flush=True)
            continue
        progress['stages'][name]={'status':'running'}
        dump(path,progress)
        try:
            stages[name]()
            after=stage_files[name] + (list((WORK/'population_points').glob('*.parquet')) if name=='access' else [])
            outputs={str(p.relative_to(ROOT)):sha(p) for p in after}
            progress['stages'][name]={'status':'complete','outputs':outputs}
        except Exception as exc:
            progress['stages'][name]={'status':'failed','error':str(exc)}
            dump(path,progress)
            raise
        dump(path,progress)
        dump(OUT/'validation/progress.json',progress)
        print('complete',name,flush=True)

if __name__=='__main__':
    main()
