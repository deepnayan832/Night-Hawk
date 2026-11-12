# NightHawk — Hardware Requirements & Capability Matrix

**Release:** 1.0.0 Tier 1 baseline  
**Target:** Windows 10/11 x64

This document distinguishes current software support from future hardware ambitions. Hardware is not considered supported merely because it appears in a design document.

## 1. Current supported baseline

### Tier 1 — Windows PC + ordinary Wi-Fi adapter

Required:
- Windows 10/11 x64.
- Python 3.10+.
- A Wi-Fi adapter with a functioning Windows WLAN driver.
- A working Wi-Fi router or access point in range.

Current capabilities:
- Windows-visible WLAN/BSSID scan using `netsh wlan`.
- Signal-quality percentage and an approximate dBm display conversion.
- User-created floor plans and router placement.
- Manual survey positioning and local persistence.
- IDW interpolation of saved samples.
- Simplified wall-aware RF estimate and router-position ranking.

**Signal caveat:** On many Windows adapters, `netsh` reports signal quality as a percentage. The displayed dBm conversion is an approximation, not a calibrated RSSI reading. Use the raw signal percentage as the more direct OS-provided value.

## 2. Capability matrix

| Feature | Standard PC + router | Optional hardware | Release 1.0.0 status |
|---|---|---|---|
| Nearby network discovery | Yes, through Windows WLAN | Not required | Implemented; Windows testing still required |
| Connected adapter status | Yes, through Windows WLAN | Not required | Implemented |
| Calibrated RSSI dBm | Driver-dependent; not generally exposed through netsh | External calibrated equipment may help | Not guaranteed |
| Walk-and-click survey | User records the physical location | Not required | Implemented |
| Local survey persistence | Yes | Not required | Implemented |
| Floor-plan drawing | User draws room geometry | Not required | Implemented |
| 2D measured heatmap | Requires multiple saved samples | Not required | IDW implemented |
| Predicted RF coverage | Uses simplified model assumptions | Not required | Implemented; estimate only |
| Router position ranking | Uses the same RF model | Not required | Implemented; validate physically |
| Isometric room preview | Standard browser canvas | Not required | Implemented; not full WebGL |
| CSI amplitude/time series | No, not from ordinary netsh scans | Compatible ESP32/CSI hardware and firmware | Not implemented |
| Motion/presence experiments | No | Compatible CSI capture setup | Not implemented |
| Automated volumetric physical scan | No | Probe, motorized frame and controller | Not implemented |
| High-resolution through-wall imaging | Unsupported | No ordinary consumer Wi-Fi setup guarantees this | Unsupported |

## 3. Tier 2 — Optional CSI research hardware (future work)

Potential future hardware:
- A compatible ESP32-family board.
- USB data cable and Windows virtual COM-port driver.
- CSI-capable firmware supported by the selected chip and SDK.
- A second compatible wireless endpoint may be needed depending on the CSI capture method.

CSI can measure changes in the wireless channel over time under suitable hardware/firmware conditions. Such measurements may support controlled motion experiments, but they do not provide detailed room scans, anatomical images, or reliable wall-structure reconstruction.

**Release 1.0.0 does not implement serial CSI capture or presence detection.**

## 4. Tier 3 — Optional motorized spatial scanner (future work)

A future physical scan rig would require:
- A stable 2D/3D motion frame.
- Motor drivers and a documented controller protocol.
- A wireless probe with repeatable measurement output.
- Mechanical and electrical safety limits, homing and emergency-stop behavior.
- Calibration of the probe's position against the room coordinate system.

**Release 1.0.0 does not implement gantry control or automatic volumetric capture.**

## 5. Measurement and privacy notes

- Windows signal quality is retained as a percentage.
- The derived dBm value is explicitly labelled as an estimate.
- Manual dBm input is available for users who have a calibrated reading from another instrument or driver.
- Survey points may include SSID and BSSID identifiers; review CSV exports before sharing.
- Local data is stored in SQLite under `%USERPROFILE%\.nighthawk` unless `NIGHTHAWK_DATA_DIR` overrides the location.
