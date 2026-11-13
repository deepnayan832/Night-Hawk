"""NightHawk local API and static application server."""
from __future__ import annotations

import csv
import io
import json
import platform
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db
from rf import make_grid, idw_value, predict_rssi_dbm, predict_rssi_3d_dbm
from wifi import scan_wifi, get_interfaces
from network_intel import get_network_info, discover_local_devices, analyze_channel_congestion
from csi import collector as csi_collector
from volumetric import parse_volumetric_csv, safe_source_name
from scanplan import build_scan_plan

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="NightHawk Local API",
    version="1.1.0",
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


class FloorModel(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(default="Floor", min_length=1, max_length=80)
    elevation_m: float = Field(default=0, ge=-50, le=500)
    width_m: float = Field(default=10, gt=1, le=100)
    height_m: float = Field(default=8, gt=1, le=100)
    wall_height_m: float = Field(default=2.7, gt=1, le=10)
    floor_loss_db: float = Field(default=18, ge=0, le=60)
    walls: list[WallModel] = Field(default_factory=list)


class ProjectModel(BaseModel):
    name: str = Field(default="My Home", min_length=1, max_length=80)
    width_m: float = Field(default=10, gt=1, le=100)
    height_m: float = Field(default=8, gt=1, le=100)
    wall_height_m: float = Field(default=2.7, gt=1, le=10)
    frequency_mhz: int = Field(default=5000)
    tx_power_dbm: float = Field(default=18, ge=0, le=30)
    router: RouterModel
    router_floor_id: str = Field(default="floor_1", max_length=40)
    floors: list[FloorModel] = Field(default_factory=list)
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


class CSIStartModel(BaseModel):
    port: str = Field(min_length=1, max_length=128)
    baud: int = Field(default=921600)
    csi_column: int = Field(default=25, ge=1, le=80)


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
        "csi_hardware": csi_collector.status()["state"],
        "csi_protocol": "ESP32-CSI-Tool CSV; configurable CSI field index",
        "motorized_scanner": "Physical controller integration remains hardware/protocol-specific and is not armed",
        "volumetric_dataset_import": True,
    }


@app.get("/api/wifi/scan")
def wifi_scan(persist: bool = Query(default=True)) -> dict[str, Any]:
    try:
        result = scan_wifi()
        if persist:
            saved = db.save_wifi_scan(result)
            result["scan_id"] = saved["id"]
        return result
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/network/interfaces")
def network_interfaces() -> list[dict[str, Any]]:
    try:
        return get_interfaces()
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/network/info")
def network_info() -> dict[str, Any]:
    return get_network_info()


@app.get("/api/network/devices")
def network_devices() -> list[dict[str, Any]]:
    net_info = get_network_info()
    gw_ip = net_info.get("default_gateway")
    return discover_local_devices(gw_ip if gw_ip != "Unavailable" else None)


@app.get("/api/network/channels")
def network_channels() -> dict[str, Any]:
    try:
        scan_res = scan_wifi()
        networks = scan_res.get("networks", [])
    except Exception:
        networks = []
    return analyze_channel_congestion(networks)


@app.get("/api/wifi/history")
def wifi_history(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    return db.list_wifi_scans(limit=limit)


@app.get("/api/wifi/history/compare")
def wifi_history_compare(
    baseline_id: int = Query(..., ge=1),
    target_id: int = Query(..., ge=1),
) -> dict[str, Any]:
    try:
        return db.compare_wifi_scans(baseline_id, target_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/wifi/history/export.csv")
def wifi_history_export_csv() -> Response:
    scans = db.list_wifi_scans(limit=100)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "scan_id", "scanned_at", "ssid", "bssid", "signal_percent",
        "rssi_dbm_estimate", "channel", "band", "radio_type", "authentication", "is_connected"
    ])
    for s in scans:
        full_scan = db.get_wifi_scan(s["id"])
        if not full_scan:
            continue
        for net in full_scan.get("networks", []):
            writer.writerow([
                s["id"],
                full_scan.get("scanned_at", ""),
                net.get("ssid", ""),
                net.get("bssid", ""),
                net.get("signal_percent", ""),
                net.get("rssi_dbm_estimate", ""),
                net.get("channel", ""),
                net.get("band", ""),
                net.get("radio_type", ""),
                net.get("authentication", ""),
                1 if net.get("is_connected") else 0,
            ])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nighthawk-scan-history.csv"'},
    )


@app.get("/api/wifi/history/export.json")
def wifi_history_export_json() -> Response:
    scans = db.list_wifi_scans(limit=100)
    full_scans = []
    for s in scans:
        detail = db.get_wifi_scan(s["id"])
        if detail:
            full_scans.append(detail)
    return Response(
        content=json.dumps({"export_timestamp": db.utc_now(), "scans": full_scans}, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="nighthawk-scan-history.json"'},
    )


@app.get("/api/wifi/history/{scan_id}")
def wifi_history_get(scan_id: int) -> dict[str, Any]:
    scan = db.get_wifi_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan record not found.")
    return scan


@app.delete("/api/wifi/history/{scan_id}")
def wifi_history_delete(scan_id: int) -> dict[str, Any]:
    success = db.delete_wifi_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan record not found.")
    return {"ok": True, "deleted_scan_id": scan_id}


@app.get("/api/project")
def project_get() -> dict[str, Any]:
    return db.get_project()


@app.put("/api/project")
def project_put(project: ProjectModel) -> dict[str, Any]:
    data = project.model_dump() if hasattr(project, "model_dump") else project.dict()
    if not data["floors"]:
        data["floors"] = [{
            "id": "floor_1", "name": "Ground floor", "elevation_m": 0.0,
            "width_m": data["width_m"], "height_m": data["height_m"],
            "wall_height_m": data["wall_height_m"], "floor_loss_db": 18.0,
            "walls": data["walls"],
        }]
    floor_ids = [floor["id"] for floor in data["floors"]]
    if len(floor_ids) != len(set(floor_ids)):
        raise HTTPException(status_code=422, detail="Floor IDs must be unique.")
    if data["router_floor_id"] not in floor_ids:
        raise HTTPException(status_code=422, detail="Router floor must exist in the project.")
    for floor in data["floors"]:
        for wall in floor["walls"]:
            if max(wall["x1"], wall["x2"]) > floor["width_m"] or max(wall["y1"], wall["y2"]) > floor["height_m"]:
                raise HTTPException(status_code=422, detail=f"Wall endpoint outside floor: {floor['name']}.")
            if math_distance(wall["x1"], wall["y1"], wall["x2"], wall["y2"]) < 0.05:
                raise HTTPException(status_code=422, detail="Wall length must be at least 5 cm.")
            if wall["material"] not in {"drywall", "wood", "glass", "brick", "concrete", "metal"}:
                raise HTTPException(status_code=422, detail="Unsupported wall material.")
    router_floor = next(floor for floor in data["floors"] if floor["id"] == data["router_floor_id"])
    if data["router"]["x"] > router_floor["width_m"] or data["router"]["y"] > router_floor["height_m"]:
        raise HTTPException(status_code=422, detail="Router position must be inside its floor.")
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
    floors = project.get("floors") or [{
        "id": "floor_1", "width_m": project["width_m"], "height_m": project["height_m"]
    }]
    floor = next((item for item in floors if item["id"] == data["floor_id"]), None)
    if floor is None:
        raise HTTPException(status_code=422, detail="Survey point floor does not exist.")
    if data["x"] > floor["width_m"] or data["y"] > floor["height_m"]:
        raise HTTPException(status_code=422, detail="Survey point must be inside its floor plan.")
    try:
        return db.add_point(session_id, data)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/coverage/measured")
def coverage_measured(
    session_id: int = Query(..., ge=1),
    floor_id: str = Query(default="floor_1", max_length=40),
    resolution: int = Query(default=36, ge=8, le=100),
) -> dict[str, Any]:
    project = db.get_project()
    if not any(item["id"] == session_id for item in db.list_sessions()):
        raise HTTPException(status_code=404, detail="Survey session not found.")
    floors = project.get("floors") or [{
        "id": "floor_1", "width_m": project["width_m"], "height_m": project["height_m"]
    }]
    floor = next((item for item in floors if item["id"] == floor_id), None)
    if floor is None:
        raise HTTPException(status_code=404, detail="Floor not found.")
    points = [p for p in db.get_points(session_id) if p["floor_id"] == floor_id]
    result = make_grid(
        floor["width_m"], floor["height_m"], resolution,
        lambda x, y: idw_value(x, y, points),
    )
    result.update({"kind": "measured_idw", "point_count": len(points), "floor_id": floor_id})
    return result


@app.get("/api/coverage/predicted")
def coverage_predicted(
    floor_id: str = Query(default="floor_1", max_length=40),
    resolution: int = Query(default=36, ge=8, le=100),
) -> dict[str, Any]:
    project = db.get_project()
    floors = project.get("floors") or [{
        "id": "floor_1", "name": "Ground floor", "elevation_m": 0.0,
        "width_m": project["width_m"], "height_m": project["height_m"],
        "walls": project["walls"], "floor_loss_db": 18.0,
    }]
    target_floor = next((floor for floor in floors if floor["id"] == floor_id), None)
    if target_floor is None:
        raise HTTPException(status_code=404, detail="Floor not found.")
    router_floor_id = project.get("router_floor_id", floors[0]["id"])
    source_floor = next((floor for floor in floors if floor["id"] == router_floor_id), floors[0])
    ordered = sorted(floors, key=lambda item: item["elevation_m"])
    floor_count = abs(ordered.index(target_floor) - ordered.index(source_floor))
    router_elevation = float(source_floor["elevation_m"]) + float(project["router"].get("z", 2.4))
    target_elevation = float(target_floor["elevation_m"]) + 1.0
    frequency = int(project["frequency_mhz"])
    result = make_grid(
        target_floor["width_m"], target_floor["height_m"], resolution,
        lambda x, y: predict_rssi_3d_dbm(
            x, y, target_elevation, project["router"], router_elevation,
            target_floor["walls"], frequency, float(project["tx_power_dbm"]),
            float(target_floor.get("floor_loss_db", 18.0)), floor_count,
        ),
    )
    result.update({
        "kind": "theoretical_3d_model",
        "frequency_mhz": frequency,
        "floor_id": floor_id,
        "floor_name": target_floor["name"],
        "floor_crossings": floor_count,
        "notice": "Simplified 3D estimate: FSPL, 2D wall intersections on the target floor and one slab-loss allowance per floor crossed. Not a full 3D ray tracer.",
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
    floor_id: str = Query(default="floor_1", max_length=40),
) -> dict[str, Any]:
    """Rank router positions on one floor; vertical slab losses are modelled."""
    project = db.get_project()
    floors = project.get("floors") or [{
        "id": "floor_1", "name": "Ground floor", "elevation_m": 0.0,
        "width_m": project["width_m"], "height_m": project["height_m"],
        "walls": project["walls"], "floor_loss_db": 18.0,
    }]
    target_floor = next((floor for floor in floors if floor["id"] == floor_id), None)
    if target_floor is None:
        raise HTTPException(status_code=404, detail="Floor not found.")
    source_id = project.get("router_floor_id", floors[0]["id"])
    source_floor = next((floor for floor in floors if floor["id"] == source_id), floors[0])
    ordered = sorted(floors, key=lambda item: item["elevation_m"])
    floor_count = abs(ordered.index(target_floor) - ordered.index(source_floor))
    source_z = float(source_floor["elevation_m"]) + float(project["router"].get("z", 2.4))
    target_z = float(target_floor["elevation_m"]) + 1.0
    width, height = float(target_floor["width_m"]), float(target_floor["height_m"])
    xs = [width * i / (resolution - 1) for i in range(resolution)]
    ys = [height * i / (resolution - 1) for i in range(resolution)]
    candidates: list[dict[str, Any]] = []
    x = min(step_m / 2.0, width / 2.0)
    while x <= width - min(step_m / 2.0, width / 2.0) + 1e-9:
        y = min(step_m / 2.0, height / 2.0)
        while y <= height - min(step_m / 2.0, height / 2.0) + 1e-9:
            router = {"x": x, "y": y}
            samples = [
                predict_rssi_3d_dbm(
                    sx, sy, target_z, router, source_z, target_floor["walls"],
                    int(project["frequency_mhz"]), float(project["tx_power_dbm"]),
                    float(target_floor.get("floor_loss_db", 18.0)), floor_count,
                )
                for sx in xs for sy in ys
            ]
            ordered_values = sorted(samples)
            candidates.append({
                "x": round(x, 2), "y": round(y, 2),
                "mean_rssi_dbm": round(sum(samples) / len(samples), 1),
                "worst_decile_dbm": round(ordered_values[max(0, int(len(ordered_values) * 0.1) - 1)], 1),
            })
            y += step_m
        x += step_m
    candidates.sort(
        key=lambda item: item["mean_rssi_dbm"] + 0.35 * item["worst_decile_dbm"],
        reverse=True,
    )
    return {
        "floor_id": floor_id, "floor_name": target_floor["name"],
        "recommendations": candidates[:5],
        "best": candidates[0] if candidates else None,
        "method": "Coarse grid search using 3D FSPL, target-floor wall crossings and simplified slab loss",
        "notice": "Estimate only. The router placement score must be validated with actual survey readings.",
    }


@app.get("/api/csi/ports")
def csi_ports() -> dict[str, Any]:
    try:
        return {"ports": csi_collector.ports()}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/csi/start")
def csi_start(config: CSIStartModel) -> dict[str, Any]:
    try:
        return csi_collector.start(config.port, config.baud, config.csi_column)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/csi/stop")
def csi_stop() -> dict[str, Any]:
    return csi_collector.stop()


@app.get("/api/csi/status")
def csi_status() -> dict[str, Any]:
    return csi_collector.status()


@app.get("/api/csi/frames")
def csi_frames(limit: int = Query(default=30, ge=1, le=120)) -> list[dict[str, Any]]:
    return csi_collector.recent(limit)


@app.post("/api/volumetric/import")
async def volumetric_import(request: Request, filename: str = Query(default="uploaded.csv", max_length=160)) -> dict[str, Any]:
    raw = await request.body()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV is larger than the 10 MB limit.")
    try:
        content = raw.decode("utf-8-sig")
        points = parse_volumetric_csv(content)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    saved = db.replace_volumetric_points(safe_source_name(filename), points)
    return {**saved, "preview": points[:10], "bounds": {
        key: [min(point[key] for point in points), max(point[key] for point in points)]
        for key in ("x", "y", "z", "rssi_dbm")
    }}


@app.get("/api/volumetric/scan-plan.csv")
def volumetric_scan_plan(
    width_m: float = Query(default=10.0, gt=0, le=100),
    depth_m: float = Query(default=8.0, gt=0, le=100),
    height_m: float = Query(default=2.4, gt=0, le=100),
    step_m: float = Query(default=0.25, ge=0.02, le=5),
) -> Response:
    try:
        waypoints = build_scan_plan(width_m, depth_m, height_m, step_m)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["sequence", "x", "y", "z"])
    writer.writeheader()
    writer.writerows(waypoints)
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nighthawk-scan-waypoints.csv"'},
    )


@app.get("/api/volumetric/points")
def volumetric_points() -> dict[str, Any]:
    points = db.get_volumetric_points()
    return {"point_count": len(points), "points": points}


@app.get("/api/project/export.json")
def project_export_json() -> Response:
    payload = json.dumps(db.get_project(), indent=2)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="nighthawk-project.json"'},
    )


@app.post("/api/project/import")
def project_import_json(project: ProjectModel) -> dict[str, Any]:
    return project_put(project)
