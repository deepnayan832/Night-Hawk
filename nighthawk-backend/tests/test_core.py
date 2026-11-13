import unittest

from rf import fspl_db, idw_value, predict_rssi_dbm, predict_rssi_3d_dbm, segments_intersect, wall_loss_db


class RFCoreTests(unittest.TestCase):
    def test_fspl_increases_with_distance(self):
        self.assertGreater(fspl_db(10, 5000), fspl_db(1, 5000))

    def test_fspl_increases_with_frequency(self):
        self.assertGreater(fspl_db(5, 5000), fspl_db(5, 2400))

    def test_segments_intersect(self):
        self.assertTrue(segments_intersect((0, 0), (10, 10), (0, 10), (10, 0)))
        self.assertFalse(segments_intersect((0, 0), (2, 2), (3, 3), (4, 4)))

    def test_wall_attenuation_adds_loss(self):
        walls = [{"x1": 5, "y1": -1, "x2": 5, "y2": 1, "material": "brick"}]
        self.assertGreater(wall_loss_db((0, 0), (10, 0), walls, 5000), 0)

    def test_predict_rssi_decreases_with_distance(self):
        router = {"x": 0, "y": 0}
        close = predict_rssi_dbm(1, 0, router, [], 5000, 18)
        far = predict_rssi_dbm(8, 0, router, [], 5000, 18)
        self.assertGreater(close, far)

    def test_idw_exact_at_measurement(self):
        points = [{"x": 1, "y": 2, "rssi_dbm": -55}, {"x": 4, "y": 5, "rssi_dbm": -80}]
        self.assertEqual(idw_value(1, 2, points), -55.0)

    def test_idw_interpolates_between_samples(self):
        points = [{"x": 0, "y": 0, "rssi_dbm": -50}, {"x": 10, "y": 0, "rssi_dbm": -90}]
        value = idw_value(5, 0, points)
        self.assertTrue(-90 < value < -50)

    def test_3d_model_applies_floor_slab_loss(self):
        router = {"x": 2, "y": 2}
        same_floor = predict_rssi_3d_dbm(5, 5, 1, router, 2.4, [], 5000, 18, 18, 0)
        upper_floor = predict_rssi_3d_dbm(5, 5, 4.2, router, 2.4, [], 5000, 18, 18, 1)
        self.assertGreater(same_floor, upper_floor)


if __name__ == "__main__":
    unittest.main()
