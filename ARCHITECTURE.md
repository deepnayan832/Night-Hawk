# Project Nighthawk — System Architecture

## 1. Architectural Vision

Project Nighthawk is a unified, local-first Wi-Fi Intelligence and 3D Mapping System designed for Windows 10/11 x64. It merges real-time native Windows Wi-Fi surveying, floor plan drafting, 2D/3D physics-based RF propagation modeling, and optional volumetric and CSI sensing into a cohesive, responsive desktop-class application.

```
+-----------------------------------------------------------------------------------------------+
|                                    PROJECT NIGHTHAWK UI                                       |
|                  React 19 + TypeScript + Tailwind CSS + Lucide Icons + Three.js               |
+-----------------------------------------------------------------------------------------------+
|  1. Overview              |  6. 2D Signal Heatmap    | 11. Measurement History                |
|  2. Live Wi-Fi Scanner    |  7. 3D Coverage Map      | 12. Data Import / Export               |
|  3. Home Survey           |  8. Router Optimizer     | 13. Settings                           |
|  4. Floor Plan Editor     |  9. Volumetric Scanner   | 14. Hardware Status                    |
|  5. 3D Home View          | 10. CSI Sensing Module   |                                        |
+-----------------------------------------------------------------------------------------------+
                                                |
                                      REST API & WebSockets
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                               NIGHTHAWK PYTHON FASTAPI BACKEND                                |
|                                   (Port 8765, Windows x64)                                    |
+-----------------------------------------------------------------------------------------------+
| [Core Modules]                                                                                |
| - Native Windows Wi-Fi Service (netsh wlan / Win32 wlanapi regex parser & live polling)      |
| - Survey & Session Engine (Multi-floor point records, distance calibration, persistent store) |
| - Spatial Interpolation Engine (Inverse Distance Weighting, Scipy RBF, grid generation)       |
| - ITU-R P.2040 RF Propagation & Attenuation Engine (Multi-Wall Model, FSPL, Band loss)       |
| - Router Placement Optimization & Interference Analyzer (Channel overlap, SNR estimation)    |
| - Volumetric 3D Scanner Adapter (Neumi CSV parser, spatial slice voxelization)                |
| - Wi-Fi CSI Stream Processor (ESP32 serial reader, subcarrier amplitude/phase, variance math) |
| - Local Storage Manager (SQLite database + JSON/CSV import/export pipelines)                  |
+-----------------------------------------------------------------------------------------------+
                                                |
                                                v
+-----------------------------------------------------------------------------------------------+
|                                 OPERATING SYSTEM & HARDWARE                                   |
+-----------------------------------------------------------------------------------------------+
| - Windows 10/11 WLAN AutoConfig (WlanSvc) & Native Wi-Fi Adapter (Realtek, Intel, Broadcom)   |
| - Local Filesystem Storage (`~/.nighthawk/data.sqlite3`, project exports)                     |
| - (Optional) ESP32 Virtual COM Ports (CH340, CP2102) via PySerial                             |
| - (Optional) Ethersweep Stepper Controller UDP Sockets (Port 8888)                            |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Component Design & Inter-Module Data Flow

### A. Wi-Fi Scanner Module (Adapted from `wifi-heatmapper` & `open-heat`)
- **Engine:** Python `netsh wlan show interfaces` and `netsh wlan show networks mode=bssid` parser with native regex matchers.
- **Capabilities:**
  - Extracts active SSID, BSSID, Signal %, RSSI in dBm (using Windows 11 direct RSSI reading or normalized formula $RSSI = (Signal\% / 2) - 100$), Band (2.4 GHz, 5 GHz, 6 GHz), Channel, Radio Type (802.11n/ac/ax), Link Rx/Tx Speeds (Mbps).
  - Background live polling loop every 1.5 seconds.
  - Returns unified JSON payload for the frontend.

### B. Survey & 2D Floor Plan Engine (Adapted from `SignalPlan` & `wifi-heatmapper`)
- **Floor Plan Data Structure:**
  - Walls with endpoints $(x_1, y_1) \to (x_2, y_2)$, thickness, and material classification.
  - Materials: `drywall`, `brick`, `concrete`, `glass`, `wood`, `metal`.
  - Openings: doors, windows.
  - Multi-floor elevation stacking with floor slab attenuation (`timber-joist`, `concrete-slab`).
- **Survey Workflow:**
  - Interactive click-to-measure: Users select a physical point on the calibrated floor plan canvas.
  - Current Wi-Fi readings are captured and stored in the active session.
  - Supports multiple survey spots, multiple APs, and historical re-surveys.

### C. 2D & 3D Spatial Coverage Engine
- **Interpolation (Real Measurements):**
  - Uses Inverse Distance Weighting (IDW) with tunable power parameter $p$ ($p=2.0$) and radial basis function (RBF) smoothing to generate continuous heatmap textures over the floor plan.
- **Simulation (Theoretical Propagation):**
  - Combines Free-Space Path Loss:
    $$FSPL(d, f) = 20 \log_{10}(d) + 20 \log_{10}(f) + 20 \log_{10}\left(\frac{4\pi}{c}\right)$$
  - With ITU-R P.2040 Multi-Wall Attenuation:
    $$PL(d) = FSPL(d, f) + \sum_{i} WAF_i \cdot N_i + FAF \cdot N_{floors}$$
    where $WAF_i$ is the empirical wall attenuation factor for material $i$, computed across 2.4 GHz, 5 GHz, and 6 GHz.
- **Measured vs. Predicted Comparison:**
  - Calculates point-by-point residual delta $\Delta = RSSI_{measured} - RSSI_{predicted}$, highlighting wall modeling errors or unexpected interference.

### D. 3D Home Visualization Engine (Three.js WebGL)
- **Geometry Generation:**
  - Walls extruded as Three.js box meshes with material-accurate textures and colors.
  - Floor slabs stacked along the vertical $Y$-axis with user-adjustable inter-floor spread.
  - Access points rendered as 3D router markers with spherical coverage halos.
  - Survey spots rendered as 3D vertical pins color-coded by measured RSSI.
  - OrbitControls for smooth 360-degree rotation, pan, and zoom.

### E. Volumetric Scanner Adapter (Adapted from `3D_wifi_scanner` & `ethersweep`)
- **Data Parser:** Reads 3D scanner CSV stacks `(x, y, z, RSSI)`.
- **Visualization:**
  - 3D voxel point cloud with color-mapped intensity.
  - Planar slice inspector allowing users to scrub through horizontal and vertical signal cross-sections.
  - Motorized rig driver interface sending UDP step commands to Ethersweep controllers.

### F. Wi-Fi CSI Sensing Module (Adapted from `ESP32-CSI-Tool`, `WiFi-CSI-Human-Detection`, `csi-gui-rs`)
- **Serial Connection:** Discovers and connects to Windows Virtual COM ports (`COM1..COM32`) at 115200 or 921600 baud.
- **Frame Decoding:** Parses `CSI_DATA` CSV frames into subcarrier matrices:
  - 64 subcarriers (20 MHz) or 128 subcarriers (40 MHz).
  - Extracts raw I/Q (In-phase / Quadrature) components to compute Subcarrier Amplitude $A_i = \sqrt{I_i^2 + Q_i^2}$ and Phase $\theta_i = \arctan2(Q_i, I_i)$.
- **Motion & Presence Detection:**
  - Sliding window variance of high-frequency subcarriers:
    $$\sigma^2 = \frac{1}{W} \sum_{t=0}^{W-1} (A_{t} - \bar{A})^2$$
  - Exceeding dynamic calibration baseline triggers "Human Motion Detected" in the room's Fresnel zone.

---

## 3. Data Schema & Contracts

### Unified Survey Point Record
```json
{
  "id": "spot_101",
  "timestamp": "2026-11-12T22:30:00.000Z",
  "floor_id": "floor_1",
  "x": 4.5,
  "y": 6.2,
  "z": 1.0,
  "ssid": "Excitel_Nayan",
  "bssid": "b4:f9:49:76:17:41",
  "band": "5 GHz",
  "frequency_mhz": 5745,
  "channel": 149,
  "rssi_dbm": -42,
  "signal_percent": 98,
  "link_speed_mbps": 390,
  "measurement_source": "windows_netsh"
}
```

### Material Attenuation Lookup (dB Loss)
| Material | 2.4 GHz | 5 GHz | 6 GHz | Description |
|---|---|---|---|---|
| `drywall` | 2.5 dB | 3.5 dB | 4.2 dB | Standard gypsum wallboard partition |
| `wood` | 3.0 dB | 4.5 dB | 5.0 dB | Solid wood door / timber paneling |
| `glass` | 2.0 dB | 3.0 dB | 3.8 dB | Single / double standard window |
| `low-e-glass` | 14.0 dB | 24.0 dB | 29.7 dB | Low-emissivity coated metallic glass |
| `brick` | 8.5 dB | 12.0 dB | 14.5 dB | Standard red clay / masonry wall |
| `concrete` | 13.0 dB | 18.0 dB | 22.0 dB | Reinforced load-bearing concrete |
| `metal` | 26.0 dB | 32.0 dB | 35.0 dB | Steel door, elevator shaft, metal siding |
| `timber-joist` | 5.0 dB | 8.0 dB | 9.5 dB | Residential ceiling/floor slab |
| `concrete-slab`| 18.0 dB| 26.0 dB| 30.0 dB| Heavy commercial floor slab |

---

## 4. Security & Privacy Architecture
1. **100% Local-First:** No telemetry, no external cloud dependencies, no mandatory external logins. All project files, floor plans, and Wi-Fi measurements reside on the user's local disk (`~/.nighthawk/` or user-chosen export paths).
2. **Defensive Scanning:** Scans are passive beacon listeners via standard Windows APIs; no packet injection, deauthentication, or password cracking tools are included.
3. **Identifier Sanitization:** Export routines offer a "Sanitize BSSIDs / SSIDs" toggle to allow sharing coverage reports publicly without leaking MAC addresses.
