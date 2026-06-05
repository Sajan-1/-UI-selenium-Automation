from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "PERMANENT_TEST_MODULE_CLICK_FIX_V2"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

js = r"""
<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">
(function(){
  const map = {
    "Overview Tab Testing": "panel-overview",
    "Chapters Tab Testing": "panel-chapters",
    "Questions Tab Testing": "panel-questions",
    "Students Tab Testing": "panel-students"
  };

  function labelFromText(t){
    t = (t || "").replace(/\s+/g," ").trim();
    return Object.keys(map).find(label => t.includes(label));
  }

  function showPanel(label){
    const id = map[label];
    const panel = document.getElementById(id);
    if(!panel) return false;

    document.querySelectorAll(".tab-panel").forEach(p => {
      p.classList.remove("active");
      p.style.display = "none";
    });

    panel.classList.add("active");
    panel.style.display = "block";

    document.querySelectorAll(".tab-btn").forEach(b => {
      b.classList.remove("active");
      if(labelFromText(b.textContent) === label) b.classList.add("active");
    });

    panel.scrollIntoView({behavior:"smooth", block:"start"});
    return true;
  }

  function bind(){
    document.querySelectorAll(".tab-btn, .sidebar button, .sidebar div, .sidebar span, .sidebar li, .tabs button").forEach(el => {
      const label = labelFromText(el.textContent);
      if(label){
        el.style.cursor = "pointer";
        el.onclick = function(e){
          e.preventDefault();
          e.stopPropagation();
          return !showPanel(label);
        };
      }
    });

    document.addEventListener("click", function(e){
      const el = e.target.closest(".tab-btn, .sidebar *");
      if(!el) return;
      const label = labelFromText(el.textContent);
      if(label){
        e.preventDefault();
        e.stopPropagation();
        showPanel(label);
      }
    }, true);
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
</script>
"""

patch = f'''

# ==============================================================================
# PERMANENT_TEST_MODULE_CLICK_FIX_V2
# Makes Test Modules sidebar clickable in local and Webex attached master report.
# ==============================================================================
def __cl_apply_test_module_click_fix__(report_path=None):
    from pathlib import Path
    import re

    root = Path(__file__).resolve().parent
    master = Path(report_path) if report_path else root / "combined_preserved_sources" / "classlens_MASTER_ALL_TABS_REPORT.html"

    if not master.exists():
        print("[TEST MODULE CLICK FIX] master not found:", master)
        return False

    html = master.read_text(encoding="utf-8", errors="replace")
    html = re.sub(r'<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">[\\s\\S]*?</script>', '', html, flags=re.I)

    fix = {js!r}

    if "</body>" in html:
        html = html.replace("</body>", fix + "\\n</body>", 1)
    else:
        html += fix

    master.write_text(html, encoding="utf-8")
    print("[TEST MODULE CLICK FIX] applied:", master)
    return True

try:
    _CL_ORIG_BUILD_MASTER_REPORT_CLICK_FIX = _build_master_report

    def _build_master_report(out_dir, order, final_code):
        path = _CL_ORIG_BUILD_MASTER_REPORT_CLICK_FIX(out_dir, order, final_code)
        try:
            __cl_apply_test_module_click_fix__(path)
        except Exception as exc:
            print("[TEST MODULE CLICK FIX] build hook failed:", exc)
        return path

    print("[TEST MODULE CLICK FIX] master build hook active.")
except Exception as exc:
    print("[TEST MODULE CLICK FIX] master build hook setup failed:", exc)

try:
    _CL_ORIG_WEBEX_SEND_CLICK_FIX = _cl_final_send_webex_report

    def _cl_final_send_webex_report(markdown_text, report_path=None):
        try:
            __cl_apply_test_module_click_fix__(report_path)
        except Exception as exc:
            print("[TEST MODULE CLICK FIX] Webex pre-send failed:", exc)
        return _CL_ORIG_WEBEX_SEND_CLICK_FIX(markdown_text, report_path)

    print("[TEST MODULE CLICK FIX] Webex pre-send hook active.")
except Exception as exc:
    print("[TEST MODULE CLICK FIX] Webex hook setup failed:", exc)

try:
    import atexit as _cl_click_fix_atexit
    _cl_click_fix_atexit.register(lambda: __cl_apply_test_module_click_fix__())
except Exception:
    pass

# ==============================================================================
# END PERMANENT_TEST_MODULE_CLICK_FIX_V2
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_CLICK_FIX_V2.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Permanent Test Modules click fix V2 inserted.")
print("Backup:", backup)
