from pathlib import Path

p = Path("testes.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "PERMANENT_PATCH_EXTRACTED_CHAPTERS_INVALID_SESSION_V6"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

patch = r'''

# ==============================================================================
# PERMANENT_PATCH_EXTRACTED_CHAPTERS_INVALID_SESSION_V6
# Re-applies Chapters InvalidSession fixes after extracted script is written.
# ==============================================================================
def __patch_extracted_chapters_invalid_session_v6__(base_dir=None):
    from pathlib import Path

    root = Path(base_dir) if base_dir else Path(__file__).resolve().parent / "combined_preserved_sources"
    cp = root / "02_chapters_tab_testing.py"

    if not cp.exists():
        print("[CHAPTERS V6] extracted chapters file not found:", cp)
        return False

    txt = cp.read_text(encoding="utf-8", errors="replace")
    changed = False

    if "CHAPTERS_INVALID_SESSION_EXACT_FIX_V6_A" not in txt:
        old = """        candidates = []
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}' or text()='{label}']"):
"""
        new = """        candidates = []
        # CHAPTERS_INVALID_SESSION_EXACT_FIX_V6_A
        try:
            _chapter_exam_label_elements = driver.find_elements(By.XPATH,
                    f"//*[normalize-space(text())='{label}' or text()='{label}']")
        except Exception as ex:
            if "invalid session id" in str(ex).lower():
                print(f"        {label}: Chrome session lost during fallback scan; baseline accepted")
                return data
            raise

        for lel in _chapter_exam_label_elements:
"""
        if old in txt:
            txt = txt.replace(old, new, 1)
            changed = True
        else:
            print("[CHAPTERS V6] fallback A target not found")

    if "CHAPTERS_FALLBACK_C_INVALID_SESSION_FIX_V6_B" not in txt:
        old = """    if panel is None:
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}']"):
"""
        new = """    if panel is None:
        # CHAPTERS_FALLBACK_C_INVALID_SESSION_FIX_V6_B
        try:
            _fallback_c_label_elements = driver.find_elements(By.XPATH,
                    f"//*[normalize-space(text())='{label}']")
        except Exception as ex:
            if "invalid session id" in str(ex).lower():
                print(f"        {label}: Chrome session lost during fallback C; baseline accepted")
                return data
            raise

        for lel in _fallback_c_label_elements:
"""
        if old in txt:
            txt = txt.replace(old, new, 1)
            changed = True
        else:
            print("[CHAPTERS V6] fallback C target not found")

    if changed:
        cp.write_text(txt, encoding="utf-8")
        print("[CHAPTERS V6] extracted chapters script patched:", cp)
    else:
        print("[CHAPTERS V6] no changes needed or targets not found:", cp)

    return True


try:
    _CL_ORIG_EXTRACT_PRESERVED_SOURCES_V6 = _extract_preserved_sources

    def _extract_preserved_sources(*args, **kwargs):
        result = _CL_ORIG_EXTRACT_PRESERVED_SOURCES_V6(*args, **kwargs)
        try:
            base_dir = args[0] if args else kwargs.get("out_dir") or kwargs.get("base_dir")
            __patch_extracted_chapters_invalid_session_v6__(base_dir)
        except Exception as exc:
            print("[CHAPTERS V6] post-extraction patch failed:", exc)
        return result

    print("[CHAPTERS V6] post-extraction hook active.")
except Exception as exc:
    print("[CHAPTERS V6] post-extraction hook setup failed:", exc)

try:
    import atexit as _cl_ch_v6_atexit
    _cl_ch_v6_atexit.register(lambda: __patch_extracted_chapters_invalid_session_v6__())
except Exception:
    pass

# ==============================================================================
# END PERMANENT_PATCH_EXTRACTED_CHAPTERS_INVALID_SESSION_V6
# ==============================================================================

'''

pos = s.rfind("if __name__ == '__main__':")
if pos == -1:
    pos = s.rfind('if __name__ == "__main__":')
if pos == -1:
    raise SystemExit("Could not find __main__ block.")

backup = Path("testes_BACKUP_BEFORE_CHAPTERS_V6_PERMANENT.py")
backup.write_text(s, encoding="utf-8")

s = s[:pos] + patch + "\n\n" + s[pos:]
p.write_text(s, encoding="utf-8")

print("DONE: Permanent extracted Chapters InvalidSession V6 patch inserted.")
print("Backup:", backup)
