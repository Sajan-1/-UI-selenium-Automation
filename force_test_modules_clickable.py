from pathlib import Path

p = Path(r"combined_preserved_sources\classlens_MASTER_ALL_TABS_REPORT.html")

html = p.read_text(encoding="utf-8", errors="replace")

fix = r"""
<script id="FORCE_TEST_MODULES_CLICKABLE_V2">
(function(){

function bindTabs(){

    const labels = [
        "Overview Tab Testing",
        "Chapters Tab Testing",
        "Questions Tab Testing",
        "Students Tab Testing"
    ];

    const panels = Array.from(document.querySelectorAll(".tab-panel"));

    document.querySelectorAll("*").forEach(function(el){

        const txt = (el.textContent || "").replace(/\s+/g," ").trim();

        labels.forEach(function(label, idx){

            if(txt === label){

                el.style.cursor = "pointer";
                el.style.pointerEvents = "auto";

                el.onclick = function(e){

                    e.preventDefault();
                    e.stopPropagation();

                    panels.forEach(function(p){
                        p.classList.remove("active");
                        p.style.display = "none";
                    });

                    if(panels[idx]){
                        panels[idx].style.display = "block";
                        panels[idx].classList.add("active");
                        panels[idx].scrollIntoView({
                            behavior:"smooth",
                            block:"start"
                        });
                    }

                    document.querySelectorAll("*").forEach(function(x){
                        x.classList.remove("active");
                    });

                    el.classList.add("active");

                    return false;
                };
            }
        });
    });
}

if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", bindTabs);
}else{
    bindTabs();
}

setTimeout(bindTabs,1000);
setTimeout(bindTabs,3000);

})();
</script>
"""

if "FORCE_TEST_MODULES_CLICKABLE_V2" not in html:
    html = html.replace("</body>", fix + "</body>")
    p.write_text(html, encoding="utf-8")
    print("DONE: TEST MODULES clickable patch applied.")
else:
    print("Already patched.")

