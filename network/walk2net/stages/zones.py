"""Do the SAM3 masks separate a sidewalk's zones? A phase 0 check (plan sections 5 and 8).

On a row of the lower image (the ground near the camera), the paving is the stretch nearest the frame's middle of
the `sidewalk` mask joined with the things standing on it (FURNITURE and people), so a pole does not cut it. Two
measures come out, measured as if the road were on the left:

- the gap: the unpaved strip between the nearest `curb` pixels and the paving (tree pits, grass), the parkway;
- the furniture: FURNITURE whose base stands on the road-side half of the row from the curb to the far edge of the
  paving, and how far from the curb, as a share of that row: the furniture zone reaches at least that far.

There is no building, grass or fence prompt, so the frontage zone cannot be told apart. All measures are in pixels
or shares of a row; metres need the lens and the camera height.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from sideseeing_tools.workspace import prompt_slug

ROWS = (0.65, 0.75, 0.85)  # fractions of the image height, on the ground near the camera
FURNITURE = ('tree', 'pole', 'planter', 'parking meter', 'fire hydrant', 'bench', 'bicycle rack', 'trash bin',
             'bus stop')
COLOURS = {'sidewalk': (59, 130, 246), 'curb': (249, 115, 22), 'furniture': (34, 197, 94)}


def frame_masks(preds_dir, route, detections, frame, prompts, min_score=0.5):
    """{prompt: union of its masks scoring at least min_score} for one frame (detections of SideSeeingWorkspace)."""
    rows = detections[(detections['frame'] == frame) & detections['prompt'].isin(prompts)]
    masks = {}
    for (prompt, chunk, name), _ in rows.groupby(['prompt', 'chunk', 'instances']):
        record = np.load(Path(preds_dir) / prompt_slug(prompt) / route / chunk / name)
        keep = record['scores'] >= min_score
        if keep.any():
            masks[prompt] = record['masks'][keep].any(axis=0)
    return masks


def _segment(row, middle):
    """(first, last) column of the run of True in `row` nearest `middle`, or None."""
    columns = np.flatnonzero(row)
    if not len(columns):
        return None
    breaks = np.flatnonzero(np.diff(columns) > 1)
    starts, ends = columns[np.r_[0, breaks + 1]], columns[np.r_[breaks, len(columns) - 1]]
    k = np.argmin(np.where((starts <= middle) & (ends >= middle), 0, np.minimum(abs(starts - middle), abs(ends - middle))))
    return starts[k], ends[k]


def _row(paved, curb, row):
    """(curb column or NaN, road-side edge, far edge) of the paving on one row, or None."""
    segment = _segment(paved[row], paved.shape[1] // 2)
    if segment is None:
        return None
    curb_columns = np.flatnonzero(curb[row, :segment[0] + 1])
    return (curb_columns.max() if len(curb_columns) else np.nan), *segment


def frame_zones(masks, road_side):
    """Zone measures of one frame with the road on `road_side` ('left' or 'right'): paving width and gap (medians
    over ROWS), the furniture on the road side and its median share from the curb (furniture_share)."""
    if 'sidewalk' not in masks:
        return dict(rows=0)
    flip = (lambda a: a[..., ::-1]) if road_side == 'right' else (lambda a: a)
    paved = flip(np.logical_or.reduce([masks[p] for p in ('sidewalk', 'person', *FURNITURE) if p in masks]))
    curb = flip(masks['curb']) if 'curb' in masks else np.zeros_like(paved)
    height = paved.shape[0]

    measured = [found for found in (_row(paved, curb, int(f * height)) for f in ROWS) if found is not None]
    if not measured:
        return dict(rows=0)
    curb_at, edge, far = map(np.array, zip(*measured))
    gap = float(np.nanmedian(edge - curb_at)) if np.isfinite(curb_at).any() else np.nan
    paving = float(np.median(far - edge))

    furniture, shares = [], []
    for prompt in FURNITURE:
        if prompt not in masks:
            continue
        mask = flip(masks[prompt])
        base = np.flatnonzero(mask.any(axis=1)).max()
        found = _row(paved, curb, base) if base >= height // 2 else None
        if found is None:
            continue
        start = found[0] if np.isfinite(found[0]) else found[1]
        share = (np.flatnonzero(mask[base]).mean() - start) / (found[2] - start)
        if share <= 0.5:
            furniture.append(prompt)
            shares.append(share)

    return dict(rows=len(measured), sidewalk_px=paving, gap_px=gap,
                gap_share=gap / (gap + paving) if np.isfinite(gap) else np.nan, furniture=', '.join(furniture),
                furniture_share=float(np.median(shares)) if shares else np.nan)


def contact_sheet(items, path, columns=4, size=(480, 270)):
    """Thumbnails with the sidewalk, curb and furniture masks over each frame. items: (image path, masks, label)."""
    rows = -(-len(items) // columns)
    sheet = Image.new('RGB', (columns * size[0], rows * (size[1] + 18)), 'white')
    for k, (image_path, masks, label) in enumerate(items):
        image = Image.open(image_path).convert('RGB')
        overlay = np.asarray(image).astype(float)
        for prompt, mask in masks.items():
            colour = COLOURS.get(prompt, COLOURS['furniture'])
            overlay[mask] = 0.5 * overlay[mask] + 0.5 * np.array(colour)
        thumb = Image.fromarray(overlay.astype(np.uint8)).resize(size)
        x, y = (k % columns) * size[0], (k // columns) * (size[1] + 18)
        sheet.paste(thumb, (x, y))
        ImageDraw.Draw(sheet).text((x + 4, y + size[1] + 3), label, fill='black')
    sheet.save(path, quality=85)
    return path
