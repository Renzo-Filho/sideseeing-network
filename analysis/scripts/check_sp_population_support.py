"""125 m pilot sensitivity for the frozen 250 m U4 population approximation."""
import copy
import pandas as pd
from sp_attributes import core as C,spatial
original=C.OUT;primary=pd.read_parquet(original/'pilot_attributes_long.parquet');C.CFG=copy.deepcopy(C.CFG);C.CFG['u4_grid_m']=125;C.CFG['u4_population_support']='125m pilot grid refinement sensitivity';C.OUT=original/'population_support_sensitivity';(C.OUT/'intermediates').mkdir(parents=True,exist_ok=True)
frames=[]
for code in C.CFG['pilots']:
 print('125m support '+code,flush=True);frames.append(spatial.transit_access(code))
f=pd.concat(frames,ignore_index=True);f.to_parquet(C.OUT/'attributes_125m.parquet',index=False)
c=f[['district_id','feature_name','value']].merge(primary[['district_id','feature_name','value']],on=['district_id','feature_name'],suffixes=('_125m','_250m'));c['relative_change']=c.value_125m/c.value_250m-1;c.to_csv(C.OUT/'comparison.csv',index=False)
print(c[c.feature_name.eq('bus_service_access_weekday_am_400m')].to_string(index=False))
