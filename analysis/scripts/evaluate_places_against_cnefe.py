"""Protocol P-PLACES-1 (docs/SIMPLE_INDEX.md): coverage of CNEFE 2022 establishment addresses by Overture Places
and OpenStreetMap in São Paulo, with a 500 m displaced-point chance baseline; descriptive OSM/Overture agreement
in both cities. Rules are fixed in the protocol; do not tune them here.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'analysis/data'
AUDIT = ROOT / 'analysis/results/SP_CHI/simple_index_source_audit_2026_10_01/tables'
OUT = ROOT / 'analysis/results/SP_CHI/places_cnefe_coverage_2026_10_01'
T = OUT / 'tables'
T.mkdir(parents=True, exist_ok=True)
CITY = {'Chicago': ('analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet', 26916),
        'SP': ('analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet', 31983)}
DISTANCES = (25, 50, 100)
SPECIES = (4, 5, 6, 8)
GEO_LEVELS = (1, 2, 3)
OSM_KEYS = ['shop', 'amenity', 'office', 'craft', 'healthcare', 'tourism']
AMENITY_EXCLUDE = {'bench', 'waste_basket', 'waste_disposal', 'recycling', 'parking', 'parking_space', 'parking_entrance',
                   'bicycle_parking', 'motorcycle_parking', 'toilets', 'drinking_water', 'post_box', 'telephone',
                   'vending_machine', 'shelter', 'fountain', 'clock', 'bicycle_rental', 'charging_station', 'taxi',
                   'bus_station', 'grit_bin', 'hunting_stand', 'loading_dock'}
STOP = set('de da do das dos del la las los el the and com para ltda eireli epp sa'.split())
SEED, SHIFT_M = 20261001, 500
summary, inputs = {}, {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(2**22), b''):
            h.update(chunk)
    inputs[str(Path(p).relative_to(ROOT))] = h.hexdigest()


def tokens(name):
    if not isinstance(name, str):
        return frozenset()
    s = unicodedata.normalize('NFKD', name.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return frozenset(t for t in re.sub(r'[^a-z0-9]+', ' ', s).split() if len(t) >= 3 and t not in STOP)


def name_match(a, b):
    return bool(a) and bool(b) and len(a & b) / min(len(a), len(b)) >= 0.5


def districts(city):
    p, crs = CITY[city]
    sha(ROOT / p)
    g = gpd.read_parquet(ROOT / p).to_crs(crs)
    if 'unit_id' not in g:
        g['unit_id'] = 'SP:' + g.district_id
    return g[['unit_id', 'land_area_m2', 'geometry']]


def in_city(g, d):
    j = gpd.sjoin(g, d[['unit_id', 'geometry']], predicate='within', how='inner')
    return j[~j.index.duplicated()].drop(columns='index_right')


def overture(city, d):
    f = D / city / 'overture_2026_08_19/place/part_0000.parquet'
    sha(f)
    g = gpd.read_parquet(f, columns=['id', 'geometry', 'names', 'taxonomy']).to_crs(d.crs)
    g['name'] = g.names.map(lambda n: n.get('primary') if isinstance(n, dict) else None)
    top = g.taxonomy.map(lambda t: t['hierarchy'][0] if t is not None and t['hierarchy'] is not None and len(t['hierarchy']) else None)
    g = g[g.name.fillna('').str.strip().ne('') & top.ne('geographic_entities')]
    return in_city(g[['name', 'geometry']], d).reset_index(drop=True)


def osm(city, d):
    f = D / city / 'osm_2026_10_01/places.parquet'
    sha(f)
    summary[f'osm_snapshot_{city}'] = json.loads((f.parent / 'manifest.json').read_text())['source_last_modified_http']
    o = pd.read_parquet(f)
    tags = o.tags.map(json.loads)
    keep = tags.map(lambda t: any(k in t and not (k == 'amenity' and t[k] in AMENITY_EXCLUDE) for k in OSM_KEYS))
    o = o[keep & o.name.fillna('').str.strip().ne('')]
    g = gpd.GeoDataFrame(o[['name']], geometry=gpd.points_from_xy(o.lon, o.lat), crs=4326).to_crs(d.crs)
    return in_city(g, d).reset_index(drop=True)


def match(ref_xy, ref_tok, cand):
    """Per reference point and distance: any candidate within d (proximity), any name-matched candidate within d."""
    xy = np.c_[cand.geometry.x, cand.geometry.y]
    tok = [tokens(n) for n in cand.name]
    tree = cKDTree(xy)
    prox = np.zeros((len(ref_xy), len(DISTANCES)), bool)
    named = np.zeros_like(prox)
    for i, nb in enumerate(tree.query_ball_point(ref_xy, max(DISTANCES))):
        if not nb:
            continue
        dist = np.hypot(*(xy[nb] - ref_xy[i]).T)
        nm = np.array([name_match(ref_tok[i], tok[j]) for j in nb])
        for k, dd in enumerate(DISTANCES):
            w = dist <= dd
            prox[i, k] = w.any()
            named[i, k] = (w & nm).any()
    return prox, named


def reference(d):
    f = D / 'SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv'
    sha(f)
    c = pd.read_csv(f, sep=';', usecols=['COD_DISTRITO', 'COD_ESPECIE', 'DSC_ESTABELECIMENTO', 'NV_GEO_COORD', 'LATITUDE', 'LONGITUDE'],
                    dtype={'DSC_ESTABELECIMENTO': str})
    c = c[c.COD_ESPECIE.isin(SPECIES)]
    excl = c[~c.NV_GEO_COORD.isin(GEO_LEVELS)]
    summary['reference_excluded_by_geocode_level'] = excl.groupby('NV_GEO_COORD').size().to_dict()
    c = c[c.NV_GEO_COORD.isin(GEO_LEVELS)].reset_index(drop=True)
    xw = pd.read_csv(AUDIT / 'cnefe_district_crosswalk.csv')
    sha(AUDIT / 'cnefe_district_crosswalk.csv')
    c['unit_id'] = c.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    pts = gpd.GeoSeries(gpd.points_from_xy(c.LONGITUDE, c.LATITUDE), crs=4674).to_crs(d.crs)
    c['x'], c['y'] = pts.x.values, pts.y.values
    summary['reference_points'] = len(c)
    summary['reference_points_by_species'] = c.groupby('COD_ESPECIE').size().to_dict()
    return c


def coverage_sp():
    d = districts('SP')
    ref = reference(d)
    ref_tok = [tokens(n) for n in ref.DSC_ESTABELECIMENTO]
    xy = ref[['x', 'y']].to_numpy()
    theta = np.random.default_rng(SEED).uniform(0, 2 * np.pi, len(xy))
    shifted = xy + SHIFT_M * np.c_[np.cos(theta), np.sin(theta)]
    sources = {'overture': overture('SP', d), 'osm': osm('SP', d)}
    summary['candidates_SP'] = {k: len(v) for k, v in sources.items()}
    city, by_unit = [], []
    for src, cand in sources.items():
        for variant, pts in (('observed', xy), ('displaced_500m', shifted)):
            prox, named = match(pts, ref_tok, cand)
            for mtype, m in (('proximity', prox), ('name', named)):
                for k, dd in enumerate(DISTANCES):
                    col = pd.Series(m[:, k])
                    for sp, grp in [('all', ref.index)] + [(s, ref.index[ref.COD_ESPECIE == s]) for s in SPECIES]:
                        city.append(dict(source=src, variant=variant, match=mtype, distance_m=dd, especie=sp,
                                         reference=len(grp), matched=int(col[grp].sum()), rate=round(col[grp].mean(), 4)))
                    u = col.groupby(ref.unit_id).agg(['size', 'sum']).reset_index()
                    u.columns = ['unit_id', 'reference', 'matched']
                    u['rate'] = (u.matched / u.reference).round(4)
                    by_unit.append(u.assign(source=src, variant=variant, match=mtype, distance_m=dd))
            print('matched', src, variant, flush=True)
    save(pd.DataFrame(city), 'coverage_citywide.csv')
    bu = pd.concat(by_unit)
    save(bu, 'coverage_by_district.csv')
    density = ref.groupby('unit_id').size() / (d.set_index('unit_id').land_area_m2 / 1e6)
    obs = bu[bu.variant == 'observed'].set_index(['source', 'match', 'distance_m', 'unit_id']).rate
    nul = bu[bu.variant != 'observed'].set_index(['source', 'match', 'distance_m', 'unit_id']).rate
    rows = []
    for key, r in (obs - nul).groupby(level=[0, 1, 2]):
        o = obs.loc[key]
        x = r.droplevel([0, 1, 2])
        rows.append(dict(source=key[0], match=key[1], distance_m=key[2],
                         observed_min=o.min(), observed_median=o.median(), observed_max=o.max(),
                         excess_min=round(x.min(), 4), excess_median=round(x.median(), 4), excess_max=round(x.max(), 4),
                         spearman_excess_vs_reference_density=round(spearmanr(x, density.reindex(x.index)).statistic, 4)))
    save(pd.DataFrame(rows), 'district_spread.csv')
    return d, sources


def agreement(city, d, sources):
    rows, counts = [], []
    for a, b in (('osm', 'overture'), ('overture', 'osm')):
        A, B = sources[a], sources[b]
        prox, named = match(np.c_[A.geometry.x, A.geometry.y], [tokens(n) for n in A.name], B)
        k = DISTANCES.index(50)
        rows.append(dict(city=city, records_of=a, found_in=b, records=len(A), name_match_50m=int(named[:, k].sum()),
                         rate=round(named[:, k].mean(), 4)))
    for s, g in sources.items():
        counts.append(g.groupby('unit_id').size().rename(f'{s}_records'))
    c = pd.concat(counts, axis=1).fillna(0).astype(int).reset_index()
    c.insert(0, 'city', city)
    return rows, c


def save(df, name):
    df.to_csv(T / name, index=False)


if __name__ == '__main__':
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    d_sp, src_sp = coverage_sp()
    d_chi = districts('Chicago')
    src_chi = {'overture': overture('Chicago', d_chi), 'osm': osm('Chicago', d_chi)}
    summary['candidates_Chicago'] = {k: len(v) for k, v in src_chi.items()}
    agree, counts = [], []
    for city, d, s in (('SP', d_sp, src_sp), ('Chicago', d_chi, src_chi)):
        r, c = agreement(city, d, s)
        agree += r
        counts.append(c)
    save(pd.DataFrame(agree), 'source_agreement.csv')
    save(pd.concat(counts), 'records_by_unit.csv')
    (OUT / 'summary.json').write_text(json.dumps(dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                                      protocol='P-PLACES-1, docs/SIMPLE_INDEX.md',
                                                      code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                      inputs_sha256=inputs, **summary), indent=2, default=str))
