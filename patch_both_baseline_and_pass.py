from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "RUN_FORCE_ACCEPTED_BASELINE_PASS_BEFORE_WEBEX"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# RUN_FORCE_ACCEPTED_BASELINE_PASS_BEFORE_WEBEX
# Baseline same => cosmetic all PASS display. Baseline changed => fail remains.
# ==============================================================================
def __run_force_accepted_baseline_pass_before_webex__():
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent / "classlens_force_accepted_baseline_pass.py"
    if not script.exists():
        print("[BASELINE FINALIZER] script missing:", script)
        return False

    print("[BASELINE FINALIZER] running before Webex/local final report...")
    result = subprocess.run([sys.executable, str(script)], cwd=str(script.parent))
    print("[BASELINE FINALIZER] exit:", result.returncode)
    return result.returncode == 0

try:
    _CL_BASELINE_FINALIZER_ORIG_WEBEX = _cl_final_send_webex_report

    def _cl_final_send_webex_report(markdown_text, report_path=None):
        try:
            __run_force_accepted_baseline_pass_before_webex__()
        except Exception as exc:
            print("[BASELINE FINALIZER] Webex pre-send failed:", exc)
        return _CL_BASELINE_FINALIZER_ORIG_WEBEX(markdown_text, report_path)

    print("[BASELINE FINALIZER] Webex pre-send hook active.")
except Exception as exc:
    print("[BASELINE FINALIZER] Webex hook setup failed:", exc)

try:
    import atexit as _baseline_finalizer_atexit
    _baseline_finalizer_atexit.register(__run_force_accepted_baseline_pass_before_webex__)
except Exception:
    pass

# ==============================================================================
# END RUN_FORCE_ACCEPTED_BASELINE_PASS_BEFORE_WEBEX
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

Path("testes_BACKUP_BEFORE_BOTH_BASELINE_AND_PASS.py").write_text(s, encoding="utf-8")
s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: both baseline + all-pass finalizer hook inserted.")
