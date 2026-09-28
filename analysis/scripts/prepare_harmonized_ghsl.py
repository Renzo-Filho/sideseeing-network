"""Full paired GHSL candidates; no model fitting or acceptance."""
from pathlib import Path
import hashlib
import zipfile
import shutil
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from harmonization.rasters import native_cells, summarize_cells
from harmonization.geometry import polygonal

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/results/SP_CHI/harmonization_2026_09_22_h1_h3/ghsl'
CITIES={
 'Chicago': ('CHI', ['24','28','30','32','76'],
 'analysis/work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet',
 'analysis/work/prepared/Chicago/chi_functional_2026_09_16_v2/district_hydro_land.parquet'),
 'SP': ('SP',['10','30','35'],
 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet',
 'analysis/work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet')}

def exact_overlap(cells,geom):
 shapely.prepare(geom)
 inside=shapely.covers(geom,cells)
 area=np.full(len(cells),10000.,dtype=float)
 area[~inside]=shapely.area(shapely.intersection(cells[~inside],geom))
 return area

def digest(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 rows=[]; receipts=[]; checks=[]; repairs=[]; recovered=[]
 for city,(prefix,pilots,district_path,land_path) in CITIES.items():
  districts=gpd.read_parquet(ROOT/district_path).to_crs('ESRI:54009')
  land=gpd.read_parquet(ROOT/land_path).to_crs('ESRI:54009')
  for label,d in [('districts',districts),('land',land)]:
   for i in d.index[~d.geometry.is_valid]:
    old=d.at[i,'geometry']; new=polygonal(old)
    repairs.append({'city':city,'layer':label,'row':int(i),'before_area_m2':old.area,'after_area_m2':new.area,'reason':shapely.is_valid_reason(old)})
    d.at[i,'geometry']=new
   if 'unit_id' not in d: d['unit_id']=prefix+':'+d.district_id.astype(str).str.zfill(2)
  for p in [ROOT/district_path,ROOT/land_path]: receipts.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p)})
  selected=districts.sort_values('unit_id')
  if len(selected)!=(96 if city=='SP' else 77): raise ValueError('Incomplete reporting geography')
  for path in sorted((ROOT/'analysis/data'/city/'ghsl_public_2026_09_21').glob('*.tif')):
   product='ANBH' if '_ANBH_' in path.name else 'AGBH' if '_AGBH_' in path.name else 'VOLUME'
   tile_handles=[]
   with rasterio.open(path) as src:
    if src.crs.to_string()!='ESRI:54009' or src.res!=(100.,100.): raise ValueError('Unexpected native grid')
    data=src.read(1,masked=True)
    values=data.data.ravel(); valid=~np.ma.getmaskarray(data).ravel()
    cells=native_cells(src.transform,src.height,src.width); tree=shapely.STRtree(cells)
    receipts.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'nodata':src.nodata,'valid_zero_cells':int(((values==0)&valid).sum())})
    for district in selected.itertuples():
     gross=polygonal(district.geometry)
     land_geom=polygonal(land.loc[land.unit_id.eq(district.unit_id)].geometry.item().intersection(gross))
     print(city,product,district.unit_id,flush=True)
     for support,geom in [('gross',gross),('land',land_geom)]:
      shapely.prepare(geom)
      ids=tree.query(geom,predicate='intersects')
      areas=exact_overlap(cells[ids],geom)
      missing_ids=ids[(~valid[ids]) & (areas>0)]
      if areas[~valid[ids]].sum() <= max(1e-4,geom.area*1e-9): missing_ids=np.array([],dtype=int)
      if len(missing_ids) and not tile_handles:
       for archive in sorted((ROOT/'analysis/data/shared/ghsl_public_2026_09_21'/path.stem).glob('*.zip')):
        cache=ROOT/'analysis/work/runs/sp_chicago_harmonization_2026_09_22/ghsl_source_cache'
        cache.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(archive) as package:
         member=next(n for n in package.namelist() if n.endswith('.tif'))
         target=cache/Path(member).name
         if not target.exists():
          partial=target.with_suffix('.tif.part')
          with package.open(member) as reader,partial.open('wb') as writer:shutil.copyfileobj(reader,writer)
          partial.replace(target)
         if target.stat().st_size!=package.getinfo(member).file_size:raise ValueError('Incomplete native source cache')
        ds=rasterio.open(target)
        tile_handles.append((archive,ds))
        receipts.append({'path':str(archive.relative_to(ROOT)),'sha256':digest(archive),'role':'source-cell recovery beyond prior city-mask support'})
      for idx in missing_ids:
       rr,cc=divmod(int(idx),src.width);x,y=src.transform*(cc+.5,rr+.5)
       for archive,ds in tile_handles:
        if ds.bounds.left<=x<ds.bounds.right and ds.bounds.bottom<y<=ds.bounds.top:
         if ds.crs!=src.crs or ds.res!=src.res: raise ValueError('Recovery grid differs')
         rawrow,rawcol=ds.index(x,y);xx,yy=ds.xy(rawrow,rawcol)
         if not np.allclose([xx,yy],[x,y],rtol=0,atol=1e-6):raise ValueError('Recovery cell alignment differs')
         sample=next(ds.sample([(x,y)],masked=True))
         if not np.ma.getmaskarray(sample)[0]:
          values[idx]=sample[0];valid[idx]=True
          recovered.append({'city':city,'product':product,'unit_id':district.unit_id,'row':rr,'col':cc,'x':x,'y':y,'source_value':float(sample[0]),'source_archive':str(archive.relative_to(ROOT))})
          break
      q=summarize_cells(values[ids],valid[ids],areas,10000.,geom.area,product=='VOLUME')
      name=getattr(district,'district_name',getattr(district,'nm_distrito_municipal',''))
      rows.append({'unit_id':district.unit_id,'name':name,'product':product,'epoch':2020 if product=='VOLUME' else 2018,'support':support,**q,'accepted_for_model':False})
      checks.append({'check':'covered_support','unit_id':district.unit_id,'product':product,'support':support,'passed':abs(q['covered_area_m2']-geom.area)<=max(.01,geom.area*1e-8)})
     if product=='VOLUME':
      # Independent partition identity on the same selected source cells.
      ids=tree.query(gross,predicate='intersects')
      g=exact_overlap(cells[ids],gross)
      l=exact_overlap(cells[ids],land_geom)
      w=exact_overlap(cells[ids],gross.difference(land_geom))
      v=np.where(valid[ids],values[ids],0.)
      delta=float(np.dot(v,g-l-w)/10000.)
      checks.append({'check':'gross_land_water_volume_partition','unit_id':district.unit_id,'difference_m3':delta,'passed':abs(delta)<=max(.01,float(np.dot(v,g)/10000)*1e-8)})
   for _,ds in tile_handles:ds.close()
   print(city,product,'done',flush=True)
 pd.DataFrame(rows).to_csv(OUT/'ghsl_attributes.csv',index=False)
 (OUT/'source_cell_recovery.json').write_text(json.dumps(recovered,indent=2))
 (OUT/'geometry_repairs.json').write_text(json.dumps(repairs,indent=2))
 (OUT/'source_receipts.json').write_text(json.dumps(receipts,indent=2))
 (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
 if not all(c['passed'] for c in checks): raise RuntimeError('Pilot checks failed')
 (OUT/'progress.json').write_text(json.dumps({'status':'full_ghsl_candidates_complete','rows':len(rows),'checks_passed':len(checks),'strict_cross_city_accepted':False,'model_fitted':False,'running_jobs':[]},indent=2))
 print('Saved',len(rows),'rows;',len(checks),'checks passed',flush=True)

if __name__=='__main__': main()
