<div align="center">

# 🌙 NIGHTHAWK

### Wi-Fi Intelligence · RF Surveying · 3D Spatial Mapping

**Make your wireless environment easier to measure, understand, and visualize.**

[![License](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows)](HARDWARE_REQUIREMENTS.md)
[![Project](https://img.shields.io/badge/Focus-Wi--Fi%20%7C%20RF%20%7C%203D-667eea)](ARCHITECTURE.md)
[![GitHub Pages](https://img.shields.io/badge/Website-GitHub%20Pages-111827?logo=github)](https://deepnayan832.github.io/Night-Hawk/)

[**Website**](https://deepnayan832.github.io/Night-Hawk/) · [**Architecture**](ARCHITECTURE.md) · [**Hardware Guide**](HARDWARE_REQUIREMENTS.md) · [**Issues**](https://github.com/deepnayan832/Night-Hawk/issues)

</div>

---

## ✨ What is NightHawk?

**NightHawk** is a Windows-focused project exploring local Wi-Fi surveying, floor-plan-based RF analysis, and 2D/3D wireless coverage visualization.

The goal is to combine real measurements from a Windows Wi-Fi adapter with floor-plan geometry and clearly labelled RF propagation models. Optional hardware integrations explore Channel State Information (CSI) sensing and physical volumetric scanning.

> **Measurement honesty is a core design principle:** measured signal data, theoretical simulations, archived sample datasets, and optional-hardware readings must never be presented as the same thing.

## 🧭 Project at a glance

| Area | Project direction |
|---|---|
| Platform | Windows 10/11 x64 |
| Primary language/runtime | Python backend + web-based frontend (planned architecture) |
| Network access | Native Windows WLAN tooling |
| Spatial analysis | 2D interpolation and 3D RF propagation modelling |
| Local data | SQLite and project JSON/CSV exports (design target) |
| Optional hardware | ESP32 CSI devices and motorized scan rigs |
| Website | Static GitHub Pages landing page |

## 🚀 Feature map

The following describes the project's intended application modules and architecture. **It is not a claim that every module is currently runnable from this repository snapshot.**

| Module | Purpose |
|---|---|
| **Wi-Fi Scanner** | Inspect nearby access points and available adapter metrics such as signal, channel, band, and link rate. |
| **Home Survey** | Record signal readings against user-selected positions on a calibrated floor plan. |
| **Floor Plan Editor** | Model rooms, walls, doors, windows, materials, and router locations. |
| **3D Home View** | Visualize floor-plan geometry and access-point positions in a 3D scene. |
| **2D Signal Heatmap** | Interpolate collected measurements using methods such as Inverse Distance Weighting (IDW). |
| **3D Coverage Map** | Explore modelled RF propagation and compare predictions with measured samples. |
| **Router Optimizer** | Compare candidate access-point placements and channel conditions. |
| **Volumetric Scanner** | Visualize spatial RSSI datasets as point clouds or voxel-like views. |
| **CSI Sensing** | Process compatible CSI streams for experimental motion/presence analysis. |
| **History & Export** | Compare survey sessions and exchange project data. |
| **Hardware Status** | Distinguish connected hardware from simulation or archived-data modes. |

## 🧱 Hardware tiers

NightHawk separates standard PC functionality from optional sensing equipment.

<details>
<summary><strong>Tier 1 — Standard Windows PC + Wi-Fi router</strong></summary>

- Windows 10/11 x64 computer.
- Integrated or USB Wi-Fi adapter supported by Windows WLAN AutoConfig.
- Existing Wi-Fi router or access point.
- Intended for WLAN discovery, adapter metrics, manual survey workflows, floor-plan modelling, and software-based RF visualization.

</details>

<details>
<summary><strong>Tier 2 — Optional ESP32 CSI hardware</strong></summary>

- Compatible ESP32-family board and USB serial connection.
- Supported CSI firmware and appropriate device/driver setup.
- Intended for collecting CSI measurements for experimental signal-based motion or presence analysis.
- CSI access is not provided by every router or Wi-Fi adapter.

</details>

<details>
<summary><strong>Tier 3 — Optional motorized scanning rig</strong></summary>

- Motorized 2-axis or 3-axis frame.
- Compatible controller and probe hardware.
- Intended for repeatable physical spatial sampling.
- Not required for ordinary Wi-Fi scanning or floor-plan work.

</details>

**Important limitation:** Consumer Wi-Fi equipment does not provide genuine architectural X-ray vision. Floor plans must be drawn or imported; RF measurements and propagation estimates cannot reveal detailed wall structures by themselves.

See **[Hardware Requirements & Truth Matrix](HARDWARE_REQUIREMENTS.md)** for details.

## 🖥️ Repository status & getting started

### Current repository snapshot

The current `main` branch contains project documentation, audit material, PowerShell utility scripts, and the static GitHub Pages landing page. The application source directories referenced by the setup scripts (such as `nighthawk-backend` and `nighthawk-ui`) are **not present in the currently published repository tree**.

The implementation tracker describes completed modules, but those source folders are not available in this public snapshot for an independent fresh-clone build. Treat the feature list as the project's documented design/status, not as a verified downloadable application.

### Before running the setup scripts

The current PowerShell scripts also contain a machine-specific base path:

```text
C:\Users\nayan\project-nighthawk
```

That path will not match most users' clone locations. The scripts need to be made portable (for example, by using `$PSScriptRoot`) and the referenced application source folders need to be included before the quick-start workflow can work from a fresh clone.

### Clone the repository

```powershell
git clone https://github.com/deepnayan832/Night-Hawk.git
Set-Location Night-Hawk
```

Review these files first:

- [Implementation Status](IMPLEMENTATION_STATUS.md)
- [Architecture](ARCHITECTURE.md)
- [Hardware Requirements](HARDWARE_REQUIREMENTS.md)
- [Repository Audit](REPOSITORY_AUDIT.md)
- [License Audit](LICENSE_AUDIT.md)

<blockquote>
<strong>Setup is not currently a verified one-command install.</strong> Do not run <code>setup.ps1</code> expecting a clean build from a fresh clone until the missing application folders are committed and the hard-coded paths in the scripts are corrected.
</blockquote>

## 🏗️ Architecture overview

The documented target architecture is organized into four layers:

1. **Frontend** — React, TypeScript, Tailwind CSS, Three.js, and interactive spatial views.
2. **Local API** — Python/FastAPI services for Wi-Fi polling, surveys, RF calculations, hardware adapters, and data exchange.
3. **Analysis** — measured-signal interpolation, propagation estimates, router-placement analysis, and optional CSI processing.
4. **Local storage & devices** — SQLite/project files, Windows WLAN services, optional ESP32 serial devices, and optional motor controllers.

For the detailed design and data flow, see **[ARCHITECTURE.md](ARCHITECTURE.md)**.

## 🔬 RF modelling principles

The project documentation describes a combination of measured and modelled approaches:

- **Measured signal:** RSSI values collected from the Windows network adapter at known survey positions.
- **Interpolation:** IDW/RBF-style methods to estimate values between recorded survey points.
- **Propagation modelling:** Free-Space Path Loss (FSPL) and material/floor attenuation estimates.
- **Validation:** Compare predicted values with measurements and expose residual/error information where available.

A simulated coverage surface is an estimate, not a substitute for a real survey. Material attenuation values depend on frequency, construction, thickness, geometry, and environment.

## 🔐 Privacy & responsible use

NightHawk is designed around local-first operation:

- Keep survey projects and exports on the user's machine.
- Clearly identify live readings, simulations, and archived sample data.
- Use standard defensive WLAN discovery and adapter information.
- Do not perform packet injection, deauthentication, password cracking, or unauthorized access.
- Sanitize SSIDs/BSSIDs before sharing survey exports publicly.

Local-first design does not automatically guarantee security. Review dependencies, permissions, data exports, and upstream code before use.

## 🧩 Upstream projects & attribution

The project documents research and integration references from these upstream repositories:

<details>
<summary><strong>View upstream repository audit (12 projects)</strong></summary>

| Repository | Area | Upstream license noted in audit |
|---|---|---|
| [hnykda/wifi-heatmapper](https://github.com/hnykda/wifi-heatmapper) | Windows Wi-Fi scanning and heatmaps | MIT |
| [dcchill/open-heat](https://github.com/dcchill/open-heat) | WLAN parsing and diagnostics | MIT |
| [J0nan/Wi-Fi_HeatMap](https://github.com/J0nan/Wi-Fi_HeatMap) | 2D interpolation and floor-plan calibration | MIT |
| [ribaldorafael/wifi-heatmap](https://github.com/ribaldorafael/wifi-heatmap) | Channel analysis and heatmap patterns | MIT |
| [NC4321/SignalPlan](https://github.com/NC4321/SignalPlan) | RF propagation and 3D floor-plan concepts | MIT |
| [Neumi/3D_wifi_scanner](https://github.com/Neumi/3D_wifi_scanner) | Volumetric RSSI dataset and visualization | Custom / review upstream terms |
| [Neumi/ethersweep](https://github.com/Neumi/ethersweep) | Motorized scanner control | GPL-3.0 |
| [DwayneCon/wifi-3d-fusion](https://github.com/DwayneCon/wifi-3d-fusion) | CSI preprocessing | Apache-2.0 |
| [s-shrikanth/WiFi-CSI-Human-Detection](https://github.com/s-shrikanth/WiFi-CSI-Human-Detection) | CSI-based motion analysis | MIT |
| [csi-rs/csi-gui-rs](https://github.com/csi-rs/csi-gui-rs) | CSI framing and device interface | MIT / Apache-2.0 |
| [csi-rs/esp-csi-cli-rs](https://github.com/csi-rs/esp-csi-cli-rs) | ESP32 CSI streaming | MIT / Apache-2.0 |
| [StevenMHernandez/ESP32-CSI-Tool](https://github.com/StevenMHernandez/ESP32-CSI-Tool) | ESP32 CSI firmware/tooling | MIT |

</details>

Upstream licenses remain applicable to the relevant code and assets. A repository-level MIT license does **not** relicense third-party material. Review [LICENSE_AUDIT.md](LICENSE_AUDIT.md) before redistributing integrated components.

## 🗺️ Project documentation

| Document | Description |
|---|---|
| [Architecture](ARCHITECTURE.md) | System components, data flow, and design decisions |
| [Hardware Requirements](HARDWARE_REQUIREMENTS.md) | Hardware tiers, capability boundaries, and limitations |
| [Implementation Status](IMPLEMENTATION_STATUS.md) | Project-reported implementation progress |
| [Repository Audit](REPOSITORY_AUDIT.md) | Upstream repository research and integration notes |
| [License Audit](LICENSE_AUDIT.md) | Third-party license review |
| [GitHub Pages](https://deepnayan832.github.io/Night-Hawk/) | Static project landing page |

## 🤝 Contributing

Contributions, issue reports, documentation fixes, and reproducible test results are welcome.

1. Check existing [issues](https://github.com/deepnayan832/Night-Hawk/issues) before opening a duplicate.
2. Describe your Windows version, Wi-Fi adapter model, and reproduction steps.
3. Separate measured results from simulated or archived data in reports.
4. Include tests or verification steps for code changes.
5. Preserve upstream notices and license obligations when working with third-party code.

## 📄 License

The project-level license is [MIT](LICENSE). Third-party components may have different licenses; see [LICENSE_AUDIT.md](LICENSE_AUDIT.md) and the original upstream repositories.

---

<div align="center">

**NightHawk — make wireless environments visible, measurable, and understandable.**

[Website](https://deepnayan832.github.io/Night-Hawk/) · [Repository](https://github.com/deepnayan832/Night-Hawk) · [Report a bug](https://github.com/deepnayan832/Night-Hawk/issues)

</div>
