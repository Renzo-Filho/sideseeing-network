"""Route plan for a collection area: one out-and-back module per street, built from OSM sidewalks and crossings.

Run from network/:  python -m walk2net.plan AREA PROTOCOL      e.g.  python -m walk2net.plan west_loop briefing-2026-11
The area's settings are in network/areas/<AREA>.toml ([plan]); the protocol (network/protocols/) says which side each
street's out leg walks: the out leg goes north or east, with the road on the side the protocol names.
Writes the area's plan/ folder (git-ignored): osm_<date>.json (cached download), routes.gpkg, sessions.csv,
unassigned.csv, overview.png and cards/<MODULE>.png.

Rule: walk a street out on one side and back on the other, crossing straight ahead at every intersection.
A crosswalk over street T therefore belongs to the perpendicular street whose sidewalk line it continues,
exactly like a sidewalk piece. OSM is a planning inventory, not ground truth: field checks win.
"""
import json
import sys
from datetime import date

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from shapely.geometry import LineString, Point, box
from shapely.ops import polygonize, unary_union

from walk2net.config import Area, Protocol

OUTER_M = 30                               # reach past the boundary-street centrelines for the outer sides
SEARCH_M = 30                              # max distance from a sidewalk piece to its street centreline
PARALLEL_DEG = 35                          # max angle between a piece and its street
WALK_MS = 1.4                              # pilot median walking speed (pilot_gps_overview.ipynb)
MIN_MODULE_M = 50                          # modules with less than this go to the review list
MIN_SPLIT_M = 100                          # split_ew_at applies when both parts have this much sidewalk
GAP_M = 40                                 # along-street stretch without mapped pieces that sessions.csv reports
ROADS = {'primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street', 'trunk'}
LINKS = {'primary_link', 'secondary_link', 'tertiary_link', 'motorway_link', 'trunk_link'}


def fetch_osm(out, bbox):
    out.mkdir(parents=True, exist_ok=True)
    cached = sorted(out.glob('osm_*.json'))
    if cached:
        return json.loads(cached[-1].read_text()), cached[-1].stem[4:]
    s, w, n, e = bbox
    q = (f'[out:json][timeout:180];(way["highway"]({s},{w},{n},{e});way["waterway"="river"]({s},{w},{n},{e});'
         f'way["railway"~"subway|light_rail|rail"]({s},{w},{n},{e});'
         f'node["crossing"]({s},{w},{n},{e}););out body geom;')
    for url in ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter',
                'https://overpass.private.coffee/api/interpreter']:
        r = requests.post(url, data={'data': q}, timeout=300, headers={'User-Agent': 'sideseeing-network research'})
        if r.ok:
            break
    r.raise_for_status()
    day = date.today().isoformat()
    (out / f'osm_{day}.json').write_text(r.text)
    return r.json(), day


def ways_frame(elements, crs):
    rows = [dict(osm_id=e['id'], **{k: e.get('tags', {}).get(k) for k in
                 ['highway', 'footway', 'crossing', 'name', 'layer', 'tunnel', 'bridge', 'level', 'waterway', 'railway']},
                 geometry=LineString([(p['lon'], p['lat']) for p in e['geometry']]))
            for e in elements if e['type'] == 'way' and len(e.get('geometry', [])) > 1]
    return gpd.GeoDataFrame(rows, crs=4326).to_crs(crs)


def street_name(name):
    """'West Erie Street' and 'East Erie Street' are one street, 'Erie'; LaSalle Drive/Street are 'LaSalle'.
    Likewise Washington Boulevard/Street, and Fulton Street/Market (Fulton Market is the street's eastern name)."""
    words = name.split()
    if words[0] in {'North', 'South', 'East', 'West'}:
        words = words[1:]
    if words[-1] in {'Street', 'Avenue', 'Drive', 'Court', 'Plaza', 'Boulevard', 'Market'} and len(words) > 1:
        words = words[:-1]
    return ' '.join(words)


def segments(gdf, cols):
    """Explode lines into their 2-point segments, keeping `cols`."""
    rows = []
    for rec in gdf[cols + ['geometry']].itertuples(index=False):
        c = np.asarray(rec.geometry.coords)
        for a, b in zip(c[:-1], c[1:]):
            if np.hypot(*(b - a)) > 0.5:
                rows.append((*rec[:-1], LineString([a, b])))
    return gpd.GeoDataFrame(rows, columns=cols + ['geometry'], crs=gdf.crs)


def gaps(g, ax):
    """Stretches along the street axis that no line of `g` covers, as arrays of their (start, end) positions."""
    b = g.bounds.sort_values('minx' if ax == 'EW' else 'miny')
    lo, hi = (b.minx, b.maxx) if ax == 'EW' else (b.miny, b.maxy)
    return np.maximum.accumulate(hi.values)[:-1], lo.values[1:]


def bearing(seg):
    (x0, y0), (x1, y1) = seg.coords
    return np.degrees(np.arctan2(x1 - x0, y1 - y0)) % 180  # 0 = N-S, 90 = E-W


def main(area_key, protocol_name):
    area_cfg, protocol = Area.load(area_key), Protocol.load(protocol_name)
    cfg, out, crs = area_cfg.plan, area_cfg.data / 'plan', area_cfg.crs
    osm, day = fetch_osm(out, cfg['bbox'])
    W = ways_frame(osm['elements'], crs)
    # Off street level. A multi-level area drops lower-level streets and everything tagged below ground. A
    # one-level area drops only 'Lower ...' streets: West Loop's layer -1 sidewalks are ordinary blocks, and
    # Randolph and Washington pass under the Ogilvie train shed as building passages.
    below = W.name.fillna('').str.contains('Lower')
    if cfg['multi_level']:
        below |= (pd.to_numeric(W.layer, errors='coerce').fillna(0) < 0) | W.tunnel.isin(['yes', 'building_passage'])

    # Area: land inside the boundary-street centrelines (median position of each), bounded by the river.
    roads = W[W.highway.isin(ROADS) & ~below & W.name.notna()].copy()
    roads['street'] = roads.name.map(street_name)
    lim = dict(zip('WSEN', W.total_bounds))
    for street, side in cfg['edges'].items():
        c = roads[roads.street == street].geometry.centroid
        lim[side] = (c.x if side in 'EW' else c.y).median()
    frame = box(lim['W'], lim['S'], lim['E'], lim['N'])
    river = W[W.waterway == 'river'].geometry
    inside = gpd.GeoSeries([Point(cfg['inside'])], crs=4326).to_crs(crs).iloc[0]
    core = next(p for p in polygonize(unary_union([frame.exterior, *river])) if p.contains(inside))
    area = core.union(core.buffer(OUTER_M).difference(frame.buffer(-1)))  # plus the outer sides of the edges

    # Pieces to walk: sidewalks and crosswalks inside the area, excluding bridges and lower levels. Bridges over
    # the river or a boundary expressway lead out of the area. A multi-level area drops all bridges; a one-level
    # area keeps the others (every West Loop E-W street crosses the Kennedy on one).
    leads_out = W[(W.waterway == 'river') | W.name.isin(cfg.get('bridges_out', []))].union_all()
    bridge = W.bridge.notna() & (W.intersects(leads_out) | cfg['multi_level'])
    walk = W[(W.highway == 'footway') & W.footway.isin(['sidewalk', 'crossing']) & ~below & ~bridge]
    walk = walk.clip(area).explode(index_parts=False)
    walk = walk[walk.geom_type == 'LineString']
    walk['kind'] = walk.footway
    walk['signals'] = walk.crossing.eq('traffic_signals')
    pieces = segments(walk, ['osm_id', 'kind', 'signals'])

    # Street centreline segments, oriented east (E-W streets) or north (N-S streets).
    rs = segments(roads.clip(area.buffer(SEARCH_M)).explode(index_parts=False).pipe(lambda d: d[d.geom_type == 'LineString']),
                  ['street'])
    rs['bear'] = rs.geometry.map(bearing)
    axis = rs.groupby('street').bear.median().map(lambda b: 'EW' if 45 <= b < 135 else 'NS')
    rs['axis'] = rs.street.map(axis)

    def oriented(seg, ax):
        (x0, y0), (x1, y1) = seg.coords
        return (x1 - x0, y1 - y0) if (x1 - x0 if ax == 'EW' else y1 - y0) >= 0 else (x0 - x1, y0 - y1)

    rs['dx'], rs['dy'] = zip(*[oriented(g, a) for g, a in zip(rs.geometry, rs.axis)])

    # Assign each piece to the nearest parallel street within SEARCH_M, and to a side of it.
    pieces['bear'] = pieces.geometry.map(bearing)
    cand = gpd.sjoin(pieces.assign(geometry=pieces.buffer(SEARCH_M)), rs, predicate='intersects', lsuffix='p', rsuffix='r')
    diff = (cand.bear_p - cand.bear_r).abs()
    cand = cand[np.minimum(diff, 180 - diff) <= PARALLEL_DEG].copy()
    cand['dist'] = [pieces.geometry.loc[i].distance(rs.geometry.loc[j]) for i, j in zip(cand.index, cand.index_r)]
    pm = pieces.geometry.interpolate(0.5, normalized=True)
    best = cand.sort_values('dist').groupby(level=0).head(1)
    pieces.loc[best.index, 'street'] = best.street.values
    pieces.loc[best.index, 'axis'] = best.axis.values
    # Side: left of an eastbound street is north, left of a northbound street is west. Tested against the street's
    # segment nearest the piece's midpoint: a long piece can tie between two segments, and the far one's line may
    # pass on the wrong side of it.
    same = cand[cand.street.values == best.street.reindex(cand.index).values].copy()
    same['dist_mid'] = [pm.loc[i].distance(rs.geometry.loc[j]) for i, j in zip(same.index, same.index_r)]
    seg = same.sort_values('dist_mid').groupby(level=0).head(1).reindex(best.index)
    rx, ry = np.array([g.coords[0] for g in rs.geometry.loc[seg.index_r]]).T
    cross = seg.dx.values * (pm.loc[best.index].y.values - ry) - seg.dy.values * (pm.loc[best.index].x.values - rx)
    left = cross > 0
    pieces.loc[best.index, 'side'] = np.where(best.axis.values == 'EW', np.where(left, 'N', 'S'), np.where(left, 'W', 'E'))
    pieces['length_m'] = pieces.length

    # Beyond the boundary streets only their own outer sidewalks are in scope, not side-street stubs.
    stub = ~pieces.geometry.centroid.within(core) & (pieces.kind == 'sidewalk') & pieces.street.notna() \
        & ~pieces.street.isin(list(cfg['edges']))
    pieces = pieces[~stub].copy()

    # Modules: one per street, unless the area config splits it.
    has = pieces.street.notna()
    pieces['module'] = pieces.street.str.upper().str.replace(' ', '_')
    if 'split_ew_at' in cfg:
        # E-W streets with sidewalk on both sides of a N-S street become two modules there (_WEST, _EAST). The
        # crosswalk over it goes to the east module, so the west module U-turns at its west corners. Compared in
        # lon/lat, where the grid street is a straight line.
        split_lon = roads[roads.street == cfg['split_ew_at']].geometry.centroid.to_crs(4326).x.median()
        lon = pieces.to_crs(4326).bounds.maxx
        lon = lon.where(pieces.kind == 'sidewalk', lon.groupby(pieces.osm_id).transform('max'))  # a crosswalk goes whole
        part = pd.Series(np.where(lon <= split_lon, '_WEST', '_EAST'), index=pieces.index)
        sw = pieces.length_m.where(has & (pieces.axis == 'EW') & (pieces.kind == 'sidewalk'), 0)
        per_part = sw.groupby([pieces.street, part]).sum().unstack().reindex(columns=['_WEST', '_EAST'], fill_value=0)
        both = (per_part.fillna(0) >= MIN_SPLIT_M).all(axis=1)
        split = pieces.street.isin(both[both].index)
        pieces.loc[split, 'module'] += part[split]
    if 'run_gap_m' in cfg:
        # A street whose centreline breaks (park, rail yard, expressway without a bridge) is walked as separate
        # runs, lettered west to east or south to north.
        pos = pd.Series(np.where(pieces.axis == 'EW', pieces.geometry.centroid.x, pieces.geometry.centroid.y),
                        index=pieces.index)
        run = pd.Series(0, index=pieces.index)
        for street, ax in pieces[has].groupby('street')['axis'].first().items():
            s0, s1 = gaps(rs[rs.street == street], ax)
            m = pieces.street == street
            run[m] = np.searchsorted(((s0 + s1) / 2)[s1 - s0 >= cfg['run_gap_m']], pos[m])
        by_module = run[has].groupby(pieces.module[has])
        multi = by_module.transform('nunique') > 1
        letter = by_module.rank(method='dense').astype(int).map(lambda r: '_' + 'ABCDEFGH'[r - 1])
        pieces.loc[multi[multi].index, 'module'] += letter[multi]
    tiny = pieces.groupby('module').length_m.transform('sum') < MIN_MODULE_M
    pieces.loc[tiny, ['street', 'axis', 'side', 'module']] = None

    # Sessions: the out leg goes north (N-S streets) or east (E-W streets) on the side the protocol gives it, the back
    # leg the other way on the other side.
    out_side = {ax: protocol.out_side(ax) for ax in ('NS', 'EW')}
    assert all(out_side.values()), f'{protocol.name} does not fix the sides of a street: it cannot plan legs'
    DIRECTION = {('NS', 'out'): 'northbound', ('NS', 'back'): 'southbound', ('EW', 'out'): 'eastbound', ('EW', 'back'): 'westbound'}
    a = pieces.dropna(subset=['street']).copy()
    a['session'] = a.module + '-' + a.side
    rows = []
    for (mod, side), g in a.groupby(['module', 'side']):
        ax = g.axis.iat[0]
        pos = g.geometry.centroid.x if ax == 'EW' else g.geometry.centroid.y
        first, last = g.loc[pos.idxmin()].geometry.centroid, g.loc[pos.idxmax()].geometry.centroid
        s0, s1 = gaps(g, ax)  # stretches of the leg with no mapped sidewalk or crosswalk: a site check
        gap = s1 - s0
        leg = 'out' if side == out_side[ax] else 'back'
        start, end = (first, last) if leg == 'out' else (last, first)
        to_ll = lambda p: gpd.GeoSeries([p], crs=crs).to_crs(4326).iloc[0]
        s, e = to_ll(start), to_ll(end)
        sw, cw = g[g.kind == 'sidewalk'], g[g.kind == 'crossing']
        other = rs[rs.street != g.street.iat[0]]
        cross_street = lambda p: other.street.iat[other.distance(p).argmin()]
        rows.append(dict(module=mod, axis=ax, session=f'{mod}-{side}', leg=leg, direction=DIRECTION[(ax, leg)],
                         from_street=cross_street(start), to_street=cross_street(end),
                         sidewalk_m=round(sw.length_m.sum()), crosswalks=cw.osm_id.nunique(),
                         signal_crosswalks=cw[cw.signals].osm_id.nunique(), crosswalk_m=round(cw.length_m.sum()),
                         walk_min=round((sw.length_m.sum() + cw.length_m.sum()) / WALK_MS / 60, 1),
                         gap_m=round(gap[gap >= GAP_M].sum()),
                         start_lat=round(s.y, 6), start_lon=round(s.x, 6), end_lat=round(e.y, 6), end_lon=round(e.x, 6)))
    sessions = pd.DataFrame(rows)
    sessions['key'] = np.where(sessions.axis == 'EW', sessions.groupby('module').start_lat.transform('mean'),
                               -sessions.groupby('module').start_lon.transform('mean'))
    sessions = sessions.sort_values(['axis', 'key', 'leg'], ascending=[False, True, False]).drop(columns='key')
    sessions.to_csv(out / 'sessions.csv', index=False)

    # Review list: what each unassigned piece sits next to (including lower-level streets) and where.
    un = pieces[pieces.street.isna()].dissolve(by='osm_id', aggfunc={'kind': 'first', 'length_m': 'sum'}).reset_index()
    un = un[un.length_m >= 5]
    near = W[W.highway.isin(ROADS | LINKS) & W.name.notna()][['name', 'layer', 'geometry']]
    un = gpd.sjoin_nearest(un, near, how='left', distance_col='near_m').drop_duplicates('osm_id')
    c = un.geometry.to_crs(4326).centroid
    un.assign(lat=c.y.round(6), lon=c.x.round(6)).rename(columns={'name': 'near_street', 'layer': 'near_layer'}) \
        [['osm_id', 'kind', 'length_m', 'near_street', 'near_layer', 'near_m', 'lat', 'lon']] \
        .round({'length_m': 0, 'near_m': 0}).sort_values('length_m', ascending=False).to_csv(out / 'unassigned.csv', index=False)

    gpd.GeoDataFrame({'name': ['core', 'collection area']}, geometry=[core, area], crs=crs).to_file(out / 'routes.gpkg', layer='area')
    pieces.drop(columns='bear').to_file(out / 'routes.gpkg', layer='pieces')

    tot = pieces.groupby('kind').length_m.sum()
    got = a.groupby('kind').length_m.sum()
    print(f'OSM snapshot {day}; core area {core.area / 1e6:.2f} km2, collection area {area.area / 1e6:.2f} km2')
    for k in tot.index:
        print(f'{k}: {tot[k] / 1e3:.1f} km in area, {got.get(k, 0) / 1e3:.1f} km assigned ({100 * got.get(k, 0) / tot[k]:.0f}%)')
    print(f'{sessions.module.nunique()} modules, {len(sessions)} sessions; walking time at {WALK_MS} m/s: '
          f'{sessions.walk_min.sum() / 60:.1f} h; crosswalks {sessions.crosswalks.sum()} '
          f'({sessions.signal_crosswalks.sum()} signalised)')

    draw(out, area_cfg.name, core, area, pieces, a, sessions, W, below)


def draw(out, name, core, area, pieces, a, sessions, W, below):
    rail = W[W.railway.notna() & ((pd.to_numeric(W.layer, errors='coerce') > 0) | W.bridge.notna())].clip(area.buffer(60))  # elevated only
    river = W[W.waterway == 'river'].clip(area.buffer(300))
    ctx = W[W.highway.isin(ROADS) & ~below].clip(area.buffer(120))

    def base(ax):
        ctx.plot(ax=ax, color='#d0d0d0', lw=.6)
        river.plot(ax=ax, color='#7fb2e0', lw=3)
        rail.plot(ax=ax, color='#555', lw=1.2, ls='--')
        gpd.GeoSeries([core]).boundary.plot(ax=ax, color='#c33', lw=1)
        ax.set_aspect('equal'); ax.set_axis_off()

    fig, ax = plt.subplots(figsize=(14, 11))
    base(ax)
    for ax_, color in [('EW', '#1f6fd1'), ('NS', '#d1661f')]:
        a[a.axis == ax_].plot(ax=ax, color=color, lw=1.4)
    pieces[pieces.street.isna()].plot(ax=ax, color='#cc0077', lw=2)
    for mod, g in a.groupby('module'):
        p = g.geometry.union_all().centroid
        ax.annotate(mod, (p.x, p.y), fontsize=7, ha='center', color='black',
                    bbox=dict(fc='white', ec='none', alpha=.75, pad=1))
    ax.set_title(f'{name} modules: blue = east-west streets, orange = north-south streets, '
                 'magenta = not assigned (review), dashed = elevated rail')
    fig.savefig(out / 'overview.png', dpi=110, bbox_inches='tight')
    plt.close(fig)

    (out / 'cards').mkdir(exist_ok=True)
    for old in (out / 'cards').glob('*.png'):  # cards of modules that no longer exist would mislead in the field
        old.unlink()
    for mod, g in a.groupby('module'):
        fig, ax = plt.subplots(figsize=(9, 8))
        base(ax)
        a.plot(ax=ax, color='#bbbbbb', lw=.8)
        for _, s in sessions[sessions.module == mod].iterrows():
            sel = g[g.session == s.session]
            color = '#1a7f37' if s.leg == 'out' else '#8250df'
            sel.plot(ax=ax, color=color, lw=2.6)
            st, en = [gpd.GeoSeries([Point(lon, lat)], crs=4326).to_crs(W.crs).iloc[0]
                      for lat, lon in [(s.start_lat, s.start_lon), (s.end_lat, s.end_lon)]]
            ax.annotate('', xy=(en.x, en.y), xytext=(st.x, st.y),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=.6))
            ax.plot(st.x, st.y, marker='^', color=color, ms=11, mec='white')
            ax.plot([], [], color=color, lw=3, label=f'{s.session} {s.leg}, {s.direction}: {s.sidewalk_m} m, '
                                                      f'{s.crosswalks} crosswalks ({s.signal_crosswalks} signals), ~{s.walk_min} min walking')
        x0, y0, x1, y1 = g.total_bounds
        pad = 120
        ax.set_xlim(x0 - pad, x1 + pad); ax.set_ylim(y0 - pad, y1 + pad)
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.01), fontsize=8, frameon=False)
        ax.set_title(f'Module {mod}  (▲ = start of each leg)')
        fig.savefig(out / 'cards' / f'{mod}.png', dpi=100, bbox_inches='tight')
        plt.close(fig)


if __name__ == '__main__':
    assert len(sys.argv) == 3, 'usage: python -m walk2net.plan AREA PROTOCOL'
    main(*sys.argv[1:])
