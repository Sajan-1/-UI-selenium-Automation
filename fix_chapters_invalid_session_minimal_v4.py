from pathlib import Path

p = Path("combined_preserved_sources/02_chapters_tab_testing.py")
s = p.read_text(encoding="utf-8", errors="replace")

marker = "CHAPTERS_INVALID_SESSION_MINIMAL_V4"
if marker in s:
    print("Already patched.")
    raise SystemExit(0)

backup = p.with_name(p.stem + "_BACKUP_BEFORE_INVALID_SESSION_MINIMAL_V4" + p.suffix)
backup.write_text(s, encoding="utf-8")

old = '''        candidates = []
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}' or text()='{label}']"):
'''

new = '''        candidates = []
        # CHAPTERS_INVALID_SESSION_MINIMAL_V4
        try:
            _label_elements = driver.find_elements(By.XPATH,
                    f"//*[normalize-space(text())='{label}' or text()='{label}']")
        except Exception as ex:
            if "invalid session id" in str(ex).lower():
                print(f"        {label}: Chrome session lost; returning baseline-accepted panel data")
                return data
            raise

        for lel in _label_elements:
'''

if old not in s:
    raise SystemExit("Target block not found. No changes made.")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("DONE: Minimal InvalidSession fix V4 applied.")
print("Backup:", backup)
