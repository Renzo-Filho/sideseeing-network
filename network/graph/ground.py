"""The ground seen by the camera (plan sections 5 and 6, phase 2b): pixels onto the ground, the lines of the curb and
the sidewalk's edges beside the walker, and the camera's height.

The camera is a pinhole with the focal length from phase 0 and its centre at the image's middle. The gravity sensor and
the camera are rigid together, so gravity gives the camera's pitch and roll at every frame. The recordings are landscape
with gravity along the phone's x axis: the image's down is that axis, the camera looks along the phone's -z.

A ground point at x metres right of the camera and y metres ahead, with the camera `height` above the ground, is
x * right + y * forward + height * down in camera coordinates (forward and right level, down along gravity), and the
pixel is where that ray meets the image. Everything measured on the ground scales with the height, which the camera
cannot see: it is inferred from the ground's motion between frames 0.1 s apart against the distance walked by steps
(heights).
"""
import numpy as np

F_PX = 1460.0       # phase 0: the image's slide per degree of turn
NEAR_M = (1.5, 8.0)  # ground read for edge lines, metres ahead


class Camera:
    """One session's camera. g_t, g_xyz: the gravity sensor on the video clock, (n,) and (n, 3)."""

    def __init__(self, g_t, g_xyz, size=(1920, 1080), focal=F_PX):
        self.t = np.asarray(g_t, float)
        self.dev = -np.asarray(g_xyz, float) / np.linalg.norm(g_xyz, axis=1, keepdims=True)  # down, phone axes
        image_down = np.array([np.sign(np.median(self.dev[:, 0])), 0.0, 0.0])
        look = np.array([0.0, 0.0, -1.0])
        self.axes = np.array([np.cross(image_down, look), image_down, look])  # camera x, y, z in phone axes
        self.size, self.focal = size, focal

    def frame(self, t):
        """(down, forward, right) at time t, unit vectors in camera coordinates."""
        down = self.axes @ np.array([np.interp(t, self.t, self.dev[:, k]) for k in range(3)])
        down /= np.linalg.norm(down)
        forward = np.array([0.0, 0.0, 1.0]) - down[2] * down
        forward /= np.linalg.norm(forward)
        return down, forward, np.cross(down, forward)

    def pitch_roll(self, t):
        down = self.frame(t)[0]
        return np.degrees(np.arcsin(down[2])), np.degrees(np.arctan2(down[0], down[1]))

    def to_ground(self, t, cols, rows, height):
        """(x right, y ahead) in metres of pixels on the ground; NaN at or above the horizon."""
        down, forward, right = self.frame(t)
        w, h = self.size
        rays = np.column_stack([(np.asarray(cols, float) - w / 2) / self.focal,
                                (np.asarray(rows, float) - h / 2) / self.focal, np.ones(len(cols))])
        depth = rays @ down
        points = rays * np.where(depth > 1e-3, height / np.where(depth > 1e-3, depth, 1), np.nan)[:, None]
        return points @ right, points @ forward

    def to_image(self, t, x, y, height):
        """Pixel (col, row) of ground points x right, y ahead."""
        down, forward, right = self.frame(t)
        points = np.outer(x, right) + np.outer(y, forward) + height * down
        w, h = self.size
        return w / 2 + self.focal * points[:, 0] / points[:, 2], h / 2 + self.focal * points[:, 1] / points[:, 2]


def line_fit(x, y, min_points=15, max_turn=0.35, tolerance_m=0.15):
    """A ground line x = a + b * y through edge points, by least squares on the points within tolerance_m of a robust
    first guess (median slope of point pairs). Returns (offset, b, points used): offset is the line's perpendicular
    distance from the camera, signed like x; None if fewer than min_points or turned more than max_turn from straight
    ahead (the edge of a cross street, a corner)."""
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if len(x) < min_points:
        return None
    pairs = np.random.default_rng(0).integers(0, len(x), (400, 2))
    gaps = y[pairs[:, 1]] - y[pairs[:, 0]]
    ok = np.abs(gaps) > 0.5
    if not ok.any():
        return None
    b = np.median((x[pairs[ok, 1]] - x[pairs[ok, 0]]) / gaps[ok])
    a = np.median(x - b * y)
    near = np.abs(x - a - b * y) < tolerance_m
    if near.sum() < min_points:
        return None
    b, a = np.polyfit(y[near], x[near], 1)
    if abs(b) > max_turn:
        return None
    return a / np.hypot(1, b), b, int(near.sum())


def edge_points(mask, side, step=4, inner=False):
    """(cols, rows) of a mask's edge on one side of the image's middle, every `step` rows: per row the mask pixel nearest
    the middle (inner=False: the near edge of a curb), or the end of the mask's run that holds the middle (inner=True:
    a sidewalk's edge on that side)."""
    height, width = mask.shape
    middle = width // 2
    cols, rows = [], []
    for row in range(height // 2, height, step):
        line = mask[row]
        if inner:
            if not line[middle]:
                continue
            gaps = np.flatnonzero(~line[:middle][::-1]) if side == 'left' else np.flatnonzero(~line[middle:])
            if not len(gaps):
                continue
            col = middle - gaps[0] if side == 'left' else middle + gaps[0] - 1
        else:
            found = np.flatnonzero(line[:middle]) if side == 'left' else np.flatnonzero(line[middle:])
            if not len(found):
                continue
            col = found.max() if side == 'left' else middle + found.min()
        cols.append(col)
        rows.append(row)
    return np.array(cols, float), np.array(rows, float)


def edge_line(camera, t, mask, side, height, inner=False):
    """The ground line of a mask's edge on one side (edge_points, line_fit), read NEAR_M ahead; None if not seen."""
    cols, rows = edge_points(mask, side, inner=inner)
    if not len(cols):
        return None
    x, y = camera.to_ground(t, cols, rows, height)
    near = (y >= NEAR_M[0]) & (y <= NEAR_M[1])
    return line_fit(x[near], y[near])


def ground_motion(camera, frames, t, res=0.004, xs=(-0.35, 0.35), ys=(1.25, 2.6), guess_height=1.25, walked=None):
    """How far the ground straight ahead moved towards the camera between consecutive grey frames (taken at times t),
    in units of the camera's height, by aligning their views from above (ECC). walked: metres walked between them,
    to start the alignment. Returns rows of (k, moved, correlation), k the later frame's index."""
    import cv2

    gx, gy = np.meshgrid(np.arange(*xs, res), np.arange(ys[1], ys[0], -res))  # top row is the farthest

    def above(frame, when):
        c, r = camera.to_image(when, gx.ravel(), gy.ravel(), 1.0)
        c, r = c.reshape(gx.shape).astype(np.float32), r.reshape(gx.shape).astype(np.float32)
        h, w = frame.shape
        inside = ((c > 2) & (c < w - 3) & (r > 2) & (r < h - 3)).astype(np.uint8)
        view = cv2.GaussianBlur(cv2.remap(frame, c, r, cv2.INTER_LINEAR), (0, 0), 2).astype(np.float32)
        return view, cv2.erode(inside, np.ones((15, 15), np.uint8))

    out = []
    views = [above(frame, when) for frame, when in zip(frames, t)]
    for k in range(1, len(views)):
        (a, inside), (b, _) = views[k - 1], views[k]
        start = (walked[k - 1] if walked is not None else 0.13) / guess_height / res
        warp = np.array([[1, 0, 0], [0, 1, start]], np.float32)  # a point of the earlier view, in the later one
        try:
            rho, warp = cv2.findTransformECC(a, b, warp, cv2.MOTION_EUCLIDEAN,
                                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-5), inside, 5)
        except cv2.error:
            continue
        centre = np.array([a.shape[1] / 2, a.shape[0] / 2])
        out.append((k, (warp[1, :2] @ centre + warp[1, 2] - centre[1]) * res, rho))
    return out
