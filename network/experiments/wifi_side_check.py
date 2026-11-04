"""Exploratory: does Wi-Fi tell the two sidewalks of a north-south street apart? (docs/METHOD.md, section 11)
Run from network/:  python -m experiments.wifi_side_check RAW_SESSION [RAW_SESSION ...]
Side comes from the West Loop protocol rule (northbound = east sidewalk, southbound = west) on GPS stretches heading
north or south. For each access point seen from both sides in the same stretch, the mean signal difference east - west,
minus the stretch's median difference (removes a session or phone offset), compared with side labels shuffled within
each stretch. A real side signal makes the observed differences larger than every shuffle.
"""
import re
import sys

import numpy as np
import pandas as pd
from pyproj import Transformer

TO_UTM = Transformer.from_crs(4326, 32616, always_xy=True)
SCAN = re.compile(r'BSSID: ([0-9a-f:]+).*?level: (-?\d+).*?timestamp: (\d+)')


def load(session):
    """One row per access point per real scan, with the walker's position and side at that moment."""
    one = pd.read_csv(f'{session}/sensors.one.csv', usecols=['timestamp_nano', 'datetime_utc'], nrows=2000)
    boot_to_utc = int((pd.to_datetime(one.datetime_utc).astype('int64') - one.timestamp_nano).median())
    rows = []
    with open(f'{session}/wifi.csv') as f:
        next(f)
        for line in f:   # fields contain commas, so parse the scan text directly
            m = SCAN.search(line)
            if m:   # the scan's own timestamp (microseconds since boot), not the logging second
                rows.append((m.group(1), int(m.group(2)), int(m.group(3)) * 1000 + boot_to_utc))
    w = pd.DataFrame(rows, columns=['ap', 'rssi', 't']).drop_duplicates(['ap', 't'])
    g = pd.read_csv(f'{session}/gps.csv')
    g['t'] = pd.to_datetime(g.datetime_utc).astype('int64')
    x, y = TO_UTM.transform(g.longitude.values, g.latitude.values)
    g['x'] = pd.Series(x).rolling(5, center=True, min_periods=1).median()
    g['y'] = pd.Series(y).rolling(5, center=True, min_periods=1).median()
    dx, dy = g.x.diff(10).shift(-5), g.y.diff(10).shift(-5)        # displacement over about 7 s
    g = g[(dy.abs() > 8) & (dx.abs() < 0.35 * dy.abs())].copy()     # walking along a north-south street
    g['side'] = np.where(dy[g.index] > 0, 'E', 'W')
    w = pd.merge_asof(w.sort_values('t'), g[['t', 'x', 'y', 'side']].sort_values('t'), on='t',
                      tolerance=2_000_000_000, direction='nearest').dropna()
    w['street'] = (w.x // 60).astype(int)                            # West Loop streets are about 200 m apart
    return w


def side_difference(w, stretch_m):
    m = (w.assign(stretch=(w.y // stretch_m).astype(int))
         .groupby(['street', 'stretch', 'ap', 'side']).rssi.mean().unstack('side').dropna(subset=['E', 'W']))
    d = m.E - m.W
    return d - d.groupby(level=['street', 'stretch']).transform('median')


def main(sessions, stretch_m=25, shuffles=200):
    rng = np.random.default_rng(1)
    w = pd.concat([load(s) for s in sessions])
    d = side_difference(w, stretch_m)
    key = [w.street, (w.y // stretch_m).astype(int)]
    null = [side_difference(w.assign(side=w.groupby(key).side.transform(lambda v: rng.permutation(v.values))),
                            stretch_m).abs().median() for _ in range(shuffles)]
    print(f'{stretch_m} m stretches: {len(d)} access-point/stretch pairs seen from both sides')
    print(f'  median |east - west| {d.abs().median():.1f} dB; shuffled {np.median(null):.1f} dB '
          f'(max of {shuffles}: {np.max(null):.1f}); share >= 10 dB: {(d.abs() >= 10).mean():.0%}')


def demo():
    """The offset removal: a session-wide offset alone leaves no side signal."""
    idx = pd.MultiIndex.from_tuples([(0, 0, 'a', 'E'), (0, 0, 'a', 'W'), (0, 0, 'b', 'E'), (0, 0, 'b', 'W')],
                                    names=['street', 'stretch', 'ap', 'side'])
    w = pd.DataFrame({'rssi': [-60, -66, -70, -76]}, index=idx).reset_index().assign(y=0.0)
    assert side_difference(w, 25).abs().max() == 0   # both APs 6 dB stronger on E: an offset, not a side signal


if __name__ == '__main__':
    demo()
    main(sys.argv[1:])
