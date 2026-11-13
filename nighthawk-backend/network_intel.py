"""Project NightHawk - Network Intelligence, Gateway Diagnostics & Device Discovery.

Performs:
- Local IP, Subnet Mask, Default Gateway & DNS extraction via Windows ipconfig
- Gateway ping latency and packet loss measurement
- Local subnet device discovery via Windows ARP table
- RF Channel utilization, co-channel & adjacent-channel interference analysis
"""
from __future__ import annotations

import locale
import platform
import re
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any


def _run_cmd(cmd: list[str], timeout: int = 8) -> str:
    """Safely execute a system command without opening a console window."""
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return (completed.stdout or "") + "\n" + (completed.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_network_info() -> dict[str, Any]:
    """Retrieve host IP configuration, default gateway, and connection latency."""
    ipconfig_text = _run_cmd(["ipconfig", "/all"], timeout=6)
    
    local_ip = ""
    subnet_mask = ""
    gateway_ip = ""
    dns_suffix = ""
    dns_servers: list[str] = []
    
    # Extract from ipconfig text
    # We look for the active Wi-Fi or primary adapter block
    current_adapter = ""
    in_target_adapter = False
    
    lines = ipconfig_text.splitlines()
    for line in lines:
        adapter_match = re.match(r"^(\S.*?adapter.*?):", line, re.I)
        if adapter_match:
            current_adapter = adapter_match.group(1).strip()
            # Prefer Wi-Fi or Wireless LAN adapter
            if "wi-fi" in current_adapter.lower() or "wireless" in current_adapter.lower():
                in_target_adapter = True
            elif not local_ip:
                in_target_adapter = True
            else:
                in_target_adapter = False
            continue
            
        if not in_target_adapter and local_ip:
            continue
            
        ip_match = re.search(r"IPv4 Address[.\s]*:\s*([0-9.]+)", line, re.I)
        if ip_match and not local_ip:
            local_ip = ip_match.group(1).strip()
            
        subnet_match = re.search(r"Subnet Mask[.\s]*:\s*([0-9.]+)", line, re.I)
        if subnet_match and not subnet_mask:
            subnet_mask = subnet_match.group(1).strip()
            
        gw_match = re.search(r"Default Gateway[.\s]*:\s*([0-9.]+)", line, re.I)
        if gw_match and not gateway_ip:
            candidate = gw_match.group(1).strip()
            if candidate != "0.0.0.0":
                gateway_ip = candidate
                
        dns_match = re.search(r"DNS Servers[.\s]*:\s*([0-9.]+)", line, re.I)
        if dns_match:
            dns_servers.append(dns_match.group(1).strip())
            
        suffix_match = re.search(r"Connection-specific DNS Suffix[.\s]*:\s*(.*)", line, re.I)
        if suffix_match and not dns_suffix:
            dns_suffix = suffix_match.group(1).strip()

    # Ping latency to gateway
    ping_latency_ms: float | None = None
    packet_loss_pct = 0.0
    gateway_reachable = False
    
    if gateway_ip:
        ping_output = _run_cmd(["ping", "-n", "2", "-w", "1000", gateway_ip], timeout=4)
        loss_match = re.search(r"\((\d+)%\s*loss\)", ping_output, re.I)
        if loss_match:
            packet_loss_pct = float(loss_match.group(1))
        avg_match = re.search(r"Average\s*=\s*(\d+)\s*ms", ping_output, re.I)
        if avg_match:
            ping_latency_ms = float(avg_match.group(1))
            gateway_reachable = packet_loss_pct < 100.0

    # Quick internet reachability check (DNS resolution)
    internet_reachable = False
    try:
        socket.setdefaulttimeout(1.5)
        socket.gethostbyname("dns.google")
        internet_reachable = True
    except (socket.error, OSError):
        internet_reachable = False

    return {
        "local_ip": local_ip or "127.0.0.1",
        "subnet_mask": subnet_mask or "255.255.255.0",
        "default_gateway": gateway_ip or "Unavailable",
        "dns_servers": dns_servers if dns_servers else ["Auto / DHCP"],
        "dns_suffix": dns_suffix,
        "gateway_ping_ms": ping_latency_ms,
        "gateway_packet_loss_percent": packet_loss_pct,
        "gateway_reachable": gateway_reachable,
        "internet_reachable": internet_reachable,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# Known MAC Organizationally Unique Identifier (OUI) prefixes
_VENDOR_OUI: dict[str, str] = {
    "08:54:bb": "Espressif Systems (IoT)",
    "24:0a:c4": "Espressif Systems (IoT)",
    "30:ae:a4": "Espressif Systems (IoT)",
    "b4:f9:49": "Broadcom / Wi-Fi Gateway",
    "22:bf:88": "Realtek Semiconductor",
    "00:1a:2b": "Cisco Systems",
    "00:50:56": "VMware Virtual NIC",
    "f8:ff:c2": "Apple Inc.",
    "a4:83:e7": "Apple Inc.",
    "3c:22:fb": "Apple Inc.",
    "e4:5f:01": "Raspberry Pi Foundation",
    "dc:a6:32": "Raspberry Pi Foundation",
    "b8:27:eb": "Raspberry Pi Foundation",
    "50:c7:bf": "TP-Link Technologies",
    "c0:06:c3": "TP-Link Technologies",
    "a0:04:60": "Netgear Inc.",
    "28:80:23": "Netgear Inc.",
    "00:17:88": "Philips Hue Bridge",
}


def _lookup_vendor(mac: str) -> str:
    cleaned = mac.lower().replace("-", ":")
    prefix = cleaned[:8]
    if prefix in _VENDOR_OUI:
        return _VENDOR_OUI[prefix]
    # Check 2-byte prefix if needed or fallback
    return "Network Device"


def discover_local_devices(gateway_ip: str | None = None) -> list[dict[str, Any]]:
    """Safe passive/active device discovery via the Windows ARP table."""
    arp_text = _run_cmd(["arp", "-a"], timeout=5)
    devices: list[dict[str, Any]] = []
    
    current_interface_ip = ""
    for line in arp_text.splitlines():
        iface_match = re.search(r"Interface:\s*([0-9.]+)", line, re.I)
        if iface_match:
            current_interface_ip = iface_match.group(1).strip()
            continue
            
        entry_match = re.search(
            r"^\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9a-fA-F-]{17})\s+(\S+)",
            line
        )
        if not entry_match:
            continue
            
        ip = entry_match.group(1).strip()
        mac = entry_match.group(2).strip().lower().replace("-", ":")
        entry_type = entry_match.group(3).strip().lower()
        
        # Filter out multicast (224.0.0.0 to 239.255.255.255) and subnet broadcast (.255)
        first_octet = int(ip.split(".")[0])
        last_octet = int(ip.split(".")[3])
        if 224 <= first_octet <= 239 or last_octet in (0, 255):
            continue
            
        is_gw = bool(gateway_ip and ip == gateway_ip)
        vendor = "Default Gateway" if is_gw else _lookup_vendor(mac)
        
        devices.append({
            "ip": ip,
            "mac": mac,
            "type": entry_type,
            "vendor": vendor,
            "is_gateway": is_gw,
            "is_local_host": ip == current_interface_ip,
            "status": "online",
        })
        
    devices.sort(key=lambda d: (not d["is_gateway"], [int(p) for p in d["ip"].split(".")]))
    return devices


def analyze_channel_congestion(networks: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Evaluates 2.4 GHz and 5 GHz channel congestion, co-channel interference,
    and adjacent-channel overlaps.
    """
    # 2.4 GHz primary channels
    ch_2g_counts: dict[int, int] = {c: 0 for c in range(1, 15)}
    ch_2g_networks: dict[int, list[str]] = {c: [] for c in range(1, 15)}
    
    # 5 GHz channels
    ch_5g_counts: dict[int, int] = {}
    ch_5g_networks: dict[int, list[str]] = {}
    
    for net in networks:
        channel = net.get("channel")
        ssid = net.get("ssid") or "Hidden Network"
        if not channel or not isinstance(channel, int):
            continue
            
        if 1 <= channel <= 14:
            ch_2g_counts[channel] = ch_2g_counts.get(channel, 0) + 1
            ch_2g_networks[channel].append(ssid)
        else:
            ch_5g_counts[channel] = ch_5g_counts.get(channel, 0) + 1
            if channel not in ch_5g_networks:
                ch_5g_networks[channel] = []
            ch_5g_networks[channel].append(ssid)

    # In 2.4 GHz, non-overlapping channels are 1, 6, 11
    # Adjacent channel interference:
    # A network on ch 2 causes interference to 1 and 6
    # A network on ch 3 causes interference to 1 and 6
    def calculate_2g_interference_score(target_ch: int) -> float:
        score = ch_2g_counts.get(target_ch, 0) * 2.0  # Co-channel weight
        # Adjacent overlap channels within 4 channels distance
        for c in range(max(1, target_ch - 4), min(15, target_ch + 5)):
            if c != target_ch:
                dist = abs(c - target_ch)
                weight = (5 - dist) / 5.0
                score += ch_2g_counts.get(c, 0) * weight
        return round(score, 2)

    scores_2g = {
        1: calculate_2g_interference_score(1),
        6: calculate_2g_interference_score(6),
        11: calculate_2g_interference_score(11),
    }
    
    best_2g_channel = min(scores_2g, key=scores_2g.get)
    
    # Format 2.4G spectrum data for UI charts
    spectrum_2g = [
        {
            "channel": c,
            "count": ch_2g_counts.get(c, 0),
            "ssids": ch_2g_networks.get(c, []),
            "is_standard": c in (1, 6, 11),
            "interference_score": calculate_2g_interference_score(c),
        }
        for c in range(1, 14)
    ]
    
    # Format 5G spectrum data
    common_5g = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
    spectrum_5g = [
        {
            "channel": c,
            "count": ch_5g_counts.get(c, 0),
            "ssids": ch_5g_networks.get(c, []),
            "band": "UNII-1" if c <= 48 else ("UNII-2 (DFS)" if c <= 64 else ("UNII-2e (DFS)" if c <= 144 else "UNII-3")),
        }
        for c in common_5g
        if ch_5g_counts.get(c, 0) > 0 or c in (36, 44, 149, 157)
    ]
    spectrum_5g.sort(key=lambda x: x["channel"])
    
    best_5g_channel = 36
    if spectrum_5g:
        # Find 5G channel with lowest count
        best_5g_channel = min(spectrum_5g, key=lambda x: x["count"])["channel"]

    return {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "total_networks_analyzed": len(networks),
        "band_2g": {
            "recommended_channel": best_2g_channel,
            "recommended_channels_ranked": sorted(scores_2g.keys(), key=lambda k: scores_2g[k]),
            "interference_scores": scores_2g,
            "spectrum": spectrum_2g,
        },
        "band_5g": {
            "recommended_channel": best_5g_channel,
            "total_5g_networks": sum(ch_5g_counts.values()),
            "spectrum": spectrum_5g,
        },
        "tips": [
            f"For 2.4 GHz, Channel {best_2g_channel} has the lowest detected co-channel and adjacent interference.",
            "Only channels 1, 6, and 11 in the 2.4 GHz band do not overlap with one another.",
            "5 GHz channels have 20/40/80 MHz non-overlapping spacing and provide higher throughput with lower interference.",
        ],
    }
