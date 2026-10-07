"""Source audit for the simplified composite index (docs/SIMPLE_INDEX.md).

Recomputes, from local data only, every source fact the index discussion relies on:
district areas, Overture Places, IBGE CNEFE 2022, GTFS stops, Overture building heights
and Overture road segments. Memory-safe: the 7.3 M-row SP building file is streamed
through its R-tree in chunks (a full read crashed the machine on 2026-10-01).
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'analysis/data'
OUT = ROOT / 'analysis/results/SP_CHI/simple_index_source_audit_2026_10_01'
T = OUT / 'tables'
T.mkdir(parents=True, exist_ok=True)
CITY = {
    'Chicago': dict(districts='analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet', crs=26916,
                    gtfs='Chicago/google_transit'),
    'SP': dict(districts='analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet', crs=31983,
               gtfs='SP/Socioeconomico/f-6gy-sptrans-latest'),
}
M1_CLASSES = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'living_street', 'pedestrian',
              'unclassified', 'unknown']
CNEFE = D / 'SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv'
SP_BUILDINGS = D / 'SP/Edificacoes/sao_paulo_building_morphology.gpkg'
summary, inputs = {}, {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(2**22), b''):
            h.update(chunk)
    inputs[str(Path(p).relative_to(ROOT))] = h.hexdigest()


def districts(city):
    g = gpd.read_parquet(ROOT / CITY[city]['districts'])
    if 'unit_id' not in g:
        g['unit_id'] = 'SP:' + g.district_id
    sha(ROOT / CITY[city]['districts'])
    return g[['unit_id', 'gross_area_m2', 'land_area_m2', 'geometry']]


def save(df, name):
    df.to_csv(T / name, index=False)


def datasets(sources, prop=None):
    """Datasets credited for a property (falls back to whole-feature credit, property '')."""
    if sources is None:
        return ''
    rows = list(sources)
    hit = [s['dataset'] for s in rows if prop and s.get('property') == prop]
    return '+'.join(sorted(set(hit or [s['dataset'] for s in rows if s.get('property') in ('', None)])))


def unit_of(points, d):
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=points, crs=d.crs), d[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(points.index)


def areas():
    rows = []
    for city in CITY:
        d = districts(city)
        for col in ('gross_area_m2', 'land_area_m2'):
            a = d[col] / 1e6
            rows.append(dict(city=city, measure=col.replace('_m2', '_km2'), units=len(d), min=a.min(), median=a.median(), max=a.max()))
    save(pd.DataFrame(rows).round(3), 'unit_areas.csv')


def places():
    status, src, tax, conf, by_unit, src_credit = [], [], [], [], [], []
    for city in CITY:
        d = districts(city)
        f = D / city / 'overture_2026_08_19/place/part_0000.parquet'
        sha(f)
        g = gpd.read_parquet(f, columns=['id', 'geometry', 'confidence', 'sources', 'operating_status', 'taxonomy']).to_crs(d.crs)
        g['unit_id'] = unit_of(g.geometry, d)
        g = g[g.unit_id.notna()].copy()
        g['source'] = g.sources.map(lambda s: '+'.join(sorted({x['dataset'] for x in s})) if s is not None else '')
        g['top'] = g.taxonomy.map(lambda t: t['hierarchy'][0] if t is not None and t['hierarchy'] is not None and len(t['hierarchy']) else 'NONE')
        g['operating_status'] = g.operating_status.fillna('NULL')
        summary[f'places_in_city_{city}'] = len(g)
        summary[f'places_buffered_extract_{city}'] = json.loads((f.parent / 'manifest.json').read_text())['rows']
        for name, col, out in (('source', 'source', src), ('operating_status', 'operating_status', status), ('top', 'top', tax)):
            v = g[col].value_counts().rename_axis('value').reset_index(name='places')
            v.insert(0, 'city', city)
            v['share'] = (v.places / len(g)).round(4)
            out.append(v)
        credit = g.source.str.split('+').explode().value_counts().rename_axis('dataset').reset_index(name='places_credited')
        credit.insert(0, 'city', city)
        credit['share'] = (credit.places_credited / len(g)).round(4)
        src_credit.append(credit)
        q = g.confidence.quantile([.1, .25, .5, .75, .9])
        conf.append(pd.DataFrame(dict(city=city, quantile=q.index, confidence=q.values.round(3))))
        u = g.pivot_table(index='unit_id', columns='top', values='id', aggfunc='count', fill_value=0)
        by_unit.append(u.reset_index())
    save(pd.concat(src), 'places_sources.csv')
    save(pd.concat(src_credit), 'places_dataset_credit.csv')
    save(pd.concat(status), 'places_operating_status.csv')
    save(pd.concat(tax), 'places_taxonomy_top.csv')
    save(pd.concat(conf), 'places_confidence_quantiles.csv')
    save(pd.concat(by_unit).fillna(0), 'places_by_unit_taxonomy_top.csv')


def cnefe():
    sha(CNEFE)
    c = pd.read_csv(CNEFE, sep=';', usecols=['COD_UNICO_ENDERECO', 'COD_DISTRITO', 'COD_ESPECIE', 'DSC_ESTABELECIMENTO',
                                             'NV_GEO_COORD', 'LATITUDE', 'LONGITUDE', 'COD_INDICADOR_ESTAB_ENDERECO'],
                    dtype={'DSC_ESTABELECIMENTO': str})
    summary.update(cnefe_rows=len(c), cnefe_unique_address_ids=int(c.COD_UNICO_ENDERECO.nunique()),
                   cnefe_rows_sharing_address_id=int(c.COD_UNICO_ENDERECO.duplicated(keep=False).sum()),
                   cnefe_missing_coordinates=int(c.LATITUDE.isna().sum()), cnefe_distinct_cod_distrito=int(c.COD_DISTRITO.nunique()))
    s = c.groupby('COD_ESPECIE').agg(records=('COD_ESPECIE', 'size'), with_name=('DSC_ESTABELECIMENTO', 'count')).reset_index()
    save(s, 'cnefe_species.csv')
    # IBGE Notas metodologicas n. 04: an establishment address may be recorded once with a 'multiple' indicator
    # (2 = up to 10, 3 = more than 10, 4 = unknown number), so establishment records are not establishment counts.
    est = c[c.COD_ESPECIE.isin([3, 4, 5, 6, 8])]
    save(pd.crosstab(est.COD_INDICADOR_ESTAB_ENDERECO, est.COD_ESPECIE).reset_index(), 'cnefe_establishment_indicator.csv')
    save(c.NV_GEO_COORD.value_counts().sort_index().rename_axis('nv_geo_coord').reset_index(name='records'), 'cnefe_geocode_level.csv')
    # Crosswalk IBGE COD_DISTRITO -> municipal district, from points at geocode level 1 (original census coordinate).
    d = districts('SP')
    p = c[c.NV_GEO_COORD == 1]
    pts = gpd.GeoSeries(gpd.points_from_xy(p.LONGITUDE, p.LATITUDE), index=p.index, crs=4674).to_crs(d.crs)
    x = pd.DataFrame(dict(cod=p.COD_DISTRITO, unit_id=unit_of(pts, d)))
    ct = x.groupby(['cod', 'unit_id']).size().rename('records').reset_index()
    top = ct.sort_values('records').groupby('cod').tail(1).rename(columns={'unit_id': 'modal_unit_id', 'records': 'modal_records'})
    top = top.merge(x.groupby('cod').size().rename('level1_records').reset_index(), on='cod')
    top['modal_share'] = (top.modal_records / top.level1_records).round(4)
    save(top.sort_values('cod'), 'cnefe_district_crosswalk.csv')
    summary['cnefe_crosswalk_min_modal_share'] = float(top.modal_share.min())
    summary['cnefe_crosswalk_one_to_one'] = bool(top.modal_unit_id.is_unique and len(top) == 96)
    by = c.groupby(['COD_DISTRITO', 'COD_ESPECIE']).size().unstack(fill_value=0).add_prefix('especie_')
    e6 = c[c.COD_ESPECIE == 6].groupby(['COD_DISTRITO', 'COD_INDICADOR_ESTAB_ENDERECO']).size().unstack(fill_value=0)
    by = by.join(e6.rename(columns=lambda k: f'especie_6_indicator_{int(k)}')).reset_index()
    by['especie_6_multiple_share'] = (1 - by.especie_6_indicator_1 / by.especie_6).round(4)
    # Smallest establishment count consistent with the indicators (single=1, up to 10>=2, more than 10>=11, unknown>=2);
    # no upper bound exists because codes 3 and 4 are open-ended.
    by['especie_6_establishments_lower_bound'] = (by.especie_6_indicator_1 + 2 * by.especie_6_indicator_2
                                                  + 11 * by.especie_6_indicator_3 + 2 * by.especie_6_indicator_4)
    save(by.merge(top[['cod', 'modal_unit_id']], left_on='COD_DISTRITO', right_on='cod').drop(columns='cod'),
         'cnefe_by_district_species.csv')
    summary['cnefe_especie_6_establishments_lower_bound_city'] = int(by.especie_6_establishments_lower_bound.sum())


def gtfs():
    rows = []
    for city, cfg in CITY.items():
        p = D / cfg['gtfs']
        for f in ('stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt'):
            sha(p / f)
        s = pd.read_csv(p / 'stops.txt', dtype=str)
        r = pd.read_csv(p / 'routes.txt', dtype=str)
        t = pd.read_csv(p / 'trips.txt', usecols=['route_id', 'trip_id'], dtype=str)
        st = pd.read_csv(p / 'stop_times.txt', usecols=['trip_id', 'stop_id'], dtype=str).drop_duplicates()
        m = st.merge(t, on='trip_id').merge(r[['route_id', 'route_type']], on='route_id')[['stop_id', 'route_type']].drop_duplicates()
        g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon.astype(float), s.stop_lat.astype(float)), crs=4326).to_crs(cfg['crs'])
        summary[f'gtfs_agencies_{city}'] = pd.read_csv(p / 'agency.txt', dtype=str).agency_name.tolist()
        for rt, ids in m.groupby('route_type').stop_id:
            x = g[g.stop_id.isin(set(ids))]
            nn = cKDTree(np.c_[x.geometry.x, x.geometry.y]).query(np.c_[x.geometry.x, x.geometry.y], k=2)[0][:, 1]
            parents = x.parent_station.nunique() if 'parent_station' in x else None
            rows.append(dict(city=city, route_type=rt, served_stops=len(x), distinct_names=x.stop_name.nunique(),
                             distinct_parent_stations=parents, nearest_same_mode_median_m=round(float(np.median(nn)), 1),
                             share_with_same_mode_stop_within_50m=round(float((nn <= 50).mean()), 4)))
    save(pd.DataFrame(rows), 'gtfs_stops_by_mode.csv')


def heights():
    rows = []
    d = districts('Chicago')
    f = D / 'Chicago/overture_2026_08_19/building/part_0000.parquet'
    sha(f)
    b = pd.read_parquet(f, columns=['height', 'num_floors', 'sources', 'bbox'])
    bb = pd.json_normalize(b.pop('bbox'))
    x, y = pyproj.Transformer.from_crs(4326, d.crs, always_xy=True).transform(((bb.xmin + bb.xmax) / 2).values, ((bb.ymin + bb.ymax) / 2).values)
    b = b[shapely.contains_xy(d.union_all(), x, y)]
    hs = b.loc[b.height > 0, 'sources'].map(lambda s: datasets(s, '/properties/height'))
    rows.append(dict(city='Chicago', file=str(f.relative_to(ROOT)), buildings_in_city=len(b), height_positive=int((b.height > 0).sum()),
                     num_floors_positive=int((b.num_floors > 0).sum()), height_sources=json.dumps(hs.value_counts().to_dict())))
    del b, bb, hs
    d = districts('SP')
    sha(SP_BUILDINGS)
    poly = d.union_all()
    shapely.prepare(poly)
    con = sqlite3.connect(f'file:{SP_BUILDINGS}?mode=ro', uri=True)
    cur = con.execute('SELECT b.height_m, b.floor_count, CASE WHEN b.height_m > 0 THEN b.sources_json END, '
                      '(r.minx + r.maxx) / 2, (r.miny + r.maxy) / 2 FROM buildings b JOIN rtree_buildings_geom r ON b.fid = r.id')
    n = hp = fp = 0
    src = {}
    while chunk := cur.fetchmany(500_000):
        c = pd.DataFrame(chunk, columns=['h', 'f', 's', 'x', 'y'])
        c = c[shapely.contains_xy(poly, c.x.values, c.y.values)]
        n += len(c)
        hp += int((c.h > 0).sum())
        fp += int((c.f > 0).sum())
        for k, v in c.s.dropna().map(lambda s: datasets(json.loads(s), '/properties/height')).value_counts().items():
            src[k] = src.get(k, 0) + int(v)
    rows.append(dict(city='SP', file=str(SP_BUILDINGS.relative_to(ROOT)), buildings_in_city=n, height_positive=hp,
                     num_floors_positive=fp, height_sources=json.dumps(src)))
    save(pd.DataFrame(rows), 'building_height_fill.csv')


def segments():
    rows = []
    for city in CITY:
        d = districts(city)
        f = D / city / 'overture_2026_08_19/segment/part_0000.parquet'
        sha(f)
        g = gpd.read_parquet(f, columns=['subtype', 'class', 'names', 'geometry'])
        g = g[(g.subtype == 'road') & g['class'].isin(M1_CLASSES)].to_crs(d.crs)
        g = g[g.within(d.union_all())]
        name = g.names.map(lambda n: n.get('primary') if isinstance(n, dict) else None)
        L = g.length
        rows.append(dict(city=city, classes='M1 ten classes', rule='segment wholly inside city', segments=len(g),
                         median_length_m=round(L.median(), 1), mean_length_m=round(L.mean(), 1),
                         unnamed_share=round(name.isna().mean(), 4), distinct_names=name.nunique(),
                         named_segments_per_name=round(name.notna().sum() / name.nunique(), 2)))
    save(pd.DataFrame(rows), 'overture_segments.csv')


if __name__ == '__main__':
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    for step in (areas, places, cnefe, gtfs, heights, segments):
        step()
        print('done', step.__name__, flush=True)
    (OUT / 'summary.json').write_text(json.dumps(dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                                      code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                      inputs_sha256=inputs, **summary), indent=2, default=str))
