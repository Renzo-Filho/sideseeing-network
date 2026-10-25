"""The walk cut into runs: straight stretches between the turns that are not 'small' (the plan's Run record).

The cut is the one sideseeing-tools uses for crossing candidates (analysis.turns.detect_crossing_candidates), so
each crossing candidate is exactly one run, of kind 'crossing'. A run's displacement and bearing come from the
smoothed GPS track, 1 s before the run starts and 2 s after it ends, while standing in the turns, as for the
crossing candidates. Below SHORT_M of displacement GPS error dominates, so the bearing is left out.

Crossings made straight on, over a cross street, have no turn, so the turn cut leaves them inside runs.
split_at_crosswalks cuts them out where the crosswalk mask lies just ahead of the walker (crosswalk_underfoot).
"""
import numpy as np
import pandas as pd
from sideseeing_tools.analysis.turns import MIN_SEGMENT_S
from sideseeing_tools.geolocation import calculate_haversine_distance

SHORT_M = 20.0
UNDERFOOT = (0.85, 0.35, 0.65)  # the ground just ahead: rows from 85% of the height, columns 35-65%
STRAIGHT_GAP_S = 2.0
RUN_COLUMNS = ['run', 'start_s', 'end_s', 'kind', 'crossing_side', 'turn_before', 'turn_after', 'moving_s',
               'distance_m', 'bearing_deg', 'lat0', 'lon0', 'lat1', 'lon1']


def bearing(lat0, lon0, lat1, lon1):
    """Initial bearing in degrees clockwise from north."""
    lat0, lon0, lat1, lon1 = map(np.radians, (lat0, lon0, lat1, lon1))
    x = np.sin(lon1 - lon0) * np.cos(lat1)
    y = np.cos(lat0) * np.sin(lat1) - np.sin(lat0) * np.cos(lat1) * np.cos(lon1 - lon0)
    return np.degrees(np.arctan2(x, y)) % 360


def _moving(runs, stops):
    still = [(np.minimum(stops['end_s'], end) - np.maximum(stops['start_s'], start)).clip(lower=0).sum()
             for start, end in zip(runs['start_s'], runs['end_s'])]
    return runs['end_s'] - runs['start_s'] - np.asarray(still, float)


def _place(runs, track):
    """Adds each run's GPS ends, displacement and bearing, and numbers the runs."""
    position = lambda t: [np.interp(t, track['t'], track[column]) for column in ('latitude', 'longitude')]
    runs['lat0'], runs['lon0'] = position(runs['start_s'] - 1)
    runs['lat1'], runs['lon1'] = position(runs['end_s'] + 2)
    ends = runs[['lat0', 'lon0', 'lat1', 'lon1']].to_numpy().T
    runs['distance_m'] = 1000 * np.array([calculate_haversine_distance(*row) for row in ends.T])
    runs['bearing_deg'] = np.where(runs['distance_m'] >= SHORT_M, bearing(*ends), np.nan)
    runs['run'] = runs.index
    return runs[RUN_COLUMNS]


def cut_runs(motion, track, duration_s):
    """Runs of one session from SideSeeingWorkspace.motion(route) and .gps(route), in time order (RUN_COLUMNS)."""
    turns, stops, crossings = motion['turns'], motion['stops'], motion['crossings']
    big = turns[turns['kind'] != 'small']
    runs = pd.DataFrame(dict(start_s=np.r_[0, big['end_s']], end_s=np.r_[big['start_s'], duration_s],
                             turn_before=['start', *big['kind']], turn_after=[*big['kind'], 'end']))
    runs = runs[runs['end_s'] - runs['start_s'] >= MIN_SEGMENT_S].reset_index(drop=True)
    runs['moving_s'] = _moving(runs, stops)
    side = dict(zip(crossings['start_s'].round(6), crossings['side']))
    runs['crossing_side'] = runs['start_s'].round(6).map(side)
    runs['kind'] = np.where(runs['crossing_side'].notna(), 'crossing', 'run')
    return _place(runs, track)


def crosswalk_underfoot(detections, load_mask, size, min_share=0.3, min_score=0.5):
    """Sorted t of the frames whose patch just ahead (UNDERFOOT) is at least min_share crosswalk. load_mask(frame)
    returns the frame's crosswalk mask (or None); frames whose crosswalk boxes miss the patch are not loaded.
    size: the frame's (width, height)."""
    width, height = size
    top, left, right = UNDERFOOT[0] * height, UNDERFOOT[1] * width, UNDERFOOT[2] * width
    boxes = detections[(detections['prompt'] == 'crosswalk') & (detections['score'] >= min_score)
                       & (detections['y1'] >= top) & (detections['x0'] <= right) & (detections['x1'] >= left)]
    times = []
    for frame, rows in boxes.groupby('frame'):
        mask = load_mask(frame)
        if mask is not None and mask[int(top):, int(left):int(right)].mean() >= min_share:
            times.append(rows['t'].iloc[0])
    return np.sort(np.asarray(times, float))


def split_at_crosswalks(runs, times, stops, track, min_frames=2):
    """runs with each stretch on a crosswalk inside a 'run' cut out as a run of kind 'crossing' and crossing_side
    'straight'. A stretch is at least min_frames of `times` (crosswalk_underfoot) less than STRAIGHT_GAP_S apart,
    widened by half a frame each side; leftovers under MIN_SEGMENT_S join the crossing. Cuts without a turn are
    marked 'none' in turn_before and turn_after."""
    pieces = []
    for run in runs.to_dict('records'):
        inside = times[(times >= run['start_s']) & (times <= run['end_s'])] if run['kind'] == 'run' else times[:0]
        groups = np.split(inside, np.flatnonzero(np.diff(inside) > STRAIGHT_GAP_S) + 1) if len(inside) else []
        start, before = run['start_s'], run['turn_before']
        for group in (g for g in groups if len(g) >= min_frames):
            a, b = max(group[0] - 0.5, start), min(group[-1] + 0.5, run['end_s'])
            if a - start < MIN_SEGMENT_S:
                a = start
            else:
                pieces.append({**run, 'start_s': start, 'end_s': a, 'turn_before': before, 'turn_after': 'none'})
                before = 'none'
            if run['end_s'] - b < MIN_SEGMENT_S:
                b = run['end_s']
            pieces.append({**run, 'start_s': a, 'end_s': b, 'kind': 'crossing', 'crossing_side': 'straight',
                           'turn_before': before, 'turn_after': run['turn_after'] if b == run['end_s'] else 'none'})
            start, before = b, 'none'
        if start < run['end_s']:
            pieces.append({**run, 'start_s': start, 'end_s': run['end_s'], 'turn_before': before})
    split = pd.DataFrame(pieces)
    split['moving_s'] = _moving(split, stops)
    return _place(split, track)


def axis_runs(runs, axis_deg, tolerance_deg=30.0, min_m=SHORT_M):
    """Runs (not crossings) along a street whose axis is axis_deg (either direction), with direction
    'forward' (towards axis_deg) or 'back'."""
    along = runs[(runs['kind'] == 'run') & (runs['distance_m'] >= min_m)].copy()
    offset = (along['bearing_deg'] - axis_deg + 180) % 360 - 180
    along['direction'] = np.where(offset.abs() <= tolerance_deg, 'forward',
                                  np.where(offset.abs() >= 180 - tolerance_deg, 'back', None))
    return along[along['direction'].notna()]
