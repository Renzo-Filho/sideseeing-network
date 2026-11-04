"""Which side of the walk the road is on, per run, from SAM3 boxes: the plan's side cue (phase 0 test).

Cars and curbs are on the road side of a sidewalk. In a run, the detections of ROAD_PROMPTS scoring at least
min_score are split by whether their box centre is left or right of the frame's middle; the cue is the side holding
at least `share` of them, from `min_count` detections up, and 'abstain' otherwise.

The West Loop protocol fixes the expected answer along the walked streets: north-south legs go northbound on the
east side and southbound on the west side, east-west legs eastbound on the north side and westbound on the south
side (data/west_loop/plan/sessions.csv), so the road is on the left along NS streets and on the right along EW streets.
Under that protocol the walking direction alone gives the side, which is worth knowing before relying on the cue.
"""
import numpy as np
import pandas as pd

ROAD_PROMPTS = ('car', 'curb')
PROTOCOL_ROAD_SIDE = {0.0: 'left', 90.0: 'right'}  # street axis (deg) -> road side under the protocol


def road_side(runs, detections, frame_width, min_score=0.5, share=0.7, min_count=5):
    """runs with, per ROAD_PROMPT, the detections left and right of the middle, and the cue (road_side)."""
    found = detections[detections['prompt'].isin(ROAD_PROMPTS) & (detections['score'] >= min_score)]
    found = found.assign(left=(found['x0'] + found['x1']) / 2 < frame_width / 2)
    result = runs.copy()

    for prompt in ROAD_PROMPTS:
        mine = found[found['prompt'] == prompt]
        t, left = mine['t'].to_numpy(), mine['left'].to_numpy()
        inside = [(t >= start) & (t <= end) for start, end in zip(runs['start_s'], runs['end_s'])]
        result[f'{prompt}_left'] = [int(left[mask].sum()) for mask in inside]
        result[f'{prompt}_right'] = [int((~left[mask]).sum()) for mask in inside]

    n_left = sum(result[f'{prompt}_left'] for prompt in ROAD_PROMPTS)
    n = n_left + sum(result[f'{prompt}_right'] for prompt in ROAD_PROMPTS)
    left_share = n_left / n.where(n > 0)
    result['road_side'] = np.select([(n >= min_count) & (left_share >= share),
                                     (n >= min_count) & (left_share <= 1 - share)], ['left', 'right'], 'abstain')
    return result


def score_against_protocol(cued, axis_deg):
    """Counts of the cue against the protocol's expected road side for runs along one axis."""
    expected = PROTOCOL_ROAD_SIDE[axis_deg]
    outcome = np.where(cued['road_side'] == 'abstain', 'abstain',
                       np.where(cued['road_side'] == expected, 'agrees', 'disagrees'))
    return pd.Series(outcome).value_counts().reindex(['agrees', 'disagrees', 'abstain'], fill_value=0)
