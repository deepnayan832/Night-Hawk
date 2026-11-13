"""Generate a bounded serpentine waypoint grid for external volumetric scanners."""
from __future__ import annotations

import math
from typing import Any


def _axis(extent: float, step: float) -> list[float]:
    count = int(math.floor(extent / step)) + 1
    values = [round(index * step, 4) for index in range(count)]
    if not values or values[-1] < extent - 1e-6:
        values.append(round(extent, 4))
    return values


def build_scan_plan(width_m: float, depth_m: float, height_m: float, step_m: float) -> list[dict[str, Any]]:
    for name, value in (("width", width_m), ("depth", depth_m), ("height", height_m)):
        if not math.isfinite(value) or value <= 0 or value > 100:
            raise ValueError(f"{name} must be greater than 0 and no more than 100 metres.")
    if not math.isfinite(step_m) or not 0.02 <= step_m <= 5:
        raise ValueError("step must be between 0.02 and 5 metres.")
    xs, ys, zs = _axis(width_m, step_m), _axis(depth_m, step_m), _axis(height_m, step_m)
    count = len(xs) * len(ys) * len(zs)
    if count > 50000:
        raise ValueError(f"Scan plan would contain {count} waypoints; increase the step size (maximum 50,000).")
    points: list[dict[str, Any]] = []
    sequence = 0
    for layer_index, z in enumerate(zs):
        y_rows = ys if layer_index % 2 == 0 else list(reversed(ys))
        for row_index, y in enumerate(y_rows):
            x_row = xs if row_index % 2 == 0 else list(reversed(xs))
            for x in x_row:
                sequence += 1
                points.append({
                    "sequence": sequence,
                    "x": x,
                    "y": y,
                    "z": z,
                })
    return points
