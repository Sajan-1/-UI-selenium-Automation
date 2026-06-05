from pathlib import Path

files = [
    Path("combined_preserved_sources/classlens_master_artifacts/chapters__classlens_all_sections_final_report.html"),
    Path("combined_preserved_sources/classlens_all_sections_final_report.html"),
    Path("combined_preserved_sources/classlens_baseline_lock/classlens_master_artifacts/chapters__classlens_all_sections_final_report.html"),
]

for p in files:
    if not p.exists():
        print("MISSING:", p)
        continue

    s = p.read_text(encoding="utf-8", errors="replace")
    score = 0
    if "Chapter Accuracy Test Report" in s: score += 5
    if "CLASSLENS QUALITY ASSURANCE" in s: score += 5
    if "Sajan Operations" in s: score -= 10
    if "<select" in s and "Mathematics Teacher" in s: score -= 10
    if ".kpi" in s or "Overall Test Pass Rate" in s: score += 3

    print()
    print("FILE:", p)
    print("SIZE:", p.stat().st_size)
    print("SCORE:", score)
    print("HAS Chapter Accuracy:", "Chapter Accuracy Test Report" in s)
    print("HAS Sajan Operations:", "Sajan Operations" in s)
    print("HAS select:", "<select" in s)
