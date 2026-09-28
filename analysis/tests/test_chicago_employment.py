"""Counterexamples for whole-block ancillary employment support."""
from pathlib import Path
import sys,unittest
import numpy as np
from shapely.geometry import box,Polygon
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.employment import exclusive_support,partition_block,allocate_jobs

class EmploymentTests(unittest.TestCase):
    def test_outside_workplace_support_is_not_lost(self):
        block=box(0,0,10,10);parts=partition_block(block,[('CHI:01',box(0,0,5,10))])
        values,_,_,fallback=allocate_jobs(100,block,parts,box(8,0,10,10))
        np.testing.assert_allclose(values,[0,100]);self.assertFalse(fallback)

    def test_zero_support_gross_fallback(self):
        block=box(0,0,10,10);parts=partition_block(block,[('CHI:01',box(0,0,2,10))])
        values,_,den,fallback=allocate_jobs(50,block,parts,Polygon())
        np.testing.assert_allclose(values,[10,40]);self.assertTrue(fallback);self.assertEqual(den,100)

    def test_same_code_duplicates_and_conflicting_excluded_use(self):
        block=box(0,0,10,10)
        support,covered,ambiguous=exclusive_support([block,block,box(0,0,4,10)],['1215','1215','1111'],block,['12'])
        self.assertEqual(support.area,60);self.assertEqual(covered,100);self.assertEqual(ambiguous,40)

    def test_transport_extension_changes_support_not_job_mass(self):
        block=box(0,0,10,10);parts=partition_block(block,[('CHI:01',box(0,0,5,10))])
        geoms=[box(0,0,2,10),box(8,0,10,10)];codes=['1215','1511']
        core,_,_=exclusive_support(geoms,codes,block,['12','13','14'])
        broad,_,_=exclusive_support(geoms,codes,block,['12','13','14','15'])
        np.testing.assert_allclose(allocate_jobs(80,block,parts,core)[0],[80,0])
        np.testing.assert_allclose(allocate_jobs(80,block,parts,broad)[0],[40,40])

    def test_overlap_ownership_preserves_partition(self):
        block=box(0,0,10,10);parts=partition_block(block,[('CHI:02',block),('CHI:01',box(0,0,4,10))])
        self.assertEqual([p[0] for p in parts],['CHI:01','CHI:02','OUTSIDE_CHICAGO'])
        np.testing.assert_allclose(allocate_jobs(10,block,parts,block)[0],[4,6,0])

    def test_touching_codes_have_no_ambiguous_area(self):
        block=box(0,0,10,10)
        support,covered,ambiguous=exclusive_support([box(0,0,5,10),box(5,0,10,10)],['1215','1111'],block,['12'])
        self.assertEqual(support.area,50);self.assertEqual(covered,100);self.assertEqual(ambiguous,0)

    def test_no_eligible_code_with_excluded_overlap(self):
        block=box(0,0,10,10)
        support,covered,ambiguous=exclusive_support([block,box(0,0,5,10)],['1111','1112'],block,['12'])
        self.assertTrue(support.is_empty);self.assertEqual(ambiguous,50)

    def test_missing_partition_and_invalid_jobs_fail(self):
        block=box(0,0,10,10)
        with self.assertRaises(ValueError):allocate_jobs(10,block,[('CHI:01',box(0,0,2,10))],block)
        with self.assertRaises(ValueError):allocate_jobs(-1,block,[('OUTSIDE_CHICAGO',block)],block)

if __name__=='__main__':unittest.main()
