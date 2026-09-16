"""Small fixtures for real spatial accounting failure modes."""
import sys
import unittest
from pathlib import Path
import geopandas as gpd
import numpy as np
import shapely
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.geometry import largest_overlap, union_coverage, normalized_entropy, polygonal, exclusive_category_areas

class ChicagoGeometryTests(unittest.TestCase):
    def test_overlap_union_and_water_not_double_counted(self):
        district=shapely.box(0,0,10,10)
        buildings=gpd.GeoDataFrame(geometry=[shapely.box(0,0,6,10),shapely.box(4,0,10,10)],crs=26916)
        gross,land,summed=union_coverage(buildings,district,shapely.box(0,0,8,10),tile_m=3)
        self.assertAlmostEqual(gross,100);self.assertAlmostEqual(land,80);self.assertAlmostEqual(summed,120)
    def test_whole_object_owner_and_tie(self):
        districts=gpd.GeoDataFrame({'district_id':['02','01']},geometry=[shapely.box(5,0,10,10),shapely.box(0,0,5,10)],crs=26916)
        objects=gpd.GeoDataFrame(geometry=[shapely.box(3,1,7,3),shapely.box(4,1,8,3),shapely.box(11,0,12,1)],crs=26916)
        owners=largest_overlap(objects,districts)
        self.assertEqual(owners[0],'01');self.assertEqual(owners[1],'02');self.assertTrue(owners.isna()[2])
    def test_entropy_fixed_ontology_and_no_mass(self):
        self.assertAlmostEqual(normalized_entropy([1]*8,8),1)
        self.assertEqual(normalized_entropy([7,0,0,0,0,0,0,0],8),0)
        self.assertTrue(np.isnan(normalized_entropy([0]*8,8)))
        with self.assertRaises(ValueError):normalized_entropy([-1,2],8)
    def test_category_conflicts_are_withheld(self):
        parts=np.array([shapely.box(0,0,6,10),shapely.box(0,0,6,10),shapely.box(4,0,10,10)],dtype=object)
        areas,ambiguous=exclusive_category_areas(parts,['a','a','b'],shapely.box(0,0,10,10))
        self.assertAlmostEqual(ambiguous,20)
        self.assertEqual(areas,{'a':40,'b':40})
    def test_repair_keeps_only_area(self):
        bowtie=shapely.Polygon([(0,0),(2,2),(0,2),(2,0),(0,0)])
        repaired=polygonal(bowtie)
        self.assertTrue(repaired.is_valid);self.assertAlmostEqual(repaired.area,2)
    def test_projection_changes_degrees_to_metres(self):
        g=gpd.GeoSeries([shapely.box(-87.7,41.8,-87.699,41.801)],crs=4326).to_crs(26916)
        self.assertGreater(g.area.iloc[0],9000);self.assertLess(g.area.iloc[0],10000)

if __name__=='__main__':unittest.main()
