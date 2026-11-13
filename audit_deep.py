import os
import glob
import json

REPOS_DIR = r"C:\Users\nayan\project-nighthawk\repos"

def get_file_content(path, max_len=2000):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()[:max_len]
        except Exception as e:
            return str(e)
    return None

details = {}

# 1. wifi-heatmapper
wh_dir = os.path.join(REPOS_DIR, "wifi-heatmapper")
details["wifi-heatmapper"] = {
    "package_json": get_file_content(os.path.join(wh_dir, "package.json")),
    "desktop": os.listdir(os.path.join(wh_dir, "desktop")) if os.path.exists(os.path.join(wh_dir, "desktop")) else [],
    "src_files": [os.path.relpath(p, wh_dir) for p in glob.glob(os.path.join(wh_dir, "src", "**", "*.*"), recursive=True)[:30]],
    "license": get_file_content(os.path.join(wh_dir, "LICENSE"), 400)
}

# 2. open-heat
oh_dir = os.path.join(REPOS_DIR, "open-heat")
details["open-heat"] = {
    "files": os.listdir(oh_dir),
    "readme": get_file_content(os.path.join(oh_dir, "README.md"), 1000),
    "code_files": [f for f in os.listdir(oh_dir) if f.endswith(('.py', '.js', '.html', '.sh', '.bat', '.ps1', '.json'))],
    "license": get_file_content(os.path.join(oh_dir, "LICENSE"), 400)
}

# 3. Wi-Fi_HeatMap
wfh_dir = os.path.join(REPOS_DIR, "Wi-Fi_HeatMap")
details["Wi-Fi_HeatMap"] = {
    "files": os.listdir(wfh_dir),
    "readme": get_file_content(os.path.join(wfh_dir, "README.md"), 1000),
    "code_files": [f for f in os.listdir(wfh_dir) if f.endswith(('.py', '.js', '.html', '.txt'))],
    "license": get_file_content(os.path.join(wfh_dir, "LICENSE"), 400)
}

# 4. wifi-heatmap (ribaldo)
rf_dir = os.path.join(REPOS_DIR, "wifi-heatmap")
details["wifi-heatmap"] = {
    "files": os.listdir(rf_dir),
    "app_py": get_file_content(os.path.join(rf_dir, "app.py"), 1000),
    "scanner_py": get_file_content(os.path.join(rf_dir, "scanner.py"), 1000),
    "heatmap_py": get_file_content(os.path.join(rf_dir, "heatmap.py"), 1000),
    "license": get_file_content(os.path.join(rf_dir, "LICENSE"), 400)
}

# 5. SignalPlan
sp_dir = os.path.join(REPOS_DIR, "SignalPlan")
details["SignalPlan"] = {
    "package_json": get_file_content(os.path.join(sp_dir, "package.json"), 1000),
    "packages": os.listdir(os.path.join(sp_dir, "packages")) if os.path.exists(os.path.join(sp_dir, "packages")) else [],
    "apps": os.listdir(os.path.join(sp_dir, "apps")) if os.path.exists(os.path.join(sp_dir, "apps")) else [],
    "license": get_file_content(os.path.join(sp_dir, "LICENSE"), 400)
}

# 6. 3D_wifi_scanner
s3d_dir = os.path.join(REPOS_DIR, "3D_wifi_scanner")
details["3D_wifi_scanner"] = {
    "files": os.listdir(s3d_dir),
    "wifi_mapper_files": os.listdir(os.path.join(s3d_dir, "wifi_mapper")) if os.path.exists(os.path.join(s3d_dir, "wifi_mapper")) else [],
    "node_mcu": os.listdir(os.path.join(s3d_dir, "node_mcu_code")) if os.path.exists(os.path.join(s3d_dir, "node_mcu_code")) else [],
    "readme": get_file_content(os.path.join(s3d_dir, "README.md"), 1000)
}

# 7. ethersweep
es_dir = os.path.join(REPOS_DIR, "ethersweep")
details["ethersweep"] = {
    "files": os.listdir(es_dir),
    "readme": get_file_content(os.path.join(es_dir, "README.md"), 1000),
    "license": get_file_content(os.path.join(es_dir, "LICENSE"), 400)
}

# 8. wifi-3d-fusion
w3f_dir = os.path.join(REPOS_DIR, "wifi-3d-fusion")
details["wifi-3d-fusion"] = {
    "files": os.listdir(w3f_dir),
    "readme": get_file_content(os.path.join(w3f_dir, "README.md"), 1000),
    "license": get_file_content(os.path.join(w3f_dir, "LICENSE"), 400)
}

# 9. WiFi-CSI-Human-Detection
csih_dir = os.path.join(REPOS_DIR, "WiFi-CSI-Human-Detection")
details["WiFi-CSI-Human-Detection"] = {
    "files": os.listdir(csih_dir),
    "readme": get_file_content(os.path.join(csih_dir, "README.md"), 1000),
    "license": get_file_content(os.path.join(csih_dir, "LICENSE"), 400)
}

# 10. csi-gui-rs
cg_dir = os.path.join(REPOS_DIR, "csi-gui-rs")
details["csi-gui-rs"] = {
    "cargo_toml": get_file_content(os.path.join(cg_dir, "Cargo.toml"), 1000),
    "files": os.listdir(cg_dir),
    "license": get_file_content(os.path.join(cg_dir, "LICENSE"), 400)
}

# 11. esp-csi-cli-rs
ecc_dir = os.path.join(REPOS_DIR, "esp-csi-cli-rs")
details["esp-csi-cli-rs"] = {
    "cargo_toml": get_file_content(os.path.join(ecc_dir, "Cargo.toml"), 1000),
    "files": os.listdir(ecc_dir),
    "license": get_file_content(os.path.join(ecc_dir, "LICENSE"), 400)
}

# 12. ESP32-CSI-Tool
ect_dir = os.path.join(REPOS_DIR, "ESP32-CSI-Tool")
details["ESP32-CSI-Tool"] = {
    "files": os.listdir(ect_dir),
    "python_utils": os.listdir(os.path.join(ect_dir, "python_utils")) if os.path.exists(os.path.join(ect_dir, "python_utils")) else [],
    "license": get_file_content(os.path.join(ect_dir, "LICENSE"), 400)
}

with open(r"C:\Users\nayan\project-nighthawk\repos_detailed_audit.json", "w", encoding="utf-8") as out:
    json.dump(details, out, indent=2)

print("Saved detailed audit.")
