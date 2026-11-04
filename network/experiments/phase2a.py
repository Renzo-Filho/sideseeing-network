"""Phase 2a of the graph plan: the ladder on Morgan (D1), with its baselines.

    python -m experiments.phase2a prepare --raw RAW --workspace W --rotation rotation_windows.csv --out PREP --sessions ...
    python -m experiments.phase2a fit --area west_loop --street morgan --workspace W --rotation rotation_windows.csv \
        --prepared PREP --out OUT --sessions ...

`prepare` needs the raw sensors (desktop-01): it writes each session's step times and crosswalk-underfoot times, on
the video clock. `fit` fits the sessions together (they share the street's two walking lines) and each alone, and
writes per session runs_<session>.csv (headings and rails), track_<session>.csv (the ladder's track, together and
alone, and the baselines' at every fix) and crossings_<session>.csv (each crossing's start and far end), plus
walking_lines.csv (each method's two walking lines at the knots) and summary.json. Until the reference is traced (plan
section 8, phase 1), only the summary's non-geometric fields are shown. The street's axis comes from the area's config,
and each session's protocol from the area's field log.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from walk2net import baselines, fieldlog
from walk2net.config import Area
from walk2net.stages import ladder, sync, walk, zones

def clock_of(windows, session):
    return sync.sensor_clock(sync.summarize_rotation(windows[windows['session'] == session]))


def prepare(raw, workspace, rotation, out, sessions):
    from PIL import Image
    from sideseeing_tools import SideSeeingDS, SideSeeingWorkspace
    from sideseeing_tools.analysis.timing import sensor_signal
    from sideseeing_tools.workspace import motion_stream

    ds, ws, windows = SideSeeingDS(str(raw)), SideSeeingWorkspace(str(workspace)), pd.read_csv(rotation)
    for session in sessions:
        instance = ds.instances[session]
        accelerometer = instance.sensors3[motion_stream(instance.sensors3, 'accelerometer')]
        times, xyz = sensor_signal(accelerometer, ['x', 'y', 'z'], instance.media_start_time)
        found = walk.step_times(times, xyz, ws.motion(session)['stops'])  # both on the sensor clock
        pd.DataFrame(dict(t=clock_of(windows, session)(found))).to_csv(out / f'steps_{session}.csv', index=False)

        detections = ws.detections(session)
        size = Image.open(ws.route_frames_dir(session) / ws.frames(session)['name'].iloc[0]).size
        crosswalk = lambda frame: zones.frame_masks(ws.preds_dir / 'sam3', session, detections, frame,
                                                    ('crosswalk',)).get('crosswalk')
        underfoot = walk.crosswalk_underfoot(detections, crosswalk, size)
        pd.DataFrame(dict(t=underfoot)).to_csv(out / f'underfoot_{session}.csv', index=False)
        print(f'[phase2] {session}: {len(found)} steps, {len(underfoot)} frames on a crosswalk', flush=True)


def in_frame(table, frame, crs):
    """table (longitude, latitude) with u and v in the street frame (projected in `crs`)."""
    import geopandas as gpd
    points = gpd.GeoSeries(gpd.points_from_xy(table['longitude'], table['latitude']), crs=4326).to_crs(crs)
    u, v = frame.to_uv(points.x, points.y)
    return table.assign(u=u, v=v)


def session_ladder(ws, windows, prepared, session, frame, crs):
    """One session's runs (with headings and rails), steps, GPS fixes in the street frame, its 5-fix median track and
    its Ladder."""
    motion = sync.to_video_clock(ws.motion(session), clock_of(windows, session))
    gps = ws.gps(session)
    start, stop = ws._media_times(session)
    cut = walk.cut_runs(motion, gps, (stop - start).total_seconds())
    underfoot = pd.read_csv(prepared / f'underfoot_{session}.csv')['t'].to_numpy()
    cut = walk.split_at_crosswalks(cut, underfoot, motion['stops'], gps)
    placed = ladder.assign_rails(ladder.headings(cut, frame, motion['turns']))
    stepped = pd.read_csv(prepared / f'steps_{session}.csv')['t'].to_numpy()
    fixes = in_frame(sync.read_fixes(ws.data_dir / session / 'gps.csv', pd.Timestamp(start, tz='UTC')), frame, crs)
    fixes = fixes[(fixes['t'] >= 0) & (fixes['t'] <= (stop - start).total_seconds())].reset_index(drop=True)
    return placed, stepped, fixes, in_frame(gps, frame, crs), ladder.Ladder(placed, stepped, fixes)


def side_summary(placed, stepped, road_side):
    """How the crossings alone placed the runs, against the session's protocol, for every run along the street and for
    those of at least 40 m. Walking +u with the road on the left is the +1 rail (right of the axis); `road_side` is
    the side the protocol puts the road on along this street, or None (a free route: no expectation)."""
    along = placed[placed['quarter'].isin([0, 2]) & ~placed['across']]
    out_rail = {'left': 1.0, 'right': -1.0}.get(road_side, np.nan)
    agrees = along['rail'].to_numpy() == np.where(along['quarter'] == 0, out_rail, -out_rail)
    long = along['distance_m'].to_numpy() >= 40
    return dict(runs=len(placed), along=len(along), crossings_of_the_street=int(placed['across'].sum()),
                conflicts=int(placed['conflict'].sum()), chain_corrections=placed.attrs['chain_corrections'],
                chain_vs_gps_deg_median=float(np.nanmedian(np.abs(placed['gps_gap_deg']))),
                side_agrees_with_protocol=float(agrees.mean()), long_runs=int(long.sum()),
                long_side_agrees_with_protocol=float(agrees[long].mean()), steps=len(stepped))


def fit(area, street, workspace, rotation, prepared, out, sessions, separations=None):
    """Each session alone (what one walk can do) and all together (the street), with the baselines. separations:
    the walking lines' separation measured along the street (phase 2b), for the joint fit."""
    from sideseeing_tools import SideSeeingWorkspace

    ws, windows = SideSeeingWorkspace(str(workspace)), pd.read_csv(rotation)
    protocols = fieldlog.protocols(fieldlog.read(area.field_log), sessions)
    frame = ladder.Frame(street.projected(area.crs))
    parts = {session: session_ladder(ws, windows, prepared, session, frame, area.crs) for session in sessions}
    models = [part[-1] for part in parts.values()]
    knots, rails, together, result, observed = ladder.fit(models, separations)
    summary = dict(together=dict(solved=bool(result.success), evaluations=int(result.nfev)))
    tracks = []

    for (session, (placed, stepped, fixes, median5, model)), p in zip(parts.items(), together):
        _, _, (alone,), alone_result, _ = ladder.fit([model])
        u, v = model.track(p)
        a_u, a_v = model.track(alone)
        m_u, m_v = (np.interp(fixes['t'], median5['t'], median5[c]) for c in ('u', 'v'))
        run_at = lambda t: np.clip(np.searchsorted(placed['start_s'], t, 'right') - 1, 0, len(placed) - 1)
        k_u, k_v = baselines.pdr_smoother(model.fix_t, fixes['u'].to_numpy(), fixes['v'].to_numpy(), stepped,
                                          lambda t: placed['heading_deg'].to_numpy()[run_at(t)], p['step_m'])
        track = pd.DataFrame(dict(t=fixes['t'], side=model.fix_side, gps_u=fixes['u'], gps_v=fixes['v'],
                                  ladder_u=u, ladder_v=v, alone_u=a_u, alone_v=a_v, median5_u=m_u, median5_v=m_v,
                                  pdr_u=k_u, pdr_v=k_v))
        tracks.append(track)
        placed.to_csv(out / f'runs_{session}.csv', index=False)
        track.to_csv(out / f'track_{session}.csv', index=False)
        model.crossings(p).to_csv(out / f'crossings_{session}.csv', index=False)
        road_side = protocols[session].road_side_along(street.orientation)
        summary[session] = dict(**side_summary(placed, stepped, road_side), step_m=float(p['step_m']), pull_m=float(p['pull_m']),
                                alone=dict(step_m=float(alone['step_m']), pull_m=float(alone['pull_m']),
                                           solved=bool(alone_result.success)))
        print(f'[phase2] {session}: ' + json.dumps(summary[session], default=lambda x: round(x, 3)), flush=True)

    # Each method's two walking lines at the knots, from all sessions' points on each side
    pooled = pd.concat(tracks, ignore_index=True)
    lines = pd.DataFrame(dict(u=knots, ladder_east=rails[1.0], ladder_west=rails[-1.0],
                              observed_east=observed[1.0], observed_west=observed[-1.0]))
    for name in ('gps', 'median5', 'pdr'):
        found = baselines.rails_from_track(pooled[f'{name}_u'].to_numpy(), pooled[f'{name}_v'].to_numpy(),
                                           pooled['side'].to_numpy(), knots)
        lines[f'{name}_east'], lines[f'{name}_west'] = found[1.0], found[-1.0]
    lines.to_csv(out / 'walking_lines.csv', index=False)
    print(f"[phase2] together: {summary['together']}", flush=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('step', choices=['prepare', 'fit'])
    parser.add_argument('--area', help='fit: an area config, network/areas/<area>.toml')
    parser.add_argument('--street', help="fit: a street of the area's config")
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--rotation', type=Path, required=True)
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sessions', nargs='+', required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.step == 'prepare':
        prepare(args.raw, args.workspace, args.rotation, args.out, args.sessions)
    else:
        area = Area.load(args.area)
        fit(area, area.streets[args.street], args.workspace, args.rotation, args.prepared, args.out, args.sessions)


if __name__ == '__main__':
    main()
