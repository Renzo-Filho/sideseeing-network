"""Checks for phase 2b: the ground under the camera. Run from network/: python -m pytest graph/tests"""
import numpy as np

from graph import ground

PITCH, HEIGHT, CURB = np.radians(20.0), 1.4, -1.2


def _camera():
    """Gravity as the phones record it: landscape, along the phone's -x, the screen tilted up by PITCH."""
    g = 9.81 * np.array([-np.cos(PITCH), 0.0, np.sin(PITCH)])
    return ground.Camera(np.array([0.0, 10.0]), np.array([g, g]))


def test_gravity_gives_the_pitch():
    pitch, roll = _camera().pitch_roll(5.0)
    assert abs(pitch - 20.0) < 1e-6 and abs(roll) < 1e-6


def test_a_curb_is_read_at_its_distance():
    camera = _camera()
    mask = np.zeros((1080, 1920), bool)
    for row in range(540, 1080):
        _, y = camera.to_ground(0.0, [960.0], [row], HEIGHT)
        if np.isfinite(y[0]):
            col = camera.to_image(0.0, [CURB], y, HEIGHT)[0][0]
            mask[row, max(int(col) - 30, 0):max(int(col) + 1, 0)] = True  # the curb's top, ending at its near edge
    offset, turn, used = ground.edge_line(camera, 0.0, mask, 'left', HEIGHT)
    assert abs(offset - CURB) < 0.02 and abs(turn) < 0.01 and used > 30
    assert ground.edge_line(camera, 0.0, mask, 'right', HEIGHT) is None
    # Twice the height, twice the distance: everything on the ground scales with it
    assert abs(ground.edge_line(camera, 0.0, mask, 'left', 2 * HEIGHT)[0] - 2 * CURB) < 0.05


def test_a_measured_separation_holds_the_walking_lines_apart():
    import pandas as pd
    from graph import ladder
    from graph.tests import test_phase2 as street
    sessions = [street._ladder(street._north_on_east()), street._ladder(street._south_on_west())]
    apart = pd.DataFrame(dict(u=[50.0, 100.0, 150.0], separation_m=[18.0, 18.0, 18.0]))
    knots, rails, *_ = ladder.fit(sessions, apart)
    assert abs(np.interp(100, knots, rails[1.0] - rails[-1.0]) - 18.0) < 0.5
