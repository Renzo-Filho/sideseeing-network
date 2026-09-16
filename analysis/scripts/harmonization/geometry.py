"""Metric geometry helpers with deterministic ownership and exact union areas."""
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely


def polygonal(geometry):
    if geometry is None or geometry.is_empty:
        return shapely.Polygon()
    g = shapely.make_valid(geometry)
    if g.geom_type in ('Polygon', 'MultiPolygon'):
        return g
    return shapely.union_all([p for p in shapely.get_parts(g)
                              if p.geom_type in ('Polygon', 'MultiPolygon')])


def largest_overlap(objects, districts):
    """Whole-object owner by positive intersection area; ties use smallest district ID."""
    a, b = districts.sindex.query(objects.geometry, predicate='intersects')
    areas = shapely.area(shapely.intersection(objects.geometry.values[a], districts.geometry.values[b]))
    q = pd.DataFrame({'object': a, 'district_id': districts.district_id.values[b], 'overlap_m2': areas})
    q = q[q.overlap_m2 > 0].sort_values(['object', 'overlap_m2', 'district_id'], ascending=[True, False, True])
    return q.drop_duplicates('object').set_index('object').district_id.reindex(range(len(objects)))


def union_coverage(buildings, district, land, tile_m=2000):
    """Disjoint tiles avoid summing overlapping building areas or double-counting parts."""
    gross = on_land = summed = 0.
    xmin, ymin, xmax, ymax = district.bounds
    for x in np.arange(np.floor(xmin/tile_m)*tile_m, xmax, tile_m):
        for y in np.arange(np.floor(ymin/tile_m)*tile_m, ymax, tile_m):
            tile = shapely.box(x,y,x+tile_m,y+tile_m).intersection(district)
            if tile.area <= 0:
                continue
            ids = buildings.sindex.query(tile, predicate='intersects')
            pieces = shapely.intersection(buildings.geometry.values[ids], tile)
            union = shapely.union_all(pieces)
            gross += union.area
            on_land += union.intersection(land).area
            summed += float(shapely.area(pieces).sum())
    return gross, on_land, summed


def normalized_entropy(masses, categories):
    a = np.asarray(masses, dtype=float)
    if not np.isfinite(a).all() or (a < 0).any():
        raise ValueError('Entropy masses must be finite and nonnegative')
    if a.sum() == 0:
        return np.nan
    p = a[a > 0] / a.sum()
    return float(-(p*np.log(p)).sum()/np.log(categories))


def exclusive_category_areas(geometries, categories, land):
    """Union within categories; withhold area contested by different categories."""
    categories=np.asarray(categories)
    unions={key:shapely.union_all(np.asarray(geometries)[categories==key]) for key in sorted(set(categories))}
    keys=list(unions)
    ambiguous=shapely.union_all([unions[a].intersection(unions[b]) for i,a in enumerate(keys) for b in keys[i+1:]])
    areas={key:g.difference(ambiguous).intersection(land).area for key,g in unions.items()}
    return areas, ambiguous.area
