import tempfile
import unittest
from pathlib import Path

import db


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db.DATA_DIR = Path(self.temp_dir.name)
        db.DB_PATH = db.DATA_DIR / "test.sqlite3"
        db.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_project_is_created_and_saved(self):
        project = db.get_project()
        self.assertEqual(project["name"], "My Home")
        project["name"] = "Test Home"
        saved = db.save_project(project)
        self.assertEqual(saved["name"], "Test Home")
        self.assertEqual(db.get_project()["name"], "Test Home")

    def test_survey_session_and_point_round_trip(self):
        session = db.create_session("Test walk")
        point = db.add_point(session["id"], {
            "x": 2.0, "y": 3.0, "rssi_dbm": -62.0,
            "ssid": "Test Wi-Fi", "measurement_source": "manual"
        })
        self.assertEqual(point["rssi_dbm"], -62.0)
        points = db.get_points(session["id"])
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0]["ssid"], "Test Wi-Fi")
        sessions = db.list_sessions()
        self.assertEqual(sessions[0]["point_count"], 1)

    def test_missing_session_rejects_point(self):
        with self.assertRaises(LookupError):
            db.add_point(99999, {"x": 1, "y": 1, "rssi_dbm": -70})


if __name__ == "__main__":
    unittest.main()
