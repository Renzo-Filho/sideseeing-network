# M4 uses exactly the same experimental enclosures as M3.
import pandas as pd
import numpy as np
import shapely
m3,faces=arg
compact=[];elong=[]
for geom in faces.geometry:
    area=geom.area; perimeter=geom.length
    compact.append(4*np.pi*area/perimeter**2)
    r=shapely.minimum_rotated_rectangle(geom)
    coords=np.asarray(r.exterior.coords)
    sides=np.linalg.norm(np.diff(coords,axis=0),axis=1)
    elong.append(float(sides.max()/sides.min()))
q=faces[['unit_id']].copy(); q['compactness']=compact; q['elongation']=elong
agg=q.groupby('unit_id').agg(M4_compactness_median=('compactness','median'),
    M4_compactness_iqr=('compactness',lambda x:x.quantile(.75)-x.quantile(.25)),
    M4_elongation_median=('elongation','median'),
    M4_elongation_iqr=('elongation',lambda x:x.quantile(.75)-x.quantile(.25)))
result=m3[['unit_id']].join(agg,on='unit_id')
result['status']='experimental_enclosures_not_accepted_blocks'
return result
