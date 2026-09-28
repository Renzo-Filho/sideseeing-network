"""Conservative land-use support and whole-block employment accounting."""
import numpy as np
import shapely
from .geometry import polygonal


def exclusive_support(geometries, codes, block, prefixes):
    """Union exact primary codes; withhold cross-code conflicts, including excluded uses."""
    codes=np.asarray(codes)
    clipped=np.array([polygonal(g) for g in shapely.intersection(np.asarray(geometries,dtype=object),block)],dtype=object)
    unions={c:shapely.union_all(clipped[codes==c]) for c in sorted(set(codes))}
    seen=shapely.Polygon(); ambiguous=shapely.Polygon()
    for geom in unions.values():
        ambiguous=polygonal(ambiguous.union(polygonal(seen.intersection(geom))))
        seen=seen.union(geom)
    eligible=polygonal(shapely.union_all([g for c,g in unions.items() if c.startswith(tuple(prefixes))]))
    support=shapely.Polygon() if eligible.is_empty else polygonal(eligible.difference(ambiguous))
    return support,seen.area,ambiguous.area


def partition_block(block, pieces):
    """Ascending district ownership plus an explicit outside-city polygon."""
    covered=shapely.Polygon();result=[]
    for unit,geom in sorted(pieces,key=lambda x:x[0]):
        owned=block.intersection(geom).difference(covered)
        covered=covered.union(owned)
        if owned.area>0:result.append((unit,owned))
    result.append(('OUTSIDE_CHICAGO',block.difference(covered)))
    return result


def allocate_jobs(jobs, block, partitions, support, epsilon=1e-6):
    if not np.isfinite(jobs) or jobs<0:raise ValueError('Invalid jobs')
    if block.area<=0:raise ValueError('Empty block')
    fallback=support.area<=epsilon
    denominator=block.area if fallback else support.area
    masses=np.array([geom.area if fallback else geom.intersection(support).area for _,geom in partitions])
    if not np.isclose(masses.sum(),denominator,rtol=1e-8,atol=1e-5):
        raise ValueError('Support partition does not conserve area')
    allocations=jobs*masses/denominator
    if not np.isclose(allocations.sum(),jobs,rtol=1e-8,atol=1e-7):
        raise ValueError('Jobs not conserved')
    return allocations,masses,denominator,fallback
