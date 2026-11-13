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

    def test_network_intelligence_endpoints(self):
        # Network Info
        info_res = self.client.get("/api/network/info")
        self.assertEqual(info_res.status_code, 200)
        data = info_res.json()
        self.assertIn("local_ip", data)
        self.assertIn("default_gateway", data)

        # Network Devices
        dev_res = self.client.get("/api/network/devices")
        self.assertEqual(dev_res.status_code, 200)
        self.assertIsInstance(dev_res.json(), list)

        # Channel Spectrum
        ch_res = self.client.get("/api/network/channels")
        self.assertEqual(ch_res.status_code, 200)
        ch_data = ch_res.json()
        self.assertIn("band_2g", ch_data)
        self.assertIn("band_5g", ch_data)

    def test_scan_history_and_exports(self):
        # Save two mock scans
        scan1 = {
            "platform": "Windows 11",
            "scanned_at": "2026-11-13T10:00:00Z",
            "connected": {"ssid": "HomeNet", "bssid": "00:11:22:33:44:55", "signal_percent": 80, "rssi_dbm_estimate": -60.0},
            "networks": [{"ssid": "HomeNet", "bssid": "00:11:22:33:44:55", "signal_percent": 80, "rssi_dbm_estimate": -60.0, "channel": 6, "band": "2.4 GHz", "radio_type": "802.11ax", "authentication": "WPA2"}]
        }
        scan2 = {
            "platform": "Windows 11",
            "scanned_at": "2026-11-13T10:02:00Z",
            "connected": {"ssid": "HomeNet", "bssid": "00:11:22:33:44:55", "signal_percent": 86, "rssi_dbm_estimate": -57.0},
            "networks": [
                {"ssid": "HomeNet", "bssid": "00:11:22:33:44:55", "signal_percent": 86, "rssi_dbm_estimate": -57.0, "channel": 6, "band": "2.4 GHz", "radio_type": "802.11ax", "authentication": "WPA2"},
                {"ssid": "Guest", "bssid": "aa:bb:cc:dd:ee:ff", "signal_percent": 50, "rssi_dbm_estimate": -75.0, "channel": 149, "band": "5 GHz", "radio_type": "802.11ac", "authentication": "WPA2"}
            ]
        }
        r1 = db.save_wifi_scan(scan1)
        r2 = db.save_wifi_scan(scan2)

        history_res = self.client.get("/api/wifi/history")
        self.assertEqual(history_res.status_code, 200)
        self.assertTrue(len(history_res.json()) >= 2)

        compare_res = self.client.get(f"/api/wifi/history/compare?baseline_id={r1['id']}&target_id={r2['id']}")
        self.assertEqual(compare_res.status_code, 200)
        diff = compare_res.json()
        self.assertEqual(diff["summary"]["common_count"], 1)
        self.assertEqual(diff["summary"]["new_count"], 1)

        csv_res = self.client.get("/api/wifi/history/export.csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn("HomeNet", csv_res.text)

        json_res = self.client.get("/api/wifi/history/export.json")
        self.assertEqual(json_res.status_code, 200)
        self.assertIn("HomeNet", json_res.text)

        del_res = self.client.delete(f"/api/wifi/history/{r1['id']}")
        self.assertEqual(del_res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
