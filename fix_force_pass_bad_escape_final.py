from pathlib import Path
import re

p = Path("classlens_force_accepted_baseline_pass.py")
s = p.read_text(encoding="utf-8", errors="replace")

# Replace ANY re.subn call in rebuild_master_srcdocs that uses iframe as direct replacement.
s2 = re.sub(
    r'(m,\s*n\s*=\s*re\.subn\(\s*r"<iframe\[\^>\]\*title=.*?re\.escape\(title\).*?\[\\s\\S\]\*\?</iframe>",\s*)iframe(\s*,\s*m,\s*count=1,\s*flags=re\.I\s*\))',
    r'\1lambda _m: iframe\2',
    s,
    flags=re.S
)

if s2 == s:
    # Direct fallback for the exact line from your traceback.
    old = 'm, n = re.subn(r"<iframe[^>]*title=[\\\'\\\\"]" + re.escape(title) + r"[\\\'\\\\"][\\s\\S]*?</iframe>", iframe, m, count=1, flags=re.I)'
    new = 'm, n = re.subn(r"<iframe[^>]*title=[\\\'\\\\"]" + re.escape(title) + r"[\\\'\\\\"][\\s\\S]*?</iframe>", lambda _m: iframe, m, count=1, flags=re.I)'
    s2 = s.replace(old, new)

if s2 == s:
    raise SystemExit("Could not patch automatically. Open file and manually replace: iframe, -> lambda _m: iframe,")

backup = Path("classlens_force_accepted_baseline_pass_BACKUP_BAD_ESCAPE.py")
backup.write_text(s, encoding="utf-8")
p.write_text(s2, encoding="utf-8")

print("DONE: bad escape regex replacement fixed.")
print("Backup:", backup)
