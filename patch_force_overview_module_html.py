from pathlib import Path
from html import escape
import re

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "FORCE_OVERVIEW_MODULE_HTML_IN_MASTER_BEFORE_WEBEX"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# FORCE_OVERVIEW_MODULE_HTML_IN_MASTER_BEFORE_WEBEX
# Ensures Webex master report shows FULL Overview details, not "No HTML report".
# ==============================================================================
def __force_overview_module_html_in_master_before_webex__(report_path=None):
    from pathlib import Path
    from html import escape
    import re
    import shutil

    root = Path(__file__).resolve().parent
    cps = root / "combined_preserved_sources"
    artifacts = cps / "classlens_master_artifacts"

    master = Path(report_path) if report_path else cps / "classlens_MASTER_ALL_TABS_REPORT.html"
    full_overview = cps / "classlens_report_all_sections_v17.html"
    overview_artifact = artifacts / "overview__classlens_all_sections_master_report_v13.html"

    if not master.exists():
        print("[OVERVIEW WEBEX FIX] master not found:", master)
        return False

    if not full_overview.exists():
        print("[OVERVIEW WEBEX FIX] full overview not found:", full_overview)
        return False

    artifacts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(full_overview, overview_artifact)

    m = master.read_text(encoding="utf-8", errors="replace")
    o = full_overview.read_text(encoding="utf-8", errors="replace")

    iframe = (
        "<iframe class='report-frame' "
        "title='Overview Tab Testing embedded report' "
        f"srcdoc=\"{escape(o, quote=True)}\" "
        "style='width:100%;height:12000px;min-height:12000px;border:0;background:#07101d;display:block;border-radius:16px;'></iframe>"
    )

    overview_block = (
        "<div class='overview-force-full-detail' "
        "style='margin-top:18px;border:1px solid #28527a;border-radius:16px;overflow:hidden;background:#07101d;'>"
        + iframe +
        "</div>"
    )

    # Replace existing Overview iframe if present.
    m, c1 = re.subn(
        r"<iframe[^>]*title=['\"]Overview Tab Testing embedded report['\"][\s\S]*?</iframe>",
        iframe,
        m,
        count=1,
        flags=re.I
    )

    # Replace the visible yellow "No HTML report..." box inside Overview module.
    m, c2 = re.subn(
        r"<div[^>]*>\s*No HTML report was produced by this module\.\s*</div>",
        overview_block,
        m,
        count=1,
        flags=re.I
    )

    # If the exact div did not match, replace plain text occurrence.
    if c2 == 0 and "No HTML report was produced by this module." in m:
        m = m.replace("No HTML report was produced by this module.", overview_block, 1)
        c2 = 1

    # Force iframe height globally.
    if "OVERVIEW_FORCE_IFRAME_HEIGHT_WEBEX" not in m:
        css = """
<style id="OVERVIEW_FORCE_IFRAME_HEIGHT_WEBEX">
iframe[title="Overview Tab Testing embedded report"],
.report-frame {
  height: 12000px !important;
  min-height: 12000px !important;
  width: 100% !important;
}
</style>
"""
        m = m.replace("</head>", css + "</head>") if "</head>" in m else css + m

    # Make left module list clickable by scrolling to module sections.
    if "OVERVIEW_FORCE_NAV_CLICK_WEBEX" not in m:
        js = """
<script id="OVERVIEW_FORCE_NAV_CLICK_WEBEX">
document.addEventListener("DOMContentLoaded", function(){
  const labels = ["Overview Tab Testing","Chapters Tab Testing","Questions Tab Testing","Students Tab Testing"];
  labels.forEach(function(label){
    document.querySelectorAll("*").forEach(function(el){
      if ((el.textContent || "").trim() === label) {
        el.style.cursor = "pointer";
        el.onclick = function(){
          const all = Array.from(document.querySelectorAll("h1,h2,h3,.module-title,.portable-module-title,section,div"));
          const target = all.find(x => (x.textContent || "").includes(label) && x.getBoundingClientRect().height > 80);
          if (target) target.scrollIntoView({behavior:"smooth", block:"start"});
        };
      }
    });
  });
});
</script>
"""
        m = m.replace("</body>", js + "</body>") if "</body>" in m else m + js

    master.write_text(m, encoding="utf-8")

    print("[OVERVIEW WEBEX FIX] full overview artifact:", overview_artifact)
    print("[OVERVIEW WEBEX FIX] iframe replaced:", c1)
    print("[OVERVIEW WEBEX FIX] no-html block replaced:", c2)
    print("[OVERVIEW WEBEX FIX] master updated before Webex:", master)
    return True

# Patch final attachment sender: this is the real Webex upload path.
try:
    _cl_original_final_send_webex_report = _cl_final_send_webex_report

    def _cl_final_send_webex_report(markdown_text, report_path=None):
        print("[OVERVIEW WEBEX FIX] applying before final Webex attachment upload...")
        __force_overview_module_html_in_master_before_webex__(report_path)
        return _cl_original_final_send_webex_report(markdown_text, report_path)

    print("[OVERVIEW WEBEX FIX] final Webex attachment sender patched.")
except Exception as exc:
    print("[OVERVIEW WEBEX FIX] final sender patch failed:", exc)

# ==============================================================================
# END FORCE_OVERVIEW_MODULE_HTML_IN_MASTER_BEFORE_WEBEX
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_FORCE_OVERVIEW_MODULE_HTML.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Forced Overview module HTML patch inserted before __main__.")
print("Backup:", backup)
