# NightHawk — License and Third-Party Notes

**Project license:** MIT  
**Copyright holder:** Nayan Deep  
**Current source status:** The Tier 1 application files in this repository are original NightHawk implementation code. The upstream projects below are research references and are not bundled as imported source dependencies in the current application.

## 1. NightHawk project license

The project-level license is in [LICENSE](LICENSE). It applies to original NightHawk code, subject to the exclusions and independent rights of third-party components, if any are added in future.

## 2. Upstream research references

The following repositories were reviewed as potential references for Wi-Fi surveying, RF modelling, CSI research, or volumetric scanning. Listing a repository here does not mean its source code is copied, linked, bundled, or integrated into NightHawk.

| Repository | Research area | License noted during prior review |
|---|---|---|
| [hnykda/wifi-heatmapper](https://github.com/hnykda/wifi-heatmapper) | Windows Wi-Fi scanning and survey workflow | MIT |
| [dcchill/open-heat](https://github.com/dcchill/open-heat) | netsh WLAN parsing and diagnostics | MIT |
| [J0nan/Wi-Fi_HeatMap](https://github.com/J0nan/Wi-Fi_HeatMap) | 2D interpolation and floor-plan calibration | MIT |
| [ribaldorafael/wifi-heatmap](https://github.com/ribaldorafael/wifi-heatmap) | Heatmap analysis and coverage metrics | MIT |
| [NC4321/SignalPlan](https://github.com/NC4321/SignalPlan) | Floor-plan and RF propagation concepts | MIT |
| [Neumi/3D_wifi_scanner](https://github.com/Neumi/3D_wifi_scanner) | Volumetric RSSI research and datasets | No license was identified in prior review; do not copy or redistribute without permission |
| [Neumi/ethersweep](https://github.com/Neumi/ethersweep) | Motorized scanner controller research | GPL-3.0 |
| [DwayneCon/wifi-3d-fusion](https://github.com/DwayneCon/wifi-3d-fusion) | CSI preprocessing and fusion research | Apache-2.0 |
| [s-shrikanth/WiFi-CSI-Human-Detection](https://github.com/s-shrikanth/WiFi-CSI-Human-Detection) | CSI-based movement research | MIT |
| [csi-rs/csi-gui-rs](https://github.com/csi-rs/csi-gui-rs) | CSI serial protocol and GUI research | MIT / Apache-2.0 |
| [csi-rs/esp-csi-cli-rs](https://github.com/csi-rs/esp-csi-cli-rs) | ESP32 CSI firmware research | MIT / Apache-2.0 |
| [StevenMHernandez/ESP32-CSI-Tool](https://github.com/StevenMHernandez/ESP32-CSI-Tool) | ESP32 CSI capture tooling | MIT |

The license column records the findings from the earlier repository review; upstream licenses can change and should be checked at the original source before any future code import.

## 3. Rules for future integration

Before integrating third-party code or datasets:

1. Inspect the upstream repository's current license file and notices.
2. Preserve required copyright and license texts.
3. Track the exact files or modules imported and the source commit.
4. Review copyleft obligations before combining code with the MIT-licensed core.
5. Do not redistribute unlicensed code or datasets without permission.
6. Add the required notices to a dedicated third-party notices file.

No third-party source should be described as integrated until that source and its required notices are actually included in this repository.
