# NightHawk — Current System Architecture

**Release:** 1.0.0 Tier 1 baseline  
**Runtime:** Windows 10/11 x64 · Python 3.10+ · FastAPI · browser-based HTML/CSS/JavaScript

This document describes the code currently present in the repository, not planned modules from earlier design drafts.

## 1. Runtime layout

```text
Windows 10/11
   │
   ├── netsh wlan show interfaces
   └── netsh wlan show networks mode=bssid
            │
            ▼
Python / FastAPI local server (127.0.0.1:8765)
   ├── wifi.py       Windows scan adapter and signal-quality parsing
   ├── rf.py         FSPL, wall intersection/loss, IDW and grid generation
   ├── db.py         SQLite projects, sessions and survey points
   └── static/
       ├── index.html
       ├── style.css
       └── app.js    Floor-plan editor, survey workflow, canvas views
            │
            ▼
SQLite database
%USERPROFILE%\.nighthawk\nighthawk.sqlite3
```

The service binds to loopback only by default. It is intended to be used by the same Windows machine running the server.

## 2. API modules

### Wi-Fi scanner

`GET /api/wifi/scan` invokes Windows `netsh` commands and parses visible network/BSSID blocks. The scanner exposes SSID, BSSID, signal percentage, channel, radio type and authentication where the OS output contains those fields.

Windows commonly exposes signal quality as a percentage, not a calibrated received-power reading. NightHawk displays an approximate conversion to dBm and retains a source label. Drivers and Windows display languages can change field availability.

### Project and survey storage

The SQLite layer maintains:
- One editable floor-plan project (dimensions, wall material segments, router position, frequency and transmit-power assumption).
- Named survey sessions.
- Survey points with x/y/z, SSID/BSSID, supplied RSSI value, signal percentage, source and timestamp.

The default data folder is `%USERPROFILE%\.nighthawk`. Set `NIGHTHAWK_DATA_DIR` before launch to use another location.

### RF calculations

The RF module includes:
- Free-space path loss (FSPL).
- 2D line-segment intersection between router-to-sample path and a wall segment.
- Indicative per-wall attenuation for drywall, wood, glass, brick, concrete and metal.
- Inverse-distance weighting (IDW) for interpolation of user-recorded survey points.
- Grid generation for measured and theoretical coverage views.
- Router position ranking using a coarse candidate grid and simplified model score.

Predicted coverage is a simplified planning estimate. It does not model measured antenna patterns, multipath, furniture, neighboring interference, exact building-material properties, or full 3D propagation.

## 3. Browser interface

The local UI uses static HTML, CSS and JavaScript without a Node build step or external UI libraries.

Current views:
1. Overview and local service status.
2. Wi-Fi scanner.
3. Home survey and saved measurements.
4. 2D floor-plan editor with material-labelled wall segments and router placement.
5. Isometric canvas projection of the room geometry.
6. Measured and theoretical coverage maps.

The 3D panel is a canvas-based isometric geometric preview. It is not a WebGL/Three.js scene in this release.

## 4. API surface

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | API and database health |
| GET | `/api/hardware/status` | Supported and unavailable hardware modes |
| GET | `/api/wifi/scan` | Scan Windows-visible WLAN networks |
| GET / PUT | `/api/project` | Load/save the floor plan and RF assumptions |
| GET | `/api/project/export.json` | Download project JSON backup |
| POST | `/api/project/import` | Validate and import project JSON |
| GET / POST | `/api/surveys` | List/create survey sessions |
| GET / POST | `/api/surveys/{id}/points` | List/save survey points |
| GET | `/api/coverage/measured` | IDW grid from saved points |
| GET | `/api/coverage/predicted` | Theoretical RF grid |
| GET | `/api/router/optimize` | Rank candidate router positions |
| GET | `/api/surveys/{id}/export.csv` | Export survey points as CSV |
| GET | `/docs` | FastAPI interactive API documentation |

## 5. Security boundaries

- WLAN discovery uses ordinary Windows WLAN commands.
- The application does not inject packets, deauthenticate clients, crack passwords or attempt unauthorized access.
- The local API binds to `127.0.0.1`; do not change the bind address without adding authentication and an explicit network security review.
- Survey data may contain household network identifiers. Review it before sharing CSV exports.

## 6. Future modules (not implemented)

ESP32 CSI serial capture, CSI human-presence experiments, motorized scanner control, volumetric live scanning, full 3D WebGL rendering, multi-floor propagation, image/CAD plan import and measured-model calibration are not included in the 1.0.0 codebase.
