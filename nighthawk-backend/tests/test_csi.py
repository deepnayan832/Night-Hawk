import csv
import unittest

from csi import parse_csi_line


class CSIParserTests(unittest.TestCase):
    def make_line(self, values):
        row = [""] * 26
        row[0] = "CSI_DATA"
        row[3] = "-48"
        row[25] = "[ " + " ".join(str(v) for v in values) + " ]"
        buffer = __import__("io").StringIO()
        csv.writer(buffer).writerow(row)
        return buffer.getvalue().strip()

    def test_parses_interleaved_iq_into_amplitude_and_phase(self):
        frame = parse_csi_line(self.make_line([3, 4, 0, 5]), 25)
        self.assertEqual(frame["rssi_dbm"], -48)
        self.assertEqual(frame["subcarrier_count"], 2)
        self.assertEqual(frame["amplitudes"], [5.0, 5.0])
        self.assertEqual(frame["phases_rad"][0], round(__import__("math").atan2(3, 4), 5))

    def test_rejects_non_csi_lines(self):
        self.assertIsNone(parse_csi_line("booting ESP32 serial"))

    def test_rejects_invalid_column_index(self):
        self.assertIsNone(parse_csi_line(self.make_line([1, 2, 3, 4]), 45))

    def test_custom_column_index(self):
        row = [""] * 5
        row[0] = "CSI_DATA"
        row[4] = "[ 6 8 5 12 ]"
        buffer = __import__("io").StringIO()
        csv.writer(buffer).writerow(row)
        frame = parse_csi_line(buffer.getvalue(), 4)
        self.assertEqual(frame["amplitudes"], [10.0, 13.0])


if __name__ == "__main__":
    unittest.main()
