# NightHawk — Implementation Status

**Current release:** 1.0.0 Tier 1 application baseline  
**Last updated:** November 12, 2026  
**Verification state:** Source committed; automated CI run pending/required; Windows hardware validation has not been performed in this session.

This file reports what is actually present in the repository. A source-code implementation is not treated as verified on a physical Windows adapter until it has been run on that platform.

## Release 1.0.0 scope

| Component | Repository implementation | Verification status |
|---|---|---|
| FastAPI local server | `nighthawk-backend/main.py` | Added; CI/import validation pending |
| SQLite project and survey storage | `nighthawk-backend/db.py` | Unit tests added |
| Windows WLAN scan | `nighthawk-backend/wifi.py` using `netsh` | Implemented; requires Windows adapter validation |
| Signal display | Signal percentage + clearly labelled estimated dBm conversion | Implemented; not calibrated RSSI |
| Survey sessions and points | Create, save, list and export CSV | Implemented; database tests added |
| Floor-plan editing | Dimensions, router placement, material-labelled wall drawing/removal | Implemented in browser UI |
| 2D plan view | Canvas floor-plan editor | Implemented |
| 3D preview | Isometric canvas projection with wall height and rotation control | Implemented as a preview; not Three.js/WebGL |
| Measured heatmap | IDW interpolation of saved measurements | Implemented; RF unit tests added |
| Predicted coverage | FSPL plus simplified wall-material attenuation | Implemented; estimates only |
| Router placement ranking | Grid-search against simplified predicted RF score | Implemented; requires real-world validation |
| API documentation | FastAPI Swagger UI at `/docs` | Available when server is running |
| Optional CSI sensing | No serial/ESP32 capture implementation in this release | Not implemented |
| Motorized volumetric scanning | No gantry/controller driver in this release | Not implemented |
| Multi-floor plans / CAD image import | Not included in this release | Not implemented |

## Automated verification

GitHub Actions workflow: `.github/workflows/ci.yml`

The workflow is configured to:
- Install the Python runtime dependencies.
- Compile the Python source files.
- Run RF and SQLite unit tests.
- Validate frontend JavaScript syntax with Node.js.

A green CI run proves the listed automated checks passed in the runner environment. It does not prove that a particular Windows Wi-Fi adapter exposes every netsh field, nor that the RF model matches a particular building.

## Windows validation checklist

These steps still need to be run on a real Windows 10/11 machine:

- [ ] Run `.`\setup.ps1 from a fresh clone.
- [ ] Confirm the local API opens at `http://127.0.0.1:8765`.
- [ ] Confirm the Wi-Fi scanner returns actual nearby BSSIDs for the adapter.
- [ ] Check behavior when Windows Location privacy access is disabled.
- [ ] Create a survey and save several measured points.
- [ ] Restart the service and confirm the project and survey points persist.
- [ ] Compare a measured heatmap with a second physical walk survey.
- [ ] Validate router-placement recommendations in the actual room.
- [ ] Test the stop script without affecting unrelated processes.

## Known limitations

1. The Windows scanner relies on `netsh wlan`. Field labels and nearby-network visibility can vary with Windows language, permissions and adapter drivers.
2. Windows signal quality percentage is not calibrated dBm. NightHawk converts it to an approximate dBm display value and records the source.
3. The RF model uses indicative wall attenuation constants and 2D wall crossings. It does not yet model detailed antenna patterns, multipath, furniture, floor-to-floor propagation, or measured material properties.
4. The 3D panel is an isometric canvas preview, not a full Three.js engine.
5. CSI sensing, people detection, volumetric live capture, motorized gantry control, and multi-floor modelling remain future work.
6. A live survey is only as accurate as the user's position calibration, adapter/driver readings and measurement procedure.

## Roadmap

### Next: stabilize Tier 1
- Validate against multiple Windows Wi-Fi adapters and locales.
- Improve Wi-Fi parsing for localized Windows command output.
- Add floor-plan image import and calibration.
- Add JSON project export/import and session management controls.
- Add model calibration from survey measurements and error metrics.
- Improve 3D rendering and multi-floor geometry.

### Later: optional hardware
- ESP32 CSI serial protocol adapter with hardware capability detection.
- CSI time-series visualizer and carefully validated motion experiments.
- Separate, opt-in motorized scanner adapter with a documented safe command contract.

No optional hardware feature is considered complete until it has been tested with the corresponding physical hardware.
