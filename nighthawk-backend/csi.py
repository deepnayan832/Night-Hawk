"""Optional ESP32 CSI serial collector.

Supports the CSV layout used by StevenMHernandez/ESP32-CSI-Tool where the
space-separated interleaved I/Q vector is in field 25. The index is configurable
because forks/firmware versions can alter metadata columns. No synthetic frames
are generated: a disconnected device reports disconnected.
"""
from __future__ import annotations

import csv
import math
import re
import statistics
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any


def parse_csi_line(line: str, csi_column: int = 25) -> dict[str, Any] | None:
    if "CSI_DATA" not in line:
        return None
    try:
        row = next(csv.reader([line], skipinitialspace=True))
    except (csv.Error, StopIteration):
        return None
    if not row or "CSI_DATA" not in row[0]:
        return None
    if csi_column < 1 or csi_column >= len(row):
        return None

    raw = row[csi_column].strip().strip('"').strip()
    raw = raw.replace("[", " ").replace("]", " ").replace(";", " ")
    values = re.findall(r"-?\d+", raw)
    if len(values) < 4 or len(values) % 2:
        return None
    numbers = [int(value) for value in values]
    # ESP32-CSI-Tool's live plot parser treats adjacent values as I/Q pairs.
    amplitudes: list[float] = []
    phases: list[float] = []
    for index in range(0, len(numbers), 2):
        imag, real = numbers[index], numbers[index + 1]
        amplitudes.append(round(math.hypot(imag, real), 3))
        phases.append(round(math.atan2(imag, real), 5))
    if not amplitudes:
        return None

    rssi: int | None = None
    if len(row) > 3:
        try:
            rssi = int(row[3].strip())
        except ValueError:
            pass
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rssi_dbm": rssi,
        "subcarrier_count": len(amplitudes),
        "amplitudes": amplitudes,
        "phases_rad": phases,
    }


class CSICollector:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._serial = None
        self._state = "disconnected"
        self._error: str | None = None
        self._port: str | None = None
        self._baud = 921600
        self._column = 25
        self._frames: deque[dict[str, Any]] = deque(maxlen=120)
        self._received = 0
        self._started_at: float | None = None

    def ports(self) -> list[dict[str, str]]:
        try:
            from serial.tools import list_ports
        except ImportError as exc:
            raise RuntimeError("pyserial is not installed. Run setup.ps1.") from exc
        return [
            {"device": item.device, "description": item.description or item.device,
             "hwid": item.hwid or ""}
            for item in list_ports.comports()
        ]

    def start(self, port: str, baud: int = 921600, csi_column: int = 25) -> dict[str, Any]:
        port = port.strip()
        if not port or len(port) > 128:
            raise ValueError("Select a valid serial port.")
        if baud not in {115200, 230400, 460800, 921600, 1000000, 1500000}:
            raise ValueError("Unsupported baud rate.")
        if not 1 <= csi_column <= 80:
            raise ValueError("CSI field index must be between 1 and 80.")
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("A CSI serial session is already running.")
            self._stop.clear()
            self._state = "connecting"
            self._error = None
            self._port = port
            self._baud = baud
            self._column = csi_column
            self._frames.clear()
            self._received = 0
            self._started_at = time.time()
            self._thread = threading.Thread(target=self._read_loop, name="NightHawk-CSI", daemon=True)
            self._thread.start()
        return self.status()

    def _read_loop(self) -> None:
        try:
            import serial
            connection = serial.Serial(self._port, self._baud, timeout=0.5)
            with self._lock:
                self._serial = connection
                self._state = "connected"
            while not self._stop.is_set():
                raw = connection.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                frame = parse_csi_line(line, self._column)
                if frame is None:
                    continue
                with self._lock:
                    self._frames.append(frame)
                    self._received += 1
        except Exception as exc:
            with self._lock:
                self._error = str(exc)
                self._state = "error"
        finally:
            with self._lock:
                connection = self._serial
                self._serial = None
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
            with self._lock:
                if self._state != "error":
                    self._state = "disconnected"

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        with self._lock:
            connection = self._serial
            thread = self._thread
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            if not thread or not thread.is_alive():
                self._state = "disconnected" if self._state != "error" else self._state
                self._thread = None
        return self.status()

    def status(self) -> dict[str, Any]:
        with self._lock:
            frames = list(self._frames)
            latest = frames[-1] if frames else None
            variance: list[float] = []
            if len(frames) >= 3 and latest:
                count = min(len(f["amplitudes"]) for f in frames[-40:])
                for index in range(count):
                    values = [f["amplitudes"][index] for f in frames[-40:]]
                    variance.append(round(statistics.pvariance(values), 4))
            return {
                "state": self._state,
                "error": self._error,
                "port": self._port,
                "baud": self._baud,
                "csi_column": self._column,
                "frames_received": self._received,
                "buffered_frames": len(frames),
                "latest": latest,
                "variance_by_subcarrier": variance,
                "variance_mean": round(sum(variance) / len(variance), 4) if variance else None,
                "data_source": "live_serial" if self._state == "connected" else "none",
            }

    def recent(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._frames)[-max(1, min(120, limit)):]


collector = CSICollector()
