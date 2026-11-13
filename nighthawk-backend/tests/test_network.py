import unittest
from wifi import parse_interfaces
from network_intel import analyze_channel_congestion, discover_local_devices, _lookup_vendor

SAMPLE_NETSH_INTERFACES = """
There is 1 interface on the system: 

    Name                   : Wi-Fi
    Description            : Realtek 8821CE Wireless LAN 802.11ac PCI-E NIC
    GUID                   : 851a099f-6f12-4e38-a377-f44dfc6f8ea0
    Physical address       : 22:bf:88:d6:f4:6a
    Interface type         : Primary
    State                  : connected
    SSID                   : Excitel_Nayan
    AP BSSID               : b4:f9:49:76:17:41
    Band                   : 5 GHz
    Channel                : 149
    Connected Akm-cipher   : [ akm = 00-0f-ac:02, cipher =  00-0f-ac:04 ]
    Network type           : Infrastructure
    Radio type             : 802.11ac
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Auto Connect
    Receive rate (Mbps)    : 390
    Transmit rate (Mbps)   : 390
    Signal                 : 100% 
    Rssi                   : -37
    Profile                : Excitel_Nayan 
"""

SAMPLE_ARP_TEXT = """
Interface: 192.168.1.41 --- 0xd
  Internet Address      Physical Address      Type
  192.168.1.1           b4-f9-49-76-17-40     dynamic   
  192.168.1.33          08-54-bb-20-77-0f     dynamic   
  192.168.1.255         ff-ff-ff-ff-ff-ff     static    
  224.0.0.22            01-00-5e-00-00-16     static    
  224.0.0.251           01-00-5e-00-00-fb     static    
  255.255.255.255       ff-ff-ff-ff-ff-ff     static    
"""


class TestNetworkIntel(unittest.TestCase):
    def test_parse_interfaces_extracts_hardware_details(self):
        ifaces = parse_interfaces(SAMPLE_NETSH_INTERFACES)
        self.assertEqual(len(ifaces), 1)
        iface = ifaces[0]
        self.assertEqual(iface["name"], "Wi-Fi")
        self.assertEqual(iface["physical_address"], "22:bf:88:d6:f4:6a")
        self.assertEqual(iface["state"], "connected")
        self.assertTrue(iface["is_connected"])
        self.assertEqual(iface["ssid"], "Excitel_Nayan")
        self.assertEqual(iface["bssid"], "b4:f9:49:76:17:41")
        self.assertEqual(iface["channel"], 149)
        self.assertEqual(iface["band"], "5 GHz")
        self.assertEqual(iface["rssi_dbm"], -37.0)
        self.assertEqual(iface["rssi_source"], "hardware_reported")
        self.assertEqual(iface["receive_rate_mbps"], 390.0)
        self.assertEqual(iface["transmit_rate_mbps"], 390.0)

    def test_vendor_oui_lookup(self):
        self.assertIn("Espressif", _lookup_vendor("08:54:bb:11:22:33"))
        self.assertIn("Apple", _lookup_vendor("f8:ff:c2:aa:bb:cc"))
        self.assertEqual(_lookup_vendor("12:34:56:78:90:ab"), "Network Device")

    def test_channel_congestion_analysis(self):
        sample_networks = [
            {"ssid": "Net1", "channel": 1, "signal_percent": 90},
            {"ssid": "Net2", "channel": 1, "signal_percent": 80},
            {"ssid": "Net3", "channel": 2, "signal_percent": 75},
            {"ssid": "Net4", "channel": 6, "signal_percent": 60},
            {"ssid": "Net5", "channel": 149, "signal_percent": 95},
        ]
        res = analyze_channel_congestion(sample_networks)
        self.assertIn("band_2g", res)
        self.assertIn("band_5g", res)
        # Channel 11 has 0 co-channel and 0 adjacent interference in sample
        self.assertEqual(res["band_2g"]["recommended_channel"], 11)
        self.assertEqual(res["band_5g"]["total_5g_networks"], 1)


if __name__ == "__main__":
    unittest.main()
