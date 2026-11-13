import tempfile
import unittest
from pathlib import Path

import db


class TestScanHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db.DATA_DIR = Path(self.temp_dir.name)
        db.DB_PATH = db.DATA_DIR / "history-test.sqlite3"
        db.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_list_scans(self):
        scan_a = {
            "platform": "Windows 11",
            "scanned_at": "2026-11-13T10:00:00Z",
            "connected": {
                "ssid": "Excitel_Nayan",
                "bssid": "b4:f9:49:76:17:41",
                "signal_percent": 90,
                "rssi_dbm_estimate": -45.0,
            },
            "networks": [
                {
                    "ssid": "Excitel_Nayan",
                    "bssid": "b4:f9:49:76:17:41",
                    "signal_percent": 90,
                    "rssi_dbm_estimate": -45.0,
                    "channel": 149,
                    "band": "5 GHz",
                    "radio_type": "802.11ac",
                    "authentication": "WPA2-Personal",
                    "is_connected": True,
                },
                {
                    "ssid": "Neighbor_2G",
                    "bssid": "aa:bb:cc:dd:ee:01",
                    "signal_percent": 50,
                    "rssi_dbm_estimate": -75.0,
                    "channel": 6,
                    "band": "2.4 GHz",
                    "radio_type": "802.11n",
                    "authentication": "WPA2-Personal",
                    "is_connected": False,
                },
            ],
        }
        res_a = db.save_wifi_scan(scan_a)
        self.assertEqual(res_a["network_count"], 2)
        scan_id_a = res_a["id"]

        history = db.list_wifi_scans()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["connected_ssid"], "Excitel_Nayan")

        # Scan B: Signal improved on Excitel, Neighbor disappeared, NewGuest appeared
        scan_b = {
            "platform": "Windows 11",
            "scanned_at": "2026-11-13T10:05:00Z",
            "connected": {
                "ssid": "Excitel_Nayan",
                "bssid": "b4:f9:49:76:17:41",
                "signal_percent": 96,
                "rssi_dbm_estimate": -40.0,
            },
            "networks": [
                {
                    "ssid": "Excitel_Nayan",
                    "bssid": "b4:f9:49:76:17:41",
                    "signal_percent": 96,
                    "rssi_dbm_estimate": -40.0,
                    "channel": 149,
                    "band": "5 GHz",
                    "radio_type": "802.11ac",
                    "authentication": "WPA2-Personal",
                    "is_connected": True,
                },
                {
                    "ssid": "NewGuest_AP",
                    "bssid": "11:22:33:44:55:66",
                    "signal_percent": 70,
                    "rssi_dbm_estimate": -65.0,
                    "channel": 11,
                    "band": "2.4 GHz",
                    "radio_type": "802.11ax",
                    "authentication": "WPA3-Personal",
                    "is_connected": False,
                },
            ],
        }
        res_b = db.save_wifi_scan(scan_b)
        scan_id_b = res_b["id"]

        # Diff Scans
        diff = db.compare_wifi_scans(scan_id_a, scan_id_b)
        self.assertEqual(diff["summary"]["common_count"], 1)
        self.assertEqual(diff["summary"]["new_count"], 1)
        self.assertEqual(diff["summary"]["lost_count"], 1)
        self.assertEqual(diff["new_networks"][0]["ssid"], "NewGuest_AP")
        self.assertEqual(diff["lost_networks"][0]["ssid"], "Neighbor_2G")
        self.assertEqual(diff["persistent_networks"][0]["delta_rssi_dbm"], 5.0)

        # Delete Scan
        deleted = db.delete_wifi_scan(scan_id_a)
        self.assertTrue(deleted)
        self.assertEqual(len(db.list_wifi_scans()), 1)


if __name__ == "__main__":
    unittest.main()
