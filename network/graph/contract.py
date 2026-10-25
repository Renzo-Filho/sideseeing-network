"""The data contract (plan phase 0): what each session holds, and how well its clocks agree.

session_summary reads metadata.json and gps.csv. The clock measures need the raw recording, and each returns how
clear its evidence was, so the alignment bound is measured, not assumed:

- sync_taps: the three knocks on the vest mount after the still start (PILOT2_PROTOCOL.md), as accelerometer jerk
  spikes and as audio transients. They count only when both show three knocks with the same spacing.
- rotation_lag: during the largest turns, the camera's rotation seen as the image sliding sideways between frames
  (phase correlation), against the gyroscope's rate about gravity. The best lag says how late the video is against
  the sensors, and the slope of pixels per degree gives the lens's horizontal focal length (rough: stabilisation and
  walking translation add to the slide).
- gps_lag: the rate of change of the raw GPS course against the same gyroscope rate; how late the fixes are.
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import median_abs_deviation

from graph.runs import bearing

TAP_WINDOW_S = 120.0
TAP_SPAN_S = 3.0
NEAR_MODULE_M = 15.0


def read_fixes(gps_csv, start):
    """Raw GPS fixes with t (seconds from `start`, the video start)."""
    fixes = pd.read_csv(gps_csv)
    fixes['t'] = (pd.to_datetime(fixes['datetime_utc'], utc=True) - pd.Timestamp(start)).dt.total_seconds()
    return fixes


def media_start(metadata):
    return pd.Timestamp(metadata['time']['mediaStartDateTime'])


def session_summary(session_dir, pieces=None):
    """One session's device, timing and GPS quality; with `pieces` (the planned route pieces, a projected
    GeoDataFrame with 'module' and 'kind'), the planned modules most of its fixes lie near."""
    metadata = json.loads((Path(session_dir) / 'metadata.json').read_text())
    start, stop = media_start(metadata), pd.Timestamp(metadata['time']['mediaStopDateTime'])
    fixes = read_fixes(Path(session_dir) / 'gps.csv', start)
    fixes = fixes[(fixes['t'] >= 0) & (fixes['t'] <= (stop - start).total_seconds())]
    device = metadata.get('device', {})
    summary = dict(
        session=Path(session_dir).name, device=f"{device.get('manufacturer', '')} {device.get('model', '')}".strip(),
        android=device.get('androidVersion'), start_utc=start.isoformat(), minutes=(stop - start).total_seconds() / 60,
        camera=metadata.get('preferences', {}).get('camera'), fixes=len(fixes),
        fix_interval_s=fixes['t'].diff().median(), accuracy_m=fixes['accuracy'].median(),
        accuracy_over_10m=(fixes['accuracy'] > 10).mean())
    if pieces is not None and len(fixes):
        import geopandas as gpd
        points = gpd.GeoSeries(gpd.points_from_xy(fixes['longitude'], fixes['latitude']), crs=4326).to_crs(pieces.crs)
        sidewalks = pieces[pieces['kind'] == 'sidewalk'].dissolve('module')
        near = {module: (points.distance(geometry) <= NEAR_MODULE_M).mean()
                for module, geometry in sidewalks.geometry.items()}
        summary['modules'] = ', '.join(f'{m} {share:.0%}' for m, share in
                                       sorted(near.items(), key=lambda item: -item[1])[:3] if share >= 0.1)
    return summary


def _three_knocks(times, signal, span_s=TAP_SPAN_S):
    """Times of the first three peaks within span_s of each other, standing far above the signal's spread."""
    level = np.median(signal) + 12 * median_abs_deviation(signal)
    step = np.median(np.diff(times))
    peaks, _ = find_peaks(signal, height=level, distance=max(1, int(0.15 / step)))
    found = times[peaks]
    for k in range(len(found) - 2):
        if found[k + 2] - found[k] <= span_s:
            return found[k:k + 3]
    return np.array([])


def audio_track(video, seconds=TAP_WINDOW_S, rate=8000):
    """The first `seconds` of the video's audio, mono, as floats."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-t', str(seconds), '-i', str(video), '-ac', '1', '-ar', str(rate),
                          '-f', 'f32le', '-'], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32), rate


def sync_taps(accel_times, accel_xyz, audio, audio_rate, window_s=TAP_WINDOW_S):
    """dict: the three knocks in the accelerometer and the audio (seconds from the video start), and the audio's
    offset from the sensors when both show three knocks spaced alike (within 0.1 s)."""
    inside = accel_times <= window_s
    jerk = np.r_[0, np.linalg.norm(np.diff(accel_xyz[inside], axis=0), axis=1)]
    sensor_knocks = _three_knocks(accel_times[inside], jerk)

    block = int(audio_rate * 0.005)
    envelope = np.abs(audio[:len(audio) // block * block]).reshape(-1, block).max(axis=1)
    audio_knocks = _three_knocks(np.arange(len(envelope)) * block / audio_rate, envelope)

    agree = (len(sensor_knocks) == 3 and len(audio_knocks) == 3
             and np.abs(np.diff(sensor_knocks) - np.diff(audio_knocks)).max() <= 0.1)
    return dict(tap_sensor_s=list(np.round(sensor_knocks, 3)), tap_audio_s=list(np.round(audio_knocks, 3)),
                tap_audio_minus_sensor_s=float(np.median(audio_knocks - sensor_knocks)) if agree else None)


def _windows(turns, duration_s, count, half_s, spacing_s=120.0):
    """Centres of the largest turns, at least spacing_s apart, inside the video."""
    centres = []
    for row in turns.sort_values('total_deg', ascending=False).itertuples():
        centre = (row.start_s + row.end_s) / 2
        if half_s <= centre <= duration_s - half_s and all(abs(centre - c) >= spacing_s for c in centres):
            centres.append(centre)
        if len(centres) == count:
            break
    return sorted(centres)


def rotation_lag(video, times, rate, turns, duration_s, count=6, half_s=6.0, width=320, max_lag_s=1.5):
    """One row per window around a large turn: how late the video is against the gyroscope (video_late_s), the
    correlation at that lag, the focal length in full-resolution pixels and how far the frame time stamps are
    from frame index / nominal fps."""
    import cv2

    capture = cv2.VideoCapture(str(video))
    fps, full_width = capture.get(cv2.CAP_PROP_FPS), capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    lags = np.arange(-max_lag_s, max_lag_s + 1e-9, 0.01)
    rows = []

    for centre in _windows(turns, duration_s, count, half_s):
        capture.set(cv2.CAP_PROP_POS_MSEC, (centre - half_s) * 1000)
        stamps, slides, previous, hann, drift = [], [], None, None, None
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            now = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if drift is None:
                drift = now - (capture.get(cv2.CAP_PROP_POS_FRAMES) - 1) / fps
            small = cv2.resize(frame, (width, int(width * frame.shape[0] / frame.shape[1])), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if hann is None:
                hann = cv2.createHanningWindow(gray.shape[::-1], cv2.CV_32F)
            if previous is not None and now > previous[1]:
                (dx, _), _ = cv2.phaseCorrelate(previous[0], gray, hann)
                stamps.append((now + previous[1]) / 2)
                slides.append(dx / (now - previous[1]))
            previous = gray, now
            if now >= centre + half_s:
                break

        stamps, slides = np.array(stamps), np.array(slides)
        if len(stamps) < 20:
            continue
        corr = np.array([np.corrcoef(slides, np.interp(stamps - lag, times, rate))[0, 1] for lag in lags])
        best = int(np.nanargmax(np.abs(corr)))
        px_per_deg = np.polyfit(np.interp(stamps - lags[best], times, rate), slides, 1)[0]
        rows.append(dict(centre_s=centre, video_late_s=lags[best], corr=corr[best], frames=len(stamps) + 1,
                         focal_px=abs(px_per_deg) * np.degrees(1) * full_width / width, pts_minus_index_s=drift))
    return pd.DataFrame(rows)


def summarize_rotation(windows, min_corr=0.8):
    """The video's lateness over a session from rotation_lag's windows with a clear correlation: median, spread,
    drift (a line through the windows, seconds per hour), focal length and the worst time stamp offset."""
    good = windows[windows['corr'].abs() >= min_corr] if len(windows) else windows
    if len(good) < 2:
        return dict(rotation_windows=len(good))
    slope, intercept = np.polyfit(good['centre_s'], good['video_late_s'], 1)
    return dict(rotation_windows=len(good), video_late_s_median=good['video_late_s'].median(),
                video_late_s_spread=good['video_late_s'].max() - good['video_late_s'].min(),
                video_late_s_at_start=intercept, video_late_drift_s_per_h=slope * 3600,
                rotation_corr_median=good['corr'].abs().median(), focal_px_median=good['focal_px'].median(),
                pts_minus_index_s_max=good['pts_minus_index_s'].abs().max())


def sensor_clock(alignment):
    """t on the sensor clock -> t on the video clock, from one session's summarize_rotation (a dict or row): an
    event the sensors time at t shows in the video at t + video_late_s_at_start + drift * t."""
    start, drift = alignment['video_late_s_at_start'], alignment['video_late_drift_s_per_h'] / 3600
    return lambda t: t + start + drift * t


def to_video_clock(motion, clock):
    """SideSeeingWorkspace.motion tables with start_s and end_s moved onto the video clock."""
    return {kind: table.assign(start_s=clock(table['start_s']), end_s=clock(table['end_s']))
            for kind, table in motion.items()}


def gps_lag(fixes, times, rate, max_lag_s=5.0, min_speed=0.7):
    """How late the raw GPS course is against the gyroscope (gps_late_s), with the correlation there."""
    t, lat, lon = (fixes[c].to_numpy(float) for c in ('t', 'latitude', 'longitude'))
    course = bearing(lat[:-2], lon[:-2], lat[2:], lon[2:])
    metres = np.hypot((lat[2:] - lat[:-2]) * 111_320, (lon[2:] - lon[:-2]) * 111_320 * np.cos(np.radians(lat[1:-1])))
    moving = metres / (t[2:] - t[:-2]) >= min_speed
    tc, course = t[1:-1], np.unwrap(np.radians(course)) * 180 / np.pi
    keep = moving[:-1] & moving[1:] & (np.diff(tc) <= 2.5)
    a, b = tc[:-1][keep], tc[1:][keep]
    course_rate = (np.diff(course) / np.diff(tc))[keep]

    heading = np.r_[0, np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(times))]
    mean_rate = lambda lag: (np.interp(b - lag, times, heading) - np.interp(a - lag, times, heading)) / (b - a)
    lags = np.arange(-max_lag_s, max_lag_s + 1e-9, 0.1)
    corr = np.array([np.corrcoef(course_rate, -mean_rate(lag))[0, 1] for lag in lags])  # course is clockwise
    best = int(np.nanargmax(corr))
    return dict(gps_late_s=float(lags[best]), gps_corr=float(corr[best]), gps_pairs=int(keep.sum()))
