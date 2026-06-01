from pathlib import Path
from html import escape
import re

base = Path("combined_preserved_sources")
master = base / "classlens_MASTER_ALL_TABS_REPORT.html"
overview = base / "classlens_report_all_sections_v17.html"

m = master.read_text(encoding="utf-8", errors="ignore")
o = overview.read_text(encoding="utf-8", errors="ignore")

backup = base / "classlens_MASTER_ALL_TABS_REPORT_BACKUP.html"
backup.write_text(m, encoding="utf-8")

encoded = escape(o, quote=True)

new_iframe = (
    "<iframe class='report-frame' "
    "title='Overview Tab Testing embedded report' "
    f"srcdoc=\"{encoded}\"></iframe>"
)

pattern = r"<iframe class='report-frame' title='Overview Tab Testing embedded report' srcdoc=\".*?\">\s*</iframe>"

new_m, count = re.subn(pattern, new_iframe, m, count=1, flags=re.S)

print("replace count =", count)

if count == 0:
    start = m.find("title='Overview Tab Testing embedded report'")
    if start == -1:
        raise RuntimeError("Overview iframe title not found")
    iframe_start = m.rfind("<iframe", 0, start)
    iframe_end = m.find("</iframe>", start)
    if iframe_start == -1 or iframe_end == -1:
        raise RuntimeError("Overview iframe boundaries not found")
    iframe_end += len("</iframe>")
    new_m = m[:iframe_start] + new_iframe + m[iframe_end:]
    print("manual replace done")

master.write_text(new_m, encoding="utf-8")
print("DONE")
print(master)
