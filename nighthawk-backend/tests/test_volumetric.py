import unittest

from volumetric import parse_volumetric_csv, safe_source_name


class VolumetricCSVTests(unittest.TestCase):
    def test_parses_required_columns(self):
        points = parse_volumetric_csv("x,y,z,rssi_dbm\n0,0,1,-45\n1,2,3,-82\n")
        self.assertEqual(len(points), 2)
        self.assertEqual(points[1]["rssi_dbm"], -82.0)

    def test_accepts_rssi_alias(self):
        points = parse_volumetric_csv("x,y,z,rssi\n1,2,3,-60\n")
        self.assertEqual(points[0]["rssi_dbm"], -60.0)

    def test_rejects_missing_columns(self):
        with self.assertRaises(ValueError):
            parse_volumetric_csv("x,y,rssi_dbm\n1,2,-60\n")

    def test_rejects_bad_numeric_rows(self):
        with self.assertRaisesRegex(ValueError, "line 2"):
            parse_volumetric_csv("x,y,z,rssi_dbm\na,2,3,-60\n")

    def test_rejects_non_finite_or_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_volumetric_csv("x,y,z,rssi_dbm\nNaN,0,0,-60\n")

    def test_sanitizes_filename(self):
        self.assertEqual(safe_source_name("../../capture.csv"), "capture.csv")


if __name__ == "__main__":
    unittest.main()
