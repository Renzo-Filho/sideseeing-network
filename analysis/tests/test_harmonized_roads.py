import unittest,sys
from pathlib import Path
import pandas as pd
import shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.roads import connector_arms,enclosure_polygons,shape_metrics
class RoadFixtures(unittest.TestCase):
 def test_false_planar_crossing_has_no_connector(self):
  d=pd.DataFrame({'id':['bridge','under'],'connectors':[[{'connector_id':'a','at':0},{'connector_id':'b','at':1}],[{'connector_id':'c','at':0},{'connector_id':'d','at':1}]]})
  self.assertEqual(max(connector_arms(d).values()),1)
 def test_interior_t_junction_and_duplicate_link(self):
  d=pd.DataFrame({'id':['through','arm'],'connectors':[[{'connector_id':'j','at':.5},{'connector_id':'j','at':.5}],[{'connector_id':'j','at':0}]]})
  self.assertEqual(connector_arms(d)['j'],3)
 def test_closed_loop_has_two_arms(self):
  d=pd.DataFrame({'id':['loop'],'connectors':[[{'connector_id':'j','at':0},{'connector_id':'j','at':1}]]})
  self.assertEqual(connector_arms(d)['j'],2)
 def test_duplicate_ids_rejected(self):
  with self.assertRaises(ValueError): connector_arms(pd.DataFrame({'id':['a','a'],'connectors':[[],[]]}))
 def test_planar_enclosure_and_sliver_diagnostic(self):
  p=enclosure_polygons([shapely.LineString([(0,0),(100,0),(100,100),(0,100),(0,0)]),shapely.LineString([(3,0),(3,100)])])
  q=shape_metrics(p)
  self.assertEqual(len(q),2);self.assertAlmostEqual(q.area_m2.sum(),10000)
  self.assertEqual((q.rectangle_min_width_m<6).sum(),1)
if __name__=='__main__': unittest.main()
