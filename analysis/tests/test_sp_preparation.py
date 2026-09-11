"""Scientific boundary/identity tests; no model attributes are constructed."""
import importlib.util
from pathlib import Path
import unittest
import tempfile
import json
import geopandas as gpd
import shapely

spec=importlib.util.spec_from_file_location('prep',Path(__file__).resolve().parents[1]/'scripts/prepare_sp_inputs.py')
prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)

class SpatialPreparationTests(unittest.TestCase):
    def districts(self):
        return gpd.GeoDataFrame({'district_id':['01','02']},geometry=[shapely.box(0,0,10,10),shapely.box(10,0,20,10)],crs=31983)

    def test_cross_boundary_uses_largest_area_preserves_whole(self):
        g=gpd.GeoDataFrame(geometry=[shapely.box(8,1,16,4)],crs=31983)
        result=prep.assign_polygons(g,self.districts())
        self.assertEqual(result.assigned_district_id[0],'02')
        self.assertAlmostEqual(result.largest_overlap_fraction[0],.75)
        self.assertEqual(g.area[0],24)

    def test_equal_overlap_deterministic_under_district_order(self):
        g=gpd.GeoDataFrame(geometry=[shapely.box(8,1,12,4)],crs=31983)
        a=prep.assign_polygons(g,self.districts())
        b=prep.assign_polygons(g,self.districts().iloc[::-1].reset_index(drop=True))
        self.assertTrue(a.assignment_tie[0])
        self.assertEqual(a.assigned_district_id[0],b.assigned_district_id[0])

    def test_outside_or_touch_only_is_not_counted_inside(self):
        g=gpd.GeoDataFrame(geometry=[shapely.box(20,1,22,2),shapely.box(30,1,31,2)],crs=31983)
        r=prep.assign_polygons(g,self.districts())
        self.assertTrue(r.assigned_district_id.isna().all())

    def test_repair_retains_polygon_area_and_discards_collapsed_line(self):
        original=shapely.GeometryCollection([shapely.box(0,0,3,4),shapely.LineString([(5,5),(6,6)])])
        fixed=prep.polygon_only(original)
        self.assertEqual(fixed.area,12)
        self.assertTrue(fixed.is_valid)

    def test_geometry_identity_invariant_to_ring_direction(self):
        p=shapely.box(0,0,3,4)
        self.assertEqual(shapely.to_wkb(shapely.normalize(p)),shapely.to_wkb(shapely.normalize(shapely.reverse(p))))

    def test_checkpoint_rejects_changed_missing_or_wrong_fingerprint(self):
        old=prep.OUT
        try:
            with tempfile.TemporaryDirectory() as directory:
                prep.OUT=Path(directory)
                artifact=prep.OUT/'artifact.txt';artifact.write_text('complete')
                checkpoint=prep.OUT/'checkpoint.json'
                checkpoint.write_text(json.dumps({'fingerprint':'abc','outputs':{'artifact.txt':prep.sha(artifact)}}))
                self.assertTrue(prep.checkpoint_valid(checkpoint,'abc'))
                self.assertFalse(prep.checkpoint_valid(checkpoint,'different'))
                artifact.write_text('corrupted')
                self.assertFalse(prep.checkpoint_valid(checkpoint,'abc'))
                artifact.unlink()
                self.assertFalse(prep.checkpoint_valid(checkpoint,'abc'))
        finally:
            prep.OUT=old

    def test_scope_excludes_removed_families_and_features(self):
        self.assertEqual(len(prep.CFG['active_families']),13)
        self.assertFalse(prep.CFG['attribute_construction_authorized'])
        self.assertFalse({'M5','U5'} & set(prep.CFG['active_families']))

if __name__=='__main__': unittest.main()
