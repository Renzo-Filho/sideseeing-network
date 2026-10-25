"""Phase 0 of the graph plan: the data contract, the runs, the side cue and the zone check.

    python -m graph.phase0 align  --raw RAW --workspace WORKSPACE --out OUT   # needs the raw videos and sensors
    python -m graph.phase0 report --workspace WORKSPACE --out OUT [--pieces routes.gpkg] [--sessions ...]
                                  [--zone-sessions ...]

`align` writes alignment.csv and rotation_windows.csv; `report` writes sessions.csv, runs/<session>.csv,
side_cue.csv and, for --zone-sessions, zones_<session>.csv and .jpg. Sessions not listed in --sessions (the
held-out ones) get only their contract rows.
"""
import argparse
import json
import subprocess
from pathlib import Path

import pandas as pd
from PIL import Image

from graph import contract, runs, side_cue, zones

AXES = (0.0, 90.0)  # the West Loop grid: north-south and east-west streets
ZONE_RUNS = 3
ZONE_FRAMES_PER_RUN = 8


def video_stream(video):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                            'stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_frames', '-of', 'json',
                            str(video)], check=True, capture_output=True, text=True)
    return json.loads(probe.stdout)['streams'][0]


def align(raw, workspace, out):
    from sideseeing_tools import SideSeeingDS, SideSeeingWorkspace
    from sideseeing_tools.analysis.timing import sensor_signal
    from sideseeing_tools.analysis.turns import heading_rate
    from sideseeing_tools.workspace import motion_stream

    ds, ws = SideSeeingDS(str(raw)), SideSeeingWorkspace(str(workspace))
    rows, windows = [], []
    for instance in ds.iterator:
        print(f'[phase0] aligning {instance.name}', flush=True)
        start, sensors = instance.media_start_time, instance.sensors3
        name = lambda kind: motion_stream(sensors, kind)
        times, rate = heading_rate(sensors[name('gyroscope')], sensors[name('gravity')], start)
        accel_times, accel = sensor_signal(sensors[name('accelerometer')], ['x', 'y', 'z'], start)
        row = dict(session=instance.name, **video_stream(instance.video))
        row.update(contract.sync_taps(accel_times, accel, *contract.audio_track(instance.video)))
        fixes = contract.read_fixes(Path(instance.path) / 'gps.csv', pd.Timestamp(start, tz='UTC'))
        row.update(contract.gps_lag(fixes, times, rate))
        light = [s for s in (instance.sensors1 or {}) if 'light' in s.lower()]
        if light:
            frame = instance.sensors1[light[0]]
            row['light_lux_median'] = frame.select_dtypes('number').drop(columns='timestamp_nano', errors='ignore').iloc[:, 0].median()
        found = contract.rotation_lag(instance.video, times, rate, ws.motion(instance.name)['turns'],
                                      instance.media_total_time)
        windows.append(found.assign(session=instance.name))
        row.update(contract.summarize_rotation(found))
        rows.append(row)
        pd.DataFrame(rows).to_csv(out / 'alignment.csv', index=False)
    pd.concat(windows, ignore_index=True).to_csv(out / 'rotation_windows.csv', index=False)


def zone_check(ws, route, along, road_of_axis, out):
    """Zone measures on every frame of ZONE_RUNS runs spread over the session, and a contact sheet of some."""
    chosen = along[along['distance_m'].between(60, 250)]
    chosen = chosen.iloc[[round(k * (len(chosen) - 1) / (ZONE_RUNS - 1)) for k in range(ZONE_RUNS)]].drop_duplicates()
    frames, detections = ws.frames(route), ws.detections(route, min_score=0.5)
    prompts = ('sidewalk', 'curb', 'person', *zones.FURNITURE)
    rows, sheet = [], []
    for run in chosen.itertuples():
        inside = frames[frames['t'].between(run.start_s, run.end_s)]
        step = max(1, len(inside) // ZONE_FRAMES_PER_RUN)
        for k, frame in enumerate(inside.itertuples()):
            masks = zones.frame_masks(ws.preds_dir / 'sam3', route, detections, frame.name, prompts)
            measure = zones.frame_zones(masks, road_of_axis[run.axis])
            rows.append(dict(run=run.run, t=frame.t, frame=frame.name, **measure))
            if k % step == 0 and len(sheet) < ZONE_RUNS * ZONE_FRAMES_PER_RUN:
                label = (f"run {run.run}  t={frame.t:.0f}s  gap {measure.get('gap_share', float('nan')):.0%}  "
                         f"{measure.get('furniture', '')}")
                shown = {p: masks[p] for p in masks if p in ('sidewalk', 'curb') or p in zones.FURNITURE}
                sheet.append((ws.route_frames_dir(route) / frame.name, shown, label))
    table = pd.DataFrame(rows)
    table.to_csv(out / f'zones_{route}.csv', index=False)
    zones.contact_sheet(sheet, out / f'zones_{route}.jpg')
    return table


def report(workspace, out, pieces_path=None, sessions=(), zone_sessions=()):
    from sideseeing_tools import SideSeeingWorkspace

    ws = SideSeeingWorkspace(str(workspace))
    pieces = None
    if pieces_path:
        import geopandas as gpd
        pieces = gpd.read_file(pieces_path, layer='pieces')

    summaries = []
    for session_dir in sorted(p for p in ws.data_dir.iterdir() if p.is_dir()):
        summary = contract.session_summary(session_dir, pieces)
        motion = ws.motion(session_dir.name)
        if motion:
            summary.update({kind: len(table) for kind, table in motion.items()})
        summaries.append(summary)
    pd.DataFrame(summaries).to_csv(out / 'sessions.csv', index=False)

    (out / 'runs').mkdir(exist_ok=True)
    cues = []
    for route in sessions:
        track, motion = ws.gps(route), ws.motion(route)
        duration = (ws._media_times(route)[1] - ws._media_times(route)[0]).total_seconds()
        cut = runs.cut_runs(motion, track, duration)
        cut.to_csv(out / 'runs' / f'{route}.csv', index=False)
        along = pd.concat([runs.axis_runs(cut, axis).assign(axis=axis) for axis in AXES]).sort_values('start_s')

        detections = ws.detections(route)
        if detections.empty:
            continue
        width = Image.open(ws.route_frames_dir(route) / ws.frames(route)['name'].iloc[0]).size[0] \
            if ws.route_frames_dir(route).is_dir() else 1920
        cued = side_cue.road_side(along, detections, width)
        cues.append(cued.assign(session=route))
        for axis in AXES:
            mine = cued[cued['axis'] == axis]
            if len(mine):
                print(route, f'axis {axis:.0f}:', side_cue.score_against_protocol(mine, axis).to_dict())
        if route in zone_sessions:
            zone_check(ws, route, along, side_cue.PROTOCOL_ROAD_SIDE, out)
    if cues:
        pd.concat(cues, ignore_index=True).to_csv(out / 'side_cue.csv', index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=['align', 'report'])
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pieces', type=Path)
    parser.add_argument('--sessions', nargs='*', default=[])
    parser.add_argument('--zone-sessions', nargs='*', default=[])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.step == 'align':
        align(args.raw, args.workspace, args.out)
    else:
        report(args.workspace, args.out, args.pieces, args.sessions, args.zone_sessions)


if __name__ == '__main__':
    main()
