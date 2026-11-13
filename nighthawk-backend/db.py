"""SQLite persistence for NightHawk. All data stays on this machine."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("NIGHTHAWK_DATA_DIR", Path.home() / ".nighthawk"))
DB_PATH = DATA_DIR / "nighthawk.sqlite3"

DEFAULT_PROJECT: dict[str, Any] = {
    "name": "My Home",
    "width_m": 10.0,
    "height_m": 8.0,
    "wall_height_m": 2.7,
    "frequency_mhz": 5000,
    "tx_power_dbm": 18.0,
    "router": {"x": 5.0, "y": 4.0, "z": 2.4},
    "walls": [
        {"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0, "material": "concrete"},
        {"x1": 10.0, "y1": 0.0, "x2": 10.0, "y2": 8.0, "material": "concrete"},
        {"x1": 10.0, "y1": 8.0, "x2": 0.0, "y2": 8.0, "material": "concrete"},
        {"x1": 0.0, "y1": 8.0, "x2": 0.0, "y2": 0.0, "material": "concrete"},
    ],
    "router_floor_id": "floor_1",
    "floors": [{
        "id": "floor_1", "name": "Ground floor", "elevation_m": 0.0,
        "width_m": 10.0, "height_m": 8.0, "wall_height_m": 2.7,
        "floor_loss_db": 18.0,
        "walls": [
            {"x1": 0.0, "y1": 0.0, "x2": 10.0, "y2": 0.0, "material": "concrete"},
            {"x1": 10.0, "y1": 0.0, "x2": 10.0, "y2": 8.0, "material": "concrete"},
            {"x1": 10.0, "y1": 8.0, "x2": 0.0, "y2": 8.0, "material": "concrete"},
            {"x1": 0.0, "y1": 8.0, "x2": 0.0, "y2": 0.0, "material": "concrete"},
        ],
    }],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


@contextmanager
def db_session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS survey_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS survey_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES survey_sessions(id) ON DELETE CASCADE,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL DEFAULT 1.0,
            floor_id TEXT NOT NULL DEFAULT 'floor_1',
            ssid TEXT NOT NULL DEFAULT '',
            bssid TEXT NOT NULL DEFAULT '',
            rssi_dbm REAL NOT NULL,
            signal_percent INTEGER,
            measurement_source TEXT NOT NULL DEFAULT 'manual',
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_points_session ON survey_points(session_id);
        CREATE TABLE IF NOT EXISTS volumetric_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            rssi_dbm REAL NOT NULL,
            imported_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_volumetric_source ON volumetric_points(source_name);

        CREATE TABLE IF NOT EXISTS wifi_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scanned_at TEXT NOT NULL,
            platform TEXT NOT NULL,
            connected_ssid TEXT NOT NULL DEFAULT '',
            connected_bssid TEXT NOT NULL DEFAULT '',
            connected_rssi REAL,
            connected_signal INTEGER,
            network_count INTEGER NOT NULL DEFAULT 0,
            raw_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_wifi_scans_date ON wifi_scans(scanned_at);

        CREATE TABLE IF NOT EXISTS wifi_scan_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL REFERENCES wifi_scans(id) ON DELETE CASCADE,
            ssid TEXT NOT NULL DEFAULT '',
            bssid TEXT NOT NULL DEFAULT '',
            signal_percent INTEGER,
            rssi_dbm_estimate REAL,
            channel INTEGER,
            band TEXT NOT NULL DEFAULT '',
            radio_type TEXT NOT NULL DEFAULT '',
            authentication TEXT NOT NULL DEFAULT '',
            is_connected INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_scan_entries_scan ON wifi_scan_entries(scan_id);
        CREATE INDEX IF NOT EXISTS idx_scan_entries_bssid ON wifi_scan_entries(bssid);
        """)
        row = conn.execute("SELECT id FROM projects WHERE id = 1").fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO projects (id, payload, updated_at) VALUES (1, ?, ?)",
                (json.dumps(DEFAULT_PROJECT), utc_now()),
            )


def get_project() -> dict[str, Any]:
    init_db()
    with db_session() as conn:
        row = conn.execute("SELECT payload, updated_at FROM projects WHERE id = 1").fetchone()
    result = json.loads(row["payload"])
    result.setdefault("router_floor_id", "floor_1")
    if not result.get("floors"):
        result["floors"] = [{
            "id": "floor_1", "name": "Ground floor", "elevation_m": 0.0,
            "width_m": float(result.get("width_m", 10.0)),
            "height_m": float(result.get("height_m", 8.0)),
            "wall_height_m": float(result.get("wall_height_m", 2.7)),
            "floor_loss_db": 18.0,
            "walls": result.get("walls", []),
        }]
    result["updated_at"] = row["updated_at"]
    return result


def save_project(payload: dict[str, Any]) -> dict[str, Any]:
    stamp = utc_now()
    with db_session() as conn:
        conn.execute(
            """INSERT INTO projects (id, payload, updated_at) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at""",
            (json.dumps(payload), stamp),
        )
    result = dict(payload)
    result["updated_at"] = stamp
    return result


def create_session(name: str, notes: str = "") -> dict[str, Any]:
    stamp = utc_now()
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO survey_sessions (name, notes, created_at) VALUES (?, ?, ?)",
            (name, notes, stamp),
        )
        row_id = cur.lastrowid
    return {"id": row_id, "name": name, "notes": notes, "created_at": stamp, "point_count": 0}


def list_sessions() -> list[dict[str, Any]]:
    with db_session() as conn:
        rows = conn.execute("""
            SELECT s.id, s.name, s.notes, s.created_at, COUNT(p.id) AS point_count
            FROM survey_sessions s
            LEFT JOIN survey_points p ON p.session_id = s.id
            GROUP BY s.id ORDER BY s.id DESC
        """).fetchall()
    return [dict(row) for row in rows]


def add_point(session_id: int, point: dict[str, Any]) -> dict[str, Any]:
    with db_session() as conn:
        exists = conn.execute("SELECT id FROM survey_sessions WHERE id = ?", (session_id,)).fetchone()
        if exists is None:
            raise LookupError("Survey session not found")
        cur = conn.execute("""
            INSERT INTO survey_points
            (session_id, x, y, z, floor_id, ssid, bssid, rssi_dbm, signal_percent, measurement_source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, point["x"], point["y"], point.get("z", 1.0),
            point.get("floor_id", "floor_1"), point.get("ssid", ""),
            point.get("bssid", ""), point["rssi_dbm"],
            point.get("signal_percent"), point.get("measurement_source", "manual"),
            utc_now(),
        ))
        row = conn.execute("SELECT * FROM survey_points WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def get_points(session_id: int) -> list[dict[str, Any]]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM survey_points WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def replace_volumetric_points(source_name: str, points: list[dict[str, Any]]) -> dict[str, Any]:
    stamp = utc_now()
    with db_session() as conn:
        conn.execute("DELETE FROM volumetric_points")
        conn.executemany(
            """INSERT INTO volumetric_points (source_name, x, y, z, rssi_dbm, imported_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(source_name, p["x"], p["y"], p["z"], p["rssi_dbm"], stamp) for p in points],
        )
    return {"source_name": source_name, "point_count": len(points), "imported_at": stamp}


def get_volumetric_points() -> list[dict[str, Any]]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, source_name, x, y, z, rssi_dbm, imported_at FROM volumetric_points ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def save_wifi_scan(scan_data: dict[str, Any]) -> dict[str, Any]:
    """Persist a complete Wi-Fi environment scan and its network entries."""
    init_db()
    scanned_at = scan_data.get("scanned_at") or utc_now()
    platform_name = scan_data.get("platform") or "Windows"
    connected = scan_data.get("connected") or {}
    conn_ssid = connected.get("ssid") or ""
    conn_bssid = connected.get("bssid") or ""
    conn_rssi = connected.get("rssi_dbm_estimate")
    conn_signal = connected.get("signal_percent")
    networks = scan_data.get("networks") or []
    raw_json = json.dumps(scan_data)

    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO wifi_scans
               (scanned_at, platform, connected_ssid, connected_bssid, connected_rssi, connected_signal, network_count, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (scanned_at, platform_name, conn_ssid, conn_bssid, conn_rssi, conn_signal, len(networks), raw_json),
        )
        scan_id = cur.lastrowid

        entry_rows = [
            (
                scan_id,
                n.get("ssid", ""),
                n.get("bssid", ""),
                n.get("signal_percent"),
                n.get("rssi_dbm_estimate"),
                n.get("channel"),
                n.get("band", ""),
                n.get("radio_type", ""),
                n.get("authentication", ""),
                1 if n.get("is_connected") else 0,
            )
            for n in networks
        ]
        if entry_rows:
            conn.executemany(
                """INSERT INTO wifi_scan_entries
                   (scan_id, ssid, bssid, signal_percent, rssi_dbm_estimate, channel, band, radio_type, authentication, is_connected)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                entry_rows,
            )

    return {
        "id": scan_id,
        "scanned_at": scanned_at,
        "network_count": len(networks),
        "connected_ssid": conn_ssid,
        "connected_bssid": conn_bssid,
    }


def list_wifi_scans(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve metadata for historical Wi-Fi scans ordered by most recent first."""
    init_db()
    with db_session() as conn:
        rows = conn.execute(
            """SELECT id, scanned_at, platform, connected_ssid, connected_bssid, connected_rssi, connected_signal, network_count
               FROM wifi_scans ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_wifi_scan(scan_id: int) -> dict[str, Any] | None:
    """Retrieve full details of a specific past Wi-Fi scan."""
    init_db()
    with db_session() as conn:
        row = conn.execute("SELECT raw_json FROM wifi_scans WHERE id = ?", (scan_id,)).fetchone()
        if not row:
            return None
        data = json.loads(row["raw_json"])
        data["id"] = scan_id
        return data


def delete_wifi_scan(scan_id: int) -> bool:
    """Delete a past Wi-Fi scan and its entries."""
    init_db()
    with db_session() as conn:
        cur = conn.execute("DELETE FROM wifi_scans WHERE id = ?", (scan_id,))
        return cur.rowcount > 0


def compare_wifi_scans(scan_id_a: int, scan_id_b: int) -> dict[str, Any]:
    """
    Compare two scans (scan A as baseline, scan B as target) to identify
    newly appeared APs, disappeared APs, and signal strength changes (delta dBm).
    """
    scan_a = get_wifi_scan(scan_id_a)
    scan_b = get_wifi_scan(scan_id_b)
    if not scan_a or not scan_b:
        raise LookupError("One or both scans not found")

    nets_a: dict[str, dict[str, Any]] = {n["bssid"].lower(): n for n in scan_a.get("networks", []) if n.get("bssid")}
    nets_b: dict[str, dict[str, Any]] = {n["bssid"].lower(): n for n in scan_b.get("networks", []) if n.get("bssid")}

    bssids_a = set(nets_a.keys())
    bssids_b = set(nets_b.keys())

    common_bssids = bssids_a & bssids_b
    new_bssids = bssids_b - bssids_a
    lost_bssids = bssids_a - bssids_b

    deltas: list[dict[str, Any]] = []
    total_delta_dbm = 0.0
    for bssid in sorted(common_bssids):
        na = nets_a[bssid]
        nb = nets_b[bssid]
        rssi_a = na.get("rssi_dbm_estimate")
        rssi_b = nb.get("rssi_dbm_estimate")
        diff_dbm = round(rssi_b - rssi_a, 1) if (rssi_a is not None and rssi_b is not None) else None
        if diff_dbm is not None:
            total_delta_dbm += diff_dbm

        deltas.append({
            "ssid": nb.get("ssid") or na.get("ssid"),
            "bssid": nb.get("bssid"),
            "band": nb.get("band"),
            "channel": nb.get("channel"),
            "baseline_rssi_dbm": rssi_a,
            "current_rssi_dbm": rssi_b,
            "delta_rssi_dbm": diff_dbm,
            "baseline_signal_percent": na.get("signal_percent"),
            "current_signal_percent": nb.get("signal_percent"),
        })

    avg_delta = round(total_delta_dbm / len(common_bssids), 2) if common_bssids else 0.0

    return {
        "baseline_scan": {
            "id": scan_id_a,
            "scanned_at": scan_a.get("scanned_at"),
            "network_count": len(nets_a),
        },
        "target_scan": {
            "id": scan_id_b,
            "scanned_at": scan_b.get("scanned_at"),
            "network_count": len(nets_b),
        },
        "summary": {
            "common_count": len(common_bssids),
            "new_count": len(new_bssids),
            "lost_count": len(lost_bssids),
            "average_signal_delta_dbm": avg_delta,
        },
        "new_networks": [nets_b[b] for b in sorted(new_bssids)],
        "lost_networks": [nets_a[b] for b in sorted(lost_bssids)],
        "persistent_networks": deltas,
    }

