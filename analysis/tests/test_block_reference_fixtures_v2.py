import sys
import unittest
from pathlib import Path

import geopandas as gpd
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_block_reference_fixtures_v2 import match_best


class ReferenceOverlapFixtures(unittest.TestCase):
    def test_exact_and_partial_whole_polygon_iou(self):
        source = gpd.GeoDataFrame(geometry=[shapely.box(0, 0, 2, 2),
                                             shapely.box(1, 0, 3, 2)])
        target = gpd.GeoDataFrame({"reference_id": ["same"]},
                                  geometry=[shapely.box(0, 0, 2, 2)])
        ids, scores = match_best(source, target, "reference_id")
        self.assertEqual(ids, ["same", "same"])
        self.assertAlmostEqual(scores[0], 1.0)
        self.assertAlmostEqual(scores[1], 1 / 3)

    def test_unmatched_object_keeps_zero(self):
        source = gpd.GeoDataFrame(geometry=[shapely.box(5, 5, 6, 6)])
        target = gpd.GeoDataFrame({"reference_id": ["remote"]},
                                  geometry=[shapely.box(0, 0, 1, 1)])
        ids, scores = match_best(source, target, "reference_id")
        self.assertEqual(ids, [None])
        self.assertEqual(scores.tolist(), [0.0])


if __name__ == "__main__":
    unittest.main()
