import sys
import unittest
from pathlib import Path

from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from harmonization.road_intervals import boundary_parts


class RoadIntervalFixtures(unittest.TestCase):
    def test_scoped_bridge_level_and_link_remove_only_their_intervals(self):
        road = LineString([(0, 0), (100, 0)])
        parts = boundary_parts(
            road,
            road_flags=[{"values": ["is_bridge"], "between": [0.2, 0.4]}],
            level_rules=[{"value": -1, "between": [0.5, 0.7]}],
            subclass_rules=[{"value": "link", "between": [0.8, 1.0]}],
        )
        self.assertEqual([(round(p.bounds[0]), round(p.bounds[2])) for p in parts],
                         [(0, 20), (40, 50), (70, 80)])


    def test_unscoped_rule_removes_whole_line_and_missing_stays_candidate(self):
        road = LineString([(0, 0), (10, 0)])
        self.assertEqual(boundary_parts(road, road_flags=[{"values": ["is_tunnel"], "between": None}]), [])
        self.assertEqual(boundary_parts(road, subclass="link"), [])
        self.assertEqual(len(boundary_parts(road)), 1)


    def test_invalid_interval_fails_loudly(self):
        road = LineString([(0, 0), (10, 0)])
        with self.assertRaises(ValueError):
            boundary_parts(road, level_rules=[{"value": 1, "between": [0.7, 0.2]}])


if __name__ == "__main__":
    unittest.main()
