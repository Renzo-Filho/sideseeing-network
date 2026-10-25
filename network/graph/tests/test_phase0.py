"""Checks for phase 0 on synthetic data. Run from network/: python -m pytest graph/tests"""
import numpy as np
import pandas as pd

from graph import contract, runs, side_cue, zones

LAT, LON = 41.88, -87.65
M_LAT = 1 / 111_320  # degrees per metre northwards


def _walk():
    """North 100 m (0-80 s), a quarter turn, east 15 m across a street (84-96 s), a quarter turn back, north."""
    turns = pd.DataFrame(dict(start_s=[80, 96, 120], end_s=[84, 100, 121], net_deg=[-90, 90, 10],
                              total_deg=[90, 90, 10], kind=['quarter turn', 'quarter turn', 'small'],
                              direction=['right', 'left', 'left']))
    stops = pd.DataFrame(dict(start_s=[40.0], end_s=[50.0], duration_s=[10.0]))
    crossings = pd.DataFrame(dict(start_s=[84.0], end_s=[96.0], side=['right'], relative_deg=[-90.0],
                                  moving_s=[12.0], turn_before=['quarter turn']))
    t = np.arange(0, 181.0)
    north = np.interp(t, [0, 82, 98, 180], [0, 100, 100, 200])
    east = np.interp(t, [0, 82, 98, 180], [0, 0, 15, 15])
    track = pd.DataFrame(dict(t=t, latitude=LAT + north * M_LAT, longitude=LON + east * M_LAT / np.cos(np.radians(LAT))))
    return dict(turns=turns, stops=stops, crossings=crossings), track


def test_runs_cut_at_big_turns_and_type_the_crossing():
    motion, track = _walk()
    cut = runs.cut_runs(motion, track, 180)
    assert list(cut['kind']) == ['run', 'crossing', 'run']
    assert cut.loc[0, 'moving_s'] == 70  # 80 s minus the 10 s stop
    assert abs(cut.loc[0, 'bearing_deg'] - 0) < 2
    assert abs(cut.loc[1, 'distance_m'] - 14) < 1 and np.isnan(cut.loc[1, 'bearing_deg'])  # too short for GPS
    along = runs.axis_runs(cut, 0.0)
    assert list(along['run']) == [0, 2] and set(along['direction']) == {'forward'}


def test_side_cue_counts_boxes_left_and_right():
    motion, track = _walk()
    cut = runs.cut_runs(motion, track, 180)
    t = np.arange(0, 80.0)
    detections = pd.DataFrame(dict(prompt='car', t=t, score=0.9, x0=100.0, x1=500.0))  # left of 1920 / 2
    cued = side_cue.road_side(cut, detections, frame_width=1920)
    assert list(cued['road_side']) == ['left', 'abstain', 'abstain']
    assert side_cue.score_against_protocol(cued.iloc[:1], 0.0)['agrees'] == 1
    assert side_cue.score_against_protocol(cued.iloc[:1], 90.0)['disagrees'] == 1


def test_zones_measure_the_gap_between_curb_and_sidewalk():
    sidewalk = np.zeros((100, 200), bool)
    sidewalk[50:, 80:180] = True  # the walked sidewalk, its road-side edge at column 80
    curb = np.zeros_like(sidewalk)
    curb[50:, 58:60] = True  # 21 columns of parkway between curb and sidewalk
    pole = np.zeros_like(sidewalk)
    pole[30:90, 68:71] = True  # standing in the parkway
    tree = np.zeros_like(sidewalk)
    tree[20:95, 85:90] = True  # on the paving, hiding it: it must not open a gap
    sidewalk[:, 85:90] = False
    masks = dict(sidewalk=sidewalk, curb=curb, pole=pole, tree=tree)
    measure = zones.frame_zones(masks, 'left')
    assert measure['gap_px'] == 21 and measure['sidewalk_px'] == 99
    assert measure['furniture'] == 'tree, pole' and abs(measure['furniture_share'] - (10 + 28) / 2 / 120) < 0.01  # pole 10, tree 28 px from the curb
    mirrored = zones.frame_zones({k: v[:, ::-1] for k, v in masks.items()}, 'right')
    assert mirrored['gap_px'] == 21 and mirrored['furniture'] == 'tree, pole'


def test_three_knocks_and_gps_lag():
    t = np.arange(0, 60, 0.02)
    signal = np.random.default_rng(0).normal(0, 0.01, len(t))
    for knock in (31.0, 31.6, 32.3):
        signal[np.argmin(abs(t - knock))] = 5
    assert np.allclose(contract._three_knocks(t, np.abs(signal)), [31.0, 31.6, 32.3], atol=0.02)

    times = np.arange(0, 300, 0.02)
    rate = 30 * np.sin(2 * np.pi * times / 40)  # weaving left and right, deg/s, + = left
    heading = np.radians(-np.cumsum(rate) * 0.02)  # clockwise compass heading
    north, east = np.cumsum(1.4 * np.cos(heading)) * 0.02, np.cumsum(1.4 * np.sin(heading)) * 0.02
    fix_t = np.arange(0, 300, 1.0)
    late = 2.0  # each fix shows where the walker was 2 s earlier
    north, east = np.interp(fix_t - late, times, north), np.interp(fix_t - late, times, east)
    fixes = pd.DataFrame(dict(t=fix_t, latitude=LAT + north * M_LAT,
                              longitude=LON + east * M_LAT / np.cos(np.radians(LAT))))
    found = contract.gps_lag(fixes, times, rate)
    assert abs(found['gps_late_s'] - late) <= 0.6 and found['gps_corr'] > 0.9


def test_straight_crossings_are_cut_out_of_runs():
    motion, track = _walk()
    cut = runs.cut_runs(motion, track, 180)
    on_crosswalk = np.arange(140.0, 150.0)  # crossing a cross street in the last run, straight on
    split = runs.split_at_crosswalks(cut, np.r_[30.0, on_crosswalk], motion['stops'], track)  # 30: one frame only
    assert list(split['kind']) == ['run', 'crossing', 'run', 'crossing', 'run']
    assert list(split['crossing_side'].fillna('')) == ['', 'right', '', 'straight', '']
    assert split.loc[3, ['start_s', 'end_s']].tolist() == [139.5, 149.5]
    assert split.loc[2, 'turn_after'] == 'none' and split.loc[4, 'turn_after'] == 'end'


def test_crosswalk_underfoot_reads_masks_only_where_boxes_reach_the_patch():
    mask = np.zeros((100, 200), bool)
    mask[80:, 60:140] = True  # the crosswalk just ahead
    detections = pd.DataFrame(dict(prompt='crosswalk', frame=['a', 'b'], t=[1.0, 2.0], score=0.9,
                                   x0=[60.0, 0.0], y0=[80.0, 10.0], x1=[140.0, 50.0], y1=[100.0, 40.0]))
    loaded = []
    found = runs.crosswalk_underfoot(detections, lambda frame: loaded.append(frame) or mask, (200, 100))
    assert list(found) == [1.0] and loaded == ['a']  # frame b's crosswalk is far ahead: never loaded


def test_sensor_clock_moves_motion_onto_the_video():
    windows = pd.DataFrame(dict(centre_s=[0.0, 3600.0], video_late_s=[-0.3, -0.5], corr=0.99, focal_px=1460.0,
                                pts_minus_index_s=0.0))
    clock = contract.sensor_clock(contract.summarize_rotation(windows))
    assert np.allclose(clock(np.array([0.0, 1800.0])), [-0.3, 1800 - 0.4])


def test_reference_keeps_the_curbs_along_the_street():
    import geopandas as gpd
    from shapely.geometry import LineString
    from graph import reference
    axis = LineString([(0, 0), (0, 100)])
    curbs = gpd.GeoSeries([LineString([(6, 0), (6, 100)]),       # along it
                           LineString([(6, 95), (60, 95)]),       # around the corner, mostly along the cross street
                           LineString([(40, 0), (40, 100)])])     # the next street
    kept = reference.along(gpd.GeoDataFrame(geometry=curbs), axis)
    assert list(kept.index) == [0]
