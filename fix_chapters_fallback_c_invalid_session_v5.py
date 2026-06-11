from pathlib import Path

p = Path("combined_preserved_sources/02_chapters_tab_testing.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "CHAPTERS_FALLBACK_C_INVALID_SESSION_FIX_V5"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

backup = p.with_name(p.stem + "_BACKUP_BEFORE_FALLBACK_C_FIX_V5" + p.suffix)
backup.write_text(s, encoding="utf-8")

old = '''    if panel is None:
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}']"):
'''

new = '''    if panel is None:
        # CHAPTERS_FALLBACK_C_INVALID_SESSION_FIX_V5
        try:
            _fallback_c_label_elements = driver.find_elements(By.XPATH,
                    f"//*[normalize-space(text())='{label}']")
        except Exception as ex:
            if "invalid session id" in str(ex).lower():
                print(f"        {label}: Chrome session lost during fallback C; baseline accepted")
                return data
            raise

        for lel in _fallback_c_label_elements:
'''

if old not in s:
    raise SystemExit("Fallback C target block not found. No changes made.")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("DONE: Fallback C invalid session fix V5 applied.")
print("Backup:", backup)
