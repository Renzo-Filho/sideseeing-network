"""Small accounting and service-policy counterexamples."""
import datetime as dt
from pathlib import Path
import sys
import unittest
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box, Point
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from harmonization.functional import active_services, allocate, population_grid, seconds, supply

class FunctionalTests(unittest.TestCase):
    def test_border_mass_and_grid(self):
        blocks=gpd.GeoDataFrame({'GEOID20':['a'],'POP20':[120],'jobs':[30]},geometry=[box(0,0,600,100)],crs=26916)
        districts=gpd.GeoDataFrame({'unit_id':['CHI:01','CHI:02']},geometry=[box(0,0,200,100),box(200,0,400,100)],crs=26916)
        p=allocate(blocks,districts)
        np.testing.assert_allclose(p.population_allocated,[40,40])
        self.assertAlmostEqual(p.jobs_allocated.sum(),20)
        grid=population_grid(p)
        self.assertAlmostEqual(grid.population_weight.sum(),80)
        self.assertTrue(all(districts.geometry.union_all().covers(x) for x in grid.geometry))

    def test_overlapping_districts_rejected(self):
        b=gpd.GeoDataFrame({'GEOID20':['a'],'POP20':[100],'jobs':[4]},geometry=[box(0,0,10,10)],crs=26916)
        d=gpd.GeoDataFrame({'unit_id':['a','b']},geometry=[box(0,0,10,10)]*2,crs=26916)
        with self.assertRaises(ValueError): allocate(b,d)

    def test_stop_max_not_sum_and_direction_addition(self):
        p=gpd.GeoDataFrame({'point_id':[0,1]},geometry=[Point(0,0),Point(2000,0)],crs=26916)
        s=gpd.GeoDataFrame({'stop_id':['a','b','c']},geometry=[Point(100,0),Point(200,0),Point(700,0)],crs=26916)
        svc=pd.DataFrame({'stop_id':['a','b','a','c'],'route_id':['r']*4,'direction_id':['0','0','1','0'],'departures':[3,5,2,9]})
        np.testing.assert_equal(supply(p,s,svc,400),[7,0])
        np.testing.assert_equal(supply(p,s,svc,800),[11,0])

    def test_calendar_add_remove_and_boundaries(self):
        cal=pd.DataFrame({'service_id':['regular'],'start_date':['20260901'],'end_date':['20260930'],'wednesday':['1']})
        ex=pd.DataFrame({'service_id':['regular','special'],'date':['20260916']*2,'exception_type':['2','1']})
        self.assertEqual(active_services(cal,ex,dt.date(2026,9,16)),{'special'})
        self.assertEqual(active_services(cal,ex,dt.date(2026,10,7)),set())

    def test_after_midnight_not_wrapped(self):
        np.testing.assert_equal(seconds(pd.Series(['07:00:00','25:30:00'])),[25200,91800])
        with self.assertRaises(ValueError): seconds(pd.Series(['12:61:00']))

if __name__=='__main__': unittest.main()
