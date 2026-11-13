import unittest

from scanplan import build_scan_plan


class ScanPlanTests(unittest.TestCase):
    def test_waypoints_cover_all_bounds_and_are_sequenced(self):
        points = build_scan_plan(1.0, 1.0, 0.5, 0.5)
        self.assertEqual(len(points), 3 * 3 * 2)
        self.assertEqual([p["sequence"] for p in points], list(range(1, len(points) + 1)))
        self.assertEqual(max(p["x"] for p in points), 1.0)
        self.assertEqual(max(p["y"] for p in points), 1.0)
        self.assertEqual(max(p["z"] for p in points), 0.5)

    def test_rejects_excessive_waypoint_count(self):
        with self.assertRaisesRegex(ValueError, "50,000"):
            build_scan_plan(100, 100, 100, 0.02)

    def test_rejects_invalid_step(self):
        with self.assertRaises(ValueError):
            build_scan_plan(2, 2, 2, 0.001)


if __name__ == "__main__":
    unittest.main()
