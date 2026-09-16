"""Family distances and their exactly equivalent Euclidean embedding."""
import numpy as np
import pandas as pd


def normalized_weights(config):
    families = config['families']
    values = np.array([f['weight'] for f in families.values()], float)
    if not len(values) or not np.isfinite(values).all() or (values < 0).any() or values.sum() <= 0:
        raise ValueError('Weights must be finite, nonnegative, with positive total')
    cols = [c for f in families.values() for c in f['columns']]
    if len(cols) != len(set(cols)):
        raise ValueError('Duplicate selected feature names')
    return dict(zip(families, values / values.sum()))


def coordinates(scalar_df, comp_df, config):
    if not scalar_df.index.is_unique or not scalar_df.index.equals(comp_df.index):
        raise ValueError('Scalar/composition district indexes must match exactly and be unique')
    result = {}
    for fam, fc in config['families'].items():
        if fc['type'] not in ('scalar', 'composition'):
            raise ValueError(f'Unknown family type: {fam}')
        frame = scalar_df if fc['type'] == 'scalar' else comp_df
        cols = [c for c in fc['columns'] if c not in frame.attrs.get('excluded_columns', [])]
        if not cols:
            raise ValueError(f'Entire family is constant: {fam}')
        x = frame[cols].to_numpy(float)
        if not np.isfinite(x).all():
            raise ValueError(f'Nonfinite family coordinates: {fam}')
        result[fam] = (cols, x, 1 / len(cols) if fc['type'] == 'scalar' else .5)
    return result


def compute_distances(scalar_df, comp_df, config, calibrations=None):
    weights = normalized_weights(config)
    matrices, fitted, contributions = {}, {}, {}
    for fam, (_, x, factor) in coordinates(scalar_df, comp_df, config).items():
        mat = factor * np.square(x[:, None, :] - x[None, :, :]).sum(axis=2)
        if calibrations is None:
            positive = mat[np.triu_indices(len(x), 1)]
            positive = positive[positive > 0]
            if not len(positive):
                raise ValueError(f'No positive pair distances: {fam}')
            b = float(np.median(positive))
        else:
            b = float(calibrations[fam])
        if not np.isfinite(b) or b <= 1e-12:
            raise ValueError(f'Invalid family calibration: {fam}')
        matrices[fam], fitted[fam] = mat, b
        contributions[fam] = weights[fam] * mat / b
    return np.sqrt(sum(contributions.values())), matrices, fitted, contributions


def build_embedding(scalar_df, comp_df, config, calibrations):
    weights = normalized_weights(config)
    out = pd.DataFrame(index=scalar_df.index)
    for fam, (cols, x, factor) in coordinates(scalar_df, comp_df, config).items():
        out[cols] = x * np.sqrt(weights[fam] * factor / calibrations[fam])
    return out


def rank_target(distance, ids, target):
    index = pd.Index(ids, name='district_id')
    s = pd.Series(distance[index.get_loc(target)], index=index).drop(target)
    result = pd.DataFrame({'distance': s, 'rank': s.rank(method='min').astype(int)})
    return result.reset_index().sort_values(['distance', 'district_id']).reset_index(drop=True)
