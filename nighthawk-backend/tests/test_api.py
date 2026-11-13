import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import db
from main import app


class NightHawkAPITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db.DATA_DIR = Path(self.temp_dir.name)
        db.DB_PATH = db.DATA_DIR / "api-test.sqlite3"
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_health_and_floor_aware_coverage(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        project = {
            "name": "Two floors",
            "width_m": 10,
            "height_m": 8,
            "wall_height_m": 2.7,
            "frequency_mhz": 5000,
            "tx_power_dbm": 18,
            "router": {"x": 5, "y": 4, "z": 2.4},
            "router_floor_id": "ground",
            "floors": [
                {"id": "ground", "name": "Ground", "elevation_m": 0, "width_m": 10, "height_m": 8, "wall_height_m": 2.7, "floor_loss_db": 18, "walls": []},
                {"id": "upper", "name": "Upper", "elevation_m": 3.2, "width_m": 12, "height_m": 9, "wall_height_m": 2.7, "floor_loss_db": 20, "walls": []}
            ],
            "walls": []
        }
        saved = self.client.put("/api/project", json=project)
        self.assertEqual(saved.status_code, 200, saved.text)
        predicted = self.client.get("/api/coverage/predicted?floor_id=upper&resolution=8")
        self.assertEqual(predicted.status_code, 200, predicted.text)
        self.assertEqual(predicted.json()["floor_crossings"], 1)
        self.assertEqual(predicted.json()["width_m"], 12)

    def test_survey_measurements_are_filtered_by_floor(self):
        project = self.client.get("/api/project").json()
        session = self.client.post("/api/surveys", json={"name": "Upper floor"}).json()
        point = self.client.post(
            f"/api/surveys/{session['id']}/points",
            json={"x": 3, "y": 3, "floor_id": "floor_1", "rssi_dbm": -61, "measurement_source": "manual"}
        )
        self.assertEqual(point.status_code, 201, point.text)
        coverage = self.client.get(f"/api/coverage/measured?session_id={session['id']}&floor_id=floor_1&resolution=8")
        self.assertEqual(coverage.status_code, 200, coverage.text)
        self.assertEqual(coverage.json()["point_count"], 1)

    def test_volumetric_csv_import_persists_points(self):
        body = "x,y,z,rssi_dbm\n0,0,1,-42\n1,2,3,-78\n"
        response = self.client.post(
            "/api/volumetric/import?filename=sample.csv",
            content=body,
            headers={"Content-Type": "text/csv"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["point_count"], 2)
        fetched = self.client.get("/api/volumetric/points")
        self.assertEqual(fetched.json()["point_count"], 2)


if __name__ == "__main__":
    unittest.main()
