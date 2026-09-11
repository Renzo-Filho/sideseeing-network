"""Boundary and frequency conservation tests for preparation, not model attributes."""
import sys,unittest,tempfile,json
from pathlib import Path
import numpy as np,geopandas as gpd,shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sp_v3 import common as C
from sp_v3.transit import time_seconds,expected_frequency

class PreparationInvariants(unittest.TestCase):
 def test_extended_service_day(self):
  self.assertEqual(time_seconds('25:30:00'),91800)
  self.assertTrue(np.isnan(time_seconds('24:61:00')))
 def test_frequency_partition_conserves_service(self):
  # 60 departures/hour, window clipping and downstream offsets.
  full=expected_frequency(0,3600,60,0,0,3600)
  halves=sum(expected_frequency(0,3600,60,0,a,b) for a,b in [(0,1800),(1800,3600)])
  self.assertEqual(full,60);self.assertEqual(full,halves)
  self.assertEqual(expected_frequency(0,3600,60,600,0,3600),50)
  self.assertEqual(expected_frequency(0,3600,60,0,3600,7200),0)
 def test_whole_entity_once_and_boundary_touch_excluded(self):
  d=gpd.GeoDataFrame({'district_id':['01','02']},geometry=[shapely.box(0,0,10,10),shapely.box(10,0,20,10)],crs=31983)
  g=gpd.GeoDataFrame(geometry=[shapely.box(8,1,14,3),shapely.box(20,1,21,3),shapely.box(9,1,11,3)],crs=31983)
  result=C.assign(g,d)
  self.assertEqual(result.district_id.iloc[0],'02');self.assertEqual(result.inside_area_m2.iloc[0],12)
  self.assertTrue(result.district_id.isna().iloc[1]);self.assertEqual(result.inside_area_m2.iloc[1],0)
  self.assertEqual(result.district_id.iloc[2],'01');self.assertEqual(result.district_candidates.iloc[2],2)
 def test_baseline_and_path_escape_rejected(self):
  original=(C.CFG,C.OUT,C.BASE)
  cfg=json.loads((C.ROOT/'analysis/config/sp_preparation_v3.json').read_text())
  try:
   with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'config.json'
    for run in [cfg['baseline_run_id'],'../outside']:
     cfg['run_id']=run;path.write_text(json.dumps(cfg))
     with self.assertRaises(ValueError):C.initialize(path)
  finally:C.CFG,C.OUT,C.BASE=original
if __name__=='__main__':unittest.main()
