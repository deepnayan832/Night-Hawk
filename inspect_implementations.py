import os
import glob
import json

REPOS_DIR = r"C:\Users\nayan\project-nighthawk\repos"

def show(title, content):
    print(f"=== {title} ===")
    if content:
        print(content[:1500])
    else:
        print("None")
    print("\n")

# 1. open-heat scanner
oh_scanner = os.path.join(REPOS_DIR, "open-heat")
for f in os.listdir(oh_scanner):
    if f.endswith('.py') or f.endswith('.js'):
        print(f"open-heat file: {f}")
        try:
            with open(os.path.join(oh_scanner, f), 'r', encoding='utf-8', errors='ignore') as fp:
                print(fp.read()[:1000])
        except Exception as e:
            pass

# 2. Wi-Fi_HeatMap
wfh_dir = os.path.join(REPOS_DIR, "Wi-Fi_HeatMap")
for f in os.listdir(wfh_dir):
    if f.endswith('.py'):
        print(f"Wi-Fi_HeatMap file: {f}")
        try:
            with open(os.path.join(wfh_dir, f), 'r', encoding='utf-8', errors='ignore') as fp:
                print(fp.read()[:1000])
        except Exception as e:
            pass

# 3. wifi-heatmap (ribaldorafael)
rf_dir = os.path.join(REPOS_DIR, "wifi-heatmap")
for f in ["scanner.py", "heatmap.py", "insights.py"]:
    p = os.path.join(rf_dir, f)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            show(f"wifi-heatmap -> {f}", fp.read())

# 4. SignalPlan packages and architecture
sp_dir = os.path.join(REPOS_DIR, "SignalPlan")
print("SignalPlan structure:")
for root, dirs, files in os.walk(sp_dir):
    rel = os.path.relpath(root, sp_dir)
    if 'node_modules' in rel or '.git' in rel:
        continue
    if len(rel.split(os.sep)) <= 3:
        print(rel, files[:5])

# 5. 3D_wifi_scanner
s3d_dir = os.path.join(REPOS_DIR, "3D_wifi_scanner")
print("3D_wifi_scanner structure:")
for root, dirs, files in os.walk(s3d_dir):
    rel = os.path.relpath(root, s3d_dir)
    if '.git' in rel:
        continue
    print(rel, files)

# 6. ESP32-CSI-Tool python utils
ect_dir = os.path.join(REPOS_DIR, "ESP32-CSI-Tool")
py_u = os.path.join(ect_dir, "python_utils")
if os.path.exists(py_u):
    print("ESP32-CSI-Tool python_utils:", os.listdir(py_u))
    for f in os.listdir(py_u):
        if f.endswith('.py'):
            with open(os.path.join(py_u, f), 'r', encoding='utf-8', errors='ignore') as fp:
                show(f"ESP32-CSI-Tool -> {f}", fp.read()[:1200])
