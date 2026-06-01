from pathlib import Path
import shutil

master = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")

html = master.read_text(encoding="utf-8", errors="replace")

backup = master.with_name("classlens_MASTER_ALL_TABS_REPORT_BACKUP_BEFORE_IFRAME_HEIGHT_FIX.html")
shutil.copy2(master, backup)

html = html.replace(
    ".report-frame{width:100%;height:900px;border:0;background:white;display:block}",
    ".report-frame{width:100%;height:12000px;border:0;background:white;display:block}"
)

html = html.replace(
    ".report-frame{height:720px}",
    ".report-frame{height:12000px}"
)

html = html.replace(
    ".fullscreen .report-frame{height:calc(100vh - 110px)!important}",
    ".fullscreen .report-frame{height:12000px!important}"
)

master.write_text(html, encoding="utf-8")

print("DONE: iframe height fixed to 12000px")
print("Backup:", backup)
print("Updated:", master)
