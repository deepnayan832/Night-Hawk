# Project Nighthawk — Repository Audit

Date of Audit: November 2026  
Target Environment: Windows 10/11 x64, Node.js, Python, Three.js, Local-First

This audit covers all 12 mandatory upstream repositories cloned into `C:\Users\nayan\project-nighthawk\repos`. Each repository is analyzed for its primary purpose, technologies, Windows compatibility, license, strengths, limitations, and its specific integration outcome into **Project Nighthawk**.

---

## 1. wifi-heatmapper (`hnykda/wifi-heatmapper`)
- **Repository URL:** https://github.com/hnykda/wifi-heatmapper
- **Primary Technologies:** TypeScript, Next.js, React, Tailwind CSS, WebGL, Tauri/Rust, native Windows `wlanapi.dll` (via Koffi) & `netsh` fallback.
- **License:** MIT License (Daniel Alder).
- **Windows Compatibility:** **High (Production Ready)**. Contains dedicated `wifiScanner-windows.ts` supporting both direct Win32 `wlanapi.dll` scanning and localized `netsh wlan show interfaces` and `netsh wlan show networks mode=bssid` parsing. Accurately handles Windows 11 24H2 location permissions.
- **Strengths:** Robust walk-and-click surveying workflow, WebGL heatmap rendering pipeline, active signal & speed-test metrics, well-designed persistence of survey points.
- **Limitations:** Monolithic Next.js + Tauri desktop architecture can be heavy; requires location permissions on Win11 24H2+.
- **Integration Outcome:** **Reused & Adapted Core Engine**.
  - Reused Windows Wi-Fi scanning routines (`netsh` + Win32 heuristics) and signal-to-dBm normalization.
  - Adapted survey point recording workflow and WebGL/Canvas heatmap visualization.

---

## 2. open-heat (`dcchill/open-heat`)
- **Repository URL:** https://github.com/dcchill/open-heat
- **Primary Technologies:** Python 3, Tkinter, native `http.server`, `netsh wlan` CLI parser.
- **License:** MIT License (dcchill).
- **Windows Compatibility:** **Native Windows**. Specifically built around Windows `netsh wlan show interfaces`.
- **Strengths:** Extremely lightweight, clean regex parsing of `netsh` fields (SSID, BSSID, RSSI dBm, State, Radio type, Channel, Band, Receive/Transmit rates). Diagnostic ping/latency collection.
- **Limitations:** Basic Tkinter UI, simple 2D drawing without multi-floor or 3D capability.
- **Integration Outcome:** **Direct Backend Adapter**.
  - Reused `WifiReading` data structure and `netsh` interface regex extraction in our Python FastAPI backend.
  - Fallback network diagnostics and ping/jitter measurements.

---

## 3. Wi-Fi_HeatMap (`J0nan/Wi-Fi_HeatMap`)
- **Repository URL:** https://github.com/J0nan/Wi-Fi_HeatMap
- **Primary Technologies:** Python, Tkinter, PIL, SciPy (`scipy.interpolate.griddata`), NumPy, Matplotlib, PyWiFi.
- **License:** MIT License (J0nan).
- **Windows Compatibility:** **Good**. Supports Windows `netsh` and optional `pywifi`.
- **Strengths:** 2D spatial interpolation using Scipy griddata (`cubic`, `linear`, `nearest`), multi-AP identification, floor plan image calibration using known distances.
- **Limitations:** Tkinter desktop UI, single-floor only, high PyWiFi dependency sensitivity on newer Windows builds.
- **Integration Outcome:** **Algorithmic Adapter**.
  - Integrated spatial interpolation algorithms (Inverse Distance Weighting and Scipy RBF/Griddata interpolation).
  - Adopted pixel-to-meter physical distance calibration math.

---

## 4. wifi-heatmap (`ribaldorafael/wifi-heatmap`)
- **Repository URL:** https://github.com/ribaldorafael/wifi-heatmap
- **Primary Technologies:** Python 3, Flask, Matplotlib, NumPy, SciPy (RBF / Kriging heuristics).
- **License:** MIT License (Rafael Ribaldo).
- **Windows Compatibility:** **Good (Cross-platform)**. Includes multi-OS scanner abstraction (`macOS`, `Linux`, `Windows` via netsh).
- **Strengths:** High test coverage (110+ tests), clean modular separation (`scanner.py`, `heatmap.py`, `insights.py`, `export.py`), AP dead-zone calculation, channel conflict analytics.
- **Limitations:** Web UI is minimalist server-side Flask templates; lacks 3D representation.
- **Integration Outcome:** **Analytics Engine & REST API Inspiration**.
  - Reused channel conflict metrics and dead-zone coverage percentage insights (`insights.py`).
  - Adapted survey import/export JSON/CSV structures.

---

## 5. SignalPlan (`NC4321/SignalPlan`)
- **Repository URL:** https://github.com/NC4321/SignalPlan
- **Primary Technologies:** TypeScript, React, Vite, Three.js (`OrbitControls`), Zod schemas, Vitest.
- **License:** MIT License (NC4321).
- **Windows Compatibility:** **Complete (Web/Localhost)**. Runs in browser or node environments seamlessly on Windows.
- **Strengths:**
  - **Industry-grade RF Propagation Engine:** Multi-Wall Model (MWM) per ITU-R P.2040-4 and ITU-R P.1238, free-space path loss (FSPL), multi-frequency attenuation (2.4 GHz, 5 GHz, 6 GHz), floor slabs, stair openings, and ray-wall intersection (`crossings.ts`).
  - **Interactive 2D & 3D Home Builder:** Wall drawing, node editing, multi-floor stacking, ceiling heights, door/window openings, material assignments (drywall, brick, concrete, glass, metal, wood).
  - **AP Placement Optimizer:** Channel planning and auto-router placement optimization.
  - **Survey Calibration & Import:** Pre-built support for survey spots and CSV/JSON survey import.
- **Limitations:** Standalone client-side application without live Windows adapter background daemon.
- **Integration Outcome:** **Core 3D & RF Engine Integration Target**.
  - SignalPlan's floor plan schema, RF attenuation calculations, Three.js 3D multi-floor viewer (`View3D.tsx`), and material physics are integrated as the visual and simulation backbone of Project Nighthawk.

---

## 6. 3D_wifi_scanner (`Neumi/3D_wifi_scanner`)
- **Repository URL:** https://github.com/Neumi/3D_wifi_scanner
- **Primary Technologies:** Python, Plotly, Matplotlib, ESP32 NodeMCU C++ (`node_mcu_code.ino`), CSV data stack.
- **License:** No explicit license file (All rights reserved / Author copyright Neumi). Clean-room data specification and adapter pattern applied.
- **Windows Compatibility:** **Good for Analysis; Hardware-dependent for Live Capture**. Python visualization runs on Windows; live capture requires physical CNC/3D printer rig.
- **Strengths:** Novel 3D volumetric RSSI visualization (`(x, y, z) -> RSSI`), real physical datasets included (`stack_data/*.csv`), proving wave diffraction and multi-path nodes in space.
- **Limitations:** Live scanning requires an ESP32 mounted to a motorized 3D printer carriage.
- **Integration Outcome:** **Optional Hardware Module & 3D Volumetric Viewer**.
  - Implemented 3D volumetric voxel and point cloud viewer in Three.js.
  - Built CSV parser for Neumi's `(x, y, rssi)` slice stack datasets.
  - Added simulated volumetric mode and clearly marked physical CNC scanning as optional.

---

## 7. ethersweep (`Neumi/ethersweep`)
- **Repository URL:** https://github.com/Neumi/ethersweep
- **Primary Technologies:** C++ (STM32 firmware), Python (UDP motor drive controllers).
- **License:** GNU General Public License v3.0 (GPL-3.0).
- **Windows Compatibility:** **Hardware/Controller Interface**. Python scripts send UDP packets to drive stepper motors.
- **Strengths:** Networked stepper motor controller for automated XY scanning rigs.
- **Limitations:** Only relevant when motorized scanning hardware is physically present.
- **Integration Outcome:** **Optional Hardware Rig Driver Adapter**.
  - Documented as an optional hardware integration for physical automated scanning rigs.
  - Built a mockable controller interface with clean separation to preserve GPL licensing boundaries.

---

## 8. wifi-3d-fusion (`DwayneCon/wifi-3d-fusion`)
- **Repository URL:** https://github.com/DwayneCon/wifi-3d-fusion
- **Primary Technologies:** Python, PyTorch, NumPy, Nexmon PCAP parser, ESP32 UDP receiver.
- **License:** Apache License 2.0.
- **Windows Compatibility:** **Partial (Experimental Research Code)**. Heavy Linux-centric scripts (`run_wifi3d.sh`, monitor mode scripts), but Python core runs on Windows.
- **Strengths:** Advanced vision of multi-AP CSI fusion, spatial occupancy grid mapping, subcarrier preprocessing.
- **Limitations:** High compute demands, experimental research code, requires Nexmon-patched Wi-Fi cards or dedicated ESP32 UDP streams. Cannot be run blindly on standard commercial Wi-Fi cards without CSI firmware.
- **Integration Outcome:** **Research Module & CSI Preprocessing Pipeline**.
  - Extracted CSI subcarrier normalization, phase unwrapping, and variance algorithms.
  - Provided graceful fallback indicating hardware requirements for multi-node CSI fusion.

---

## 9. WiFi-CSI-Human-Detection (`s-shrikanth/WiFi-CSI-Human-Detection`)
- **Repository URL:** https://github.com/s-shrikanth/WiFi-CSI-Human-Detection
- **Primary Technologies:** Python, ESP32 CSI serial receiver, Matplotlib, SciPy.
- **License:** MIT License (s-shrikanth).
- **Windows Compatibility:** **High**. Python serial scripts connect to ESP32 via Windows COM ports (e.g., `COM3`).
- **Strengths:** Clean implementation of CSI amplitude variance filtering over sliding windows for human movement/motion detection across Fresnel zones.
- **Limitations:** Requires an ESP32 flashed with CSI-compatible firmware.
- **Integration Outcome:** **CSI Motion & Presence Engine**.
  - Ported subcarrier amplitude variance and threshold-based presence detection to the Nighthawk backend.
  - Added live serial port auto-detection for Windows COM ports.

---

## 10. csi-gui-rs (`csi-rs/csi-gui-rs`)
- **Repository URL:** https://github.com/csi-rs/csi-gui-rs
- **Primary Technologies:** Rust, eframe/egui, cross-platform serial communication, Rerun SDK.
- **License:** MIT / Apache-2.0 Dual License.
- **Windows Compatibility:** **Native Windows**. Compiles to native Windows `.exe`.
- **Strengths:** Excellent multi-board ESP32 device manager, subcarrier waterfall spectrograms, simulated board backend (`sim.rs`) for testing without physical hardware.
- **Limitations:** Requires Rust toolchain to build natively; UI is egui (immediate mode), distinct from web stack.
- **Integration Outcome:** **Protocol Specification & Simulation Adapter**.
  - Reused packet protocol definitions for ESP32 subcarrier matrices.
  - Integrated simulation concepts into Nighthawk to allow realistic CSI demonstration and testing even when no ESP32 is plugged in.

---

## 11. esp-csi-cli-rs (`csi-rs/esp-csi-cli-rs`)
- **Repository URL:** https://github.com/csi-rs/esp-csi-cli-rs
- **Primary Technologies:** Rust (`no_std`), ESP32 bare-metal firmware (`esp-hal`).
- **License:** MIT / Apache-2.0 Dual License.
- **Windows Compatibility:** **Firmware / Flashing Target**. Flashes to ESP32 from Windows using `espflash`.
- **Strengths:** High-rate (115200 to 921600 baud) binary CSI serialization over UART for ESP32, ESP32-S3, and ESP32-C3.
- **Limitations:** Firmware only; must be flashed to physical microcontrollers.
- **Integration Outcome:** **Hardware Firmware Compatibility Target**.
  - Documented as the recommended firmware for Project Nighthawk's optional ESP32 CSI module.

---

## 12. ESP32-CSI-Tool (`StevenMHernandez/ESP32-CSI-Tool`)
- **Repository URL:** https://github.com/StevenMHernandez/ESP32-CSI-Tool
- **Primary Technologies:** C (ESP-IDF), Python utilities (`python_utils/*.py`).
- **License:** MIT License (Steven M. Hernandez).
- **Windows Compatibility:** **High**. Standard serial monitor and Python parser work across all Windows COM ports.
- **Strengths:** Most widely cited and battle-tested ESP32 CSI firmware format. Emits readable CSV formatted frames:
  `CSI_DATA,node_id,mac,rssi,rate,sig_mode,mcs,bandwidth,...[subcarrier values]`.
- **Limitations:** Limited to 802.11n/g subcarriers (64 subcarriers for 20MHz, 128 for 40MHz).
- **Integration Outcome:** **Primary CSI Serial Protocol Parser**.
  - Implemented parser in Python backend supporting the standard `CSI_DATA` CSV serial stream.
  - Provides instant compatibility with any off-the-shelf ESP32 running Hernandez's firmware.

---

## Summary Integration Matrix

| # | Repository | Category | License | Integration Method | Hardware Required? |
|---|------------|----------|---------|---------------------|--------------------|
| 1 | `wifi-heatmapper` | Survey & Scanning | MIT | Direct Code Reuse / Adapted WebGL | No (Windows PC only) |
| 2 | `open-heat` | Diagnostics & Netsh | MIT | Backend Netsh Module | No (Windows PC only) |
| 3 | `Wi-Fi_HeatMap` | Interpolation | MIT | Spatial Math & Calibration | No (Windows PC only) |
| 4 | `wifi-heatmap` | Analytics | MIT | Heatmap & Insight Algorithms | No (Windows PC only) |
| 5 | `SignalPlan` | 3D Floor Plan & RF | MIT | Core UI, 3D Engine, MWM Propagation | No (Windows PC only) |
| 6 | `3D_wifi_scanner` | Volumetric | Custom/None | Adapter & 3D Voxel Viewer | Optional (CNC Rig) |
| 7 | `ethersweep` | Motor Control | GPL-3.0 | Isolated Hardware Driver Pattern | Optional (Motor Rig) |
| 8 | `wifi-3d-fusion` | CSI Sensing | Apache-2.0 | Signal Processing Algorithms | Optional (Multi-ESP32) |
| 9 | `WiFi-CSI-Human-Detection` | CSI Presence | MIT | Fresnel Variance Algorithm | Optional (ESP32) |
| 10 | `csi-gui-rs` | CSI Protocol | MIT/Apache | Protocol Spec & Simulator | Optional (ESP32) |
| 11 | `esp-csi-cli-rs` | CSI Firmware | MIT/Apache | Recommended Firmware Reference | Optional (ESP32) |
| 12 | `ESP32-CSI-Tool` | CSI Serial Stream | MIT | Serial Parser & Stream Handler | Optional (ESP32) |

