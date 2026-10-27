"""Phase 2b of the graph plan: the curb and the sidewalk's edges from the video, on Morgan (D1).

    python -m graph.phase2b measure --raw RAW --workspace W --rotation rotation_windows.csv --prepared PREP \
        --fit FIT --out OUT --sessions ...
    python -m graph.phase2b fit --workspace W --rotation rotation_windows.csv --prepared PREP --fit FIT \
        --measured OUT --out FIT2 --sessions ...

`measure` needs the video and the masks (desktop-01). Per session it writes:
- heights_<session>.csv: the camera's height from the ground's motion (ground.ground_motion) in the middle 20 s of
  the ten longest runs of the phase 2a fit FIT, against the distance walked by steps (PREP, FIT's step length);
- edges_<session>.csv: per frame, the camera's pitch and roll, the share of the ground just ahead (runs.UNDERFOOT)
  that is sidewalk, and, on each side, the near edge of the curb mask and the edge of the sidewalk mask's run under
  the walker, as ground lines (offset in metres, signed like x: negative to the left; turn; points), at the
  session's height. A session whose heights are already written keeps them.

`fit` (the laptop) turns these into the walking lines' separation along the street and refits the ladder with it:
- the road's width at every leg across the street: the steps taken while no sidewalk is underfoot (road_widths). The
  crosswalk mask covers only the painted bars, so the crosswalk is underfoot only now and then while crossing;
- each walking line's distance from its curb: the curb on the road side of every frame along the street, placed at
  the frame's u on FIT's track (curb_offsets);
- the separation at each leg: its road width plus the two walking lines' distances from their curbs within NEAR_U_M.
It writes FIT2 as phase2 fit does, plus widths.csv, offsets.csv and separations.csv.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from graph import contract, ground, phase2, zones
from graph.runs import STRAIGHT_GAP_S, UNDERFOOT

WINDOW_S, EVERY = 20.0, 3       # height: seconds read from each long run, and every third frame (0.1 s apart)
MIN_RHO, MIN_WALKED_M = 0.6, 0.05
ON_ROAD = 0.5                   # road just ahead: under half of it is sidewalk (the same at both curbs)
NEAR_U_M, MIN_FRAMES = 20.0, 5  # a walking line's distance from its curb: frames within this along the street


def camera_of(instance, clock):
    from sideseeing_tools.analysis.timing import sensor_signal
    from sideseeing_tools.workspace import motion_stream

    g_t, g = sensor_signal(instance.sensors3[motion_stream(instance.sensors3, 'gravity')], ['x', 'y', 'z'],
                           instance.media_start_time)
    return ground.Camera(clock(g_t), g)


def heights(video_path, camera, runs, steps, step_m):
    """One row per long run: metres walked and the ground's motion (in heights) over its middle WINDOW_S."""
    import cv2

    count = lambda t: np.interp(t, steps, np.arange(len(steps)))
    long = runs[runs['kind'] == 'run'].nlargest(10, 'distance_m')
    video = cv2.VideoCapture(str(video_path))
    rows = []
    for run in long.itertuples():
        middle = (run.start_s + run.end_s) / 2
        video.set(cv2.CAP_PROP_POS_FRAMES, int((middle - WINDOW_S / 2) * video.get(cv2.CAP_PROP_FPS)))
        frames, times, k = [], [], 0
        while True:
            ok, frame = video.read()
            t = video.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if not ok or t > middle + WINDOW_S / 2:
                break
            if k % EVERY == 0:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                times.append(t)
            k += 1
        walked = step_m * np.diff(count(np.array(times)))
        moved = pd.DataFrame(ground.ground_motion(camera, frames, times, walked=walked), columns=['k', 'moved', 'rho'])
        moved['walked'] = walked[moved['k'].to_numpy(int) - 1]
        good = moved[(moved['rho'] > MIN_RHO) & (moved['walked'] > MIN_WALKED_M)]
        rows.append(dict(run=run.run, start_s=middle - WINDOW_S / 2, pairs=len(moved), used=len(good),
                         walked_m=good['walked'].sum(), moved=good['moved'].sum()))
    out = pd.DataFrame(rows)
    out['height_m'] = out['walked_m'] / out['moved']
    return out


def edges(ws, session, camera, height):
    """One row per frame: pitch, roll and the curb and sidewalk edge lines on both sides (ground.edge_line)."""
    detections, rows = ws.detections(session), []
    width, height_px = camera.size
    top, left, right = int(UNDERFOOT[0] * height_px), int(UNDERFOOT[1] * width), int(UNDERFOOT[2] * width)
    for frame in ws.frames(session).itertuples():
        masks = zones.frame_masks(ws.preds_dir / 'sam3', session, detections, frame.name, ('curb', 'sidewalk'))
        row = dict(t=frame.t, **dict(zip(('pitch_deg', 'roll_deg'), camera.pitch_roll(frame.t))),
                   sidewalk_underfoot=masks['sidewalk'][top:, left:right].mean() if 'sidewalk' in masks else 0.0)
        for prompt, inner in (('curb', False), ('sidewalk', True)):
            for side in ('left', 'right'):
                line = ground.edge_line(camera, frame.t, masks[prompt], side, height, inner) if prompt in masks else None
                row.update({f'{prompt}_{side}_m': np.nan, f'{prompt}_{side}_turn': np.nan, f'{prompt}_{side}_n': 0}
                           if line is None else
                           {f'{prompt}_{side}_m': line[0], f'{prompt}_{side}_turn': line[1], f'{prompt}_{side}_n': line[2]})
        rows.append(row)
    return pd.DataFrame(rows)


def measure(raw, workspace, rotation, prepared, fit, out, sessions):
    from sideseeing_tools import SideSeeingDS, SideSeeingWorkspace

    ds, ws, windows = SideSeeingDS(str(raw)), SideSeeingWorkspace(str(workspace)), pd.read_csv(rotation)
    step_m = json.loads((fit / 'summary.json').read_text())
    for session in sessions:
        clock = contract.sensor_clock(contract.summarize_rotation(windows[windows['session'] == session]))
        camera = camera_of(ds.instances[session], clock)
        steps = np.sort(pd.read_csv(prepared / f'steps_{session}.csv')['t'].to_numpy())
        written = out / f'heights_{session}.csv'
        if written.exists():
            found = pd.read_csv(written)
        else:
            found = heights(Path(raw) / session / 'video.mp4', camera, pd.read_csv(fit / f'runs_{session}.csv'), steps,
                            step_m[session]['step_m'])
            found.to_csv(written, index=False)
        height = found['walked_m'].sum() / found['moved'].sum()
        print(f'[phase2b] {session}: height {height:.3f} m (runs {found["height_m"].min():.2f}-'
              f'{found["height_m"].max():.2f})', flush=True)
        edges(ws, session, camera, height).assign(height_m=height).to_csv(out / f'edges_{session}.csv', index=False)
        print(f'[phase2b] {session}: edges written', flush=True)


def road_widths(runs, crossings, edges, steps, step_m):
    """One row per leg across the street: its u and the road's width by steps, from about half a frame before its first
    frame with road just ahead (ON_ROAD) to half a frame after its last. The ground just ahead is about 2 m away, the
    same at both curbs, so the look-ahead cancels."""
    count = lambda t: np.interp(t, steps, np.arange(len(steps)))
    on_road = np.sort(edges.loc[edges['sidewalk_underfoot'] < ON_ROAD, 't'].to_numpy())
    rows = []
    for leg in crossings.itertuples():
        run = runs[runs['run'] == leg.run].iloc[0]
        inside = on_road[(on_road >= run['start_s']) & (on_road <= run['end_s'])]
        if len(inside) < 2:
            continue
        stretch = max(np.split(inside, np.flatnonzero(np.diff(inside) > STRAIGHT_GAP_S) + 1), key=len)
        if len(stretch) >= 2:
            rows.append(dict(run=leg.run, u=leg.u, frames=len(stretch),
                             width_m=step_m * (count(stretch[-1] + 0.5) - count(stretch[0] - 0.5))))
    return pd.DataFrame(rows)


def curb_offsets(edges, runs, track):
    """One row per frame along the street with the curb seen on the road side: t, u, the walking line (side) and its
    distance from the curb. Walking +u on the +v line (or -u on the -v line), the road is on the left."""
    along = runs[(runs['kind'] == 'run') & runs['quarter'].isin([0, 2]) & runs['rail'].notna()]
    rows = []
    for run in along.itertuples():
        frames = edges[(edges['t'] >= run.start_s) & (edges['t'] <= run.end_s)]
        road_left = (run.quarter == 0) == (run.rail == 1)
        distance = -frames['curb_left_m'] if road_left else frames['curb_right_m']
        rows.append(pd.DataFrame(dict(t=frames['t'], side=run.rail, distance_m=distance)))
    found = pd.concat(rows, ignore_index=True).dropna()
    order = np.argsort(track['t'].to_numpy())
    found['u'] = np.interp(found['t'], track['t'].to_numpy()[order], track['ladder_u'].to_numpy()[order])
    return found[found['distance_m'] > 0]


def separations(widths, offsets):
    """Each leg's separation: its road width plus both walking lines' median distance from their curbs within
    NEAR_U_M along the street (legs without MIN_FRAMES on both sides are left out)."""
    rows = []
    for leg in widths.itertuples():
        near = offsets[np.abs(offsets['u'] - leg.u) <= NEAR_U_M]
        east, west = near[near['side'] == 1]['distance_m'], near[near['side'] == -1]['distance_m']
        if len(east) >= MIN_FRAMES and len(west) >= MIN_FRAMES:
            rows.append(dict(u=leg.u, width_m=leg.width_m, east_m=east.median(), west_m=west.median(),
                             separation_m=leg.width_m + east.median() + west.median()))
    return pd.DataFrame(rows)


def fit(workspace, rotation, prepared, before, measured, out, sessions):
    summary = json.loads((before / 'summary.json').read_text())
    widths, offsets = [], []
    for session in sessions:
        runs, crossings = pd.read_csv(before / f'runs_{session}.csv'), pd.read_csv(before / f'crossings_{session}.csv')
        steps = np.sort(pd.read_csv(prepared / f'steps_{session}.csv')['t'].to_numpy())
        edges = pd.read_csv(measured / f'edges_{session}.csv')
        widths.append(road_widths(runs, crossings, edges, steps, summary[session]['step_m']).assign(session=session))
        offsets.append(curb_offsets(edges, runs, pd.read_csv(before / f'track_{session}.csv')).assign(session=session))
    widths, offsets = pd.concat(widths, ignore_index=True), pd.concat(offsets, ignore_index=True)
    measured_apart = separations(widths, offsets)
    for name, table in (('widths', widths), ('offsets', offsets), ('separations', measured_apart)):
        table.to_csv(out / f'{name}.csv', index=False)
    print(f'[phase2b] road width by steps: {len(widths)} legs, median {widths["width_m"].median():.2f} m; '
          f'distance from the curb: east {offsets[offsets["side"] == 1]["distance_m"].median():.2f} m, '
          f'west {offsets[offsets["side"] == -1]["distance_m"].median():.2f} m; '
          f'separation at {len(measured_apart)} legs, median {measured_apart["separation_m"].median():.2f} m', flush=True)
    phase2.fit(workspace, rotation, prepared, out, sessions, measured_apart)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=['measure', 'fit'])
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--rotation', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--measured', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sessions', nargs='+', required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.step == 'measure':
        measure(args.raw, args.workspace, args.rotation, args.prepared, args.fit, args.out, args.sessions)
    else:
        fit(args.workspace, args.rotation, args.prepared, args.fit, args.measured, args.out, args.sessions)


if __name__ == '__main__':
    main()
