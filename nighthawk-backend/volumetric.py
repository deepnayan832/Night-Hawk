"""CSV parsing for measured volumetric RSSI point clouds."""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path
from typing import Any


def parse_volumetric_csv(content: str) -> list[dict[str, float]]:
    reader = csv.DictReader(io.StringIO(content))
    headers = {str(name).strip().lower(): name for name in (reader.fieldnames or [])}
    if not {"x", "y", "z"}.issubset(headers) or not ({"rssi_dbm", "rssi"} & set(headers)):
        raise ValueError("CSV needs x,y,z and rssi_dbm (or rssi) columns.")
    rssi_column = headers.get("rssi_dbm") or headers["rssi"]
    points: list[dict[str, float]] = []
    for line_no, row in enumerate(reader, start=2):
        if not row or not any((value or "").strip() for value in row.values()):
            continue
        try:
            point = {
                "x": float(row[headers["x"]]),
                "y": float(row[headers["y"]]),
                "z": float(row[headers["z"]]),
                "rssi_dbm": float(row[rssi_column]),
            }
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError(f"Invalid numeric value on CSV line {line_no}.") from exc
        if not all(math.isfinite(value) for value in point.values()):
            raise ValueError(f"Non-finite value on CSV line {line_no}.")
        if any(abs(point[key]) > 10000 for key in ("x", "y", "z")) or not -120 <= point["rssi_dbm"] <= -10:
            raise ValueError(f"Out-of-range value on CSV line {line_no}.")
        points.append(point)
        if len(points) > 100000:
            raise ValueError("CSV contains more than 100,000 points.")
    if not points:
        raise ValueError("CSV contains no valid data rows.")
    return points


def safe_source_name(filename: str) -> str:
    return Path(filename).name[:160] or "uploaded.csv"
