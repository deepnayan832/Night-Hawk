# NightHawk — Upstream Research Audit

**Audit purpose:** Document open-source projects reviewed as research references for possible future development.  
**Important distinction:** The repositories listed below are not bundled or imported into the current Tier 1 application source. The current application implementation was authored for this repository. This audit is not a claim of code integration.

## Research references

| # | Repository | Research area | Potential relevance | Current NightHawk status |
|---|---|---|---|---|
| 1 | [hnykda/wifi-heatmapper](https://github.com/hnykda/wifi-heatmapper) | Windows Wi-Fi surveying and heatmaps | Survey workflow and WLAN discovery reference | Reviewed as reference; no source bundled |
| 2 | [dcchill/open-heat](https://github.com/dcchill/open-heat) | Windows netsh WLAN scanner | Windows command-output reference | Reviewed as reference; no source bundled |
| 3 | [J0nan/Wi-Fi_HeatMap](https://github.com/J0nan/Wi-Fi_HeatMap) | 2D signal interpolation | Spatial interpolation concepts | Reviewed as reference; no source bundled |
| 4 | [ribaldorafael/wifi-heatmap](https://github.com/ribaldorafael/wifi-heatmap) | Heatmap analytics | Coverage metrics and analytics concepts | Reviewed as reference; no source bundled |
| 5 | [NC4321/SignalPlan](https://github.com/NC4321/SignalPlan) | Floor-plan modelling and RF propagation | RF model and spatial editor research | Reviewed as reference; no source bundled |
| 6 | [Neumi/3D_wifi_scanner](https://github.com/Neumi/3D_wifi_scanner) | Volumetric Wi-Fi scanning | Physical scan data and 3D visualization research | Not bundled; verify permissions before use |
| 7 | [Neumi/ethersweep](https://github.com/Neumi/ethersweep) | Motorized scanner control | Optional rig-control research | Not bundled; GPL boundary review required before integration |
| 8 | [DwayneCon/wifi-3d-fusion](https://github.com/DwayneCon/wifi-3d-fusion) | CSI preprocessing/fusion | Optional CSI research | Reviewed as reference; no source bundled |
| 9 | [s-shrikanth/WiFi-CSI-Human-Detection](https://github.com/s-shrikanth/WiFi-CSI-Human-Detection) | CSI movement detection | Optional sensing research | Reviewed as reference; no source bundled |
| 10 | [csi-rs/csi-gui-rs](https://github.com/csi-rs/csi-gui-rs) | CSI stream display/protocol | Optional ESP32 serial research | Reviewed as reference; no source bundled |
| 11 | [csi-rs/esp-csi-cli-rs](https://github.com/csi-rs/esp-csi-cli-rs) | ESP32 firmware | Optional CSI firmware research | Reviewed as reference; no source bundled |
| 12 | [StevenMHernandez/ESP32-CSI-Tool](https://github.com/StevenMHernandez/ESP32-CSI-Tool) | ESP32 CSI capture | Optional CSI protocol research | Reviewed as reference; no source bundled |

## Current Tier 1 implementation in this repository

| Capability | Source |
|---|---|
| Windows WLAN scanning with netsh | `nighthawk-backend/wifi.py` |
| SQLite project/session/point storage | `nighthawk-backend/db.py` |
| FastAPI local service | `nighthawk-backend/main.py` |
| FSPL, wall loss, IDW and coverage grids | `nighthawk-backend/rf.py` |
| Browser UI and floor-plan editor | `nighthawk-backend/static/` |
| RF and database unit tests | `nighthawk-backend/tests/` |

## Integration policy

Future integration work must record the exact upstream commit, files imported, license requirements, modifications made, and tests performed. A research reference or an independently implemented equivalent is not evidence that upstream source code has been integrated.
