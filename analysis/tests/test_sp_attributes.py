import sys,unittest
from pathlib import Path
import numpy as np,shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sp_attributes.core import block_metrics,entropy
from sp_attributes.tabular import linear_parts
class AttributeInvariants(unittest.TestCase):
 def test_square_and_rectangle_shape(self):
  a,c,e=block_metrics(np.array([shapely.box(0,0,10,10),shapely.box(0,0,20,10)],dtype=object))
  np.testing.assert_allclose(a,[100,200]);np.testing.assert_allclose(c,[np.pi/4,2*np.pi/9]);np.testing.assert_allclose(e,[1,2])
 def test_entropy_bounds_and_missing(self):
  self.assertAlmostEqual(entropy([1]*7),1);self.assertEqual(entropy([10,0,0,0,0,0,0]),0);self.assertTrue(np.isnan(entropy([0]*7)))
 def test_boundary_contacts_have_zero_length(self):
  mixed=shapely.GeometryCollection([shapely.LineString([(0,0),(10,0)]),shapely.Point(20,0)])
  shared=shapely.GeometryCollection([shapely.LineString([(5,0),(10,0)]),shapely.Point(0,0)])
  result=shapely.union_all(list(linear_parts(mixed))).difference(shapely.union_all(list(linear_parts(shared))))
  self.assertEqual(result.length,5)
 def test_self_retraced_edge_uses_geometric_length(self):
  line=shapely.LineString([(0,0),(10,0),(6,0)])
  city=shapely.box(-1,-1,11,1)
  self.assertEqual(line.length,14)
  self.assertEqual(shapely.union_all([line]).length,10)
  self.assertEqual(line.intersection(city).length,10)
 def test_disjoint_tile_union_conserves_overlap(self):
  roofs=[shapely.box(0,0,10,10),shapely.box(5,0,15,10)];tiles=[shapely.box(0,0,7,10),shapely.box(7,0,15,10)]
  tiled=sum(shapely.union_all(shapely.intersection(roofs,t)).area for t in tiles)
  self.assertEqual(tiled,150);self.assertLess(tiled,sum(x.area for x in roofs))
if __name__=='__main__':unittest.main()
