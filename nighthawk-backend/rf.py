"""Small, dependency-free indoor RF estimation and interpolation utilities."""
from __future__ import annotations

import math
from typing import Any

SPEED_OF_LIGHT_M_S = 299_792_458.0
MATERIAL_LOSS_DB_AT_5_GHZ = {
    "drywall": 3.5,
    "wood": 4.5,
    "glass": 3.0,
    "brick": 12.0,
    "concrete": 18.0,
    "metal": 32.0,
}
FREQUENCY_SCALE = {2400: 0.82, 5000: 1.0, 6000: 1.12}


def fspl_db(distance_m: float, frequency_mhz: float) -> float:
    distance = max(0.5, float(distance_m))
    frequency_hz = float(frequency_mhz) * 1_000_000.0
    return 20.0 * math.log10(4.0 * math.pi * distance * frequency_hz / SPEED_OF_LIGHT_M_S)


def _cross(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    a: tuple[float, float], b: tuple[float, float],
    c: tuple[float, float], d: tuple[float, float],
) -> bool:
    eps = 1e-9
    o1, o2 = _cross(a, b, c), _cross(a, b, d)
    o3, o4 = _cross(c, d, a), _cross(c, d, b)
    return (o1 * o2 < -eps) and (o3 * o4 < -eps)


def wall_loss_db(
    source: tuple[float, float],
    target: tuple[float, float],
    walls: list[dict[str, Any]],
    frequency_mhz: int,
) -> float:
    scale = min(FREQUENCY_SCALE.values(), key=lambda value: abs(value - 1.0))
    scale = FREQUENCY_SCALE.get(int(frequency_mhz), 1.0)
    loss = 0.0
    for wall in walls:
        start = (float(wall["x1"]), float(wall["y1"]))
        end = (float(wall["x2"]), float(wall["y2"]))
        if segments_intersect(source, target, start, end):
            material = str(wall.get("material", "drywall")).lower()
            loss += MATERIAL_LOSS_DB_AT_5_GHZ.get(material, 3.5) * scale
    return loss


def predict_rssi_dbm(
    x: float, y: float, router: dict[str, float], walls: list[dict[str, Any]],
    frequency_mhz: int = 5000, tx_power_dbm: float = 18.0,
) -> float:
    dx = float(x) - float(router["x"])
    dy = float(y) - float(router["y"])
    distance = math.hypot(dx, dy)
    source = (float(router["x"]), float(router["y"]))
    target = (float(x), float(y))
    path_loss = fspl_db(distance, frequency_mhz)
    material_loss = wall_loss_db(source, target, walls, frequency_mhz)
    return round(max(-100.0, min(-15.0, tx_power_dbm - path_loss - material_loss)), 1)


def idw_value(x: float, y: float, points: list[dict[str, Any]], power: float = 2.0) -> float | None:
    if not points:
        return None
    weighted_sum = 0.0
    weight_total = 0.0
    for point in points:
        distance = math.hypot(x - float(point["x"]), y - float(point["y"]))
        value = float(point["rssi_dbm"])
        if distance < 1e-8:
            return value
        weight = 1.0 / (distance ** power)
        weighted_sum += value * weight
        weight_total += weight
    return round(weighted_sum / weight_total, 1) if weight_total else None


def make_grid(
    width_m: float, height_m: float, resolution: int,
    value_fn,
) -> dict[str, Any]:
    count = max(8, min(100, int(resolution)))
    xs = [round(width_m * i / (count - 1), 3) for i in range(count)]
    ys = [round(height_m * i / (count - 1), 3) for i in range(count)]
    rows = [[value_fn(x, y) for x in xs] for y in ys]
    values = [value for row in rows for value in row if value is not None]
    return {
        "width_m": width_m, "height_m": height_m, "resolution": count,
        "xs": xs, "ys": ys, "values": rows,
        "min_dbm": min(values) if values else None,
        "max_dbm": max(values) if values else None,
    }
