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
