from pathlib import Path

p = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
s = p.read_text(encoding="utf-8", errors="replace")

# Remove old click-fix if already injected
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
    if (!panel) {
      console.warn("Panel not found:", id);
      return;
    }

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

p.write_text(s, encoding="utf-8")
print("DONE: Strong Test Modules click fix applied.")
