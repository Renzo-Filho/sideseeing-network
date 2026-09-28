import sys
import unittest
from pathlib import Path

import geopandas as gpd
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from harmonization.junctions_v2 import linked_components, short_connector_links


def fixture(ids, points, roads):
    connectors = gpd.GeoDataFrame({"id": ids}, geometry=[shapely.Point(*p) for p in points])
    edges = gpd.GeoDataFrame({"id": [x[0] for x in roads],
                              "connectors": [x[2] for x in roads]},
                             geometry=[shapely.LineString(x[1]) for x in roads])
    return connectors, edges


class JunctionComplexFixtures(unittest.TestCase):
    def test_short_connected_pair_only(self):
        c, r = fixture(["a", "b", "c"], [(0, 0), (8, 0), (9, 2)],
                       [("ab", [(0, 0), (8, 0)],
                         [{"connector_id": "a", "at": 0}, {"connector_id": "b", "at": 1}])])
        links = short_connector_links(r, c)
        self.assertEqual([(x["connector_a"], x["connector_b"]) for x in links], [("a", "b")])
        self.assertEqual(linked_components(c, links)[0]["connector_ids"], ["a", "b"])

    def test_long_link_rejected(self):
        c, r = fixture(["a", "b"], [(0, 0), (25, 0)],
                       [("ab", [(0, 0), (25, 0)],
                         [{"connector_id": "a", "at": 0}, {"connector_id": "b", "at": 1}])])
        self.assertEqual(short_connector_links(r, c), [])

    def test_near_planar_crossing_without_source_link_rejected(self):
        c, r = fixture(["a", "b"], [(0, 0), (0, 2)],
                       [("road", [(-10, 0), (10, 0)],
                         [{"connector_id": "a", "at": .5}])])
        self.assertEqual(short_connector_links(r, c), [])

    def test_chain_too_wide_flagged(self):
        c, r = fixture(["a", "b", "c"], [(0, 0), (20, 0), (40, 0)],
                       [("ab", [(0, 0), (20, 0)],
                         [{"connector_id": "a", "at": 0}, {"connector_id": "b", "at": 1}]),
                        ("bc", [(20, 0), (40, 0)],
                         [{"connector_id": "b", "at": 0}, {"connector_id": "c", "at": 1}])])
        groups = linked_components(c, short_connector_links(r, c))
        self.assertEqual(groups[0]["count"], 3)
        self.assertFalse(groups[0]["within_diameter_cap"])


if __name__ == "__main__":
    unittest.main()
