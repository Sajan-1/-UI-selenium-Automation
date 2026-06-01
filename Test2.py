@'
import subprocess
import sys
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent

print("=" * 80)
print("RUNNING MAIN MASTER SCRIPT: testes.py")
print("=" * 80)

main_result = subprocess.run([sys.executable, str(ROOT / "testes.py")])

print("=" * 80)
print("APPLYING FINAL OVERVIEW MASTER REPORT FIX")
print("=" * 80)

fix_result = subprocess.run([sys.executable, str(ROOT / "FORCE_FIX_OVERVIEW_IN_MASTER.py")])

master = ROOT / "combined_preserved_sources" / "classlens_MASTER_ALL_TABS_REPORT.html"

print("=" * 80)
print("OPENING FINAL PORTABLE MASTER QA REPORT")
print("=" * 80)
print(master)

if master.exists():
    os.startfile(master)

raise SystemExit(main_result.returncode if main_result.returncode != 0 else fix_result.returncode)
'@ | Set-Content RUN_FINAL_MASTER_WITH_OVERVIEW_FIX.py -Encoding UTF8