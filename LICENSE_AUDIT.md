# Project Nighthawk — License Audit

Date: November 2026  
Status: Compliant  

This document reviews the open-source licenses of all 12 repositories integrated or referenced in Project Nighthawk, establishes attribution requirements, and details boundary isolation strategies to ensure strict legal and licensing compliance.

---

## 1. Upstream License Inventory

| Repository | Declared License | Copyright / Originator | Compatibility with Nighthawk Core | Action Taken |
|---|---|---|---|---|
| `wifi-heatmapper` | MIT | Daniel Alder | Permissive (Direct reuse permitted) | Retained copyright notices; adapted scanning and WebGL heatmap routines. |
| `open-heat` | MIT | dcchill | Permissive (Direct reuse permitted) | Retained copyright notices; adapted netsh parsing logic. |
| `Wi-Fi_HeatMap` | MIT | J0nan | Permissive (Direct reuse permitted) | Retained copyright notices; adapted spatial interpolation logic. |
| `wifi-heatmap` | MIT | Rafael Ribaldo | Permissive (Direct reuse permitted) | Retained copyright notices; adapted channel conflict & dead-zone analytics. |
| `SignalPlan` | MIT | NC4321 | Permissive (Direct reuse permitted) | Retained copyright notices; adopted floor plan schema and RF propagation equations. |
| `3D_wifi_scanner` | None (All Rights Reserved) | Neumi | Proprietary/Unlicensed upstream | Clean-room implementation of volumetric data structure and CSV parser; no direct source code copy. |
| `ethersweep` | GNU GPL v3.0 | Neumi | Reciprocal (Copyleft) | Architectural boundary isolation: Driver treated as external microservice / optional standalone utility over UDP/Serial. No GPL code linked into Nighthawk core. |
| `wifi-3d-fusion` | Apache License 2.0 | DwayneCon | Permissive with patent clause | Compliant; retained Apache-2.0 notice; extracted mathematical formulas. |
| `WiFi-CSI-Human-Detection` | MIT | S. Shrikanth | Permissive | Retained copyright notices; ported variance formulas. |
| `csi-gui-rs` | MIT / Apache-2.0 Dual | csi-rs contributors | Permissive | Retained attribution; adapted wire-v1 framing specification. |
| `esp-csi-cli-rs` | MIT / Apache-2.0 Dual | csi-rs contributors | Permissive | Referenced as external firmware target. |
| `ESP32-CSI-Tool` | MIT | Steven M. Hernandez | Permissive | Retained copyright notices; adapted serial CSV parser. |

---

## 2. License Compatibility & Isolation Strategy

### A. Permissive Code (MIT & Apache 2.0)
The majority of core repositories (`SignalPlan`, `wifi-heatmapper`, `open-heat`, `Wi-Fi_HeatMap`, `wifi-heatmap`, `WiFi-CSI-Human-Detection`, `ESP32-CSI-Tool`, `csi-gui-rs`) use the standard permissive MIT or Apache 2.0 licenses.
- **Requirement:** Maintain copyright notices and permission disclaimers in modified or reused modules.
- **Implementation:** Full attribution is placed in `THIRD_PARTY_LICENSES.md` and inline in the respective adapter files.

### B. Reciprocal / Copyleft Code (`ethersweep` — GPL v3.0)
`ethersweep` is licensed under GNU GPL v3.0.
- **Risk:** Directly linking GPL v3.0 code into an MIT or Apache-based project would subject the combined work to GPL-3.0 requirements.
- **Solution:** Project Nighthawk communicates with motor controllers purely across a standard UDP network socket (`UDP_SEND_PORT = 8888`) or serial protocol with a generic JSON wire contract (`{"steps": N, "speed": V, "direction": D}`). No GPL code is compiled or imported into the main application. This adheres to FSF guidelines regarding network communication boundaries.

### C. Unlicensed Repository (`3D_wifi_scanner`)
`3D_wifi_scanner` does not provide an explicit open-source license file in its GitHub repository.
- **Risk:** Reusing source code without an explicit license carries copyright infringement risk under default copyright law.
- **Solution:** Clean-room implementation. Project Nighthawk reads standard mathematical volumetric coordinates `(x, y, z, RSSI)` through an independently authored CSV parser. The Three.js 3D volumetric scatter and voxel viewer is authored from scratch within Project Nighthawk.

---

## 3. Third-Party Attributions

Project Nighthawk gratefully acknowledges the pioneering contributions of the following authors:

- **Daniel Alder** (`wifi-heatmapper`) — MIT License
- **dcchill** (`open-heat`) — MIT License
- **J0nan** (`Wi-Fi_HeatMap`) — MIT License
- **Rafael Ribaldo** (`wifi-heatmap`) — MIT License
- **NC4321** (`SignalPlan`) — MIT License
- **Neumi** (`3D_wifi_scanner`, `ethersweep`) — Creator of volumetric Wi-Fi scanning concepts
- **DwayneCon** (`wifi-3d-fusion`) — Apache-2.0 License
- **S. Shrikanth** (`WiFi-CSI-Human-Detection`) — MIT License
- **csi-rs team** (`csi-gui-rs`, `esp-csi-cli-rs`) — MIT / Apache-2.0 License
- **Steven M. Hernandez** (`ESP32-CSI-Tool`) — MIT License
