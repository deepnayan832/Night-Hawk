"""Windows WLAN scanner and interface manager using the built-in netsh utility.

Windows netsh usually reports signal quality as a percentage. On supported modern
drivers and adapters, netsh also reports true RSSI in dBm directly in the interface
details. Where dBm is not exposed, an approximate conversion is calculated and
explicitly marked as an estimate.
"""
from __future__ import annotations

import locale
import platform
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any


def _run_netsh(args: list[str]) -> str:
    if platform.system() != "Windows":
        raise RuntimeError("Live WLAN scanning is supported on Windows 10/11.")
    if not shutil.which("netsh"):
        raise RuntimeError("netsh.exe was not found. Check the Windows PATH.")
    completed = subprocess.run(
        ["netsh", "wlan", *args],
        capture_output=True,
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
        timeout=12,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    if completed.returncode != 0 and not output.strip():
        raise RuntimeError(f"netsh exited with code {completed.returncode}")
    return output


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def _quality_to_dbm(percent: int | None) -> float | None:
    if percent is None:
        return None
    # Approximation for visual orientation only. It is not calibrated RSSI.
    return round(max(-100.0, min(-50.0, percent / 2.0 - 100.0)), 1)


def parse_interfaces(interfaces_text: str) -> list[dict[str, Any]]:
    """Parse netsh wlan show interfaces output into structured interface dictionaries."""
    interfaces: list[dict[str, Any]] = []
    # Split text into blocks per interface
    # Each interface starts with "Name                   : ..."
    lines = interfaces_text.splitlines()
    current_lines: list[str] = []

    def flush_block(block_lines: list[str]) -> None:
        if not block_lines:
            return
        block_text = "\n".join(block_lines)
        name = _field(block_text, "Name")
        if not name:
            return
        desc = _field(block_text, "Description") or ""
        guid = _field(block_text, "GUID") or ""
        mac = _field(block_text, "Physical address") or ""
        if_type = _field(block_text, "Interface type") or ""
        state = (_field(block_text, "State") or "disconnected").strip()
        ssid = _field(block_text, "SSID") or ""
        bssid = _field(block_text, "AP BSSID") or _field(block_text, "BSSID") or ""
        band = _field(block_text, "Band") or ""
        channel_str = _field(block_text, "Channel")
        channel = int(channel_str) if channel_str and channel_str.isdigit() else None
        radio_type = _field(block_text, "Radio type") or ""
        auth = _field(block_text, "Authentication") or ""
        cipher = _field(block_text, "Cipher") or ""
        conn_mode = _field(block_text, "Connection mode") or ""
        profile = _field(block_text, "Profile") or ""

        rx_rate_str = _field(block_text, "Receive rate (Mbps)")
        tx_rate_str = _field(block_text, "Transmit rate (Mbps)")
        rx_rate = float(rx_rate_str) if rx_rate_str and rx_rate_str.replace(".", "", 1).isdigit() else None
        tx_rate = float(tx_rate_str) if tx_rate_str and tx_rate_str.replace(".", "", 1).isdigit() else None

        signal_str = _field(block_text, "Signal")
        signal_match = re.search(r"(\d{1,3})\s*%", signal_str or "")
        signal_percent = int(signal_match.group(1)) if signal_match else None
        if signal_percent is not None:
            signal_percent = min(100, signal_percent)

        # Check if hardware reported true RSSI directly
        rssi_str = _field(block_text, "Rssi")
        true_rssi_dbm: float | None = None
        if rssi_str:
            rssi_match = re.search(r"(-?\d+(?:\.\d+)?)", rssi_str)
            if rssi_match:
                true_rssi_dbm = float(rssi_match.group(1))

        effective_rssi = true_rssi_dbm if true_rssi_dbm is not None else _quality_to_dbm(signal_percent)

        interfaces.append({
            "name": name,
            "description": desc,
            "guid": guid,
            "physical_address": mac,
            "interface_type": if_type,
            "state": state,
            "is_connected": state.lower() == "connected",
            "ssid": ssid,
            "bssid": bssid,
            "band": band if band else ("2.4 GHz" if channel and channel <= 14 else ("5 GHz / 6 GHz" if channel else "")),
            "channel": channel,
            "radio_type": radio_type,
            "authentication": auth,
            "cipher": cipher,
            "connection_mode": conn_mode,
            "profile": profile,
            "receive_rate_mbps": rx_rate,
            "transmit_rate_mbps": tx_rate,
            "signal_percent": signal_percent,
            "rssi_dbm": effective_rssi,
            "rssi_source": "hardware_reported" if true_rssi_dbm is not None else "percentage_estimate",
        })

    for line in lines:
        if re.match(r"^\s*Name\s*:\s*", line, re.IGNORECASE) and current_lines:
            flush_block(current_lines)
            current_lines = [line]
        else:
            current_lines.append(line)
    flush_block(current_lines)

    return interfaces


def get_interfaces() -> list[dict[str, Any]]:
    """Query live wireless interfaces via netsh wlan show interfaces."""
    interfaces_text = _run_netsh(["show", "interfaces"])
    return parse_interfaces(interfaces_text)


def scan_wifi() -> dict[str, Any]:
    interfaces_text = _run_netsh(["show", "interfaces"])
    networks_text = _run_netsh(["show", "networks", "mode=bssid"])

    parsed_ifaces = parse_interfaces(interfaces_text)
    active_iface = next((i for i in parsed_ifaces if i.get("is_connected")), parsed_ifaces[0] if parsed_ifaces else None)

    connected_ssid = active_iface["ssid"] if active_iface else ""
    connected_bssid = active_iface["bssid"] if active_iface else ""
    connected_percent = active_iface["signal_percent"] if active_iface else None
    connected_rssi = active_iface["rssi_dbm"] if active_iface else None
    connected_rssi_source = active_iface["rssi_source"] if active_iface else "percentage_estimate"

    networks: list[dict[str, Any]] = []
    ssid_name = ""
    network_auth = ""
    network_radio = ""
    current: dict[str, Any] | None = None

    def flush() -> None:
        if current and current.get("bssid"):
            networks.append(dict(current))

    for line in networks_text.splitlines():
        ssid_match = re.match(r"^\s*SSID\s+\d+\s*:\s*(.*?)\s*$", line, re.I)
        if ssid_match:
            flush()
            current = None
            ssid_name = ssid_match.group(1).strip()
            network_auth = ""
            network_radio = ""
            continue

        auth_match = re.match(r"^\s*Authentication\s*:\s*(.*?)\s*$", line, re.I)
        radio_match = re.match(r"^\s*Radio type\s*:\s*(.*?)\s*$", line, re.I)
        if auth_match:
            network_auth = auth_match.group(1).strip()
            if current is not None:
                current["authentication"] = network_auth
        if radio_match:
            network_radio = radio_match.group(1).strip()
            if current is not None:
                current["radio_type"] = network_radio

        bssid_match = re.match(r"^\s*BSSID\s+\d+\s*:\s*(.*?)\s*$", line, re.I)
        if bssid_match:
            flush()
            current = {
                "ssid": ssid_name,
                "bssid": bssid_match.group(1).strip(),
                "authentication": network_auth,
                "radio_type": network_radio,
                "signal_percent": None,
                "channel": None,
            }
            continue

        if current is None:
            continue
        signal = re.match(r"^\s*Signal\s*:\s*(\d{1,3})\s*%?", line, re.I)
        channel = re.match(r"^\s*Channel\s*:\s*(\d+)", line, re.I)
        if signal:
            current["signal_percent"] = min(100, int(signal.group(1)))
        if channel:
            current["channel"] = int(channel.group(1))

    flush()
    for item in networks:
        item["rssi_dbm_estimate"] = _quality_to_dbm(item["signal_percent"])
        channel = item.get("channel")
        item["band"] = "2.4 GHz" if channel and channel <= 14 else ("5 GHz / 6 GHz" if channel else "Unknown")
        item["is_connected"] = bool(
            connected_bssid and item["bssid"].lower() == connected_bssid.lower()
        )
    networks.sort(key=lambda item: item.get("signal_percent") or 0, reverse=True)

    return {
        "platform": platform.platform(),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "connected": {
            "ssid": connected_ssid or "",
            "bssid": connected_bssid or "",
            "signal_percent": connected_percent,
            "rssi_dbm_estimate": connected_rssi,
            "rssi_source": connected_rssi_source,
            "interface_name": active_iface["name"] if active_iface else "",
            "mac_address": active_iface["physical_address"] if active_iface else "",
        },
        "interfaces": parsed_ifaces,
        "networks": networks,
        "notes": [
            "RSSI values without direct hardware reporting are approximate conversions from Windows signal quality (%), not calibrated dBm readings.",
            "Windows display language and Wi-Fi driver versions can change netsh field labels.",
            "Windows Location privacy settings may be required to list nearby BSSIDs.",
        ],
    }

