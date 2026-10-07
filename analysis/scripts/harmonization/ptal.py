"""PTAL Access Index arithmetic (TfL Connectivity Assessment Guide 2015, section 2 and figure 2.15)."""
import numpy as np

WALK_M_PER_MIN = 4800 / 60                      # 4.8 km/h
MAX_WALK_M = {"bus": 640, "metro": 960, "rail": 960}  # 8 min bus, 12 min Tube/rail
RELIABILITY_MIN = {"bus": 2.0, "metro": 0.75, "rail": 0.75}


def edf(distance_m, per_hour, mode):
    """Equivalent doorstep frequency of one route: 0.5 * 60 / (walk time + 0.5 * 60 / f + reliability)."""
    tat = np.asarray(distance_m) / WALK_M_PER_MIN + 0.5 * 60 / np.asarray(per_hour) + RELIABILITY_MIN[mode]
    return 0.5 * 60 / tat


def mode_ai(edfs):
    """Largest EDF at full weight plus half of all the others (one mode)."""
    e = np.asarray(edfs, dtype=float)
    return 0.0 if e.size == 0 else e.max() + 0.5 * (e.sum() - e.max())


if __name__ == "__main__":
    # TfL figure 2.15: (mode, distance m, vehicles per hour); published total Access Index 15.16.
    rows = [("bus", 200, 3), ("bus", 200, 10), ("bus", 200, 7), ("bus", 400, 3), ("bus", 400, 4), ("bus", 400, 7),
            ("metro", 746, 8), ("metro", 746, 8), ("rail", 900, 3), ("rail", 900, 2)]
    assert round(float(edf(200, 3, "bus")), 2) == 2.07 and round(float(edf(900, 2, "rail")), 2) == 1.11
    total = sum(mode_ai([edf(d, f, m) for mm, d, f in rows if mm == m]) for m in MAX_WALK_M)
    assert round(total, 2) == 15.16, total
    print("TfL figure 2.15 reproduced: AI =", round(total, 4))
