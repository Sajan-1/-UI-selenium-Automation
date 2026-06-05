from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "PERMANENT_WEBEX_TEST_MODULE_CLICK_FIX"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# PERMANENT_WEBEX_TEST_MODULE_CLICK_FIX
# Ensures Test Modules sidebar is clickable in local + Webex attached master HTML.
# ==============================================================================
def __cl_force_test_module_click_fix__(report_path=None):
    from pathlib import Path

    root = Path(__file__).resolve().parent
    master = Path(report_path) if report_path else root / "combined_preserved_sources" / "classlens_MASTER_ALL_TABS_REPORT.html"

    if not master.exists():
        print("[TEST MODULE CLICK FIX] master not found:", master)
        return False

    s = master.read_text(encoding="utf-8", errors="replace")

    start = s.find('<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">')
    if start != -1:
        end = s.find("</script>", start)
        if end != -1:
            s = s[:start] + s[end + len("</script>"):]

    fix = r'''
<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">
(function(){
  const map = {
    "Overview Tab Testing": "panel-overview",
    "Chapters Tab Testing": "panel-chapters",
    "Questions Tab Testing": "panel-questions",
    "Students Tab Testing": "panel-students"
  };

  function showPanel(label){
    const id = map[label];
    const panel = document.getElementById(id);
    if (!panel) return;

    document.querySelectorAll(".tab-panel").forEach(function(p){
      p.classList.remove("active");
      p.style.display = "none";
    });

    panel.classList.add("active");
    panel.style.display = "block";

    document.querySelectorAll(".tab-btn").forEach(function(b){
      b.classList.remove("active");
      const t = (b.textContent || "").replace(/\s+/g," ").trim();
      if (t.includes(label)) b.classList.add("active");
    });

    setTimeout(function(){
      panel.scrollIntoView({behavior:"smooth", block:"start"});
    }, 80);
  }

  function bind(){
    Object.keys(map).forEach(function(label){
      document.querySelectorAll("button, a, div, span, li").forEach(function(el){
        const txt = (el.textContent || "").replace(/\s+/g," ").trim();
        if (txt === label || txt.includes(label)) {
          if (el.closest(".sidebar") || el.classList.contains("tab-btn")) {
            el.style.cursor = "pointer";
            el.onclick = function(e){
              e.preventDefault();
              e.stopPropagation();
              showPanel(label);
              return false;
            };
          }
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
</script>
'''

    if "</body>" in s:
        s = s.replace("</body>", fix + "\n</body>", 1)
    else:
        s += fix

    master.write_text(s, encoding="utf-8")
    print("[TEST MODULE CLICK FIX] applied:", master)
    return True

# Wrap Webex final attachment sender so attached HTML is fixed before upload.
try:
    _CL_ORIG_WEBEX_FINAL_SEND_WITH_CLICK_FIX = _cl_final_send_webex_report

    def _cl_final_send_webex_report(markdown_text, report_path=None):
        try:
            __cl_force_test_module_click_fix__(report_path)
        except Exception as exc:
            print("[TEST MODULE CLICK FIX] pre-Webex failed:", exc)
        return _CL_ORIG_WEBEX_FINAL_SEND_WITH_CLICK_FIX(markdown_text, report_path)

    print("[TEST MODULE CLICK FIX] Webex pre-send wrapper active.")
except Exception as exc:
    print("[TEST MODULE CLICK FIX] Webex wrapper setup failed:", exc)

# Also run at normal script exit for local opened report.
try:
    import atexit as _cl_click_atexit
    _cl_click_atexit.register(lambda: __cl_force_test_module_click_fix__())
except Exception:
    pass

# ==============================================================================
# END PERMANENT_WEBEX_TEST_MODULE_CLICK_FIX
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_PERMANENT_CLICK_FIX.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Permanent Webex Test Modules click fix inserted.")
print("Backup:", backup)
