"""Independent Chicago functional-support primitives; metric inputs required."""
import datetime as dt
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely


def active_services(calendar, exceptions, date):
    stamp = date.strftime('%Y%m%d')
    day = date.strftime('%A').lower()
    active = set(calendar.loc[(calendar.start_date <= stamp) &
                             (calendar.end_date >= stamp) & calendar[day].eq('1'), 'service_id'])
    for row in exceptions.loc[exceptions.date.eq(stamp)].itertuples():
        if row.exception_type == '1':
            active.add(row.service_id)
        elif row.exception_type == '2':
            active.discard(row.service_id)
        else:
            raise ValueError('Unknown calendar exception type')
    return active


def seconds(values):
    parts = values.str.extract(r'^(\d+):([0-5]\d):([0-5]\d)$')
    if parts.isna().any().any():
        raise ValueError('Invalid or missing departure time')
    return parts.astype('int64').to_numpy() @ np.array([3600, 60, 1])


def allocate(blocks, districts):
    """Gross-area allocation, retaining whole-block denominators and outside residuals."""
    a, b = districts.sindex.query(blocks.geometry, predicate='intersects')
    pieces = shapely.intersection(blocks.geometry.values[a], districts.geometry.values[b])
    area = shapely.area(pieces)
    keep = area > 0
    a, b, pieces, area = a[keep], b[keep], pieces[keep], area[keep]
    q = gpd.GeoDataFrame({'GEOID20': blocks.GEOID20.values[a],
                         'unit_id': districts.unit_id.values[b],
                         'piece_area_m2': area,
                         'block_area_m2': blocks.geometry.area.values[a],
                         'POP20': blocks.POP20.values[a],
                         'jobs': blocks.jobs.values[a]}, geometry=pieces, crs=blocks.crs)
    q['weight'] = q.piece_area_m2 / q.block_area_m2
    sums = q.groupby('GEOID20').weight.sum()
    if (sums > 1 + 1e-8).any():
        raise ValueError('Overlapping reporting geography allocates excess mass')
    q['population_allocated'] = q.POP20 * q.weight
    q['jobs_allocated'] = q.jobs * q.weight
    return q


def population_grid(pieces, step=250):
    rows, geoms = [], []
    for row in pieces.loc[pieces.POP20 > 0].itertuples():
        xmin, ymin, xmax, ymax = row.geometry.bounds
        xx, yy = np.meshgrid(np.arange(np.floor(xmin/step)*step, xmax, step),
                             np.arange(np.floor(ymin/step)*step, ymax, step))
        cells = shapely.box(xx.ravel(), yy.ravel(), xx.ravel()+step, yy.ravel()+step)
        parts = shapely.intersection(cells, row.geometry)
        areas = shapely.area(parts)
        for part, area in zip(parts[areas > 0], areas[areas > 0]):
            rows.append((row.GEOID20, row.unit_id, row.POP20 * area / row.block_area_m2))
            geoms.append(part.representative_point())
    points = gpd.GeoDataFrame(rows, columns=['GEOID20', 'unit_id', 'population_weight'],
                             geometry=geoms, crs=pieces.crs)
    points['point_id'] = np.arange(len(points))
    expected = pieces.groupby('unit_id').population_allocated.sum()
    actual = points.groupby('unit_id').population_weight.sum().reindex(expected.index, fill_value=0)
    if not np.allclose(actual, expected, rtol=1e-9, atol=.001):
        raise ValueError('Population grid does not conserve district mass')
    return points


def supply(points, stops, service, radius):
    """Maximum stop supply per route/direction, summed over route/directions."""
    a, b = stops.sindex.query(points.geometry, predicate='dwithin', distance=radius)
    pairs = pd.DataFrame({'point_id': points.point_id.values[a], 'stop_id': stops.stop_id.values[b]})
    joined = pairs.merge(service, on='stop_id', validate='many_to_many')
    maxima = joined.groupby(['point_id', 'route_id', 'direction_id']).departures.max()
    values = maxima.groupby('point_id').sum()
    return points.point_id.map(values).fillna(0).to_numpy()
