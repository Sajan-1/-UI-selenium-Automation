from pathlib import Path
import re

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

needle = "[WEBEX] status:"
idx = s.find(needle)
if idx == -1:
    raise SystemExit("WEBEX status print not found. Need Webex send block location.")

# Find start of the line/block before WEBEX status print.
line_start = s.rfind("\n", 0, idx)
insert_at = line_start + 1

call = """
# ----------------------------------------------------------------------
# FORCE OVERVIEW FULL DETAIL BEFORE WEBEX SEND
# This must run BEFORE Webex uploads classlens_MASTER_ALL_TABS_REPORT.html
# ----------------------------------------------------------------------
try:
    __cl_force_full_detailed_overview_in_master_now__()
except Exception as _webex_overview_fix_exc:
    print("[WEBEX PRE-FIX] Overview full-detail master fix failed:", _webex_overview_fix_exc)

"""

if "FORCE OVERVIEW FULL DETAIL BEFORE WEBEX SEND" in s:
    print("Already patched.")
else:
    s = s[:insert_at] + call + s[insert_at:]
    backup = Path("testes_BACKUP_BEFORE_WEBEX_OVERVIEW_MOVE.py")
    backup.write_text(p.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    p.write_text(s, encoding="utf-8")
    print("DONE: Overview fix inserted before Webex send/status block.")
    print("Backup:", backup)
