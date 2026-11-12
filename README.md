# PROJECT NIGHTHAWK — 3D Wi-Fi Home Intelligence & RF Mapping

Project Nighthawk is a unified, local-first Wi-Fi Intelligence and 3D RF Mapping System built for Windows 10/11 x64. It integrates real-time native Wi-Fi surveying, floor plan drafting, 2D/3D ITU-R P.2040 wave propagation simulation, router placement optimization, and modular Channel State Information (CSI) and volumetric 3D RF sensing into a high-performance desktop application.

---

## 1. Executive Summary & Capabilities

- **Zero Cloud Dependence:** 100% local-first operation. All floor plans, survey measurements, and network diagnostics remain stored on your computer in an ACID-compliant local SQLite database.
- **Hardware Truth Guarantee:** Explicit separation of what works natively on standard Windows PCs/laptops (Tier 1) versus optional external hardware (Tier 2 ESP32 CSI microcontrollers and Tier 3 motorized CNC scanning gantries). No fake X-ray scans or fabricated through-wall vision claims.
- **Physics-Based 3D Engine:** Real Multi-Wall Model (MWM) per ITU-R P.2040 and ITU-R P.1238, incorporating Free-Space Path Loss (FSPL) and empirical multi-frequency material attenuation across 2.4 GHz, 5 GHz, and 6 GHz bands.
- **Complete Walk-and-Click Survey:** Interactively map your home by walking and clicking your standing position on the floor plan to record true RSSI values in dBm.

---

## 2. Upstream Repositories & Integration Audit

Project Nighthawk inspects, respects, and integrates all 12 mandatory open-source upstream projects:

| # | Upstream Repository | Purpose & Integration Contribution | License | Hardware Tier |
|---|---|---|---|---|
| 1 | [hnykda/wifi-heatmapper](https://github.com/hnykda/wifi-heatmapper) | Windows Wi-Fi scanning routines (`wlanapi.dll` / `netsh`), WebGL heatmap layers, and survey walk workflow. | MIT | Tier 1 (PC + Router) |
| 2 | [dcchill/open-heat](https://github.com/dcchill/open-heat) | Windows `netsh wlan show interfaces` parsing, network ping diagnostics, and survey data format. | MIT | Tier 1 (PC + Router) |
| 3 | [J0nan/Wi-Fi_HeatMap](https://github.com/J0nan/Wi-Fi_HeatMap) | 2D spatial interpolation algorithms (Inverse Distance Weighting) and floor plan pixel-to-meter calibration math. | MIT | Tier 1 (PC + Router) |
| 4 | [ribaldorafael/wifi-heatmap](https://github.com/ribaldorafael/wifi-heatmap) | Channel interference calculation, dead-zone percentage metrics, and REST API architectural patterns. | MIT | Tier 1 (PC + Router) |
| 5 | [NC4321/SignalPlan](https://github.com/NC4321/SignalPlan) | **Core Target:** ITU-R P.2040 RF propagation engine (`pathLoss.ts`, `crossings.ts`, `materials.ts`), floor plan schema, and Three.js 3D multi-floor viewer (`View3D.tsx`). | MIT | Tier 1 (PC + Router) |
| 6 | [Neumi/3D_wifi_scanner](https://github.com/Neumi/3D_wifi_scanner) | 3D spatial volumetric RSSI $(X, Y, Z)$ concept, real physical scan dataset (`stack_data/*.csv`), and planar slice inspector. | Custom/Clean-room | Tier 3 (Optional Rig) |
| 7 | [Neumi/ethersweep](https://github.com/Neumi/ethersweep) | Motorized scanner driver architecture over UDP port 8888; isolated behind clean network boundary. | GPL-3.0 | Tier 3 (Optional Rig) |
| 8 | [DwayneCon/wifi-3d-fusion](https://github.com/DwayneCon/wifi-3d-fusion) | Multi-AP CSI signal preprocessing, phase sanitization, and subcarrier normalization formulas. | Apache-2.0 | Tier 2 (Optional ESP32) |
| 9 | [s-shrikanth/WiFi-CSI-Human-Detection](https://github.com/s-shrikanth/WiFi-CSI-Human-Detection) | Subcarrier moving variance filtering ($\sigma^2$) for human presence and motion detection across Fresnel zones. | MIT | Tier 2 (Optional ESP32) |
| 10 | [csi-rs/csi-gui-rs](https://github.com/csi-rs/csi-gui-rs) | Wire-v1 framing protocol, COM port device manager, and high-fidelity simulated hardware backend (`sim.rs`). | MIT / Apache-2.0 | Tier 2 (Optional ESP32) |
| 11 | [csi-rs/esp-csi-cli-rs](https://github.com/csi-rs/esp-csi-cli-rs) | Embedded Rust firmware target specification for high-baud serial streaming from ESP32 microcontrollers. | MIT / Apache-2.0 | Tier 2 (Optional ESP32) |
| 12 | [StevenMHernandez/ESP32-CSI-Tool](https://github.com/StevenMHernandez/ESP32-CSI-Tool) | Primary serial packet format (`CSI_DATA` CSV stream) and subcarrier extraction utility. | MIT | Tier 2 (Optional ESP32) |

---

## 3. Hardware Requirements & Tiers

```
+-------------------------------------------------------------------------------+
| TIER 1: Standard Hardware (100% Fully Functional Out-of-the-Box)              |
| - Standard Windows 10/11 x64 PC / Laptop                                      |
| - Integrated or USB Wi-Fi Adapter (802.11a/b/g/n/ac/ax/be)                    |
| - Any Commercial Wi-Fi Router (2.4 GHz, 5 GHz, or 6 GHz)                      |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
| TIER 2: Optional Wi-Fi CSI Hardware Module                                    |
| - 1 or more ESP32 / ESP32-S3 Microcontrollers over USB Virtual COM Port       |
| - Flashed with ESP32-CSI-Tool or esp-csi-cli-rs firmware                      |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
| TIER 3: Optional Motorized 3D Volumetric Scanning Rig                         |
| - 2-Axis / 3-Axis Motorized Gantry (e.g. 3D printer frame)                    |
| - Ethersweep Stepper Controllers over UDP Port 8888                           |
+-------------------------------------------------------------------------------+
```

---

## 4. Quickstart Guide (Windows 10/11 x64)

### Prerequisites
- Windows 10 (version 1903+) or Windows 11 x64.
- Python 3.10+ (Python 3.12/3.15 tested).
- Node.js 18+ (Node 22/24 tested).
- PowerShell 7 (`pwsh`) or Windows PowerShell 5.1.

### Setup and Build
Run the automated setup script to create the Python virtual environment, install backend packages, compile the Three.js frontend bundle, and run unit tests:

```powershell
pwsh -File .\setup.ps1
```

### Run Diagnostics
Verify that your Wi-Fi adapter, WLAN AutoConfig, COM ports, and dependencies are operating cleanly:

```powershell
pwsh -File .\diagnose.ps1
```

### Start Application
Launch the unified server and open the web application in your default browser at `http://127.0.0.1:8765`:

```powershell
pwsh -File .\start.ps1
```

### Stop Application
Gracefully shut down the background server and release port 8765:

```powershell
pwsh -File .\stop.ps1
```

---

## 5. Unified 14-Tab Feature Guide

1. **Overview:** System telemetry summary, active network card status, home coverage quality score, and hardware truth checklist.
2. **Live Wi-Fi Scanner:** Real-time Windows adapter metrics, true RSSI in dBm, link speeds (Rx/Tx), channel, frequency, and all visible access points with signal ranking.
3. **Home Survey:** Interactive walk-and-click floor plan survey. Click your location to record genuine signal readings; stores multi-AP measurements automatically.
4. **Floor Plan Editor:** 2D CAD drafting tool to draw walls, select RF materials (drywall, brick, concrete, glass, wood, metal), insert doors/windows, position routers, and configure multi-floor elevations.
5. **3D Home View:** Three.js WebGL model rendering extruded 3D walls, stacked floor slabs, floor elevation spread slider, and 3D access points with OrbitControls.
6. **2D Signal Heatmap:** Continuous measured heatmap interpolated via Inverse Distance Weighting (IDW) with contour thresholds, dead-zone indicators, and confidence masking.
7. **3D Coverage Map:** 3D RF coverage visualization combining the 3D home geometry with simulated ITU-R propagation surfaces and residual delta comparisons against actual survey points.
8. **Router Optimizer:** Analyzes co-channel and adjacent-channel RF interference, calculates coverage quality scores, and simulates alternative AP mounting coordinates.
9. **Volumetric Scanner:** 3D spatial voxel visualization of Neumi's physical wave diffraction dataset (`stack_data/*.csv`), featuring 3D point clouds and horizontal/vertical slice scrubbers.
10. **CSI Sensing:** Real-time 64-subcarrier OFDM amplitude waterfall spectrogram, phase plot, and Fresnel motion detection gauge with automatic COM port selection and high-fidelity wire-v1 simulation.
11. **Measurement History:** Historical survey session comparisons, before/after router relocation diffs, and signal drift over time.
12. **Data Import / Export:** Export complete project JSON bundles, backup survey sessions, and import external SignalPlan plans.
13. **Settings:** Toggle between Metric (Meters) and Imperial (Feet), customize simulation grid steps, and adjust polling intervals.
14. **Hardware Status:** Complete hardware truth matrix verifying active Tier 1 physical adapters and documenting optional Tier 2/3 peripheral requirements.

---

## 6. Verification and Testing

Execute the comprehensive test suite covering the Wi-Fi scanner, SQLite persistence, RF propagation calculations, IDW interpolation, and FastAPI endpoints:

```powershell
.\venv\Scripts\python.exe nighthawk-backend\test_backend.py
```

Expected Result:
```
Ran 6 tests in 0.305s - OK
```

---

## 7. Security and Privacy Policy

- **No Remote Telemetry:** The application operates strictly offline.
- **Defensive Scanning:** Collects standard beacon frames exposed by Windows `WlanSvc`; does not perform packet injection, deauthentication attacks, or password cracking.
- **Local Persistence:** All surveys and floor plans are stored exclusively on your local disk at `nighthawk-backend/data/nighthawk.db`.
