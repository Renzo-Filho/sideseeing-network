"""Native-grid GHSL aggregation; no building-level interpretation or interpolation."""
import numpy as np
import shapely


def summarize_cells(values, valid, overlap_m2, cell_area_m2, support_area_m2, extensive=False):
    """Allocate extensive mass uniformly; average intensive values by valid area.

    Zero is retained. Missing coverage is exposed and never scaled up to full support.
    """
    values = np.asarray(values, dtype=float)
    valid = np.asarray(valid, dtype=bool)
    overlap = np.asarray(overlap_m2, dtype=float)
    if values.shape != valid.shape or values.shape != overlap.shape:
        raise ValueError('Cell arrays must have matching shapes')
    if not np.isfinite(cell_area_m2) or cell_area_m2 <= 0:
        raise ValueError('Cell area must be positive')
    if not np.isfinite(support_area_m2) or support_area_m2 <= 0:
        raise ValueError('Support area must be positive')
    if not np.isfinite(overlap).all() or (overlap < 0).any() or (overlap > cell_area_m2 + 1e-6).any():
        raise ValueError('Invalid intersection area')
    if not np.isfinite(values[valid]).all() or (values[valid] < 0).any():
        raise ValueError('Valid GHSL values must be finite and nonnegative')
    total = float(overlap.sum())
    tolerance = max(1e-4, support_area_m2 * 1e-9)
    if total > support_area_m2 + tolerance:
        raise ValueError('Cell overlaps exceed reporting support')
    area = float(overlap[valid].sum())
    numerator = float(np.dot(values[valid], overlap[valid]))
    result = {
        'support_area_m2': float(support_area_m2),
        'covered_area_m2': total,
        'valid_area_m2': area,
        'nodata_area_m2': float(overlap[~valid].sum()),
        'outside_raster_area_m2': max(0., support_area_m2 - total),
        'valid_area_fraction': area / support_area_m2,
        'zero_area_m2': float(overlap[valid & (values == 0)].sum()),
        'partial_cell_area_m2': float(overlap[(overlap > 0) & (overlap < cell_area_m2 - 1e-6)].sum()),
        'value': None,
        'observed_allocated_mass_m3': None,
    }
    if extensive:
        result['observed_allocated_mass_m3'] = numerator / cell_area_m2
        # Withhold density for missing support, rather than silently assuming zero there.
        if support_area_m2 - area <= tolerance:
            result['value'] = numerator / cell_area_m2 / support_area_m2
    elif area > 0:
        result['value'] = numerator / area
    return result


def native_cells(transform, height, width):
    if transform.b != 0 or transform.d != 0 or transform.a <= 0 or transform.e >= 0:
        raise ValueError('Expected north-up native grid')
    rows, cols = np.indices((height, width))
    x = transform.c + cols.ravel() * transform.a
    y = transform.f + rows.ravel() * transform.e
    return shapely.box(x, y + transform.e, x + transform.a, y)
