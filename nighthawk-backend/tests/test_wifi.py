import unittest
from unittest.mock import patch

from wifi import scan_wifi


INTERFACES = """There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi Adapter
    State                  : connected
    SSID                   : TestHome
    BSSID                  : aa:bb:cc:dd:ee:ff
    Signal                 : 86%
    Radio type             : 802.11ax
"""

NETWORKS = """There are 2 networks currently visible.

SSID 1 : TestHome
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : aa:bb:cc:dd:ee:ff
         Signal              : 86%
         Radio type          : 802.11ax
         Channel             : 36
    BSSID 2                 : aa:bb:cc:dd:ee:11
         Signal              : 70%
         Radio type          : 802.11ac
         Channel             : 44
SSID 2 : Guest
    Network type            : Infrastructure
    Authentication          : WPA3-Personal
    Encryption              : CCMP
    BSSID 1                 : 11:22:33:44:55:66
         Signal              : 43%
         Channel             : 6
"""


class WindowsNetshParserTests(unittest.TestCase):
    @patch("wifi._run_netsh", side_effect=[INTERFACES, NETWORKS])
    def test_parses_multiple_bssids_and_connected_access_point(self, mocked):
        result = scan_wifi()
        self.assertEqual(result["connected"]["ssid"], "TestHome")
        self.assertEqual(len(result["networks"]), 3)
        self.assertEqual(result["networks"][0]["bssid"], "aa:bb:cc:dd:ee:ff")
        self.assertTrue(result["networks"][0]["is_connected"])
        self.assertFalse(result["networks"][1]["is_connected"])
        self.assertEqual(result["networks"][0]["channel"], 36)
        self.assertEqual(result["networks"][0]["band"], "5 GHz")
        self.assertEqual(result["networks"][2]["band"], "2.4 GHz")
        self.assertEqual(result["networks"][0]["rssi_dbm_estimate"], -57.0)
        self.assertEqual(mocked.call_count, 2)

    @patch("wifi._run_netsh", side_effect=["", "There are no networks currently visible."])
    def test_handles_no_visible_networks(self, mocked):
        result = scan_wifi()
        self.assertEqual(result["networks"], [])
        self.assertIsNone(result["connected"]["rssi_dbm_estimate"])


if __name__ == "__main__":
    unittest.main()
