# NightHawk — Implementation Status

**Release target:** 1.2.0  
**Last updated:** November 13, 2026  
**Code state:** Tier 1 Windows application (WLAN scanner, adapter hardware introspection, network health, ARP device discovery, spectrum overlap analyzer, scan history diffing, multi-floor RF simulation, 3D room/camera views) plus optional Tier 2 CSI serial and volumetric dataset workflows are complete and verified.  
**Hardware verification:** Real Windows Wi-Fi adapter verified live (`Realtek 8821CE 802.11ac PCI-E NIC`, SSID `Excitel_Nayan`, true hardware RSSI `-37 dBm`). Physical external ESP32 and motorized CNC controllers remain documented as external hardware options.

This document separates code that exists, code covered by automated tests, and hardware validation that still requires physical devices.

## Implemented in the repository

| Component | Implementation | Verification boundary |
|---|---|---|
| Local FastAPI service | `nighthawk-backend/main.py`, localhost-only on port 8765 | 35 automated tests passing; live smoke test verified |
| SQLite persistence | Project, floors, surveys, volumetric clouds, scan history, and scan diffs | Database & history unit tests; WAL mode |
| Windows WLAN scanner & introspection | `netsh wlan` interface and BSSID scan parser (`wifi.py`) | Tested on real Windows WLAN adapter; reports true dBm & % |
| Network health & gateway latency | `network_intel.py`, gateway ping, IPv4/IPv6, DNS check | Network unit tests and live execution |
| Local device discovery | Non-intrusive ARP cache reading (`arp -a`) with vendor OUI lookup | Tested with local devices & OUI unit tests |
| Spectrum congestion analyzer | 2.4 GHz (channels 1-14 with overlap matrix) & 5 GHz cleaner-channel scoring | Spectrum math unit tests; UI spectrum charts |
| Scan history & differencing | Scan recording, scan-diffing (new/dropped APs, signal $\Delta$ dBm), CSV/JSON export | History unit tests and API integration tests |
| Multi-floor project model | Per-floor ID, name, elevation, dimensions, walls and slab-loss assumptions | API tests cover 2-floor estimates |
| Floor-plan editor | Per-floor dimensions, material-labelled walls, router floor placement | Interactive browser UI tested |
| 3D room & camera views | Bundled Three.js/WebGL geometry with Orbit, Top-Down, and Room-Walk modes | Bundled locally; JS syntax validated; camera switcher tested |
| Measured coverage | Per-floor IDW from saved physical survey points | RF and API tests |
| Predicted coverage | 3D-distance FSPL, target-floor wall crossings and simplified floor-slab loss | Formula/API tests; clear theoretical separation |
| 3D RF surface | Three.js mesh with colour and elevation derived from RF grid | Bundle build covered by CI; visual WebGL checked |
| Router placement ranking | Per-floor candidate grid search using the propagation model | API integration tests |
| ESP32 CSI serial reader | COM-port discovery, configurable baud and CSI field column, I/Q amplitude/phase parsing | CSI parser unit tests |
| CSI signal view | Live subcarrier amplitude plot and rolling variance | Signal-variation visualizer; no people classification |
| Volumetric dataset import | CSV validation, SQLite persistence and Three.js point cloud | Parser tests; database persistence verified |
| Scan waypoint planner | Bounded serpentine x/y/z waypoint CSV for an external/manual scanner | Scan-plan unit tests |
| Project backup | JSON export/import | API endpoints verified |
| Local privacy boundary | FastAPI bound to loopback; no packet injection/deauthentication/password cracking | Safe local-first architecture |

## Not implemented or not hardware-verified

1. **Physical motorized rig control:** The release exports waypoint plans but does not send commands to stepper motors. Controller protocol, homing, travel limits, end-stops and emergency-stop integration are rig-specific and are not guessed.
2. **Physical ESP32 validation:** The serial reader and documented ESP32-CSI-Tool CSV parser exist. A compatible board and firmware are required to verify real stream timing and firmware-specific CSV layout.
3. **High-resolution through-wall imaging:** Not provided. Ordinary Wi-Fi/CSI data cannot be represented as architectural X-ray imaging.
4. **Full RF ray tracing:** The current propagation model is a simplified estimate, not a full 3D ray tracer. It omits detailed antenna patterns, multipath, furniture, doors/windows as openings, dynamic interference and calibrated material data.
5. **CAD/image floor-plan import:** Not implemented; floors are drawn in the editor.

## Automated verification

GitHub Actions workflow: `.github/workflows/ci.yml`

The workflow is configured to:
- Install Python dependencies and compile the backend.
- Run RF, SQLite, WLAN parser, CSI parser, volumetric/scan-plan, network intelligence, and scan history unit tests (35 tests).
- Run FastAPI integration tests for multi-floor coverage, survey persistence, volumetric import, network info, and history exports.
- Install Node.js, build the locally bundled Three.js renderer, and syntax-check JavaScript.
- Run Windows runner smoke tests (`setup.ps1`, `diagnose.ps1`, `start.ps1 -SmokeTest`).

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
