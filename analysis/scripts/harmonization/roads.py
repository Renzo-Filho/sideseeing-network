"""Shared mapped-street geometry; graph and enclosure measures remain candidates."""
import numpy as np
import pandas as pd
import shapely

CLASSES=['motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown']

def connector_arms(roads):
    """Count each unique segment-side once; never infer a connection from a crossing."""
    if not roads.id.is_unique: raise ValueError('Duplicate source road IDs')
    arms={}
    for row in roads.itertuples():
        for link in row.connectors:
            at=float(link['at'])
            if not np.isfinite(at) or not 0<=at<=1: raise ValueError('Invalid connector position')
            bucket=arms.setdefault(link['connector_id'],set())
            if at>0: bucket.add((row.id,at,'before'))
            if at<1: bucket.add((row.id,at,'after'))
    return {k:len(v) for k,v in arms.items()}

def enclosure_polygons(lines):
    """Planar road enclosures, not accepted physical blocks or a routable graph."""
    merged=shapely.union_all(lines)
    return shapely.get_parts(shapely.polygonize(shapely.get_parts(merged)))

def shape_metrics(polygons):
    area=shapely.area(polygons);perimeter=shapely.length(polygons)
    rectangles=shapely.minimum_rotated_rectangle(polygons)
    elong=[];width=[]
    for r in rectangles:
        coords=np.asarray(r.exterior.coords)
        lens=np.linalg.norm(np.diff(coords,axis=0),axis=1)
        width.append(lens.min());elong.append(lens.max()/lens.min())
    return pd.DataFrame({'area_m2':area,'log_area':np.log(area),
        'compactness':4*np.pi*area/perimeter**2,'elongation':elong,'rectangle_min_width_m':width})
