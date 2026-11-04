"""Worked example for network/docs/ROUTING_WORKFLOW.md: route_methods.tour() on four West Loop blocks, in four stages.

Run from the repo root after routes.py:  .venv/bin/python network/scripts/routing_example.py
Writes network/docs/img/routing-example.png.
"""
import sys; sys.path.insert(0, 'network')  # noqa: E702
import numpy as np, networkx as nx, geopandas as gpd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import box
import route_methods as rm
from routes import ROOT, street_name
E, G = rm.build(ROOT / 'data/west_loop/plan')
B = gpd.GeoSeries([box(-87.6530, 41.8803, -87.6490, 41.8836)], crs=4326).to_crs(32616).iloc[0]
mid = E.geometry.interpolate(0.5, normalized=True)
req = list(E.index[E.req & mid.within(B)])
near = E.index[E.geometry.intersects(B.buffer(150))]
Gb = G.edge_subgraph([(E.u[e], E.v[e], e) for e in near]).copy()
walk = rm.tour(E, Gb, req)
M = nx.MultiGraph(); M.add_edges_from((E.u[e], E.v[e], e) for e in req)
xy = {}
for e in near:
    c = E.geometry[e].coords; xy[E.u[e]] = c[0]; xy[E.v[e]] = c[-1]
odd = [n for n, d in M.degree() if d % 2]
x0, y0, x1, y1 = B.buffer(25).bounds
fig, axs = plt.subplots(2, 2, figsize=(13, 12))
roads = E.loc[near][(E.kind[near] == 'road') & E.name[near].notna()]
def base(ax, title):
    roads.plot(ax=ax, color='#e4e4e4', lw=7, zorder=0)
    for nm, g in roads.groupby(roads.name.map(street_name)):
        u = g.union_all().intersection(B.buffer(-15))
        if u.is_empty: continue
        p = u.representative_point()
        x_, y_ = np.array(u.bounds[2:]) - np.array(u.bounds[:2])
        ax.text(p.x, p.y, nm, fontsize=9, color='#666', ha='center', va='center', rotation=90 if y_ > x_ else 0,
                zorder=6, bbox=dict(fc='white', ec='none', alpha=.7, pad=.5))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.set_axis_off(); ax.set_title(title, fontsize=11, loc='left')
r = E.loc[req]
ax = axs[0, 0]; base(ax, '1. OpenStreetMap: sidewalks (grey) and crosswalks (orange)')
r[r.kind == 'sidewalk'].plot(ax=ax, color='#555', lw=2); r[r.kind == 'crossing'].plot(ax=ax, color='#e8730c', lw=2.5)
ax = axs[0, 1]; base(ax, f'2. As a graph: {M.number_of_nodes()} nodes, {len(req)} edges; {len(odd)} odd nodes (red)')
r.plot(ax=ax, color='#555', lw=1.5)
ev = [n for n in M if n not in odd]
ax.scatter([xy[n][0] for n in ev], [xy[n][1] for n in ev], s=6, color='#555', zorder=3)
ax.scatter([xy[n][0] for n in odd], [xy[n][1] for n in odd], s=40, color='#d62728', zorder=4, edgecolor='white')
ax = axs[1, 0]
rep = [w for w in walk if not w[3]]
rep_m = E.m[[w[2] for w in rep]].sum()
base(ax, f'3. Pair the odd nodes; walk the purple stretches twice ({rep_m:.0f} m)')
r.plot(ax=ax, color='#bbb', lw=1.5)
ax.scatter([xy[n][0] for n in odd], [xy[n][1] for n in odd], s=40, color='#d62728', zorder=4, edgecolor='white')
E.loc[[w[2] for w in rep]].plot(ax=ax, color='#8250df', lw=4, alpha=.8, zorder=2)
ax = axs[1, 1]; base(ax, f'4. The Euler tour: every edge once, purple ones twice ({len(walk)} steps, start ▲)')
cm = plt.get_cmap('viridis')
for k, (u, v, e, f) in enumerate(walk):
    (a, b), (c, d) = xy[u], xy[v]
    col = cm(k / len(walk))
    ax.plot([a, c], [b, d], color=col, lw=2.2 if f else 4, alpha=1 if f else .55, solid_capstyle='round')
    if k % 12 == 6 and np.hypot(c - a, d - b) > 4:
        ax.annotate('', xy=(c, d), xytext=((a + c) / 2, (b + d) / 2), arrowprops=dict(arrowstyle='-|>', color=col, lw=1.5, mutation_scale=14))
s = xy[walk[0][0]]; ax.plot(*s, marker='^', ms=13, color=cm(0), mec='white', zorder=5)
sm = plt.cm.ScalarMappable(cmap=cm); sm.set_array([0, 1])
cb = fig.colorbar(sm, ax=ax, fraction=.04, pad=.01, ticks=[0, 1]); cb.ax.set_yticklabels(['start', 'end'])
fig.tight_layout()
fig.savefig(ROOT / 'docs/img/routing-example.png', dpi=85, bbox_inches='tight')
print('req', len(req), 'nodes', M.number_of_nodes(), 'odd', len(odd), 'pieces', nx.number_connected_components(M),
      'walk', len(walk), 'repeat m', round(rep_m), 'req m', round(E.m[req].sum()))
