# M6 consumes the exact selected, clipped, boundary-owned lengths from M1.
import numpy as np
m1,lengths=arg
classes=['motorway','trunk','primary','secondary','tertiary','residential','living_street','pedestrian','unclassified','unknown']
wide=lengths.pivot(index='unit_id',columns='class',values='length_m').reindex(columns=classes)
if wide.isna().any().any(): raise ValueError('Missing road class lengths')
result=m1[['unit_id','eligible_road_length_m']].merge(wide,left_on='unit_id',right_index=True,validate='one_to_one')
for c in classes: result['M6_share_'+c]=result[c]/result.eligible_road_length_m
assert np.allclose(result.filter(like='M6_share_').sum(axis=1),1,atol=1e-9)
result['status']='constructed_chicago'
return result[['unit_id']+['M6_share_'+c for c in classes]+['eligible_road_length_m','status']]
