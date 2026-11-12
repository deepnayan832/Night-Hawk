"""Windows WLAN scanner using the built-in netsh utility.

Windows netsh usually reports signal quality as a percentage. The RSSI value
derived from that percentage is explicitly an estimate, not a calibrated dBm
measurement.
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


def scan_wifi() -> dict[str, Any]:
    interfaces_text = _run_netsh(["show", "interfaces"])
    networks_text = _run_netsh(["show", "networks", "mode=bssid"])

    connected_ssid = _field(interfaces_text, "SSID")
    connected_bssid = _field(interfaces_text, "BSSID")
    connected_signal_raw = _field(interfaces_text, "Signal")
    signal_match = re.search(r"(\d{1,3})\s*%", connected_signal_raw or "")
    connected_percent = int(signal_match.group(1)) if signal_match else None
    if connected_percent is not None:
        connected_percent = min(100, connected_percent)

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
            "rssi_dbm_estimate": _quality_to_dbm(connected_percent),
        },
        "networks": networks,
        "notes": [
            "RSSI values are approximate conversions from Windows signal quality (%), not calibrated dBm readings.",
            "Windows display language and Wi-Fi driver versions can change netsh field labels.",
            "Windows Location privacy settings may be required to list nearby BSSIDs.",
        ],
    }
