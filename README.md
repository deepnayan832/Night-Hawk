<div align="center">

# 🌙 NIGHTHAWK

### Local Wi-Fi Intelligence · RF Surveying · 3D Mapping

**Measure your wireless environment. Draw your floors. Inspect measured and modelled coverage.**

[![License](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows)](HARDWARE_REQUIREMENTS.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](requirements.txt)
[![CI](https://github.com/deepnayan832/Night-Hawk/actions/workflows/ci.yml/badge.svg)](https://github.com/deepnayan832/Night-Hawk/actions/workflows/ci.yml)

[**Project Website**](https://deepnayan832.github.io/Night-Hawk/) · [**Architecture**](ARCHITECTURE.md) · [**Hardware Guide**](HARDWARE_REQUIREMENTS.md) · [**Issues**](https://github.com/deepnayan832/Night-Hawk/issues)

</div>

---

## What NightHawk does

NightHawk is a local-first Windows application for WLAN discovery, floor-plan based RF surveying, multi-floor coverage estimates and 3D visualization.

The desktop app runs locally on the Windows PC. GitHub Pages hosts the project information site only; it cannot run the Python service or access your local Wi-Fi adapter.

> **Measurement integrity:** live adapter signal quality, manually entered measurements, interpolated heatmaps, theoretical RF estimates, and archived/imported datasets are different data sources. NightHawk labels their origin. It does not provide Wi-Fi X-ray vision or infer wall structure from ordinary router signals.

## Current application features

| Module | Current implementation |
|---|---|
| Windows Wi-Fi scanner | Uses Windows `netsh wlan` to list visible SSIDs/BSSIDs, signal quality, channel, authentication and live interface details |
| Network interfaces | Discovers all physical WLAN adapters with GUID, MAC, radio type, state, and hardware link rates (Rx/Tx Mbps) |
| Gateway & Network info | Detects local IP, subnet mask, default gateway, DNS servers, gateway ping latency, and internet status |
| Local device discovery | Safe passive/active subnet device discovery via Windows ARP table with vendor identification |
| Channel spectrum & overlap | Analyzes 2.4 GHz and 5 GHz channel congestion, co-channel interference, and adjacent channel overlap recommendations |
| Scan history & comparisons | Persists Wi-Fi environment scans in SQLite; diffs scans to track newly appeared, lost, and delta RSSI APs |
| Scan data export | Exports historical scan records to structured CSV and JSON formats |
| Signal quality | Shows the Windows percentage and true hardware RSSI in dBm where exposed, or labelled approximate conversions |
| Home survey | Create sessions, click a position on the floor plan, save a reading and export CSV |
| Multi-floor plans | Add floors with individual dimensions, elevations, wall geometry and floor-loss assumptions |
| Floor-plan editor | Draw/remove material-labelled walls, edit room dimensions and place the router on a selected floor |
| Three.js room view | Actual bundled Three.js/WebGL geometry with 3D Orbit, Top-Down 2D Orthographic, and Room Walk camera modes |
| Measured coverage | Per-floor IDW interpolation using saved survey samples |
| Predicted coverage | Per-floor 3D-distance FSPL model, target-floor wall intersections and simplified floor-slab attenuation |
| 3D RF surface | Three.js surface mesh with signal strength represented by elevation and colour |
| Router placement | Per-floor grid-search ranking using the simplified model |
| ESP32 CSI | Optional live serial reader; parses the ESP32-CSI-Tool CSV vector into I/Q-derived amplitude and phase |
| CSI analysis | Live subcarrier amplitude plot and rolling amplitude variance; not a validated people detector |
| Volumetric dataset viewer | Import `x,y,z,rssi_dbm` CSV data, persist it in SQLite and display a Three.js point cloud |
| Scan waypoint planner | Export a bounded serpentine x/y/z waypoint CSV for a manual or externally controlled scanner |
| Project backup | JSON project import/export |
| Local storage | SQLite database under the user's home directory |

## What still requires external equipment or validation

- CSI capture requires a compatible ESP32 board flashed with compatible firmware and connected by USB serial.
- The physical motorized scanner is not driven by this release. The waypoint planner exports a scan path; it does not command motors.
- The Windows WLAN scanner still needs testing on the actual PC and adapter that will run NightHawk.
- RF wall-loss constants are indicative assumptions. They must be calibrated against measurements for a particular building.
- Floor-to-floor attenuation is a simplified slab-loss allowance, not a full 3D ray tracer.
- Detailed antenna patterns, multipath, furniture, and neighbouring-network interference are not fully modelled.
- No architectural through-wall imaging is provided.

## Requirements

- Windows 10/11 x64.
- Python 3.10 or newer.
- Node.js 20+ and npm (used once to bundle Three.js locally).
- PowerShell 5.1 or PowerShell 7.
- A Wi-Fi adapter with a working Windows WLAN driver for live scanning.
- Optional: a compatible ESP32 CSI device and firmware for live CSI serial data.

Windows may require **Settings → Privacy & security → Location → Let desktop apps access your location** to enumerate nearby BSSIDs.

## Quick start

Open PowerShell in the directory where you want the project.

### 1. Clone the repository

```powershell
git clone https://github.com/deepnayan832/Night-Hawk.git
Set-Location Night-Hawk
```

### 2. Install and build

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

The setup script:
- Creates a local Python virtual environment.
- Installs Python dependencies, including FastAPI and pyserial.
- Installs the local Three.js/esbuild frontend dependencies.
- Builds the bundled Three.js renderer into `nighthawk-backend/static/`.
- Compiles Python source and runs the unit/integration tests.

### 3. Start the local app

```powershell
.\start.ps1
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Stop it with:

```powershell
.\stop.ps1
```

Check your machine and adapter with:

```powershell
.\diagnose.ps1
```

## First-use workflow

1. Open **Wi-Fi Scanner** and run a scan.
2. Open **Floor Plan & 3D**, create the floors you need, set elevations and dimensions, then draw internal walls with approximate materials.
3. Choose the floor containing the router and place it on that floor.
4. Open **Home Survey**, create a session, select the floor, walk to a real location and click that point on the plan.
5. Save multiple readings around the home. Use manual dBm input only when you have an actual reading from a suitable instrument or driver.
6. In **Coverage Maps**, choose the floor and compare its measured IDW surface with the theoretical RF model.
7. Use the router optimizer as a candidate-ranking aid, then validate a position with another real walk survey.

## CSI hardware workflow

1. Use a supported ESP32 board and flash a compatible ESP32-CSI-Tool firmware build.
2. Connect the board by a USB data cable and confirm that Windows exposes a COM port.
3. Open **CSI Sensing**, refresh the ports, select the correct COM port and baud rate, then connect.
4. The default CSI vector column is 25, matching the documented ESP32-CSI-Tool serial plotting layout. Change it when using a firmware fork with different columns.
5. Inspect live amplitude and rolling variance. No person classification or room imaging is performed.

The CSI stream parser expects the selected CSV field to contain interleaved I/Q integer samples. Firmware builds can change CSV layouts; inspect the actual serial output before changing the field index.

## Volumetric data workflow

The **Volumetric Data** view accepts CSV files with these required headers:

```csv
x,y,z,rssi_dbm
0,0,1.0,-48
1,0,1.0,-56
1,1,1.0,-63
```

Coordinates are metres and signal values are dBm. The imported points are stored locally in SQLite and rendered as a 3D point cloud. The scan waypoint planner exports a serpentine CSV for an external/manual scanning workflow; it does not move a rig.

## RF model and limitations

NightHawk keeps measurement and modelling separate:

- **Measured coverage:** IDW interpolation over saved samples on the selected floor.
- **Predicted coverage:** free-space path loss, 2D wall-segment crossings on the target floor, and a simplified slab-loss allowance for each floor crossed.
- **Router ranking:** coarse candidate search using the same theoretical model.

The model does not include calibrated antenna radiation patterns, detailed 3D ray tracing, furniture, doors/windows as openings, dynamic interference, or measured material attenuation. Treat predictions as planning estimates, not guaranteed signal levels.

Windows often exposes signal quality as a percentage rather than calibrated RSSI. The approximate display conversion is:

```text
estimated_dBm = (signal_percent / 2) - 100
```

The app stores a measurement-source label so estimated and manually entered values are not silently mixed.

## Privacy and local data

- Default data directory: `%USERPROFILE%\.nighthawk\`.
- Database: `nighthawk.sqlite3`.
- Override storage with `NIGHTHAWK_DATA_DIR` before starting the app.
- FastAPI binds to `127.0.0.1` only.
- SSIDs/BSSIDs can identify your home network. Review CSV files before sharing them.
- Wi-Fi discovery uses Windows WLAN commands; it does not crack passwords, inject packets or deauthenticate clients.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API and database status |
| GET | `/api/hardware/status` | Platform and hardware capability status |
| GET | `/api/wifi/scan` | Windows WLAN scan |
| GET / PUT | `/api/project` | Read/save multi-floor project |
| GET | `/api/project/export.json` | Download project JSON |
| POST | `/api/project/import` | Validate/import project JSON |
| GET / POST | `/api/surveys` | List/create survey sessions |
| GET / POST | `/api/surveys/{id}/points` | Read/save measurement points |
| GET | `/api/coverage/measured` | Per-floor measured IDW coverage |
| GET | `/api/coverage/predicted` | Per-floor simplified 3D RF estimate |
| GET | `/api/router/optimize` | Per-floor router-position ranking |
| GET | `/api/csi/ports` | Detect serial ports |
| POST | `/api/csi/start` / `/api/csi/stop` | Start/stop live CSI collection |
| GET | `/api/csi/status` / `/api/csi/frames` | CSI collector state and recent frames |
| POST | `/api/volumetric/import` | Import measured CSV point cloud |
| GET | `/api/volumetric/points` | Read saved point cloud |
| GET | `/api/volumetric/scan-plan.csv` | Export bounded serpentine waypoints |
| GET | `/api/surveys/{id}/export.csv` | Export survey samples |
| GET | `/docs` | Interactive FastAPI documentation |

## Tests and CI

The GitHub Actions workflow checks:
- Python compilation.
- RF formula and interpolation tests.
- SQLite persistence tests.
- WLAN parser fixture tests.
- CSI CSV parsing tests.
- Volumetric CSV and scan-plan validation tests.
- FastAPI integration tests for multi-floor coverage and imports.
- Node syntax validation and local Three.js bundle build.

A green CI run validates code paths in the CI environment. It does not substitute for testing on a real Windows Wi-Fi adapter or with physical ESP32/motor hardware.

## Project documentation

- [Implementation status](IMPLEMENTATION_STATUS.md)
- [System architecture](ARCHITECTURE.md)
- [Hardware requirements](HARDWARE_REQUIREMENTS.md)
- [Upstream research audit](REPOSITORY_AUDIT.md)
- [License notes](LICENSE_AUDIT.md)

## License

The original NightHawk source is licensed under [MIT](LICENSE). Referenced upstream projects retain their own licenses and terms. The motorized controller and optional hardware protocols are not bundled as third-party code.

---

<div align="center">

**NightHawk — measure first. Model second. Never fake the signal.**

[Website](https://deepnayan832.github.io/Night-Hawk/) · [Repository](https://github.com/deepnayan832/Night-Hawk) · [Report an issue](https://github.com/deepnayan832/Night-Hawk/issues)

</div>
