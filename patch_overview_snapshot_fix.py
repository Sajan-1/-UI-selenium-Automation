from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "FORCE_OVERVIEW_ARTIFACT_IN_SNAPSHOT_FIX"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# FORCE_OVERVIEW_ARTIFACT_IN_SNAPSHOT_FIX
# Ensures Overview HTML is captured so Embedded count becomes 4 and module panel works.
# ==============================================================================
try:
    _CL_ORIG_SNAPSHOT_MODULE_ARTIFACTS = _snapshot_module_artifacts

    def _snapshot_module_artifacts(key: str, module_dir: _Path, started_at: float, exit_code: int) -> dict:
        result = _CL_ORIG_SNAPSHOT_MODULE_ARTIFACTS(key, module_dir, started_at, exit_code)

        if str(key).lower() == "overview":
            try:
                artifact_dir = module_dir / _MASTER_ARTIFACT_DIRNAME
                artifact_dir.mkdir(parents=True, exist_ok=True)

                candidates = [
                    module_dir / "classlens_report_all_sections_v17.html",
                    module_dir / "classlens_all_sections_final_report.html",
                    module_dir / "classlens_all_sections_report.html",
                    module_dir / "classlens_all_sections_master_report_v13.html",
                ]

                found = None
                for c in candidates:
                    if c.exists() and c.is_file() and c.stat().st_size > 100000:
                        found = c
                        break

                if found is None:
                    large = list(module_dir.glob("*all_sections*.html")) + list(module_dir.glob("*overview*.html"))
                    large = [x for x in large if x.is_file() and x.stat().st_size > 100000]
                    if large:
                        found = max(large, key=lambda x: x.stat().st_size)

                if found:
                    target = artifact_dir / ("overview__" + found.name)
                    _shutil.copy2(found, target)

                    artifacts = list(result.get("artifacts", []))
                    if target not in artifacts:
                        artifacts.insert(0, target)
                    result["artifacts"] = artifacts

                    try:
                        for r in _MASTER_RUN_RESULTS:
                            if r.get("module") == "overview":
                                r["artifacts"] = artifacts
                    except Exception:
                        pass

                    print("[OVERVIEW SNAPSHOT FIX] Overview HTML forced into artifacts:", target)
                else:
                    print("[OVERVIEW SNAPSHOT FIX] No large Overview HTML found to force-add.")

            except Exception as exc:
                print("[OVERVIEW SNAPSHOT FIX] failed:", exc)

        return result

    print("[OVERVIEW SNAPSHOT FIX] active.")
except Exception as exc:
    print("[OVERVIEW SNAPSHOT FIX] setup failed:", exc)

# ==============================================================================
# END FORCE_OVERVIEW_ARTIFACT_IN_SNAPSHOT_FIX
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_OVERVIEW_SNAPSHOT_FIX.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Overview snapshot artifact fix inserted.")
print("Backup:", backup)
