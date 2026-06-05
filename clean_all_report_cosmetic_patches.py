from pathlib import Path
import re

root = Path("combined_preserved_sources")
targets = list(root.glob("*.html")) + list((root / "classlens_master_artifacts").glob("*.html"))

bad_ids = [
    "CLASSLENS_FORCE_ACCEPTED_BASELINE_PASS",
    "BASELINE_ACCEPTED_KPI_PASS_FIX",
    "SAFE_BASELINE_PASS_UI",
    "FORCE_BASELINE_PASS_DISPLAY",
]

for p in targets:
    s = p.read_text(encoding="utf-8", errors="replace")
    old = s
    for bid in bad_ids:
        s = re.sub(rf'<script id="{bid}">[\s\S]*?</script>', '', s, flags=re.I)
    if s != old:
        p.write_text(s, encoding="utf-8")
        print("cleaned:", p)

print("DONE: cosmetic/pass-display JS removed.")
