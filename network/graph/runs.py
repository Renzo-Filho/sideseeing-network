"""The walk cut into runs: straight stretches between the turns that are not 'small' (the plan's Run record).

The cut is the one sideseeing-tools uses for crossing candidates (analysis.turns.detect_crossing_candidates), so
each crossing candidate is exactly one run, of kind 'crossing'. A run's displacement and bearing come from the
smoothed GPS track, 1 s before the run starts and 2 s after it ends, while standing in the turns, as for the
crossing candidates. Below SHORT_M of displacement GPS error dominates, so the bearing is left out.
"""
import numpy as np
import pandas as pd
from sideseeing_tools.analysis.turns import MIN_SEGMENT_S
from sideseeing_tools.geolocation import calculate_haversine_distance

SHORT_M = 20.0
RUN_COLUMNS = ['run', 'start_s', 'end_s', 'kind', 'crossing_side', 'turn_before', 'turn_after', 'moving_s',
               'distance_m', 'bearing_deg', 'lat0', 'lon0', 'lat1', 'lon1']


def bearing(lat0, lon0, lat1, lon1):
    """Initial bearing in degrees clockwise from north."""
    lat0, lon0, lat1, lon1 = map(np.radians, (lat0, lon0, lat1, lon1))
    x = np.sin(lon1 - lon0) * np.cos(lat1)
    y = np.cos(lat0) * np.sin(lat1) - np.sin(lat0) * np.cos(lat1) * np.cos(lon1 - lon0)
    return np.degrees(np.arctan2(x, y)) % 360


def cut_runs(motion, track, duration_s):
    """Runs of one session from SideSeeingWorkspace.motion(route) and .gps(route), in time order (RUN_COLUMNS)."""
    turns, stops, crossings = motion['turns'], motion['stops'], motion['crossings']
    big = turns[turns['kind'] != 'small']
    runs = pd.DataFrame(dict(start_s=np.r_[0, big['end_s']], end_s=np.r_[big['start_s'], duration_s],
                             turn_before=['start', *big['kind']], turn_after=[*big['kind'], 'end']))
    runs = runs[runs['end_s'] - runs['start_s'] >= MIN_SEGMENT_S].reset_index(drop=True)

    still = [(np.minimum(stops['end_s'], end) - np.maximum(stops['start_s'], start)).clip(lower=0).sum()
             for start, end in zip(runs['start_s'], runs['end_s'])]
    runs['moving_s'] = runs['end_s'] - runs['start_s'] - np.asarray(still, float)

    side = dict(zip(crossings['start_s'].round(6), crossings['side']))
    runs['crossing_side'] = runs['start_s'].round(6).map(side)
    runs['kind'] = np.where(runs['crossing_side'].notna(), 'crossing', 'run')

    position = lambda t: [np.interp(t, track['t'], track[column]) for column in ('latitude', 'longitude')]
    runs['lat0'], runs['lon0'] = position(runs['start_s'] - 1)
    runs['lat1'], runs['lon1'] = position(runs['end_s'] + 2)
    ends = runs[['lat0', 'lon0', 'lat1', 'lon1']].to_numpy().T
    runs['distance_m'] = 1000 * np.array([calculate_haversine_distance(*row) for row in ends.T])
    runs['bearing_deg'] = np.where(runs['distance_m'] >= SHORT_M, bearing(*ends), np.nan)
    runs['run'] = runs.index
    return runs[RUN_COLUMNS]


def axis_runs(runs, axis_deg, tolerance_deg=30.0, min_m=SHORT_M):
    """Runs (not crossings) along a street whose axis is axis_deg (either direction), with direction
    'forward' (towards axis_deg) or 'back'."""
    along = runs[(runs['kind'] == 'run') & (runs['distance_m'] >= min_m)].copy()
    offset = (along['bearing_deg'] - axis_deg + 180) % 360 - 180
    along['direction'] = np.where(offset.abs() <= tolerance_deg, 'forward',
                                  np.where(offset.abs() >= 180 - tolerance_deg, 'back', None))
    return along[along['direction'].notna()]
