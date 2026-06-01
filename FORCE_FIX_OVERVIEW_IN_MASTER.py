from pathlib import Path
from html import escape
import re
import shutil

master = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
overview = Path("combined_preserved_sources/classlens_master_artifacts/overview__classlens_all_sections_master_report_v13.html")

m = master.read_text(encoding="utf-8", errors="replace")
o = overview.read_text(encoding="utf-8", errors="replace")

backup = master.with_name("classlens_MASTER_ALL_TABS_REPORT_BACKUP_BEFORE_OVERVIEW_IFRAME_FIX.html")
shutil.copy2(master, backup)

new_iframe = (
    "<iframe class='report-frame' "
    "title='Overview Tab Testing embedded report' "
    f"srcdoc=\"{escape(o, quote=True)}\"></iframe>"
)

pattern1 = r"<iframe[^>]*title=['\"]Overview Tab Testing embedded report['\"][\s\S]*?</iframe>"
m2, count1 = re.subn(pattern1, new_iframe, m, flags=re.I)

pattern2 = r"<iframe[^>]*overview__classlens_all_sections_master_report_v13\.html[\s\S]*?</iframe>"
m2, count2 = re.subn(pattern2, new_iframe, m2, flags=re.I)

master.write_text(m2, encoding="utf-8")

print("DONE")
print("title iframe replacements:", count1)
print("file iframe replacements:", count2)
print("backup:", backup)
print("master:", master)
print("overview artifact size:", overview.stat().st_size)
