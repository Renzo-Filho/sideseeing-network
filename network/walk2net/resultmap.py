"""A map of a street's walking lines over the orthophoto: the reference, the GPS, each fit's walking lines, the last
fit's track and crossings, and the curb where the video puts it. One self-contained page, for looking only.

    python -m walk2net.resultmap --area west_loop --street morgan --fits data/west_loop/graph/phase2a \
        data/west_loop/graph/phase2a_far data/west_loop/graph/phase2b --out data/west_loop/graph/map.html \
        [--reference FOLDER]

The reference is drawn as stored (NAD83, the orthophoto's datum); everything from the phones is moved from the GPS's
datum into it (score.datum_shift). The parcel lines stay local: the page is not to be shared.
"""
import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint

from walk2net.config import Area
from walk2net.evaluate import score
from walk2net.stages import ladder

FIT_COLOURS = ('#a855f7', '#f59e0b', '#10b981', '#2563eb')  # in the order of --fits; the last (best) is blue
COLOURS = {'gps': '#e5e7eb',
           'track': '#60a5fa', 'video_curb': '#ef4444', 'crossing': '#22d3ee', 'curb': '#22c55e', 'back': '#f472b6'}


def to_lonlat(frame, u, v, shift, crs):
    """(u, v) in the street frame (GPS datum, projected in `crs`) to lon/lat in the reference's datum."""
    x, y = frame.to_xy(np.asarray(u, float), np.asarray(v, float))
    points = gpd.GeoSeries(gpd.points_from_xy(x - shift[0], y - shift[1]), crs=crs).to_crs(4326)
    return np.column_stack([points.x, points.y])


def runs_of(mask):
    """(start, stop) of the stretches where mask is True."""
    edges = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
    return list(zip(edges[::2], edges[1::2]))


def layer(name, geometries, style, kind='line'):
    return dict(name=name, kind=kind, style=style,
                data=json.loads(gpd.GeoSeries(geometries, crs=4326).to_json()) if len(geometries) else None)


def build(area, street, reference_dir, fits, out):
    frame = ladder.Frame(street.projected(area.crs))
    to_ll = lambda u, v: to_lonlat(frame, u, v, shift, area.crs)
    trace = gpd.read_file(reference_dir / f'{street.key}_trace.geojson')
    curbs = trace[((trace['kind'] == 'city_curb') & (trace['status'] != 'changed')) | (trace['kind'] == 'curb')]
    backs = gpd.read_file(reference_dir / f'{street.key}_back.geojson')
    shift = score.datum_shift(*curbs.union_all().centroid.coords[0], area)
    layers = [layer('Reference curbs (city 2010, checked; redrawn)', list(curbs.geometry), dict(color=COLOURS['curb'], weight=2)),
              layer('Reference back of sidewalk (parcels)', list(backs.geometry), dict(color=COLOURS['back'], weight=2))]

    last = fits[-1]
    tracks = sorted(last.glob('track_*.csv'))
    gps = pd.concat([pd.read_csv(path) for path in tracks])
    layers.append(layer('GPS fixes (both sessions)', [MultiPoint(to_ll(gps['gps_u'], gps['gps_v']))],
                        dict(color=COLOURS['gps'], radius=1.5), kind='points'))

    for n, fit in enumerate(fits):
        lines = pd.read_csv(fit / 'walking_lines.csv')
        drawn = []
        for side, key in ((1.0, 'east'), (-1.0, 'west')):
            for a, b in runs_of(lines[f'observed_{key}'].to_numpy(bool)):
                if b - a >= 2:
                    drawn.append(LineString(to_ll(lines['u'][a:b], lines[f'ladder_{key}'][a:b])))
        layers.append(layer(f'Walking lines: {fit.name}', drawn, dict(color=FIT_COLOURS[n - len(fits)], weight=3)))

    lines = pd.read_csv(last / 'walking_lines.csv')
    track = [LineString(to_ll(t['ladder_u'], t['ladder_v'])) for t in map(pd.read_csv, tracks)]
    layers.append(layer(f'Corrected track: {last.name}', track, dict(color=COLOURS['track'], weight=1, opacity=0.6)))
    crossings = pd.concat([pd.read_csv(path) for path in sorted(last.glob('crossings_*.csv'))])
    layers.append(layer(f'Crossings by steps: {last.name}',
                        [LineString(to_ll([c.u, c.u], [c.v_start, c.v_end])) for c in crossings.itertuples()],
                        dict(color=COLOURS['crossing'], weight=2)))
    offsets = last / 'offsets.csv'
    if offsets.exists():
        seen = pd.read_csv(offsets)
        rail = {s: np.interp(seen['u'], lines['u'], lines[f'ladder_{k}']) for s, k in ((1.0, 'east'), (-1.0, 'west'))}
        v = np.where(seen['side'] > 0, rail[1.0], rail[-1.0]) - seen['side'] * seen['distance_m']
        layers.append(layer('Curb where the video puts it (walking line minus measured distance)',
                            [MultiPoint(to_ll(seen['u'], v))],
                            dict(color=COLOURS['video_curb'], radius=2), kind='points'))

    page = (Path(__file__).with_name('resultmap.html').read_text()
            .replace('/*LAYERS*/null', json.dumps(layers)))
    out.write_text(page)
    print(f'[resultmap] {len(layers)} layers -> {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--area', required=True, help='an area config: network/areas/<area>.toml')
    parser.add_argument('--street', required=True, help="a street of the area's config")
    parser.add_argument('--reference', type=Path, help="default: the area's reference folder")
    parser.add_argument('--fits', type=Path, nargs='+', required=True, help='fit folders, the last one in full')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    area = Area.load(args.area)
    build(area, area.streets[args.street], args.reference or area.reference_dir, args.fits, args.out)


if __name__ == '__main__':
    main()
