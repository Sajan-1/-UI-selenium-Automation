from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

if "[WEBEX FINAL FIX] Applying full detailed Overview report before upload..." in s:
    print("Already patched.")
    raise SystemExit(0)

target = """def _cl_final_send_webex_report(markdown_text, report_path=None):
    try:
        import requests as _requests
    except Exception as exc:
        print('[WEBEX] requests package not available:', exc)
        return False
    try:
        token = globals().get('WEBEX_BOT_TOKEN', '') or _os.environ.get('WEBEX_BOT_TOKEN', '')
"""

replacement = """def _cl_final_send_webex_report(markdown_text, report_path=None):
    try:
        import requests as _requests
    except Exception as exc:
        print('[WEBEX] requests package not available:', exc)
        return False

    try:
        print("[WEBEX FINAL FIX] Applying full detailed Overview report before upload...")
        __cl_force_full_detailed_overview_in_master_now__()
        print("[WEBEX FINAL FIX] Overview report patched successfully.")
    except Exception as exc:
        print("[WEBEX FINAL FIX] Patch failed:", exc)

    try:
        token = globals().get('WEBEX_BOT_TOKEN', '') or _os.environ.get('WEBEX_BOT_TOKEN', '')
"""

if target not in s:
    raise SystemExit("Target block not found. File structure changed; patch not applied.")

backup = Path("testes_BACKUP_BEFORE_WEBEX_FINAL_FIX_INSERT.py")
backup.write_text(s, encoding="utf-8")

s = s.replace(target, replacement, 1)
p.write_text(s, encoding="utf-8")

print("DONE: WEBEX FINAL FIX inserted inside _cl_final_send_webex_report before upload.")
print("Backup:", backup)
