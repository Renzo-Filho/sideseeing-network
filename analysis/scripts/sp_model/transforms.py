"""Validated transforms with an explicit, serializable fit/apply boundary."""
import numpy as np
import pandas as pd


def transformed_values(series, kind):
    x = series.astype(float)
    if not np.isfinite(x).all():
        raise ValueError(f"Nonfinite input: {series.name}")
    if kind == 'log':
        if (x <= 0).any():
            raise ValueError(f"Log requires positive values: {series.name}")
        x = np.log(x)
    elif kind == 'log1p':
        if (x < 0).any():
            raise ValueError(f"Service log1p requires nonnegative values: {series.name}")
        x = np.log1p(x)
    elif kind != 'identity':
        raise ValueError(f"Unknown transform {kind}")
    if not np.isfinite(x).all():
        raise ValueError(f"Nonfinite transformed value: {series.name}")
    return x


def fit_transform_scalars(df, config):
    params = {}
    tol = config['scaling']['fallback_to_sd_tolerance']
    if not np.isfinite(tol) or tol <= 0:
        raise ValueError('Invalid scale tolerance')
    for fc in config['families'].values():
        if fc['type'] != 'scalar':
            continue
        for col in fc['columns']:
            x = transformed_values(df[col], fc['transform'])
            iqr = float(x.quantile(.75) - x.quantile(.25))
            sd = float(x.std(ddof=0))
            threshold = tol * max(1., float(x.abs().max()))
            standard = config['scaling']['method'] == 'standard_mean_sd'
            if config['scaling']['method'] not in ('robust_median_iqr', 'standard_mean_sd'):
                raise ValueError('Unknown scaling method')
            fallback = not standard and iqr <= threshold
            scale = sd if standard or fallback else iqr
            params[col] = dict(transform=fc['transform'], median=float(x.median()),
                               center=float(x.mean() if standard else x.median()), iqr=iqr,
                               sd_ddof0=sd, selected_scale=scale, used_sd_fallback=fallback,
                               effective_zero=threshold, retained=scale > threshold)
    return apply_scalar_transforms(df, params), params


def apply_scalar_transforms(df, params):
    if not df.index.is_unique:
        raise ValueError('Duplicate district IDs')
    out = pd.DataFrame(index=df.index)
    excluded = []
    for col, p in params.items():
        x = transformed_values(df[col], p['transform'])
        if not p.get('retained', True):
            excluded.append(col)
            continue
        scale = p['selected_scale']
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError(f'Invalid fitted scale: {col}')
        out[col] = (x - p.get('center', p['median'])) / scale
    if not np.isfinite(out.to_numpy()).all():
        raise ValueError('Nonfinite scaled coordinates')
    out.attrs['excluded_columns'] = excluded
    return out


def transform_composition(df, config):
    if not df.index.is_unique:
        raise ValueError('Duplicate district IDs')
    out = pd.DataFrame(index=df.index)
    adjustments = {}
    for fam, fc in config['families'].items():
        if fc['type'] != 'composition':
            continue
        x = df[fc['columns']].to_numpy(float)
        if not np.isfinite(x).all() or (x < 0).any():
            raise ValueError(f'Invalid composition: {fam}')
        sums = x.sum(axis=1)
        if not np.allclose(sums, 1., rtol=0, atol=1e-8):
            raise ValueError(f'Composition {fam} must sum to one within absolute 1e-8')
        adjustments[fam] = float(np.max(abs(sums - 1.)))
        out[fc['columns']] = np.sqrt(x / sums[:, None])
    out.attrs['max_sum_adjustments'] = adjustments
    return out
