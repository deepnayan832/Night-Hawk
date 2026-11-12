import os
import json
import re

REPOS_DIR = r"C:\Users\nayan\project-nighthawk\repos"

def inspect():
    audit_data = {}
    repos = [d for d in os.listdir(REPOS_DIR) if os.path.isdir(os.path.join(REPOS_DIR, d))]
    
    for r in sorted(repos):
        r_path = os.path.join(REPOS_DIR, r)
        files = os.listdir(r_path)
        
        # license check
        lic_files = [f for f in files if re.search(r'(license|copying)', f, re.I)]
        lic_text = ""
        if lic_files:
            try:
                with open(os.path.join(r_path, lic_files[0]), 'r', encoding='utf-8', errors='ignore') as lf:
                    lic_text = lf.read()[:500]
            except Exception as e:
                lic_text = f"Error reading license: {e}"
        
        # readme check
        readme_files = [f for f in files if re.search(r'readme', f, re.I)]
        readme_head = ""
        if readme_files:
            try:
                with open(os.path.join(r_path, readme_files[0]), 'r', encoding='utf-8', errors='ignore') as rf:
                    readme_head = rf.read()[:1000]
            except Exception as e:
                readme_head = f"Error reading readme: {e}"

        # detect project type
        proj_types = []
        if 'package.json' in files:
            proj_types.append('Node/JS/TS')
        if any(f.endswith('.py') for f in files) or 'requirements.txt' in files or 'setup.py' in files or 'pyproject.toml' in files:
            proj_types.append('Python')
        if 'Cargo.toml' in files:
            proj_types.append('Rust')
        if any(f.endswith('.ino') for f in files) or 'platformio.ini' in files or 'CMakeLists.txt' in files:
            proj_types.append('C/C++/Embedded/ESP32')

        # check file list tree (top 2 levels)
        structure = []
        for root, dirs, f_list in os.walk(r_path):
            rel = os.path.relpath(root, r_path)
            depth = rel.count(os.sep)
            if depth >= 2:
                continue
            for f in f_list[:8]:
                structure.append(os.path.join(rel, f) if rel != '.' else f)

        audit_data[r] = {
            "path": r_path,
            "project_types": proj_types,
            "top_files": files[:20],
            "sample_structure": structure[:25],
            "license_file": lic_files[0] if lic_files else "MISSING",
            "license_snippet": lic_text.strip().split('\n')[0] if lic_text else "No license file",
            "readme_head": readme_head[:600]
        }
        
    print(json.dumps(audit_data, indent=2))
    with open(r"C:\Users\nayan\project-nighthawk\repos_audit_raw.json", "w", encoding="utf-8") as out:
        json.dump(audit_data, out, indent=2)

if __name__ == '__main__':
    inspect()
