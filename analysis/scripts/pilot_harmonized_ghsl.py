"""Paired GHSL pilots; report candidate statistics, never fit a model."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from harmonization.rasters import native_cells, summarize_cells

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/SP_CHI/harmonization_2026_09_22_h0_h1'
CITIES={
 'Chicago': ('CHI', ['24','28','30','32','76'],
 'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet',
 'analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet'),
 'SP': ('SP',['10','30','35'],
 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet',
 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet')}

def digest(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 rows=[]; receipts=[]; checks=[]
 for city,(prefix,pilots,district_path,land_path) in CITIES.items():
  districts=gpd.read_parquet(ROOT/district_path).to_crs('ESRI:54009')
  land=gpd.read_parquet(ROOT/land_path).to_crs('ESRI:54009')
  for d in [districts,land]:
   if 'unit_id' not in d: d['unit_id']=prefix+':'+d.district_id.astype(str).str.zfill(2)
  for p in [ROOT/district_path,ROOT/land_path]: receipts.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p)})
  # Select SP pilots by source names, not an assumed numeric ID mapping.
  if city=='SP':
   name_col='nm_distrito_municipal'
   names=districts[name_col].astype(str).str.upper()
   selected=districts.loc[names.isin(['BRAS','BRÁS','ITAIM BIBI','GRAJAU','GRAJAÚ'])]
   if len(selected)!=3: raise ValueError('SP pilot name crosswalk incomplete')
  else: selected=districts.loc[districts.unit_id.isin([prefix+':'+i for i in pilots])]
  if len(selected)!=len(pilots): raise ValueError('Pilot crosswalk incomplete')
  for path in sorted((ROOT/'analysis/data'/city/'ghsl_public_2026_09_21').glob('*.tif')):
   product='ANBH' if '_ANBH_' in path.name else 'AGBH' if '_AGBH_' in path.name else 'VOLUME'
   with rasterio.open(path) as src:
    if src.crs.to_string()!='ESRI:54009' or src.res!=(100.,100.): raise ValueError('Unexpected native grid')
    data=src.read(1,masked=True)
    values=data.data.ravel(); valid=~np.ma.getmaskarray(data).ravel()
    cells=native_cells(src.transform,src.height,src.width); tree=shapely.STRtree(cells)
    receipts.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'nodata':src.nodata,'valid_zero_cells':int(((values==0)&valid).sum())})
    for district in selected.itertuples():
     gross=district.geometry
     land_geom=land.loc[land.unit_id.eq(district.unit_id)].geometry.item().intersection(gross)
     for support,geom in [('gross',gross),('land',land_geom)]:
      ids=tree.query(geom,predicate='intersects')
      areas=shapely.area(shapely.intersection(cells[ids],geom))
      q=summarize_cells(values[ids],valid[ids],areas,10000.,geom.area,product=='VOLUME')
      name=getattr(district,'district_name',getattr(district,'nm_distrito_municipal',''))
      rows.append({'unit_id':district.unit_id,'name':name,'product':product,'epoch':2020 if product=='VOLUME' else 2018,'support':support,**q,'accepted_for_model':False})
      checks.append({'check':'covered_support','unit_id':district.unit_id,'product':product,'support':support,'passed':abs(q['covered_area_m2']-geom.area)<=max(.01,geom.area*1e-8)})
     if product=='VOLUME':
      # Independent partition identity on the same selected source cells.
      ids=tree.query(gross,predicate='intersects')
      g=shapely.area(shapely.intersection(cells[ids],gross))
      l=shapely.area(shapely.intersection(cells[ids],land_geom))
      w=shapely.area(shapely.intersection(cells[ids],gross.difference(land_geom)))
      v=np.where(valid[ids],values[ids],0.)
      delta=float(np.dot(v,g-l-w)/10000.)
      checks.append({'check':'gross_land_water_volume_partition','unit_id':district.unit_id,'difference_m3':delta,'passed':abs(delta)<=max(.01,float(np.dot(v,g)/10000)*1e-8)})
   print(city,product,'done',flush=True)
 pd.DataFrame(rows).to_csv(OUT/'ghsl_pilot_attributes.csv',index=False)
 (OUT/'source_receipts.json').write_text(json.dumps(receipts,indent=2))
 (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
 if not all(c['passed'] for c in checks): raise RuntimeError('Pilot checks failed')
 (OUT/'progress.json').write_text(json.dumps({'status':'ghsl_pilot_complete_contract_partial','pilot_rows':len(rows),'checks_passed':len(checks),'strict_cross_city_accepted':False,'model_fitted':False,'running_jobs':[]},indent=2))
 print('Saved',len(rows),'rows;',len(checks),'checks passed',flush=True)

if __name__=='__main__': main()
