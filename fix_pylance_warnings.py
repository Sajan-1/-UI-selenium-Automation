from pathlib import Path
import re

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

backup = Path("testes_BACKUP_BEFORE_PYLANCE_WARNING_FIX.py")
backup.write_text(s, encoding="utf-8")

# Ensure _re is available near top
if "import re as _re" not in s:
    s = "import re as _re\n" + s

# Add safe dummy placeholders for old dead hook references so Pylance stops warning.
stub = r'''

# ----------------------------------------------------------------------
# PYLANCE SAFE PLACEHOLDERS FOR OLD OPTIONAL HOOKS
# These are no-op fallbacks only. Real builders, if defined earlier/later,
# will still be used by runtime code where applicable.
# ----------------------------------------------------------------------
try:
    _build_portable_master_html
except NameError:
    def _build_portable_master_html(*args, **kwargs):
        raise RuntimeError("_build_portable_master_html is unavailable in this build")

try:
    _build_master_report_html
except NameError:
    def _build_master_report_html(*args, **kwargs):
        raise RuntimeError("_build_master_report_html is unavailable in this build")

try:
    _build_master_html
except NameError:
    def _build_master_html(*args, **kwargs):
        raise RuntimeError("_build_master_html is unavailable in this build")
# ----------------------------------------------------------------------

'''

marker = "PYLANCE SAFE PLACEHOLDERS FOR OLD OPTIONAL HOOKS"
if marker not in s:
    pos = s.find("def ")
    if pos == -1:
        s += stub
    else:
        s = s[:pos] + stub + "\n" + s[pos:]

p.write_text(s, encoding="utf-8")

print("DONE: Pylance warning fixes added.")
print("Backup:", backup)
