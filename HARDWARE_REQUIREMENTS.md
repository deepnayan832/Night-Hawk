# Project Nighthawk — Hardware Requirements & Truth Matrix

Date: November 2026  
Purpose: Explicitly delineate genuine capabilities supported by standard PC/router hardware vs. optional external hardware modules.

---

## 1. Hardware Tiers Overview

Project Nighthawk is architected with a strict **Hardware-Truth Guarantee**: The application never fabricates measurements, simulates fake through-wall vision on consumer routers, or pretends that missing physical peripherals exist.

```
+-------------------------------------------------------------------------------+
| TIER 1: Standard Hardware (100% Fully Functional Out-of-the-Box)              |
| - Standard Windows 10/11 x64 PC / Laptop                                      |
| - Integrated or USB Wi-Fi Adapter (802.11a/b/g/n/ac/ax/be)                    |
| - Any Existing Commercial Wi-Fi Router or Access Point                        |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
| TIER 2: Optional Wi-Fi CSI Hardware Module                                    |
| - 1 or more Espressif ESP32 / ESP32-S3 / ESP32-C3 Microcontrollers            |
| - USB-to-UART Cable (CP2102 / CH340 / FTDI)                                   |
| - Flashed with ESP32-CSI-Tool or esp-csi-cli-rs firmware                      |
+-------------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------------+
| TIER 3: Optional Motorized 3D Volumetric Scanning Rig                         |
| - ESP32 NodeMCU Wi-Fi Probe                                                   |
| - Motorized 2-Axis / 3-Axis Frame (e.g. 3D printer gantry or CNC rig)         |
| - Ethersweep Stepper Controllers (UDP over Ethernet / Wi-Fi)                  |
+-------------------------------------------------------------------------------+
```

---

## 2. Capability Matrix by Hardware Tier

| Feature / Module | Tier 1 (PC + Router Only) | Tier 2 (With ESP32 CSI) | Tier 3 (With Motorized Rig) | Status & Fallback Behavior |
|---|---|---|---|---|
| **Live Wi-Fi Scanner** | **Full** (Real netsh/WlanAPI) | Full | Full | Direct hardware readings on Windows |
| **Walk-and-Click Home Survey** | **Full** (Real RSSI in dBm) | Full | Full | User walks and clicks positions |
| **2D Floor Plan Editor** | **Full** | Full | Full | Multi-room, walls, doors, windows |
| **3D Interactive Home View** | **Full** (Three.js WebGL) | Full | Full | Multi-floor 3D extrusion, camera orbit |
| **2D Measured Heatmap** | **Full** (Real IDW / RBF) | Full | Full | Interpolated from actual survey points |
| **3D RF Coverage Simulation** | **Full** (ITU-R MWM Model) | Full | Full | Physics-based ray attenuation |
| **Router Placement Optimizer** | **Full** | Full | Full | Coverage score & channel analysis |
| **Historical Survey Comparison**| **Full** (Local SQLite/JSON) | Full | Full | Compare before/after router moves |
| **CSI Subcarrier Amplitude Matrix** | Simulated / Fallback | **Full** (Real 64/128 subcarriers) | Full | Shows "Hardware Disconnected" banner |
| **CSI Fresnel Motion Sensing** | Simulated / Fallback | **Full** (Real variance detection) | Full | Requires ESP32 in LOS/NLOS link |
| **3D Volumetric RSSI Voxel Cloud** | Sample Stack Datasets | Sample Stack Datasets | **Full** (Automated Motorized) | Pre-loaded Neumi dataset + import |
| **Through-Wall Structural Imaging** | **Unsupported** | **Unsupported** | **Unsupported** | **Truth Notice:** Neither commercial Wi-Fi nor ESP32 CSI can produce high-resolution architectural X-ray scans. Floor plans must be drawn or imported. |

---

## 3. Detailed Hardware Specifications

### Tier 1: Standard Hardware (Zero Additional Cost)
- **Computer:** Any x64 PC running Windows 10 (version 1903+) or Windows 11 (including 24H2).
- **Wi-Fi Adapter:** Any internal or external Wi-Fi card reporting to Windows WLAN AutoConfig (`WlanSvc`). Supported drivers include Realtek, Intel, Broadcom, MediaTek, Qualcomm.
- **Router:** Any standard IEEE 802.11 access point (2.4 GHz, 5 GHz, or 6 GHz). No router firmware modifications or SSH access required.
- **Location Permission Notice (Windows 11 24H2+):** Windows requires "Let desktop apps access your location" to be enabled in `Settings > Privacy & security > Location` for applications to query Wi-Fi BSSID and nearby SSID lists via `netsh` or `wlanapi.dll`.

### Tier 2: Optional CSI Sensing Hardware
- **Supported Microcontrollers:**
  - ESP32-WROOM-32 / ESP32-DevKitC (tensilica Xtensa dual-core)
  - ESP32-S3 (Xtensa LX7 dual-core)
  - ESP32-C3 / ESP32-C5 (RISC-V)
- **Firmware:**
  - `ESP32-CSI-Tool` (active station or passive monitor mode emitting serial `CSI_DATA` CSV packets)
  - `esp-csi-cli-rs` (binary wire-v1 framing over 115200 or 921600 baud)
- **Connection:** Standard USB-to-MicroUSB or USB-C cable recognized as a Virtual COM Port (`COM1` - `COM99`).
- **Physical Sensing Principle:**
  - CSI measures the channel matrix $H(f, t)$ capturing phase and amplitude across 64 OFDM subcarriers (in 20MHz bandwidth) or 128 subcarriers (in 40MHz bandwidth).
  - Human movement through the multipath Fresnel zones alters the subcarrier amplitude variance $\sigma^2_{amp}$.
  - **Limitations:** Only detects movement/presence along the RF propagation path; cannot image anatomical details or penetrate multiple dense concrete walls reliably.

### Tier 3: Optional Motorized Volumetric Rig
- **Scanner Carriage:** 3D printer frame (e.g. Ender-3 or custom 2-axis carriage).
- **Controllers:** Ethersweep networked stepper motor boards responding to UDP commands on port 8888.
- **Probe:** ESP32 NodeMCU running a lightweight HTTP server returning JSON `{"rssi": -XX}`.
- **Resolution:** Typically 10mm spatial grid increments.

---

## 4. Software Graceful Degradation Protocol

When optional hardware is absent:
1. The UI displays an amber status badge: `Hardware Module Inactive (Simulation / Archive Mode)`.
2. A direct "Connect Hardware" drawer guides the user through serial COM port selection or UDP configuration.
3. Users can explore the features using verified pre-recorded datasets from the upstream repositories (e.g., Neumi's `stack_data/*.csv` for volumetric scanning, Hernandez's CSI traces for CSI sensing).
4. No synthetic data is ever masked as live data; clear labels (`[ARCHIVED SAMPLE]`, `[SIMULATED]`, `[LIVE HARDWARE]`) are rendered on every plot.
