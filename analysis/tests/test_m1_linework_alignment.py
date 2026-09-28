import sys
import unittest
from pathlib import Path
import shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_m1_geometry_alignment_v1 import sampled_near_fractions

class LineworkSamplingFixture(unittest.TestCase):
    def test_parallel_lines_and_partial_match(self):
        source=[shapely.LineString([(0,0),(100,0)])]
        parallel=[shapely.LineString([(0,10),(100,10)])]
        result=sampled_near_fractions(source,parallel,spacing_m=10)
        self.assertEqual(result[5],0)
        self.assertEqual(result[15],1)
        partial=[shapely.LineString([(0,0),(50,0)])]
        result=sampled_near_fractions(source,partial,spacing_m=10)
        self.assertAlmostEqual(result[5],.5)

if __name__=='__main__':unittest.main()
