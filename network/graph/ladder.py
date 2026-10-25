"""The ladder of one street (plan sections 3 and 6): two walking lines (rails) joined by crossings (rungs), fitted
together with the trajectory, without a map.

The street frame has u along the street's axis and v across it, positive to the right of u (east for a north-going
axis). Every run gets its heading from the gyroscope: the turn angles chained from the first run, turned onto the frame
by the GPS bearings of the long runs and rounded to the nearest quarter (headings). You cross towards the street, so a
crossing heading +v goes from the -v rail to the +v rail, and the crossings alone say which rail every run between them
is on (assign_rails): no GPS, video or protocol rule. A run whose crossings before and after disagree is flagged.

Under the West Loop protocol a crosswalk is crossed there and back: the walker turns at the far curb and never walks the
far sidewalk. So a crossing is a leg measured by steps, from the walking line it leaves to its own far end, a port at
the far curb; and a walking line is placed only by the runs walked on it. The sessions of one street are fitted
together (fit), sharing the two rails: on Morgan, D1's first session walked the east side and the second the west.

fit solves, by robust least squares, for the two rails and, per session, the step length, the GPS's pull towards the street's middle, where each run starts along the street and where
each crossing starts across it, so that: the position reached by steps along each run's heading lies on its rail, or
for a crossing crosses the street; the GPS fixes match it (with the pull on the sidewalks); and consecutive runs meet.
Both rails belong to one street: they are a centre line, which may bend, plus and minus a half-separation, which barely
changes (both piecewise linear in u, KNOT_M apart). So a stretch of GPS on the wrong side of the street cannot drag one
walking line across the other.
"""
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

KNOT_M = 40.0
GPS_M = 3.0          # GPS error scale
GPS_LATE_S = 1.0     # a fix shows where the walker was about this long before (phase 0: 0.6-2.0 s)
JOIN_M = 1.5         # consecutive runs meet within this (turning in place)
SMOOTH_M = 0.3       # second difference of the street's centre line per knot (it may bend)
SMOOTH_W_M = 0.05    # second difference of the walking lines' half-separation per knot (it barely changes)
STEP_PRIOR = (0.78, 0.1)
ALONG, ACROSS, STAND = 0, 1, 2


def robust(r):
    """Residuals whose squares are the soft-L1 cost: quadratic near zero, linear far out, so an outlier (a GPS fix on
    the wrong side of the street, a missed crossing) pulls little. The shape terms stay quadratic."""
    return np.sign(r) * np.sqrt(2 * (np.sqrt(1 + r ** 2) - 1))


class Frame:
    """u along `axis` (a projected LineString, from its first point), v to the right of it, in metres."""

    def __init__(self, axis):
        (x0, y0), (x1, y1) = axis.coords[0], axis.coords[-1]
        self.origin = np.array([x0, y0])
        self.u = np.array([x1 - x0, y1 - y0]) / np.hypot(x1 - x0, y1 - y0)
        self.v = np.array([self.u[1], -self.u[0]])
        self.bearing = np.degrees(np.arctan2(self.u[0], self.u[1])) % 360  # compass bearing of +u

    def to_uv(self, x, y):
        offset = np.column_stack([x, y]) - self.origin
        return offset @ self.u, offset @ self.v

    def to_xy(self, u, v):
        point = self.origin + np.outer(u, self.u) + np.outer(v, self.v)
        return point[:, 0], point[:, 1]


def headings(runs, frame, turns, min_m=40.0):
    """runs with quarter (0: +u, 1: -v, 2: -u, 3: +v), heading_deg (the quarter's) and gps_gap_deg.

    On a street grid every turn between two runs is a whole number of quarters (a quarter turn, a U-turn, a spin): the
    gyroscope's angles of the turns between consecutive runs, small ones included, are added and rounded to quarters,
    so its error never builds up. Each run of at least min_m takes its quarter from its GPS bearing, reliable to about
    10 degrees over that length. Where the rounded turns between two such runs do not add up to the change their
    bearings show, one rounding slipped: the gap whose angle was nearest to rounding the other way is moved
    (attribute chain_corrections counts them). gps_gap_deg is each long run's GPS bearing against its quarter.
    """
    order = np.argsort(turns['end_s'].to_numpy())
    ends, angles = turns['end_s'].to_numpy()[order], turns['net_deg'].to_numpy(float)[order]
    turned = np.r_[0, np.cumsum(angles)][np.searchsorted(ends, runs['start_s'].to_numpy(), 'right')]
    angle = np.diff(np.r_[0, turned]) / 90  # quarters turned before each run, unrounded
    step = np.round(angle).astype(int)
    observed = -(runs['bearing_deg'].to_numpy(float) - frame.bearing)
    anchors = np.flatnonzero((runs['distance_m'].to_numpy(float) >= min_m) & np.isfinite(observed))
    seen = np.zeros(len(runs), int)
    seen[anchors] = np.round(observed[anchors] / 90).astype(int) % 4

    corrections = 0
    for a, b in zip(anchors[:-1], anchors[1:]):
        gaps = np.arange(a + 1, b + 1)
        need = (seen[b] - seen[a] - step[gaps].sum()) % 4
        need = need - 4 if need > 2 else need
        while need:
            sign = np.sign(need)
            g = gaps[np.argmax(sign * (angle[gaps] - step[gaps]))]
            step[g] += sign
            need -= sign
            corrections += 1

    first = anchors[0] if len(anchors) else 0
    quarter = np.zeros(len(runs), int)
    quarter[first] = seen[first]
    for i in range(first + 1, len(runs)):
        quarter[i] = quarter[i - 1] + step[i]
    for i in range(first - 1, -1, -1):
        quarter[i] = quarter[i + 1] - step[i + 1]
    quarter %= 4
    placed = runs.assign(quarter=quarter, heading_deg=quarter * 90.0,
                         gps_gap_deg=np.where(np.isin(np.arange(len(runs)), anchors),
                                              (observed - quarter * 90 + 180) % 360 - 180, np.nan))
    placed.attrs['chain_corrections'] = corrections
    return placed


def assign_rails(runs):
    """runs with `across` (a crossing of the street), its rail_from and rail_to (+1: the +v side, -1: the -v side),
    the rail of every other run from the crossings around it, and `conflict` where those crossings disagree."""
    across = ((runs['kind'] == 'crossing') & runs['crossing_side'].isin(['left', 'right'])
              & runs['quarter'].isin([1, 3])).to_numpy()
    to = np.where(runs['quarter'] == 3, 1.0, -1.0)
    crossings = np.flatnonzero(across)
    rail, conflict = np.full(len(runs), np.nan), np.zeros(len(runs), bool)
    for i in np.flatnonzero(~across):
        before, after = crossings[crossings < i], crossings[crossings > i]
        by_before = to[before[-1]] if len(before) else np.nan
        by_after = -to[after[0]] if len(after) else np.nan
        rail[i] = by_before if np.isfinite(by_before) else by_after
        conflict[i] = np.isfinite(by_before) and np.isfinite(by_after) and by_before != by_after
    return runs.assign(across=across, rail=rail, rail_from=np.where(across, -to, np.nan),
                       rail_to=np.where(across, to, np.nan), conflict=conflict)


class Ladder:
    """One session's part of the fit (module docstring). runs: from headings and assign_rails; steps: step times;
    fixes: t (video clock, as recorded: GPS_LATE_S is applied here), u and v of the GPS fixes."""

    def __init__(self, runs, steps, fixes):
        self.runs, self.steps = runs.reset_index(drop=True), np.sort(steps)
        if 'run' not in self.runs:
            self.runs['run'] = self.runs.index
        r = self.runs
        self.kind = np.where(r['across'], ACROSS, np.where(r['quarter'].isin([0, 2]), ALONG, STAND))
        self.dir = np.where(r['quarter'] == 2, -1.0, 1.0)     # along u
        self.sign = np.where(r['quarter'] == 3, 1.0, -1.0)    # across, in v
        self.rail = r['rail'].fillna(1).to_numpy()
        self.start, self.end = r['start_s'].to_numpy(float), r['end_s'].to_numpy(float)
        self.total = self._count(self.end) - self._count(self.start)
        self.across, self.n_runs = np.flatnonzero(self.kind == ACROSS), len(r)

        t = self.fix_t = fixes['t'].to_numpy(float) - GPS_LATE_S
        self.fix_u, self.fix_v = fixes['u'].to_numpy(float), fixes['v'].to_numpy(float)
        self.fix_a, self.fix_na, self.fix_b, self.fix_nb, self.fix_w = self._locate(t)
        inside = (self.fix_w == 0) & (self.fix_a == self.fix_b)
        self.fix_side = np.where(inside & (self.kind[self.fix_a] != ACROSS), self.rail[self.fix_a], 0.0)
        on_rails = self.fix_side != 0
        self.u_range = (self.fix_u[on_rails].min() - 20, self.fix_u[on_rails].max() + 20)
        self.n_local = 2 + self.n_runs + len(self.across)

    def _count(self, t):
        return np.searchsorted(self.steps, t)

    def _locate(self, t):
        """For times t: the run before (a) and after (b), the steps taken in each by then, and the weight of b, so that
        a position is (1 - w) * at(a) + w * at(b); inside a run, a = b and w = 0."""
        last = len(self.start) - 1
        a = np.clip(np.searchsorted(self.start, t, 'right') - 1, 0, last)
        inside = t <= self.end[a]
        b = np.where(inside, a, np.minimum(a + 1, last))
        w = np.where(inside | (a == b), 0.0, np.clip((t - self.end[a]) / np.maximum(self.start[b] - self.end[a], 1e-9), 0, 1))
        na = self._count(np.clip(np.where(inside, t, self.end[a]), self.start[a], self.end[a])) - self._count(self.start[a])
        nb = np.where(inside, na, 0)
        return a, na, b, nb, w

    def unpack(self, local, rails, knots):
        v0 = np.zeros(self.n_runs)
        v0[self.across] = local[2 + self.n_runs:]
        return dict(step_m=local[0], pull_m=local[1], u0=local[2:2 + self.n_runs], v0=v0, rails=rails, knots=knots)

    @staticmethod
    def rail_v(p, side, u):
        return np.where(side > 0, np.interp(u, p['knots'], p['rails'][1.0]), np.interp(u, p['knots'], p['rails'][-1.0]))

    def position(self, p, i, n):
        moved = p['step_m'] * n
        u = p['u0'][i] + np.where(self.kind[i] == ALONG, self.dir[i] * moved, 0.0)
        return u, np.where(self.kind[i] == ACROSS, p['v0'][i] + self.sign[i] * moved, self.rail_v(p, self.rail[i], u))

    def track(self, p):
        ua, va = self.position(p, self.fix_a, self.fix_na)
        ub, vb = self.position(p, self.fix_b, self.fix_nb)
        return (1 - self.fix_w) * ua + self.fix_w * ub, (1 - self.fix_w) * va + self.fix_w * vb

    def residuals(self, p):
        u, v = self.track(p)
        i = np.arange(self.n_runs - 1)
        u1, v1 = self.position(p, i, self.total[i])
        u2, v2 = self.position(p, i + 1, np.zeros(len(i)))
        return np.concatenate([robust((u - self.fix_u) / GPS_M), robust((v - self.fix_side * p['pull_m'] - self.fix_v) / GPS_M),
                               robust((u1 - u2) / JOIN_M), robust((v1 - v2) / JOIN_M),
                               [(p['step_m'] - STEP_PRIOR[0]) / STEP_PRIOR[1], p['pull_m'] / 10]])

    def initial(self):
        """Step length and pull from their priors; each run's start, and each crossing's, at the GPS of that moment."""
        order = np.argsort(self.fix_t)
        u0 = np.interp(self.start, self.fix_t[order], self.fix_u[order])
        v0 = np.interp(self.start[self.across], self.fix_t[order], self.fix_v[order])
        return np.concatenate([[STEP_PRIOR[0], 3.0], u0, v0])

    def crossings(self, p):
        """One row per crossing of the street: where it starts (u, v), where its steps end (the port at the far curb),
        its length by steps, and the rail it leaves."""
        c = self.across
        extent = p['step_m'] * self.total[c]
        return pd.DataFrame(dict(run=self.runs['run'].to_numpy()[c], start_s=self.start[c], u=p['u0'][c],
                                 v_start=p['v0'][c], v_end=p['v0'][c] + self.sign[c] * extent, steps=self.total[c],
                                 by_steps_m=extent, leaves=-self.sign[c]))


def fit(sessions):
    """Fits the Ladders of one street together. Returns (knots, rails, [p per session], result, observed): rails is
    {+1: v, -1: v} at the knots, and observed marks, per rail, the knots near fixes taken on it."""
    lo, hi = min(l.u_range[0] for l in sessions), max(l.u_range[1] for l in sessions)
    knots = np.linspace(lo, hi, int(np.ceil((hi - lo) / KNOT_M)) + 1)
    k = len(knots)
    side = np.concatenate([l.fix_side for l in sessions])
    v, u = np.concatenate([l.fix_v for l in sessions]), np.concatenate([l.fix_u for l in sessions])
    level = {s: np.median(v[side == s]) if (side == s).any() else np.nan for s in (1.0, -1.0)}
    for s in (1.0, -1.0):
        if np.isnan(level[s]):
            level[s] = level[-s] + s * 15.0
    bounds = np.cumsum([2 * k] + [l.n_local for l in sessions])
    slices = [slice(a, b) for a, b in zip(bounds[:-1], bounds[1:])]

    def unpack(theta):
        centre, half = theta[:k], theta[k:2 * k]
        rails = {1.0: centre + half, -1.0: centre - half}
        return rails, [l.unpack(theta[sl], rails, knots) for l, sl in zip(sessions, slices)]

    def residuals(theta):
        rails, ps = unpack(theta)
        return np.concatenate([np.diff(theta[:k], 2) / SMOOTH_M, np.diff(theta[k:2 * k], 2) / SMOOTH_W_M,
                               *(l.residuals(p) for l, p in zip(sessions, ps))])

    centre, half = (level[1.0] + level[-1.0]) / 2, (level[1.0] - level[-1.0]) / 2
    x0 = np.concatenate([np.full(k, centre), np.full(k, half), *(l.initial() for l in sessions)])
    result = least_squares(residuals, x0, x_scale='jac')
    rails, ps = unpack(result.x)
    observed = {s: np.array([((side == s) & (np.abs(u - q) <= KNOT_M / 2)).any() for q in knots]) for s in (1.0, -1.0)}
    return knots, rails, ps, result, observed
