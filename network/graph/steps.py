"""Steps from the accelerometer, as in the West Loop notebook (west_loop.ipynb, section 2): the magnitude,
band-passed to BAND_HZ, has one peak per step, at least MIN_GAP_S apart and PROMINENCE (m/s²) high. Peaks inside
stops are dropped. The notebook found 0.78 m per step on the West Loop days.
"""
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

BAND_HZ = (0.8, 3.5)
MIN_GAP_S = 0.33
PROMINENCE = 1.0


def step_times(times, xyz, stops=None):
    """Times of the steps in an accelerometer stream (times in s, xyz in m/s²), outside `stops` (start_s, end_s)."""
    rate = 1 / np.median(np.diff(times))
    b, a = butter(2, [BAND_HZ[0] / (rate / 2), BAND_HZ[1] / (rate / 2)], 'band')
    peaks, _ = find_peaks(filtfilt(b, a, np.linalg.norm(xyz, axis=1)), distance=int(MIN_GAP_S * rate),
                          prominence=PROMINENCE)
    found = times[peaks]
    if stops is not None and len(stops):
        inside = ((found[:, None] >= stops['start_s'].to_numpy()) & (found[:, None] < stops['end_s'].to_numpy())).any(1)
        found = found[~inside]
    return found
