# NightHawk — Hardware Requirements & Capability Matrix

**Release:** 1.1.0  
**Target:** Windows 10/11 x64

This matrix distinguishes software support from physical-device testing. A feature marked implemented in source is not automatically certified against every hardware model.

## 1. Tier 1 — Standard Windows PC + Wi-Fi router

Required:
- Windows 10/11 x64.
- Python 3.10+.
- Node.js 20+ and npm for the local Three.js build.
- Wi-Fi adapter with a working Windows WLAN driver.
- An ordinary Wi-Fi router or access point.

Supported software workflows:
- Windows netsh WLAN interface and visible-BSSID scan.
- Signal percentage with explicitly estimated dBm conversion.
- Survey session and floor-specific measurement capture.
- User-drawn multi-floor floor plans.
- Measured IDW and simplified 3D floor-aware RF estimates.
- Three.js/WebGL room and coverage rendering.
- Per-floor router-position candidate ranking.
- Project JSON backup and survey CSV export.

**Important:** A router-only setup does not expose CSI on the Windows machine. Ordinary Wi-Fi scanning cannot produce architectural X-ray images or identify wall structure.

## 2. Current capability matrix

| Feature | Standard PC + router | Optional hardware | Current release status |
|---|---|---|---|
| Nearby WLAN discovery | Yes, via Windows WLAN | No | Implemented in code; live PC/adapter validation pending |
| Signal quality | Windows signal percentage | Calibrated measurement hardware for actual dBm | Percentage implemented; dBm is estimated |
| Walk-and-click survey | Yes | No | Implemented |
| Multi-floor project editing | Yes | No | Implemented |
| Measured per-floor heatmap | Requires saved samples | No | IDW implemented |
| Predicted per-floor RF map | Uses assumptions about geometry/materials | No | Simplified 3D-distance/slab model implemented |
| Three.js room renderer | Browser with WebGL | GPU/browser support | Implemented and bundled locally; target-GPU visual check pending |
| Router-position ranking | Uses simplified model | No | Implemented; real-world validation required |
| CSI serial capture | No | Compatible ESP32 + CSI firmware + USB serial | Collector and parser implemented; physical ESP32 test pending |
| CSI motion/presence classifier | No | Compatible CSI capture and validated model | Not implemented; UI only displays amplitude/variance |
| Volumetric CSV point cloud | Yes, from a measured CSV | Existing dataset | Implemented |
| Waypoint grid export | Yes | No | Implemented |
| Automatic motorized scan control | No | Exact motor/controller hardware and protocol | Not implemented |
| High-resolution through-wall structural imaging | Unsupported | Not available from ordinary Wi-Fi/CSI alone | Unsupported |

## 3. Tier 2 — Optional ESP32 CSI hardware

Potential setup:
- ESP32-family board supported by the selected firmware.
- USB data cable and Windows virtual COM-port driver.
- Compatible ESP32-CSI-Tool firmware build.
- Serial baud rate configured consistently with firmware (the UI defaults to 921600).
- Optional second wireless endpoint depending on active/passive CSI collection mode.

NightHawk can enumerate serial ports, connect to a selected port, parse a configurable CSV vector field and visualize CSI amplitudes/phases and rolling variance.

**Limitations:**
- Firmware forks can change CSV field layout; inspect actual serial output and set the field index accordingly.
- Physical board/firmware compatibility has not been validated in this session.
- CSI variance is not a trained or validated people detector.
- CSI does not produce detailed anatomical imagery or architectural X-ray scans.

## 4. Tier 3 — Optional motorized volumetric scanner

The current application provides:
- A CSV point-cloud importer.
- A Three.js volumetric RSSI viewer.
- A bounded serpentine x/y/z waypoint-plan CSV exporter.

It does **not** send motor commands, home axes, read limit switches or implement an emergency-stop circuit.

Before adding physical rig control, the exact controller model, protocol documentation, motion limits, end-stop configuration, homing behaviour, and emergency-stop wiring must be supplied and tested. A guessed UDP/serial movement command can damage hardware or injure someone; NightHawk deliberately does not invent one.

## 5. Measurement and privacy notes

- Windows signal quality is retained as a percentage.
- The derived dBm value is labelled as an estimate.
- Manual dBm entry is available for calibrated readings from another instrument or driver.
- Survey points may include SSID/BSSID identifiers; review CSV exports before sharing.
- Local data is stored under `%USERPROFILE%\.nighthawk` unless `NIGHTHAWK_DATA_DIR` is set.
