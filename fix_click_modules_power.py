from pathlib import Path
import re

p = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
s = p.read_text(encoding="utf-8", errors="replace")

# remove existing click fix
s = re.sub(r'<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">[\s\S]*?</script>', '', s, flags=re.I)
s = re.sub(r'<style id="FORCE_TEST_MODULE_NAV_CLICK_STYLE">[\s\S]*?</style>', '', s, flags=re.I)

fix = r'''
<style id="FORCE_TEST_MODULE_NAV_CLICK_STYLE">
#module-nav, .module-nav, .sidebar, .test-modules, .tab-btn,
#module-nav *, .module-nav *, .sidebar *, .test-modules *, .tab-btn * {
  pointer-events: auto !important;
  cursor: pointer !important;
  z-index: 99999 !important;
}
</style>

<script id="FORCE_TEST_MODULE_NAV_CLICK_FIX">
(function(){
  const MAP = {
    "Overview Tab Testing": "panel-overview",
    "Chapters Tab Testing": "panel-chapters",
    "Questions Tab Testing": "panel-questions",
    "Students Tab Testing": "panel-students"
  };

  function clean(t){ return (t || "").replace(/\s+/g," ").trim(); }

  function findLabel(el){
    let n = el;
    while(n && n !== document.body){
      const t = clean(n.textContent);
      for(const label of Object.keys(MAP)){
        if(t === label || (t.includes(label) && t.length < 180)) return label;
      }
      n = n.parentElement;
    }
    return null;
  }

  function activate(label){
    const panel = document.getElementById(MAP[label]);
    if(!panel){
      console.log("Panel missing:", label, MAP[label]);
      return false;
    }

    document.querySelectorAll(".tab-panel").forEach(function(p){
      p.classList.remove("active");
      p.style.display = "none";
    });

    panel.classList.add("active");
    panel.style.display = "block";

    document.querySelectorAll(".tab-btn, button, a, div, span, li").forEach(function(el){
      const t = clean(el.textContent);
      if(t.includes("Tab Testing") && t.length < 180) el.classList.remove("active");
      if(t.includes(label) && t.length < 180) el.classList.add("active");
    });

    panel.scrollIntoView({behavior:"smooth", block:"start"});
    console.log("Activated:", label);
    return true;
  }

  function bind(){
    document.querySelectorAll("button,a,div,span,li").forEach(function(el){
      const label = findLabel(el);
      if(label){
        el.style.cursor = "pointer";
        el.onclick = function(e){
          e.preventDefault();
          e.stopPropagation();
          activate(label);
          return false;
        };
      }
    });
  }

  document.addEventListener("click", function(e){
    const label = findLabel(e.target);
    if(label){
      e.preventDefault();
      e.stopPropagation();
      activate(label);
      return false;
    }
  }, true);

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }

  setTimeout(bind, 500);
  setTimeout(bind, 1500);

  console.log("FORCE_TEST_MODULE_NAV_CLICK_FIX loaded");
})();
</script>
'''

s = s.replace("</body>", fix + "\n</body>", 1) if "</body>" in s else s + fix
p.write_text(s, encoding="utf-8")
print("DONE: stronger Test Modules click fix injected.")
