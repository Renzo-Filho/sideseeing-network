"""The walking lines of a fit, and its baselines, against the reference of one street (S11; on Morgan, the phase 2 gate).

    python -m walk2net.evaluate.score --area west_loop --street morgan --fit data/west_loop/graph/phase2a --out OUT \
        [--reference FOLDER]

The reference (agreed 26 October), in the area's reference folder unless --reference names another: the city's curbs
as checked on the orthophoto (<street>_trace.geojson; a line marked changed is replaced by the one redrawn, and
unchecked lines count as matching), and the back of the sidewalk from the parcels (<street>_back.geojson). Both are read
across the street every metre in the ladder's frame: at each u, the road is the gap between two curbs, and each
sidewalk runs from its curb to the first property line beyond it.

The rails are named east (+1, right of the axis) and west (-1) in the fit's tables, as on a north-going street.
"""
import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from pyproj import Transformer
from shapely.ops import transform

from walk2net.config import Area
from walk2net.stages import ladder

SIDES = {1.0: 'east', -1.0: 'west'}


def in_frame(lines, frame):
    """GeoSeries of lines (projected) -> one MultiLineString in (u, v)."""
    to_uv = lambda x, y: frame.to_uv(np.atleast_1d(x), np.atleast_1d(y))
    return MultiLineString([transform(to_uv, line) for line in lines])


def profile(curbs, backs, us, reach=40.0, road=(8.0, 18.0), widest=8.0):
    """For each u: curb_e, curb_w (the road's edges) and back_e, back_w (the sidewalks' backs), NaN where the
    reference cannot say (a cross street, a gap, a sidewalk wider than `widest` m)."""
    rows = []
    for u in us:
        ray = LineString([(u, -reach), (u, reach)])
        hits = lambda lines: np.sort([p.y for p in getattr(ray.intersection(lines), 'geoms', [ray.intersection(lines)])
                                      if not p.is_empty and p.geom_type == 'Point'])
        c, b = hits(curbs), hits(backs)
        row = dict(u=u, curb_e=np.nan, curb_w=np.nan, back_e=np.nan, back_w=np.nan)
        gaps = [(w, e) for w, e in zip(c[:-1], c[1:]) if road[0] <= e - w <= road[1] and not ((b > w) & (b < e)).any()]
        if len(gaps) == 1:
            row['curb_w'], row['curb_e'] = gaps[0]
            east, west = b[b > row['curb_e']], b[b < row['curb_w']]
            if len(east) and east[0] - row['curb_e'] <= widest:
                row['back_e'] = east[0]
            if len(west) and row['curb_w'] - west[-1] <= widest:
                row['back_w'] = west[-1]
        rows.append(row)
    return pd.DataFrame(rows)


def datum_shift(lon, lat, area):
    """(east, north) metres from a point's coordinates in the reference's datum to the GPS's frame at the recordings'
    epoch (the area's [reference] datum, gps_frame and epoch). In West Loop the city's curbs, the county's parcels and
    the orthophoto are NAD83(2011), read as if they were WGS84 (pyproj's default treats the two as the same); phone GPS
    is WGS84, which is ITRF2014 at the recording date to within centimetres."""
    src = area.reference
    x, y, _, _ = Transformer.from_crs(src['datum'], src['gps_frame'], always_xy=True).transform(lon, lat, 0.0, src['epoch'])
    a, b = gpd.GeoSeries(gpd.points_from_xy([lon, x], [lat, y]), crs=4326).to_crs(area.crs)
    return b.x - a.x, b.y - a.y


def reference_lines(folder, street, area, frame):
    """The checked curbs and the parcel backs of `street`, moved into the GPS's datum, in the frame."""
    trace = gpd.read_file(folder / f'{street}_trace.geojson')
    kept = trace[((trace['kind'] == 'city_curb') & (trace['status'] != 'changed')) | (trace['kind'] == 'curb')]
    backs = gpd.read_file(folder / f'{street}_back.geojson')
    east, north = datum_shift(*kept.union_all().centroid.coords[0], area)
    move = lambda lines: lines.to_crs(area.crs).translate(east, north)
    return in_frame(move(kept.geometry), frame), in_frame(move(backs.geometry), frame), (east, north)


def at(prof, u):
    """Rows of the profile nearest to positions u."""
    return np.clip(np.round(np.asarray(u, dtype=float) - prof['u'].iloc[0]).astype(int), 0, len(prof) - 1)


def sidewalk(prof, u, side):
    """The reference on `side` at positions u (nearest metre): its curb, its back, and the road's middle."""
    i = at(prof, u)
    key = 'e' if side > 0 else 'w'
    pick = lambda column: prof[column].to_numpy()[i]
    return pick(f'curb_{key}'), pick(f'back_{key}'), (pick('curb_e') + pick('curb_w')) / 2


def score(v, curb, back, centre, side):
    """Where positions v, meant to be on `side`'s sidewalk, fall against it: the share inside it, the median distance
    to its middle, the median distance onto it from the curb (negative: in the road), the share in the road and the
    share past the road's middle (the street's other half)."""
    ok = ~np.isnan(v + curb + back + centre)
    v, curb, back, centre = v[ok], curb[ok], back[ok], centre[ok]
    if not len(v):
        return dict(n=0)
    onto = side * (v - curb)
    return dict(n=int(len(v)), inside=float(np.mean((onto >= 0) & (side * (back - v) >= 0))),
                to_middle_m=float(np.median(np.abs(v - (curb + back) / 2))), from_curb_m=float(np.median(onto)),
                in_road=float(np.mean(onto < 0)), other_half=float(np.mean(side * (v - centre) < 0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--area', required=True, help='an area config: network/areas/<area>.toml')
    parser.add_argument('--street', required=True, help="a street of the area's config")
    parser.add_argument('--reference', type=Path, help="default: the area's reference folder")
    parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reference-only', action='store_true', help='write the profile only, without the fit')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    area = Area.load(args.area)
    street = area.streets[args.street]
    frame = ladder.Frame(street.projected(area.crs))
    curbs, backs, shift = reference_lines(args.reference or area.reference_dir, street.key, area, frame)
    us = np.arange(np.floor(min(g.bounds[0] for g in curbs.geoms)), np.ceil(max(g.bounds[2] for g in curbs.geoms)))
    prof = profile(curbs, backs, us)
    prof.to_csv(args.out / 'reference_profile.csv', index=False)
    road = prof['curb_e'] - prof['curb_w']
    summary = dict(reference=dict(datum_shift_m=np.round(shift, 3).tolist(),
                                  metres=len(prof), with_road=int(road.notna().sum()),
                                  road_m=float(road.median()),
                                  **{f'{name}_sidewalk': dict(metres=int(w.notna().sum()),
                                                              width_m=np.nanpercentile(w, [10, 50, 90]).round(2).tolist())
                                     for name, w in (('east', prof['back_e'] - prof['curb_e']),
                                                     ('west', prof['curb_w'] - prof['back_w']))}))
    print(json.dumps(summary['reference']))
    if args.reference_only:
        return

    # Walking lines, read every metre where their side was walked
    lines = pd.read_csv(args.fit / 'walking_lines.csv')
    near_knot = lambda u: np.abs(lines['u'].to_numpy()[None, :] - u[:, None]).argmin(axis=1)
    summary['walking_lines'] = {}
    for side, name in SIDES.items():
        walked = lines[f'observed_{name}'].to_numpy()[near_knot(us)].astype(bool)
        curb, back, centre = sidewalk(prof, us, side)
        for method in METHODS_LINES:
            v = np.where(walked, np.interp(us, lines['u'], lines[f'{method}_{name}']), np.nan)
            summary['walking_lines'][f'{method}_{name}'] = score(v, curb, back, centre, side)

    # The two lines' errors, split: the shift they share (the street's centre, which without a map only GPS can place)
    # and their separation (which the crossings and steps measure)
    walked = np.ones(len(us), bool)
    for name in SIDES.values():
        walked &= lines[f'observed_{name}'].to_numpy()[near_knot(us)].astype(bool)
    middle = {side: (lambda c, b, _: (c + b) / 2)(*sidewalk(prof, us, side)) for side in SIDES}
    summary['centre_and_separation'] = {}
    for method in METHODS_LINES:
        east, west = (np.interp(us, lines['u'], lines[f'{method}_{name}']) for name in SIDES.values())
        ok = walked & np.isfinite(east + west + middle[1.0] + middle[-1.0])
        shift = ((east + west) - (middle[1.0] + middle[-1.0]))[ok] / 2
        apart = ((east - west) - (middle[1.0] - middle[-1.0]))[ok]
        summary['centre_and_separation'][method] = dict(
            n=int(ok.sum()), shift_median_m=float(np.median(shift)), shift_abs_median_m=float(np.median(np.abs(shift))),
            shift_abs_p90_m=float(np.percentile(np.abs(shift), 90)), separation_median_m=float(np.median(apart)),
            separation_abs_median_m=float(np.median(np.abs(apart))))

    # Tracks, fix by fix, on the side the crossings put each run
    tracks = pd.concat([pd.read_csv(path).assign(session=path.stem[len('track_'):])
                        for path in sorted(args.fit.glob('track_*.csv'))], ignore_index=True)
    summary['tracks'] = {}
    for method in METHODS_TRACKS:
        for side, name in SIDES.items():
            fixes = tracks[tracks['side'] == side]
            curb, back, centre = sidewalk(prof, fixes[f'{method}_u'], side)
            summary['tracks'][f'{method}_{name}'] = score(fixes[f'{method}_v'].to_numpy(), curb, back, centre, side)

    # Crossings: where the steps end against the far curb, and their length against the reference's
    crossings = pd.concat([pd.read_csv(path) for path in sorted(args.fit.glob('crossings_*.csv'))], ignore_index=True)
    far = -crossings['leaves'].to_numpy()
    i = at(prof, crossings['u'])
    curb_far = np.where(far > 0, prof['curb_e'].to_numpy()[i], prof['curb_w'].to_numpy()[i])
    road_at = prof['curb_e'].to_numpy()[i] - prof['curb_w'].to_numpy()[i]
    to_far_curb = far * (curb_far - crossings['v_start'].to_numpy())
    ok = ~np.isnan(curb_far)
    stats = lambda x: dict(median=float(np.median(x)), p25=float(np.percentile(x, 25)), p75=float(np.percentile(x, 75)))
    summary['crossings'] = dict(
        n=int(len(crossings)), with_reference=int(ok.sum()),
        past_far_curb_m=stats(far[ok] * (crossings['v_end'].to_numpy()[ok] - curb_far[ok])),
        by_steps_m=stats(crossings['by_steps_m'].to_numpy()[ok]),
        start_to_far_curb_m=stats(to_far_curb[ok]),
        by_steps_minus_reference_m=stats(crossings['by_steps_m'].to_numpy()[ok] - to_far_curb[ok]),
        road_m=stats(road_at[ok & ~np.isnan(road_at)]))

    # The phase 2 gate (plan section 8): inside the sidewalk and nearer its middle than the GPS + steps smoother
    scored = summary['walking_lines']
    summary['gate'] = {name: dict(ladder_inside=scored[f'ladder_{name}'].get('inside'),
                                  ladder_to_middle_m=scored[f'ladder_{name}'].get('to_middle_m'),
                                  pdr_to_middle_m=scored[f'pdr_{name}'].get('to_middle_m'))
                       for name in SIDES.values()}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ('walking_lines', 'crossings', 'gate')}, indent=1))
    plot(prof, lines, us, args.out / 'walking_lines.png', street.name)


METHODS_LINES = ('ladder', 'gps', 'median5', 'pdr')
METHODS_TRACKS = ('gps', 'median5', 'pdr', 'ladder', 'alone')


def plot(prof, lines, us, path, street_name):
    """Each side's sidewalk (curb to back) and the methods' walking lines, as distance from the curb along the street."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    colors = dict(ladder='#2563eb', pdr='#d97706', median5='#64748b', gps='#cbd5e1')
    for ax, (side, name) in zip(axes, SIDES.items()):
        key = name[0]
        curb = prof[f'curb_{key}'].to_numpy()
        ax.fill_between(prof['u'], 0, side * (prof[f'back_{key}'] - curb), color='#dcfce7', label='sidewalk (reference)')
        ax.axhline(0, color='#16a34a', lw=1, label='curb')
        walked = lines[f'observed_{name}'].to_numpy().astype(bool)
        for method in ('gps', 'median5', 'pdr', 'ladder'):
            v = np.interp(prof['u'], lines['u'], lines[f'{method}_{name}'])
            near = walked[np.abs(lines['u'].to_numpy()[None, :] - prof['u'].to_numpy()[:, None]).argmin(axis=1)]
            ax.plot(prof['u'], np.where(near, side * (v - curb), np.nan), color=colors[method], lw=1.6, label=method)
        ax.set_ylabel(f'{name} side: metres\nfrom the curb (+ onto\nthe sidewalk)')
        ax.set_ylim(-12, 10)
    axes[0].legend(ncol=6, fontsize=8, loc='upper left')
    axes[1].set_xlabel(f'metres along {street_name} from the start of its axis')
    fig.tight_layout()
    fig.savefig(path, dpi=130)


if __name__ == '__main__':
    main()
