"""Protocol P-AB-1 (docs/SIMPLE_INDEX.md): build the advisor's composite index (method A) and the corrected one
(method B) for 96 SP districts and 77 Chicago Community Areas, run the construction checks (any failure stops the
run) and the pre-registered bias tests T1-T4 and sensitivity S1. Definitions and thresholds come from the protocol;
do not tune them here.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import pyproj
import shapely
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'analysis/data'
W = ROOT / 'analysis/work/prepared'
AUDIT = ROOT / 'analysis/results/SP_CHI/simple_index_source_audit_2026_10_01/tables'
GHSL = ROOT / 'analysis/results/SP_CHI/bv_ghsl_lidar_evaluation_2026_09_30/tables/bv_variants_with_b1.csv'
OUT = ROOT / 'analysis/results/SP_CHI/simple_index_ab_2026_10_01'
T = OUT / 'tables'
T.mkdir(parents=True, exist_ok=True)
CRS = {'SP': 31983, 'Chicago': 26916}
COMMERCIAL = ['shopping', 'food_and_drink', 'services_and_business', 'lifestyle_services', 'lodging']
M1 = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'residential', 'living_street', 'pedestrian', 'unclassified', 'unknown']
FACTORS = ['C', 'R', 'H', 'V', 'N', 'L']
SEED, BOOT, BUS_MERGE_M = 20261001, 2000, 50
inputs, checks = {}, {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(2**22), b''):
            h.update(chunk)
    inputs[str(Path(p).relative_to(ROOT))] = h.hexdigest()


def check(name, ok, detail):
    checks[name] = dict(passed=bool(ok), detail=detail)
    if not ok:
        (OUT / 'checks.json').write_text(json.dumps(checks, indent=2, default=str))
        raise AssertionError(f'{name}: {detail}')
    print('check ok', name, flush=True)


def save(df, name):
    df.to_csv(T / name, index=False)


def norm(s):
    s = unicodedata.normalize('NFKD', str(s).lower())
    return re.sub(r'[^a-z0-9]+', '', ''.join(c for c in s if not unicodedata.combining(c)))


def units():
    sp_p = W / 'SP/sp_prep_2026_09_10_v3/N02/districts.parquet'
    chi_p = W / 'Chicago/chi_local_2026_09_16_v1/districts.parquet'
    chi_land_p = ROOT / 'analysis/results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.parquet'
    for p in (sp_p, chi_p, chi_land_p):
        sha(p)
    sp = gpd.read_parquet(sp_p)
    sp['unit_id'] = 'SP:' + sp.district_id
    sp['land_km2'] = sp.land_area_m2 / 1e6
    chi = gpd.read_parquet(chi_p)
    land = pd.read_parquet(chi_land_p).set_index('unit_id').hydro_land_m2
    chi['land_km2'] = chi.unit_id.map(land) / 1e6
    return {'SP': sp[['unit_id', 'land_km2', 'geometry']], 'Chicago': chi[['unit_id', 'land_km2', 'geometry']]}


def assign(geom, u):
    """unit_id of the unit that contains each geometry (NaN outside every unit)."""
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=geom, crs=u.crs), u[['unit_id', 'geometry']], predicate='within', how='left')
    return j[~j.index.duplicated()].unit_id.reindex(geom.index)


def commercial(city, u):
    f = D / city / 'overture_2026_08_19/place/part_0000.parquet'
    sha(f)
    g = gpd.read_parquet(f, columns=['id', 'geometry', 'taxonomy']).to_crs(u.crs)
    top = g.taxonomy.map(lambda t: t['hierarchy'][0] if t is not None and t['hierarchy'] is not None and len(t['hierarchy']) else None)
    g = g[top.isin(COMMERCIAL)]
    g['unit_id'] = assign(g.geometry, u)
    c = g.groupby('unit_id').size()
    # Independent route: vectorised point-in-polygon per unit.
    x, y = g.geometry.x.values, g.geometry.y.values
    alt = pd.Series({r.unit_id: int(shapely.contains_xy(r.geometry, x, y).sum()) for r in u.itertuples()})
    check(f'commercial_independent_route_{city}', c.reindex(alt.index, fill_value=0).equals(alt), 'sjoin vs contains_xy counts per unit')
    a = pd.read_csv(AUDIT / 'places_by_unit_taxonomy_top.csv').set_index('unit_id')
    sha(AUDIT / 'places_by_unit_taxonomy_top.csv')
    a = a.loc[a.index.isin(u.unit_id), COMMERCIAL].sum(axis=1).astype(int)
    check(f'commercial_matches_source_audit_{city}', c.reindex(a.index, fill_value=0).equals(a), 'per-unit totals vs audit table')
    return c.rename('C_count')


def dwellings_sp(u):
    f = D / 'SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv'
    sha(f)
    c = pd.read_csv(f, sep=';', usecols=['COD_DISTRITO', 'COD_ESPECIE'])
    c = c[c.COD_ESPECIE == 1]
    xw = pd.read_csv(AUDIT / 'cnefe_district_crosswalk.csv')
    sha(AUDIT / 'cnefe_district_crosswalk.csv')
    r = c.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id))).value_counts()
    total = int(pd.read_csv(AUDIT / 'cnefe_species.csv').set_index('COD_ESPECIE').loc[1, 'records'])
    check('dwellings_SP_conserved', int(r.sum()) == total and set(r.index) == set(u.unit_id), f'sum {int(r.sum())} vs CNEFE private dwellings {total}')
    return r.rename('R_count').astype(float)


def dwellings_chi(u):
    pieces_p = W / 'Chicago/chi_functional_2026_09_16_v2/block_district_pieces.parquet'
    tiger = D / 'Chicago/tl_2022_17_tabblock20/tl_2022_17_tabblock20.dbf'
    rel = ROOT / 'analysis/results/Chicago/chi_functional_2026_09_16_v2/tables/functional_attributes.parquet'
    for p in (pieces_p, tiger):
        sha(p)
    pc = pd.read_parquet(pieces_p, columns=['GEOID20', 'unit_id', 'weight', 'POP20'])
    hu = pyogrio.read_dataframe(tiger.with_suffix('.shp'), columns=['GEOID20', 'HOUSING20'], read_geometry=False)
    pc = pc.merge(hu, on='GEOID20', how='left', validate='many_to_one')
    check('dwellings_CHI_blocks_joined', pc.HOUSING20.notna().all(), f'{pc.HOUSING20.isna().sum()} pieces without HOUSING20')
    pop = (pc.POP20 * pc.weight).groupby(pc.unit_id).sum()
    pub = pd.read_parquet(rel).set_index('unit_id').population_allocated
    check('dwellings_CHI_weights_reproduce_U3', float((pop - pub.reindex(pop.index)).abs().max()) < 1e-6, 'area weights reproduce published U3 population')
    wsum = pc.groupby('GEOID20').weight.sum()
    check('dwellings_CHI_no_overallocation', float(wsum.max()) <= 1 + 1e-9, f'max weight sum per block {wsum.max()}')
    alloc = pc.HOUSING20 * pc.weight
    blocks = pc.drop_duplicates('GEOID20')
    checks['dwellings_CHI_accounting'] = dict(passed=True, detail=dict(blocks_intersecting_city=len(blocks),
                                              housing_units_in_those_blocks=int(blocks.HOUSING20.sum()),
                                              allocated=float(alloc.sum()), outside_city_remainder=float(blocks.HOUSING20.sum() - alloc.sum())))
    return alloc.groupby(pc.unit_id).sum().rename('R_count')


def gtfs(city, u):
    p = D / ('Chicago/google_transit' if city == 'Chicago' else 'SP/Socioeconomico/f-6gy-sptrans-latest')
    for f in ('stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt'):
        sha(p / f)
    s = pd.read_csv(p / 'stops.txt', dtype=str)
    r = pd.read_csv(p / 'routes.txt', dtype=str)
    t = pd.read_csv(p / 'trips.txt', usecols=['route_id', 'trip_id'], dtype=str)
    st = pd.read_csv(p / 'stop_times.txt', usecols=['trip_id', 'stop_id'], dtype=str).drop_duplicates()
    m = st.merge(t, on='trip_id').merge(r[['route_id', 'route_type']], on='route_id')[['stop_id', 'route_type']].drop_duplicates()
    g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.stop_lon.astype(float), s.stop_lat.astype(float)), crs=4326).to_crs(u.crs)
    rail = g[g.stop_id.isin(m[m.route_type == '1'].stop_id)]
    if city == 'Chicago':
        stations = g[g.stop_id.isin(rail.parent_station.dropna())]
        check('stations_CHI_all_platforms_have_parent', rail.parent_station.notna().all(), f'{rail.parent_station.isna().sum()} without parent')
    else:
        rail = rail.assign(k=rail.stop_name)
        stations = gpd.GeoDataFrame(rail.groupby('k').geometry.apply(lambda x: shapely.Point(x.x.mean(), x.y.mean())).reset_index(),
                                    geometry='geometry', crs=u.crs)
    bus = g[g.stop_id.isin(m[m.route_type == '3'].stop_id)].reset_index(drop=True)
    # S1: union same-normalized-name bus stops within 50 m.
    xy = np.c_[bus.geometry.x, bus.geometry.y]
    names = bus.stop_name.map(norm).values
    parent = np.arange(len(bus))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, j in cKDTree(xy).query_pairs(BUS_MERGE_M):
        if names[i] == names[j]:
            parent[find(i)] = find(j)
    root = np.array([find(i) for i in range(len(bus))])
    cl = pd.DataFrame(dict(root=root, x=xy[:, 0], y=xy[:, 1])).groupby('root')[['x', 'y']].mean()
    merged = gpd.GeoSeries(gpd.points_from_xy(cl.x, cl.y), crs=u.crs)
    out = pd.DataFrame(dict(
        H_stations=assign(stations.geometry.reset_index(drop=True), u).value_counts(),
        H_bus=assign(bus.geometry, u).value_counts(),
        H_bus_merged=assign(merged, u).value_counts())).reindex(u.unit_id).fillna(0)
    checks[f'hubs_{city}_inventory'] = dict(passed=True, detail=dict(stations_in_feed=len(stations), stations_in_units=int(out.H_stations.sum()),
                                            bus_stops_served=len(bus), bus_in_units=int(out.H_bus.sum()), bus_clusters=len(cl),
                                            bus_clusters_in_units=int(out.H_bus_merged.sum())))
    return out


def heights_A(city, u):
    if city == 'Chicago':
        f = D / 'Chicago/overture_2026_08_19/building/part_0000.parquet'
        sha(f)
        b = pd.read_parquet(f, columns=['height', 'bbox'])
        b = b[b.height > 0]
        bb = pd.json_normalize(b.pop('bbox'))
        x, y = pyproj.Transformer.from_crs(4326, u.crs, always_xy=True).transform(((bb.xmin + bb.xmax) / 2).values, ((bb.ymin + bb.ymax) / 2).values)
        uid = assign(gpd.GeoSeries(gpd.points_from_xy(x, y), crs=u.crs), u)
        h = pd.Series(b.height.values).groupby(uid.values)
        res = pd.DataFrame(dict(V_A_sum=h.sum(), V_A_n=h.size()))
    else:
        f = D / 'SP/Edificacoes/sao_paulo_building_morphology.gpkg'
        sha(f)
        con = sqlite3.connect(f'file:{f}?mode=ro', uri=True)
        cur = con.execute('SELECT b.height_m, (r.minx + r.maxx) / 2, (r.miny + r.maxy) / 2 FROM buildings b '
                          'JOIN rtree_buildings_geom r ON b.fid = r.id WHERE b.height_m > 0')
        parts = []
        while chunk := cur.fetchmany(500_000):
            c = pd.DataFrame(chunk, columns=['h', 'x', 'y'])
            uid = assign(gpd.GeoSeries(gpd.points_from_xy(c.x, c.y), crs=u.crs), u)
            parts.append(c.h.groupby(uid.values).agg(['sum', 'size']))
        a = pd.concat(parts).groupby(level=0).sum()
        res = pd.DataFrame(dict(V_A_sum=a['sum'], V_A_n=a['size']))
    audit = int(pd.read_csv(AUDIT / 'building_height_fill.csv').set_index('city').loc[city, 'height_positive'])
    diff = audit - int(res.V_A_n.sum())
    check(f'heights_A_{city}_reconcile_audit', abs(diff) <= 1e-4 * audit, f'assigned {int(res.V_A_n.sum())} vs audit {audit} (diff {diff}; points on internal unit boundaries)')
    return res


def heights_B():
    sha(GHSL)
    g = pd.read_csv(GHSL).set_index('unit_id')
    w = g.support_m2 * g.valid_fraction
    num, den = g.agbh_mean * w, g.ghsl_built_fraction * w
    check('heights_B_recombination_exact', float(((num / den) / g.height_built_weighted - 1).abs().max()) < 1e-9,
          'built volume / built surface reproduces height_built_weighted')
    return pd.DataFrame(dict(V_B_num=num, V_B_den=den))


def streets(city, u):
    f = D / city / 'overture_2026_08_19/segment/part_0000.parquet'
    sha(f)
    g = gpd.read_parquet(f, columns=['subtype', 'class', 'geometry'])
    g = g[(g.subtype == 'road') & g['class'].isin(M1)].to_crs(u.crs).reset_index(drop=True)
    mid = gpd.GeoSeries(shapely.line_interpolate_point(g.geometry.values, 0.5, normalized=True), crs=u.crs)
    uid = assign(mid, u)
    L = pd.Series(g.length.values).groupby(uid.values)
    return pd.DataFrame(dict(N_count=L.size(), L_sum=L.sum()))


def raw_factors(comp):
    """Raw A and B factor values from additive components (so merged units recombine exactly)."""
    land = comp.land_km2
    hubs = comp.H_stations + comp.H_bus
    hubs_m = comp.H_stations + comp.H_bus_merged
    A = pd.DataFrame(dict(C=comp.C_count, R=comp.R_count, H=hubs, V=comp.V_A_sum / comp.V_A_n, N=comp.N_count, L=comp.L_sum / comp.N_count))
    B = pd.DataFrame(dict(C=comp.C_count / land, R=comp.R_count / land, H=hubs / land, V=comp.V_B_num / comp.V_B_den,
                          N=comp.N_count / land, L=comp.L_sum / comp.N_count))
    S1 = dict(A=hubs_m, B=hubs_m / land)
    return A, B, S1


def scale(raw, ref):
    return (raw - ref.min()) / (ref.max() - ref.min())


def boot_spearman(x, y, rng):
    n = len(x)
    rho = spearmanr(x, y).statistic
    bs = [spearmanr(x[i], y[i]).statistic for i in (rng.integers(0, n, n) for _ in range(BOOT))]
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return rho, lo, hi


def build_components():
    """Additive per-unit components for all 173 units (construction checks run inside)."""
    U = units()
    comps = []
    for city, u in U.items():
        parts = [commercial(city, u), dwellings_sp(u) if city == 'SP' else dwellings_chi(u), gtfs(city, u), heights_A(city, u), streets(city, u)]
        c = pd.concat(parts, axis=1).reindex(u.unit_id)
        c.insert(0, 'land_km2', u.set_index('unit_id').land_km2)
        c.insert(0, 'city', city)
        comps.append(c)
        print('built', city, flush=True)
    comp = pd.concat(comps).join(heights_B())
    comp.index.name = 'unit_id'
    check('units_complete', len(comp) == 173 and comp.index.is_unique and not comp.drop(columns='city').isna().any().any(),
          f'{len(comp)} units, missing: {comp.isna().sum()[comp.isna().sum() > 0].to_dict()}')
    return comp


def build_indices(comp):
    """Raw, scaled factors and index for A and B; res = one row per unit with both methods and ranks."""
    A, B, S1 = raw_factors(comp)
    out = {}
    for name, raw in (('A', A), ('B', B)):
        sc = scale(raw, raw)
        check(f'scaled_range_{name}', bool(((sc.min() == 0) & (sc.max() == 1)).all()), 'every scaled factor spans exactly 0..1')
        idx = sc.sum(axis=1)
        check(f'index_is_sum_{name}', bool(np.allclose(idx, sc[FACTORS].sum(axis=1))), 'index = sum of six scaled factors')
        out[name] = (raw, sc, idx)
    res = pd.DataFrame({'city': comp.city, 'land_km2': comp.land_km2})
    for name, (raw, sc, idx) in out.items():
        res = res.join(raw.add_prefix(f'{name}_raw_')).join(sc.add_prefix(f'{name}_scaled_'))
        res[f'{name}_index'] = idx
        res[f'{name}_rank'] = idx.rank(ascending=False, method='min').astype(int)
    return out, res, S1


def test_t1(comp, out):
    """T1 boundary invariance: SP districts merged into subprefeituras."""
    sub = pd.read_csv(ROOT / 'analysis/config/sp_district_subprefeitura.csv', dtype={'district_id': str})
    sha(ROOT / 'analysis/config/sp_district_subprefeitura.csv')
    sub['unit_id'] = 'SP:' + sub.district_id
    spc = comp.loc[comp.city == 'SP'].join(sub.set_index('unit_id').subprefeitura_id)
    additive = [c for c in comp.columns if c not in ('city', 'subprefeitura_id')]
    merged = spc.groupby('subprefeitura_id')[additive].sum()
    MA, MB, _ = raw_factors(merged)
    sizes = spc.groupby('subprefeitura_id').size()
    multi = sizes[sizes >= 2].index
    t1, t1_detail = [], []
    for name, mraw in (('A', MA), ('B', MB)):
        raw, sc, idx = out[name]
        msc = scale(mraw, raw)  # 173-unit min-max applied unchanged
        mvals = pd.concat([mraw, msc.sum(axis=1).rename('index')], axis=1)
        pvals = pd.concat([raw, idx.rename('index')], axis=1).loc[spc.index].join(spc.subprefeitura_id)
        for f in FACTORS + ['index']:
            lo, hi = pvals.groupby('subprefeitura_id')[f].min(), pvals.groupby('subprefeitura_id')[f].max()
            tol = 1e-9 * np.maximum(1, hi.abs())
            inside = ((mvals[f] >= lo - tol) & (mvals[f] <= hi + tol)).loc[multi]
            ratio = (mvals[f] / hi).loc[multi]
            t1.append(dict(method=name, factor=f, subprefeituras_tested=len(multi), within_parts=int(inside.sum()),
                           share_within=round(inside.mean(), 4), verdict='boundary-invariant' if inside.mean() >= 0.95 else 'depends on boundaries',
                           merged_over_max_part_median=round(ratio.median(), 4), merged_over_max_part_max=round(ratio.max(), 4)))
            t1_detail.append(pd.DataFrame(dict(method=name, factor=f, subprefeitura_id=multi, merged=mvals[f].loc[multi].values,
                                               parts_min=lo.loc[multi].values, parts_max=hi.loc[multi].values, within=inside.values)))
    return pd.DataFrame(t1), pd.concat(t1_detail)


def test_t2(comp, out):
    """T2 size dependence: Spearman with land area, bootstrap 95% interval."""
    rng = np.random.default_rng(SEED)
    t2 = []
    for name, (raw, sc, idx) in out.items():
        for f in FACTORS + ['index']:
            v = idx if f == 'index' else raw[f]
            for scope, mask in (('pooled', comp.city.notna()), ('SP', comp.city == 'SP'), ('Chicago', comp.city == 'Chicago')):
                rho, lo, hi = boot_spearman(v[mask].to_numpy(), comp.land_km2[mask].to_numpy(), rng)
                t2.append(dict(method=name, factor=f, scope=scope, n=int(mask.sum()), spearman=round(rho, 4), ci_low=round(lo, 4), ci_high=round(hi, 4),
                               verdict='size-dependent' if (lo > 0 or hi < 0) and abs(rho) >= 0.3 else 'not size-dependent'))
    return pd.DataFrame(t2)


def top(r, k):
    return set(r[r <= k].index)


def test_t3(res, comp):
    """T3 agreement between the A and B indices."""
    rA, rB = res.A_rank, res.B_rank
    t3 = dict(spearman_pooled=round(spearmanr(res.A_index, res.B_index).statistic, 4),
              spearman_SP=round(spearmanr(res.A_index[comp.city == 'SP'], res.B_index[comp.city == 'SP']).statistic, 4),
              spearman_Chicago=round(spearmanr(res.A_index[comp.city == 'Chicago'], res.B_index[comp.city == 'Chicago']).statistic, 4),
              top10_overlap=len(top(rA, 10) & top(rB, 10)), bras_rank_A=int(rA['SP:10']), bras_rank_B=int(rB['SP:10']),
              max_rank_shift=int((rA - rB).abs().max()), unit_with_max_shift=str((rA - rB).abs().idxmax()))
    t3['verdict'] = 'substantively disagree' if t3['spearman_pooled'] < 0.8 or t3['top10_overlap'] < 7 else 'agree'
    return t3


def test_t4(res, comp):
    """T4 city composition of the top and bottom 20."""
    t4 = []
    for name in ('A', 'B'):
        r = res[f'{name}_rank']
        for label, sel in (('top20', r <= 20), ('bottom20', r > 173 - 20)):
            t4.append(dict(method=name, group=label, chicago=int((comp.city[sel] == 'Chicago').sum()), sp=int((comp.city[sel] == 'SP').sum()),
                           expected_chicago_at_unit_share=round(20 * 77 / 173, 2)))
    return pd.DataFrame(t4)


def test_s1(out, S1):
    """S1 sensitivity: bus stops merged (same normalized name within 50 m)."""
    s1 = []
    for name in ('A', 'B'):
        raw, sc, idx = out[name]
        raw2 = raw.assign(H=S1[name])
        idx2 = scale(raw2, raw2).sum(axis=1)
        r1, r2 = idx.rank(ascending=False, method='min'), idx2.rank(ascending=False, method='min')
        s1.append(dict(method=name, spearman_with_primary=round(spearmanr(idx, idx2).statistic, 4), top10_overlap=len(top(r1, 10) & top(r2, 10)),
                       bras_rank_primary=int(r1['SP:10']), bras_rank_merged=int(r2['SP:10']), max_rank_shift=int((r1 - r2).abs().max())))
    return pd.DataFrame(s1)


def unit_names():
    sp = pd.read_parquet(W / 'SP/sp_prep_2026_09_10_v3/N02/districts.parquet', columns=['district_id', 'nm_distrito_municipal'])
    chi = pd.read_parquet(W / 'Chicago/chi_local_2026_09_16_v1/districts.parquet', columns=['unit_id', 'district_name'])
    return {**dict(zip('SP:' + sp.district_id, sp.nm_distrito_municipal)), **dict(zip(chi.unit_id, chi.district_name))}


def match_chicago(res, unit='SP:10'):
    """Application: every Chicago area ranked by closeness to `unit` in index value (the agreed one-number model), per
    method. profile_distance (Euclidean over the six scaled factors) is a diagnostic of whether a match holds factor by factor."""
    names = unit_names()
    rows = []
    chi = res[res.city == 'Chicago']
    for m in ('A', 'B'):
        sc = [f'{m}_scaled_{f}' for f in FACTORS]
        gap = (chi[f'{m}_index'] - res.at[unit, f'{m}_index']).abs()
        prof = np.sqrt(((chi[sc].astype(float) - res.loc[unit, sc].astype(float)) ** 2).sum(axis=1))
        t = pd.DataFrame(dict(method=m, unit_id=chi.index, name=chi.index.map(names), index=chi[f'{m}_index'].round(4),
                              reference=unit, reference_index=round(res.at[unit, f'{m}_index'], 4), index_gap=gap.round(4),
                              rank_by_index_gap=gap.rank(method='min').astype(int), profile_distance=prof.round(4),
                              rank_by_profile_distance=prof.rank(method='min').astype(int)))
        rows.append(t.reset_index(drop=True).sort_values(['rank_by_index_gap', 'unit_id']))
    return pd.concat(rows)


def index_summary(res):
    """Distribution of each index by city."""
    return pd.concat({m: res.groupby('city')[f'{m}_index'].describe()[['count', 'min', '25%', '50%', '75%', 'max']] for m in ('A', 'B')}).round(4).reset_index().rename(columns={'level_0': 'method'})


def main():
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    comp = build_components()
    save(comp.reset_index(), 'unit_components.csv')
    out, res, S1 = build_indices(comp)
    save(res.reset_index(), 'index_A_B.csv')
    t1, t1_detail = test_t1(comp, out)
    save(t1, 't1_boundary_invariance.csv')
    save(t1_detail, 't1_boundary_invariance_detail.csv')
    save(test_t2(comp, out), 't2_size_dependence.csv')
    t3 = test_t3(res, comp)
    save(pd.DataFrame([t3]), 't3_agreement.csv')
    save(test_t4(res, comp), 't4_city_composition.csv')
    save(test_s1(out, S1), 's1_bus_merged.csv')
    save(match_chicago(res), 'bras_chicago_match.csv')
    save(index_summary(res), 'index_summary.csv')
    (OUT / 'checks.json').write_text(json.dumps(checks, indent=2, default=str))
    (OUT / 'summary.json').write_text(json.dumps(dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                                      protocol='P-AB-1, docs/SIMPLE_INDEX.md', code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                      checks_passed=sum(c['passed'] for c in checks.values()), checks_total=len(checks),
                                                      t3=t3, inputs_sha256=inputs), indent=2, default=str))
    print('done', flush=True)


if __name__ == '__main__':
    main()
