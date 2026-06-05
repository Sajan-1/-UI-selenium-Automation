from pathlib import Path
import re

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "MASTER CLICKABILITY FIX AFTER FULL OVERVIEW EMBED"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

fix_func = r'''

# ==============================================================================
# MASTER CLICKABILITY FIX AFTER FULL OVERVIEW EMBED
# Fixes issue where huge Overview iframe blocks other test modules/tabs.
# ==============================================================================
def __cl_fix_master_clickability_after_overview_embed__():
    try:
        from pathlib import Path as _Path
        root = _Path.cwd()
        master = root / "combined_preserved_sources" / "classlens_MASTER_ALL_TABS_REPORT.html"
        if not master.exists():
            return 1

        html = master.read_text(encoding="utf-8", errors="replace")

        # Remove bad giant iframe sizing that blocks tabs/modules.
        html = html.replace("height:12000px!important;min-height:12000px!important;", "height:900px!important;min-height:900px!important;")
        html = html.replace("height:12000px!important", "height:900px!important")
        html = html.replace("height:12000px", "height:900px")
        html = html.replace("min-height:12000px", "min-height:900px")

        css = """
<style id="cl-master-clickability-fix">
  .tab-panel:not(.active),
  .module-panel:not(.active),
  .report-panel:not(.active){
    display:none!important;
    pointer-events:none!important;
    height:0!important;
    overflow:hidden!important;
  }

  .tab-panel.active,
  .module-panel.active,
  .report-panel.active{
    display:block!important;
    pointer-events:auto!important;
    height:auto!important;
    overflow:visible!important;
    position:relative!important;
    z-index:1!important;
  }

  .tabs,
  .tab-btn,
  .module-tabs,
  .module-nav,
  button,
  a{
    position:relative!important;
    z-index:99999!important;
    pointer-events:auto!important;
  }

  iframe.report-frame,
  .report-frame{
    width:100%!important;
    height:900px!important;
    min-height:900px!important;
    max-height:900px!important;
    position:relative!important;
    z-index:1!important;
    display:block!important;
    border:0!important;
    pointer-events:auto!important;
  }

  .fullscreen iframe.report-frame,
  .fullscreen .report-frame{
    height:calc(100vh - 110px)!important;
    min-height:calc(100vh - 110px)!important;
    max-height:calc(100vh - 110px)!important;
  }
</style>
"""

        if "cl-master-clickability-fix" not in html:
            head_end = html.lower().find("</head>")
            if head_end != -1:
                html = html[:head_end] + css + html[head_end:]
            else:
                html = css + html

        master.write_text(html, encoding="utf-8")
        print("[MASTER CLICKABILITY FIX] Applied. Tabs/modules clickable; Overview remains scrollable.")
        return 0
    except Exception as exc:
        print("[MASTER CLICKABILITY FIX] Failed:", exc)
        return 1

# ==============================================================================
# END MASTER CLICKABILITY FIX
# ==============================================================================

'''

# Insert function before __main__
pos = max(s.rfind("if __name__ == '__main__':"), s.rfind('if __name__ == "__main__":'))
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

s = s[:pos] + fix_func + "\n\n" + s[pos:]

# Call clickability fix immediately after every full overview fix call.
s = s.replace(
    "__cl_force_full_detailed_overview_in_master_now__()\n            print(\"[WEBEX PRE-SEND ATTACHMENT] Overview master report fix complete.\")",
    "__cl_force_full_detailed_overview_in_master_now__()\n            __cl_fix_master_clickability_after_overview_embed__()\n            print(\"[WEBEX PRE-SEND ATTACHMENT] Overview master report fix complete.\")"
)

s = s.replace(
    "_cl_fix_exit_code = __cl_force_full_detailed_overview_in_master_now__()",
    "_cl_fix_exit_code = __cl_force_full_detailed_overview_in_master_now__()\n    __cl_fix_master_clickability_after_overview_embed__()"
)

backup = Path("testes_BACKUP_BEFORE_MASTER_CLICKABILITY_FIX.py")
backup.write_text(p.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
p.write_text(s, encoding="utf-8")

print("DONE: Master clickability fix added.")
print("Backup:", backup)
