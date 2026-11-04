"""Compare route plans for one area: the module plan of routes.py against CPP, RPP and CARP routes.

Run after routes.py:  .venv/bin/python network/scripts/route_methods.py west_loop
Reads network/data/<area>/plan/ (OSM snapshot, routes.gpkg, sessions.csv) and writes its routing/:
  routing.gpkg   `edges` (the walkable graph, `req` = survey target), `zones`, and one layer per plan with every
                 traversal in walking order: day, session, status (first pass, repeat, transfer)
  compare.csv    one row per plan
  map.html       the plans by day and session, with direction arrows and your position (open it on the phone)
  gpx/<plan>/    one GPX track per session, for a phone map app

All plans cover the same required edges: the sidewalk and crosswalk pieces routes.py assigned to a module.
Costs are field seconds: walking at 1.4 m/s, plus a signal wait or a curb pause per crosswalk traversed.
The solvers are the standard heuristics: join the pieces with a minimum spanning tree of shortest paths, pair
odd nodes by minimum-weight matching, follow an Euler circuit, then cut it into sessions and days
(route first, cluster second). They give good routes, not proven optima.
"""
import json
import math
import sys
from pathlib import Path

import folium
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from folium import plugins
from shapely.geometry import LineString, MultiLineString, Point
from sklearn.cluster import KMeans

sys.path.insert(0, str(Path(__file__).parent))
from routes import ROOT, UTM, WALK_MS, street_name  # noqa: E402

SIGNAL_S = 35            # mean of Pilot 2's four signal stops (pilot2_test.ipynb); the planning range is 30-60 s
CURB_S = 3               # F3 curb pause at an unsignalised crosswalk
RITUAL_S = 40            # F1 + F2 per session: 30 s still start, 10 s still end
ROAD_FACTOR = 3          # walking along a street centreline (no sidewalk mapped) is a last-resort connector
SESSION_S = 30 * 60      # longest recording session
DAY_S = 3 * 3600         # longest field day: recording, transfers and rituals
TRANSFER_M = 200         # a deadhead stretch longer than this is walked with the recording stopped
MATCH_K, MATCH_CUTOFF_S = 10, 1200   # candidate partners per odd node for the matching
ZONE_SLACK = 1.4         # zones sized so required time x this fits a day; 1.2-1.3 overran into extra short days
PATHS = {'footway', 'pedestrian', 'path', 'steps'}
ROADS = {'living_street', 'residential', 'tertiary', 'secondary', 'primary', 'unclassified', 'service'}
PALETTE = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#e377c2', '#bcbd22',
           '#393b79', '#ad494a', '#637939', '#7b4173', '#e7969c']


def build(out):
    """Walkable graph: one edge per OSM segment, weighted in field seconds; `req` marks the survey targets."""
    osm = json.loads(sorted(out.glob('osm_*.json'))[-1].read_text())
    rows = []
    for e in osm['elements']:
        tags = e.get('tags', {})
        if e['type'] != 'way' or tags.get('highway') not in PATHS | ROADS or tags.get('access') in ('private', 'no'):
            continue
        fw = tags.get('footway')
        kind = fw if fw in ('sidewalk', 'crossing') else 'road' if tags['highway'] in ROADS else 'path'
        for a, b, p, q in zip(e['nodes'][:-1], e['nodes'][1:], e['geometry'][:-1], e['geometry'][1:]):
            if a != b:
                rows.append(dict(u=a, v=b, osm_id=e['id'], kind=kind, sig=tags.get('crossing') == 'traffic_signals',
                                 name=tags.get('name'), geometry=LineString([(p['lon'], p['lat']), (q['lon'], q['lat'])])))
    E = gpd.GeoDataFrame(rows, crs=4326).to_crs(UTM)
    E['m'] = E.length
    way_m = E.groupby('osm_id').m.transform('sum')
    E['t'] = E.m / WALK_MS * np.where(E.kind == 'road', ROAD_FACTOR, 1) \
        + np.where(E.kind == 'crossing', np.where(E.sig, SIGNAL_S, CURB_S) * E.m / way_m, 0)
    E['crossings'] = np.where(E.kind == 'crossing', E.m / way_m, 0)  # a full crosswalk traversal sums to 1

    # Survey targets: the segments under a piece that routes.py assigned to a module.
    P = gpd.read_file(out / 'routes.gpkg', layer='pieces').dropna(subset=['module'])
    mid = gpd.GeoDataFrame({'osm_id': E.osm_id}, geometry=E.geometry.interpolate(0.5, normalized=True), crs=UTM)
    j = gpd.sjoin(mid[E.kind.isin(['sidewalk', 'crossing'])], P[['osm_id', 'street', 'module', 'side', 'geometry']]
                  .assign(geometry=P.buffer(1)), predicate='intersects')
    j = j[j.osm_id_left == j.osm_id_right]
    j = j[~j.index.duplicated()]
    for c in ['street', 'module', 'side']:
        E[c] = j[c].reindex(E.index)
    E['req'] = E.module.notna()
    E['session'] = E.module + '-' + E.side
    E['label'] = E.street.fillna(E.name.map(lambda n: street_name(n) if n else None)).fillna(E.kind)
    G = nx.MultiGraph()
    G.add_edges_from((r.u, r.v, i, {'t': r.t}) for i, r in zip(E.index, E.itertuples()))
    return E, G


def steps(G, nodes):
    """Edges along a node path, taking the cheapest of parallel edges."""
    return [(a, b, min(G[a][b], key=lambda k: G[a][b][k]['t'])) for a, b in zip(nodes[:-1], nodes[1:])]


def tour(E, G, req, start=None):
    """Closed walk covering the edges `req`, deadheading along G. Returns [(u, v, edge, first pass?)]."""
    M = nx.MultiGraph()
    M.add_edges_from((E.u[e], E.v[e], ('r', e)) for e in req)
    n = 0

    def deadhead(path):
        nonlocal n
        for a, b, e in path:
            M.add_edge(a, b, ('d', e, n))
            n += 1

    # 1. Join the pieces: minimum spanning tree over the cheapest connection between every two pieces.
    comps = [frozenset(c) for c in nx.connected_components(M)]
    if len(comps) > 1:
        H = nx.Graph()
        for i, c in enumerate(comps):
            d = nx.multi_source_dijkstra_path_length(G, set(c), weight='t')
            for k in range(i + 1, len(comps)):
                y = min(comps[k], key=lambda x: d.get(x, math.inf))
                H.add_edge(i, k, weight=d.get(y, math.inf), src=i, dst=y)
        for _, _, a in nx.minimum_spanning_edges(H, data=True):
            deadhead(steps(G, nx.multi_source_dijkstra(G, set(comps[a['src']]), target=a['dst'], weight='t')[1]))
    # 2. Pair the odd nodes so every node is even (minimum-weight matching on near candidates).
    odd = {x for x, d in M.degree() if d % 2}
    C = nx.Graph()
    for x in odd:
        d = nx.single_source_dijkstra_path_length(G, x, cutoff=MATCH_CUTOFF_S, weight='t')
        for t, y in sorted((d[y], y) for y in odd if y != x and y in d)[:MATCH_K]:
            C.add_edge(x, y, weight=t)
    pairs = set(nx.min_weight_matching(C))
    left = odd - {x for p in pairs for x in p}
    while left:  # nodes the near candidates could not pair
        x = left.pop()
        d = nx.single_source_dijkstra_path_length(G, x, weight='t')
        y = min(left, key=lambda y: d.get(y, math.inf))
        left.remove(y)
        pairs.add((x, y))
    for x, y in pairs:
        deadhead(steps(G, nx.dijkstra_path(G, x, y, weight='t')))
    assert nx.is_eulerian(M)
    start = start if start in M else next(iter(M))
    return [(u, v, k[1], k[0] == 'r') for u, v, k in nx.eulerian_circuit(M, source=start, keys=True)]


def schedule(E, walk, day0=1):
    """Cut a closed walk into recording sessions and days. Deadhead stretches longer than TRANSFER_M are walked
    with the recording stopped; a session ends at SESSION_S and a day at DAY_S."""
    e = np.array([w[2] for w in walk])
    first = np.array([w[3] for w in walk])
    m, t = E.m.values[e], E.t.values[e]
    status = np.where(first, 'first pass', 'repeat').astype(object)
    i = 0
    while i < len(walk):
        k = i
        while k < len(walk) and not first[k]:
            k += 1
        if m[i:k].sum() > TRANSFER_M:
            status[i:k] = 'transfer'
        i = max(k, i + 1)
    sess, day = np.zeros(len(walk), int), np.zeros(len(walk), int)
    s, d, s_t, d_t, rec = 0, day0, 0.0, 0.0, False
    for k in range(len(walk)):
        if d_t + t[k] > DAY_S and d_t > 0:
            d, d_t, rec = d + 1, 0.0, False
        if status[k] == 'transfer':
            rec = False
        elif not rec or s_t + t[k] > SESSION_S:
            s, s_t, rec = s + 1, 0.0, True
            d_t += RITUAL_S
        if status[k] != 'transfer':
            s_t += t[k]
            sess[k] = s
        d_t += t[k]
        day[k] = d
    return rows(E, walk, status, sess, day)


def rows(E, walk, status, sess, day):
    """One row per traversal, geometry oriented in walking direction."""
    e = [w[2] for w in walk]
    geom = [g if E.u.values[x] == u else LineString(g.coords[::-1]) for (u, _, x, _), g in zip(walk, E.geometry.values[e])]
    return gpd.GeoDataFrame({'seq': range(len(walk)), 'edge': e, 'status': status, 'session': sess, 'day': day,
                             'kind': E.kind.values[e], 'label': E.label.values[e], 'm': E.m.values[e],
                             't': E.t.values[e], 'crossings': E.crossings.values[e] * E.sig.values[e]},
                            geometry=geom, crs=UTM)


def label_sessions(R, by_leg=None):
    """Session names: day and order within the day (D03-2), or the leg ID for the module plan."""
    rec = R[R.session > 0]
    order = rec.groupby('session').agg(day=('day', 'first'), seq=('seq', 'min')).sort_values('seq')
    order['n'] = order.groupby('day').cumcount() + 1
    names = {s: by_leg[s] if by_leg else f'D{r.day:02d}-{r.n}' for s, r in order.iterrows()}
    R['name'] = R.session.map(names).fillna('')
    return R


def module_plan(E, G, out):
    """The routes.py plan as walked: each module's out leg, the U-turn, its back leg; modules in a short order,
    packed into days. Transfers between modules are walked with the recording stopped."""
    legs = pd.read_csv(out / 'sessions.csv')
    xy = gpd.GeoSeries(gpd.points_from_xy(np.r_[legs.start_lon, legs.end_lon], np.r_[legs.start_lat, legs.end_lat]),
                       crs=4326).to_crs(UTM)
    legs['start_pt'], legs['end_pt'] = xy.values[:len(legs)], xy.values[len(legs):]
    req = E[E.req]

    def snap(session, pt):
        g = req[req.session == session]
        ends = pd.concat([pd.Series(g.u.values, index=[Point(c.coords[0]) for c in g.geometry]),
                          pd.Series(g.v.values, index=[Point(c.coords[-1]) for c in g.geometry])])
        return ends.iloc[np.argmin([p.distance(pt) for p in ends.index])]

    def leg_walk(L):
        """The leg's pieces ordered along it, each oriented from start to end. Gaps stay gaps."""
        g = req[req.session == L.session]
        d = np.array([L.end_pt.x - L.start_pt.x, L.end_pt.y - L.start_pt.y])
        proj = lambda p: (p[0] - L.start_pt.x) * d[0] + (p[1] - L.start_pt.y) * d[1]
        walk = []
        for i, r in g.assign(o=[proj(c.interpolate(.5, normalized=True).coords[0]) for c in g.geometry]).sort_values('o').iterrows():
            a, b = (r.u, r.v) if proj(r.geometry.coords[0]) <= proj(r.geometry.coords[-1]) else (r.v, r.u)
            walk.append((a, b, i, True))
        return walk

    mods = []
    for mod, g in legs.groupby('module', sort=False):
        g = g.sort_values('leg', ascending=False)  # out before back
        walks = [leg_walk(L) for L in g.itertuples()]
        ends = [(snap(L.session, L.start_pt), snap(L.session, L.end_pt)) for L in g.itertuples()]
        uturn = steps(G, nx.dijkstra_path(G, ends[0][1], ends[-1][0], weight='t')) if len(g) == 2 else []
        gap_s = g.gap_m.sum() / WALK_MS  # walked along the street where OSM maps nothing
        mods.append(dict(module=mod, legs=list(g.session), walks=walks, uturn=uturn, start=ends[0][0], end=ends[-1][1],
                         t=sum(E.t.values[[w[2] for w in walk]].sum() for walk in walks) + gap_s
                         + sum(G[x][y][k]['t'] for x, y, k in uturn) + RITUAL_S * len(g), gap_s=gap_s))

    # Module order: a short path through all modules (travelling salesman on transfer times, threshold accepting),
    # cut into days where the next module won't fit.
    dist = [nx.single_source_dijkstra_path_length(G, m['end'], weight='t') for m in mods]
    D = nx.DiGraph()
    D.add_weighted_edges_from((i, j, dist[i][mods[j]['start']]) for i in range(len(mods)) for j in range(len(mods)) if i != j)
    cyc = nx.approximation.threshold_accepting_tsp(D, 'greedy', seed=0)[:-1]  # a cycle; open it at its longest hop
    cut = max(range(len(cyc)), key=lambda i: D[cyc[i - 1]][cyc[i]]['weight'])
    seq = cyc[cut:] + cyc[:cut]
    assert sorted(seq) == list(range(len(mods)))
    order, day, day_t = [], 1, 0.0
    for prev, i in zip([None] + seq[:-1], seq):
        m = mods[i]
        hop = steps(G, nx.dijkstra_path(G, mods[prev]['end'], m['start'], weight='t')) if prev is not None else []
        hop_t = sum(G[a][b][k]['t'] for a, b, k in hop)
        if day_t + hop_t + m['t'] > DAY_S and day_t > 0:
            day, day_t, hop, hop_t = day + 1, 0.0, [], 0.0
        order.append((m, hop, day))
        day_t += hop_t + m['t']

    walk, status, sess, days, names, s = [], [], [], [], {}, 0
    for m, hop, day in order:
        for w in hop:
            walk.append((*w, False)); status.append('transfer'); sess.append(0); days.append(day)
        for i, (leg, w) in enumerate(zip(m['legs'], m['walks'])):
            s += 1
            names[s] = leg
            part = w + ([(a, b, k, False) for a, b, k in m['uturn']] if i == 0 else [])
            walk += part
            status += ['first pass'] * len(w) + ['repeat'] * (len(part) - len(w))
            sess += [s] * len(part)
            days += [day] * len(part)
    R = rows(E, walk, np.array(status, dtype=object), np.array(sess), np.array(days))
    return label_sessions(R, names), sum(m['gap_s'] for m, _, _ in order)


def carp(E, G, req, slack=ZONE_SLACK):
    """Hierarchical CARP: compact zones of about a day's work (k-means weighted by field time), a tour per zone,
    cut into sessions. A zone that overruns the day spills into an extra day."""
    mid = E.geometry[req].interpolate(0.5, normalized=True)
    k = math.ceil(E.t[req].sum() * slack / DAY_S)
    zone = pd.Series(KMeans(k, n_init=10, random_state=0).fit_predict(np.c_[mid.x, mid.y], sample_weight=E.t[req]),
                     index=req)
    zone = zone.groupby(E.osm_id[req].where(E.kind[req] == 'crossing', -E.index[req])).transform('first')  # a crosswalk stays whole
    centre = np.c_[mid.x, mid.y].mean(axis=0)  # days go round the area, so consecutive zones are neighbours
    order = sorted(range(k), key=lambda z: math.atan2(*(np.c_[mid.x, mid.y][zone.values == z].mean(axis=0) - centre)[::-1]))
    out, day, last = [], 1, 0
    for n, z in enumerate(order, 1):
        R = schedule(E, tour(E, G, list(zone.index[zone == z])), day0=day)
        R['session'] = np.where(R.session > 0, R.session + last, 0)
        last, day = R.session.max(), R.day.max() + 1
        out.append(R.assign(zone=n))
    zones = gpd.GeoDataFrame({'zone': range(1, k + 1)}, crs=UTM,
                             geometry=[E.geometry[zone.index[zone == z]].buffer(15).union_all() for z in order])
    return label_sessions(pd.concat(out, ignore_index=True).assign(seq=lambda d: range(len(d)))), zones


def metrics(name, R, E, extra_rec_s=0.0):
    req_m = E[E.req].m.sum()
    ids = R[R.status != 'transfer'].edge.unique()
    covered = E.m.values[ids][E.req.values[ids]].sum()
    rec = R[R.status != 'transfer']
    sess_t = rec.groupby('session').t.sum() + RITUAL_S
    changes = sum((g.label.values[1:] != g.label.values[:-1]).sum() for _, g in rec.groupby('session'))
    return dict(plan=name, coverage_pct=round(100 * covered / req_m, 1),
                recorded_km=round(rec.m.sum() / 1e3, 1), repeat_km=round(R[R.status == 'repeat'].m.sum() / 1e3, 1),
                transfer_km=round(R[R.status == 'transfer'].m.sum() / 1e3, 1), walked_km=round(R.m.sum() / 1e3, 1),
                field_h=round((R.t.sum() + RITUAL_S * len(sess_t) + extra_rec_s) / 3600, 1),
                sessions=len(sess_t), days=R.day.nunique(), longest_session_min=round(sess_t.max() / 60),
                signal_crossings=round(R.crossings.sum()), street_changes_per_km=round(changes / (rec.m.sum() / 1e3), 1))


def gpx(R, path):
    """One GPX track per session (recorded parts only), named by session."""
    path.mkdir(parents=True, exist_ok=True)
    for f in path.glob('*.gpx'):
        f.unlink()
    for name, g in R[R.session > 0].to_crs(4326).groupby('name'):
        segs, cur = [], []
        for line in g.sort_values('seq').geometry:
            c = list(line.coords)
            if cur and Point(cur[-1]).distance(Point(c[0])) > 1e-5:
                segs.append(cur)
                cur = []
            cur += c if not cur else c[1:]
        segs.append(cur)
        trk = ''.join('<trkseg>' + ''.join(f'<trkpt lat="{y:.6f}" lon="{x:.6f}"/>' for x, y in s) + '</trkseg>' for s in segs)
        x, y = segs[0][0]
        (path / f'D{g.day.iat[0]:02d}_{name}.gpx').write_text(
            '<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="sideseeing-network" '
            f'xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="{y:.6f}" lon="{x:.6f}"><name>{name} start</name></wpt>'
            f'<trk><name>{name}</name>{trk}</trk></gpx>')


def lines(g):
    """Merge consecutive traversals into as few lines as possible."""
    parts, cur = [], []
    for line in g.sort_values('seq').geometry:
        c = list(line.coords)
        if cur and Point(cur[-1]).distance(Point(c[0])) > 1e-5:
            parts.append(cur)
            cur = []
        cur += c if not cur else c[1:]
    parts.append(cur)
    return MultiLineString(parts)


def web_map(E, plans, zones, path, area_name):
    req = E[E.req].to_crs(4326)
    c = req.union_all().centroid
    # OSM and CARTO tiles refuse a page opened from a file (no referrer or key); Esri's serve it.
    m = folium.Map(location=[c.y, c.x], zoom_start=15, control_scale=True, max_zoom=20, tiles=None)
    esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}'
    folium.TileLayer(esri.format('World_Street_Map'), attr='Esri, HERE, Garmin, OpenStreetMap contributors',
                     name='Streets (Esri)', max_zoom=20, max_native_zoom=19).add_to(m)
    folium.TileLayer(esri.format('World_Imagery'), attr='Esri, Maxar, Earthstar Geographics', name='Satellite (Esri)',
                     max_zoom=20, max_native_zoom=19, show=False).add_to(m)
    folium.GeoJson(req[['geometry']].dissolve().__geo_interface__, name='Survey targets (all sidewalks and crosswalks)',
                   style_function=lambda f: {'color': '#888', 'weight': 2, 'opacity': .6}).add_to(m)
    folium.GeoJson(zones.to_crs(4326).__geo_interface__, name='CARP zones', show=False,
                   style_function=lambda f: {'color': '#555', 'weight': 1, 'fillOpacity': .05},
                   tooltip=folium.GeoJsonTooltip(['zone'])).add_to(m)
    for name, R in plans.items():
        R = R.to_crs(4326)
        for day, gd in R.groupby('day'):
            fg = folium.FeatureGroup(name=f'{name}: day {day}', show=(name, day) == ('modules', 1))
            color = PALETTE[(day - 1) % len(PALETTE)]
            for (sess, nm), g in gd.groupby(['session', 'name']):
                transfer = sess == 0
                shape = lines(g)
                tip = f'{name} · day {day} · ' + ('transfer (not recording)' if transfer else
                                                   f'{nm}: {g.t.sum() / 60:.0f} min, {g.m.sum() / 1e3:.2f} km')
                for part in shape.geoms:
                    ll = [(y, x) for x, y in part.coords]
                    pl = folium.PolyLine(ll, color='#666' if transfer else color, weight=2 if transfer else 4,
                                         dash_array='4 6' if transfer else None, tooltip=tip).add_to(fg)
                    if not transfer and len(ll) > 1:
                        plugins.PolyLineTextPath(pl, '  ►  ', repeat=True, offset=5,
                                                 attributes={'fill': color, 'font-size': '11'}).add_to(fg)
                if not transfer:
                    x, y = shape.geoms[0].coords[0]
                    folium.CircleMarker((y, x), radius=5, color=color, fill=True, fill_opacity=1,
                                        tooltip=f'start {nm}').add_to(fg)
            fg.add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    plugins.LocateControl(keepCurrentZoomLevel=True).add_to(m)
    m.get_root().html.add_child(folium.Element(f'<title>{area_name} routes</title>'))
    m.save(path)


def main(key):
    from routes import AREAS
    out = ROOT / 'data' / key / 'plan'
    dest = out / 'routing'
    dest.mkdir(exist_ok=True)
    E, G = build(out)
    req = list(E.index[E.req])
    print(f'graph: {len(E)} edges; survey targets {E[E.req].m.sum() / 1e3:.1f} km in {len(req)} edges')

    plans, extra = {}, {}
    plans['modules'], extra['modules'] = module_plan(E, G, out)

    # CPP: the classic postman tour may only walk the network it covers, so it needs one connected piece.
    Rq = G.edge_subgraph([(E.u[e], E.v[e], e) for e in req])
    big = max(nx.connected_components(Rq), key=len)
    cpp_req = [e for e in req if E.u[e] in big]
    plans['cpp'] = label_sessions(schedule(E, tour(E, nx.MultiGraph(Rq.subgraph(big)), cpp_req)))

    # RPP: cover every target, using any walkable way as a connector; one tour, cut into sessions and days.
    plans['rpp'] = label_sessions(schedule(E, tour(E, G, req)))

    plans['carp'], zones = carp(E, G, req)

    cmp = pd.DataFrame([metrics(n, R, E, extra.get(n, 0)) for n, R in plans.items()])
    cmp.to_csv(dest / 'compare.csv', index=False)
    print(cmp.to_string(index=False))
    assert (cmp[cmp.plan != 'cpp'].coverage_pct == 100).all(), 'a plan misses survey targets'

    gpkg = dest / 'routing.gpkg'
    gpkg.unlink(missing_ok=True)
    E.drop(columns=['name']).to_file(gpkg, layer='edges')
    zones.to_file(gpkg, layer='zones')
    for n, R in plans.items():
        R.to_file(gpkg, layer=f'plan_{n}')
    for n, R in plans.items():
        gpx(R, dest / 'gpx' / n)
    web_map(E, plans, zones, dest / 'map.html', AREAS[key]['name'])
    figure(E, plans, cmp, dest / 'plans.png')


def figure(E, plans, cmp, path):
    """The plans side by side, coloured by day; dotted = walked with the recording stopped."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 2, figsize=(16, 14))
    for ax, (n, R), c in zip(axs.flat, plans.items(), cmp.itertuples()):
        E[E.req].plot(ax=ax, color='#ddd', lw=.5)
        for d, g in R[R.status != 'transfer'].groupby('day'):
            g.plot(ax=ax, color=PALETTE[(d - 1) % len(PALETTE)], lw=1.1)
        R[R.status == 'transfer'].plot(ax=ax, color='k', lw=.7, ls=':')
        ax.set_title(f'{n.upper()}: {c.walked_km} km walked, {c.field_h} h, {c.days} days, {c.sessions} sessions, '
                     f'{c.street_changes_per_km} street changes per km', fontsize=10)
        ax.set_aspect('equal')
        ax.set_axis_off()
    fig.savefig(path, dpi=90, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'west_loop')
