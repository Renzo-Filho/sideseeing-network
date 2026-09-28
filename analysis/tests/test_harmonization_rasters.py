import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.rasters import summarize_cells

class NativeRasterAccounting(unittest.TestCase):
    def test_partial_volume_conservation(self):
        # One 100 m cell split between districts and an outside residual.
        allocations=[summarize_cells([200],[True],[a],10000,a,True)['observed_allocated_mass_m3'] for a in [2500,5000,2500]]
        self.assertEqual(sum(allocations),200)
        self.assertEqual(allocations,[50,100,50])
    def test_zero_is_observed(self):
        q=summarize_cells([0,10],[True,True],[100,300],10000,400)
        self.assertEqual(q['value'],7.5)
        self.assertEqual(q['valid_area_fraction'],1)
    def test_nodata_is_not_zero_or_scaled_mass(self):
        q=summarize_cells([100,4294967295],[True,False],[5000,5000],10000,10000,True)
        self.assertIsNone(q['value'])
        self.assertEqual(q['observed_allocated_mass_m3'],50)
        self.assertEqual(q['nodata_area_m2'],5000)
    def test_height_uses_valid_area(self):
        q=summarize_cells([20,255],[True,False],[100,300],10000,400)
        self.assertEqual(q['value'],20)
        self.assertEqual(q['valid_area_fraction'],.25)
    def test_no_support(self):
        with self.assertRaises(ValueError): summarize_cells([],[],[],10000,0)
    def test_invalid_or_duplicate_areas_rejected(self):
        for overlap in [[-1],[10001],[5000,5000]]:
            with self.assertRaises(ValueError): summarize_cells(np.ones(len(overlap)),np.ones(len(overlap),bool),overlap,10000,5000)
    def test_nonfinite_valid_value_rejected(self):
        with self.assertRaises(ValueError): summarize_cells([float('nan')],[True],[100],10000,100)
    def test_absent_raster_coverage(self):
        q=summarize_cells([20],[True],[5000],10000,10000,True)
        self.assertEqual(q['outside_raster_area_m2'],5000)
        self.assertIsNone(q['value'])

if __name__=='__main__': unittest.main()
