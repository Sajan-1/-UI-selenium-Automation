from pathlib import Path
import re

p = Path("combined_preserved_sources/classlens_MASTER_ALL_TABS_REPORT.html")
s = p.read_text(encoding="utf-8", errors="replace")

# Remove bad forced baseline display script
s = re.sub(
    r'<script id="FORCE_BASELINE_PASS_DISPLAY">[\s\S]*?</script>',
    '',
    s,
    flags=re.I
)

# Remove banner if inserted
s = re.sub(
    r'<div[^>]*>BASELINE ACCEPTED MODE:[\s\S]*?</div>',
    '',
    s,
    flags=re.I
)

p.write_text(s, encoding="utf-8")
print("DONE: Bad baseline display override removed. Professional report restored.")
