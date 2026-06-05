from pathlib import Path

p = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "FORCE_TEST_MODULE_NAV_CLICK_FIX"
if marker in s:
    print("Already fixed.")
    raise SystemExit(0)

fix = r'''
<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">
document.addEventListener("DOMContentLoaded", function () {
  const map = {
    "Overview Tab Testing": "panel-overview",
    "Chapters Tab Testing": "panel-chapters",
    "Questions Tab Testing": "panel-questions",
    "Students Tab Testing": "panel-students"
  };

  function activatePanel(label) {
    const id = map[label];
    if (!id) return;

    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

    const panel = document.getElementById(id);
    if (panel) {
      panel.classList.add("active");
      panel.style.display = "block";
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    document.querySelectorAll(".tab-btn").forEach(btn => {
      if ((btn.textContent || "").includes(label)) btn.classList.add("active");
    });
  }

  document.querySelectorAll(".tab-btn").forEach(btn => {
    const txt = (btn.textContent || "").trim();
    Object.keys(map).forEach(label => {
      if (txt.includes(label)) {
        btn.style.cursor = "pointer";
        btn.onclick = function(e) {
          e.preventDefault();
          e.stopPropagation();
          activatePanel(label);
        };
      }
    });
  });
});
</script>
'''

if "</body>" in s:
    s = s.replace("</body>", fix + "\n</body>", 1)
else:
    s += fix

p.write_text(s, encoding="utf-8")
print("DONE: Test Modules click navigation fixed in master HTML.")
