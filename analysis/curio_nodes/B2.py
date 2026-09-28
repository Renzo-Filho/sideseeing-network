# B2: explicit unavailable state; no invented measurement.
import geopandas as gpd
import pandas as pd
areas=gpd.read_file(arg[0]['community_areas'])
ids='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
assert len(ids)==ids.nunique()==77
return pd.DataFrame({'unit_id':ids,'feature':['B2']*77,'value':[float('nan')]*77,
    'status':['not_constructed_source_or_entity_gate']*77,'reason':['Reported floor-count distribution: municipal story reports cover a selective subset; floor-category meaning, eligible entity joins and commercial, condominium and DuPage support remain unresolved. Height in metres is not reported floors.']*77}).sort_values('unit_id')
