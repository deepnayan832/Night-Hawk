# NightHawk — Current System Architecture

**Release:** 1.1.0  
**Runtime:** Windows 10/11 x64 · Python 3.10+ · FastAPI · Three.js/WebGL · SQLite

This document describes source code currently present in the repository.

## 1. Runtime layout

```text
Windows 10/11
   ├── netsh wlan interface/BSSID scan
   ├── optional ESP32 CSI serial stream
   └── optional measured volumetric CSV
            │
            ▼
Python / FastAPI local server (127.0.0.1:8765)
   ├── wifi.py       Windows WLAN scan and signal-quality parsing
   ├── rf.py         FSPL, wall intersections, IDW, 3D slab-loss estimate
   ├── db.py         Projects, floors, surveys and volumetric point storage
   ├── csi.py        Optional serial collector and CSI I/Q parser
   ├── volumetric.py CSV validation and point conversion
   ├── scanplan.py   Bounded serpentine waypoint planner
   └── static/
       ├── index.html / style.css / app.js
       └── three-scene.js (built locally from nighthawk-ui/src/three-scene.js)
            │
            ▼
SQLite database
%USERPROFILE%\.nighthawk\nighthawk.sqlite3
```

The app binds to loopback only. Three.js is bundled locally during setup; the desktop app does not need a CDN at runtime.

## 2. Windows WLAN scanner

`GET /api/wifi/scan` invokes `netsh wlan show interfaces` and `netsh wlan show networks mode=bssid`. It parses connected-interface and visible BSSID fields when exposed by the Windows driver and command output.

Windows often provides signal quality as a percentage, not calibrated received power. The conversion shown in the UI is an approximation and is stored with a source label. Parser fixtures are tested in CI; live adapter validation remains a Windows hardware task.

## 3. Project and multi-floor data model

A project contains:
- Global RF frequency and transmit-power assumptions.
- A router x/y/z position and the floor on which the router is installed.
- An ordered set of floors, each with a unique ID, name, elevation, dimensions, wall height, wall segments and a simplified floor-slab loss value.
- Survey sessions and survey points carrying a floor ID.

Older one-floor projects are normalized into a single `floor_1` floor when read. New saves persist the floor list in the project JSON.

## 4. RF calculations

The RF module includes:
- Free-space path loss (FSPL) from 3D distance and frequency.
- 2D line-segment intersection between the router-to-grid path and wall segments on the target floor.
- Indicative material attenuation for drywall, wood, glass, brick, concrete and metal.
- A simple per-floor slab-loss allowance when the target floor differs from the router floor.
- Inverse-distance weighting (IDW) for interpolation of measured survey points.
- Grid generation for each floor.
- Candidate router ranking using the same theoretical model.

This is a simplified planning model, not a complete ray tracer. It omits calibrated antenna radiation patterns, multipath, furniture, dynamic interference, openings, and measured material properties. Predictions require real survey validation.

## 5. Three.js/WebGL renderer

The browser UI uses ordinary HTML/JavaScript for controls and API calls. The 3D renderer is built locally from the Three.js package using esbuild.

Current scenes:
- **Room scene:** floor slab, grid, material-coloured wall meshes, router marker and survey points.
- **RF surface:** Three.js mesh built from measured or predicted coverage grid values, with signal strength mapped to colour and elevation.
- **Volumetric cloud:** 3D point cloud from imported x/y/z/RSSI CSV data.

OrbitControls support rotate, pan and zoom. A compatible browser and GPU/WebGL support are required. CI builds the renderer bundle, but visual hardware validation must still be done on the target PC.

## 6. CSI serial module

The optional CSI view:
- Lists serial ports using pyserial.
- Connects using a selected baud rate and configurable CSI CSV field index.
- Parses the ESP32-CSI-Tool-style `CSI_DATA` CSV vector.
- Converts interleaved I/Q values to amplitude and phase.
- Displays the latest subcarrier amplitude vector and rolling per-subcarrier amplitude variance.

The default field index is 25 based on the documented upstream live-plot parser. Different firmware forks can change the CSV field layout. This is a signal-variation visualizer, not a validated people detector or room imager. Physical ESP32 validation remains required.

## 7. Volumetric datasets and waypoint plans

`POST /api/volumetric/import` validates UTF-8 CSV rows with `x,y,z,rssi_dbm` (or `rssi`) columns, enforces coordinate/value/row-count limits, and stores the points in SQLite. The browser renders stored data as a Three.js point cloud.

`GET /api/volumetric/scan-plan.csv` creates a bounded serpentine waypoint order for a rectangular scan volume. It exports coordinates only; it does not operate or move a motorized rig.

## 8. API surface

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | API and database health |
| GET | `/api/hardware/status` | Platform and hardware capability status |
| GET | `/api/wifi/scan` | Scan Windows-visible WLAN networks |
| GET / PUT | `/api/project` | Read/save multi-floor project |
| GET | `/api/project/export.json` | Download project JSON |
| POST | `/api/project/import` | Validate/import project JSON |
| GET / POST | `/api/surveys` | List/create sessions |
| GET / POST | `/api/surveys/{id}/points` | Read/save survey points |
| GET | `/api/coverage/measured` | Per-floor IDW coverage |
| GET | `/api/coverage/predicted` | Per-floor 3D RF estimate |
| GET | `/api/router/optimize` | Per-floor router candidate ranking |
| GET | `/api/csi/ports` | List serial ports |
| POST | `/api/csi/start` / `/api/csi/stop` | Start/stop CSI serial collector |
| GET | `/api/csi/status` / `/api/csi/frames` | CSI state/recent frames |
| POST | `/api/volumetric/import` | Import volumetric CSV |
| GET | `/api/volumetric/points` | Read saved point cloud |
| GET | `/api/volumetric/scan-plan.csv` | Export waypoint plan |
| GET | `/api/surveys/{id}/export.csv` | Export survey points |
| GET | `/docs` | FastAPI API documentation |

## 9. Security and hardware boundaries

- WLAN discovery uses normal Windows WLAN commands.
- The app does not inject packets, deauthenticate devices, crack passwords or attempt unauthorized network access.
- FastAPI binds to `127.0.0.1`; do not expose it on a network without authentication and a security review.
- CSI serial collection is opt-in and uses only the selected COM port.
- No motorized controller commands are issued. A specific controller protocol and safety interlocks are required before rig control is added.
- Survey/volumetric files may contain private household network data; review exports before sharing.
