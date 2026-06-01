from pathlib import Path
from html import escape

master = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
overview = Path("combined_preserved_sources/classlens_master_artifacts/overview__classlens_all_sections_master_report_v13.html")

m = master.read_text(encoding="utf-8", errors="replace")
o = overview.read_text(encoding="utf-8", errors="replace")

new_iframe = (
    "<iframe class='report-frame' "
    "title='Overview Tab Testing embedded report' "
    f"srcdoc=\"{escape(o, quote=True)}\"></iframe>"
)

start = m.find("title='Overview Tab Testing embedded report'")
if start == -1:
    raise RuntimeError("Overview iframe not found")

iframe_start = m.rfind("<iframe", 0, start)
iframe_end = m.find("</iframe>", start) + len("</iframe>")

m = m[:iframe_start] + new_iframe + m[iframe_end:]
master.write_text(m, encoding="utf-8")

print("DONE: Portable Master Overview iframe updated with full v17 report.")
