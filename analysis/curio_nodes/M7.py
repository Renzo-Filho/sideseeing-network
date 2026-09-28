# M7: explicit unavailable state; no invented measurement.
import geopandas as gpd
import pandas as pd
areas=gpd.read_file(arg[0]['community_areas'])
ids='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
assert len(ids)==ids.nunique()==77
return pd.DataFrame({'unit_id':ids,'feature':['M7']*77,'value':[float('nan')]*77,
    'status':['not_constructed_source_or_entity_gate']*77,'reason':['Physical cadastral entity density: Cook parcel, PIN, parent and condominium records do not yet identify unique entities without multiplying tax interests; DuPage support is also unresolved.']*77}).sort_values('unit_id')
