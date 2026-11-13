# NightHawk — Implementation Status

**Release target:** 1.1.0  
**Last updated:** November 13, 2026  
**Code state:** Tier 1 Windows application plus optional Tier 2 CSI serial and volumetric dataset workflows are present in `main`.  
**Hardware verification:** A real Windows Wi-Fi adapter and physical ESP32/controller have not been tested from this repository session.

This document separates code that exists, code covered by automated tests, and hardware validation that still requires physical devices.

## Implemented in the repository

| Component | Implementation | Verification boundary |
|---|---|---|
| Local FastAPI service | `nighthawk-backend/main.py`, localhost-only on port 8765 | FastAPI integration tests |
| SQLite persistence | Project, surveys, points and volumetric point cloud | Database unit tests |
| Windows WLAN scanner | `netsh wlan` interface and BSSID scan parser | Fixture-based parser tests; real adapter test still required |
| Signal display | Windows signal percentage with explicitly estimated dBm conversion | Conversion is not calibrated RSSI |
| Survey sessions | Create sessions, save points, list and CSV export | API integration and DB tests |
| Multi-floor project model | Per-floor ID, name, elevation, dimensions, walls and slab-loss assumptions | API tests cover 2-floor estimates |
| Floor-plan editor | Per-floor dimensions, material-labelled walls, router floor placement | Browser workflow implemented; Windows browser testing pending |
| 3D room view | Bundled Three.js/WebGL geometry with OrbitControls | Bundle build covered by CI; GPU/browser visual check still required |
| Measured coverage | Per-floor IDW from saved physical survey points | RF and API tests |
| Predicted coverage | 3D-distance FSPL, target-floor wall crossings and simplified floor-slab loss | Formula/API tests; building calibration not performed |
| 3D RF surface | Three.js mesh with colour and elevation derived from RF grid | Bundle build covered by CI; visual/GPU check pending |
| Router placement ranking | Per-floor candidate grid search using the same model | API code present; real placement validation pending |
| ESP32 CSI serial reader | COM-port discovery, configurable baud and CSI field column, I/Q amplitude/phase parsing | Parser tests; physical ESP32 streaming test pending |
| CSI signal view | Live subcarrier amplitude plot and rolling variance | Browser/hardware validation pending; no people classification |
| Volumetric dataset import | CSV validation, SQLite persistence and Three.js point cloud | Parser tests; browser/GPU validation pending |
| Scan waypoint planner | Bounded serpentine x/y/z waypoint CSV for an external/manual scanner | Scan-plan unit tests |
| Project backup | JSON export/import | API endpoint present |
| Local privacy boundary | FastAPI bound to loopback; no packet injection/deauthentication/password cracking | Code/config review |

## Not implemented or not hardware-verified

1. **Physical motorized rig control:** The release exports waypoint plans but does not send commands to stepper motors. Controller protocol, homing, travel limits, end-stops and emergency-stop integration are rig-specific and are not guessed.
2. **Physical Windows adapter validation:** No access to the user's actual Windows machine or WLAN adapter was available. The scanner parser has fixture tests, but it still needs live testing on the target PC/driver.
3. **Physical ESP32 validation:** The serial reader and documented ESP32-CSI-Tool CSV parser exist. A compatible board and firmware are required to verify real stream timing and firmware-specific CSV layout.
4. **High-resolution through-wall imaging:** Not provided. Ordinary Wi-Fi/CSI data cannot be represented as architectural X-ray imaging.
5. **Full RF ray tracing:** The current propagation model is a simplified estimate, not a full 3D ray tracer. It omits detailed antenna patterns, multipath, furniture, doors/windows as openings, dynamic interference and calibrated material data.
6. **CAD/image floor-plan import:** Not implemented; floors are drawn in the editor.

## Automated verification

GitHub Actions workflow: `.github/workflows/ci.yml`

The workflow is configured to:
- Install Python dependencies and compile the backend.
- Run RF, SQLite, WLAN parser, CSI parser and volumetric/scan-plan unit tests.
- Run FastAPI integration tests for multi-floor coverage, survey persistence and volumetric import.
- Install Node.js, build the locally bundled Three.js renderer, and syntax-check JavaScript.

A successful CI run verifies the tested code paths in the runner environment. It does not prove compatibility with every Windows WLAN driver or physical hardware.

## Windows validation checklist

These items must be checked on the actual target PC:

- [ ] Run `.`\setup.ps1 from a fresh clone with Python 3.10+, Node.js 20+ and npm.
- [ ] Confirm `.`\start.ps1 opens `http://127.0.0.1:8765`.
- [ ] Scan nearby networks on the actual Windows Wi-Fi adapter.
- [ ] Check behavior with Windows Location privacy disabled/enabled.
- [ ] Create a two-floor project and save/reload it.
- [ ] Record multiple points on each floor and compare measured coverage by floor.
- [ ] Check Three.js room and RF surfaces on the actual GPU/browser.
- [ ] Connect a compatible ESP32, confirm serial parsing, and compare CSI columns with firmware output.
- [ ] Import a volumetric CSV, restart the app, and confirm point-cloud persistence.
- [ ] Validate router placement suggestions with a physical survey.
- [ ] Confirm `.`\stop.ps1 stops only the NightHawk server process.

## Next work

- Live Windows adapter validation and localized netsh field handling.
- CSI stream validation on selected ESP32 board/firmware combinations.
- Add measured-model calibration and residual/RMSE reporting.
- Add CAD/image plan import and opening-aware wall geometry.
- Implement a physical scanner adapter only after the exact controller protocol and safety interlocks are supplied.
