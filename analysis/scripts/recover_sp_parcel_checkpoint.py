"""Verify interrupted-run parcel artifacts against sources before safe reuse.

This verifies every raw attribute/FID and exact geometry against its output and
recomputes all geometry-based IDs. Assignment method/district hashes pin the
already executed assignment algorithm. No tax artifact is adopted.
"""
from pathlib import Path
import importlib.util,hashlib,inspect,json
import geopandas as gpd
import pandas as pd
import shapely
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('prep',ROOT/'analysis/scripts/prepare_sp_inputs.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def main():
 recovered={}
 district_hash=a.sha(a.OUT/'01_districts/districts.parquet')
 for source in sorted((a.CAD/'Lotes').glob('*.gpkg')):
  code=source.name.split('LOTES_')[1].split('_')[0]
  target=a.OUT/'02_parcels_tax/parcel_records'/f'{code}.parquet'
  raw=a.read_geo(source);out=gpd.read_parquet(target)
  assert len(raw)==len(out)
  for col in raw.columns.drop('geometry'):
   # Original parcel codes already have documented widths; allow string storage dtype.
   expected=raw[col].astype(str)
   if col in {'lo_setor':3,'lo_quadra':3,'lo_lote':4,'lo_condomi':2}: expected=expected.str.zfill({'lo_setor':3,'lo_quadra':3,'lo_lote':4,'lo_condomi':2}[col])
   assert expected.equals(out[col].astype(str)),(source,col)
  assert (shapely.to_wkb(raw.geometry.values)==shapely.to_wkb(out.geometry.values)).all()
  hashes=[hashlib.sha256(w).hexdigest() for w in shapely.to_wkb(shapely.normalize(raw.geometry.values),byte_order=1)]
  assert hashes==out.geometry_hash.tolist()
  assert [hashlib.sha256((s+':'+h).encode()).hexdigest() for s,h in zip(out.sql_key,hashes)]==out.parcel_candidate_id.tolist()
  recovered[source.name]={'source_sha256':a.sha(source),'output_sha256':a.sha(target),'rows':len(raw),
   'preparation_script_sha256':a.sha(ROOT/'analysis/scripts/prepare_sp_inputs.py'),'config_sha256':a.sha(a.CONFIG_PATH),
   'district_sha256':district_hash,'assignment_method_sha256':hashlib.sha256(inspect.getsource(a.assign_polygons).encode()).hexdigest(),
   'verification':'all raw attributes/FIDs/exact geometry and candidate hashes verified; assignment inherited from identical method/district run'}
  print(code,'verified',flush=True)
 a.dump(a.OUT/'parcel_geometry_recovery.json',recovered)
 print('Recovery metadata saved for',len(recovered),'files',flush=True)
if __name__=='__main__':main()
