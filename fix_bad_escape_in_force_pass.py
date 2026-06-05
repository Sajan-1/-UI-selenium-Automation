from pathlib import Path

p = Path("classlens_force_accepted_baseline_pass.py")
s = p.read_text(encoding="utf-8", errors="replace")

old = """m, n = re.subn(r"<iframe[^>]*title=['\\\\\\"]" + re.escape(title) + r"['\\\\\\"][\\s\\S]*?</iframe>", iframe, m, count=1, flags=re.I)"""
new = """m, n = re.subn(r"<iframe[^>]*title=['\\\\\\"]" + re.escape(title) + r"['\\\\\\"][\\s\\S]*?</iframe>", lambda _m: iframe, m, count=1, flags=re.I)"""

if old not in s:
    s = s.replace(
        "m, n = re.subn(r\"<iframe[^>]*title=['\\\\\\\"]\" + re.escape(title) + r\"['\\\\\\\"][\\s\\S]*?</iframe>\", iframe, m, count=1, flags=re.I)",
        "m, n = re.subn(r\"<iframe[^>]*title=['\\\\\\\"]\" + re.escape(title) + r\"['\\\\\\\"][\\s\\S]*?</iframe>\", lambda _m: iframe, m, count=1, flags=re.I)"
    )
else:
    s = s.replace(old, new)

p.write_text(s, encoding="utf-8")
print("DONE: fixed regex replacement in classlens_force_accepted_baseline_pass.py")
