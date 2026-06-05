from pathlib import Path
from html import escape
import re

master = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
chapter = Path("combined_preserved_sources/classlens_master_artifacts/chapters__classlens_all_sections_final_report.html")

m = master.read_text(encoding="utf-8", errors="replace")
c = chapter.read_text(encoding="utf-8", errors="replace")

iframe = (
    "<iframe class='report-frame' "
    "title='Chapters Tab Testing embedded report' "
    f"srcdoc=\"{escape(c, quote=True)}\"></iframe>"
)

m2, n = re.subn(
    r"<iframe[^>]*title=['\"]Chapters Tab Testing embedded report['\"][\s\S]*?</iframe>",
    lambda _m: iframe,
    m,
    count=1,
    flags=re.I
)

if n == 0:
    raise SystemExit("Chapters iframe not found in master report.")

master.write_text(m2, encoding="utf-8")
print("DONE: Chapters iframe rebuilt from clean professional chapter artifact.")
