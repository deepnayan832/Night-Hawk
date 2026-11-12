import os
import glob
import json

REPOS_DIR = r"C:\Users\nayan\project-nighthawk\repos"

# 1. SignalPlan
sp_dir = os.path.join(REPOS_DIR, "SignalPlan")
print("=== SignalPlan packages ===")
for root, dirs, files in os.walk(os.path.join(sp_dir, "packages")):
    for f in files:
        if f.endswith(('.ts', '.js', '.json')) and not f.endswith(('.d.ts', '.map')):
            rel = os.path.relpath(os.path.join(root, f), sp_dir)
            print(rel)

print("\n=== SignalPlan apps ===")
for root, dirs, files in os.walk(os.path.join(sp_dir, "apps")):
    for f in files:
        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.json')) and not f.endswith(('.d.ts', '.map')):
            rel = os.path.relpath(os.path.join(root, f), sp_dir)
            print(rel)

# 2. 3D_wifi_scanner wifi_mapper
s3d_dir = os.path.join(REPOS_DIR, "3D_wifi_scanner")
print("\n=== 3D_wifi_scanner files ===")
for root, dirs, files in os.walk(os.path.join(s3d_dir, "wifi_mapper")):
    for f in files:
        p = os.path.join(root, f)
        print(f, os.path.getsize(p))
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                print(f"--- {f} content head ---")
                print(fp.read()[:800])
        except Exception as e:
            print(f"Error {e}")

# 3. ethersweep
es_dir = os.path.join(REPOS_DIR, "ethersweep")
print("\n=== ethersweep files ===")
for root, dirs, files in os.walk(es_dir):
    if '.git' in root: continue
    for f in files:
        if f.endswith(('.py', '.ino', '.cpp', '.h', '.md')):
            print(os.path.relpath(os.path.join(root, f), es_dir))

# 4. wifi-3d-fusion
w3f_dir = os.path.join(REPOS_DIR, "wifi-3d-fusion")
print("\n=== wifi-3d-fusion files ===")
for root, dirs, files in os.walk(w3f_dir):
    if '.git' in root: continue
    for f in files:
        if f.endswith(('.py', '.ipynb', '.md', '.yaml', '.sh')):
            print(os.path.relpath(os.path.join(root, f), w3f_dir))

# 5. WiFi-CSI-Human-Detection
csih_dir = os.path.join(REPOS_DIR, "WiFi-CSI-Human-Detection")
print("\n=== WiFi-CSI-Human-Detection files ===")
for root, dirs, files in os.walk(csih_dir):
    if '.git' in root: continue
    for f in files:
        print(os.path.relpath(os.path.join(root, f), csih_dir))
