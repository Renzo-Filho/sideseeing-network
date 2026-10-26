"""Checks for phase 2a on a simulated street. Run from network/: python -m pytest graph/tests"""
import numpy as np
import pandas as pd
from shapely.geometry import LineString

from graph import baselines, ladder, reference, steps

SPEED, STEP, PULL = 1.3, 0.75, 3.5   # m/s, m per step, the GPS's pull towards the street's middle (m)
EAST, WEST, CURB = 8.0, -8.0, 6.0    # walking lines and curbs (|v|, metres)
NORTH = ladder.Frame(LineString([(0, 0), (0, 300)]))


def _session(points, kinds, turns_deg, bearings, seed):
    """A walk through `points` (u, v): run i goes from points[i] to points[i + 1] at SPEED, then the walker turns for
    3 s by turns_deg[i]. GPS fixes come every 0.55 s, a second late, pulled towards v = 0 on the sidewalks."""
    rows, t = [], 0.0
    for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
        length = np.hypot(b[0] - a[0], b[1] - a[1])
        rows.append(dict(start_s=t, end_s=t + length / SPEED, kind=kinds[i], a=a, b=b, distance_m=length,
                         bearing_deg=bearings[i], crossing_side='left' if kinds[i] == 'crossing' else None,
                         turn_deg=turns_deg[i - 1] if i else 0.0))
        t += length / SPEED + 3
    runs = pd.DataFrame(rows)
    turns = pd.DataFrame(dict(start_s=runs.end_s[:-1].to_numpy(), end_s=runs.start_s[1:].to_numpy(), net_deg=turns_deg))

    def where(time):
        for r in rows:
            if time <= r['end_s'] + 3:
                share = np.clip((time - r['start_s']) / (r['end_s'] - r['start_s']), 0, 1)
                return np.array(r['a']) + share * (np.array(r['b']) - np.array(r['a'])), r['kind'] == 'run'
        return np.array(rows[-1]['b']), True

    rng = np.random.default_rng(seed)
    fix_t = np.arange(1.0, t, 0.55)
    true, on_sidewalk = zip(*(where(x - 1.0) for x in fix_t))
    true = np.array(true)
    pull = np.where(on_sidewalk, -np.sign(true[:, 1]) * PULL, 0.0)
    fixes = pd.DataFrame(dict(t=fix_t, u=true[:, 0] + rng.normal(0, 2, len(fix_t)),
                              v=true[:, 1] + pull + rng.normal(0, 2, len(fix_t))))
    walked = np.concatenate([np.arange(r['start_s'], r['end_s'], STEP / SPEED) for r in rows])
    return runs, walked, fixes, turns


def _north_on_east(seed=1):
    """North on the east line, across to the west curb and straight back at u = 100, north again."""
    points = [(0, EAST), (100, EAST), (100, -CURB), (100, EAST), (200, EAST)]
    return _session(points, ['run', 'crossing', 'crossing', 'run'], [90.0, 180.0, 90.0], [0.0, 270.0, 90.0, 0.0], seed)


def _south_on_west(seed=2):
    """South on the west line, across to the east curb and straight back at u = 100, south again."""
    points = [(200, WEST), (100, WEST), (100, CURB), (100, WEST), (0, WEST)]
    return _session(points, ['run', 'crossing', 'crossing', 'run'], [90.0, 180.0, 90.0], [180.0, 90.0, 270.0, 180.0], seed)


def _ladder(session):
    runs, walked, fixes, turns = session
    return ladder.Ladder(ladder.assign_rails(ladder.headings(runs, NORTH, turns)), walked, fixes)


def test_the_crossings_alone_put_each_run_on_its_sidewalk():
    runs, _, _, turns = _north_on_east()
    placed = ladder.assign_rails(ladder.headings(runs, NORTH, turns))
    assert list(placed['quarter']) == [0, 1, 3, 0]
    assert list(placed['across']) == [False, True, True, False]
    assert list(placed['rail'].fillna(0)) == [1, 0, 0, 1]  # both runs on the east (+v) side
    assert not placed['conflict'].any()


def test_one_session_finds_its_walking_line_and_the_far_curb():
    model = _ladder(_north_on_east())
    knots, rails, (p,), result, observed = ladder.fit([model])
    assert result.success
    # Alone, the line's sideways position rests on the few fixes taken while crossing: pull and line trade off.
    assert abs(p['step_m'] - STEP) < 0.03 and abs(p['pull_m'] - PULL) < 1.5
    assert abs(np.interp(100, knots, rails[1.0]) - EAST) < 1.5
    assert observed[1.0].all() and not observed[-1.0].any()  # the west line was never walked
    ends = model.crossings(p)['v_end'].to_numpy()
    assert abs(ends[0] + CURB) < 1.0  # the first crossing ends at the west curb


def test_two_sessions_find_both_walking_lines():
    knots, rails, ps, result, observed = ladder.fit([_ladder(_north_on_east()), _ladder(_south_on_west())])
    assert result.success
    assert abs(np.interp(100, knots, rails[1.0]) - EAST) < 1.0 and abs(np.interp(100, knots, rails[-1.0]) - WEST) < 1.0


def test_lines_across_the_street_are_not_curbs():
    import geopandas as gpd
    axis = LineString([(0, 0), (0, 300)])
    lines = gpd.GeoSeries([LineString([(-7, 50), (7, 51)]),                          # across, like a bridge edge
                           LineString([(7, 52), (9.5, 52)]),                          # a stub at the bridge's side
                           LineString([(7, 0), (7, 100)]),                            # along: a curb
                           LineString([(7, 100), (8, 105), (12, 107), (20, 108)]),    # a corner curve
                           LineString([(11, 120), (20, 120)])])                       # a cross street's curb
    assert list(reference.across(gpd.GeoDataFrame(geometry=lines), axis)) == [True, True, False, False, False]


def test_the_reference_is_read_across_the_street():
    from shapely.geometry import MultiLineString
    from graph import evaluate
    curbs = MultiLineString([[(0, -7), (40, -7)], [(60, -7), (100, -7)], [(0, 7), (40, 7)], [(60, 7), (100, 7)]])
    backs = MultiLineString([[(0, -10), (100, -10)], [(0, 10.5), (100, 10.5)]])
    prof = evaluate.profile(curbs, backs, np.arange(0.0, 100.0))
    assert list(prof.loc[20, ['curb_w', 'curb_e', 'back_w', 'back_e']]) == [-7, 7, -10, 10.5]
    assert prof.loc[50, ['curb_w', 'curb_e']].isna().all()  # a cross street: no road edges to read
    curb, back, centre = evaluate.sidewalk(prof, [20, 30, 50], 1.0)
    scored = evaluate.score(np.array([8.75, 5.0, 9.0]), curb, back, centre, 1.0)
    assert scored['n'] == 2 and scored['inside'] == 0.5 and scored['in_road'] == 0.5


def test_the_reference_moves_into_the_gps_datum():
    from graph import evaluate
    east, north = evaluate.datum_shift(-87.652, 41.883)  # Morgan, October 2026
    assert -1.1 < east < -0.9 and 0.8 < north < 1.0


def test_steps_are_peaks_of_the_shaking():
    rate = 50
    t = np.arange(0, 20, 1 / rate)
    walking = (t > 5) & (t < 15)
    xyz = np.column_stack([np.zeros_like(t), np.zeros_like(t), 9.81 + walking * 3 * np.sin(2 * np.pi * 1.8 * t)])
    found = steps.step_times(t, xyz, pd.DataFrame(dict(start_s=[0.0], end_s=[5.0])))
    assert abs(len(found) - 18) <= 1  # 1.8 steps a second for 10 s


def test_the_steps_smoother_beats_raw_gps():
    t = np.arange(0, 120, 0.55)
    true_u = SPEED * t
    rng = np.random.default_rng(2)
    u, v = true_u + rng.normal(0, 3, len(t)), rng.normal(0, 3, len(t))
    step_times = np.arange(0, 120, STEP / SPEED)
    su, sv = baselines.pdr_smoother(t, u, v, step_times, lambda times: np.zeros_like(times), STEP)
    assert np.hypot(su - true_u, sv).mean() < np.hypot(u - true_u, v).mean() / 2
