"""NightHawk local API and static application server."""
from __future__ import annotations

import csv
import io
import platform
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db
from rf import make_grid, idw_value, predict_rssi_dbm
from wifi import scan_wifi

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="NightHawk Local API",
    version="1.0.0",
    description="Local-first Wi-Fi survey, floor-plan and RF analysis service.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class RouterModel(BaseModel):
    x: float = Field(ge=0, le=1000)
    y: float = Field(ge=0, le=1000)
    z: float = Field(default=2.4, ge=0, le=100)


class WallModel(BaseModel):
    x1: float = Field(ge=0, le=1000)
    y1: float = Field(ge=0, le=1000)
    x2: float = Field(ge=0, le=1000)
    y2: float = Field(ge=0, le=1000)
    material: str = "drywall"


class ProjectModel(BaseModel):
    name: str = Field(default="My Home", min_length=1, max_length=80)
    width_m: float = Field(default=10, gt=1, le=100)
    height_m: float = Field(default=8, gt=1, le=100)
    wall_height_m: float = Field(default=2.7, gt=1, le=10)
    frequency_mhz: int = Field(default=5000)
    tx_power_dbm: float = Field(default=18, ge=0, le=30)
    router: RouterModel
    walls: list[WallModel] = Field(default_factory=list)


class SessionModel(BaseModel):
    name: str = Field(default="Home survey", min_length=1, max_length=80)
    notes: str = Field(default="", max_length=500)


class PointModel(BaseModel):
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    z: float = Field(default=1.0, ge=0, le=20)
    floor_id: str = Field(default="floor_1", max_length=40)
    ssid: str = Field(default="", max_length=128)
    bssid: str = Field(default="", max_length=32)
    rssi_dbm: float = Field(ge=-120, le=-10)
    signal_percent: int | None = Field(default=None, ge=0, le=100)
    measurement_source: str = Field(default="manual", max_length=40)


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    db.init_db()
    return {
        "ok": True, "app": "NightHawk", "version": app.version,
        "platform": platform.platform(), "data_directory": str(db.DATA_DIR),
        "database": str(db.DB_PATH),
    }


@app.get("/api/hardware/status")
def hardware_status() -> dict[str, Any]:
    return {
        "platform": platform.system(),
        "windows_wifi_scanner": platform.system() == "Windows",
        "wifi_scanner_method": "Windows netsh WLAN commands",
        "rssi_quality": "Estimated from signal percentage; not calibrated dBm",
        "csi_hardware": "Not implemented in this release; ESP32 required",
        "motorized_scanner": "Not implemented in this release; external rig required",
    }


@app.get("/api/wifi/scan")
def wifi_scan() -> dict[str, Any]:
    try:
        return scan_wifi()
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/project")
def project_get() -> dict[str, Any]:
    return db.get_project()


@app.put("/api/project")
def project_put(project: ProjectModel) -> dict[str, Any]:
    data = project.model_dump() if hasattr(project, "model_dump") else project.dict()
    if data["router"]["x"] > data["width_m"] or data["router"]["y"] > data["height_m"]:
        raise HTTPException(status_code=422, detail="Router position must be inside the floor plan.")
    for wall in data["walls"]:
        if max(wall["x1"], wall["x2"]) > data["width_m"] or max(wall["y1"], wall["y2"]) > data["height_m"]:
            raise HTTPException(status_code=422, detail="Every wall endpoint must be inside the floor plan.")
        if math_distance(wall["x1"], wall["y1"], wall["x2"], wall["y2"]) < 0.05:
            raise HTTPException(status_code=422, detail="Wall length must be at least 5 cm.")
        if wall["material"] not in {"drywall", "wood", "glass", "brick", "concrete", "metal"}:
            raise HTTPException(status_code=422, detail="Unsupported wall material.")
    return db.save_project(data)


def math_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


@app.get("/api/surveys")
def surveys_list() -> list[dict[str, Any]]:
    return db.list_sessions()


@app.post("/api/surveys", status_code=201)
def surveys_create(session: SessionModel) -> dict[str, Any]:
    return db.create_session(session.name, session.notes)


@app.get("/api/surveys/{session_id}/points")
def survey_points(session_id: int) -> list[dict[str, Any]]:
    if not any(item["id"] == session_id for item in db.list_sessions()):
        raise HTTPException(status_code=404, detail="Survey session not found.")
    return db.get_points(session_id)


@app.post("/api/surveys/{session_id}/points", status_code=201)
def survey_point_add(session_id: int, point: PointModel) -> dict[str, Any]:
    data = point.model_dump() if hasattr(point, "model_dump") else point.dict()
    project = db.get_project()
    if data["x"] > project["width_m"] or data["y"] > project["height_m"]:
        raise HTTPException(status_code=422, detail="Survey point must be inside the saved floor plan.")
    try:
        return db.add_point(session_id, data)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/coverage/measured")
def coverage_measured(
    session_id: int = Query(..., ge=1),
    resolution: int = Query(default=36, ge=8, le=100),
) -> dict[str, Any]:
    project = db.get_project()
    if not any(item["id"] == session_id for item in db.list_sessions()):
        raise HTTPException(status_code=404, detail="Survey session not found.")
    points = db.get_points(session_id)
    result = make_grid(
        project["width_m"], project["height_m"], resolution,
        lambda x, y: idw_value(x, y, points),
    )
    result.update({"kind": "measured_idw", "point_count": len(points)})
    return result


@app.get("/api/coverage/predicted")
def coverage_predicted(resolution: int = Query(default=36, ge=8, le=100)) -> dict[str, Any]:
    project = db.get_project()
    frequency = int(project["frequency_mhz"])
    result = make_grid(
        project["width_m"], project["height_m"], resolution,
        lambda x, y: predict_rssi_dbm(
            x, y, project["router"], project["walls"],
            frequency, float(project["tx_power_dbm"]),
        ),
    )
    result.update({
        "kind": "theoretical_model",
        "frequency_mhz": frequency,
        "notice": "Model estimate only. Real walls, construction, interference and antenna patterns affect results.",
    })
    return result


@app.get("/api/surveys/{session_id}/export.csv")
def survey_export_csv(session_id: int) -> Response:
    if not any(item["id"] == session_id for item in db.list_sessions()):
        raise HTTPException(status_code=404, detail="Survey session not found.")
    points = db.get_points(session_id)
    buffer = io.StringIO()
    fields = ["id", "session_id", "x", "y", "z", "floor_id", "ssid", "bssid",
              "rssi_dbm", "signal_percent", "measurement_source", "created_at"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(points)
    return Response(
        content=buffer.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="nighthawk-survey-{session_id}.csv"'},
    )


@app.get("/api/router/optimize")
def router_optimize(
    step_m: float = Query(default=1.0, ge=0.5, le=5.0),
    resolution: int = Query(default=10, ge=5, le=20),
) -> dict[str, Any]:
    """Rank candidate router locations by mean modelled RSSI across a coarse grid."""
    project = db.get_project()
    width, height = float(project["width_m"]), float(project["height_m"])
    xs = [width * i / (resolution - 1) for i in range(resolution)]
    ys = [height * i / (resolution - 1) for i in range(resolution)]
    candidates: list[dict[str, Any]] = []
    x = min(step_m / 2.0, width / 2.0)
    while x <= width - min(step_m / 2.0, width / 2.0) + 1e-9:
        y = min(step_m / 2.0, height / 2.0)
        while y <= height - min(step_m / 2.0, height / 2.0) + 1e-9:
            router = {"x": x, "y": y}
            samples = [
                predict_rssi_dbm(
                    sx, sy, router, project["walls"],
                    int(project["frequency_mhz"]), float(project["tx_power_dbm"]),
                )
                for sx in xs for sy in ys
            ]
            ordered = sorted(samples)
            candidates.append({
                "x": round(x, 2), "y": round(y, 2),
                "mean_rssi_dbm": round(sum(samples) / len(samples), 1),
                "worst_decile_dbm": round(ordered[max(0, int(len(ordered) * 0.1) - 1)], 1),
            })
            y += step_m
        x += step_m
    candidates.sort(
        key=lambda item: (item["mean_rssi_dbm"] + 0.35 * item["worst_decile_dbm"]),
        reverse=True,
    )
    return {
        "recommendations": candidates[:5],
        "best": candidates[0] if candidates else None,
        "method": "Coarse grid search maximizing mean predicted RSSI with a weak-area penalty",
        "notice": "The optimizer uses the same simplified RF model as the predicted map. Validate placement with a real walk survey.",
    }
