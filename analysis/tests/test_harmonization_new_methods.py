import unittest,sys
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.functional import supply,supply_windows
from harmonization.employment_v2 import allocate_jobs
class PairedMethods(unittest.TestCase):
 def test_shared_window_supply_retains_route_maxima(self):
  p=gpd.GeoDataFrame({'point_id':[0,1]},geometry=[shapely.Point(0,0),shapely.Point(2000,0)],crs=26916)
  stops=gpd.GeoDataFrame({'stop_id':['a','b']},geometry=[shapely.Point(10,0),shapely.Point(500,0)],crs=26916)
  service=pd.DataFrame({'stop_id':['a','b','a'],'route_id':['r','r','t'],'direction_id':['0','0','0'],'departures':[3.,5.,2.],'window':['am']*3})
  q=supply_windows(p,stops,service)
  np.testing.assert_array_equal(q[('am',400)],[5,0]);np.testing.assert_array_equal(q[('am',800)],[7,0])
  np.testing.assert_array_equal(q[('am',800)],supply(p,stops,service,800))
 def test_roundoff_normalized_and_material_error_rejected(self):
  block=shapely.box(0,0,100,100)
  parts=[('a',shapely.box(0,0,50,100)),('b',shapely.box(50-.000001,0,100,100))]
  values,_,den,_=allocate_jobs(100,block,parts,block)
  self.assertAlmostEqual(sum(values),100);self.assertGreater(den,block.area)
  with self.assertRaises(ValueError):allocate_jobs(100,block,[('a',block),('b',block)],block)
 def test_containment_shortcuts_equal_exact_overlay(self):
  from prepare_harmonized_ghsl import exact_overlap
  from prepare_harmonized_roads import clip_lines
  geom=shapely.box(0,0,200,200).difference(shapely.box(75,75,125,125))
  cells=np.array([shapely.box(0,0,100,100),shapely.box(100,100,200,200),shapely.box(150,0,250,100)])
  np.testing.assert_allclose(exact_overlap(cells,geom),[9375,9375,5000])
  lines=np.array([shapely.LineString([(0,25),(200,25)]),shapely.LineString([(-50,100),(250,100)])])
  np.testing.assert_allclose(shapely.length(clip_lines(lines,geom)),[200,150])
 def test_area_support_discards_zero_area_repair_lines(self):
  from harmonization.geometry import polygonal
  from prepare_harmonized_ghsl import exact_overlap
  raw=shapely.GeometryCollection([shapely.box(0,0,100,100),shapely.LineString([(100,100),(300,300)])])
  fixed=polygonal(raw)
  self.assertEqual(fixed.geom_type,'Polygon');self.assertEqual(fixed.area,raw.area)
  np.testing.assert_allclose(exact_overlap(np.array([shapely.box(0,0,100,100)]),fixed),[10000])
if __name__=='__main__':unittest.main()
