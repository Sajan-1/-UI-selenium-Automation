from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "# WEBEX PRE-SEND OVERVIEW FULL REPORT WRAPPER"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

insert = r'''

# ==============================================================================
# WEBEX PRE-SEND OVERVIEW FULL REPORT WRAPPER
# ADD-ONLY: patches Portable Master before Webex uploads the HTML attachment.
# ==============================================================================
try:
    _classlens_original_webex_send_message = _classlens_webex_send_message

    def _classlens_webex_send_message(markdown_message):
        try:
            print("[WEBEX PRE-SEND] Applying full Overview report patch before Webex upload...")
            __cl_force_full_detailed_overview_in_master_now__()
            print("[WEBEX PRE-SEND] Overview full report patch complete.")
        except Exception as _pre_send_fix_exc:
            print("[WEBEX PRE-SEND] Overview patch failed:", _pre_send_fix_exc)

        # Avoid Windows charmap crash from emoji markdown in some consoles.
        try:
            markdown_message = (
                str(markdown_message)
                .replace("✅", "[PASS]")
                .replace("❌", "[FAIL]")
                .replace("⚠️", "[WARN]")
                .replace("⚠", "[WARN]")
                .replace("📎", "[ATTACHED]")
            )
        except Exception:
            pass

        return _classlens_original_webex_send_message(markdown_message)

    print("[WEBEX PRE-SEND] Wrapper active: patched master report will be uploaded to Webex.")
except Exception as _webex_wrapper_exc:
    print("[WEBEX PRE-SEND] Wrapper install failed:", _webex_wrapper_exc)

# ==============================================================================
# END WEBEX PRE-SEND OVERVIEW FULL REPORT WRAPPER
# ==============================================================================

'''

positions = [
    s.rfind("if __name__ == '__main__':"),
    s.rfind('if __name__ == "__main__":'),
]
pos = max(positions)

if pos == -1:
    raise SystemExit("Could not find __main__ block. Do not patch automatically.")

backup = Path("testes_BACKUP_BEFORE_SAFE_WEBEX_WRAPPER.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + insert + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Safe Webex pre-send wrapper inserted before __main__ block.")
print("Backup:", backup)
