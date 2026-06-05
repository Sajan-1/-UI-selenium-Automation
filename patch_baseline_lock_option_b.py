from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "CLASSLENS_BASELINE_LOCK_OPTION_B"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# CLASSLENS_BASELINE_LOCK_OPTION_B
# Current UI/data artifacts become accepted baseline. Future changes become FAIL.
# ==============================================================================
def __cl_baseline_lock_option_b__(out_dir=None):
    from pathlib import Path
    import shutil
    import hashlib
    import json
    import re

    root = Path(__file__).resolve().parent
    out = Path(out_dir) if out_dir else root / "combined_preserved_sources"
    baseline_dir = out / "classlens_baseline_lock"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    patterns = [
        "classlens_data_all_sections_v17.json",
        "students_all_sections.json",
        "classlens_report_all_sections_v17.html",
        "classlens_MASTER_ALL_TABS_REPORT.html",
        "classlens_master_artifacts/overview__*.html",
        "classlens_master_artifacts/chapters__*.html",
        "classlens_master_artifacts/questions__*.html",
        "classlens_master_artifacts/students__*.html",
        "classlens_master_artifacts/students__*.json",
    ]

    def normalize_text(path):
        txt = path.read_text(encoding="utf-8", errors="replace")
        # remove generated timestamps and volatile local paths
        txt = re.sub(r"\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?", "<TIME>", txt)
        txt = re.sub(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?", "<TIME>", txt)
        txt = re.sub(r"C:\\Users\\User\\Downloads\\-UI-selenium-Automation", "<ROOT>", txt, flags=re.I)
        txt = re.sub(r"file:///C:/Users/User/Downloads/-UI-selenium-Automation", "<ROOTURL>", txt, flags=re.I)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def digest(path):
        data = normalize_text(path).encode("utf-8", errors="replace")
        return hashlib.sha256(data).hexdigest()

    files = []
    for pat in patterns:
        files.extend([x for x in out.glob(pat) if x.is_file()])

    # de-duplicate
    seen = set()
    unique = []
    for f in files:
        key = str(f.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(f)

    if not unique:
        print("[BASELINE LOCK] No artifacts found.")
        return 1

    manifest_path = baseline_dir / "baseline_manifest.json"
    current = {}
    for f in unique:
        rel = str(f.relative_to(out)).replace("\\", "/")
        current[rel] = {
            "sha256": digest(f),
            "size": f.stat().st_size,
        }

    if not manifest_path.exists():
        for f in unique:
            rel = Path(str(f.relative_to(out)).replace("\\", "/"))
            target = baseline_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)

        manifest_path.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
        print("[BASELINE LOCK] Baseline created. Current UI/data accepted as PASS.")
        print("[BASELINE LOCK] Files locked:", len(current))
        return 0

    old = json.loads(manifest_path.read_text(encoding="utf-8", errors="replace"))
    changes = []

    for rel, info in current.items():
        if rel not in old:
            changes.append("NEW: " + rel)
        elif old[rel].get("sha256") != info.get("sha256"):
            changes.append("CHANGED: " + rel)

    for rel in old:
        if rel not in current:
            changes.append("MISSING: " + rel)

    result_path = baseline_dir / "baseline_compare_result.json"
    result_path.write_text(json.dumps({
        "status": "PASS" if not changes else "FAIL",
        "changes": changes,
        "checked_files": len(current),
    }, indent=2), encoding="utf-8")

    if changes:
        print("[BASELINE LOCK] FAIL: UI/data changed from accepted baseline.")
        for x in changes[:30]:
            print("[BASELINE LOCK]", x)
        return 1

    print("[BASELINE LOCK] PASS: Current UI/data matches accepted baseline.")
    return 0


try:
    _CL_BASELINE_PREV_MAIN = main

    def main():
        code = _CL_BASELINE_PREV_MAIN()
        try:
            baseline_code = __cl_baseline_lock_option_b__("combined_preserved_sources")
            if baseline_code != 0:
                return baseline_code
        except Exception as exc:
            print("[BASELINE LOCK] error:", exc)
            return 1
        return 0

    print("[BASELINE LOCK] Option B active.")
except Exception as exc:
    print("[BASELINE LOCK] setup failed:", exc)

# ==============================================================================
# END CLASSLENS_BASELINE_LOCK_OPTION_B
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_BASELINE_LOCK_OPTION_B.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Baseline Lock Option B inserted.")
print("Backup:", backup)
