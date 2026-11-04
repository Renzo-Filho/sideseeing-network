"""Baselines for the walking lines (plan section 6), in the street frame of walk2net.stages.ladder.

pdr_smoother is GPS + pedestrian dead reckoning: between fixes the walker moves by the steps taken along the
gyroscope heading, each fix measures the position, and a Kalman filter with a Rauch-Tung-Striebel smoother combines
them. It knows the same steps and headings as the ladder, but not that runs lie on rails, that crossings join them,
or that GPS is pulled towards the street's middle. rails_from_track turns any track (raw GPS, the 5-fix median, the
smoother) into two walking lines, for comparing with the ladder's.
"""
import numpy as np

STEP_NOISE_M = 0.05  # per step
TURN_NOISE_M = 0.1   # per fix interval


def pdr_smoother(t, u, v, step_times, heading_at, step_m, gps_m=3.0):
    """Smoothed (u, v) at the fix times t. heading_at(times) gives the heading in degrees anticlockwise from +u."""
    count = np.searchsorted(np.sort(step_times), t)
    taken = np.r_[0, np.diff(count)]
    heading = np.radians(heading_at((t + np.r_[t[0], t[:-1]]) / 2))
    move = step_m * taken[:, None] * np.column_stack([np.cos(heading), -np.sin(heading)])  # +v is to the right
    noise = (TURN_NOISE_M + STEP_NOISE_M * taken) ** 2
    z, r = np.column_stack([u, v]), gps_m ** 2

    n = len(t)
    x, p = np.zeros((n, 2)), np.zeros(n)          # filtered (the variance is the same in u and v)
    xp, pp = np.zeros((n, 2)), np.zeros(n)        # predicted
    x[0], p[0] = z[0], r
    for k in range(1, n):
        xp[k], pp[k] = x[k - 1] + move[k], p[k - 1] + noise[k]
        gain = pp[k] / (pp[k] + r)
        x[k], p[k] = xp[k] + gain * (z[k] - xp[k]), (1 - gain) * pp[k]
    smooth = x.copy()
    for k in range(n - 2, -1, -1):
        smooth[k] = x[k] + p[k] / pp[k + 1] * (smooth[k + 1] - xp[k + 1])
    return smooth[:, 0], smooth[:, 1]


def rails_from_track(u, v, side, knots, half_m=None):
    """{+1: v, -1: v} at each knot: the median v of the track's points on that side within half a knot spacing
    (NaN where it has none)."""
    half = half_m or np.median(np.diff(knots)) / 2
    return {s: np.array([np.median(v[(side == s) & (np.abs(u - k) <= half)])
                         if ((side == s) & (np.abs(u - k) <= half)).any() else np.nan for k in knots])
            for s in (1.0, -1.0)}
