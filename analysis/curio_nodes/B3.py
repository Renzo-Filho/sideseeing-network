# B3: explicit unavailable state; no invented measurement.
import geopandas as gpd
import pandas as pd
areas=gpd.read_file(arg[0]['community_areas'])
ids='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
assert len(ids)==ids.nunique()==77
return pd.DataFrame({'unit_id':ids,'feature':['B3']*77,'value':[float('nan')]*77,
    'status':['not_constructed_source_or_entity_gate']*77,'reason':['Constructed floor area per land area: no verified unique all-stock area source is available across residential, condominium, commercial, exempt and DuPage property; parent totals and unit areas may duplicate.']*77}).sort_values('unit_id')
