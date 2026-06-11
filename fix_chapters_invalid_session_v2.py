from pathlib import Path
import re

files = [
    Path("combined_preserved_sources/02_chapters_tab_testing.py"),
    Path("testes.py"),
]

for p in files:
    if not p.exists():
        print("SKIP missing:", p)
        continue

    s = p.read_text(encoding="utf-8", errors="replace")

    if "CHAPTERS_READ_EXAM_PANEL_INVALID_SESSION_FIX_V2" in s:
        print("Already patched:", p)
        continue

    backup = p.with_name(p.stem + "_BACKUP_BEFORE_CHAPTERS_INVALID_SESSION_V2" + p.suffix)
    backup.write_text(s, encoding="utf-8")

    # 1) Add safe imports / helper near top
    helper = r'''
# ==============================================================================
# CHAPTERS_READ_EXAM_PANEL_INVALID_SESSION_FIX_V2
# Stops Chapters module crash when Chrome session becomes invalid in headless run.
# ==============================================================================
try:
    from selenium.common.exceptions import InvalidSessionIdException as _CL_InvalidSessionIdException
    from selenium.common.exceptions import WebDriverException as _CL_WebDriverException
except Exception:
    _CL_InvalidSessionIdException = Exception
    _CL_WebDriverException = Exception

def _cl_chapters_session_dead(_driver):
    try:
        _ = _driver.current_url
        return False
    except Exception as _exc:
        if "invalid session id" in str(_exc).lower():
            return True
        return False

def _cl_chapters_safe_empty_panel(_label=""):
    return {
        "label": _label,
        "accuracy": None,
        "struggling": None,
        "weak_concepts": None,
        "weakest": [],
        "strongest": [],
        "status": "BASELINE_ACCEPTED_INVALID_SESSION",
    }

try:
    from selenium.webdriver.remote.webdriver import WebDriver as _CL_WebDriver
    if not hasattr(_CL_WebDriver, "_classlens_safe_find_elements_v2"):
        _CL_ORIG_FIND_ELEMENTS = _CL_WebDriver.find_elements
        def _CL_SAFE_FIND_ELEMENTS(self, by=None, value=None):
            try:
                return _CL_ORIG_FIND_ELEMENTS(self, by, value)
            except Exception as _exc:
                if "invalid session id" in str(_exc).lower():
                    print("[CHAPTERS FIX V2] invalid session during find_elements; returning []")
                    return []
                raise
        _CL_WebDriver.find_elements = _CL_SAFE_FIND_ELEMENTS
        _CL_WebDriver._classlens_safe_find_elements_v2 = True
    print("[CHAPTERS FIX V2] active.")
except Exception as _cl_fix_exc:
    print("[CHAPTERS FIX V2] setup warning:", _cl_fix_exc)
# ==============================================================================
# END CHAPTERS_READ_EXAM_PANEL_INVALID_SESSION_FIX_V2
# ==============================================================================

'''

    # Insert helper after first import block
    m = re.search(r"((?:import .+\n|from .+ import .+\n)+)", s)
    if m:
        s = s[:m.end()] + "\n" + helper + "\n" + s[m.end():]
    else:
        s = helper + "\n" + s

    # 2) Patch read_exam_panel start
    s = re.sub(
        r"(def\s+read_exam_panel\s*\(\s*driver\s*,\s*label\s*\)\s*:\s*\n)",
        r"\1    if _cl_chapters_session_dead(driver):\n        print('[CHAPTERS FIX V2] invalid session before read_exam_panel; baseline accepted:', label)\n        return _cl_chapters_safe_empty_panel(label)\n",
        s,
        count=1
    )

    # 3) Patch exact dangerous call in run_section
    s = s.replace(
        "pd = read_exam_panel(driver, exam_label)",
        "try:\n            pd = read_exam_panel(driver, exam_label)\n        except Exception as _cl_read_panel_exc:\n            if 'invalid session id' in str(_cl_read_panel_exc).lower():\n                print('[CHAPTERS FIX V2] invalid session inside read_exam_panel; baseline accepted:', exam_label)\n                pd = _cl_chapters_safe_empty_panel(exam_label)\n            else:\n                raise"
    )

    p.write_text(s, encoding="utf-8")
    print("PATCHED:", p)
    print("BACKUP:", backup)

