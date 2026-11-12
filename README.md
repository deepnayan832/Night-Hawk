<div align="center">

# 🌙 NIGHTHAWK

### Local Wi-Fi Intelligence · RF Surveying · Spatial Mapping

**Measure wireless coverage. Draw your space. Compare real readings with an indoor RF model.**

[![License](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows)](HARDWARE_REQUIREMENTS.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](requirements.txt)
[![CI](https://github.com/deepnayan832/Night-Hawk/actions/workflows/ci.yml/badge.svg)](https://github.com/deepnayan832/Night-Hawk/actions/workflows/ci.yml)

[**Project Website**](https://deepnayan832.github.io/Night-Hawk/) · [**Architecture**](ARCHITECTURE.md) · [**Hardware Guide**](HARDWARE_REQUIREMENTS.md) · [**Issues**](https://github.com/deepnayan832/Night-Hawk/issues)

</div>

---

## ✨ What NightHawk does

NightHawk is a local Windows application for surveying the Wi-Fi environment around your home and visualizing indoor coverage against a user-drawn floor plan.

The first runnable release includes a Python/FastAPI local service, a browser-based interface, Windows WLAN scanning through `netsh`, SQLite storage, a floor-plan editor, measured-signal interpolation, and a simplified indoor RF propagation model.

> **Important:** NightHawk does not perform Wi-Fi X-ray imaging. It does not infer architectural structure from ordinary router signals. You draw or import the geometry yourself; RF coverage is measured or modelled inside that geometry.

## ✅ Current working scope

| Module | Current implementation |
|---|---|
| Windows Wi-Fi Scanner | Lists visible BSSIDs, SSIDs, signal quality, channel and security using Windows `netsh` |
| Signal strength | Shows Windows signal percentage and a clearly labelled approximate dBm conversion |
| Survey sessions | Create named sessions and store sample positions in a local SQLite database |
| Measurement capture | Click a room position and save a selected network's estimated signal or a manually entered dBm value |
| Floor-plan editor | Set dimensions, draw/remove material-labelled walls and place the router |
| 2D plan view | Canvas-based floor-plan editing on a metre grid |
| 3D spatial preview | Local isometric canvas projection of room geometry and wall height; not a WebGL/Three.js engine |
| Measured heatmap | IDW interpolation from saved survey points |
| Predicted coverage | Simplified FSPL plus per-wall material attenuation model |
| Router placement | Grid-search ranking of candidate router positions using the same simplified model |
| Survey export | Download a session's measurements as CSV |
| Project backup | Export/import floor-plan and RF settings as JSON |
| Local persistence | SQLite database stored under the user's home directory |

**Not in this release:** ESP32 CSI capture, human-presence sensing, automated motorized scanning, multi-floor geometry, CAD/image import, true Three.js/WebGL rendering, and detailed antenna/interference simulation. These are future milestones, not completed features.

## 🖥️ Requirements

- Windows 10 or Windows 11 x64.
- Python 3.10 or newer.
- PowerShell 5.1 or PowerShell 7.
- A Windows WLAN-supported Wi-Fi adapter for live scanning.
- Internet access is needed once to install Python packages. The app itself serves locally on your PC; the UI does not load external JavaScript libraries or fonts.

Windows may require **Settings → Privacy & security → Location → Let desktop apps access your location** to allow nearby Wi-Fi/BSSID enumeration.

## ⚡ Quick start

Open PowerShell in the cloned repository directory.

### 1. Clone

```powershell
git clone https://github.com/deepnayan832/Night-Hawk.git
Set-Location Night-Hawk
```

### 2. Install dependencies and run tests

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

This creates a local `.venv`, installs the small Python dependency set from `requirements.txt`, compiles the Python files, and runs the unit tests.

### 3. Launch

```powershell
.\start.ps1
```

Open manually at [http://127.0.0.1:8765](http://127.0.0.1:8765) if the browser does not open automatically.

### 4. Stop

```powershell
.\stop.ps1
```

Run diagnostics at any time:

```powershell
.\diagnose.ps1
```

## 🧭 First-use workflow

1. Open **Wi-Fi Scanner** and select **Scan now**.
2. Open **Home Survey** and create a survey session.
3. Select the network you are measuring. Walk to a physical position and click that location on the plan.
4. Save the sample. Repeat at several positions around the home.
5. Open **Coverage Maps** and select the survey to generate a measured IDW heatmap.
6. Open **Floor Plan & 3D** to adjust room size, draw internal walls with the correct material, and position the router.
7. Generate the predicted RF map or run the router-position ranking. Validate any model suggestion with another walk survey.

## 🧪 How the RF model works

NightHawk keeps two different data sources separate:

- **Measured map:** inverse-distance weighting (IDW) between saved survey samples.
- **Predicted map:** free-space path loss (FSPL) plus simplified material loss for wall segments crossed by the path from the router to a grid point.

The predicted map uses indicative attenuation constants. Real losses depend on construction, wall thickness, moisture, furniture, antenna orientation, multipath and interference. Treat model output as a planning aid, not a calibrated measurement.

## 📶 Signal accuracy

Windows `netsh wlan show networks mode=bssid` typically reports signal quality as a percentage, not calibrated RSSI in dBm. NightHawk converts that percentage to an approximate display value using:

```text
estimated_dBm = (signal_percent / 2) - 100
```

That conversion is approximate. The app labels its origin in the saved `measurement_source` field. Manual dBm entry is available for measurements obtained from a calibrated instrument or a driver that exposes actual RSSI.

## 💾 Data and privacy

- Local database: `%USERPROFILE%\.nighthawk\nighthawk.sqlite3`.
- Override the storage directory with the `NIGHTHAWK_DATA_DIR` environment variable before starting the server.
- The service binds to `127.0.0.1` only; it is not exposed to your LAN by default.
- Survey points and floor plans are not uploaded by the application.
- Wi-Fi scanning uses Windows WLAN commands; it does not crack passwords, inject packets, or deauthenticate clients.

## 🏗️ Architecture

```text
Browser UI (HTML / CSS / JavaScript)
          │ same-origin HTTP
          ▼
FastAPI local server (127.0.0.1:8765)
          ├── Windows WLAN adapter (netsh)
          ├── RF maths (FSPL, wall loss, IDW)
          └── SQLite (%USERPROFILE%/.nighthawk/)
```

Key source files:

| Path | Responsibility |
|---|---|
| `nighthawk-backend/main.py` | FastAPI routes, validation and static app serving |
| `nighthawk-backend/wifi.py` | Windows WLAN scanner and signal-quality normalization |
| `nighthawk-backend/rf.py` | FSPL, wall intersection/attenuation, IDW and grid generation |
| `nighthawk-backend/db.py` | SQLite schema and persistence |
| `nighthawk-backend/static/` | Browser interface and visualizations |
| `nighthawk-backend/tests/` | RF and database unit tests |

## 🧰 API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service and local database status |
| GET | `/api/hardware/status` | Hardware capability and limitation report |
| GET | `/api/wifi/scan` | Scan Windows-visible Wi-Fi networks |
| GET / PUT | `/api/project` | Read or save the floor plan and router settings |
| GET | `/api/project/export.json` | Download the project as JSON |
| POST | `/api/project/import` | Validate and import a project JSON payload |
| GET / POST | `/api/surveys` | List or create survey sessions |
| GET / POST | `/api/surveys/{id}/points` | Read or save survey points |
| GET | `/api/coverage/measured` | Generate IDW coverage from saved points |
| GET | `/api/coverage/predicted` | Generate simplified RF model coverage |
| GET | `/api/router/optimize` | Rank candidate router positions |
| GET | `/api/surveys/{id}/export.csv` | Export survey samples to CSV |

Interactive API documentation is available at [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs) while the server is running.

## 🧱 Hardware tiers and limitations

| Tier | Hardware | Current state |
|---|---|---|
| Tier 1 | Windows PC + ordinary Wi-Fi adapter/router | Supported for netsh scanning, survey workflow and model-based visualization |
| Tier 2 | Compatible ESP32 CSI board + firmware | Not implemented; hardware and serial protocol integration remain future work |
| Tier 3 | Motorized 2D/3D gantry + probe/controller | Not implemented; external rig integration remains future work |

Ordinary Wi-Fi hardware does not provide high-resolution through-wall structural imaging. CSI sensing, where supported by compatible hardware, can reveal channel variations associated with motion but is not architectural X-ray vision.

## 🧪 Tests and CI

Run tests locally:

```powershell
Push-Location .\nighthawk-backend
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
Pop-Location
```

GitHub Actions also runs Python compilation, unit tests, and JavaScript syntax validation on pushes and pull requests.

## 🤝 Contributing

Bug reports and reproducible fixes are welcome. Include your Windows version, Wi-Fi adapter/driver, Python version, steps to reproduce, and whether a value was measured, estimated or manually entered. Never publish private SSIDs/BSSIDs or raw household survey data without checking the export first.

## 📚 Project documents

- [Implementation status](IMPLEMENTATION_STATUS.md)
- [System architecture](ARCHITECTURE.md)
- [Hardware requirements](HARDWARE_REQUIREMENTS.md)
- [Upstream research audit](REPOSITORY_AUDIT.md)
- [License notes](LICENSE_AUDIT.md)

## 📄 License

The NightHawk original code is licensed under [MIT](LICENSE). Referenced upstream repositories retain their own licenses and terms. No upstream repository should be assumed to be bundled into NightHawk unless the corresponding source and notices are actually present.

---

<div align="center">

**NightHawk — measure first. Model second. Never fake the signal.**

[Website](https://deepnayan832.github.io/Night-Hawk/) · [Repository](https://github.com/deepnayan832/Night-Hawk) · [Report an issue](https://github.com/deepnayan832/Night-Hawk/issues)

</div>
