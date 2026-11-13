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
   ├── wifi.py          Windows WLAN interface introspection, BSSID parser, hardware RSSI
   ├── network_intel.py Local IP/gateway ping, non-intrusive ARP device discovery, 2.4/5GHz spectrum analysis
   ├── rf.py            FSPL, wall intersections, IDW, 3D slab-loss estimate
   ├── db.py            Projects, floors, surveys, volumetric clouds, scan history and diffs
   ├── csi.py           Optional serial collector and CSI I/Q parser
   ├── volumetric.py    CSV validation and point conversion
   ├── scanplan.py      Bounded serpentine waypoint planner
   └── static/
       ├── index.html / style.css / app.js
       └── three-scene.js (built locally from nighthawk-ui/src/three-scene.js)
            │
            ▼
SQLite database
%USERPROFILE%\.nighthawk\nighthawk.sqlite3
```

The app binds to loopback only. Three.js is bundled locally during setup; the desktop app does not need a CDN at runtime.

## 2. Windows WLAN Scanner & Adapter Introspection

`GET /api/wifi/scan` invokes `netsh wlan show interfaces` and `netsh wlan show networks mode=bssid`. It parses connected-interface and visible BSSID fields when exposed by the Windows driver and command output.

`GET /api/network/interfaces` queries the Windows WLAN service for installed Wi-Fi adapters, reporting adapter name, description, GUID, MAC address, connection state, link transmit/receive rates (Mbps), radio type, signal percentage, and hardware-reported RSSI (dBm).

Windows percentage-to-dBm conversions in general network tables are explicitly distinguished from calibrated measurements and labeled by source.

## 2.1 Network Intelligence & Channel Congestion

`network_intel.py` provides:
- **Interface & Gateway Health (`/api/network/info`):** Queries local IPv4/IPv6 addresses, default gateway, subnet mask, and DNS servers using standard Windows network queries, measures round-trip ping latency to the gateway, and checks public DNS reachability.
- **Local Device Discovery (`/api/network/devices`):** Inspects the host ARP cache (`arp -a`) non-intrusively without sending broadcast storms or unauthorized probe packets, mapping IP addresses, MAC addresses, known vendor OUIs (e.g. Apple, Google, Intel, Espressif), and gateway identification.
- **Spectrum Overlap Analysis (`/api/network/channels`):** Calculates co-channel and adjacent-channel interference across 2.4 GHz channels (1-14 with spectral mask roll-off weighting) and 5 GHz channels (UNII-1, UNII-2, UNII-3), recommending cleanest channels for router configuration (favoring non-overlapping channels 1, 6, 11 on 2.4 GHz).

## 2.2 Scan History & Differencing

`db.py` persists complete Wi-Fi scans into SQLite (`wifi_scans` and `wifi_scan_entries` tables) in WAL mode.
- `GET /api/wifi/history`: Lists recorded historical scans with timestamps, network counts, and best signal.
- `GET /api/wifi/history/{scan_id}`: Retrieves full details of a specific scan.
- `GET /api/wifi/history/compare?scan_a={id}&scan_b={id}`: Computes differential metrics between two scans:
  - New APs appeared
  - APs dropped/disappeared
  - Persistent APs with per-BSSID and average signal delta ($\Delta$ dBm)
- `GET /api/wifi/history/export.csv` and `GET /api/wifi/history/export.json`: Export scan history for external analysis.

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

Camera modes (`setCameraMode(elementId, mode)`):
- **3D Orbit (`perspective`):** Full 3D orbiting around the center of the floor plan with rotate, pan, and zoom.
- **Top-Down (`top_down`):** Overhead 2D architectural blueprint view looking directly down along the Y-axis.
- **Room Walk (`room_walk`):** Eye-level interior perspective (1.65m height) positioned inside the floor space looking outward across room walls.

OrbitControls support rotate, pan and zoom. A compatible browser and GPU/WebGL support are required. CI builds the renderer bundle, and JavaScript syntax is verified in CI.

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
| GET | `/api/network/interfaces` | Windows WLAN adapters, MAC, link speeds, true hardware RSSI |
| GET | `/api/network/info` | Local IPv4/IPv6, gateway ping latency, DNS and internet connectivity |
| GET | `/api/network/devices` | Discovered local LAN devices via ARP table with OUI vendor lookups |
| GET | `/api/network/channels` | 2.4 GHz & 5 GHz channel congestion, overlap scores and best channels |
| GET | `/api/wifi/scan` | Scan Windows-visible WLAN networks (with optional auto-persistence) |
| GET | `/api/wifi/history` | List historical Wi-Fi scans from SQLite |
| GET / DELETE | `/api/wifi/history/{id}` | Retrieve or delete specific historical scan record |
| GET | `/api/wifi/history/compare` | Compare two scans (new APs, dropped APs, signal deltas) |
| GET | `/api/wifi/history/export.csv` | Export scan history to CSV |
| GET | `/api/wifi/history/export.json` | Export scan history to JSON |
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
