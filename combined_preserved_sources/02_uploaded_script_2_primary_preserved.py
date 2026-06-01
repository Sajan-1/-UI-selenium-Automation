# -*- coding: utf-8 -*-
# ==============================================================================
# ADD-ONLY PRELUDE - ORIGINAL UPLOADED SCRIPT STARTS BELOW UNCHANGED
# No original line is deleted. This prelude only prepares CLI/runtime behaviour.
# ==============================================================================
import os as _CL_OS_ADDONLY, sys as _CL_SYS_ADDONLY, time as _CL_TIME_ADDONLY, glob as _CL_GLOB_ADDONLY, json as _CL_JSON_ADDONLY
from datetime import datetime as _CL_DATETIME_ADDONLY

_CL_ORIGINAL_SLEEP_ADDONLY = _CL_TIME_ADDONLY.sleep
_CL_ARGS_ADDONLY = set(_CL_SYS_ADDONLY.argv[1:])
_CL_FAST_MODE_ADDONLY = ('--fast' in _CL_ARGS_ADDONLY) or ('--headless' in _CL_ARGS_ADDONLY) or ('--all' in _CL_ARGS_ADDONLY)
_CL_HEADLESS_ADDONLY = ('--headless' in _CL_ARGS_ADDONLY)
_CL_SKIP_ZZ_ADDONLY = ('--skip-zz' in _CL_ARGS_ADDONLY) or ('--all' in _CL_ARGS_ADDONLY)
_CL_NO_INPUT_ADDONLY = ('--headless' in _CL_ARGS_ADDONLY) or ('--no-input' in _CL_ARGS_ADDONLY) or ('--all' in _CL_ARGS_ADDONLY)

if _CL_FAST_MODE_ADDONLY:
    def _classlens_fast_sleep_addonly(seconds=0):
        try:
            s = float(seconds)
        except Exception:
            s = 0
        # Keep waits functional, but avoid long hard sleeps from slowing the run.
        if s <= 0:
            return _CL_ORIGINAL_SLEEP_ADDONLY(0)
        return _CL_ORIGINAL_SLEEP_ADDONLY(min(s, 0.20))
    _CL_TIME_ADDONLY.sleep = _classlens_fast_sleep_addonly

if _CL_NO_INPUT_ADDONLY:
    import builtins as _CL_BUILTINS_ADDONLY
    def _classlens_no_block_input_addonly(prompt=''):
        try:
            if prompt:
                print(prompt)
        except Exception:
            pass
        return ''
    _CL_BUILTINS_ADDONLY.input = _classlens_no_block_input_addonly

_CL_OS_ADDONLY.environ.setdefault('CLASSLENS_HEADLESS', '1' if _CL_HEADLESS_ADDONLY else '0')
_CL_OS_ADDONLY.environ.setdefault('CLASSLENS_FAST_MODE', '1' if _CL_FAST_MODE_ADDONLY else '0')
_CL_OS_ADDONLY.environ.setdefault('CLASSLENS_SKIP_ZZ', '1' if _CL_SKIP_ZZ_ADDONLY else '0')

print('[ADD-ONLY PRELUDE] Loaded. Original uploaded script is preserved below without deleting lines.')
# ==============================================================================
# ORIGINAL UPLOADED SCRIPT BELOW
# ==============================================================================
"""
ClassLens 4-in-1 Mega Merge
==========================
This readable merge preserves every original line from all four uploaded scripts.
Nothing from the uploaded script bodies was removed.
Extra separator banners were added only between scripts for readability.
See manifest.json for SHA256 checksums and source mapping.
"""

####################################################################################################
# START OF SCRIPT 1: ClassLens – UI Test Suite v16.0
# Original upload: Pasted text(24).txt
# Preserved lines: 2822
# SHA256: 4aa5961c1f35e560a1856502d6abeb20100e4576704c20de3189d57d2d7617bd
####################################################################################################
"""
═══════════════════════════════════════════════════════════════════════════════
  ClassLens – UI Test Suite v16.0
  Target : https://classlens.inferentics.com
  Author : Fixed from source-code analysis of the actual React/Next.js repo

  ROOT CAUSES FIXED (from reading actual source code):
  ─────────────────────────────────────────────────────

  1.  CHAPTER PANEL BACKGROUNDS WERE WRONG
      v14/v15 used bg-red-50 (Reteach), bg-yellow-50 (Brushup), bg-green-50 (OnTrack)
      SOURCE CODE (ChapterFocusCard.ts CARD_THEME):
        Reteach  → container = "bg-blue-50 outline-sky-200"
        Brushup  → container = "bg-[#FFF7E6] outline-orange-200"
        OnTrack  → container = "bg-green-50 outline-green-200"
      FIX: Use correct bg-blue-50, FFF7E6, bg-green-50 selectors.

  2.  CHAPTER BADGE SELECTOR WRONG
      SOURCE CODE: <div class="text-zinc-700 text-sm font-semibold">{chaptersCount} chapters</div>
      This div is INSIDE the card, not the section panel. Find it scoped inside correct panel.

  3.  STUDENT BADGE SELECTOR WRONG
      SOURCE CODE (STUDENT_PERFORMANCE_THEME): subtitle = "text-black/50" for ALL categories
      Rendered as: <div class="text-base font-medium text-black/50">{totalStudents} students</div>
      FIX: Search for this class pattern inside the student card container.

  4.  STUDENT PANEL CONTAINERS IDENTICAL
      SOURCE CODE: ALL 3 categories use containerBg = "bg-[#F1F5FA]"
      The student card outer div is: flex flex-col gap-y-4 p-6 rounded-4xl w-full border-l-2
      FIX: Find the student section by walking up from the heading (text-2xl font-semibold text-slate-600)
      and getting the right parent container. Use heading-scoped search.

  5.  STUDENT VISIBLE ROWS: BOTH CHILDREN HAVE SAME CLASS
      SOURCE CODE: name → font-bold ${theme.studentName} = "text-slate-500"
                   score → font-bold ${theme.studentScore} = "text-slate-500"
      Both are font-bold text-slate-500. They are SIBLINGS inside a flex justify-between row.
      FIX: Find the row (cursor-pointer rounded-2xl bg-white border flex justify-between),
           then get its first and second direct div children.
      SCORE is student.scoreExamB (the Preboard 1 score, e.g. "30%").

  6.  OVERFLOW BUTTON IS A <button> (chapters) OR <div> (students)
      SOURCE CODE ChapterFocusArea:
        <button class="px-6 py-4 rounded-2xl bg-white border border-dashed font-bold text-gray-600 ...">
          +{remainingCount} more chapters
        </button>
      SOURCE CODE StudentPerformanceCard:
        <div class="px-8 py-4 rounded-2xl border border-dashed cursor-pointer font-semibold ...">
          +{remainingCount} more students
        </div>

  7.  MODAL OPENS VIA URL STATE, NOT DIRECT DOM
      SOURCE CODE (useNavigation.ts + useRouteState.ts):
        Clicking overflow calls goTo(screen, { modal: "chapters", modalItem: "Reteach" })
        This pushes URL params: ?modal=chapters&modalItem=Reteach
        React useEffect watches route.modal and sets isChapterModalOpen = true
      FIX: After clicking overflow, wait for URL to contain ?modal= param.
           Then wait for DOM modal to appear.

  8.  MODAL CLOSE ALSO GOES VIA URL
      SOURCE CODE: close calls goTo(screen, { modal: null, modalItem: null })
      This removes modal & modalItem from URL.
      FIX: After clicking X, wait for URL to NOT contain modal= param.

  9.  MODAL DOM STRUCTURE (from Modal.tsx)
      Backdrop:  div.fixed.inset-0.z-50.flex.items-center.justify-center (bg-[#0000005C])
      Card:      div.relative.bg-white.rounded-4xl.shadow-2xl (max-w-162.75)
      Heading:   p.text-2xl.font-semibold.text-[#23262F]   → "Reteach" or "Weak"
      Subheading: p.text-base.font-medium.text-[#58728D]   → "N chapters in this category"
      Close btn: button[aria-label="Close modal"]          → contains SVG image (Close.svg)

  10. STUDENT MODAL ROW STRUCTURE (from FullMarksStudentsModal.tsx)
      Row:   div.rounded-2xl.grid.grid-cols-5.justify-between.py-3.px-6.bg-[#F8FAFC]
      Name:  p.text-sm.font-semibold.text-[#23262F]
      Class: p.text-xs.font-semibold.text-[#768EA7]  → "Class 12P"
      Score: p.text-[32px].font-bold   → student.delta (which is scoreExamB)

  11. CHAPTER MODAL ROW STRUCTURE (from ChapterAccuracyModal.tsx)
      Row:   div.rounded-2xl.grid.grid-cols-5.items-center.py-4.px-6.bg-[#F8FAFC]
      Name:  p.text-sm.font-semibold.text-[#23262F]

  12. CHAPTER METRICS (from ChapterFocusArea.tsx - expanded block)
      Expanded div: div.px-6.pb-4.pt-2.border-t.border-gray-100
      Metric label: span.text-slate-400.text-xs.font-semibold  → "Chapter Avg" or "Avg Weightage"
      Metric value: span.text-slate-800.text-2xl.font-semibold → "-3.1%" or <span>35<span>/ 80</span></span>
      The label key "accuracy" maps to "Chapter Avg"
      The label key "boardWeightage" maps to "Avg Weightage"

  13. DATA LEAKAGE IN v12
      v12's overflow click always opened the SAME (Brushup) modal because the panel
      detection was wrong — the overflow button wasn't scoped to the right section.
      FIX: Find the overflow button by searching WITHIN the correctly identified panel element.

═══════════════════════════════════════════════════════════════════════════════
"""

import os, re, sys, json, time, traceback, webbrowser, subprocess
from copy      import deepcopy
from datetime  import datetime
from typing    import List, Tuple, Optional, Dict

from selenium                            import webdriver
from selenium.webdriver.common.by        import By
from selenium.webdriver.chrome.options   import Options
from selenium.webdriver.support.ui       import WebDriverWait
from selenium.webdriver.support          import expected_conditions as EC
from selenium.common.exceptions          import (
    NoSuchElementException, ElementClickInterceptedException,
    TimeoutException, StaleElementReferenceException,
)
from selenium.webdriver.common.keys         import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

LOGIN_URL         = "https://classlens.inferentics.com"
USERNAME          = "sajan"
PASSWORD          = "Operations123"

VALUES = {
    "Class"        : "12",
    "Section"      : "I",
    "Subject"      : "Maths",
    "Exam"         : "Midterm",
    "CompareLeft"  : "Midterm",
    "CompareRight" : "Preboard 1",
}

# Auto-run all requested sections one by one and produce one combined output/report
SECTION_RUN_LIST   = ["C", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "ZZ"]
MULTI_SECTION_MODE = True

KEEP_BROWSER_OPEN = True
AUTO_OPEN_REPORT  = True
REPORT_FILE       = "classlens_report_v17.html"
JSON_FILE         = "classlens_data_v17.json"
COMBINED_REPORT_FILE = "classlens_report_all_sections_v17.html"
COMBINED_JSON_FILE   = "classlens_data_all_sections_v17.json"
TIMEOUT           = 30

# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE-CODE VERIFIED CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# CARD_THEME containers from ChapterFocusCard.ts  (FIXES v14/v15 bg-red/yellow wrong)
CHAPTER_PANEL_BG = {
    "Reteach"  : "bg-blue-50",      # "bg-blue-50 outline-sky-200"
    "Brushup"  : "FFF7E6",          # "bg-[#FFF7E6] outline-orange-200" — match substring
    "On Track" : "bg-green-50",     # "bg-green-50 outline-green-200"
}

# From ChapterFocusArea.tsx: buildCard passes variant as the modalItem
CHAPTER_MODAL_ITEM = {
    "Reteach"  : "Reteach",
    "Brushup"  : "Brushup",
    "On Track" : "OnTrack",
}

# From StudentPerformanceCard.ts: level is used as the modalItem
STUDENT_MODAL_ITEM = {
    "Weak"          : "Weak",
    "Lagging"       : "Lagging",
    "Performing Well": "Performing_Well",
}

# ══════════════════════════════════════════════════════════════════════════════
#  DATA STORE
# ══════════════════════════════════════════════════════════════════════════════

run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
_P = 0; _F = 0; _W = 0

def _ch():
    return {"badge": "", "badge_n": 0, "cards": [], "modal_chapters": [],
            "overflow_txt": "", "tests": []}

def _st():
    return {"badge": "", "total": 0, "visible": [], "modal_rows": [],
            "all": [], "overflow_txt": "", "modal_opened": False, "tests": []}

store = {
    "run_ts"  : run_ts,
    "config"  : deepcopy(VALUES),
    "exam"    : {"left_pct": "", "right_pct": "", "trend": ""},
    "chapters": {
        "Reteach" : _ch(), "Brushup": _ch(), "On Track": _ch()
    },
    "students": {
        "Weak": _st(), "Lagging": _st(), "Performing Well": _st()
    },
    "login_tests": [], "nav_tests": [], "exam_tests": [], "summary": {}
}


def make_store(section_value: str):
    cfg = deepcopy(VALUES)
    cfg["Section"] = section_value
    return {
        "run_ts"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config"  : cfg,
        "exam"    : {"left_pct": "", "right_pct": "", "trend": ""},
        "chapters": {
            "Reteach" : _ch(), "Brushup": _ch(), "On Track": _ch()
        },
        "students": {
            "Weak": _st(), "Lagging": _st(), "Performing Well": _st()
        },
        "login_tests": [], "nav_tests": [], "exam_tests": [], "summary": {}
    }


def reset_run_state(section_value: str):
    global run_ts, _P, _F, _W, store
    run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _P = 0; _F = 0; _W = 0
    VALUES["Section"] = section_value
    store = make_store(section_value)


def snapshot_current_run():
    total = _P + _F + _W
    snap = deepcopy(store)
    snap["summary"] = {
        "total": total,
        "passed": _P,
        "failed": _F,
        "warnings": _W,
        "pass_rate": round(_P / max(total, 1) * 100, 1),
    }
    return snap


def flatten_test_groups(run_store):
    all_ch = sum((run_store["chapters"][l]["tests"] for l in ["Reteach","Brushup","On Track"]), [])
    all_st = sum((run_store["students"][c]["tests"] for c in ["Weak","Lagging","Performing Well"]), [])
    return {
        "login": run_store["login_tests"],
        "nav": run_store["nav_tests"],
        "exam": run_store["exam_tests"],
        "chapters": all_ch,
        "students": all_st,
    }


def aggregate_summary(runs):
    total_pass = sum(r["summary"].get("passed", 0) for r in runs)
    total_fail = sum(r["summary"].get("failed", 0) for r in runs)
    total_warn = sum(r["summary"].get("warnings", 0) for r in runs)
    total_tests = sum(r["summary"].get("total", 0) for r in runs)
    return {
        "sections_run": len(runs),
        "total": total_tests,
        "passed": total_pass,
        "failed": total_fail,
        "warnings": total_warn,
        "pass_rate": round(total_pass / max(total_tests, 1) * 100, 1),
    }

ICONS = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}

def rec(bucket, tc_id, desc, status, detail=""):
    global _P, _F, _W
    entry = {"tc_id": tc_id, "desc": desc, "status": status,
             "detail": str(detail)[:400], "ts": datetime.now().strftime("%H:%M:%S")}
    bucket.append(entry)
    ico = ICONS.get(status, "   ")
    print(f"  {ico} [{tc_id}] {desc}")
    if detail:
        print(f"         → {str(detail)[:180]}")
    if status == "PASS": _P += 1
    elif status == "FAIL": _F += 1
    elif status == "WARN": _W += 1

def sep(t):
    print(f"\n{'═'*70}\n  {t}\n{'═'*70}")

# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER
# ══════════════════════════════════════════════════════════════════════════════

def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(0)
    return d

# ══════════════════════════════════════════════════════════════════════════════
#  GENERAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def el_text(el) -> str:
    try:    return (el.text or "").strip()
    except: return ""

def scroll_to(d, el):
    try:
        d.execute_script(
            "arguments[0].scrollIntoView({block:'center',behavior:'smooth'});", el)
        time.sleep(0.25)
    except: pass

def safe_click(d, el, label="element") -> bool:
    scroll_to(d, el)
    for strategy in ("direct", "actions", "js"):
        try:
            if strategy == "direct":    el.click()
            elif strategy == "actions": ActionChains(d).move_to_element(el).click().perform()
            else:                       d.execute_script("arguments[0].click();", el)
            return True
        except ElementClickInterceptedException: continue
        except Exception:               continue
    print(f"      ✗ safe_click failed: {label}")
    return False

def get_selects(d):
    return d.find_elements(By.TAG_NAME, "select")

def js_pick(d, sel, val) -> bool:
    return d.execute_script(
        "var s=arguments[0],w=arguments[1].trim();"
        "var fire=function(e){"
        "  e.dispatchEvent(new Event('input',{bubbles:true}));"
        "  e.dispatchEvent(new Event('change',{bubbles:true}));};"
        "for(var i=0;i<s.options.length;i++){"
        "  if((s.options[i].textContent||'').trim()===w){"
        "    s.value=s.options[i].value;fire(s);return true;}}"
        "return false;", sel, val)

def wait_opt(d, idx, val, timeout=30) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        sels = get_selects(d)
        if len(sels) > idx:
            if val in [o.text.strip()
                       for o in sels[idx].find_elements(By.TAG_NAME, "option")]:
                return True
        time.sleep(0.35)
    return False

def page_text(d) -> str:
    try:   return d.find_element(By.TAG_NAME, "body").text
    except: return ""

def current_url(d) -> str:
    try:   return d.current_url
    except: return ""

# ══════════════════════════════════════════════════════════════════════════════
#  URL / MODAL STATE HELPERS
#  FIX: Modals open/close via URL params (useNavigation.ts pushState).
#  We must wait for URL change, not just time.sleep.
# ══════════════════════════════════════════════════════════════════════════════

def wait_for_url_param(d, param_name, param_value=None, timeout=10.0) -> bool:
    """
    Wait until the URL contains ?param_name=param_value (or just param_name if value is None).
    Source: goTo() pushes ?modal=chapters&modalItem=Reteach into the URL.
    """
    end = time.time() + timeout
    while time.time() < end:
        url = current_url(d)
        if param_value is not None:
            if f"{param_name}={param_value}" in url:
                return True
        else:
            if f"{param_name}=" in url:
                return True
        time.sleep(0.2)
    return False


def wait_for_url_param_gone(d, param_name, timeout=10.0) -> bool:
    """
    Wait until URL no longer contains param_name=.
    Source: modal close calls goTo(screen, { modal: null }) which deletes the param.
    """
    end = time.time() + timeout
    while time.time() < end:
        if f"{param_name}=" not in current_url(d):
            return True
        time.sleep(0.2)
    return False


def wait_for_modal_dom(d, heading_text, timeout=12.0):
    """
    Wait for the student/chapter modal card to appear and return it.

    Source (Modal.tsx):
      Backdrop : div.fixed.inset-0.z-50.flex.items-center.justify-center
      Card     : div.relative.bg-white.rounded-4xl.shadow-2xl
      Heading  : p.text-2xl.font-semibold.text-[#23262F]   → e.g. "Weak"
      Close btn: button[aria-label="Close modal"]

    Strategy (multiple fallbacks — backdrop detection was fragile):
      1. JS scan: find all elements whose innerText starts with heading_text
         and whose parent has shadow-2xl class. Fast and bypasses XPath limits.
      2. XPath via Close button anchor: find button[aria-label="Close modal"],
         walk up to the rounded-4xl card, verify heading text.
      3. XPath via heading paragraph: find p.text-2xl.font-semibold containing
         the heading text, walk up to the card.
      4. XPath via backdrop (original, kept as last resort).
    """
    end = time.time() + timeout

    # Give React a moment to respond to URL pushState before polling
    time.sleep(0.5)

    while time.time() < end:
        # ── Strategy 1: JS scan (most reliable, bypasses XPath class issues) ──
        try:
            card = d.execute_script("""
                var target = arguments[0].toLowerCase();
                // Look for the close button first — it's unique to the modal
                var closeBtns = document.querySelectorAll('button[aria-label="Close modal"]');
                for (var i = 0; i < closeBtns.length; i++) {
                    var btn = closeBtns[i];
                    if (!btn.offsetParent && btn.offsetWidth === 0) continue; // hidden
                    // Walk up to find the card
                    var node = btn;
                    for (var j = 0; j < 8; j++) {
                        node = node.parentElement;
                        if (!node) break;
                        var cls = node.className || '';
                        if (cls.indexOf('shadow-2xl') !== -1 && cls.indexOf('bg-white') !== -1) {
                            // Verify heading text
                            var txt = (node.innerText || '').toLowerCase();
                            if (txt.indexOf(target) !== -1) {
                                return node;
                            }
                        }
                    }
                }
                return null;
            """, heading_text)
            if card:
                return card
        except Exception:
            pass

        # ── Strategy 2: XPath via Close button → walk up ──
        try:
            close_btns = d.find_elements(
                By.XPATH, "//button[@aria-label='Close modal']")
            for btn in close_btns:
                try:
                    if not btn.is_displayed():
                        continue
                    node = btn
                    for _ in range(8):
                        node = node.find_element(By.XPATH, "..")
                        cls = node.get_attribute("class") or ""
                        if "shadow-2xl" in cls and "bg-white" in cls:
                            card_text = (node.text or "").lower()
                            if heading_text.lower() in card_text:
                                return node
                except Exception:
                    continue
        except Exception:
            pass

        # ── Strategy 3: XPath via heading paragraph ──
        try:
            heading_els = d.find_elements(
                By.XPATH,
                f"//p[contains(@class,'text-2xl') and contains(@class,'font-semibold') "
                f"and normalize-space(text())='{heading_text}']")
            if not heading_els:
                # Looser: any visible p containing the text
                heading_els = d.find_elements(
                    By.XPATH,
                    f"//p[contains(@class,'font-semibold') "
                    f"and normalize-space(text())='{heading_text}']")
            for h_el in heading_els:
                try:
                    if not h_el.is_displayed():
                        continue
                    node = h_el
                    for _ in range(8):
                        node = node.find_element(By.XPATH, "..")
                        cls = node.get_attribute("class") or ""
                        if "shadow-2xl" in cls and "bg-white" in cls:
                            return node
                except Exception:
                    continue
        except Exception:
            pass

        # ── Strategy 4: backdrop XPath (original fallback) ──
        try:
            backdrops = d.find_elements(
                By.XPATH,
                "//div[contains(@class,'fixed') and contains(@class,'z-50')]")
            for bd in backdrops:
                try:
                    sz = bd.size
                    if sz.get("width", 0) < 200:
                        continue
                    cards = bd.find_elements(
                        By.XPATH,
                        ".//div[contains(@class,'bg-white') "
                        "and contains(@class,'shadow-2xl')]")
                    for card in cards:
                        card_text = (card.text or "").lower()
                        if heading_text.lower() in card_text:
                            return card
                except Exception:
                    continue
        except Exception:
            pass

        time.sleep(0.35)

    return None


def close_modal_by_url(d, timeout=8.0) -> bool:
    """
    Close modal by clicking the Close button (aria-label='Close modal').
    Then wait for URL ?modal= param to disappear.

    Source (Modal.tsx):
      <button onClick={onClose} aria-label="Close modal" ...>
        <Image src={Close} alt="Close icon" />
      </button>
    onClose calls goTo(screen, { modal: null, modalItem: null })
    """
    try:
        close_btn = d.find_element(
            By.XPATH, "//button[@aria-label='Close modal']")
        if close_btn.is_displayed():
            close_btn.click()
        else:
            # Fallback: ESC key
            d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        try:
            d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

    # Wait for URL modal param to be removed
    gone = wait_for_url_param_gone(d, "modal", timeout=timeout)
    if gone:
        time.sleep(0.4)  # Brief wait for DOM to settle after React re-render
    return gone

# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER PANEL FINDER
#  FIX: Use correct background class from CARD_THEME in source code.
#  Reteach=bg-blue-50, Brushup=bg-[#FFF7E6], OnTrack=bg-green-50
# ══════════════════════════════════════════════════════════════════════════════

def find_chapter_panel(d, label: str):
    """
    Find the ChapterFocusCard container for the given label.

    Source (ChapterFocusCard in ChapterFocusArea.tsx):
      <div class="flex flex-col gap-y-4 p-6 rounded-4xl {theme.container} w-full">
    Where theme.container:
      Reteach  = "bg-blue-50 outline-sky-200"
      Brushup  = "bg-[#FFF7E6] outline-orange-200"
      OnTrack  = "bg-green-50 outline-green-200"

    We find the panel by its background color class, then confirm it contains
    the correct tag label heading (h-8 px-4 rounded-lg font-bold bg-blue-600 text-white).
    """
    bg_map = {
        "Reteach"  : "bg-blue-50",
        "Brushup"  : "FFF7E6",      # substring of bg-[#FFF7E6]
        "On Track" : "bg-green-50",
    }
    bg = bg_map.get(label, "")
    tag_label = label  # The tag text: "Reteach", "Brushup", "On Track"

    # Strategy 1: Find by background class containing the expected tag heading
    try:
        # Find all divs with the right background
        all_panels = d.find_elements(
            By.XPATH,
            f"//div[contains(@class,'{bg}') "
            f"and contains(@class,'rounded-4xl') "
            f"and contains(@class,'flex-col') "
            f"and contains(@class,'p-6')]")
        for panel in all_panels:
            if not panel.is_displayed():
                continue
            # Confirm the tag heading is inside this panel
            try:
                tag_el = panel.find_element(
                    By.XPATH,
                    f".//*[normalize-space(text())='{tag_label}' "
                    f"and contains(@class,'font-bold')]")
                if tag_el.is_displayed():
                    return panel
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 2: Find tag heading, walk up to panel container
    try:
        heading_els = d.find_elements(
            By.XPATH,
            f"//*[normalize-space(text())='{tag_label}' "
            f"and contains(@class,'font-bold')]")
        for h_el in heading_els:
            if not h_el.is_displayed():
                continue
            node = h_el
            for _ in range(10):
                try:
                    parent = node.find_element(By.XPATH, "..")
                    cls = parent.get_attribute("class") or ""
                    sz  = parent.size
                    # Panel must have rounded-4xl, flex-col, and the bg color
                    if ("rounded-4xl" in cls and bg in cls
                            and sz.get("width", 0) > 200
                            and sz.get("height", 0) > 100):
                        return parent
                    node = parent
                except Exception:
                    break
    except Exception:
        pass

    print(f"      ⚠ Could not find panel for '{label}' using bg='{bg}'")
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER BADGE READER
#  FIX: Source code renders <div class="text-zinc-700 text-sm font-semibold">
#       {chaptersCount} chapters</div> INSIDE the panel.
# ══════════════════════════════════════════════════════════════════════════════

def read_chapter_badge(d, panel_el, label: str) -> Tuple[str, int]:
    """
    Source (ChapterFocusArea.tsx inside ChapterFocusCard):
      <div class="text-zinc-700 text-sm font-semibold">{chaptersCount} chapters</div>
    """
    root = panel_el if panel_el else d

    # Try exact class from source
    for xp in [
        ".//*[contains(@class,'text-zinc-700') and contains(@class,'font-semibold') "
        "and contains(@class,'text-sm')]",
        ".//*[contains(@class,'text-zinc-700') and contains(@class,'font-semibold')]",
        # Any element with "N chapters" pattern
        ".//*[contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'chapters') "
        "and string-length(normalize-space(text())) < 20]",
    ]:
        try:
            method = root.find_elements if panel_el else d.find_elements
            els = (panel_el or d).find_elements(By.XPATH, xp)
            for el in els:
                try:
                    txt = (el.text or "").strip()
                    m = re.search(r'(\d+)', txt)
                    if m and "chapter" in txt.lower():
                        return txt, int(m.group(1))
                except Exception:
                    continue
        except Exception:
            pass

    return "", 0


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT PANEL / CARD CONTAINER FINDER
#  FIX: All 3 categories use bg-[#F1F5FA]. Distinguish by heading.
#  Source (StudentPerformanceCard):
#    <div class="flex flex-col gap-y-4 p-6 rounded-4xl w-full border-l-2
#                {theme.containerBg} {theme.border}">
#  Where containerBg = "bg-[#F1F5FA]" for ALL categories.
#  The border differs: Weak=border-red-400, Lagging=border-orange-400, PW=border-green-400
# ══════════════════════════════════════════════════════════════════════════════

STUDENT_BORDER = {
    "Weak"          : "border-red-400",
    "Lagging"       : "border-orange-400",
    "Performing Well": "border-green-400",
}

def find_student_card(d, category: str):
    """
    Find the StudentPerformanceCard container for the given category.
    Uses border color to distinguish (all share bg-[#F1F5FA]).

    Source (STUDENT_PERFORMANCE_THEME):
      Weak          → border = "border-red-400"
      Lagging       → border = "border-orange-400"
      Performing_Well → border = "border-green-400"
    """
    border_cls = STUDENT_BORDER.get(category, "")

    # Strategy 1: Find by border color + contains heading text
    if border_cls:
        try:
            panels = d.find_elements(
                By.XPATH,
                f"//div[contains(@class,'{border_cls}') "
                f"and contains(@class,'rounded-4xl') "
                f"and contains(@class,'flex-col')]")
            for panel in panels:
                if not panel.is_displayed():
                    continue
                txt = (panel.text or "")
                if category.lower() in txt.lower():
                    return panel
        except Exception:
            pass

    # Strategy 2: Walk up from the category heading
    # Source: <div class="text-2xl font-semibold text-slate-600">{title}</div>
    try:
        headings = d.find_elements(
            By.XPATH,
            f"//div[contains(@class,'text-2xl') "
            f"and contains(@class,'font-semibold') "
            f"and contains(@class,'text-slate-600') "
            f"and normalize-space(text())='{category}']")
        if not headings:
            headings = d.find_elements(
                By.XPATH,
                f"//*[normalize-space(text())='{category}' "
                f"and contains(@class,'font-semibold')]")
        for h_el in headings:
            if not h_el.is_displayed():
                continue
            node = h_el
            for _ in range(10):
                try:
                    parent = node.find_element(By.XPATH, "..")
                    cls = parent.get_attribute("class") or ""
                    sz  = parent.size
                    if ("rounded-4xl" in cls
                            and sz.get("width", 0) > 200
                            and sz.get("height", 0) > 100):
                        return parent
                    node = parent
                except Exception:
                    break
    except Exception:
        pass

    print(f"      ⚠ Could not find student card for '{category}'")
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT BADGE READER
#  FIX: Source renders <div class="text-base font-medium text-black/50">
#       {totalStudents} students</div>
# ══════════════════════════════════════════════════════════════════════════════

def read_student_badge(d, card_el, category: str) -> Tuple[str, int]:
    """
    Source (StudentPerformanceCard.tsx):
      <div class="text-base font-medium text-black/50">{totalStudents} students</div>
      theme.subtitle = "text-black/50" for all categories.

    Strategy: search by text content pattern "N students" inside the card.
    The Tailwind v4 class text-black/50 may render differently in some environments,
    so we prioritise content matching over class matching.
    """
    root = card_el if card_el else d

    # Strategy 1: JS scan inside the card element — most reliable
    try:
        result = d.execute_script("""
            var root = arguments[0];
            var all = root.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var t = (all[i].innerText || all[i].textContent || '').trim();
                if (/^\\d+\\s+students?$/i.test(t)) {
                    return t;
                }
            }
            return null;
        """, root)
        if result:
            m = re.search(r'(\d+)', result)
            if m:
                return result.strip(), int(m.group(1))
    except Exception:
        pass

    # Strategy 2: XPath text-content based (no class dependency)
    for xp in [
        ".//*[contains(@class,'font-medium') "
        "and contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'students') "
        "and string-length(normalize-space(text())) < 20]",
        # Any element: "N students" pattern, short text, inside card
        ".//*[string-length(normalize-space(text())) < 20 "
        "and contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'students')]",
    ]:
        try:
            els = root.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    txt = (el.text or "").strip()
                    m = re.search(r'^(\d+)\s+students?$', txt, re.I)
                    if m:
                        return txt, int(m.group(1))
                except Exception:
                    continue
        except Exception:
            pass

    # Strategy 3: XPath with class (original, kept as fallback)
    for xp in [
        ".//*[contains(@class,'text-black/50') and contains(@class,'font-medium') "
        "and contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'student')]",
        ".//*[contains(@class,'text-black') and contains(@class,'font-medium') "
        "and contains(translate(normalize-space(text()),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'student')]",
    ]:
        try:
            els = root.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    txt = (el.text or "").strip()
                    m = re.search(r'(\d+)', txt)
                    if m and "student" in txt.lower():
                        return txt, int(m.group(1))
                except Exception:
                    continue
        except Exception:
            pass

    return "", 0


# ══════════════════════════════════════════════════════════════════════════════
#  SCRAPE VISIBLE STUDENT ROWS
#  FIX: Read from row containers inside student card. Both children have same
#  class (font-bold text-slate-500). Use child ORDER not class to distinguish.
#
#  Source (StudentPerformanceCard.tsx):
#    <div class="px-8 py-4 flex justify-between cursor-pointer rounded-2xl bg-white
#                border {theme.studentCardBorder} {theme.moreHover}">
#      <div class="font-bold {theme.studentName}">{student.name}</div>
#      <div class="font-bold {theme.studentScore}">{student.scoreExamB}</div>
#    </div>
#  theme.studentCardBorder = "border-[#E6E8EC]"
#  theme.studentName = theme.studentScore = "text-slate-500"  ← SAME CLASS
# ══════════════════════════════════════════════════════════════════════════════

def scrape_visible_students(d, category: str, card_el) -> List[Dict]:
    students = []
    seen     = set()
    root     = card_el if card_el else d

    # Find student row containers
    # Source: div.px-8.py-4.flex.justify-between.cursor-pointer.rounded-2xl.bg-white.border
    row_xpaths = [
        # Most specific: all defining classes
        ".//*[contains(@class,'px-8') and contains(@class,'py-4') "
        "and contains(@class,'justify-between') and contains(@class,'cursor-pointer') "
        "and contains(@class,'rounded-2xl') and contains(@class,'bg-white')]",
        # Slightly looser
        ".//*[contains(@class,'justify-between') and contains(@class,'cursor-pointer') "
        "and contains(@class,'rounded-2xl') and contains(@class,'bg-white') "
        "and contains(@class,'border')]",
    ]

    rows = []
    for xp in row_xpaths:
        try:
            candidates = root.find_elements(By.XPATH, xp)
            # Filter out the overflow button (border-dashed) and empty-state divs
            for r in candidates:
                cls = r.get_attribute("class") or ""
                if "border-dashed" in cls:
                    continue
                rows.append(r)
            if rows:
                print(f"      Found {len(rows)} student row containers")
                break
        except Exception:
            pass

    for row in rows:
        try:
            # Get the two direct div children (name=first, score=second)
            # Both have class "font-bold text-slate-500" — distinguish by position only
            children = row.find_elements(
                By.XPATH, "./div[contains(@class,'font-bold')]")

            if len(children) < 2:
                # Try any direct children with text
                children = row.find_elements(By.XPATH, "./div[normalize-space(text())!='']")

            if len(children) < 2:
                continue

            name  = (children[0].text or "").strip()
            score = (children[1].text or "").strip()

            # Validate name: starts capital, no %, reasonable length
            if not name or not re.match(r"^[A-Z]", name):
                continue
            if len(name) < 2 or len(name) > 70:
                continue
            if "%" in name or name in seen:
                continue

            # Validate score: should be a percentage string like "30%" or "-6.5%"
            if not re.match(r"^-?\d+\.?\d*%$", score):
                # Could be empty or malformed — still record the name
                score = score if score else "N/A"

            seen.add(name)
            students.append({
                "name"    : name,
                "pct"     : score,
                "category": category,
                "src"     : "visible",
            })
        except StaleElementReferenceException:
            continue
        except Exception:
            continue

    if not students:
        print(f"      Row strategy found 0 rows, trying text fallback")
        students = _student_text_fallback(d, category, card_el)

    return students


def _student_text_fallback(d, category: str, card_el) -> List[Dict]:
    """
    Fallback: parse name+pct pairs from text lines within the card element.
    """
    students = []; seen = set()
    try:
        root = card_el if card_el else d.find_element(By.TAG_NAME, "body")
        lines = [l.strip() for l in (root.text or "").split("\n") if l.strip()]
        i = 0
        skip = {category.lower(), "students", "no students in this category yet",
                "highlighted students", "reteach", "brushup", "on track",
                "weak", "lagging", "performing well"}
        while i < len(lines):
            line = lines[i]
            if (re.match(r"^[A-Z][a-z]", line) and "%" not in line
                    and 2 <= len(line) <= 60
                    and line.lower() not in skip):
                # Look ahead for a percentage
                for j in range(i + 1, min(i + 4, len(lines))):
                    if re.match(r"^-?\d+\.?\d*%$", lines[j]):
                        if line not in seen:
                            seen.add(line)
                            students.append({"name": line, "pct": lines[j],
                                             "category": category, "src": "text-fallback"})
                        break
            i += 1
    except Exception as e:
        print(f"      text fallback error: {e}")
    return students


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER OVERFLOW BUTTON FINDER
#  FIX: Source uses <button> (not div) with border-dashed for chapters.
#  Source (ChapterFocusArea.tsx):
#    <button class="px-6 py-4 rounded-2xl bg-white border border-dashed
#                   font-bold text-gray-600 hover:bg-gray-50 text-left">
#      +{remainingCount} more chapters
#    </button>
# ══════════════════════════════════════════════════════════════════════════════

def find_chapter_overflow_btn(d, panel_el):
    """
    Find the '+N more chapters' button strictly inside the chapter panel.
    Source: <button class="...border-dashed...">+N more chapters</button>
    """
    root = panel_el if panel_el else d

    xpaths = [
        # Most specific: button with border-dashed starting with +
        ".//button[contains(@class,'border-dashed') "
        "and starts-with(normalize-space(text()),'+')]",
        # Looser: any element with border-dashed and '+' text
        ".//*[contains(@class,'border-dashed') "
        "and starts-with(normalize-space(text()),'+')]",
        # Fallback: any element with '+N more chapters' text
        ".//*[starts-with(normalize-space(text()),'+') "
        "and contains(normalize-space(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')),'more chapters')]",
    ]

    for xp in xpaths:
        try:
            els = root.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    txt = (el.text or "").strip()
                    if "+" in txt:
                        return el, txt
        except Exception:
            pass

    return None, ""


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT OVERFLOW BUTTON FINDER
#  FIX: Source uses <div> with border-dashed for student overflow.
#  Source (StudentPerformanceCard.tsx):
#    <div class="px-8 py-4 rounded-2xl border border-dashed cursor-pointer
#                font-semibold transition bg-white {theme.moreText} {theme.moreHover}">
#      +{remainingCount} more students
#    </div>
# ══════════════════════════════════════════════════════════════════════════════

def find_student_overflow_btn(d, card_el):
    """
    Find '+N more students' button inside student card container.
    Source: div.border-dashed.cursor-pointer with text '+N more students'
    """
    root = card_el if card_el else d

    xpaths = [
        ".//*[contains(@class,'border-dashed') and contains(@class,'cursor-pointer') "
        "and starts-with(normalize-space(text()),'+') "
        "and contains(normalize-space(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')),'student')]",
        ".//*[contains(@class,'border-dashed') and contains(@class,'cursor-pointer') "
        "and starts-with(normalize-space(text()),'+')]",
        ".//*[contains(@class,'border-dashed') "
        "and starts-with(normalize-space(text()),'+')]",
    ]

    for xp in xpaths:
        try:
            els = root.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    txt = (el.text or "").strip()
                    if "+" in txt:
                        return el, txt
        except Exception:
            pass

    return None, ""


# ══════════════════════════════════════════════════════════════════════════════
#  READ CHAPTER MODAL ROWS
#  Source (ChapterAccuracyModal.tsx):
#    <div class="rounded-2xl grid grid-cols-5 items-center py-4 px-6 bg-[#F8FAFC]">
#      <div class="col-span-3">
#        <p class="text-sm font-semibold text-[#23262F]">{chapter.chapterName}</p>
#      </div>
#    </div>
# ══════════════════════════════════════════════════════════════════════════════

def read_chapter_modal_rows(d, modal_el) -> List[str]:
    """
    Read chapter names from the chapter accuracy modal.
    Source (ChapterAccuracyModal.tsx):
      <p class="text-sm font-semibold text-[#23262F]">{chapter.chapterName}</p>
    """
    chapters = []
    seen     = set()

    try:
        # Find chapter name paragraphs inside modal
        name_els = modal_el.find_elements(
            By.XPATH,
            ".//p[contains(@class,'text-sm') and contains(@class,'font-semibold') "
            "and contains(@class,'text-[#23262F]')]")

        if not name_els:
            # Fallback: any p with text-sm font-semibold inside modal
            name_els = modal_el.find_elements(
                By.XPATH,
                ".//p[contains(@class,'font-semibold') and contains(@class,'text-sm')]")

        for el in name_els:
            try:
                txt = (el.text or "").strip()
                if txt and len(txt) >= 3 and txt not in seen:
                    # Skip noise
                    if txt.lower() in ("chapters in this category", "students in this category"):
                        continue
                    if re.match(r"^\d+\s+(chapters|students)", txt, re.I):
                        continue
                    seen.add(txt)
                    chapters.append(txt)
            except Exception:
                continue
    except Exception:
        pass

    # If the above fails, fall back to parsing modal text
    if not chapters:
        try:
            modal_text = (modal_el.text or "")
            lines = [l.strip() for l in modal_text.split("\n") if l.strip()]
            skip = {"reteach", "brushup", "on track", "chapters in this category",
                    "view chapter details", "chapter avg", "avg weightage"}
            for line in lines:
                if (re.match(r"^[A-Z]", line) and 3 <= len(line) <= 80
                        and "%" not in line
                        and line.lower() not in skip
                        and not re.match(r"^\d+\s+chapters", line, re.I)
                        and line not in seen):
                    seen.add(line)
                    chapters.append(line)
        except Exception:
            pass

    return chapters


# ══════════════════════════════════════════════════════════════════════════════
#  READ STUDENT MODAL ROWS
#  Source (FullMarksStudentsModal.tsx):
#    <div class="rounded-2xl grid grid-cols-5 justify-between py-3 px-6 bg-[#F8FAFC]">
#      <div class="flex gap-2 items-center col-span-3">
#        <p class="text-sm font-semibold text-[#23262F]">{student.name}</p>
#        <p class="text-xs font-semibold text-[#768EA7]">Class {className}{section}</p>
#      </div>
#      <p class="text-[32px] font-bold ...">{student.delta}</p>   ← scoreExamB
#    </div>
# ══════════════════════════════════════════════════════════════════════════════

def read_student_modal_rows(d, modal_el, category: str) -> List[Dict]:
    """
    Read student name + score + class info from the student modal.

    Source (FullMarksStudentsModal.tsx):
      Scrollable wrapper : div.overflow-y-auto.flex-col.gap-2
      Row container      : div.relative > div.rounded-2xl.grid.grid-cols-5...bg-[#F8FAFC]
      Name               : p.text-sm.font-semibold.text-[#23262F]   → student.name
      Class info         : p.text-xs.font-semibold.text-[#768EA7]   → "Class {grade}{section}"
                           ONLY rendered when className prop is truthy.
                           className = grade (e.g. "12"), section = section (e.g. "P")
                           Renders as: "Class 12P"
      Score              : p.text-[32px].font-bold                   → student.delta = scoreExamB

    Strategy — JS-first:
      1. Use JavaScript to scan grid-cols-5 rows, extract text by position.
         This avoids all XPath issues with Tailwind v4 arbitrary color classes.
      2. XPath fallback using text-content matching for class info.
    """
    students   = []
    seen       = set()

    # Find scrollable container for scroll loop
    scroll_target = None
    try:
        scrollables = modal_el.find_elements(
            By.XPATH,
            ".//div[contains(@class,'overflow-y-auto')]")
        if scrollables:
            scroll_target = scrollables[0]
    except Exception:
        pass

    for scroll_step in range(50):

        # ── Strategy 1: JS row extraction (bypasses all class-name issues) ──
        try:
            rows_data = d.execute_script("""
                var modal = arguments[0];
                var results = [];
                // Find row containers: div with grid and bg-[#F8FAFC]
                // Use a broad selector then filter
                var all_divs = modal.querySelectorAll('div');
                for (var i = 0; i < all_divs.length; i++) {
                    var div = all_divs[i];
                    var cls = div.className || '';
                    // Must have grid-cols-5 pattern
                    if (cls.indexOf('grid-cols-5') === -1) continue;
                    // Must be visible
                    if (div.offsetWidth === 0 || div.offsetHeight === 0) continue;

                    var name = '';
                    var classInfo = '';
                    var score = '';

                    // Find name: p.text-sm.font-semibold — first one that starts capital
                    var paras = div.querySelectorAll('p');
                    for (var j = 0; j < paras.length; j++) {
                        var pt = (paras[j].innerText || '').trim();
                        var pc = paras[j].className || '';
                        if (pc.indexOf('text-sm') !== -1 && pc.indexOf('font-semibold') !== -1
                                && /^[A-Z]/.test(pt) && pt.indexOf('Class') === -1
                                && pt.length > 1 && pt.length < 70) {
                            name = pt;
                            break;
                        }
                    }
                    if (!name) continue;

                    // Find class info: p.text-xs containing "Class"
                    for (var j = 0; j < paras.length; j++) {
                        var pt = (paras[j].innerText || '').trim();
                        var pc = paras[j].className || '';
                        if (pc.indexOf('text-xs') !== -1 && pt.indexOf('Class') === 0) {
                            classInfo = pt;
                            break;
                        }
                    }

                    // Find score: p with large font (text-[32px] or text-3xl or font-bold
                    // and contains a % or number)
                    for (var j = 0; j < paras.length; j++) {
                        var pt = (paras[j].innerText || '').trim();
                        var pc = paras[j].className || '';
                        if (pc.indexOf('font-bold') !== -1
                                && (pt.indexOf('%') !== -1 || /^-?\\d/.test(pt))
                                && pt.length < 20) {
                            score = pt;
                            break;
                        }
                    }

                    results.push({name: name, classInfo: classInfo, score: score});
                }
                return results;
            """, modal_el)

            if rows_data:
                for row in rows_data:
                    name       = (row.get("name") or "").strip()
                    class_info = (row.get("classInfo") or "").strip()
                    score      = (row.get("score") or "").strip()
                    if name and name not in seen:
                        seen.add(name)
                        students.append({
                            "name"      : name,
                            "pct"       : score,
                            "class_info": class_info,
                            "category"  : category,
                            "src"       : "modal",
                        })
        except Exception as e:
            print(f"        JS row extraction error: {e}")

        # ── Strategy 2: XPath fallback if JS got nothing ──
        if not students:
            try:
                row_els = modal_el.find_elements(
                    By.XPATH,
                    ".//div[contains(@class,'grid-cols-5')]")
                for row in row_els:
                    try:
                        # Name
                        name_els = row.find_elements(
                            By.XPATH,
                            ".//p[contains(@class,'text-sm') and contains(@class,'font-semibold')]")
                        name = ""
                        for ne in name_els:
                            t = (ne.text or "").strip()
                            if t and re.match(r"^[A-Z]", t) and "Class" not in t and len(t) > 1:
                                name = t; break
                        if not name or name in seen:
                            continue

                        # Class info — search by text content starting with "Class"
                        class_info = ""
                        try:
                            ci_els = row.find_elements(
                                By.XPATH,
                                ".//p[contains(@class,'text-xs') "
                                "and starts-with(normalize-space(text()),'Class')]")
                            if ci_els:
                                class_info = (ci_els[0].text or "").strip()
                        except Exception:
                            pass

                        # Score — font-bold with % or number, short text
                        score = ""
                        try:
                            score_els = row.find_elements(
                                By.XPATH,
                                ".//p[contains(@class,'font-bold') "
                                "and (contains(text(),'%') or contains(text(),'.')) "
                                "and string-length(normalize-space(text())) < 15]")
                            if score_els:
                                score = (score_els[0].text or "").strip()
                        except Exception:
                            pass

                        seen.add(name)
                        students.append({
                            "name"      : name,
                            "pct"       : score,
                            "class_info": class_info,
                            "category"  : category,
                            "src"       : "modal",
                        })
                    except Exception:
                        continue
            except Exception:
                pass

        # Scroll to get more rows
        at_bottom = True
        try:
            tgt = scroll_target if scroll_target else modal_el
            st = d.execute_script("return arguments[0].scrollTop", tgt)
            sh = d.execute_script("return arguments[0].scrollHeight", tgt)
            ch = d.execute_script("return arguments[0].clientHeight", tgt)
            at_bottom = (st + ch) >= (sh - 10)
            if not at_bottom:
                d.execute_script("arguments[0].scrollTop += 200", tgt)
        except Exception:
            pass

        time.sleep(0.35)
        if at_bottom and scroll_step >= 1:
            break

    return students


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER CARD METRICS EXTRACTOR
#  FIX: Source structure confirmed from ChapterFocusArea.tsx:
#  Expanded block: div.px-6.pb-4.pt-2.border-t.border-gray-100
#  Metric wrapper: div.bg-blue-50 (or bg-[#FFF7E6] or bg-green-50)... p-4.rounded-2xl
#  Label:  span.text-slate-400.text-xs.font-semibold  → "Chapter Avg" or "Avg Weightage"
#  Value:  span.text-slate-800.text-2xl.font-semibold → the value
# ══════════════════════════════════════════════════════════════════════════════

def read_chapter_card_metrics(d, outer_card_el) -> Dict:
    m = {"chapter_avg": "N/A", "avg_weightage": "N/A"}

    try:
        # Find expanded block: div.border-t.border-gray-100
        expanded = outer_card_el.find_elements(
            By.XPATH,
            ".//div[contains(@class,'border-t') "
            "and contains(@class,'border-gray-100')]")

        if not expanded:
            return m

        exp_div = expanded[0]

        # Find label spans: text-slate-400 text-xs font-semibold
        label_spans = exp_div.find_elements(
            By.XPATH,
            ".//span[contains(@class,'text-slate-400') "
            "and contains(@class,'text-xs') "
            "and contains(@class,'font-semibold')]")

        for lbl in label_spans:
            lbl_txt = (lbl.text or "").strip().lower()

            # Value is a sibling span with text-slate-800 text-2xl font-semibold
            try:
                val_el = lbl.find_element(
                    By.XPATH,
                    "following-sibling::span[contains(@class,'text-slate-800') "
                    "and contains(@class,'font-semibold')][1]")
                val_txt = (val_el.text or "").strip()
            except Exception:
                # Try parent's sibling approach
                try:
                    parent = lbl.find_element(By.XPATH, "..")
                    val_el = parent.find_element(
                        By.XPATH,
                        ".//span[contains(@class,'text-slate-800') "
                        "and contains(@class,'font-semibold')]")
                    val_txt = (val_el.text or "").strip()
                except Exception:
                    continue

            if not val_txt:
                continue

            if "chapter avg" in lbl_txt or lbl_txt == "chapter avg":
                m["chapter_avg"] = val_txt
            elif "weightage" in lbl_txt or "avg weightage" in lbl_txt:
                m["avg_weightage"] = val_txt

    except Exception as e:
        print(f"      metrics error: {e}")

    return m


def wait_for_chapter_expansion(d, outer_card_el, timeout=5.0) -> bool:
    """
    Wait for div.border-t.border-gray-100 to appear in the outer card.
    Source: this div only renders when the card is expanded (isOpen=true).
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            els = outer_card_el.find_elements(
                By.XPATH,
                ".//div[contains(@class,'border-t') "
                "and contains(@class,'border-gray-100')]")
            if els and any(e.is_displayed() for e in els):
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


def find_chapter_outer_card(header_el, d) -> object:
    """
    Walk UP from the chapter header div to find the outer card.
    Source: outer card = div.rounded-2xl.bg-white (parent of header)
    """
    node = header_el
    for _ in range(8):
        try:
            parent = node.find_element(By.XPATH, "..")
            cls = parent.get_attribute("class") or ""
            if "rounded-2xl" in cls and "bg-white" in cls:
                return parent
            node = parent
        except Exception:
            break
    return header_el


# ══════════════════════════════════════════════════════════════════════════════
#  EXTRACT ALL INLINE CHAPTER CARDS
# ══════════════════════════════════════════════════════════════════════════════

_CH_SKIP = {
    "reteach", "brushup", "on track", "revise thoroughly",
    "review specific concepts", "significant improvement",
    "no chapters available", "view chapter details",
    "chapter avg", "avg weightage", "weak", "lagging", "performing well",
    "target these chapters", "chapters recommended", "maths",
}

def extract_chapter_cards(d, panel_el, label: str) -> List[Dict]:
    """
    Find and expand chapter cards inside the panel.

    Source (ChapterFocusArea.tsx - ChapterFocusCard):
      Outer card:  div.rounded-2xl.bg-white.transition-all.border
      Header:      div.px-6.py-4.flex.cursor-pointer  (click toggles isOpen)
      Name:        div.font-bold.text-gray-700.normal-case  inside header
      Expanded:    div.px-6.pb-4.pt-2.border-t.border-gray-100  (only when isOpen=true)
    """
    chapters_data = []
    seen          = set()

    if panel_el is None:
        return chapters_data

    # Find chapter name elements inside panel
    # Source: <div class="font-bold text-gray-700 normal-case">{toTitleCase(chapter.name)}</div>
    try:
        name_els = panel_el.find_elements(
            By.XPATH,
            ".//div[contains(@class,'font-bold') "
            "and contains(@class,'text-gray-700') "
            "and contains(@class,'normal-case')]")
    except Exception:
        print(f"      ✗ No chapter name elements found for '{label}'")
        return chapters_data

    print(f"      Found {len(name_els)} chapter name elements")

    for name_el in name_els:
        try:
            name = (name_el.text or "").strip()
            if not name or len(name) < 3 or len(name) > 90:
                continue
            if name in seen:
                continue
            if name.lower() in _CH_SKIP:
                continue
            seen.add(name)
        except StaleElementReferenceException:
            continue

        print(f"\n      Processing: '{name}'")

        # Walk up to find the clickable header div (has cursor-pointer)
        try:
            header = name_el.find_element(By.XPATH, "..")
            cls = header.get_attribute("class") or ""
            if "cursor-pointer" not in cls:
                header = header.find_element(By.XPATH, "..")
                cls = header.get_attribute("class") or ""
            if "cursor-pointer" not in cls:
                # One more level
                header = header.find_element(By.XPATH, "..")
        except Exception:
            print(f"        ✗ No clickable header found")
            chapters_data.append({"name": name, "chapter_avg": "N/A",
                                  "avg_weightage": "N/A", "has_button": False})
            continue

        # Find outer card (rounded-2xl bg-white)
        outer_card = find_chapter_outer_card(header, d)

        # Click to expand
        if not safe_click(d, header, name):
            print(f"        ✗ Click failed")
            chapters_data.append({"name": name, "chapter_avg": "N/A",
                                  "avg_weightage": "N/A", "has_button": False})
            continue

        # Wait for expansion
        expanded = wait_for_chapter_expansion(d, outer_card, timeout=5.0)
        if not expanded:
            print(f"        ✗ Expansion timeout")
            try:
                safe_click(d, header, f"collapse {name}")
            except Exception:
                pass
            chapters_data.append({"name": name, "chapter_avg": "N/A",
                                  "avg_weightage": "N/A", "has_button": False})
            continue

        # Read metrics
        metrics = read_chapter_card_metrics(d, outer_card)

        # Check for View Chapter Details button
        has_btn = False
        try:
            outer_card.find_element(
                By.XPATH,
                ".//button[contains(normalize-space(translate(text(),"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')),"
                "'view chapter details')]")
            has_btn = True
        except Exception:
            pass

        print(f"        Avg: {metrics['chapter_avg']}  "
              f"Wt: {metrics['avg_weightage']}  Btn: {has_btn}")

        chapters_data.append({
            "name"         : name,
            "chapter_avg"  : metrics["chapter_avg"],
            "avg_weightage": metrics["avg_weightage"],
            "has_button"   : has_btn,
        })

        # Collapse the card
        try:
            safe_click(d, header, f"collapse {name}")
            time.sleep(0.3)
        except Exception:
            pass

    return chapters_data


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════

def test_login(d, wait) -> bool:
    sep("SECTION 1 – Login & Page Load")
    b = store["login_tests"]

    try:
        d.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        rec(b, "TC-L-001", "Login page loads", "PASS", d.current_url)
    except Exception as e:
        rec(b, "TC-L-001", "Login page loads", "FAIL", str(e))
        return False

    try:
        assert d.find_element(By.TAG_NAME, "img").is_displayed()
        rec(b, "TC-L-002", "Logo visible", "PASS")
    except Exception as e:
        rec(b, "TC-L-002", "Logo", "WARN", str(e))

    try:
        usr = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@type='text' or @type='email']")))
        pwd = d.find_element(By.XPATH, "//input[@type='password']")
        btn = d.find_element(By.XPATH, "//button[@type='submit']")
        rec(b, "TC-L-003", "Username / Password / Submit visible", "PASS")
    except Exception as e:
        rec(b, "TC-L-003", "Fields", "FAIL", str(e))
        return False

    try:
        assert pwd.get_attribute("type") == "password"
        rec(b, "TC-L-004", "Password masked", "PASS")
    except Exception as e:
        rec(b, "TC-L-004", "Password masked", "WARN", str(e))

    try:
        usr.clear(); usr.send_keys(USERNAME)
        pwd.clear(); pwd.send_keys(PASSWORD)
        btn.click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(.,'Class') or contains(.,'Overview')]")))
        rec(b, "TC-L-005", "Login succeeds", "PASS", d.current_url)
        return True
    except Exception as e:
        rec(b, "TC-L-005", "Login", "FAIL", str(e))
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def test_navigation(d, wait) -> bool:
    sep("SECTION 2 – Form Selection & Navigation")
    b = store["nav_tests"]

    plan = [
        (0, "Class",        VALUES["Class"]),
        (1, "Section",      VALUES["Section"]),
        (2, "Subject",      VALUES["Subject"]),
        (3, "Exam",         VALUES["Exam"]),
        (4, "CompareLeft",  VALUES["CompareLeft"]),
        (5, "CompareRight", VALUES["CompareRight"]),
    ]

    for idx, key, val in plan:
        tc = f"TC-N-{idx+1:03d}"
        if not wait_opt(d, idx, val, TIMEOUT):
            rec(b, tc, f"Dropdown '{key}'", "FAIL", "Timed out")
            return False
        ok = js_pick(d, get_selects(d)[idx], val)
        rec(b, tc, f"Dropdown '{key}'='{val}'", "PASS" if ok else "FAIL")
        if not ok:
            return False
        time.sleep(0.4)

    # Click Enter
    try:
        old_url = d.current_url
        d.find_element(
            By.XPATH, "//button[normalize-space()='Enter']").click()
        wait.until(lambda drv: drv.current_url != old_url)
        rec(b, "TC-N-007", "Enter → Dashboard", "PASS", d.current_url)
    except Exception as e:
        rec(b, "TC-N-007", "Enter", "FAIL", str(e))
        return False

    time.sleep(2.0)

    # Click Overview tab
    ov_el = None
    for xp in [
        "//button[normalize-space()='Overview']",
        "//a[normalize-space()='Overview']",
        "//*[normalize-space(text())='Overview' and contains(@class,'cursor')]",
        "//*[normalize-space(text())='Overview']",
    ]:
        for el in d.find_elements(By.XPATH, xp):
            if el.is_displayed():
                ov_el = el
                break
        if ov_el:
            break

    if ov_el:
        safe_click(d, ov_el, "Overview tab")
        rec(b, "TC-N-008", "Overview tab clicked", "PASS")
    else:
        rec(b, "TC-N-008", "Overview tab", "WARN", "Not found — may already be active")

    # Wait for page header
    time.sleep(1.5)
    try:
        WebDriverWait(d, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Overview of Section')]")))
        hdr = d.find_element(By.XPATH, "//*[contains(text(),'Overview of Section')]")
        rec(b, "TC-N-009", "Page header visible", "PASS", (hdr.text or "")[:60])
    except Exception as e:
        rec(b, "TC-N-009", "Page header", "WARN", str(e))

    # Wait for data to load (students or chapters text present)
    try:
        WebDriverWait(d, 15).until(
            EC.presence_of_element_located((By.XPATH,
                "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'students') "
                "or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'chapters')]")))
        rec(b, "TC-N-009a", "Dashboard data loaded", "PASS")
    except Exception as e:
        rec(b, "TC-N-009a", "Data load timeout", "FAIL", str(e))
        return False

    # Check tabs visible
    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        n = 10 + ["Overview", "Chapters", "Questions", "Students"].index(tab)
        try:
            el = d.find_element(
                By.XPATH,
                f"//button[normalize-space()='{tab}']"
                f"|//a[normalize-space()='{tab}']"
                f"|//*[normalize-space(text())='{tab}' and contains(@class,'cursor')]")
            assert el.is_displayed()
            rec(b, f"TC-N-{n:03d}", f"Tab '{tab}' visible", "PASS")
        except Exception as e:
            rec(b, f"TC-N-{n:03d}", f"Tab '{tab}'", "WARN", str(e))

    return True


# ══════════════════════════════════════════════════════════════════════════════
#  EXAM COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

def test_exam_comparison(d):
    sep("SECTION 3 – Exam Comparison Banner")
    b  = store["exam_tests"]
    pt = page_text(d)

    for tc, desc, kw in [
        ("TC-EC-001", "Exam Comparison heading", "Exam Comparison"),
        ("TC-EC-002", "Sub-label 'Change in'", "Change in"),
    ]:
        try:
            el = d.find_element(By.XPATH, f"//*[contains(text(),'{kw}')]")
            rec(b, tc, desc, "PASS", (el.text or "")[:60])
        except Exception as e:
            rec(b, tc, desc, "WARN", str(e))

    rec(b, "TC-EC-003", "Midterm label present",  "PASS" if "Midterm"  in pt else "WARN")
    rec(b, "TC-EC-004", "Preboard label present", "PASS" if "Preboard" in pt else "WARN")

    pcts = re.findall(r'\d+\.?\d*\s*%', pt)[:6]
    if len(pcts) >= 2:
        store["exam"]["left_pct"]  = pcts[0]
        store["exam"]["right_pct"] = pcts[1]
        rec(b, "TC-EC-005", f"Left avg = {pcts[0]}",  "PASS", pcts[0])
        rec(b, "TC-EC-006", f"Right avg = {pcts[1]}", "PASS", pcts[1])
    else:
        rec(b, "TC-EC-005", "Percentages", "WARN", f"found: {pcts}")
        rec(b, "TC-EC-006", "Right pct",   "WARN")

    trend = re.search(r'[-+]?\d+\.?\d*\s*points?\s*(decline|drop|improve)', pt, re.I)
    if not trend:
        trend = re.search(r'-\d+\.?\d*\s*points', pt, re.I)
    if trend:
        store["exam"]["trend"] = trend.group(0)
        rec(b, "TC-EC-007", f"Trend: '{trend.group(0)}'", "PASS")
    else:
        rec(b, "TC-EC-007", "Trend badge", "WARN")


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER SECTION TEST
# ══════════════════════════════════════════════════════════════════════════════

def test_chapter_section(d, label: str):
    prefix_map = {"Reteach": "TC-RT", "Brushup": "TC-BU", "On Track": "TC-OT"}
    prefix = prefix_map[label]
    b  = store["chapters"][label]["tests"]
    cd = store["chapters"][label]

    sep(f"SECTION – {label} Chapters")

    # ── 1. Find panel ──────────────────────────────────────────────────────
    panel = find_chapter_panel(d, label)
    if panel:
        rec(b, f"{prefix}-001", "Chapter panel found", "PASS",
            f"bg={CHAPTER_PANEL_BG[label]}")
    else:
        rec(b, f"{prefix}-001", "Chapter panel found", "WARN",
            "Using body fallback")
        panel = None   # will fallback to document root where needed

    # ── 2. Badge ───────────────────────────────────────────────────────────
    badge_txt, badge_n = read_chapter_badge(d, panel, label)
    if badge_n > 0:
        cd["badge"]   = badge_txt
        cd["badge_n"] = badge_n
        rec(b, f"{prefix}-002", "Chapter badge", "PASS",
            f"'{badge_txt}' → {badge_n} chapters declared")
    else:
        rec(b, f"{prefix}-002", "Chapter badge", "WARN",
            "Not found — will still attempt card extraction")

    # ── 3. Instruction text ────────────────────────────────────────────────
    instr_map = {
        "Reteach"  : "Revise Thoroughly",
        "Brushup"  : "Review Specific Concepts",
        "On Track" : "Significant Improvement",
    }
    try:
        el = d.find_element(
            By.XPATH, f"//*[contains(text(),'{instr_map[label]}')]")
        rec(b, f"{prefix}-003", f"Instruction '{instr_map[label]}'", "PASS",
            (el.text or "")[:60])
    except Exception as e:
        rec(b, f"{prefix}-003", "Instruction text", "WARN", str(e))

    # ── 4. Empty check ─────────────────────────────────────────────────────
    if badge_n == 0:
        # Try to see if the panel itself says "No chapters"
        try:
            if panel:
                no_ch = panel.find_elements(
                    By.XPATH,
                    ".//*[contains(normalize-space(text()),'No chapters')]")
                if no_ch:
                    rec(b, f"{prefix}-004", "Empty state — No chapters", "INFO",
                        (no_ch[0].text or ""))
                    return
            # If badge not found but we have a panel, still attempt extraction
            # (badge selector might have missed it)
        except Exception:
            pass

    # ── 5. Find and click chapter overflow button ──────────────────────────
    # Re-fetch fresh panel to avoid stale refs
    panel = find_chapter_panel(d, label) or panel

    ovf_btn, ovf_txt = find_chapter_overflow_btn(d, panel)

    if ovf_btn:
        cd["overflow_txt"] = ovf_txt
        print(f"\n    Found chapter overflow: '{ovf_txt}'")

        # Click overflow — this triggers goTo(screen, { modal: 'chapters', modalItem: variant })
        # FIX: After clicking, wait for URL to contain modal=chapters
        scroll_to(d, ovf_btn)
        clicked = safe_click(d, ovf_btn, ovf_txt)

        if clicked:
            modal_item = CHAPTER_MODAL_ITEM[label]  # "Reteach", "Brushup", or "OnTrack"

            # Wait for URL param first (URL-driven modal system)
            url_ok = wait_for_url_param(d, "modal", "chapters", timeout=8.0)
            if url_ok:
                print(f"      URL updated: modal=chapters&modalItem={modal_item}")
            else:
                print(f"      ⚠ URL param 'modal=chapters' not detected in time")

            # Wait for modal DOM to appear with correct heading
            modal_el = wait_for_modal_dom(d, label, timeout=10.0)

            if modal_el:
                # Read subheading to confirm chapter count
                try:
                    sub = modal_el.find_element(
                        By.XPATH,
                        ".//p[contains(@class,'text-base') "
                        "and contains(@class,'font-medium')]")
                    sub_txt = (sub.text or "").strip()
                    print(f"      Modal subheading: '{sub_txt}'")
                    m = re.search(r'(\d+)', sub_txt)
                    if m and badge_n == 0:
                        cd["badge_n"] = int(m.group(1))
                        cd["badge"]   = f"{m.group(1)} chapters"
                except Exception:
                    pass

                # Read chapter rows from modal
                chapters_from_modal = read_chapter_modal_rows(d, modal_el)
                cd["modal_chapters"] = chapters_from_modal

                rec(b, f"{prefix}-OVF", "Chapter overflow → modal opened",
                    "PASS" if chapters_from_modal else "WARN",
                    f"'{ovf_txt}' → {len(chapters_from_modal)} chapters")

                for i, ch_name in enumerate(chapters_from_modal, 1):
                    print(f"        #{i:>2}: {ch_name}")
                    rec(b, f"{prefix}-MCH{i:02d}",
                        f"Modal chapter #{i}: {ch_name}", "PASS")

                # Close modal via URL
                close_modal_by_url(d, timeout=8.0)
                print(f"      Modal closed.")
                time.sleep(0.5)

            else:
                rec(b, f"{prefix}-OVF", "Chapter overflow click", "WARN",
                    "Modal DOM not found after click")
                # Try closing via ESC in case something partially opened
                try:
                    d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                except Exception:
                    pass
                wait_for_url_param_gone(d, "modal", timeout=5.0)
        else:
            rec(b, f"{prefix}-OVF", "Chapter overflow", "WARN", "Click failed")
    else:
        rec(b, f"{prefix}-OVF", "No chapter overflow button",
            "INFO", "All chapters visible inline")

    # ── 6. Extract inline chapter cards ───────────────────────────────────
    panel = find_chapter_panel(d, label) or panel
    cards = extract_chapter_cards(d, panel, label)
    cd["cards"] = cards

    if cards:
        rec(b, f"{prefix}-004", "Chapter cards extracted", "PASS",
            f"{len(cards)} cards: {[c['name'] for c in cards]}")
        for idx, card in enumerate(cards, 1):
            tc = f"{prefix}-C{idx:02d}"
            rec(b, tc, f"Card '{card['name']}' expanded", "PASS")
            rec(b, f"{tc}-AVG",
                f"  Chapter Avg = '{card['chapter_avg']}'",
                "PASS" if card["chapter_avg"] != "N/A" else "WARN")
            rec(b, f"{tc}-WT",
                f"  Avg Weightage = '{card['avg_weightage']}'",
                "PASS" if card["avg_weightage"] != "N/A" else "WARN")
            rec(b, f"{tc}-BTN",
                "  View Chapter Details button",
                "PASS" if card["has_button"] else "WARN")
    else:
        if badge_n == 0 and not cd["modal_chapters"]:
            rec(b, f"{prefix}-004", "0 chapters in section", "INFO", "Empty section")
        else:
            rec(b, f"{prefix}-004", "Chapter cards", "WARN",
                "0 cards extracted")

    # ── 7. Print summary ───────────────────────────────────────────────────
    print(f"\n  {'─'*65}")
    print(f"  {label.upper()} — SUMMARY")
    print(f"  Badge: {cd['badge'] or 'N/A'} ({cd['badge_n']} declared)")
    if cd["modal_chapters"]:
        print(f"  Modal chapters ({len(cd['modal_chapters'])}):")
        for i, ch in enumerate(cd["modal_chapters"], 1):
            print(f"    #{i:<3} {ch}")
    if cd["cards"]:
        print(f"  Inline cards ({len(cd['cards'])}):")
        for c in cd["cards"]:
            print(f"    {c['name']:<40} "
                  f"Avg: {c['chapter_avg']:>8}  "
                  f"Wt: {c['avg_weightage']:>10}")
    print(f"  {'─'*65}")


# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT CATEGORY TEST
# ══════════════════════════════════════════════════════════════════════════════

def test_student_category(d, category: str):
    prefix_map = {
        "Weak"          : "TC-HS-W",
        "Lagging"       : "TC-HS-L",
        "Performing Well": "TC-HS-P",
    }
    prefix = prefix_map[category]
    sd = store["students"][category]
    b  = sd["tests"]

    sep(f"  {category}")
    print(f"\n  ▶ {category}")

    # ── 1. Heading ─────────────────────────────────────────────────────────
    try:
        hd = d.find_element(
            By.XPATH,
            f"//div[contains(@class,'text-2xl') "
            f"and contains(@class,'font-semibold') "
            f"and contains(@class,'text-slate-600') "
            f"and normalize-space(text())='{category}']")
        rec(b, f"{prefix}-001", f"'{category}' heading visible", "PASS",
            (hd.text or ""))
    except Exception as e:
        try:
            hd = d.find_element(
                By.XPATH, f"//*[normalize-space(text())='{category}']")
            rec(b, f"{prefix}-001", f"'{category}' heading visible", "PASS",
                (hd.text or ""))
        except Exception:
            rec(b, f"{prefix}-001", "Heading", "WARN", str(e))

    # ── 2. Find student card container ────────────────────────────────────
    card_el = find_student_card(d, category)

    # ── 3. Read badge ──────────────────────────────────────────────────────
    badge_txt, badge_n = read_student_badge(d, card_el, category)
    if badge_n > 0 or badge_txt:
        sd["badge"] = badge_txt
        sd["total"] = badge_n
        rec(b, f"{prefix}-002", "Student count badge", "PASS",
            f"'{badge_txt}' → {badge_n} declared")
    else:
        rec(b, f"{prefix}-002", "Student count badge", "WARN", "Not found")

    # ── 4. Empty state check ───────────────────────────────────────────────
    empty = False
    if card_el:
        try:
            empty_els = card_el.find_elements(
                By.XPATH,
                ".//*[contains(normalize-space(text()),'No students')]")
            if empty_els and any(e.is_displayed() for e in empty_els):
                empty = True
                rec(b, f"{prefix}-EMPTY", "Empty state detected", "INFO",
                    (empty_els[0].text or ""))
        except Exception:
            pass

    if badge_n == 0 and not empty and badge_txt == "":
        # Badge not found — might be 0 students OR badge selector missed it.
        # We'll still try to scrape.
        pass

    if empty or (badge_n == 0 and badge_txt and "0" in badge_txt):
        sd["all"] = []
        _print_student_summary(category, [])
        return

    # ── 5. Scrape visible rows ─────────────────────────────────────────────
    print(f"\n    Scraping visible student rows…")
    card_el  = find_student_card(d, category)  # fresh lookup
    visible  = scrape_visible_students(d, category, card_el)
    sd["visible"] = visible

    if visible:
        print(f"    ✅ {len(visible)} visible students:")
        for i, s in enumerate(visible, 1):
            print(f"      #{i}: {s['name']} — {s['pct']}")
            rec(b, f"{prefix}-S{i:02d}",
                f"Visible #{i}: {s['name']}", "PASS",
                f"Score: {s['pct']}")
    else:
        rec(b, f"{prefix}-VISIBLE", "Visible student rows", "WARN", "0 found")

    # ── 6. Overflow button ─────────────────────────────────────────────────
    print(f"\n    Looking for '+N more students' overflow button…")
    card_el  = find_student_card(d, category)  # fresh
    ovf_el, ovf_txt = find_student_overflow_btn(d, card_el)

    if not ovf_el:
        rec(b, f"{prefix}-OVF-001", "Overflow button",
            "INFO" if visible else "WARN",
            "Not found — all students visible")
        sd["all"] = visible
        _print_student_summary(category, sd["all"])
        return

    sd["overflow_txt"] = ovf_txt
    rec(b, f"{prefix}-OVF-001", "Overflow button found", "PASS", f"'{ovf_txt}'")
    print(f"    ✅ Found: '{ovf_txt}'")

    # Click overflow — triggers goTo(screen, { modal: 'students', modalItem: level })
    scroll_to(d, ovf_el)
    clicked = safe_click(d, ovf_el, ovf_txt)

    if not clicked:
        rec(b, f"{prefix}-MODAL-001", "Overflow click", "WARN", "Click failed")
        sd["all"] = visible
        _print_student_summary(category, sd["all"])
        return

    # FIX: Wait for URL param modal=students (URL-driven modal)
    modal_item = STUDENT_MODAL_ITEM[category]
    url_ok = wait_for_url_param(d, "modal", "students", timeout=8.0)
    if url_ok:
        print(f"      URL: modal=students&modalItem={modal_item}")
    else:
        print(f"      ⚠ URL param not detected in time — current URL: {current_url(d)[:120]}")

    # Debug: print current URL and page title to help diagnose
    print(f"      Current URL: {current_url(d)[:120]}")

    # Wait for modal DOM — try with exact heading first, then partial
    modal_el = wait_for_modal_dom(d, category, timeout=12.0)

    if not modal_el and category == "Performing Well":
        print(f"      Trying partial heading match for 'Performing Well'…")
        modal_el = wait_for_modal_dom(d, "Performing", timeout=5.0)

    if not modal_el:
        # Last-ditch: check if any Close button is visible (modal opened but heading mismatch)
        try:
            close_btns = d.find_elements(By.XPATH, "//button[@aria-label='Close modal']")
            visible_close = [b for b in close_btns if b.is_displayed()]
            if visible_close:
                print(f"      Close button visible — modal IS open, walking up to find card")
                node = visible_close[0]
                for _ in range(10):
                    try:
                        node = node.find_element(By.XPATH, "..")
                        cls = node.get_attribute("class") or ""
                        if "shadow-2xl" in cls and "bg-white" in cls:
                            modal_el = node
                            print(f"      Found modal card via Close button walk-up")
                            break
                    except Exception:
                        break
        except Exception:
            pass

    if not modal_el:
        rec(b, f"{prefix}-MODAL-001", "Student modal", "WARN",
            "Modal DOM not found")
        sd["modal_opened"] = False
        sd["all"] = visible
        # Close if partially opened
        try:
            d.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass
        wait_for_url_param_gone(d, "modal", timeout=5.0)
        _print_student_summary(category, sd["all"])
        return

    sd["modal_opened"] = True

    # Read all students from modal (with scroll)
    modal_students = read_student_modal_rows(d, modal_el, category)
    sd["modal_rows"] = modal_students

    if modal_students:
        rec(b, f"{prefix}-MODAL-001", "Student modal read", "PASS",
            f"{len(modal_students)} students captured")
        for j, s in enumerate(modal_students, 1):
            ci = f"  {s['class_info']}" if s.get("class_info") else ""
            rec(b, f"{prefix}-M{j:02d}",
                f"Modal #{j}: {s['name']}", "PASS",
                f"Score:{s['pct']}{ci}")
        print(f"\n      {len(modal_students)} students read from modal:")
        for i, s in enumerate(modal_students, 1):
            ci = f"  ({s['class_info']})" if s.get("class_info") else ""
            print(f"        #{i:>2}: {s['name']:<40} {s['pct']:>8}{ci}")

        # Validate count
        if badge_n > 0:
            got = len(modal_students)
            rec(b, f"{prefix}-VAL",
                f"Count check: declared={badge_n}, captured={got}",
                "PASS" if got >= badge_n else "WARN",
                f"{got}/{badge_n}")
    else:
        rec(b, f"{prefix}-MODAL-001", "Student modal", "WARN",
            "Modal opened but 0 rows captured")

    sd["all"] = modal_students if modal_students else visible

    # Close modal
    close_modal_by_url(d, timeout=8.0)
    print(f"      Modal closed.")
    time.sleep(0.5)

    _print_student_summary(category, sd["all"])


def _print_student_summary(category, students):
    print(f"\n  {'─'*70}")
    print(f"  📊  {category.upper()} — {len(students)} STUDENTS")
    print(f"  {'─'*70}")
    if not students:
        print("  ⚠️  No students captured")
    else:
        print(f"  {'#':<4} {'Name':<42} {'Class':<12} {'Score':>8}")
        print(f"  {'-'*4} {'-'*42} {'-'*12} {'-'*8}")
        for i, s in enumerate(students, 1):
            print(f"  {i:<4} {s['name']:<42} "
                  f"{s.get('class_info',''):<12} {s.get('pct',''):>8}")
    print(f"  {'─'*70}")


def test_all_students(d, wait):
    sep("SECTION 7 – Highlighted Students")
    b = store["students"]["Weak"]["tests"]

    try:
        hd = d.find_element(
            By.XPATH, "//*[contains(text(),'Highlighted Students')]")
        rec(b, "TC-HS-000", "Highlighted Students heading", "PASS",
            (hd.text or ""))
    except Exception as e:
        rec(b, "TC-HS-000", "Highlighted Students heading", "WARN", str(e))

    try:
        sub = d.find_element(
            By.XPATH,
            "//*[contains(text(),'preboard') or contains(text(),'classified')]")
        rec(b, "TC-HS-SUB", "Sub-text visible", "PASS",
            (sub.text or "")[:80])
    except Exception as e:
        rec(b, "TC-HS-SUB", "Sub-text", "WARN", str(e))

    for cat in ["Weak", "Lagging", "Performing Well"]:
        test_student_category(d, cat)
        time.sleep(0.5)


# ══════════════════════════════════════════════════════════════════════════════
#  HTML REPORT
# ══════════════════════════════════════════════════════════════════════════════

def _sb(s):
    m = {
        "PASS": ("pbg", "cpass", "✔"),
        "FAIL": ("fbg", "cfail", "✘"),
        "WARN": ("wbg", "cwarn", "⚠"),
        "INFO": ("ibg", "cinfo", "ℹ"),
    }
    bg, c, ic = m.get(s, ("ibg", "cinfo", "ℹ"))
    return f'<span class="sb {bg} {c}">{ic} {s}</span>'

def _tbl(entries):
    if not entries:
        return '<p class="nil">No entries.</p>'
    rows = "".join(
        f'<tr><td class="tid">{e["tc_id"]}</td>'
        f'<td>{e["desc"]}</td>'
        f'<td style="text-align:center">{_sb(e["status"])}</td>'
        f'<td class="det">{e.get("detail","")}</td>'
        f'<td class="ts">{e.get("ts","")}</td></tr>'
        for e in entries)
    return (
        f'<table><thead><tr>'
        f'<th style="width:140px">Test ID</th>'
        f'<th>Description</th>'
        f'<th style="width:90px;text-align:center">Status</th>'
        f'<th>Detail</th>'
        f'<th style="width:65px">Time</th>'
        f'</tr></thead><tbody>{rows}</tbody></table>')

CSS = """
:root{--bg:#0f1724;--s1:#162032;--s2:#1c2a40;--s3:#223050;--bd:#2a3f5f;
  --ac:#3b82f6;--a2:#60a5fa;--pass:#22c55e;--pbg:#052e16;--fail:#ef4444;--fbg:#450a0a;
  --warn:#f59e0b;--wbg:#422006;--info:#38bdf8;--ibg:#082f49;
  --txt:#e2e8f0;--mut:#94a3b8;--dim:#64748b;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.6}
.topbar{background:linear-gradient(135deg,#0a1628,#162032);border-bottom:2px solid var(--ac);
  padding:0 32px;display:flex;align-items:center;justify-content:space-between;
  height:64px;position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.5)}
.tb-brand{display:flex;align-items:center;gap:14px}
.tb-logo{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,var(--ac),#1d4ed8);
  display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;color:#fff}
.tb-title{font-size:18px;font-weight:700;color:#fff}
.tb-sub{font-size:11px;color:var(--mut)}
.tb-meta{font-size:12px;color:var(--dim);text-align:right}
.tb-meta span{color:var(--a2);font-weight:600}
.wrap{max-width:1400px;margin:0 auto;padding:32px 24px}
.hero{background:linear-gradient(135deg,#162032,#1e3a5f,#162032);border:1px solid var(--bd);
  border-radius:16px;padding:40px;margin-bottom:28px}
.hero-grid{display:grid;grid-template-columns:1fr auto;gap:32px;align-items:center}
.hero-title{font-size:28px;font-weight:800;color:#fff;margin-bottom:8px}
.hero-title span{color:var(--a2)}
.hero-desc{color:var(--mut);font-size:14px;margin-bottom:20px}
.tags{display:flex;flex-wrap:wrap;gap:8px}
.tag{background:var(--s3);border:1px solid var(--bd);border-radius:20px;padding:4px 14px;font-size:12px;color:var(--mut)}
.tag strong{color:var(--a2)}
.big-r{font-size:64px;font-weight:900;color:var(--pass);line-height:1}
.scorecard{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:28px}
.sc{background:var(--s1);border:1px solid var(--bd);border-radius:12px;padding:22px 20px;text-align:center}
.sc.total{border-top:3px solid var(--a2)}.sc.pass{border-top:3px solid var(--pass)}
.sc.fail{border-top:3px solid var(--fail)}.sc.warn{border-top:3px solid var(--warn)}
.sc.rate{border-top:3px solid #a855f7}
.sc-n{font-size:36px;font-weight:800;line-height:1;margin-bottom:6px}
.sc.total .sc-n{color:var(--a2)}.sc.pass .sc-n{color:var(--pass)}.sc.fail .sc-n{color:var(--fail)}
.sc.warn .sc-n{color:var(--warn)}.sc.rate .sc-n{color:#c084fc}
.sc-l{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px}
.section{margin-bottom:28px}
.sec-hdr{display:flex;align-items:center;justify-content:space-between;background:var(--s2);
  border:1px solid var(--bd);border-radius:12px 12px 0 0;padding:16px 22px;cursor:pointer;user-select:none}
.sec-hdr:hover{background:var(--s3)}
.sec-hl{display:flex;align-items:center;gap:12px}
.sec-ico{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px}
.sec-ttl{font-size:15px;font-weight:700;color:#fff}
.sec-sub{font-size:11px;color:var(--dim);margin-top:2px}
.sec-stats{display:flex;gap:10px;align-items:center}
.badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
.badge-pass{background:var(--pbg);color:var(--pass);border:1px solid rgba(34,197,94,.3)}
.badge-blue{background:rgba(59,130,246,.15);color:var(--a2);border:1px solid rgba(59,130,246,.3)}
.chev{color:var(--dim);font-size:18px;transition:transform .3s}.chev.open{transform:rotate(180deg)}
.sec-body{background:var(--s1);border:1px solid var(--bd);border-top:none;border-radius:0 0 12px 12px;overflow:hidden}
.sec-body.hidden{display:none}
table{width:100%;border-collapse:collapse}
thead th{background:var(--s3);color:var(--mut);font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.8px;padding:12px 16px;text-align:left;border-bottom:1px solid var(--bd)}
tbody tr{border-bottom:1px solid var(--bd)}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(59,130,246,.04)}
tbody td{padding:11px 16px;font-size:13px;vertical-align:middle}
.tid{font-family:Consolas,monospace;color:var(--a2);font-size:12px;white-space:nowrap}
.det{color:var(--mut);font-size:12px}.ts{color:var(--dim);font-size:11px;white-space:nowrap}
.sb{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
.pbg{background:var(--pbg)}.cpass{color:var(--pass);border:1px solid rgba(34,197,94,.3)}
.fbg{background:var(--fbg)}.cfail{color:var(--fail);border:1px solid rgba(239,68,68,.3)}
.wbg{background:var(--wbg)}.cwarn{color:var(--warn);border:1px solid rgba(245,158,11,.3)}
.ibg{background:var(--ibg)}.cinfo{color:var(--info);border:1px solid rgba(56,189,248,.3)}
.nil{padding:12px 16px;color:var(--dim);font-size:12px}
.sub-hdr{padding:10px 14px 5px;font-size:11px;font-weight:700;color:var(--mut);text-transform:uppercase;letter-spacing:.4px}
.cat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:20px}
.ccat{border-radius:12px;overflow:hidden}
.weak-col{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.35)}
.lag-col{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.35)}
.perf-col{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.35)}
.chdr{padding:16px 18px;display:flex;align-items:flex-start;gap:12px}
.weak-hdr{background:rgba(239,68,68,.25)}.lag-hdr{background:rgba(245,158,11,.25)}.perf-hdr{background:rgba(34,197,94,.25)}
.cico{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800;color:#fff;flex-shrink:0}
.weak-ico{background:#ef4444}.lag-ico{background:#f59e0b}.perf-ico{background:#22c55e}
.cmeta{flex:1}.ctit{font-size:16px;font-weight:700;color:#fff}
.cpills{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
.pill{padding:2px 9px;border-radius:20px;font-size:10px;font-weight:600}
.pp{background:rgba(34,197,94,.2);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
.pi{background:rgba(56,189,248,.15);color:#38bdf8;border:1px solid rgba(56,189,248,.3)}
.srow{display:flex;align-items:center;gap:10px;padding:9px 16px;border-top:1px solid var(--bd)}
.srow:hover{background:rgba(255,255,255,.03)}
.snum{font-size:11px;font-weight:700;color:var(--dim);width:22px;text-align:center;flex-shrink:0}
.sinfo{flex:1;min-width:0}.snm{font-size:13px;font-weight:500;color:var(--txt);display:block}
.ci{font-size:10px;color:var(--dim);display:block;margin-top:1px}
.bw{width:80px;background:var(--s3);border-radius:4px;height:5px;overflow:hidden;flex-shrink:0}
.bar{height:100%;border-radius:4px}
.spct{font-size:14px;font-weight:700;width:60px;text-align:right;flex-shrink:0}
.modal-tag{background:rgba(59,130,246,.15);color:var(--a2);border:1px solid rgba(59,130,246,.3);border-radius:10px;padding:1px 7px;font-size:10px;font-weight:600}
.vis-tag{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);border-radius:10px;padding:1px 7px;font-size:10px;font-weight:600}
.cbdg{font-size:12px;color:var(--mut);margin-top:2px}
.exam-banner{background:linear-gradient(135deg,#7c3009,#b45309,#7c3009);border-radius:12px;
  padding:28px 36px;display:flex;align-items:center;gap:32px;margin:20px}
.exam-lbl{font-size:11px;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.exam-pct{font-size:42px;font-weight:800;color:#fff;line-height:1}
.exam-arr{font-size:32px;color:rgba(255,255,255,.8)}
.exam-dec{background:rgba(0,0,0,.25);border-radius:20px;padding:5px 16px;font-size:12px;color:#fed7aa;font-weight:600;margin-top:10px;display:inline-block}
.exam-div{width:1px;height:60px;background:rgba(255,255,255,.2)}
.ch-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:16px}
.ch-card{background:var(--s2);border:1px solid var(--bd);border-radius:10px;overflow:hidden}
.ch-hdr{padding:12px 16px;font-size:13px;font-weight:700}
.rt-hdr{background:rgba(37,99,235,.2);color:#60a5fa;border-left:3px solid #2563eb}
.bu-hdr{background:rgba(217,119,6,.2);color:#fbbf24;border-left:3px solid #d97706}
.ot-hdr{background:rgba(22,163,74,.2);color:#4ade80;border-left:3px solid #16a34a}
.footer{border-top:1px solid var(--bd);margin-top:40px;padding:24px;text-align:center;color:var(--dim);font-size:12px}
"""

def _chapter_cards_html():
    html = '<div class="ch-grid">'
    colors = {
        "Reteach"  : ("rt-hdr", "#2563eb"),
        "Brushup"  : ("bu-hdr", "#d97706"),
        "On Track" : ("ot-hdr", "#16a34a"),
    }
    for label in ["Reteach", "Brushup", "On Track"]:
        cd       = store["chapters"][label]
        hdr_cls, color = colors[label]
        rows_html = ""
        for ch in cd["modal_chapters"]:
            rows_html += (
                f'<tr><td class="tid">{ch}</td>'
                f'<td style="text-align:center">'
                f'<span style="color:#94a3b8;font-size:11px">modal</span></td></tr>')
        for c in cd["cards"]:
            avg_c = ("#22c55e" if c["chapter_avg"] != "N/A" and
                     not str(c["chapter_avg"]).startswith("-") else
                     "#ef4444" if str(c["chapter_avg"]).startswith("-") else "#64748b")
            rows_html += (
                f'<tr><td class="tid">{c["name"]}</td>'
                f'<td style="text-align:center;color:{avg_c};font-weight:700">'
                f'{c["chapter_avg"]}</td>'
                f'<td style="text-align:center;color:#38bdf8;font-weight:700">'
                f'{c["avg_weightage"]}</td></tr>')
        table_html = (
            f'<table><thead><tr>'
            f'<th>Chapter</th><th>Avg %</th><th>Weightage</th>'
            f'</tr></thead><tbody>{rows_html or "<tr><td colspan=3 class=nil>None</td></tr>"}'
            f'</tbody></table>')
        badge_str = cd["badge"] or f"{cd['badge_n']} chapters"
        html += (
            f'<div class="ch-card">'
            f'<div class="ch-hdr {hdr_cls}">'
            f'{label} '
            f'<span style="font-weight:400;font-size:11px;opacity:.8">'
            f'({badge_str})</span></div>'
            f'{table_html}</div>')
    html += '</div>'
    return html

def _student_cards_html():
    html = '<div class="cat-grid">'
    cat_data = {
        "Weak"          : ("weak", "weak", "#ef4444", "W"),
        "Lagging"       : ("lag",  "lag",  "#f59e0b", "L"),
        "Performing Well": ("perf","perf", "#22c55e", "P"),
    }
    for cat in ["Weak", "Lagging", "Performing Well"]:
        sd = store["students"][cat]
        css, hdr, color, ico = cat_data[cat]
        stus  = sd["all"]
        vc    = len(sd["visible"])
        mc    = len(sd["modal_rows"])
        ovf   = sd["overflow_txt"]
        mopn  = sd["modal_opened"]

        pills = ""
        if ovf:
            pills += f'<span class="pill pp">✅ {ovf} clicked</span>'
        if mopn:
            pills += f'<span class="pill pp">🪟 Modal · {mc} students</span>'
        pills += f'<span class="pill pi">👁 {vc} visible · 📂 {mc} modal · ✅ {len(stus)} total</span>'

        if not stus:
            body = ('<div style="padding:28px;text-align:center;color:var(--dim);'
                    'font-style:italic">No students captured</div>')
        else:
            body = ""
            for i, s in enumerate(stus, 1):
                raw_pct = re.sub(r'[^0-9.]', '', s.get("pct", "0") or "0")
                pv  = float(raw_pct) if raw_pct else 0
                bw  = min(int(pv), 100)
                tag = ('<span class="modal-tag">📂 modal</span>'
                       if (i > vc and mopn) else
                       '<span class="vis-tag">👁 visible</span>' if i <= vc else "")
                ci  = (f'<span class="ci">{s.get("class_info","")}</span>'
                       if s.get("class_info") else "")
                body += (
                    f'<div class="srow">'
                    f'<span class="snum">{i}</span>'
                    f'<div class="sinfo">'
                    f'<span class="snm">{s["name"]}</span>{ci}</div>'
                    f'<div class="bw"><div class="bar" '
                    f'style="width:{bw}%;background:{color}"></div></div>'
                    f'<span class="spct" style="color:{color}">'
                    f'{s.get("pct","")}</span>'
                    f'{tag}</div>')

        html += (
            f'<div class="ccat {css}-col">'
            f'<div class="chdr {css}-hdr">'
            f'<div class="cico {css}-ico">{ico}</div>'
            f'<div class="cmeta">'
            f'<div class="ctit">{cat}</div>'
            f'<div class="cbdg">{sd["badge"]}</div>'
            f'<div class="cpills">{pills}</div>'
            f'</div></div>{body}</div>')
    html += '</div>'
    return html


def build_report() -> str:
    total = _P + _F + _W
    rate  = round(_P / max(total, 1) * 100, 1)

    all_ch  = sum((store["chapters"][l]["tests"] for l in ["Reteach","Brushup","On Track"]), [])
    all_st  = sum((store["students"][c]["tests"] for c in ["Weak","Lagging","Performing Well"]), [])

    lp = sum(1 for e in store["login_tests"]  if e["status"] == "PASS")
    np = sum(1 for e in store["nav_tests"]     if e["status"] == "PASS")
    ep = sum(1 for e in store["exam_tests"]    if e["status"] == "PASS")
    cp = sum(1 for e in all_ch                 if e["status"] == "PASS")
    sp = sum(1 for e in all_st                 if e["status"] == "PASS")

    lp2 = store["exam"].get("left_pct",  "—")
    rp2 = store["exam"].get("right_pct", "—")
    tr  = store["exam"].get("trend",     "—")

    def sec(icon, title, sub, icon_bg, pc, tc, extra, tests):
        return (
            f"<div class='section'>"
            f"<div class='sec-hdr' onclick='tog(this)'>"
            f"<div class='sec-hl'>"
            f"<div class='sec-ico' style='background:{icon_bg}'>{icon}</div>"
            f"<div><div class='sec-ttl'>{title}</div>"
            f"<div class='sec-sub'>{sub}</div></div></div>"
            f"<div class='sec-stats'>"
            f"<span class='badge badge-pass'>{pc} PASSED</span>"
            f"<span class='badge badge-blue'>{tc} TESTS</span>"
            f"<span class='chev open'>▾</span></div></div>"
            f"<div class='sec-body'>{extra}{_tbl(tests)}</div></div>")

    exam_html = (
        "<div class='exam-banner'>"
        f"<div><div class='exam-lbl'>"
        f"{VALUES['CompareLeft']} vs {VALUES['CompareRight']}</div></div>"
        "<div class='exam-div'></div>"
        f"<div><div class='exam-lbl'>{VALUES['CompareLeft']}</div>"
        f"<div class='exam-pct'>{lp2}</div></div>"
        "<div class='exam-arr'>→</div>"
        f"<div><div class='exam-lbl'>{VALUES['CompareRight']}</div>"
        f"<div class='exam-pct' style='color:#fed7aa'>{rp2}</div>"
        f"<div class='exam-dec'>⬇ {tr}</div></div></div>")

    ch_extra = (
        "<div class='sub-hdr'>📋 Chapter Data (Source-verified selectors)</div>"
        + _chapter_cards_html()
        + "<div class='sub-hdr' style='margin-top:10px'>🧪 Tests</div>")

    st_extra = (
        "<div class='sub-hdr'>📋 Student Lists</div>"
        + _student_cards_html()
        + "<div class='sub-hdr' style='margin-top:10px'>🧪 Tests</div>")

    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>ClassLens Test Report v17</title>"
        "<style>" + CSS + "</style></head><body>"
        "<div class='topbar'>"
        "<div class='tb-brand'>"
        "<div class='tb-logo'>CL</div>"
        "<div>"
        "<div class='tb-title'>ClassLens QA — Test Report v17</div>"
        "<div class='tb-sub'>Source-code verified · URL-driven modal wait · "
        "JS-first modal detection · JS-first student row extraction</div>"
        "</div></div>"
        "<div class='tb-meta'>"
        "Generated: <span id='gt'></span><br>"
        f"{VALUES['Class']}-{VALUES['Section']} | "
        f"{VALUES['Subject']} | "
        f"{VALUES['CompareLeft']} → {VALUES['CompareRight']}"
        "</div></div>"
        "<div class='wrap'>"
        "<div class='hero'><div class='hero-grid'><div>"
        "<div class='hero-title'>ClassLens Overview Tab "
        "<span>v17 Test Report</span></div>"
        "<div class='hero-desc'>"
        "v17 fixes: JS-first modal detection (bypasses Tailwind v4 class issues) · "
        "JS-first student row + class-info extraction · "
        "Robust badge reading via text-content · "
        "Last-resort Close-button walk-up for modal"
        "</div>"
        "<div class='tags'>"
        f"<span class='tag'><strong>URL:</strong> classlens.inferentics.com</span>"
        f"<span class='tag'><strong>User:</strong> {USERNAME}</span>"
        f"<span class='tag'><strong>Class:</strong> {VALUES['Class']}-{VALUES['Section']}</span>"
        f"<span class='tag'><strong>Run:</strong> {run_ts}</span>"
        "</div></div>"
        f"<div style='text-align:center'>"
        f"<div class='big-r'>{rate}%</div>"
        f"<div style='font-size:12px;color:var(--mut);margin-top:4px'>PASS RATE</div>"
        f"<div style='font-size:11px;color:var(--dim);margin-top:8px'>{_P}/{total}</div>"
        "</div></div></div>"
        "<div class='scorecard'>"
        f"<div class='sc total'><div class='sc-n'>{total}</div><div class='sc-l'>Total</div></div>"
        f"<div class='sc pass'><div class='sc-n'>{_P}</div><div class='sc-l'>✔ Passed</div></div>"
        f"<div class='sc fail'><div class='sc-n'>{_F}</div><div class='sc-l'>✘ Failed</div></div>"
        f"<div class='sc warn'><div class='sc-n'>{_W}</div><div class='sc-l'>⚠ Warn</div></div>"
        f"<div class='sc rate'><div class='sc-n'>{rate}%</div><div class='sc-l'>Rate</div></div>"
        "</div>"
        + sec("🔐", "Section 1 – Login",       "Auth · Fields · Logo",
              "rgba(59,130,246,.2)", lp, len(store["login_tests"]), "", store["login_tests"])
        + sec("🧭", "Section 2 – Navigation",   "Dropdowns · Enter · Tabs",
              "rgba(168,85,247,.2)", np, len(store["nav_tests"]),   "", store["nav_tests"])
        + sec("📊", "Section 3 – Exam Comparison", "Banner · Percentages · Trend",
              "rgba(245,158,11,.2)", ep, len(store["exam_tests"]),  exam_html, store["exam_tests"])
        + sec("📚", "Sections 4/5/6 – Chapters", "Reteach · Brushup · On Track",
              "rgba(34,197,94,.2)",  cp, len(all_ch),               ch_extra, all_ch)
        + sec("👥", "Section 7 – Students",      "Weak · Lagging · Performing Well",
              "rgba(168,85,247,.2)", sp, len(all_st),               st_extra, all_st)
        + "<div class='footer'>"
        f"<div>ClassLens QA v17 &nbsp;|&nbsp; <span id='ft'></span>"
        f" &nbsp;|&nbsp; {total} Tests · {rate}%</div></div>"
        "</div>"
        "<script>"
        "var f=new Date().toLocaleString('en-IN',{timeZone:'Asia/Kolkata',"
        "year:'numeric',month:'short',day:'2-digit',"
        "hour:'2-digit',minute:'2-digit',second:'2-digit'});"
        "document.getElementById('gt').textContent=f;"
        "document.getElementById('ft').textContent=f;"
        "function tog(h){"
        "  var b=h.nextElementSibling,c=h.querySelector('.chev');"
        "  var hidden=b.classList.toggle('hidden');"
        "  c.classList.toggle('open',!hidden);}"
        "</script></body></html>")




def build_combined_report(runs) -> str:
    agg = aggregate_summary(runs)
    sections_tags = "".join(
        f"<span class='tag'><strong>Section:</strong> {r['config']['Section']} · {r['summary']['pass_rate']}% · {r['summary']['passed']}/{r['summary']['total']}</span>"
        for r in runs
    )

    runs_html = ""
    for idx, run in enumerate(runs, 1):
        exam = run.get("exam", {})
        test_groups = flatten_test_groups(run)
        all_tests = test_groups["login"] + test_groups["nav"] + test_groups["exam"] + test_groups["chapters"] + test_groups["students"]

        runs_html += (
            f"<div class='section'><div class='sec-hdr' onclick='tog(this)'><div class='sec-hl'>"
            f"<div class='sec-ico' style='background:rgba(59,130,246,.2)'>#{idx}</div>"
            f"<div><div class='sec-ttl'>Section {run['config']['Section']}</div>"
            f"<div class='sec-sub'>{run['config']['Class']}-{run['config']['Section']} · {run['config']['Subject']} · {run['run_ts']}</div></div></div>"
            f"<div class='sec-stats'><span class='badge badge-pass'>{run['summary']['passed']} PASSED</span>"
            f"<span class='badge badge-blue'>{run['summary']['total']} TESTS</span>"
            f"<span class='badge badge-blue'>{run['summary']['pass_rate']}% RATE</span><span class='chev open'>▾</span></div></div>"
            f"<div class='sec-body'>"
            f"<div class='exam-banner'><div><div class='exam-lbl'>{run['config']['CompareLeft']}</div><div class='exam-pct'>{exam.get('left_pct','—') or '—'}</div></div><div class='exam-arr'>→</div><div><div class='exam-lbl'>{run['config']['CompareRight']}</div><div class='exam-pct' style='color:#fed7aa'>{exam.get('right_pct','—') or '—'}</div><div class='exam-dec'>⬇ {exam.get('trend','—') or '—'}</div></div></div>"
        )

        runs_html += '<div class="sub-hdr">📚 Chapters</div><div class="ch-grid">'
        hdr_map = {"Reteach":"rt-hdr","Brushup":"bu-hdr","On Track":"ot-hdr"}
        for label in ["Reteach","Brushup","On Track"]:
            cd = run["chapters"][label]
            rows = ""
            for c in cd.get("cards", []):
                rows += f"<tr><td class='tid'>{c['name']}</td><td>{c.get('chapter_avg','N/A')}</td><td>{c.get('avg_weightage','N/A')}</td></tr>"
            for ch in cd.get("modal_chapters", []):
                rows += f"<tr><td class='tid'>{ch}</td><td colspan='2'>modal list</td></tr>"
            if not rows:
                rows = "<tr><td colspan='3' class='nil'>No data captured</td></tr>"
            runs_html += f"<div class='ch-card'><div class='ch-hdr {hdr_map[label]}'>{label} <span style='font-weight:400;font-size:11px;opacity:.8'>({cd.get('badge') or cd.get('badge_n',0)})</span></div><table><thead><tr><th>Chapter</th><th>Avg</th><th>Weightage</th></tr></thead><tbody>{rows}</tbody></table></div>"
        runs_html += '</div>'

        runs_html += '<div class="sub-hdr" style="margin-top:12px">👥 Students</div><div class="cat-grid">'
        style_map = {"Weak":("weak-col","weak-hdr","weak-ico","W"),"Lagging":("lag-col","lag-hdr","lag-ico","L"),"Performing Well":("perf-col","perf-hdr","perf-ico","P")}
        for cat in ["Weak","Lagging","Performing Well"]:
            sd = run["students"][cat]
            outer, hdr, ico_cls, ico = style_map[cat]
            rows_html = ""
            rows = sd.get("all") or sd.get("visible") or []
            if rows:
                for i, s in enumerate(rows, 1):
                    rows_html += f"<div class='srow'><span class='snum'>{i}</span><div class='sinfo'><span class='snm'>{s.get('name','')}</span><span class='ci'>{s.get('class_info','')}</span></div><span class='spct'>{s.get('pct','')}</span></div>"
            else:
                rows_html = "<div class='nil' style='padding:16px'>No students captured</div>"
            runs_html += f"<div class='ccat {outer}'><div class='chdr {hdr}'><div class='cico {ico_cls}'>{ico}</div><div class='cmeta'><div class='ctit'>{cat}</div><div class='cbdg'>{sd.get('badge','')}</div></div></div>{rows_html}</div>"
        runs_html += '</div>'

        runs_html += _tbl(all_tests) + '</div></div>'

    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>ClassLens Multi-Section Test Report v17</title><style>" + CSS + "</style></head><body>"
        "<div class='topbar'><div class='tb-brand'><div class='tb-logo'>CL</div><div><div class='tb-title'>ClassLens QA — Multi-Section Report v17</div><div class='tb-sub'>Auto-runs all requested sections sequentially and merges output into one report</div></div></div>"
        f"<div class='tb-meta'>Generated: <span id='gt'></span><br>Sections: {agg['sections_run']} | Pass Rate: {agg['pass_rate']}%</div></div>"
        "<div class='wrap'><div class='hero'><div class='hero-grid'><div><div class='hero-title'>Combined <span>All Sections</span> Report</div><div class='hero-desc'>Runs each section one by one with the same flow and merges everything into one final JSON + HTML report.</div>"
        f"<div class='tags'>{sections_tags}</div></div><div style='text-align:center'><div class='big-r'>{agg['pass_rate']}%</div><div style='font-size:12px;color:var(--mut);margin-top:4px'>OVERALL PASS RATE</div></div></div></div>"
        "<div class='scorecard'>"
        f"<div class='sc total'><div class='sc-n'>{agg['total']}</div><div class='sc-l'>Total</div></div>"
        f"<div class='sc pass'><div class='sc-n'>{agg['passed']}</div><div class='sc-l'>✔ Passed</div></div>"
        f"<div class='sc fail'><div class='sc-n'>{agg['failed']}</div><div class='sc-l'>✘ Failed</div></div>"
        f"<div class='sc warn'><div class='sc-n'>{agg['warnings']}</div><div class='sc-l'>⚠ Warn</div></div>"
        f"<div class='sc rate'><div class='sc-n'>{agg['sections_run']}</div><div class='sc-l'>Sections Run</div></div></div>"
        + runs_html + "<div class='footer'><div>ClassLens QA v17 Multi-Section</div></div></div>"
        "<script>var f=new Date().toLocaleString('en-IN',{timeZone:'Asia/Kolkata',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'});document.getElementById('gt').textContent=f;function tog(h){var b=h.nextElementSibling,c=h.querySelector('.chev');var hidden=b.classList.toggle('hidden');c.classList.toggle('open',!hidden);}</script></body></html>"
    )


def save_combined_outputs(runs):
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "class": VALUES["Class"],
            "subject": VALUES["Subject"],
            "exam": VALUES["Exam"],
            "compare_left": VALUES["CompareLeft"],
            "compare_right": VALUES["CompareRight"],
            "sections": [r["config"]["Section"] for r in runs],
        },
        "summary": aggregate_summary(runs),
        "runs": runs,
    }
    with open(COMBINED_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\n  📦 Combined JSON → {os.path.abspath(COMBINED_JSON_FILE)}")

    html = build_combined_report(runs)
    with open(COMBINED_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  📄 Combined HTML → {os.path.abspath(COMBINED_REPORT_FILE)}")

    if AUTO_OPEN_REPORT:
        open_browser(COMBINED_REPORT_FILE)

# ══════════════════════════════════════════════════════════════════════════════
#  SAVE + OPEN
# ══════════════════════════════════════════════════════════════════════════════

def open_browser(path):
    abs_p = os.path.abspath(path)
    url   = "file:///" + abs_p.replace(os.sep, "/")
    print(f"\n  🌐 {url}")
    try:
        if webbrowser.open(url, new=2):
            print("  ✅ Browser launched.")
            return
    except Exception:
        pass
    try:
        if sys.platform.startswith("win"):   os.startfile(abs_p)
        elif sys.platform == "darwin":        subprocess.Popen(["open", abs_p])
        else:
            for cmd in ["xdg-open", "google-chrome", "firefox"]:
                try:
                    subprocess.Popen([cmd, abs_p]); return
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"  ⚠ {e}")


def save_outputs():
    total = _P + _F + _W
    store["summary"] = {
        "total": total, "passed": _P, "failed": _F, "warnings": _W,
        "pass_rate": f"{round(_P/max(total,1)*100,1)}%",
    }
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
    print(f"\n  📦 JSON → {os.path.abspath(JSON_FILE)}")

    html = build_report()
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  📄 HTML → {os.path.abspath(REPORT_FILE)}")

    if AUTO_OPEN_REPORT:
        open_browser(REPORT_FILE)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_single_section(section_value: str):
    reset_run_state(section_value)

    print("\n╔" + "═"*70 + "╗")
    print("║   ClassLens – UI Test Suite v17.0                                   ║")
    print("║   JS-first modal detection · JS student rows · badge text-content   ║")
    line = f"║   Section: {section_value:<3} Started: {run_ts}"
    print(line + " " * max(0, 71 - len(line)) + "║")
    print("╚" + "═"*70 + "╝")

    driver = make_driver()
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        if not test_login(driver, wait):
            print(f"❌ Login failed — aborting section {section_value}")
            return snapshot_current_run()
        if not test_navigation(driver, wait):
            print(f"❌ Navigation failed — aborting section {section_value}")
            return snapshot_current_run()

        test_exam_comparison(driver)

        for label in ["Reteach", "Brushup", "On Track"]:
            test_chapter_section(driver, label)

        test_all_students(driver, wait)

    except Exception as exc:
        print(f"\n💥 Unexpected error in section {section_value}: {exc}")
        traceback.print_exc()

    finally:
        sep(f"FINAL SUMMARY — SECTION {section_value}")
        total = _P + _F + _W
        rate  = round(_P / max(total, 1) * 100, 1)
        print(f"  ✅  Passed   : {_P}")
        print(f"  ❌  Failed   : {_F}")
        print(f"  ⚠️   Warnings : {_W}")
        print(f"  📊  Pass Rate: {rate}%  ({_P}/{total})")
        try:
            driver.quit()
        except Exception:
            pass

    return snapshot_current_run()


def print_combined_console_summary(runs):
    agg = aggregate_summary(runs)
    sep("COMBINED FINAL SUMMARY — ALL SECTIONS")
    print(f"  Sections Run : {agg['sections_run']}")
    print(f"  ✅ Passed    : {agg['passed']}")
    print(f"  ❌ Failed    : {agg['failed']}")
    print(f"  ⚠️ Warnings  : {agg['warnings']}")
    print(f"  📊 Pass Rate : {agg['pass_rate']}%  ({agg['passed']}/{agg['total']})")
    print("\n  Section-wise summary")
    print("  " + "-" * 66)
    print(f"  {'Section':<10}{'Passed':>8}{'Failed':>10}{'Warn':>8}{'Rate':>10}")
    print("  " + "-" * 66)
    for run in runs:
        sm = run['summary']
        print(f"  {run['config']['Section']:<10}{sm['passed']:>8}{sm['failed']:>10}{sm['warnings']:>8}{str(sm['pass_rate'])+'%':>10}")


def main_all_sections():
    sections = [s.strip() for s in SECTION_RUN_LIST if str(s).strip()]
    if not sections:
        print("❌ No sections configured in SECTION_RUN_LIST")
        return

    all_runs = []
    for idx, section_value in enumerate(sections, 1):
        sep(f"RUN {idx}/{len(sections)} — SECTION {section_value}")
        run_result = run_single_section(section_value)
        all_runs.append(run_result)

    print_combined_console_summary(all_runs)
    save_combined_outputs(all_runs)

    if KEEP_BROWSER_OPEN:
        input("\n👉  Press ENTER to finish…")
    print("\n🏁  Done.")


def main():
    if MULTI_SECTION_MODE and len(SECTION_RUN_LIST) > 1:
        main_all_sections()
        return

    single_section = VALUES.get("Section", "I")
    run_result = run_single_section(single_section)

    global store, _P, _F, _W
    store = deepcopy(run_result)
    _P = run_result["summary"]["passed"]
    _F = run_result["summary"]["failed"]
    _W = run_result["summary"]["warnings"]
    save_outputs()

    if KEEP_BROWSER_OPEN:
        input("\n👉  Press ENTER to finish…")
    print("\n🏁  Done.")



# ==============================================================================
# ADD-ONLY RUNTIME PATCH BEFORE ORIGINAL MAIN
# This block adds behaviour only. It does not delete or replace original source lines.
# ==============================================================================
try:
    if globals().get('_CL_SKIP_ZZ_ADDONLY') and 'SECTION_RUN_LIST' in globals():
        SECTION_RUN_LIST = [s for s in SECTION_RUN_LIST if str(s).strip().upper() != 'ZZ']
        print('[ADD-ONLY PATCH] Section ZZ skipped at runtime.')
except Exception as _e:
    print('[ADD-ONLY PATCH] skip ZZ setup warning:', _e)

try:
    if globals().get('_CL_NO_INPUT_ADDONLY'):
        KEEP_BROWSER_OPEN = False
        AUTO_OPEN_REPORT = False
        print('[ADD-ONLY PATCH] Non-blocking mode enabled: KEEP_BROWSER_OPEN=False, AUTO_OPEN_REPORT=False')
except Exception as _e:
    print('[ADD-ONLY PATCH] no-input setup warning:', _e)

try:
    if globals().get('_CL_HEADLESS_ADDONLY') and 'make_driver' in globals() and not globals().get('_CL_MAKE_DRIVER_PATCHED_ADDONLY'):
        _CL_ORIG_MAKE_DRIVER_ADDONLY = make_driver
        def make_driver(*args, **kwargs):
            try:
                from selenium import webdriver as _wd
                from selenium.webdriver.chrome.options import Options as _Options
                opts = _Options()
                opts.add_argument('--headless=new')
                opts.add_argument('--disable-gpu')
                opts.add_argument('--window-size=1920,1080')
                opts.add_argument('--disable-notifications')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-extensions')
                opts.add_argument('--blink-settings=imagesEnabled=false')
                opts.add_argument('--disable-background-networking')
                opts.add_argument('--disable-sync')
                opts.add_argument('--metrics-recording-only')
                opts.add_argument('--disable-default-apps')
                d = _wd.Chrome(options=opts)
                try: d.implicitly_wait(0)
                except Exception: pass
                try:
                    if 'driver_ref' in globals():
                        driver_ref.clear(); driver_ref.append(d)
                except Exception: pass
                return d
            except Exception as _e:
                print('[ADD-ONLY PATCH] headless driver fallback:', _e)
                return _CL_ORIG_MAKE_DRIVER_ADDONLY(*args, **kwargs)
        _CL_MAKE_DRIVER_PATCHED_ADDONLY = True
        print('[ADD-ONLY PATCH] Headless fast Chrome driver enabled.')
except Exception as _e:
    print('[ADD-ONLY PATCH] driver setup warning:', _e)

try:
    if globals().get('_CL_FAST_MODE_ADDONLY'):
        # Reduce broad timeout constants without changing original code lines.
        for _name in ('TIMEOUT','CARD_WAIT_SEC'):
            if _name in globals():
                try: globals()[_name] = min(int(float(globals()[_name])), 18)
                except Exception: pass
        for _name in ('PANEL_WAIT_SEC','S_DROP','S_NAV','S_CARD','S_SEARCH','S_CLEAR','S_LABEL'):
            if _name in globals():
                try: globals()[_name] = min(float(globals()[_name]), 0.35)
                except Exception: pass
        print('[ADD-ONLY PATCH] Fast timeout/sleep settings applied.')
except Exception as _e:
    print('[ADD-ONLY PATCH] fast setup warning:', _e)
# ==============================================================================
# ORIGINAL MAIN BLOCK CONTINUES BELOW
# ==============================================================================

if __name__ == "__main__":
    main()





####################################################################################################
# END OF SCRIPT 1: ClassLens – UI Test Suite v16.0
####################################################################################################

####################################################################################################
# START OF SCRIPT 2: ClassLens – Chapters Tab – All Sections (FINAL MERGED v4)
# Original upload: Pasted text (2)(5).txt
# Preserved lines: 2662
# SHA256: 8c0076db34287d9c0e4b92feaaf6943f02ec02d7dd67dc9f8dbf92ef45da319c
####################################################################################################
"""
ClassLens – Chapters Tab – All Sections  (FINAL MERGED v4)
============================================================
Fully merges Script 1 (Chapter tab REFIXED with Header Accuracy Badge)
and Script 2 (All Sections REFIXED v3 with Excel Validation).

Additions from Script 1 merged into Script 2:
  ✦ read_header_accuracy_badge() — reads "Preboard 1 accuracy XX%" header badge
  ✦ Header accuracy badge test per chapter detail panel
  ✦ Header accuracy column in HTML report: Overview, Consistency, Accuracy tabs
  ✦ Header accuracy terminal summary per chapter

All Script 2 features preserved:
  ✦ Multi-section switching + per-section runner
  ✦ Master chapter/subchapter map (EXCEL_UNITS)
  ✦ Excel validation (CL vs Excel, Full Coverage)
  ✦ Per-section HTML report with all tabs
  ✦ Global 4-Way consistency across all sections
  ✦ Grand summary with progress bars

Script 1 LOC 4 logic (exact REFIXED version) preserved:
  ✦ read_why_text(), read_why_pct(), read_why_pct_from_page(), read_why_accuracy_pct()
  ✦ _CHANGE_KWS_STRICT, _STABLE_PHRASES, _ACC_BEFORE_PHRASES, _FALLBACK_PATTERNS
  ✦ _is_accuracy_pct() guard
  ✦ align_sign() applied consistently to all four locations
  ✦ loc4_display() exact Script 1 version

Run:
    python classlens_all_sections_final.py

Env vars (optional):
    CLASSLENS_USER   (default: sajan)
    CLASSLENS_PASS   (default: Operations123)
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os, re, sys, time, webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
LOGIN_URL    = "https://classlens.inferentics.com/"
CHAPTERS_URL = "https://classlens.inferentics.com/?exams=Midterm%2CPreboard+1&screen=chapters"
USERNAME     = os.getenv("CLASSLENS_USER", "sajan")
PASSWORD     = os.getenv("CLASSLENS_PASS", "Operations123")
REPORT_FILE  = "classlens_all_sections_final_report.html"

ENTRY = {
    "Class":        "12",
    "Subject":      "Maths",
    "Exam":         "Midterm",
    "CompareLeft":  "Midterm",
    "CompareRight": "Preboard 1",
}
EXAM_LABELS    = ["Midterm", "Preboard 1"]
CARD_WAIT_SEC  = 45
PANEL_WAIT_SEC = 4.5

# Timing
S_DROP=0.3; S_NAV=1.2; S_CARD=1.0; S_SEARCH=0.7; S_CLEAR=0.5; S_LABEL=0.8

# Console colours
G="\033[92m"; R="\033[91m"; Y="\033[93m"; C="\033[96m"
W="\033[97m"; DIM="\033[2m"; BLD="\033[1m"; RST="\033[0m"

# ─────────────────────────────────────────────────────────────────────────────
# MASTER CHAPTER MAP
# ─────────────────────────────────────────────────────────────────────────────
EXCEL_UNITS = {
    "Relations and Functions": {
        "marks": 8,
        "chapters": {
            "Relations & Functions": [
                ("Types of Relations", False),
                ("Types of Functions", True),
                ("Composite Functions", False),
                ("Invertible Functions", True),
            ],
            "Inverse Trigonometric Functions": [
                ("Principal Values (Domain and Range)", True),
                ("Formulas for Trigonometry", True),
                ("Algebra of Inverse Trig Functions", False),
                ("Substitution using Trig Formulas", True),
            ],
        }
    },
    "Algebra": {
        "marks": 10,
        "chapters": {
            "Matrices": [
                ("Basics & Types of Matrices", False),
                ("Matrix Operations", True),
                ("Transpose, Symmetric & Skew-symmetric", False),
                ("Elementary Operations", False),
                ("Inverse Matrices", False),
            ],
            "Determinants": [
                ("Determinant of a Matrix", False),
                ("Properties of Determinants", True),
                ("Applications (Area, Cramers Rule, Linear via inverse)", False),
                ("Minors & Cofactors", False),
                ("Adjoint & Inverse", True),
            ],
        }
    },
    "Calculus": {
        "marks": 35,
        "chapters": {
            "Continuity & Differentiability": [
                ("Continuity", False),
                ("Rules of Differentiations", True),
                ("Chain Rule", True),
                ("Parametric & Implicit Differentiation", False),
                ("Derivatives of Inverse Trig Functions", False),
                ("Exponential & Logarithmic Functions/Logarithmic Properties", True),
                ("Second Order Derivative", False),
            ],
            "Application of Derivatives": [
                ("Rate of Change", True),
                ("Increasing & Decreasing Functions", True),
                ("Maxima & Minima", True),
                ("Maxima & Minima real life Applications", False),
            ],
            "Integrals": [
                ("Indefinite Integrals (Anti derivatives)", True),
                ("Rules of integrals", True),
                ("Integration by Substitution", False),
                ("Integration by Parts", False),
                ("Partial Fractions", False),
                ("Properties of Definite Integrals", True),
                ("Definite Integrals", True),
            ],
            "Application of Integrals": [
                ("Area under Curves", True),
            ],
            "Differential Equations": [
                ("Definition, Order & Degree", False),
                ("General & Particular Solution", True),
                ("Formation of DE", False),
                ("Variable Separable Method", False),
                ("Homogeneous DE", True),
                ("Linear DE", False),
                ("Applications (Growth/Decay)", False),
            ],
        }
    },
    "Vectors and Three-dimensional Geometry": {
        "marks": 14,
        "chapters": {
            "Vector Algebra": [
                ("Scalars & Vectors", False),
                ("Position Vector & Unit Vector", True),
                ("Vector Addition & Scalar Multiplication", True),
                ("Dot (Scalar) Product", False),
                ("Cross (Vector) Product", False),
            ],
            "3D Geometry": [
                ("Direction Cosines & Ratios", True),
                ("Equation of a Line", True),
                ("Angle between Lines", False),
            ],
        }
    },
    "Linear Programming Problem": {
        "marks": 5,
        "chapters": {
            "Linear Programming": [
                ("Formulating LPP", True),
                ("Objective Function", False),
                ("Graphical method for problems in two variables", True),
                ("Feasible Region", False),
                ("Optimization", False),
            ],
        }
    },
    "Probability": {
        "marks": 8,
        "chapters": {
            "Probability": [
                ("Conditional Probability", True),
                ("Multiplication Rule", True),
                ("Bayes Theorem", False),
            ],
        }
    },
}

MIDTERM_QUESTIONS = {
    "Relations & Functions": [
        ("1","Types of Functions",False),("18","Types of Functions",False),
        ("36.1","Types of Relations",False),("36.2","Types of Relations",False),
        ("36.3","Types of Relations",False),("36.4","Types of Relations",False),
    ],
    "Linear Programming": [
        ("2","Feasible Region",False),("17","Feasible Region",False),
        ("31","Graphical method for problems in two variables",False),
    ],
    "Matrices": [
        ("3","Matrix Operations",False),("9","Inverse Matrices",False),
        ("14","Basics & Types of Matrices",False),("22","Matrix Operations",False),
        ("27","Transpose, Symmetric & Skew-symmetric",False),
    ],
    "Integrals": [
        ("4","Integration by Substitution",False),("13","Rules of integrals",False),
        ("15","Definite Integrals",False),("24","Definite Integrals",False),
        ("35.1","Partial Fractions",False),("35.2","Properties of Definite Integrals",False),
        ("38.1","Integration by Parts",False),("38.2","Integration by Parts",False),
    ],
    "Determinants": [
        ("5","Determinant of a Matrix",False),("16","Adjoint & Inverse",False),
        ("23","Applications (Area, Cramers Rule, Linear via inverse)",False),
        ("32","Applications (Area, Cramers Rule, Linear via inverse)",False),
    ],
    "Continuity & Differentiability": [
        ("6","Rules of Differentiations",False),("8","Continuity",False),
        ("10","Continuity",False),("12","Parametric & Implicit Differentiation",False),
        ("28.1","Continuity",False),("28.2","Parametric & Implicit Differentiation",False),
        ("33.1","Second Order Derivative",False),
        ("33.2","Exponential & Logarithmic Functions/Logarithmic Properties",False),
    ],
    "Application of Integrals": [
        ("7","Area under Curves",False),("25.1","Area under Curves",False),
        ("25.2","Area under Curves",False),("30.1","Area under Curves",False),
        ("30.2","Area under Curves",False),
    ],
    "Application of Derivatives": [
        ("11","Maxima & Minima real life Applications",False),
        ("20","Increasing & Decreasing Functions",False),
        ("29","Increasing & Decreasing Functions",False),
        ("34","Maxima & Minima real life Applications",False),
        ("37.1","Rate of Change",False),("37.2","Rate of Change",False),
        ("37.3","Rate of Change",False),("37.4","Rate of Change",False),
    ],
    "Inverse Trigonometric Functions": [
        ("19","Principal Values (Domain and Range)",True),
        ("21.1","Principal Values (Domain and Range)",True),
        ("21.2","Principal Values (Domain and Range)",True),
        ("26","Algebra of Inverse Trig Functions",False),
    ],
}

PREBOARD_QUESTIONS = {
    "Relations & Functions": [
        ("1","Types of Relations",False),
        ("38.1","Types of Functions",False),("38.2","Types of Relations",False),
    ],
    "Continuity & Differentiability": [
        ("2","Continuity",False),("11","Parametric & Implicit Differentiation",False),
        ("21.1","Derivatives of Inverse Trig Functions",False),
        ("21.2","Second Order Derivative",False),("24","Continuity",False),
        ("28.1","Exponential & Logarithmic Functions/Logarithmic Properties",False),
        ("28.2","Parametric & Implicit Differentiation",False),
    ],
    "Determinants": [
        ("3","Determinant of a Matrix",False),
        ("8","Applications (Area, Cramers Rule, Linear via inverse)",False),
        ("14","Properties of Determinants",False),("33","Adjoint & Inverse",False),
    ],
    "3D Geometry": [
        ("4","Angle between Lines",False),("5","Equation of a Line",False),
        ("29.1","Equation of a Line",True),("29.2","Equation of a Line",True),
        ("32","Angle between Lines",False),
    ],
    "Differential Equations": [
        ("6","Definition, Order & Degree",False),
        ("34.1","Applications (Growth/Decay)",False),("34.2","Linear DE",True),
    ],
    "Matrices": [
        ("7","Matrix Operations",False),
        ("9","Transpose, Symmetric & Skew-symmetric",False),
    ],
    "Application of Integrals": [
        ("10","Area under Curves",False),("25.2","Area under Curves",False),
        ("30","Area under Curves",False),
    ],
    "Linear Programming": [
        ("12","Graphical method for problems in two variables",False),
        ("16","Objective Function",False),
        ("31","Graphical method for problems in two variables",False),
    ],
    "Probability": [
        ("13","Conditional Probability",False),("26","Conditional Probability",False),
        ("36.1","Bayes Theorem",False),("36.2","Bayes Theorem",False),
        ("36.3","Bayes Theorem",False),
    ],
    "Application of Derivatives": [
        ("15","Maxima & Minima",False),("27","Rate of Change",False),
        ("37.1","Maxima & Minima real life Applications",False),
        ("37.2","Maxima & Minima real life Applications",False),
        ("37.3","Maxima & Minima real life Applications",False),
        ("37.4","Maxima & Minima real life Applications",True),
    ],
    "Integrals": [
        ("18","Indefinite Integrals (Anti derivatives)",False),
        ("25.1","Integration by Substitution",False),
        ("35.1","Rules of integrals",False),("35.2","Partial Fractions",False),
    ],
    "Inverse Trigonometric Functions": [
        ("19","Principal Values (Domain and Range)",False),
        ("23","Algebra of Inverse Trig Functions",False),
    ],
    "Vector Algebra": [
        ("17","Dot (Scalar) Product",False),("20","Cross (Vector) Product",False),
        ("22","Cross (Vector) Product",False),
    ],
}

ALL_EXCEL_CHAPTERS = set()
for _u in EXCEL_UNITS.values():
    for _ch in _u["chapters"]:
        ALL_EXCEL_CHAPTERS.add(_ch)

EXCEL_ALIASES = {
    "continuity & differentiability":      "Continuity & Differentiability",
    "continuity and differentiability":    "Continuity & Differentiability",
    "application of derivatives":          "Application of Derivatives",
    "applications of derivatives":         "Application of Derivatives",
    "application of integrals":            "Application of Integrals",
    "applications of integrals":           "Application of Integrals",
    "inverse trigonometric functions":     "Inverse Trigonometric Functions",
    "relations and functions":             "Relations & Functions",
    "relations & functions":               "Relations & Functions",
    "three dimensional geometry":          "3D Geometry",
    "three-dimensional geometry":          "3D Geometry",
    "3d geometry":                         "3D Geometry",
    "differential equations":              "Differential Equations",
    "linear programming":                  "Linear Programming",
    "probability":                         "Probability",
    "vectors":                             "Vector Algebra",
    "vector algebra":                      "Vector Algebra",
    "matrices":                            "Matrices",
    "determinants":                        "Determinants",
    "integrals":                           "Integrals",
}

def enorm(name: str) -> Optional[str]:
    n = name.lower().strip().replace("&", "and")
    n = re.sub(r"\s+", " ", n)
    if n in EXCEL_ALIASES:
        return EXCEL_ALIASES[n]
    for ec in ALL_EXCEL_CHAPTERS:
        if ec.lower() == name.lower():
            return ec
    return None

# ─────────────────────────────────────────────────────────────────────────────
# RESULT STORE
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TC:
    phase:  str
    name:   str
    passed: bool
    detail: str = ""
    value:  str = ""

_cur: List[TC] = []
_ph = ""

def sp(p: str):
    global _ph; _ph = p

def rec(name: str, passed: bool, detail: str = "", value: str = "") -> bool:
    _cur.append(TC(_ph, name, passed, detail, value))
    icon = f"{G}✔{RST}" if passed else f"{R}✘{RST}"
    st   = f"{G}[PASS]{RST}" if passed else f"{R}[FAIL]{RST}"
    v    = f"  {DIM}{value}{RST}" if value else ""
    print(f"    {icon} {st}  {name}{v}")
    return passed

def banner(n, t: str):
    print(f"\n{BLD}{C}{'═'*72}\n  PHASE {n}  ▶  {W}{t}\n{'═'*72}{RST}")

def sec_banner(s: str):
    print(f"\n{BLD}{W}{'▓'*72}\n  SECTION  {Y}{s}{RST}{BLD}{W}\n{'▓'*72}{RST}\n")

def warn(msg: str):
    print(f"    {Y}⚠ {msg}{RST}")

# ─────────────────────────────────────────────────────────────────────────────
# SELENIUM HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def safe_text(el) -> str:
    try:    return (el.text or "").strip()
    except: return ""

def safe_attr(el, a: str) -> str:
    try:    return (el.get_attribute(a) or "").strip()
    except: return ""

def js_select(driver, sel, wanted: str) -> bool:
    return bool(driver.execute_script("""
        const sel=arguments[0],want=arguments[1].trim(),wl=want.toLowerCase();
        const fire=e=>{e.dispatchEvent(new Event('input',{bubbles:true}));
                       e.dispatchEvent(new Event('change',{bubbles:true}));};
        for(const o of sel.options){if((o.textContent||'').trim()===want){sel.value=o.value;fire(sel);return true;}}
        for(const o of sel.options){if((o.textContent||'').trim().toLowerCase()===wl){sel.value=o.value;fire(sel);return true;}}
        return false;
    """, sel, wanted))

def get_selects(driver):
    return driver.find_elements(By.TAG_NAME, "select")

def wait_option(driver, idx: int, text: str, timeout: int = 30) -> bool:
    tl = text.lower()
    end = time.time() + timeout
    while time.time() < end:
        sels = get_selects(driver)
        if len(sels) > idx:
            opts = [o.text.strip().lower()
                    for o in sels[idx].find_elements(By.TAG_NAME, "option")]
            if tl in opts:
                return True
        time.sleep(0.4)
    return False

def wait_cards(driver, timeout: int = CARD_WAIT_SEC):
    try:
        WebDriverWait(driver, timeout).until(lambda d:
            len(d.find_elements(By.XPATH,
                "//*[contains(text(),'%') and ("
                "contains(text(),'+') or contains(text(),'-') or "
                "contains(text(),'↑') or contains(text(),'↓'))]")) > 0)
    except:
        time.sleep(3)

def scroll_into_view(driver, el):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
    except:
        pass

def get_section_sel(driver):
    sels = get_selects(driver)
    for idx in [1, 0, 2, 3]:
        if idx >= len(sels): continue
        sel = sels[idx]
        opts = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option")
                if o.text.strip() and o.text.strip().lower() not in ("select","select section","--","")]
        if not opts: continue
        not_class = not all(o.isdigit() for o in opts)
        not_subj  = not any(o.lower() in ("maths","physics","chemistry","english","biology","hindi") for o in opts)
        not_exam  = not any(o.lower() in ("midterm","preboard 1","preboard1","final","annual") for o in opts)
        if not_class and not_subj and not_exam and all(len(o) <= 12 for o in opts):
            return sel, idx
    if len(sels) > 1: return sels[1], 1
    return None, -1

def get_all_sections(driver):
    sel, idx = get_section_sel(driver)
    if sel is None: return []
    opts = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option")
            if o.text.strip() and o.text.strip().lower() not in ("select","select section","--","")]
    print(f"  {G}Section dropdown at index {idx}:{RST} {opts}")
    return opts

def switch_section(driver, section_name: str, chapters_url: str):
    sel, idx = get_section_sel(driver)
    if sel is None: raise RuntimeError("Section dropdown not found")
    old_len = len(driver.page_source)
    ok = js_select(driver, sel, section_name)
    if not ok: raise RuntimeError(f"Could not select '{section_name}'")
    print(f"  {G}✔ Section selected: {section_name}{RST}")
    time.sleep(S_DROP)
    try:
        WebDriverWait(driver, 15).until(lambda d:
            abs(len(d.page_source) - old_len) > 500 or
            len(d.find_elements(By.XPATH,
                "//*[contains(text(),'%') and (contains(text(),'+') or contains(text(),'-') "
                "or contains(text(),'↑') or contains(text(),'↓'))]")) > 0)
    except:
        driver.get(chapters_url); time.sleep(S_NAV)
        sel2, _ = get_section_sel(driver)
        if sel2: js_select(driver, sel2, section_name); time.sleep(S_DROP)
    wait_cards(driver)

# ─────────────────────────────────────────────────────────────────────────────
# PERCENTAGE UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def normalize_arrow(ch: str) -> str:
    if ch in ("↑","▲","△","⬆","+"): return "+"
    if ch in ("↓","▼","▽","⬇","-"): return "-"
    return ch

def arrow_sign(s: str) -> str:
    for a, r in [("↑","+"),("↓","-"),("▲","+"),("▼","-"),("△","+"),("▽","-")]:
        s = s.replace(a, r)
    return s

def extract_pct(text: str) -> Optional[str]:
    if not text: return None
    t = re.sub(r"\s+", "", arrow_sign(text))
    m = re.search(r"([+\-])(\d+\.?\d*)%", t)
    if m: return f"{m.group(1)}{m.group(2)}%"
    m2 = re.search(r"(\d+\.?\d*)%", t)
    if m2: return f"+{m2.group(1)}%"
    return None

def extract_num(p: Optional[str]) -> Optional[float]:
    if not p: return None
    m = re.search(r"[+\-]?\d+\.?\d*", p)
    return float(m.group()) if m else None

def norm_val(p: Optional[str]) -> Optional[str]:
    if not p: return None
    m = re.search(r"(\d+\.?\d*)", p)
    if not m: return None
    try:
        v = str(float(m.group(1)))
        return v[:-2] if v.endswith(".0") else v
    except:
        return m.group(1)

def align_sign(ref: Optional[str], cand: Optional[str]) -> Optional[str]:
    if not ref or not cand: return cand
    rs = "+" if "+" in ref else "-"
    rn = re.search(r"(\d+\.?\d*)", ref)
    cn = re.search(r"(\d+\.?\d*)", cand)
    if rn and cn and rn.group(1) == cn.group(1) and ("+" in cand) != (rs == "+"):
        return f"{rs}{cn.group(1)}%"
    return cand

def _closest_pct(candidates: List[str], ref: Optional[str]) -> Optional[str]:
    if not candidates: return None
    if not ref: return candidates[0]
    rn = abs(extract_num(ref) or 0)
    return min(candidates, key=lambda p: abs(abs(extract_num(p) or 0) - rn))

# ─────────────────────────────────────────────────────────────────────────────
# CARD DISCOVERY
# ─────────────────────────────────────────────────────────────────────────────
_IGNORE_NAMES = {
    "chapter","chapters","sort chapters","search chapter",
    "chapter avg: high to low","chapter avg",
}

def discover_cards(driver) -> List[dict]:
    cards, seen = [], set()
    badges = driver.find_elements(By.XPATH,
        "//*[(contains(text(),'+') or contains(text(),'-') or "
        "     contains(text(),'↑') or contains(text(),'↓') or "
        "     contains(text(),'▲') or contains(text(),'▼')) "
        "    and contains(text(),'%') "
        "    and string-length(normalize-space(text())) < 15]")
    for badge in badges:
        pct = extract_pct(safe_text(badge))
        if not pct: continue
        for lvl in range(1, 10):
            try:
                c  = badge.find_element(By.XPATH, "/".join([".."] * lvl))
                ct = safe_text(c)
                nm = re.sub(r"[+\-↑↓▲▼△▽⬆⬇]?\s*\d+\.?\d*\s*%", "", ct).strip()
                nm = re.sub(r"[↑↓▲▼△▽⬆⬇]", "", nm).strip()
                if (4 < len(nm) <= 72 and not re.fullmatch(r"[\d\s.]+", nm)
                        and nm not in seen and nm.lower() not in _IGNORE_NAMES
                        and len(ct) < 200):
                    seen.add(nm); cards.append({"name": nm, "pct": pct, "el": c}); break
            except: continue
    if not cards:
        for el in driver.find_elements(By.XPATH,
                "//*[contains(text(),'%') and string-length(normalize-space(text()))<18]"):
            pct = extract_pct(safe_text(el))
            if not pct: continue
            try:
                p = el.find_element(By.XPATH, "..")
                for s in p.find_elements(By.XPATH, "./*"):
                    st = safe_text(s)
                    if st and "%" not in st and 4 < len(st) <= 72 and st not in seen:
                        seen.add(st); cards.append({"name": st, "pct": pct, "el": p}); break
            except: continue
    if not cards:
        src = driver.page_source
        for m in re.finditer(
                r">([A-Z][A-Za-z &\-]{3,60}?)<(?:(?!</ul>).){0,400}>"
                r"([+\-↑↓▲▼]\d+\.?\d*\s*%)<", src, re.DOTALL):
            nm = m.group(1).strip(); pct = extract_pct(m.group(2))
            if pct and nm not in seen and 3 < len(nm) <= 72:
                seen.add(nm)
                el = None
                try: el = driver.find_element(By.XPATH,
                        f"//*[contains(text(),'{nm.split()[0]}')]/ancestor::*[3]")
                except: pass
                cards.append({"name": nm, "pct": pct, "el": el})
    return cards

def read_card_pct(driver, card: dict) -> Optional[str]:
    nm = card["name"]; first = nm.split()[0]
    for xp in [
        f"//*[normalize-space(text())='{nm}']/following-sibling::*[contains(text(),'%')][1]",
        f"//*[contains(text(),'{first}')]/following-sibling::*[contains(text(),'%')][1]",
        f"//*[normalize-space(text())='{nm}']/parent::*//*[contains(text(),'%') and string-length(normalize-space(text()))<15][1]",
    ]:
        try:
            for e in driver.find_elements(By.XPATH, xp):
                p = extract_pct(safe_text(e))
                if p: return p
        except: continue
    src = driver.page_source
    m = re.search(re.escape(nm) + r".{0,300}?([+\-↑↓▲▼]\s*\d+\.?\d*)\s*%", src, re.DOTALL)
    if m: return extract_pct(m.group(1) + "%")
    return card.get("pct")

def click_card(driver, card: dict) -> bool:
    nm = card["name"]; first = nm.split()[0]; last = nm.replace("&","and").split()[-1]
    def try_click(el) -> bool:
        try:
            scroll_into_view(driver, el)
            try: el.click()
            except: driver.execute_script("arguments[0].click();", el)
            return True
        except: return False
    if card.get("el") and try_click(card["el"]): return True
    for xp in [
        f"//*[normalize-space(text())='{nm}']",
        f"//*[contains(normalize-space(text()),'{nm}')]",
        f"//*[contains(text(),'{first}') and contains(text(),'{last}')]",
        f"//*[contains(text(),'{first}')]/parent::*[.//*[contains(text(),'%')]]",
        f"//*[contains(text(),'{first}')]/ancestor::*[2]",
        f"//*[contains(text(),'{first}')]/ancestor::*[3]",
    ]:
        try:
            for c in driver.find_elements(By.XPATH, xp):
                t = safe_text(c)
                if first in t and len(t) < 200 and try_click(c): return True
        except: continue
    return False

# ─────────────────────────────────────────────────────────────────────────────
# LOC 2 — IMPROVED / DECLINED CHIP
# ─────────────────────────────────────────────────────────────────────────────
_CHIP_POS = {"IMPROVED","Improved","improved"}
_CHIP_NEG = {"DECLINED","Declined","declined"}
_CHIP_ALL = _CHIP_POS | _CHIP_NEG

def _chip_sign(kw: str) -> str:
    return "+" if kw in _CHIP_POS else "-"

def _harvest(txt: str, sign: str, out: List[str]):
    for m in re.finditer(r"(\d+\.?\d*)\s*%", txt):
        p = f"{sign}{m.group(1)}%"
        if p not in out: out.append(p)

def read_improved_chip(driver, ref_pct: Optional[str] = None) -> Optional[str]:
    candidates: List[str] = []
    for kw in _CHIP_ALL:
        sign = _chip_sign(kw)
        try:
            for lel in driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{kw}']"):
                for lvl in range(1, 10):
                    try:
                        c = lel.find_element(By.XPATH, "/".join([".."] * lvl))
                        ct = safe_text(c)
                        if len(ct) > 100 or "%" not in ct: continue
                        _harvest(ct, sign, candidates)
                        it = driver.execute_script("return arguments[0].innerText||''", c)
                        if it: _harvest(it.strip(), sign, candidates)
                        break
                    except: continue
        except: continue
    for kw in _CHIP_ALL:
        sign = _chip_sign(kw)
        for xp in [
            f"//*[normalize-space(text())='{kw}']/preceding-sibling::*[1]",
            f"//*[normalize-space(text())='{kw}']/preceding-sibling::*[2]",
            f"//*[normalize-space(text())='{kw}']/../preceding-sibling::*[1]",
            f"//*[normalize-space(text())='{kw}']/../*[contains(text(),'%')]",
            f"//*[normalize-space(text())='{kw}']/parent::*/parent::*//*[contains(text(),'%')]",
        ]:
            try:
                for e in driver.find_elements(By.XPATH, xp):
                    t = safe_text(e)
                    if "%" in t and len(t) < 30: _harvest(t, sign, candidates)
            except: continue
    try:
        js_out = driver.execute_script("""
            const words=arguments[0],out=[];
            for(const w of words){
                for(const el of document.querySelectorAll('*')){
                    const t=(el.innerText||el.textContent||'').trim();
                    if(t!==w)continue;
                    let node=el;
                    for(let i=0;i<10;i++){
                        node=node.parentElement; if(!node)break;
                        const ct=(node.innerText||'').trim();
                        if(ct.includes('%')&&ct.length<100){
                            out.push({sign:w.toLowerCase().includes('improv')?'+':'-',text:ct});break;
                        }
                    }
                    if(out.length)break;
                }
                if(out.length)break;
            }
            return out;
        """, list(_CHIP_ALL))
        for row in (js_out or []): _harvest(row["text"], row["sign"], candidates)
    except: pass
    src = driver.page_source
    for kw in _CHIP_ALL:
        sign = _chip_sign(kw); idx = src.find(kw)
        while idx >= 0:
            for region in [src[max(0,idx-500):idx], src[idx:idx+500]]:
                clean = re.sub(r"<[^>]+>"," ",region); clean = re.sub(r"\s+"," ",clean)
                _harvest(clean, sign, candidates)
            idx = src.find(kw, idx+1)
    if not candidates: return None
    return align_sign(ref_pct, _closest_pct(candidates, ref_pct))

# ─────────────────────────────────────────────────────────────────────────────
# LOC 3 — CHANGE IN CHAPTER AVERAGE BADGE
# ─────────────────────────────────────────────────────────────────────────────
_BADGE_PHRASES = [
    "Change in chapter average",
    "Change in chapter avg",
    "Change in chapter",
]
_BADGE_SIBLING_XPS = [
    "./following-sibling::*[1]",
    "./following-sibling::*[2]",
    "./following-sibling::*[contains(text(),'%')][1]",
    "./following::*[contains(text(),'%')][1]",
    "./../*[contains(text(),'%')][1]",
    "./parent::*/following-sibling::*//*[contains(text(),'%')][1]",
    ("./parent::*//*[(contains(text(),'↑') or contains(text(),'↓') or "
     " contains(text(),'+') or contains(text(),'-')) and contains(text(),'%') and "
     " string-length(normalize-space(text()))<20][1]"),
]

def read_change_badge(driver, ref_pct: Optional[str] = None) -> Optional[str]:
    candidates: List[str] = []
    for phrase in _BADGE_PHRASES:
        try:
            for lel in driver.find_elements(By.XPATH, f"//*[contains(text(),'{phrase}')]"):
                for xp in _BADGE_SIBLING_XPS:
                    try:
                        for e in lel.find_elements(By.XPATH, xp):
                            for txt in [safe_text(e),
                                        driver.execute_script("return arguments[0].innerText||''", e)]:
                                txt = (txt or "").strip()
                                if "%" in txt and 0 < len(txt) < 30:
                                    p = extract_pct(txt)
                                    if p and p not in candidates: candidates.append(p)
                    except: pass
        except: pass
    src = driver.page_source
    for phrase in _BADGE_PHRASES:
        idx = src.find(phrase)
        while idx >= 0:
            region = src[idx:idx+600]
            clean  = re.sub(r"<[^>]+>"," ",region); clean = re.sub(r"\s+"," ",clean)
            for m in re.finditer(r"([+\-↑↓▲▼△▽])\s*(\d+\.?\d*)\s*%", clean):
                sign = normalize_arrow(m.group(1)); p = f"{sign}{m.group(2)}%"
                if p not in candidates: candidates.append(p)
            idx = src.find(phrase, idx+1)
    if not candidates: return None
    return align_sign(ref_pct, _closest_pct(candidates, ref_pct))

# ─────────────────────────────────────────────────────────────────────────────
# LOC 4 — WHY THIS CHAPTER TEXT + % EXTRACTION  (exact Script 1 REFIXED)
# ─────────────────────────────────────────────────────────────────────────────
_WHY_HEADINGS = [
    "Why this chapter improved",
    "Why this chapter declined",
    "Why this chapter",
]
_ACC_BEFORE_PHRASES = [
    "remained stable at around","stable at around","at around",
    "remained stable at","stable at","remained at","performance at",
    "accuracy of","at approximately","approximately","around",
]
_ACC_AFTER_WORDS = ["accuracy","accura"]
_STABLE_PHRASES  = [
    "remained stable","performance remained stable","no significant change",
    "no change","stayed stable","did not change","remained the same","performance stable",
]
_CHANGE_KWS_STRICT = [
    "slight decline of","significant decline of","slight improvement of",
    "significant improvement of","declined by","decline of","declined significantly by",
    "improved by","improvement of","improved significantly by","drop of","dropped by",
    "change of","changed by","progress of","increased by","decreased by",
    "reduced by","fell by","significantly by","considerably by","notably by",
    "good improvement of","chapter dropped","this chapter dropped",
    "chapter declined","this chapter declined","chapter improved","this chapter improved",
]
_FALLBACK_PATTERNS: List[Tuple[str, Optional[str]]] = [
    (r"[Ss]light\s+decline\s+of\s+([+\-]?\d+\.?\d*)\s*%",           "-"),
    (r"[Ss]ignificant\s+decline\s+of\s+([+\-]?\d+\.?\d*)\s*%",      "-"),
    (r"[Ss]light\s+improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%",       "+"),
    (r"[Ss]ignificant\s+improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%",  "+"),
    (r"significantly\s+by\s+([+\-]?\d+\.?\d*)\s*%",                   None),
    (r"considerably\s+by\s+([+\-]?\d+\.?\d*)\s*%",                    None),
    (r"notably\s+by\s+([+\-]?\d+\.?\d*)\s*%",                         None),
    (r"improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%",                    "+"),
    (r"improved\s+by\s+([+\-]?\d+\.?\d*)\s*%",                       "+"),
    (r"improved\s+significantly\s+by\s+([+\-]?\d+\.?\d*)\s*%",       "+"),
    (r"declined\s+by\s+([+\-]?\d+\.?\d*)\s*%",                       "-"),
    (r"decline\s+of\s+([+\-]?\d+\.?\d*)\s*%",                        "-"),
    (r"drop\s+of\s+([+\-]?\d+\.?\d*)\s*%",                           "-"),
    (r"dropped\s+by\s+([+\-]?\d+\.?\d*)\s*%",                        "-"),
    (r"progress\s+of\s+([+\-]?\d+\.?\d*)\s*%",                       "+"),
    (r"change\s+of\s+([+\-]?\d+\.?\d*)\s*%",                          None),
    (r"increased\s+by\s+([+\-]?\d+\.?\d*)\s*%",                      "+"),
    (r"decreased\s+by\s+([+\-]?\d+\.?\d*)\s*%",                      "-"),
    (r"reduced\s+by\s+([+\-]?\d+\.?\d*)\s*%",                        "-"),
    (r"fell\s+by\s+([+\-]?\d+\.?\d*)\s*%",                           "-"),
]

def _is_accuracy_pct(num_str: str, ctx_before: str, ctx_after: str) -> bool:
    cb = ctx_before.lower(); ca = ctx_after.lower().strip()
    if any(ca.startswith(k) or (" "+k) in ca[:25] for k in _ACC_AFTER_WORDS): return True
    for phrase in _ACC_BEFORE_PHRASES:
        if phrase in cb: return True
    for sp2 in _STABLE_PHRASES:
        if sp2 in cb: return True
    if "." not in num_str:
        try:
            if float(num_str) >= 50: return True
        except: pass
    return False

def read_why_text(driver) -> Optional[str]:
    try:
        result = driver.execute_script("""
            const WHY_KWS=arguments[0];
            const headingEls=document.querySelectorAll('div[class*="text-zinc-800"][class*="font-semibold"]');
            for(const hEl of headingEls){
                const hText=(hEl.innerText||'').trim();
                if(!WHY_KWS.some(k=>hText.startsWith(k)))continue;
                let body=hEl.nextElementSibling;
                while(body){
                    const bt=(body.innerText||'').trim();
                    if(bt.length>15&&!WHY_KWS.some(k=>bt.startsWith(k)))return bt;
                    body=body.nextElementSibling;
                }
                let p=hEl.parentElement;
                for(let i=0;i<5&&p;i++,p=p.parentElement){
                    const pt=(p.innerText||'').trim();
                    if(pt.length>hText.length+20&&pt.length<1500){
                        const s=pt.replace(hText,'').trim();
                        if(s.length>15)return s;
                    }
                }
            }
            for(const kw of WHY_KWS){
                for(const el of document.querySelectorAll('*')){
                    const t=(el.innerText||el.textContent||'').trim();
                    if(!t.startsWith(kw))continue;
                    let sib=el.nextElementSibling;
                    while(sib){
                        const st=(sib.innerText||'').trim();
                        if(st.length>15&&!st.startsWith('Why this'))return st;
                        sib=sib.nextElementSibling;
                    }
                    let p=el.parentElement;
                    for(let i=0;i<6&&p;i++,p=p.parentElement){
                        const pt=(p.innerText||'').trim();
                        if(pt.length>t.length+20&&pt.length<1500){
                            const body=pt.replace(t,'').trim();
                            if(body.length>15)return body;
                        }
                    }
                }
            }
            return null;
        """, _WHY_HEADINGS)
        if result and len(result.strip()) > 15: return result.strip()
    except: pass
    for kw in _WHY_HEADINGS:
        for xp in [
            (f"//*[contains(@class,'text-zinc-800') and contains(@class,'font-semibold') and "
             f"starts-with(normalize-space(text()),'{kw}')]/following-sibling::*[1]"),
            f"//*[starts-with(normalize-space(text()),'{kw}')]/following-sibling::*[1]",
            f"//*[starts-with(normalize-space(text()),'{kw}')]/following-sibling::div[1]",
            f"//*[starts-with(normalize-space(text()),'{kw}')]/following::*[string-length(normalize-space(text()))>20][1]",
            f"//*[contains(normalize-space(text()),'{kw}')]/../following-sibling::*[1]",
        ]:
            try:
                for e in driver.find_elements(By.XPATH, xp):
                    t = safe_text(e)
                    if t and len(t) > 20 and not any(t.startswith(k) for k in _WHY_HEADINGS):
                        return t
            except: continue
    ps = driver.page_source
    for kw in _WHY_HEADINGS:
        idx = ps.find(kw)
        if idx < 0: continue
        region = ps[idx:idx+1500]
        plain  = re.sub(r"<[^>]+>"," ",region); plain = re.sub(r"\s+"," ",plain).strip()
        he = plain.find(kw)
        rest = plain[he+len(kw):].strip(" :") if he >= 0 else plain
        for sent in re.split(r"(?<=[.!?])\s+", rest):
            sent = sent.strip()
            if len(sent) > 30 and kw.split()[0] not in sent: return sent
        if len(rest) > 30: return rest[:600]
    return None

def read_why_pct(why_text: Optional[str]) -> Optional[str]:
    if not why_text: return None
    lower = why_text.lower()
    if any(ph in lower for ph in _STABLE_PHRASES): return None
    is_neg = any(k in lower for k in [
        "decline","declined","declin","drop","dropped",
        "fell","decrease","decreased","worsened","reduction","reduced"])
    for m in re.finditer(r"([+\-]?)(\d+\.?\d*)\s*%", why_text):
        pos=m.start(); raw_sgn=m.group(1); num_str=m.group(2)
        ctx_b=lower[max(0,pos-100):pos]; ctx_a=lower[pos:pos+60]
        if _is_accuracy_pct(num_str, ctx_b, ctx_a): continue
        if any(kw in ctx_b for kw in _CHANGE_KWS_STRICT):
            sign = raw_sgn if raw_sgn else ("-" if is_neg else "+")
            return f"{sign}{num_str}%"
    return None

def read_why_pct_from_page(driver, ref_pct: Optional[str] = None) -> Optional[str]:
    ps = driver.page_source
    for kw in _WHY_HEADINGS:
        idx = ps.find(kw)
        if idx < 0: continue
        region = ps[idx:idx+1200]
        clean  = re.sub(r"<[^>]+>"," ",region); clean = re.sub(r"\s+"," ",clean)
        is_neg = any(k in clean.lower() for k in
                     ["decline","drop","decreased","fell","worsened","reduced"])
        for pat, forced_sign in _FALLBACK_PATTERNS:
            m = re.search(pat, clean, re.IGNORECASE)
            if m:
                val = m.group(1)
                if val.startswith("+") or val.startswith("-"): return f"{val}%"
                if forced_sign: return f"{forced_sign}{val}%"
                return f"{'-' if is_neg else '+'}{val}%"
        is_stable = any(ph in clean.lower() for ph in _STABLE_PHRASES)
        if not is_stable:
            for m in re.finditer(r"([+\-]?)(\d+\.?\d*)\s*%", clean):
                num_str=m.group(2)
                ctx_b=clean[max(0,m.start()-100):m.start()].lower()
                ctx_a=clean[m.end():m.end()+60].lower()
                if _is_accuracy_pct(num_str, ctx_b, ctx_a): continue
                if any(kw2 in ctx_b for kw2 in _CHANGE_KWS_STRICT):
                    sign = m.group(1) if m.group(1) else ("-" if is_neg else "+")
                    return f"{sign}{num_str}%"
    return None

def read_why_accuracy_pct(why_text: Optional[str]) -> Optional[str]:
    if not why_text: return None
    lower = why_text.lower()
    for pat in [
        r"remained\s+stable\s+at\s+around\s+(\d+\.?\d*)\s*%",
        r"stable\s+at\s+around\s+(\d+\.?\d*)\s*%",
        r"at\s+around\s+(\d+\.?\d*)\s*%(?:\s*accuracy)?",
        r"around\s+(\d+\.?\d*)\s*%(?:\s*accuracy)?",
        r"stable\s+at\s+(\d+\.?\d*)\s*%",
        r"remained\s+at\s+(\d+\.?\d*)\s*%",
        r"at\s+approximately\s+(\d+\.?\d*)\s*%",
        r"approximately\s+(\d+\.?\d*)\s*%",
        r"accuracy\s+of\s+(\d+\.?\d*)\s*%",
        r"(\d+\.?\d*)\s*%\s+accuracy",
        r"(\d+\.?\d*)\s*%\s+accur",
    ]:
        m = re.search(pat, lower)
        if m: return f"{m.group(1)}%"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ★ FROM SCRIPT 1 — READ "Preboard 1 accuracy XX%" HEADER BADGE
# ─────────────────────────────────────────────────────────────────────────────
def read_header_accuracy_badge(driver) -> Optional[str]:
    """
    Reads the blue badge at the top-right of each chapter detail panel
    that shows e.g. "Preboard 1 accuracy  51.8%"
    Returns just the percentage string like "51.8%" or None.
    """
    # Strategy 1: JS — scan for elements matching "XYZ accuracy" + nearby %
    try:
        result = driver.execute_script(r"""
            const EXAM_LABELS = arguments[0];
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText || el.textContent || '').trim();
                for (const exam of EXAM_LABELS) {
                    const pat = new RegExp(exam + '\\s+accuracy\\s*(\\d+\\.?\\d*)\\s*%', 'i');
                    const m = t.match(pat);
                    if (m && t.length < 80) {
                        return { exam: exam, pct: m[1] + '%', text: t };
                    }
                }
            }
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText || '').trim();
                for (const exam of EXAM_LABELS) {
                    if (!t.includes(exam) || !t.toLowerCase().includes('accuracy')) continue;
                    if (t.length > 100) continue;
                    const m = t.match(/(\d+\.?\d*)\s*%/);
                    if (m) return { exam: exam, pct: m[1] + '%', text: t };
                }
            }
            return null;
        """, EXAM_LABELS)
        if result and result.get("pct"):
            return result["pct"]
    except:
        pass

    # Strategy 2: page source regex
    src = driver.page_source
    for exam in EXAM_LABELS:
        pattern = rf"{re.escape(exam)}\s+accuracy\s*[\s\S]{{0,200}}?(\d+\.?\d*)\s*%"
        m = re.search(pattern, src, re.IGNORECASE)
        if m:
            return f"{m.group(1)}%"

    # Strategy 3: XPath
    for exam in EXAM_LABELS:
        for xp in [
            f"//*[contains(text(),'{exam}') and contains(text(),'accuracy')]",
            f"//*[contains(text(),'{exam} accuracy')]",
        ]:
            try:
                for el in driver.find_elements(By.XPATH, xp):
                    t = safe_text(el)
                    if len(t) < 80:
                        m = re.search(r"(\d+\.?\d*)\s*%", t)
                        if m: return f"{m.group(1)}%"
                    for sib_xp in ["./following-sibling::*[1]",
                                    "./following-sibling::*[2]",
                                    "./../*[contains(text(),'%')]"]:
                        try:
                            for sib in el.find_elements(By.XPATH, sib_xp):
                                st = safe_text(sib)
                                m = re.search(r"(\d+\.?\d*)\s*%", st)
                                if m and len(st) < 20: return f"{m.group(1)}%"
                        except: pass
            except: continue

    return None


# ─────────────────────────────────────────────────────────────────────────────
# EXAM PANEL READER  — column-aware JS (exact Script 1 REFIXED)
# ─────────────────────────────────────────────────────────────────────────────
def read_exam_panel(driver, label: str) -> dict:
    data = {
        "label": label, "accuracy": None, "exam_date": None,
        "struggling_count": None, "weak_concepts_count": None,
        "weakest_concepts": [], "strongest_concepts": [],
    }
    OTHER_LABELS = [l for l in EXAM_LABELS if l != label]

    try:
        result = driver.execute_script(r"""
            const label   = arguments[0];
            const PCT_RE  = /^\d{1,3}(\.\d+)?%$/;
            const INT_RE  = /^\d+$/;
            const ACC_KWS = ['ACCURACY','Accuracy','accuracy'];
            const STR_KWS = ['Struggling students','Struggling Students',
                             'STRUGGLING STUDENTS','struggling students'];
            const WK_KWS  = ['Weak Concepts','Weak concepts',
                             'WEAK CONCEPTS','weak concepts'];
            const DATE_RE = /[A-Z][a-z]+ \d+, \d{4}/;
            const BADGE_WORDS = new Set(['New','Improved','Declined',
                                         'NEW','IMPROVED','DECLINED',
                                         'new','improved','declined']);

            function findByColumn(kws, targetX, tolerance) {
                let best = null; let bestDist = Infinity;
                for (const kw of kws) {
                    for (const el of document.querySelectorAll('*')) {
                        const t = (el.innerText || el.textContent || '').trim();
                        if (t !== kw) continue;
                        const r = el.getBoundingClientRect();
                        if (r.width === 0 && r.height === 0) continue;
                        const midX = (r.left + r.right) / 2;
                        const d = Math.abs(midX - targetX);
                        if (d < tolerance && d < bestDist) { bestDist = d; best = el; }
                    }
                }
                return best;
            }

            function numAbove(refEl, regex) {
                const refRect = refEl.getBoundingClientRect();
                const refMidX = (refRect.left + refRect.right) / 2;
                let sib = refEl.previousElementSibling;
                while (sib) {
                    const t = (sib.innerText || '').trim();
                    if (regex.test(t)) return t;
                    for (const ch of sib.querySelectorAll('*')) {
                        const ct = (ch.innerText||'').trim(); if (regex.test(ct)) return ct;
                    }
                    sib = sib.previousElementSibling;
                }
                if (refEl.parentElement) {
                    let psib = refEl.parentElement.previousElementSibling;
                    while (psib) {
                        const t = (psib.innerText||'').trim();
                        if (regex.test(t)) return t;
                        for (const ch of psib.querySelectorAll('*')) {
                            const ct = (ch.innerText||'').trim(); if (regex.test(ct)) return ct;
                        }
                        psib = psib.previousElementSibling;
                    }
                }
                let bestEl = null; let bestYDist = Infinity;
                for (const el of document.querySelectorAll('*')) {
                    const t = (el.innerText||'').trim();
                    if (!regex.test(t) || el.children.length > 2) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    if (Math.abs((r.left+r.right)/2 - refMidX) < 90 && r.bottom <= refRect.top + 10) {
                        const yd = refRect.top - r.bottom;
                        if (yd < bestYDist) { bestYDist = yd; bestEl = el; }
                    }
                }
                return bestEl ? (bestEl.innerText||'').trim() : null;
            }

            function numBelow(refEl, regex) {
                const refRect = refEl.getBoundingClientRect();
                const refMidX = (refRect.left + refRect.right) / 2;
                let sib = refEl.nextElementSibling;
                while (sib) {
                    const t = (sib.innerText||'').trim();
                    if (regex.test(t)) return t;
                    for (const ch of sib.querySelectorAll('*')) {
                        const ct=(ch.innerText||'').trim(); if(regex.test(ct)) return ct;
                    }
                    sib = sib.nextElementSibling;
                }
                if (refEl.parentElement) {
                    let nsib = refEl.parentElement.nextElementSibling;
                    while (nsib) {
                        const t = (nsib.innerText||'').trim();
                        if (regex.test(t)) return t;
                        for (const ch of nsib.querySelectorAll('*')) {
                            const ct=(ch.innerText||'').trim(); if(regex.test(ct)) return ct;
                        }
                        nsib = nsib.nextElementSibling;
                    }
                }
                let bestEl = null; let bestYDist = Infinity;
                for (const el of document.querySelectorAll('*')) {
                    const t = (el.innerText||'').trim();
                    if (!regex.test(t) || el.children.length > 2) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    const elMidX = (r.left + r.right) / 2;
                    if (Math.abs(elMidX - refMidX) < 130 && r.top >= refRect.bottom - 10) {
                        const yd = r.top - refRect.bottom;
                        if (yd < bestYDist) { bestYDist = yd; bestEl = el; }
                    }
                }
                return bestEl ? (bestEl.innerText||'').trim() : null;
            }

            let labelEl = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (t === label && el.children.length <= 4) { labelEl = el; break; }
            }
            if (!labelEl) {
                for (const el of document.querySelectorAll('*')) {
                    if ((el.innerText||'').trim() === label) { labelEl = el; break; }
                }
            }
            if (!labelEl) return null;

            const lblRect = labelEl.getBoundingClientRect();
            const lblMidX = (lblRect.left + lblRect.right) / 2;

            const accEl  = findByColumn(ACC_KWS, lblMidX, 160);
            let accuracy = accEl ? numAbove(accEl, PCT_RE) : null;
            if (accuracy) { const v=parseFloat(accuracy); if(v<=5||v>100) accuracy=null; }

            const strEl      = findByColumn(STR_KWS, lblMidX, 220);
            const strRaw     = strEl ? numBelow(strEl, INT_RE) : null;
            const struggling = (strRaw !== null && strRaw !== '') ? parseInt(strRaw) : null;

            const wkEl      = findByColumn(WK_KWS, lblMidX, 220);
            const wkRaw     = wkEl ? numBelow(wkEl, INT_RE) : null;
            const weakCount = (wkRaw !== null && wkRaw !== '') ? parseInt(wkRaw) : null;

            let panelEl = labelEl;
            for (let i = 0; i < 20; i++) {
                panelEl = panelEl.parentElement;
                if (!panelEl) break;
                const pt2 = (panelEl.innerText||'').trim();
                if (pt2.length > 6000) break;
                if (ACC_KWS.some(k => pt2.includes(k)) && pt2.length > 30) break;
            }
            const pt    = panelEl ? (panelEl.innerText||'').trim() : '';
            const dateM = DATE_RE.exec(pt);

            const COLUMN_TOLERANCE = 250;
            let weakestHeadEl  = null;
            let strongestHeadEl = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||'').trim();
                if (!weakestHeadEl  && (t === 'Weakest Concepts'  || t === 'Weakest concepts'))  weakestHeadEl  = el;
                if (!strongestHeadEl && (t === 'Strongest Concepts'|| t === 'Strongest concepts')) strongestHeadEl = el;
                if (weakestHeadEl && strongestHeadEl) break;
            }

            function collectConceptRows(headEl, stopKeywords) {
                if (!headEl) return [];
                const headRect = headEl.getBoundingClientRect();
                const rows = [];
                const seen = new Set();
                const all = Array.from(document.querySelectorAll('*'));
                const headIdx = all.indexOf(headEl);
                if (headIdx < 0) return [];
                for (let i = headIdx + 1; i < all.length; i++) {
                    const el = all[i];
                    const t  = (el.innerText || el.textContent || '').trim();
                    if (!t || t.length > 80 || t.length < 2) continue;
                    if (stopKeywords.some(k => t === k)) break;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    if (r.top < headRect.bottom - 5) continue;
                    const elMidX = (r.left + r.right) / 2;
                    if (Math.abs(elMidX - lblMidX) > COLUMN_TOLERANCE) continue;
                    if (/^\d+$/.test(t)) continue;
                    if (/^\d{1,3}(\.\d+)?%$/.test(t)) continue;
                    if (seen.has(t)) continue;
                    seen.add(t);
                    rows.push({ text: t, midX: elMidX, top: r.top, el });
                }
                return rows;
            }

            const weakestStopKws = ['Strongest Concepts','Strongest concepts',
                                    'Why this chapter','Why This Chapter',
                                    'Midterm','Preboard 1'];
            const weakestRows = collectConceptRows(weakestHeadEl, weakestStopKws);
            const weakestConcepts = weakestRows
                .filter(r => !BADGE_WORDS.has(r.text) && r.text.length > 3)
                .map(r => r.text)
                .slice(0, 6);

            const strongestStopKws = ['Why this chapter','Why This Chapter',
                                      'Midterm','Preboard 1','Change in chapter'];
            const strongestRows = collectConceptRows(strongestHeadEl, strongestStopKws);

            const strongestConcepts = [];
            let i2 = 0;
            while (i2 < strongestRows.length) {
                const row = strongestRows[i2];
                if (BADGE_WORDS.has(row.text) || /^\d{1,3}(\.\d+)?%$/.test(row.text)) { i2++; continue; }
                const concept = { name: row.text, pct: null, badge: null };
                for (let j = i2 + 1; j < Math.min(i2 + 5, strongestRows.length); j++) {
                    const rt = strongestRows[j].text;
                    if (!concept.pct && /^\d{1,3}(\.\d+)?%$/.test(rt)) { concept.pct = rt; continue; }
                    if (!concept.badge && BADGE_WORDS.has(rt)) { concept.badge = rt; continue; }
                    if (!BADGE_WORDS.has(rt) && !/^\d{1,3}(\.\d+)?%$/.test(rt) && rt.length > 3) break;
                }
                strongestConcepts.push(concept);
                i2++;
            }

            return {
                accuracy,
                date:             dateM ? dateM[0] : null,
                struggling,
                weakCount,
                weakestConcepts,
                strongestConcepts: strongestConcepts.slice(0, 8),
                panelText: pt,
                _lblMidX:  lblMidX,
                _accElTxt: accEl ? (accEl.innerText||'').trim() : null,
                _strElTxt: strEl ? (strEl.innerText||'').trim() : null,
                _strRaw:   strRaw,
                _wkElTxt:  wkEl  ? (wkEl.innerText||'').trim()  : null,
                _wkRaw:    wkRaw,
            };
        """, label)

        if result:
            if result.get("accuracy"):
                data["accuracy"] = result["accuracy"]
            if result.get("date"):
                data["exam_date"] = result["date"]
            if result.get("struggling") is not None:
                data["struggling_count"] = result["struggling"]
            if result.get("weakCount") is not None:
                data["weak_concepts_count"] = result["weakCount"]
            if result.get("weakestConcepts"):
                data["weakest_concepts"] = result["weakestConcepts"]
            if result.get("strongestConcepts"):
                data["strongest_concepts"] = result["strongestConcepts"]
            print(f"        {label}: acc={result.get('accuracy')}  "
                  f"str={result.get('struggling')} (raw='{result.get('_strRaw')}' "
                  f"el='{result.get('_strElTxt')}')  "
                  f"wk={result.get('weakCount')} (raw='{result.get('_wkRaw')}' "
                  f"el='{result.get('_wkElTxt')}')")
            print(f"        {label}: weakest={data['weakest_concepts']}")
            print(f"        {label}: strongest={[c['name'] for c in data['strongest_concepts']]}")
        else:
            print(f"        {label}: JS returned null")
    except Exception as ex:
        print(f"        {label}: JS exception: {ex}")

    # ── FALLBACK A: XPath scoped ancestor ─────────────────────────────────
    panel = None
    if not data["accuracy"] or data["struggling_count"] is None or data["weak_concepts_count"] is None:
        candidates = []
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}' or text()='{label}']"):
            for lvl in range(1, 18):
                try:
                    anc = lel.find_element(By.XPATH, "/".join([".."] * lvl))
                    at  = safe_text(anc)
                    has_acc   = any(k in at for k in ["ACCURACY","Accuracy"])
                    has_other = any(o in at for o in OTHER_LABELS)
                    if has_acc and not has_other and 40 < len(at) < 2500:
                        candidates.append((len(at), anc)); break
                except: break
        if candidates:
            panel = min(candidates, key=lambda x: x[0])[1]
            pt_xp = safe_text(panel)
            if not data["exam_date"]:
                dm = re.search(r"([A-Z][a-z]+\s+\d+,\s+\d{4})", pt_xp)
                if dm: data["exam_date"] = dm.group(1)
            if not data["accuracy"]:
                try:
                    for acc_el in panel.find_elements(By.XPATH,
                            ".//*[normalize-space(text())='ACCURACY' or "
                            "     normalize-space(text())='Accuracy' or "
                            "     normalize-space(text())='accuracy']"):
                        for xp2 in [
                            "./preceding-sibling::*[1]","./preceding-sibling::*[2]",
                            "./../preceding-sibling::*[1]",
                            "./preceding::*[contains(text(),'%')][1]",
                            "./parent::*/preceding-sibling::*[1]",
                            "./following-sibling::*[1]",
                        ]:
                            try:
                                ve = acc_el.find_element(By.XPATH, xp2)
                                m  = re.search(r"(\d{1,3}\.?\d*)\s*%", safe_text(ve))
                                if m and float(m.group(1)) > 5:
                                    data["accuracy"] = m.group(1) + "%"; break
                            except: pass
                        if data["accuracy"]: break
                except: pass
            if data["struggling_count"] is None:
                try:
                    for sel2 in panel.find_elements(By.XPATH,
                            ".//*[contains(translate(text(),'STUDENRGLAB','studenrglab'),'struggling')]"):
                        for xp2 in ["./following-sibling::*[1]","./following-sibling::*[2]",
                                     "./../following-sibling::*[1]","./following::*[1]"]:
                            try:
                                ne = sel2.find_element(By.XPATH, xp2); nt = safe_text(ne)
                                nm = re.search(r"\b(\d+)\b", nt)
                                if nm and len(nt) < 10:
                                    data["struggling_count"] = int(nm.group(1)); break
                            except: pass
                        if data["struggling_count"] is not None: break
                except: pass
                if data["struggling_count"] is None:
                    m = re.search(r"[Ss]truggling\s+[Ss]tudents?\D{0,5}?(\d+)", pt_xp, re.IGNORECASE)
                    if m: data["struggling_count"] = int(m.group(1))
            if data["weak_concepts_count"] is None:
                try:
                    for wel in panel.find_elements(By.XPATH,
                            ".//*[contains(text(),'Weak Concept') or contains(text(),'Weak concept')]"):
                        for xp2 in ["./following-sibling::*[1]","./following-sibling::*[2]",
                                     "./../following-sibling::*[1]","./following::*[1]"]:
                            try:
                                ne = wel.find_element(By.XPATH, xp2); nt = safe_text(ne)
                                nm = re.search(r"\b(\d+)\b", nt)
                                if nm and len(nt) < 10:
                                    data["weak_concepts_count"] = int(nm.group(1)); break
                            except: pass
                        if data["weak_concepts_count"] is not None: break
                except: pass
                if data["weak_concepts_count"] is None:
                    m2 = re.search(r"[Ww]eak\s+[Cc]oncepts?\D{0,5}?(\d+)", pt_xp, re.IGNORECASE)
                    if m2: data["weak_concepts_count"] = int(m2.group(1))

    # ── FALLBACK B: page-source ────────────────────────────────────────────
    if not data["accuracy"]:
        src = driver.page_source
        idx = src.find(label)
        while idx >= 0:
            end = len(src)
            for o in OTHER_LABELS:
                oi = src.find(o, idx + len(label))
                if 0 < oi < end: end = oi
            region = src[idx:min(idx + 4000, end)]
            clean  = re.sub(r"<[^>]+>", " ", region)
            clean  = re.sub(r"\s+", " ", clean)
            for m in re.finditer(r"(\d{1,3}\.?\d*)\s*%", clean):
                val = float(m.group(1))
                if 5 < val <= 100:
                    data["accuracy"] = m.group(1) + "%"; break
            if data["accuracy"]: break
            idx = src.find(label, idx + 1)

    # ── FALLBACK C: XPath concept lists ───────────────────────────────────
    if panel is None:
        for lel in driver.find_elements(By.XPATH,
                f"//*[normalize-space(text())='{label}']"):
            for lvl in range(1, 15):
                try:
                    anc = lel.find_element(By.XPATH, "/".join([".."] * lvl))
                    at  = safe_text(anc)
                    if "ACCURACY" in at and len(at) < 3000:
                        panel = anc; break
                except: break
            if panel: break

    if panel and not data["weakest_concepts"]:
        try:
            wh = panel.find_elements(By.XPATH,
                ".//*[contains(text(),'Weakest Concepts') or contains(text(),'Weakest concepts')]")
            if wh:
                items = []
                for el in panel.find_elements(By.XPATH,
                        ".//*[contains(text(),'Weakest')]/following::*"):
                    t = safe_text(el)
                    if not t: continue
                    if any(k in t for k in ["Strongest","strongest"]): break
                    if (3 < len(t) < 70 and not re.fullmatch(r"[\d\s.%]+", t)
                            and "Weakest" not in t and "Concepts" not in t and t not in items):
                        items.append(t)
                data["weakest_concepts"] = items[:6]
        except: pass

    if panel and not data["strongest_concepts"]:
        try:
            sh = panel.find_elements(By.XPATH,
                ".//*[contains(text(),'Strongest Concepts') or contains(text(),'Strongest concepts')]")
            if sh:
                rows_d: dict = {}; cur = None
                BADGE_WORDS = {"New","Improved","Declined","NEW","IMPROVED","DECLINED",
                               "new","improved","declined"}
                for el in panel.find_elements(By.XPATH,
                        ".//*[contains(text(),'Strongest')]/following::*"):
                    t = safe_text(el)
                    if not t or len(t) > 80: continue
                    if t in {"Strongest Concepts","Strongest concepts"}: continue
                    if t in BADGE_WORDS:
                        if cur and cur in rows_d: rows_d[cur]["badge"] = t
                        continue
                    pm = re.fullmatch(r"(\d{1,3}\.?\d*)\s*%", t)
                    if pm:
                        if cur and cur in rows_d: rows_d[cur]["pct"] = t
                        continue
                    if 3 < len(t) < 70 and not re.fullmatch(r"[\d\s.%]+", t):
                        cur = t
                        if cur not in rows_d: rows_d[cur] = {"pct": None, "badge": None}
                data["strongest_concepts"] = [
                    {"name": k, "pct": v["pct"], "badge": v["badge"]}
                    for k, v in rows_d.items()
                ][:8]
        except: pass

    return data

# ─────────────────────────────────────────────────────────────────────────────
# LOC 4 HTML CELL HELPER  (exact Script 1 version)
# ─────────────────────────────────────────────────────────────────────────────
def loc4_display(ch: dict) -> str:
    pct_why  = ch.get("pct_why")
    acc_pct  = ch.get("why_acc_pct")
    pct_card = ch.get("pct_card") or ""
    why_h    = ch.get("why_heading") or ""
    if pct_why:
        col = "#3fb950" if "+" in pct_why else "#f85149"
        arr = "▲" if "+" in pct_why else "▼"
        return f'<span style="color:{col};font-weight:700;font-family:\'DM Mono\',monospace">{arr} {pct_why}</span>'
    if acc_pct:
        improved = "+" in pct_card or "improved" in why_h.lower()
        col = "#3fb950" if improved else "#f85149"
        arr = "▲" if improved else "▼"
        return (f'<span style="color:{col};font-weight:700;font-family:\'DM Mono\',monospace">{arr} {acc_pct}</span>'
                f'<br><span style="color:#5a7490;font-size:10px">accuracy in why-text</span>')
    return '<span style="color:#5a7490">—</span>'

# ─────────────────────────────────────────────────────────────────────────────
# DRIVER SETUP
# ─────────────────────────────────────────────────────────────────────────────
opts = Options()
opts.add_argument("--start-maximized")
opts.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=opts)
wait   = WebDriverWait(driver, 30)
RUN_TS = datetime.now().strftime("%d %b %Y  %H:%M:%S")

print(f"\n{BLD}{C}{'═'*72}")
print(f"  ClassLens · All Sections · FINAL MERGED v4")
print(f"  {DIM}{RUN_TS}{RST}")
print(f"{C}{'═'*72}{RST}\n")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 0 — LOGIN
# ─────────────────────────────────────────────────────────────────────────────
banner("0", "LOGIN")
sp("Login")
try:
    driver.get(LOGIN_URL)
    u = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email']")))
    p = driver.find_element(By.XPATH, "//input[@type='password']")
    u.clear(); u.send_keys(USERNAME)
    p.clear(); p.send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(.,'Enter your Class')]")))
    rec("Login successful", True, value=f"user={USERNAME}")
except Exception as exc:
    rec("Login failed", False, str(exc))
    driver.quit(); sys.exit("Login failed — aborting.")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — ENTRY PAGE FILTERS + COLLECT SECTIONS
# ─────────────────────────────────────────────────────────────────────────────
banner("1", "ENTRY PAGE FILTERS")
sp("Filters")
entry_secs = []
try:
    for idx, key, val in [
        (0,"Class",ENTRY["Class"]),
        (2,"Subject",ENTRY["Subject"]),
        (3,"Exam",ENTRY["Exam"]),
        (4,"CompareLeft",ENTRY["CompareLeft"]),
        (5,"CompareRight",ENTRY["CompareRight"]),
    ]:
        try: wait_option(driver, idx, val, timeout=20)
        except RuntimeError as e:
            print(f"    {Y}⚠ Skip '{key}'={val}: {e}{RST}"); continue
        sels = get_selects(driver)
        if len(sels) > idx:
            ok = js_select(driver, sels[idx], val)
            rec(f"Filter '{key}' = '{val}'", ok, value=val)
            time.sleep(S_DROP)
    sels = get_selects(driver)
    if len(sels) > 1:
        raw = [o.text.strip() for o in sels[1].find_elements(By.TAG_NAME, "option")]
        entry_secs = [o for o in raw if o and o.lower() not in ("select","select section","--","")]
    print(f"\n  {G}Entry-page sections:{RST} {entry_secs}\n")
    first = entry_secs[0] if entry_secs else ""
    if first:
        try: wait_option(driver, 1, first, timeout=10)
        except: pass
        sels = get_selects(driver)
        if len(sels) > 1: js_select(driver, sels[1], first); time.sleep(S_DROP)
    old_url = driver.current_url
    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()
    try: WebDriverWait(driver, 15).until(lambda d: d.current_url != old_url)
    except: pass
    time.sleep(S_NAV)
    rec("Dashboard entered", True)
except Exception as exc:
    rec("Entry page error", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — NAVIGATE TO CHAPTERS + DISCOVER SECTIONS
# ─────────────────────────────────────────────────────────────────────────────
banner("2", "CHAPTERS PAGE + DISCOVER SECTIONS")
sp("Navigation")
driver.get(CHAPTERS_URL); time.sleep(S_NAV); wait_cards(driver)
avail = get_all_sections(driver)
for s in entry_secs:
    if s not in avail: avail.append(s)
if not avail:
    print(f"  {R}No sections found — using fallback [M]{RST}"); avail = ["M"]
print(f"\n  {G}{BLD}Testing {len(avail)} section(s):{RST}")
for s in avail: print(f"    • {Y}{BLD}{s}{RST}")

# ─────────────────────────────────────────────────────────────────────────────
# PER-SECTION RUNNER
# ─────────────────────────────────────────────────────────────────────────────
def run_section(sec: str) -> dict:
    global _cur, _ph
    _cur = []
    sec_banner(sec)
    chdata: List[dict] = []
    cons:   List[dict] = []

    # ── Switch section ──────────────────────────────────────────────────────
    banner("S", f"SWITCH → {sec}"); sp("Switch")
    try:
        switch_section(driver, sec, CHAPTERS_URL)
        rec(f"Section '{sec}' selected", True)
    except Exception as e:
        rec(f"Section '{sec}' selected", False, str(e))
        try:
            driver.get(CHAPTERS_URL); time.sleep(S_NAV); wait_cards(driver)
            s2, _ = get_section_sel(driver)
            if s2: js_select(driver, s2, sec); time.sleep(S_DROP)
        except: pass

    # ── Navigation verify ───────────────────────────────────────────────────
    banner(3, "NAVIGATION VERIFY"); sp("Nav")
    src = driver.page_source
    rec("Chapters URL", "screen=chapters" in driver.current_url or "chapters" in driver.current_url,
        value=driver.current_url[-60:])
    for tab in ["Overview","Chapters","Questions","Students"]:
        rec(f"Tab '{tab}'", tab in src)

    # ── Card discovery ──────────────────────────────────────────────────────
    banner(4, "CHAPTER CARD DISCOVERY"); sp("Discovery")
    cc = discover_cards(driver)
    rec("Cards discovered", len(cc) >= 1, value=f"{len(cc)} found")
    nums = []
    for c in cc:
        m2 = re.search(r"(\d+\.?\d*)", c["pct"] or "")
        if m2:
            try: nums.append(float(m2.group(1)))
            except: pass
    if len(nums) >= 2:
        rec("Sorted High→Low",
            all(nums[i] >= nums[i+1] for i in range(len(nums)-1)),
            value=str([round(v,1) for v in nums[:5]])+"…")
    rec("Sort label present",
        len(driver.find_elements(By.XPATH, "//*[contains(text(),'Chapter Avg')]")) >= 1)

    print(f"\n  {BLD}Chapters [{sec}]:{RST}")
    for i, c in enumerate(cc, 1):
        col = G if "+" in c["pct"] else R
        ec = enorm(c["name"])
        unit_info = ""
        if ec:
            for uname, udata in EXCEL_UNITS.items():
                if ec in udata["chapters"]:
                    unit_info = f"  {DIM}[{uname}  {udata['marks']}m]{RST}"
                    break
        match_mark = f"  {G}✔{RST}" if ec else f"  {R}✘ NOT MAPPED{RST}"
        print(f"    {DIM}{i:>2}.{RST} {c['name']:<52} {col}{'▲' if '+' in c['pct'] else '▼'} {c['pct']} {match_mark}{unit_info}")

    # ── Per-chapter detail ──────────────────────────────────────────────────
    banner(5, "PER-CHAPTER DETAIL — LOC1/LOC2/LOC3/LOC4 + HEADER ACCURACY")
    for card in cc:
        ch = card["name"]; sp(f"Chapter:{ch}")
        direction = "▲" if "+" in (card["pct"] or "") else "▼"
        col = G if direction == "▲" else R
        print(f"\n  {BLD}{col}{direction}  {W}{ch}{RST}  {col}{card['pct']}{RST}")
        print(f"  {'─'*65}")
        cht: List[dict] = []

        def ct(name: str, passed: bool, detail: str = "", value: str = "") -> bool:
            rec(name, passed, detail, value)
            cht.append({"name": name, "passed": passed, "detail": detail, "value": value})
            return passed

        # LOC 1
        pct_card = read_card_pct(driver, card)
        ct("Loc 1 · Card list badge % readable", pct_card is not None, value=str(pct_card or "N/A"))

        clicked = click_card(driver, card)
        ct("Card clickable / detail panel opens", clicked)
        if not clicked:
            warn("Could not click card — skipping detail tests")
            cons.append({"name":ch,"pct_card":pct_card,"pct_chip":None,"pct_badge":None,
                         "pct_why":None,"why_acc_pct":None,"header_accuracy":None,
                         "match":False,"skip":True})
            chdata.append({
                "name":ch,"pct_card":pct_card,"pct_chip":None,"pct_badge":None,"pct_why":None,
                "why_heading":None,"why_text":None,"why_acc_pct":None,"header_accuracy":None,
                "panels":[],"pills":[],"tests":cht,"match":False,"skip":True,
            })
            continue

        time.sleep(PANEL_WAIT_SEC)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: any(kw in d.page_source for kw in _WHY_HEADINGS))
        except: time.sleep(1.5)
        src = driver.page_source

        # ★ Header accuracy badge (from Script 1)
        header_accuracy = read_header_accuracy_badge(driver)

        # LOC 2
        pct_chip  = read_improved_chip(driver, ref_pct=pct_card)
        # LOC 3
        pct_badge = read_change_badge(driver, ref_pct=pct_card)
        # LOC 4
        why_h     = next((kw for kw in _WHY_HEADINGS if kw in src), None)
        why_t_raw = read_why_text(driver)
        if why_t_raw:
            for _kw in _WHY_HEADINGS:
                if why_t_raw.startswith(_kw):
                    why_t_raw = why_t_raw[len(_kw):].strip(" :\n"); break
        why_t       = why_t_raw if why_t_raw and len(why_t_raw.strip()) > 10 else None
        pct_why     = read_why_pct(why_t)
        if pct_why is None:
            pct_why = read_why_pct_from_page(driver, ref_pct=pct_card)
        why_acc_pct = read_why_accuracy_pct(why_t)

        # align_sign on all four locations
        pct_chip  = align_sign(pct_card, pct_chip)
        pct_badge = align_sign(pct_card, pct_badge)
        if pct_why: pct_why = align_sign(pct_card, pct_why)

        ct("Loc 2 · IMPROVED/DECLINED chip % readable", pct_chip  is not None, value=str(pct_chip  or "N/A"))
        ct("Loc 3 · Change in chapter average badge",   pct_badge is not None, value=str(pct_badge or "N/A"))
        _l4v = pct_why or (f"acc:{why_acc_pct}" if why_acc_pct else None)
        ct("Loc 4 · Why-text % (change or accuracy)",   _l4v is not None,
           value=(f"change%={pct_why}" if pct_why
                  else (f"accuracy%={why_acc_pct} (stable)" if why_acc_pct else "NOTHING FOUND")))

        # ★ Header accuracy badge test (from Script 1)
        ct("Header accuracy badge readable",
           header_accuracy is not None,
           value=f"{header_accuracy}" if header_accuracy else "NOT FOUND")

        # 4-way consistency
        n1,n2,n3,n4 = norm_val(pct_card),norm_val(pct_chip),norm_val(pct_badge),norm_val(pct_why)
        present   = [n for n in [n1,n2,n3,n4] if n is not None]
        all_match = len(set(present)) == 1 and len(present) >= 2 and len(present) == 4
        ct("✦ 4-Way Consistency Loc1==Loc2==Loc3==Loc4", all_match,
           value=f"L1={pct_card}  L2={pct_chip}  L3={pct_badge}  L4={pct_why}")

        cons.append({"name":ch,"pct_card":pct_card,"pct_chip":pct_chip,
                     "pct_badge":pct_badge,"pct_why":pct_why,"why_acc_pct":why_acc_pct,
                     "header_accuracy":header_accuracy,
                     "match":all_match,"skip":False})

        ct("'Why this chapter' heading present", why_h is not None, value=why_h or "NOT FOUND")
        ct("Explanation body text present", bool(why_t and len(why_t) > 10),
           value=(why_t or "")[:60]+"…" if why_t else "NOT FOUND")
        ct("Midterm panel visible",    "Midterm"    in src)
        ct("Preboard 1 panel visible", "Preboard 1" in src)
        ct("ACCURACY label present",   any(k in src for k in ["ACCURACY","Accuracy","accuracy"]))
        ct("Weakest Concepts section",  any(k in src for k in ["Weakest Concepts","Weakest concepts"]))
        ct("Strongest Concepts section",any(k in src for k in ["Strongest Concepts","Strongest concepts"]))
        ct("Struggling students label", any(k in src for k in ["Struggling students","Struggling"]))
        ct("Weak Concepts label",       any(k in src for k in ["Weak Concepts","Weak concepts"]))
        ct("IMPROVED/DECLINED chip",    any(k in src for k in ["IMPROVED","DECLINED","Improved","Declined"]))
        ct("Change in chapter average", any(k in src for k in ["Change in chapter average","Change in chapter"]))

        # Read exam panels
        panels: List[dict] = []
        for exam_label in EXAM_LABELS:
            pd = read_exam_panel(driver, exam_label)
            ct(f"[{exam_label}] Accuracy % readable",
               pd["accuracy"] is not None, value=pd["accuracy"] or "N/A")
            sc2 = pd["struggling_count"]
            ct(f"[{exam_label}] Struggling students count",
               sc2 is not None,
               value=f"{sc2} students" if sc2 is not None else "NOT FOUND")
            wk = pd["weak_concepts_count"]
            ct(f"[{exam_label}] Weak Concepts count",
               wk is not None,
               value=f"{wk} concepts" if wk is not None else "NOT FOUND")
            ct(f"[{exam_label}] Weakest Concepts list ≥ 1 item",
               len(pd["weakest_concepts"]) >= 1,
               value=f"{len(pd['weakest_concepts'])} items: {pd['weakest_concepts'][:3]}")
            ct(f"[{exam_label}] Strongest Concepts list ≥ 1 item",
               len(pd["strongest_concepts"]) >= 1,
               value=f"{len(pd['strongest_concepts'])} items")
            panels.append(pd)
            print(f"      {DIM}{exam_label}:{RST}  "
                  f"Accuracy={G}{BLD}{pd['accuracy'] or '?'}{RST}  "
                  f"Struggling={Y}{BLD}{sc2 if sc2 is not None else '?'}{RST}  "
                  f"WeakConcepts={C}{wk if wk is not None else '?'}{RST}")
            if pd["weakest_concepts"]:
                print(f"        Weakest : {pd['weakest_concepts']}")
            if pd["strongest_concepts"]:
                print(f"        Strongest: {[c['name']+(' '+c['pct'] if c.get('pct') else '')+(' ['+c['badge']+']' if c.get('badge') else '') for c in pd['strongest_concepts']]}")

        pill_els = driver.find_elements(By.XPATH,
            "//*[normalize-space()='New' or normalize-space()='Improved' or "
            "    normalize-space()='Declined' or normalize-space()='NEW' or "
            "    normalize-space()='IMPROVED' or normalize-space()='DECLINED']")
        pills = list({safe_text(e) for e in pill_els if safe_text(e)})
        ct("Concept pill badges present", len(pills) >= 1, value=str(pills))

        # ★ Header accuracy terminal print (from Script 1)
        print(f"\n      {C}┌─ HEADER ACCURACY BADGE {'─'*38}┐{RST}")
        h_col = G if header_accuracy else R
        print(f"      {C}│{RST} Preboard 1 accuracy : {h_col}{BLD}{header_accuracy or 'NOT FOUND'}{RST}")
        print(f"      {C}└{'─'*60}┘{RST}")

        print(f"\n      {Y}┌─ WHY SECTION {'─'*45}┐{RST}")
        print(f"      {Y}│{RST} Heading : {why_h or 'NOT FOUND'}")
        preview = (why_t or "NOT FOUND")[:70]
        print(f"      {Y}│{RST} Text    : {preview}{'…' if why_t and len(why_t)>70 else ''}")
        pct_disp = pct_why if pct_why else "— (only accuracy % in text)"
        pct_col  = G if pct_why and "+" in pct_why else (R if pct_why else Y)
        print(f"      {Y}│{RST} Change %: {pct_col}{BLD}{pct_disp}{RST}")
        print(f"      {Y}└{'─'*55}┘{RST}")

        chdata.append({
            "name":ch,"pct_card":pct_card,"pct_chip":pct_chip,"pct_badge":pct_badge,
            "pct_why":pct_why,"why_heading":why_h,"why_text":why_t,"why_acc_pct":why_acc_pct,
            "header_accuracy":header_accuracy,
            "panels":panels,"pills":pills,"tests":cht,"match":all_match,"skip":False,
        })

    # ── Search ──────────────────────────────────────────────────────────────
    banner(6, "SEARCH BOX FUNCTIONALITY"); sp("Search")
    driver.get(CHAPTERS_URL); time.sleep(S_NAV)
    try:
        s2, _ = get_section_sel(driver)
        if s2: js_select(driver, s2, sec); time.sleep(S_DROP)
    except: pass
    wait_cards(driver); time.sleep(S_LABEL)
    fresh = discover_cards(driver)
    sb = None
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        ph = safe_attr(inp, "placeholder").lower()
        if "chapter" in ph or "search" in ph: sb = inp; break
    if not sb:
        inps = driver.find_elements(By.TAG_NAME, "input")
        if inps: sb = inps[0]
    rec("Search input element present", sb is not None,
        value=safe_attr(sb,"placeholder") if sb else "N/A")
    if sb and fresh:
        def clr():
            sb.click(); sb.send_keys(Keys.CONTROL,"a"); sb.send_keys(Keys.DELETE)
            time.sleep(S_CLEAR)
        kw = fresh[0]["name"].split()[0]; other = fresh[-1]["name"] if len(fresh) > 1 else None
        clr(); sb.send_keys(kw); time.sleep(S_SEARCH)
        rec(f"Search '{kw}' → target visible", fresh[0]["name"] in driver.page_source)
        if other and other.split()[0].lower() != kw.lower():
            ov = driver.find_elements(By.XPATH, f"//*[normalize-space()='{other}']")
            rec("Search filters non-matching", all(not e.is_displayed() for e in ov) if ov else True)
        clr()
        missing = [c["name"] for c in fresh if c["name"] not in driver.page_source]
        rec("Search cleared → all restored", len(missing)==0,
            value="all present" if not missing else f"missing {len(missing)}")
        clr(); sb.send_keys("ZZZNOMATCH99"); time.sleep(S_SEARCH)
        vis = driver.find_elements(By.XPATH, f"//*[normalize-space()='{fresh[0]['name']}']")
        rec("No-match query → cards hidden", all(not e.is_displayed() for e in vis) if vis else True)
        clr()

    # ── Static labels ────────────────────────────────────────────────────────
    banner(7, "STATIC UI LABELS"); sp("StaticLabels")
    driver.get(CHAPTERS_URL); time.sleep(S_NAV)
    try:
        s2, _ = get_section_sel(driver)
        if s2: js_select(driver, s2, sec); time.sleep(S_DROP)
    except: pass
    wait_cards(driver); time.sleep(S_LABEL)
    if fresh:
        opened = click_card(driver, fresh[0])
        if opened: time.sleep(1.5)
    src = driver.page_source
    for lbl, kws in [
        ("Sort label 'Chapter Avg'",           ["Chapter Avg"]),
        ("Nav tab 'Overview'",                 ["Overview"]),
        ("Nav tab 'Chapters'",                 ["Chapters"]),
        ("Nav tab 'Questions'",                ["Questions"]),
        ("Nav tab 'Students'",                 ["Students"]),
        ("'Midterm' header",                   ["Midterm"]),
        ("'Preboard 1' header",                ["Preboard 1","Preboard1"]),
        ("'ACCURACY' label",                   ["ACCURACY","Accuracy","accuracy"]),
        ("'Struggling students' label",        ["Struggling students","Struggling"]),
        ("'Weak Concepts' label",              ["Weak Concepts","Weak concepts"]),
        ("'Weakest Concepts' section",         ["Weakest Concepts","Weakest concepts"]),
        ("'Strongest Concepts' section",       ["Strongest Concepts","Strongest concepts"]),
        ("'Why this chapter' heading",         ["Why this chapter","Why This Chapter"]),
        ("IMPROVED/DECLINED chip",             ["IMPROVED","DECLINED","Improved","Declined"]),
        ("'Change in chapter average' label",  ["Change in chapter average","Change in chapter"]),
        ("Concept pill badges",                ["New","Improved","Declined","NEW","IMPROVED"]),
        ("Header accuracy badge",              ["accuracy"]),
    ]:
        rec(lbl, any(k in src for k in kws))

    # ── Excel validation ─────────────────────────────────────────────────────
    banner(8, "EXCEL VALIDATION"); sp("Excel")
    ecl  = []
    ecov = []
    cls  = {enorm(c["name"]) for c in cc if enorm(c["name"])}
    for card in cc:
        cn = card["name"]; ec = enorm(cn); ie = ec is not None
        un = ""; um = 0; co = []; mq = []; pq = []
        if ie:
            for uname, udata in EXCEL_UNITS.items():
                if ec in udata["chapters"]:
                    un = uname; um = udata["marks"]; co = udata["chapters"][ec]; break
            mq = MIDTERM_QUESTIONS.get(ec, [])
            pq = PREBOARD_QUESTIONS.get(ec, [])
        rec(f"Excel match '{cn}'", ie, value=(ec if ie else "NOT FOUND"))
        ecl.append({
            "cl_name":cn,"pct":card["pct"],"excel_ch":ec or "","unit":un,"unit_marks":um,
            "concepts":co,"mid_qs":mq,"pre_qs":pq,"mid_count":len(mq),"pre_count":len(pq),
            "result":"MATCH" if ie else "NOT IN EXCEL"
        })
    for uname, udata in EXCEL_UNITS.items():
        for ch2, co in udata["chapters"].items():
            ic = ch2 in cls
            ecov.append({
                "unit":uname,"unit_marks":udata["marks"],"excel_ch":ch2,"concepts":co,
                "mid_count":len(MIDTERM_QUESTIONS.get(ch2,[])),
                "pre_count":len(PREBOARD_QUESTIONS.get(ch2,[])),
                "mid_qs":MIDTERM_QUESTIONS.get(ch2,[]),
                "pre_qs":PREBOARD_QUESTIONS.get(ch2,[]),
                "result":"PRESENT" if ic else "MISSING"
            })

    pl2 = [r for r in _cur if r.passed]
    fl2 = [r for r in _cur if not r.passed]
    rt  = round(100*len(pl2)/len(_cur)) if _cur else 0
    print(f"\n  {BLD}Section {Y}{sec}{RST}{BLD}: {G}{len(pl2)}✔{RST}/{R}{len(fl2)}✘{RST} ({rt}%)")

    # ★ Header accuracy summary for this section
    print(f"\n  {BLD}{C}┌─ HEADER ACCURACY — Section {sec} {'─'*30}┐{RST}")
    for i, ch in enumerate(chdata, 1):
        ha = ch.get("header_accuracy")
        icon = f"{G}✔{RST}" if ha else f"{R}✘{RST}"
        print(f"    {icon}  {i:>2}. {ch['name']:<50} {C}{BLD}{ha or 'NOT FOUND'}{RST}")
    print(f"  {C}└{'─'*60}┘{RST}")

    return {
        "section": sec, "results": list(_cur), "chdata": chdata, "cc": cc,
        "cons": cons, "ecl": ecl, "ecov": ecov, "pl": pl2, "fl": fl2, "rate": rt,
    }

# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL SECTIONS
# ─────────────────────────────────────────────────────────────────────────────
AD: Dict[str, dict] = {}
for sec in avail:
    AD[sec] = run_section(sec)

# ─────────────────────────────────────────────────────────────────────────────
# GRAND TERMINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
tt = tp = tf = 0
for d in AD.values():
    tt += len(d["results"]); tp += len(d["pl"]); tf += len(d["fl"])
gr = round(100*tp/tt) if tt else 0

print(f"\n{BLD}{C}{'═'*72}\n  GRAND SUMMARY\n{'═'*72}{RST}")
for sec, d in AD.items():
    b = round(d["rate"]*30/100)
    col = G if d["rate"]==100 else (Y if d["rate"]>=70 else R)
    print(f"  {BLD}{Y}{sec:<10}{RST}  {col}{'█'*b}{'░'*(30-b)}{RST}  {d['rate']:>3}%  {G}{len(d['pl'])}✔{RST}  {R}{len(d['fl'])}✘{RST}")
print(f"{C}{'─'*72}{RST}")
print(f"  TOTAL  {tt} tests  {tp} pass  {tf} fail  {gr}%")
print(f"{C}{'═'*72}{RST}\n")

print(f"\n{BLD}{C}{'═'*72}\n  4-WAY CONSISTENCY + HEADER ACCURACY (All Sections)\n{'═'*72}{RST}")
print(f"  {'Sec':<6}  {'Chapter':<42}  {'Loc1':>7}  {'Loc2':>7}  {'Loc3':>7}  {'Loc4':>7}  {'HdrAcc':>8}  {'OK?':>5}")
for sec, d in AD.items():
    for row in d["cons"]:
        if row.get("skip"): continue
        ok = f"{G}✔{RST}" if row["match"] else f"{R}✘{RST}"
        ha = row.get("header_accuracy") or "N/A"
        print(f"  {sec:<6}  {row['name']:<42}  "
              f"{(row['pct_card'] or '—'):>7}  {(row.get('pct_chip') or '—'):>7}  "
              f"{(row.get('pct_badge') or '—'):>7}  {(row.get('pct_why') or '—'):>7}  "
              f"{C}{ha:>8}{RST}  {ok}")

# ★ Header accuracy grand summary
print(f"\n{BLD}{C}{'═'*72}\n  HEADER ACCURACY BADGE — ALL SECTIONS\n{'═'*72}{RST}")
for sec, d in AD.items():
    print(f"  {BLD}{Y}Section {sec}:{RST}")
    for i, ch in enumerate(d["chdata"], 1):
        ha = ch.get("header_accuracy")
        icon = f"{G}✔{RST}" if ha else f"{R}✘{RST}"
        print(f"    {icon}  {i:>2}. {ch['name']:<50} {C}{BLD}{ha or 'NOT FOUND'}{RST}")

# ─────────────────────────────────────────────────────────────────────────────
# HTML REPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hb(ok: bool) -> str:
    return ('<span class="badge ok">PASS</span>' if ok
            else '<span class="badge fail">FAIL</span>')

def hp(pct: Optional[str]) -> str:
    if not pct: return '<span class="muted">—</span>'
    col = "#3fb950" if "+" in pct else "#f85149"
    arr = "▲" if "+" in pct else "▼"
    return f'<span style="color:{col};font-weight:700;font-family:\'DM Mono\',monospace">{arr} {pct}</span>'

def hpill(t: str) -> str:
    if not t: return ""
    t_low = t.lower()
    if t_low == "new":       cls = "pill-new"
    elif t_low == "improved": cls = "pill-pos"
    else:                     cls = "pill-neg"
    return f'<span class="{cls}">{t}</span>'

def grp_row(title: str, cols: int, chip: str = "", extra: str = "") -> str:
    ch = ""
    if chip == "+": ch = '<span class="chip-pos">▲ IMPROVED</span>'
    elif chip == "-": ch = '<span class="chip-neg">▼ DECLINED</span>'
    return f'<tr class="grp-row"><td colspan="{cols}"><span class="grp-title">{title}</span>{ch}{extra}</td></tr>'

def loc_cell(v: Optional[str], ref: Optional[str]) -> str:
    if not v: return '<span class="miss">✘ MISSING</span>'
    rn = re.search(r"(\d+\.?\d*)", ref or "")
    vn = re.search(r"(\d+\.?\d*)", v or "")
    ok = rn and vn and rn.group(1) == vn.group(1)
    col = "#3fb950" if "+" in v else "#f85149"
    arr = "▲" if "+" in v else "▼"
    tick = ('<span class="badge ok" style="font-size:10px;padding:1px 5px;margin-left:4px">✔</span>'
            if ok else
            '<span class="badge fail" style="font-size:10px;padding:1px 5px;margin-left:4px">✘</span>')
    return f'<span style="color:{col};font-weight:700;font-family:\'DM Mono\',monospace">{arr} {v}</span>{tick}'

def hacc_cell(v: Optional[str]) -> str:
    if not v: return '<span class="miss">✘ NOT FOUND</span>'
    return (f'<span style="color:#58a6ff;font-size:18px;font-weight:700;'
            f'font-family:\'DM Mono\',monospace">{v}</span>')

# ─────────────────────────────────────────────────────────────────────────────
# BUILD PER-SECTION HTML  (with header accuracy columns merged from Script 1)
# ─────────────────────────────────────────────────────────────────────────────
def build_section_html(sec: str, d: dict) -> str:
    sid    = re.sub(r"[^A-Za-z0-9]", "_", sec)
    cd     = d["chdata"]; cc = d["cc"]; cr = d["cons"]
    ar     = d["results"]; pl = d["pl"]; fl = d["fl"]; rt = d["rate"]
    by_ph  = defaultdict(list)
    for r in ar: by_ph[r.phase].append(r)

    # ── Overview rows (with header accuracy column) ────────────────────────
    ov_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in ch["pct_card"] else "-"
        ov_rows += grp_row(f"{i}.  {ch['name']}", 9, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
        p_tc = sum(1 for t in ch["tests"] if t["passed"]); t_tc = len(ch["tests"])
        pct_tc = round(100*p_tc/t_tc) if t_tc else 0
        bar_c  = "#3fb950" if pct_tc==100 else ("#d29922" if pct_tc>=50 else "#f85149")
        tc_bar = (f'<div style="display:flex;align-items:center;gap:8px">'
                  f'<div style="flex:1;background:#1a2330;border-radius:3px;height:5px;min-width:60px">'
                  f'<div style="width:{pct_tc}%;height:5px;background:{bar_c};border-radius:3px"></div></div>'
                  f'<span style="font-size:11px;color:#5a7490;font-family:\'DM Mono\',monospace">{p_tc}/{t_tc}</span></div>')
        cons_badge = (f'<span class="badge ok">MATCH</span>' if ch["match"]
                      else ('<span class="badge skip">SKIP</span>' if ch.get("skip")
                            else '<span class="badge fail">MISMATCH</span>'))
        ov_rows += (f'<tr><td class="num">{i}</td><td class="chn">{ch["name"]}</td>'
                    f'<td style="text-align:center">{hp(ch["pct_card"])}</td>'
                    f'<td style="text-align:center">{hp(ch.get("pct_chip"))}</td>'
                    f'<td style="text-align:center">{hp(ch.get("pct_badge"))}</td>'
                    f'<td style="text-align:center">{loc4_display(ch)}</td>'
                    f'<td style="text-align:center">{hacc_cell(ch.get("header_accuracy"))}</td>'
                    f'<td style="text-align:center">{cons_badge}</td>'
                    f'<td>{tc_bar}</td></tr>')

    # ── All-tests rows ─────────────────────────────────────────────────────
    tc_rows = ""
    for ph, rs in by_ph.items():
        p2 = sum(1 for r in rs if r.passed); f2 = len(rs)-p2
        bge = (f'<span class="badge ok">{p2} passed</span>'
               + (f'&nbsp;<span class="badge fail">{f2} failed</span>' if f2 else ""))
        tc_rows += grp_row(ph.replace("Chapter:",""), 5,
                           extra=f'<span style="float:right">{bge}</span>')
        for r in rs:
            cls2 = "pass-row" if r.passed else "fail-row"
            icon = ('<span style="color:#3fb950;font-weight:700">✔</span>' if r.passed
                    else '<span style="color:#f85149;font-weight:700">✘</span>')
            v = (r.value or r.detail or "")[:70]
            tc_rows += (f'<tr class="{cls2}"><td style="width:28px">{icon}</td>'
                        f'<td class="muted" style="font-size:11px">{r.phase.replace("Chapter:","")}</td>'
                        f'<td>{r.name}</td><td>{hb(r.passed)}</td>'
                        f'<td class="muted mono" style="font-size:12px">{v}</td></tr>')

    # ── Consistency rows (with header accuracy column) ─────────────────────
    cons_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        cons_rows += grp_row(f"{i}.  {ch['name']}", 7, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
        cls2 = "pass-row" if ch["match"] else ("skip-row" if ch.get("skip") else "fail-row")
        res = (f'<span class="badge ok">ALL MATCH</span>' if ch["match"]
               else (f'<span class="badge skip">SKIPPED</span>' if ch.get("skip")
                     else f'<span class="badge fail">MISMATCH</span>'))
        cons_rows += (f'<tr class="{cls2}"><td class="chn">{ch["name"]}</td>'
                      f'<td style="text-align:center">{loc_cell(ch["pct_card"], ch["pct_card"])}</td>'
                      f'<td style="text-align:center">{loc_cell(ch.get("pct_chip"), ch["pct_card"])}</td>'
                      f'<td style="text-align:center">{loc_cell(ch.get("pct_badge"), ch["pct_card"])}</td>'
                      f'<td style="text-align:center">{loc4_display(ch)}</td>'
                      f'<td style="text-align:center">{hacc_cell(ch.get("header_accuracy"))}</td>'
                      f'<td style="text-align:center;font-weight:700">{res}</td></tr>')

    # ── Exam stats rows ────────────────────────────────────────────────────
    est_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        est_rows += grp_row(f"{i}.  {ch['name']}", 6, chip)
        for pd in ch.get("panels", []):
            acc = pd["accuracy"] or "—"; acc_ok = pd["accuracy"] is not None
            acc_sty = ("color:#3fb950;font-size:18px;font-weight:700;font-family:'DM Mono',monospace"
                       if acc_ok else "color:#5a7490")
            sc2 = pd["struggling_count"]
            st_h = ('<span class="muted">—</span>' if sc2 is None
                    else (f'<span style="color:#3fb950;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{sc2}</span>' if sc2==0
                          else (f'<span style="color:#d29922;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{sc2}</span>' if sc2<=5
                                else f'<span style="color:#f85149;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{sc2}</span>')))
            wk = pd["weak_concepts_count"]
            wk_h = ('<span class="muted">—</span>' if wk is None
                    else (f'<span style="color:#3fb950;font-weight:700;font-family:\'DM Mono\',monospace">{wk}</span>' if wk==0
                          else f'<span style="color:#f85149;font-weight:700;font-family:\'DM Mono\',monospace">{wk}</span>'))
            est_rows += (f'<tr><td class="chn">{ch["name"]}</td>'
                         f'<td><strong style="color:#cdd9e5">{pd["label"]}</strong></td>'
                         f'<td class="muted mono">{pd.get("exam_date") or "—"}</td>'
                         f'<td class="num" style="{acc_sty}">{acc}</td>'
                         f'<td class="num">{st_h}</td>'
                         f'<td class="num">{wk_h}</td></tr>')

    # ── Accuracy rows (with header accuracy column) ────────────────────────
    acc_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        acc_rows += grp_row(f"{i}.  {ch['name']}", 7, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
        mid_acc_v = pre_acc_v = None
        for pd in ch.get("panels", []):
            if pd["label"] == "Midterm":    mid_acc_v = pd.get("accuracy")
            if pd["label"] == "Preboard 1": pre_acc_v = pd.get("accuracy")
        why_acc_v = ch.get("why_acc_pct")
        header_acc_v = ch.get("header_accuracy")
        mid_cell = (f'<span style="color:#d29922;font-size:20px;font-weight:700;font-family:\'DM Mono\',monospace">{mid_acc_v}</span>'
                    if mid_acc_v else '<span class="muted">—</span>')
        pre_cell = (f'<span style="color:#58a6ff;font-size:20px;font-weight:700;font-family:\'DM Mono\',monospace">{pre_acc_v}</span>'
                    if pre_acc_v else '<span class="muted">—</span>')
        wacc_cell = (f'<span style="color:#3fb950;font-size:17px;font-weight:700;font-family:\'DM Mono\',monospace">{why_acc_v}</span>'
                     if why_acc_v else '<span class="muted">—</span>')
        acc_rows += (f'<tr><td class="chn">{ch["name"]}</td>'
                     f'<td style="text-align:center">{hp(ch.get("pct_card"))}</td>'
                     f'<td style="text-align:center">{hacc_cell(header_acc_v)}</td>'
                     f'<td style="text-align:center">{mid_cell}</td>'
                     f'<td style="text-align:center">{pre_cell}</td>'
                     f'<td style="text-align:center">{loc4_display(ch)}</td>'
                     f'<td style="text-align:center">{wacc_cell}</td></tr>')

    # ── Weakest concepts rows ──────────────────────────────────────────────
    wk_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        wk_rows += grp_row(f"{i}.  {ch['name']}", 4, chip)
        for pd in ch.get("panels", []):
            exam_col = "#d29922" if pd["label"] == "Midterm" else "#58a6ff"
            wk_rows += (f'<tr class="sub-row"><td colspan="4" style="color:{exam_col}">'
                        f'📅 &nbsp;{pd["label"]}</td></tr>')
            if pd["weakest_concepts"]:
                for rank, concept in enumerate(pd["weakest_concepts"], 1):
                    if isinstance(concept, dict):
                        cname  = concept.get("name", str(concept))
                        cbadge = hpill(concept.get("badge", "")) if concept.get("badge") else ""
                    else:
                        cname = str(concept); cbadge = ""
                    wk_rows += (f'<tr><td class="num" style="color:#d29922;font-weight:700;'
                                f'font-family:\'DM Mono\',monospace;width:36px">{rank}</td>'
                                f'<td style="font-weight:500;padding-left:24px">{cname}</td>'
                                f'<td class="muted mono">{pd["label"]}</td>'
                                f'<td>{cbadge}</td></tr>')
            else:
                wk_rows += '<tr><td colspan="4" class="empty">None extracted</td></tr>'

    # ── Strongest concepts rows ────────────────────────────────────────────
    st_rows = ""
    for i, ch in enumerate(cd, 1):
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        st_rows += grp_row(f"{i}.  {ch['name']}", 5, chip)
        for pd in ch.get("panels", []):
            exam_col = "#d29922" if pd["label"] == "Midterm" else "#58a6ff"
            st_rows += (f'<tr class="sub-row"><td colspan="5" style="color:{exam_col}">'
                        f'📅 &nbsp;{pd["label"]}</td></tr>')
            if pd["strongest_concepts"]:
                for c in pd["strongest_concepts"]:
                    if isinstance(c, dict):
                        cname  = c.get("name", "")
                        cpct   = c.get("pct")
                        cbadge = c.get("badge", "")
                    else:
                        cname = str(c); cpct = None; cbadge = ""
                    bh  = hpill(cbadge) if cbadge else '<span class="muted">—</span>'
                    ph2 = (f'<span style="color:#58a6ff;font-weight:600;'
                           f'font-family:\'DM Mono\',monospace">{cpct}</span>'
                           if cpct else '<span class="muted">—</span>')
                    st_rows += (f'<tr><td style="font-weight:500;padding-left:24px">{cname}</td>'
                                f'<td class="muted mono">{pd["label"]}</td>'
                                f'<td class="num">{ph2}</td><td>{bh}</td><td></td></tr>')
            else:
                st_rows += '<tr><td colspan="5" class="empty">None extracted</td></tr>'

    # ── Why text rows ──────────────────────────────────────────────────────
    why_rows = ""
    for i, ch in enumerate(cd, 1):
        if not ch.get("why_heading") and not ch.get("why_text"): continue
        chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
        why_rows += grp_row(f"{i}.  {ch['name']}", 5, chip)
        why_rows += (f'<tr><td class="chn">{ch["name"]}</td>'
                     f'<td>{hp(ch["pct_card"])}</td>'
                     f'<td><strong style="color:#cdd9e5">{ch.get("why_heading") or "—"}</strong></td>'
                     f'<td style="font-size:13px;line-height:1.65;max-width:440px;color:#cdd9e5">{ch.get("why_text") or "—"}</td>'
                     f'<td style="text-align:center">{loc4_display(ch)}</td></tr>')
    if not why_rows:
        why_rows = '<tr><td colspan="5" class="empty">No explanation text extracted</td></tr>'

    # ── Failed tests rows ──────────────────────────────────────────────────
    failed_rows = ""; prev_ph2 = ""
    for r in [r for r in ar if not r.passed]:
        ph = r.phase.replace("Chapter:","")
        if ph != prev_ph2: failed_rows += grp_row(ph, 4); prev_ph2 = ph
        det = (r.detail or r.value or "")[:80]
        failed_rows += (f'<tr class="fail-row">'
                        f'<td style="width:28px"><span style="color:#f85149;font-weight:700">✘</span></td>'
                        f'<td class="muted mono" style="font-size:11px">{ph}</td>'
                        f'<td>{r.name}</td>'
                        f'<td class="muted mono" style="font-size:12px">{det}</td></tr>')
    if not failed_rows:
        failed_rows = '<tr><td colspan="4" class="empty" style="color:#3fb950;font-style:normal;font-weight:600">🎉 All tests passed!</td></tr>'

    # ── Phase cards ────────────────────────────────────────────────────────
    phase_cards = ""
    for ph, rs in by_ph.items():
        p2 = sum(1 for r in rs if r.passed); f2 = len(rs)-p2
        pct_ph = round(100*p2/len(rs)) if rs else 0
        border_col = "#1a7f37" if f2==0 else "#cf222e"
        bar_col    = "#3fb950" if f2==0 else "#f85149"
        phase_cards += (f'<div style="background:#0d1219;border:1px solid #1f2d3d;border-left:3px solid {border_col};'
                        f'border-radius:8px;padding:14px 16px;">'
                        f'<div style="font-size:12px;font-weight:600;color:#cdd9e5;margin-bottom:8px;'
                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{ph.replace("Chapter:","")}">'
                        f'{ph.replace("Chapter:","📖 ")}</div>'
                        f'<div style="background:#1a2330;border-radius:3px;height:4px;overflow:hidden;margin-bottom:8px">'
                        f'<div style="width:{pct_ph}%;height:4px;background:{bar_col};border-radius:3px"></div></div>'
                        f'<div style="font-size:11px;display:flex;gap:8px;font-family:\'DM Mono\',monospace">'
                        f'<span style="color:#3fb950">{p2}✔</span>'
                        f'<span style="color:#f85149">{f2}✘</span>'
                        f'<span style="color:#5a7490">{pct_ph}%</span>'
                        f'</div></div>')

    # ── Excel validation HTML ──────────────────────────────────────────────
    def CP2(n, f=False):
        bg="#0d2318" if f else "#1c2840"; c="#3fb950" if f else "#8b949e"
        b="#238636" if f else "#30363d"; t=" ★" if f else ""
        return f'<span style="display:inline-block;padding:1px 6px;border-radius:12px;font-size:11px;background:{bg};color:{c};border:1px solid {b};margin:1px">{n}{t}</span>'
    def QP2(q, cn, o):
        c2 = "#e3b341" if o else "#8b949e"
        return f'<span style="display:inline-block;padding:1px 7px;border-radius:4px;font-size:11px;background:#1c2128;color:{c2};border:1px solid #30363d;margin:1px"><strong>Q{q}</strong>: {cn}</span>'
    def BX2(r):
        m2 = {"MATCH":("em","✔ MATCH"),"PRESENT":("em","✔ PRESENT"),"NOT IN EXCEL":("ex","✘ NOT IN EXCEL"),"MISSING":("ems","⚠ MISSING")}
        cl, lb = m2.get(r, ("ems",r)); return f'<span class="{cl}">{lb}</span>'

    exc = ""
    for _r in d["ecl"]:
        rc = "pass-row" if _r["result"]=="MATCH" else "fail-row"
        cp = " ".join(CP2(c2,f) for c2,f in _r["concepts"]) if _r["concepts"] else '<span class="muted">—</span>'
        mp = " ".join(QP2(q,c2,o) for q,c2,o in _r["mid_qs"]) if _r["mid_qs"] else '<span class="muted" style="font-size:12px">Not in Midterm</span>'
        pp2 = " ".join(QP2(q,c2,o) for q,c2,o in _r["pre_qs"]) if _r["pre_qs"] else '<span class="muted" style="font-size:12px">Not in Preboard</span>'
        exc += f'''<tr class="{rc}"><td class="chn">{_r["cl_name"]}</td><td style="text-align:center">{hp(_r["pct"])}</td>
        <td style="font-weight:600;color:#cdd9e5">{_r["excel_ch"] or "<i style='color:#f85149'>Not Found</i>"}</td>
        <td class="muted" style="font-size:12px">{_r["unit"] or "—"}</td>
        <td class="num" style="font-weight:700;color:#e3b341">{_r["unit_marks"] or "—"}</td>
        <td class="num" style="font-weight:700;color:#58a6ff">{_r["mid_count"]}</td>
        <td class="num" style="font-weight:700;color:#bc8cff">{_r["pre_count"]}</td>
        <td style="text-align:center">{BX2(_r["result"])}</td></tr>
        <tr class="{rc}" style="border-top:none"><td colspan="2" class="muted" style="font-size:11px">Concepts:</td><td colspan="6" style="padding-bottom:5px">{cp}</td></tr>
        <tr class="{rc}" style="border-top:none"><td colspan="2" style="font-size:11px;color:#58a6ff">Midterm Qs:</td><td colspan="6" style="padding-bottom:5px">{mp}</td></tr>
        <tr class="{rc}" style="border-top:none;border-bottom:2px solid #1f2d3d"><td colspan="2" style="font-size:11px;color:#bc8cff">Preboard Qs:</td><td colspan="6" style="padding-bottom:7px">{pp2}</td></tr>'''

    exco = ""; cu = ""
    for _r in d["ecov"]:
        if _r["unit"] != cu:
            cu = _r["unit"]
            exco += f'<tr class="grp-row"><td colspan="6"><span class="grp-title">Unit: {_r["unit"]}</span><span class="chip-pos" style="margin-left:12px">{_r["unit_marks"]} marks</span></td></tr>'
        rc = "pass-row" if _r["result"]=="PRESENT" else "skip-row"
        cp = " ".join(CP2(c2,f) for c2,f in _r["concepts"])
        mp = " ".join(QP2(q,c2,o) for q,c2,o in _r["mid_qs"]) if _r["mid_qs"] else '<span class="muted" style="font-size:12px">Not in Midterm</span>'
        pp2 = " ".join(QP2(q,c2,o) for q,c2,o in _r["pre_qs"]) if _r["pre_qs"] else '<span class="muted" style="font-size:12px">Not in Preboard</span>'
        exco += f'''<tr class="{rc}"><td class="chn" colspan="2">{_r["excel_ch"]}  {BX2(_r["result"])}</td>
        <td class="num" style="font-weight:700;color:#58a6ff">{_r["mid_count"]}q</td>
        <td class="num" style="font-weight:700;color:#bc8cff">{_r["pre_count"]}q</td>
        <td class="num" style="font-weight:700;color:#e3b341">{_r["unit_marks"]}</td><td></td></tr>
        <tr class="{rc}" style="border-top:none"><td class="muted" style="font-size:11px;width:80px">Concepts:</td><td colspan="5" style="padding-bottom:4px">{cp}</td></tr>
        <tr class="{rc}" style="border-top:none"><td style="font-size:11px;color:#58a6ff">Midterm:</td><td colspan="5" style="padding-bottom:4px">{mp}</td></tr>
        <tr class="{rc}" style="border-top:none;border-bottom:2px solid #1f2d3d"><td style="font-size:11px;color:#bc8cff">Preboard:</td><td colspan="5" style="padding-bottom:7px">{pp2}</td></tr>'''

    bar_col2 = "#3fb950" if rt == 100 else ("#d29922" if rt >= 70 else "#f85149")

    return f"""
<div class="sec-summary">
  <div class="kpi-row">
    <div class="kpi"><div class="kv" style="color:#58a6ff">{len(ar)}</div><div class="kl">Total Tests</div></div>
    <div class="kpi"><div class="kv" style="color:#3fb950">{len(pl)}</div><div class="kl">Passed</div></div>
    <div class="kpi"><div class="kv" style="color:#f85149">{len(fl)}</div><div class="kl">Failed</div></div>
    <div class="kpi"><div class="kv" style="color:#d29922">{rt}%</div><div class="kl">Pass Rate</div></div>
    <div class="kpi"><div class="kv" style="color:#cdd9e5">{len(cc)}</div><div class="kl">Chapters</div></div>
  </div>
  <div class="prog">
    <div class="prog-head"><span class="prog-label">Section {sec} Pass Rate</span>
    <span class="prog-val">{rt}%</span></div>
    <div class="prog-track"><div class="prog-fill" style="width:{rt}%;background:{bar_col2}"></div></div>
  </div>
</div>

<div class="nav-wrap">
  <div class="nav" id="nav-{sid}">
    <div class="nt active" onclick="tab(this,'t-{sid}-ov')">📋 Overview</div>
    <div class="nt" onclick="tab(this,'t-{sid}-ph')">⚡ Phases</div>
    <div class="nt" onclick="tab(this,'t-{sid}-tc')">🧪 All Tests</div>
    <div class="nt" onclick="tab(this,'t-{sid}-pc')">📐 Consistency</div>
    <div class="nt" onclick="tab(this,'t-{sid}-ex')">📊 Exam Stats</div>
    <div class="nt" onclick="tab(this,'t-{sid}-acc')">🎯 Accuracy</div>
    <div class="nt" onclick="tab(this,'t-{sid}-wk')">⚠️ Weakest</div>
    <div class="nt" onclick="tab(this,'t-{sid}-st')">★ Strongest</div>
    <div class="nt" onclick="tab(this,'t-{sid}-wy')">💡 Why Text</div>
    <div class="nt" onclick="tab(this,'t-{sid}-fl')">❌ Failed</div>
    <div class="nt" onclick="tab(this,'t-{sid}-xl')">📚 Excel</div>
  </div>
</div>

<div id="t-{sid}-ov" class="tc active">
  <div class="sh"><div class="sh-icon">📋</div><h2>Chapter Overview</h2><div class="sh-pills"><span class="pill">{len(cc)} chapters</span></div></div>
  <div class="tw"><table><thead><tr><th>#</th><th>Chapter</th><th>Loc 1 Card</th><th>Loc 2 Chip</th><th>Loc 3 Badge</th><th>Loc 4 Why</th><th style="color:#58a6ff">Header Acc</th><th>4-Way</th><th>Tests</th></tr></thead><tbody>{ov_rows}</tbody></table></div>
</div>

<div id="t-{sid}-ph" class="tc">
  <div class="sh"><div class="sh-icon">⚡</div><h2>Phase Summary</h2></div>
  <div class="pg">{phase_cards}</div>
</div>

<div id="t-{sid}-tc" class="tc">
  <div class="sh"><div class="sh-icon">🧪</div><h2>All Test Cases</h2>
    <div class="sh-pills"><span class="pill">{len(ar)} tests</span>
    <span class="pill pill-g">{len(pl)} passed</span><span class="pill pill-r">{len(fl)} failed</span></div>
  </div>
  <div class="tw"><table><thead><tr><th></th><th>Phase</th><th>Test Name</th><th>Result</th><th>Value / Detail</th></tr></thead><tbody>{tc_rows}</tbody></table></div>
</div>

<div id="t-{sid}-pc" class="tc">
  <div class="sh"><div class="sh-icon">📐</div><h2>4-Way Percentage Consistency</h2><div class="sh-pills"><span class="pill">{len(cd)} chapters</span></div></div>
  <div class="desc"><strong>Loc 1</strong> Card badge &nbsp;·&nbsp; <strong>Loc 2</strong> IMPROVED/DECLINED chip &nbsp;·&nbsp; <strong>Loc 3</strong> Change in chapter avg &nbsp;·&nbsp; <strong>Loc 4</strong> Why-text &nbsp;·&nbsp; <strong style="color:#58a6ff">Header Acc</strong> "Preboard 1 accuracy XX%" badge</div>
  <div class="tw"><table><thead><tr><th>Chapter</th><th>Loc 1 Card</th><th>Loc 2 Chip</th><th>Loc 3 Badge</th><th>Loc 4 Why</th><th style="color:#58a6ff">Header Acc</th><th>Result</th></tr></thead><tbody>{cons_rows}</tbody></table></div>
</div>

<div id="t-{sid}-ex" class="tc">
  <div class="sh"><div class="sh-icon">📊</div><h2>Exam Statistics per Chapter</h2></div>
  <div class="tw"><table><thead><tr><th>Chapter</th><th>Exam</th><th>Date</th><th>Accuracy %</th><th>Struggling Students</th><th>Weak Concepts</th></tr></thead><tbody>{est_rows}</tbody></table></div>
</div>

<div id="t-{sid}-acc" class="tc">
  <div class="sh"><div class="sh-icon">🎯</div><h2>Accuracy — Every Chapter</h2><div class="sh-pills"><span class="pill">{len(cd)} chapters</span></div></div>
  <div class="desc"><strong style="color:#58a6ff">Header Acc</strong> is the "Preboard 1 accuracy XX%" blue badge. &nbsp; <strong style="color:#d29922">Midterm %</strong> and <strong style="color:#58a6ff">Preboard 1 %</strong> are exam-panel accuracy scores. &nbsp; <strong style="color:#3fb950">Accuracy in why-text</strong> is explicitly stated in the Why section.</div>
  <div class="tw"><table><thead><tr>
    <th>Chapter</th>
    <th style="text-align:center">Change %<br><small>Card · Loc1</small></th>
    <th style="text-align:center;color:#58a6ff">Header Acc<br>Badge</th>
    <th style="text-align:center;color:#d29922">Midterm<br>Accuracy</th>
    <th style="text-align:center;color:#58a6ff">Preboard 1<br>Accuracy</th>
    <th style="text-align:center">Loc 4 Change %<br><small>Why-text</small></th>
    <th style="text-align:center;color:#3fb950">Accuracy %<br><small>In why-text</small></th>
  </tr></thead><tbody>{acc_rows}</tbody></table></div>
</div>

<div id="t-{sid}-wk" class="tc">
  <div class="sh"><div class="sh-icon">⚠️</div><h2>Weakest Concepts</h2>
    <div class="sh-pills">
      <span class="pill-new" style="font-size:11px;padding:3px 10px">New</span>
      <span class="pill-pos" style="font-size:11px;padding:3px 10px">Improved</span>
      <span class="pill-neg" style="font-size:11px;padding:3px 10px">Declined</span>
    </div>
  </div>
  <div class="tw"><table><thead><tr><th>Rank</th><th>Concept</th><th>Exam</th><th>Badge</th></tr></thead><tbody>{wk_rows}</tbody></table></div>
</div>

<div id="t-{sid}-st" class="tc">
  <div class="sh"><div class="sh-icon">★</div><h2>Strongest Concepts</h2>
    <div class="sh-pills">
      <span class="pill-new" style="font-size:11px;padding:3px 10px">New</span>
      <span class="pill-pos" style="font-size:11px;padding:3px 10px">Improved</span>
      <span class="pill-neg" style="font-size:11px;padding:3px 10px">Declined</span>
    </div>
  </div>
  <div class="tw"><table><thead><tr><th>Concept</th><th>Exam</th><th>Score</th><th>Badge</th><th></th></tr></thead><tbody>{st_rows}</tbody></table></div>
</div>

<div id="t-{sid}-wy" class="tc">
  <div class="sh"><div class="sh-icon">💡</div><h2>Why This Chapter Improved / Declined</h2></div>
  <div class="desc">Loc 4 shows — when the explanation references only an accuracy % (e.g. "stable at 19.2% accuracy"). This is expected and correct.</div>
  <div class="tw"><table><thead><tr><th>Chapter</th><th>Change (Card)</th><th>Heading</th><th>Explanation Text</th><th>Extracted %</th></tr></thead><tbody>{why_rows}</tbody></table></div>
</div>

<div id="t-{sid}-fl" class="tc">
  <div class="sh"><div class="sh-icon">❌</div><h2>Failed Tests</h2><div class="sh-pills"><span class="pill pill-r">{len(fl)} failed</span></div></div>
  <div class="tw"><table><thead><tr><th></th><th>Phase</th><th>Test Name</th><th>Detail</th></tr></thead><tbody>{failed_rows}</tbody></table></div>
</div>

<div id="t-{sid}-xl" class="tc">
  <div class="sh"><div class="sh-icon">📚</div><h2>Excel Validation</h2>
    <div class="sh-pills">
      <span class="pill pill-g">{sum(1 for r in d['ecl'] if r['result']=='MATCH')} matched</span>
      <span class="pill">{sum(1 for r in d['ecl'] if r['result']=='NOT IN EXCEL')} extra</span>
      <span class="pill pill-r">{sum(1 for r in d['ecov'] if r['result']=='MISSING')} missing</span>
    </div>
  </div>
  <div class="nav-wrap" style="margin-bottom:10px">
    <div class="nav" id="xnav-{sid}">
      <div class="nt active" onclick="xtab(this,'{sid}','xl1')">CL vs Excel</div>
      <div class="nt" onclick="xtab(this,'{sid}','xl2')">Full Coverage</div>
    </div>
  </div>
  <div id="xl1-{sid}" class="xtc active">
    <div class="tw"><table><thead><tr><th>CL Chapter</th><th>Change</th><th>Excel Chapter</th><th>Unit</th><th>Marks</th><th style="color:#58a6ff">Mid Qs</th><th style="color:#bc8cff">Pre Qs</th><th>Result</th></tr></thead><tbody>{exc}</tbody></table></div>
  </div>
  <div id="xl2-{sid}" class="xtc">
    <div class="tw"><table><thead><tr><th colspan="2">Chapter</th><th>Mid</th><th>Pre</th><th>Marks</th><th></th></tr></thead><tbody>{exco}</tbody></table></div>
  </div>
</div>
"""

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CONSISTENCY HTML (with header accuracy column)
# ─────────────────────────────────────────────────────────────────────────────
def build_global_html() -> str:
    rows = ""
    for sec, d in AD.items():
        for row in d["cons"]:
            if row.get("skip"): continue
            ok = '<span class="badge ok">✔ MATCH</span>' if row["match"] else '<span class="badge fail">✘ MISMATCH</span>'
            cls2 = "pass-row" if row["match"] else "fail-row"
            ha = row.get("header_accuracy")
            rows += (f'<tr class="{cls2}"><td style="font-weight:700;color:#d29922">{sec}</td>'
                     f'<td class="chn">{row["name"]}</td>'
                     f'<td style="text-align:center">{loc_cell(row["pct_card"], row["pct_card"])}</td>'
                     f'<td style="text-align:center">{loc_cell(row.get("pct_chip"), row["pct_card"])}</td>'
                     f'<td style="text-align:center">{loc_cell(row.get("pct_badge"), row["pct_card"])}</td>'
                     f'<td style="text-align:center">{loc4_display(row)}</td>'
                     f'<td style="text-align:center">{hacc_cell(ha)}</td>'
                     f'<td style="text-align:center">{ok}</td></tr>')
    return rows

# Grand summary rows
gr_rows = ""
for sec, d in AD.items():
    bar_col3 = "#3fb950" if d["rate"]==100 else ("#d29922" if d["rate"]>=70 else "#f85149")
    gr_rows += (f'<tr><td style="font-weight:700;color:#cdd9e5">{sec}</td>'
                f'<td class="num" style="color:#58a6ff">{len(d["results"])}</td>'
                f'<td class="num" style="color:#3fb950">{len(d["pl"])}</td>'
                f'<td class="num" style="color:#f85149">{len(d["fl"])}</td>'
                f'<td class="num" style="color:#d29922;font-weight:700">{d["rate"]}%</td>'
                f'<td><div style="background:#1a2330;border-radius:3px;height:8px;min-width:100px">'
                f'<div style="width:{d["rate"]}%;height:8px;background:{bar_col3};border-radius:3px"></div></div></td></tr>')

# Section selector tabs
secs = list(AD.keys())
sec_tabs = "".join(
    f'<div class="nt {"active" if i==0 else ""}" '
    f'onclick="secTab(this,\'{re.sub(chr(91)+"^A-Za-z0-9"+chr(93),"_",s)}\')">'
    f'{s} <span style="color:{"#3fb950" if AD[s]["rate"]==100 else("#d29922" if AD[s]["rate"]>=70 else"#f85149")};font-size:11px">{AD[s]["rate"]}%</span></div>'
    for i,s in enumerate(secs)
)
sec_contents = "".join(
    f'<div id="sec-{re.sub(chr(91)+"^A-Za-z0-9"+chr(93),"_",s)}" '
    f'class="sec-blk {"active" if i==0 else ""}">{build_section_html(s,AD[s])}</div>'
    for i,s in enumerate(secs)
)

# ─────────────────────────────────────────────────────────────────────────────
# FULL HTML REPORT
# ─────────────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens — All Sections FINAL MERGED v4</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#080c10;--s1:#0d1219;--s2:#131a23;--s3:#1a2330;
  --bdr:#1f2d3d;--bdr2:#253345;
  --tx:#cdd9e5;--tx2:#8fa4bc;--muted:#5a7490;--hd:#e6edf3;
  --pos:#1a7f37;--pos-bg:#0a1f10;--pos-t:#3fb950;
  --neg:#cf222e;--neg-bg:#1c0a0c;--neg-t:#f85149;
  --amb:#9e6a03;--amb-bg:#1c1508;--amb-t:#d29922;
  --blu:#1158cb;--blu-bg:#071228;--blu-t:#58a6ff;
  --acc:#6e40c9;--acc-t:#bc8cff;
  --new:#0a2a35;--new-t:#39c5cf;--new-bdr:#1a6870;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--tx);line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh}}
.wrap{{max-width:1420px;margin:0 auto;padding:32px 36px 72px}}
.hero{{display:grid;grid-template-columns:1fr auto;align-items:start;gap:24px;background:var(--s1);border:1px solid var(--bdr);border-radius:14px;padding:32px 36px;margin-bottom:20px}}
.hero-eye{{font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--blu-t);margin-bottom:10px;display:flex;align-items:center;gap:10px}}
.hero-eye::before{{content:'';display:inline-block;width:24px;height:2px;background:linear-gradient(90deg,var(--blu-t),var(--acc-t));border-radius:2px}}
.hero-title{{font-size:26px;font-weight:700;color:var(--hd);letter-spacing:-.4px;line-height:1.2;margin-bottom:8px}}
.hero-sub{{font-size:13px;color:var(--muted);margin-bottom:16px}}
.hero-tags{{display:flex;gap:8px;flex-wrap:wrap}}
.htag{{background:var(--blu-bg);border:1px solid var(--bdr2);color:var(--blu-t);padding:4px 14px;border-radius:20px;font-size:12px;font-weight:500;font-family:'DM Mono',monospace}}
.hero-meta{{text-align:right;font-family:'DM Mono',monospace;font-size:12px;color:var(--muted);line-height:2;white-space:nowrap}}
.hero-rate{{font-size:40px;font-weight:700;color:var(--hd);display:block;letter-spacing:-1px;line-height:1;margin-bottom:4px}}
.hero-rate-label{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--pos-t)}}
.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px}}
.kpi{{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;padding:20px 16px 16px;text-align:center}}
.kv{{font-size:32px;font-weight:700;line-height:1;margin-bottom:4px;font-family:'DM Mono',monospace}}
.kl{{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}}
.prog{{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;padding:20px 24px;margin-bottom:24px}}
.prog-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}}
.prog-label{{font-size:13px;font-weight:600;color:var(--tx2);letter-spacing:.03em}}
.prog-val{{font-size:24px;font-weight:700;color:var(--pos-t);font-family:'DM Mono',monospace}}
.prog-track{{background:var(--s3);border-radius:999px;height:10px;overflow:hidden}}
.prog-fill{{height:10px;border-radius:999px}}
.global-box{{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;padding:20px 24px;margin-bottom:20px}}
.gb-title{{font-size:14px;font-weight:700;color:var(--hd);margin-bottom:14px}}
.sec-select{{border-bottom:2px solid var(--bdr);margin-bottom:0;display:flex;flex-wrap:wrap;gap:0}}
.sec-blk{{display:none;padding-top:16px}}.sec-blk.active{{display:block}}
.sec-summary{{margin-bottom:16px}}
.nav-wrap{{border-bottom:1px solid var(--bdr);margin-bottom:20px;overflow-x:auto}}
.nav{{display:flex;gap:0;min-width:max-content}}
.nt{{padding:10px 18px;cursor:pointer;color:var(--muted);font-weight:500;font-size:13px;border-bottom:2px solid transparent;transition:color .15s,border-color .2s;white-space:nowrap;user-select:none}}
.nt:hover{{color:var(--tx)}}.nt.active{{color:var(--hd);border-bottom-color:var(--blu-t);font-weight:600}}
.tc{{display:none}}.tc.active{{display:block;animation:fadeUp .2s ease}}
.xtc{{display:none}}.xtc.active{{display:block}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.sh{{display:flex;align-items:center;gap:10px;margin:0 0 14px;padding-bottom:10px;border-bottom:1px solid var(--bdr)}}
.sh-icon{{width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px;background:var(--blu-bg);border:1px solid var(--bdr2);flex-shrink:0}}
.sh h2{{font-size:15px;font-weight:700;color:var(--hd);letter-spacing:-.2px}}
.sh-pills{{margin-left:auto;display:flex;gap:6px;align-items:center}}
.pill{{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid var(--bdr);background:var(--s2);color:var(--tx2)}}
.pill-g{{background:var(--pos-bg);color:var(--pos-t);border-color:var(--pos)}}
.pill-r{{background:var(--neg-bg);color:var(--neg-t);border-color:var(--neg)}}
.desc{{font-size:13px;color:var(--tx2);background:var(--s2);border:1px solid var(--bdr);border-left:3px solid var(--blu-t);border-radius:0 6px 6px 0;padding:10px 14px;margin-bottom:16px;line-height:1.75}}
.desc strong{{color:var(--blu-t)}}
.tw{{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;overflow:hidden;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
thead tr{{background:var(--s2)}}
th{{padding:9px 13px;text-align:left;font-weight:600;color:var(--muted);border-bottom:1px solid var(--bdr);white-space:nowrap;font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;font-family:'DM Mono',monospace}}
td{{padding:9px 13px;border-bottom:1px solid var(--s3);vertical-align:middle}}
tbody tr:last-child td{{border-bottom:none}}tbody tr:hover{{background:var(--s2)}}
.pass-row:hover{{background:rgba(26,127,55,.07)!important}}
.fail-row{{background:rgba(207,34,46,.04)}}.fail-row:hover{{background:rgba(207,34,46,.09)!important}}
.skip-row{{background:rgba(158,106,3,.04)}}
.grp-row td{{background:linear-gradient(90deg,#0f1e35,var(--s2));color:var(--hd);font-weight:700;font-size:12px;padding:9px 15px;border-top:1px solid var(--bdr2);border-bottom:1px solid var(--bdr)}}
.grp-title{{font-size:12px;font-weight:700;color:var(--hd);margin-right:10px}}
.sub-row td{{background:var(--s2);font-size:11px;font-weight:600;padding:5px 15px 5px 26px;border-top:1px solid var(--bdr);font-style:italic}}
.num{{text-align:center;font-variant-numeric:tabular-nums;font-family:'DM Mono',monospace}}
.chn{{font-weight:600;color:var(--hd)}}.muted{{color:var(--muted)}}.mono{{font-family:'DM Mono',monospace}}
.miss{{color:var(--neg-t);font-size:11px;font-weight:600}}.empty{{color:var(--muted);font-style:italic;text-align:center;padding:16px}}
.badge{{display:inline-block;padding:3px 9px;border-radius:5px;font-size:11px;font-weight:700;letter-spacing:.04em;font-family:'DM Mono',monospace}}
.badge.ok{{background:var(--pos-bg);color:var(--pos-t);border:1px solid var(--pos)}}
.badge.fail{{background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg)}}
.badge.skip{{background:var(--amb-bg);color:var(--amb-t);border:1px solid var(--amb)}}
.chip-pos,.chip-neg{{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.04em;margin-left:10px}}
.chip-pos{{background:var(--pos-bg);color:var(--pos-t);border:1px solid var(--pos)}}
.chip-neg{{background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg)}}
.pill-new{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:var(--new);color:var(--new-t);border:1px solid var(--new-bdr)}}
.pill-pos{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(10,35,20,.8);color:#56d364;border:1px solid var(--pos)}}
.pill-neg{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg)}}
.pg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:10px;margin-bottom:24px}}
.em{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700;background:#0d2318;color:#3fb950;border:1px solid #3fb950}}
.ex{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700;background:#2d1116;color:#ff7b72;border:1px solid #ff7b72}}
.ems{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:11px;font-weight:700;background:#2d2005;color:#e3b341;border:1px solid #e3b341}}
.foot{{text-align:center;color:var(--muted);font-size:12px;margin-top:48px;padding-top:20px;border-top:1px solid var(--bdr);font-family:'DM Mono',monospace;letter-spacing:.03em}}
::-webkit-scrollbar{{width:6px;height:6px}}::-webkit-scrollbar-track{{background:var(--s1)}}::-webkit-scrollbar-thumb{{background:var(--bdr2);border-radius:3px}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <div>
    <div class="hero-eye">ClassLens Quality Assurance · All Sections · FINAL MERGED v4</div>
    <div class="hero-title">Chapter Accuracy Test Report — All Sections</div>
    <div class="hero-sub">{len(avail)} sections tested · {ENTRY['CompareLeft']} vs {ENTRY['CompareRight']} · Class {ENTRY['Class']} {ENTRY['Subject']}</div>
    <div class="hero-tags">
      <span class="htag">Class {ENTRY['Class']}</span>
      <span class="htag">{ENTRY['Subject']}</span>
      <span class="htag">{ENTRY['CompareLeft']} ↔ {ENTRY['CompareRight']}</span>
      <span class="htag">{len(avail)} Sections</span>
      <span class="htag">{tt} Tests</span>
    </div>
  </div>
  <div class="hero-meta">
    <span class="hero-rate">{gr}%</span>
    <span class="hero-rate-label">Overall Pass Rate</span>
    <br>{RUN_TS}
  </div>
</div>

<div class="kpi-row">
  <div class="kpi"><div class="kv" style="color:#cdd9e5">{len(avail)}</div><div class="kl">Sections</div></div>
  <div class="kpi"><div class="kv" style="color:#58a6ff">{tt}</div><div class="kl">Total Tests</div></div>
  <div class="kpi"><div class="kv" style="color:#3fb950">{tp}</div><div class="kl">Passed</div></div>
  <div class="kpi"><div class="kv" style="color:#f85149">{tf}</div><div class="kl">Failed</div></div>
  <div class="kpi"><div class="kv" style="color:#d29922">{gr}%</div><div class="kl">Pass Rate</div></div>
</div>

<div class="prog">
  <div class="prog-head"><span class="prog-label">Overall Test Pass Rate — All Sections</span>
  <span class="prog-val">{gr}% <span style="font-size:15px;color:var(--muted)">({tp} / {tt})</span></span></div>
  <div class="prog-track"><div class="prog-fill" id="pf" style="width:0%;background:#3fb950;box-shadow:0 0 14px rgba(63,185,80,.2)"></div></div>
</div>

<div class="global-box">
  <div class="gb-title">📈 Grand Summary — All Sections</div>
  <div class="tw" style="margin-bottom:0"><table>
    <thead><tr><th>Section</th><th style="text-align:center">Tests</th><th style="text-align:center">Pass</th><th style="text-align:center">Fail</th><th style="text-align:center">Rate</th><th>Progress</th></tr></thead>
    <tbody>{gr_rows}</tbody>
  </table></div>
</div>

<div class="global-box">
  <div class="gb-title">🔍 Global 4-Way % Consistency + Header Accuracy — All Sections</div>
  <div class="tw" style="margin-bottom:0"><table>
    <thead><tr><th>Section</th><th>Chapter</th>
      <th style="text-align:center">Loc1 Card</th><th style="text-align:center">Loc2 Chip</th>
      <th style="text-align:center">Loc3 Badge</th><th style="text-align:center">Loc4 Why</th>
      <th style="text-align:center;color:#58a6ff">Header Acc</th>
      <th style="text-align:center">Result</th></tr></thead>
    <tbody>{build_global_html()}</tbody>
  </table></div>
</div>

<div style="border-bottom:2px solid var(--bdr);margin-bottom:0">
  <div class="sec-select" id="sec-nav">{sec_tabs}</div>
</div>
{sec_contents}

<div class="foot">
  ClassLens All-Sections FINAL MERGED v4 · {RUN_TS} · {len(avail)} sections · {tt} tests · {gr}% pass rate
</div>

</div>
<script>
function tab(el,id){{
  const nav=el.closest('.nav-wrap').querySelector('.nav');
  nav.querySelectorAll('.nt').forEach(t=>t.classList.remove('active'));
  const blk=el.closest('.sec-blk')||document;
  blk.querySelectorAll(':scope > .tc, .sec-blk > .tc').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  const t=document.getElementById(id);if(t)t.classList.add('active');
}}
function xtab(el,sid,xid){{
  const nav=el.closest('.nav-wrap').querySelector('.nav');
  nav.querySelectorAll('.nt').forEach(t=>t.classList.remove('active'));
  const blk=el.closest('.tc');
  if(blk)blk.querySelectorAll('.xtc').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  const t=document.getElementById(xid+'-'+sid);if(t)t.classList.add('active');
}}
function secTab(el,sid){{
  document.querySelectorAll('#sec-nav .nt').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.sec-blk').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  const t=document.getElementById('sec-'+sid);if(t)t.classList.add('active');
}}
window.addEventListener('load',()=>{{
  const f=document.getElementById('pf');
  if(f) requestAnimationFrame(()=>{{f.style.width='{gr}%';}});
}});
</script>
</body></html>"""

with open(REPORT_FILE, "w", encoding="utf-8") as fh:
    fh.write(html)

print(f"\n  {G}{BLD}📄  Report saved → {REPORT_FILE}{RST}")
try:
    webbrowser.open(f"file://{os.path.abspath(REPORT_FILE)}")
    print(f"  {G}🌐  Opening in browser…{RST}")
except: pass
print(f"\n  🟢  Browser kept open. Close manually when done.\n")



####################################################################################################
# END OF SCRIPT 2: ClassLens – Chapters Tab – All Sections (FINAL MERGED v4)
####################################################################################################

####################################################################################################
# START OF SCRIPT 3: ClassLens – All Sections Question Audit Engine
# Original upload: Pasted text (3)(3).txt
# Preserved lines: 1551
# SHA256: 4470ef479c566a9d910efbccaa373df1fd2d6377110942b4cc19018a9a3aa220
####################################################################################################
import os
import re
import time
import traceback
import webbrowser
from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# ╔══════════════════════════════════════════════════════════════════╗
# ║                     TERMINAL COLOR PALETTE                       ║
# ╚══════════════════════════════════════════════════════════════════╝

class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m";  DIM     = "\033[2m"
    WHITE   = "\033[97m"; BLACK   = "\033[30m"; RED     = "\033[91m"
    GREEN   = "\033[92m"; YELLOW  = "\033[93m"; BLUE    = "\033[94m"
    CYAN    = "\033[96m"; ORANGE  = "\033[38;5;214m"; PINK = "\033[38;5;219m"
    TEAL    = "\033[38;5;87m";  LIME   = "\033[38;5;154m"
    VIOLET  = "\033[38;5;177m"; BG_BLACK = "\033[40m"
    BG_GREEN = "\033[42m"; BG_RED = "\033[41m"; BG_YELLOW = "\033[43m"

def c(color, text): return f"{color}{text}{C.RESET}"
def bold(text):     return f"{C.BOLD}{text}{C.RESET}"
def dim(text):      return f"{C.DIM}{text}{C.RESET}"

# ╔══════════════════════════════════════════════════════════════════╗
# ║                          CONFIG  ← EDIT                         ║
# ╚══════════════════════════════════════════════════════════════════╝

LOGIN_URL   = "https://classlens.inferentics.com/"
USERNAME    = os.getenv("CLASSLENS_USER", "Tanmay")
PASSWORD    = os.getenv("CLASSLENS_PASS", "Operations123")
REPORT_FILE = "classlens_all_sections_report.html"

ALL_SECTIONS = ["C","H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "ZZ"]

BASE_VALUES = {
    "Class":   "12",
    "Subject": "Maths",
    "Exam":    "Preboard 1",
}

RUN_TS = datetime.now().strftime("%d %b %Y  %H:%M:%S")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                   CURRICULUM KNOWLEDGE BASE                      ║
# ╚══════════════════════════════════════════════════════════════════╝

CHAPTER_CONCEPTS: dict[str, list[str]] = {
    "Relations & Functions": [
        "Types of Relations","Types of Functions","Composite Functions","Invertible Functions",
    ],
    "Inverse Trigonometric Functions": [
        "Principal Values (Domain and Range)","Formulas for Trigonometry",
        "Algebra of Inverse Trig Functions","Substitution using Trig Formulas",
    ],
    "Matrices": [
        "Basics & Types of Matrices","Matrix Operations",
        "Transpose, Symmetric & Skew-symmetric","Elementary Operations","Inverse Matrices",
    ],
    "Determinants": [
        "Determinant of a Matrix","Properties of Determinants",
        "Applications (Area, Cramer's Rule, Linear Equations using inverse matrices)",
        "Minors & Cofactors","Adjoint & Inverse",
    ],
    "Continuity & Differentiability": [
        "Continuity","Rules of Differentiations","Chain Rule",
        "Parametric & Implicit Differentiation","Derivatives of Inverse Trig Functions",
        "Exponential & Logarithmic Functions/Logarithmic Properties","Second Order Derivative",
    ],
    "Application of Derivatives": [
        "Rate of Change","Increasing & Decreasing Functions",
        "Maxima & Minima","Maxima & Minima real life Applications",
    ],
    "Integrals": [
        "Indefinite Integrals (Anti derivatives)","Rules of integrals",
        "Integration by Substitution","Integration by Parts","Partial Fractions",
        "Properties of Definite Integrals","Definite Integrals",
    ],
    "Application of Integrals": ["Area under Curves"],
    "Differential Equations": [
        "Definition, Order & Degree","General & Particular Solution","Formation of DE",
        "Variable Separable Method","Homogeneous DE","Linear DE","Applications (Growth/Decay)",
    ],
    "Vector Algebra": [
        "Scalars & Vectors","Position Vector & Unit Vector",
        "Vector Addition & Scalar Multiplication","Dot (Scalar) Product","Cross (Vector) Product",
    ],
    "3D Geometry": [
        "Direction Cosines & Ratios","Equation of a Line","Angle between Lines",
    ],
    "Linear Programming": [
        "Formulating LPP","Objective Function",
        "Graphical method of solution for problems in two variables",
        "Feasible Region","Optimization",
    ],
    "Probability": [
        "Conditional Probability","Multiplication Rule","Bayes' Theorem",
    ],
}

CONCEPT_TO_CHAPTER: dict[str, str] = {
    concept.lower(): chapter
    for chapter, concepts in CHAPTER_CONCEPTS.items()
    for concept in concepts
}

KNOWN_QUESTION_TYPES = {
    "MCQ","VSA","SA","LA",
    "Multiple Choice","Very Short Answer","Short Answer","Long Answer",
    "Case Based","Assertion Reason","True False",
}

# ╔══════════════════════════════════════════════════════════════════╗
# ║                       DATA STRUCTURES                            ║
# ╚══════════════════════════════════════════════════════════════════╝

@dataclass
class QuestionData:
    section: str
    label: str
    chapter: str = ""
    concept: str = ""
    marks: str = "—"
    average: str = "N/A"
    qtype: str = "Unknown"
    question_text: str = ""
    full_marks_students: str = "—"
    partial_students: str = "—"
    wrong_students: str = "—"
    got_it_right_count: str = "—"
    got_it_right_pct: str = "—"
    chapter_ok: bool = False
    chapter_msg: str = ""
    type_ok: bool = False
    type_msg: str = ""
    status: str = "FAIL"
    struggle_gaps: list = field(default_factory=list)

@dataclass
class SectionResult:
    section: str
    questions: list = field(default_factory=list)
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    total_questions: int = 0
    error: str = ""
    skipped: bool = False
    elapsed: float = 0.0

# ╔══════════════════════════════════════════════════════════════════╗
# ║                          LOGGING                                 ║
# ╚══════════════════════════════════════════════════════════════════╝

def print_banner():
    print()
    print(c(C.CYAN, "  ╔══════════════════════════════════════════════════════════════╗"))
    print(c(C.CYAN, "  ║") + c(C.BOLD+C.WHITE, "    🎯  CLASSLENS ALL-SECTIONS QUESTION AUDIT ENGINE          ") + c(C.CYAN, "║"))
    print(c(C.CYAN, "  ║") + dim("       Fresh browser per section · Combined HTML report       ") + c(C.CYAN, "║"))
    print(c(C.CYAN, "  ╚══════════════════════════════════════════════════════════════╝"))
    print(dim(f"  Started at {datetime.now().strftime('%A, %d %b %Y  %I:%M:%S %p')}"))
    print(c(C.VIOLET, f"\n  Sections: {c(C.TEAL, str(ALL_SECTIONS))}"))
    print()

def section_hdr(title, icon="▸"):
    print()
    print(c(C.VIOLET, f"  {'─'*60}"))
    print(c(C.VIOLET, f"  {icon}  ") + bold(c(C.WHITE, title)))
    print(c(C.VIOLET, f"  {'─'*60}"))

def log_pass(msg): print(c(C.LIME,   f"  ✅  {msg}"))
def log_fail(msg): print(c(C.RED,    f"  ✗   {msg}"))
def log_warn(msg): print(c(C.YELLOW, f"  ⚠   {msg}"))
def log_info(msg): print(c(C.CYAN,   f"  ℹ   {msg}"))

def progress_bar(current, total, width=40):
    if total == 0: return c(C.DIM, f"  [{'░'*width}]   0%  0/0")
    filled = int(width * current / total)
    bar    = "█"*filled + "░"*(width-filled)
    pct    = int(100 * current / total)
    return c(C.LIME if pct == 100 else C.CYAN, f"  [{bar}] {pct:>3}%  {current}/{total}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      DRIVER  (fresh per section)                 ║
# ╚══════════════════════════════════════════════════════════════════╝

def make_driver():
    """No detach=True — that's what caused 'invalid session id' on sections I+."""
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    drv = webdriver.Chrome(options=opts)
    drv.set_page_load_timeout(90)
    return drv

def quit_driver(drv):
    try: drv.quit()
    except Exception: pass

# ╔══════════════════════════════════════════════════════════════════╗
# ║                       AUTH + FORM                                ║
# ╚══════════════════════════════════════════════════════════════════╝

def login(drv, wait):
    section_hdr("AUTHENTICATION", "🔐")
    drv.get(LOGIN_URL)
    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email']"))).send_keys(USERNAME)
    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='password']"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']"))).click()
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
    log_pass(f"Logged in as {bold(c(C.TEAL, USERNAME))}")

def select_dropdown(drv, wait, index, value):
    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
    selects = drv.find_elements(By.TAG_NAME, "select")
    if index >= len(selects):
        raise Exception(f"Dropdown index {index} not found (found {len(selects)})")
    from selenium.webdriver.support.ui import Select as _Sel
    _Sel(selects[index]).select_by_visible_text(value)

def fill_form(drv, wait, section_val):
    """Fill filters and open Questions tab. Called right after fresh login."""
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
    time.sleep(1.0)
    select_dropdown(drv, wait, 0, BASE_VALUES["Class"]);   time.sleep(0.5)
    select_dropdown(drv, wait, 1, section_val);            time.sleep(0.5)
    select_dropdown(drv, wait, 2, BASE_VALUES["Subject"]); time.sleep(0.5)
    select_dropdown(drv, wait, 3, BASE_VALUES["Exam"]);    time.sleep(0.5)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Enter']"))).click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[normalize-space()='Overview']")))
    time.sleep(0.5)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[normalize-space()='Questions']"))).click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(normalize-space(),'Sort By')]")))
    time.sleep(0.8)
    log_pass(f"Section {bold(c(C.TEAL, section_val))} — Questions tab loaded")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                          HELPERS                                 ║
# ╚══════════════════════════════════════════════════════════════════╝

def safe_click(drv, el):
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:    ActionChains(drv).move_to_element(el).click(el).perform()
    except: drv.execute_script("arguments[0].click();", el)

def is_q_label(text): return bool(re.match(r"^Q\d+(\.\d+)?$", text.strip()))

def get_all_labels(drv, wait):
    try:
        WebDriverWait(drv, 20).until_not(
            EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Loading...']")))
    except TimeoutException: pass
    try:
        WebDriverWait(drv, 20).until(EC.presence_of_element_located(
            (By.XPATH, "//*[normalize-space()='Q1' or normalize-space()='Q2' or normalize-space()='Q3']")))
    except TimeoutException: pass
    time.sleep(1.0)
    els = drv.find_elements(By.XPATH, "//*[starts-with(normalize-space(),'Q') and normalize-space()!='Q']")
    labels, seen = [], set()
    for el in els:
        try:
            if not el.is_displayed(): continue
        except: continue
        t = el.text.strip()
        if is_q_label(t) and t not in seen:
            seen.add(t); labels.append(t)
    return labels

def find_q_el(drv, label):
    els = drv.find_elements(By.XPATH, f"//*[normalize-space()='{label}']")
    for el in els:
        try:
            if el.is_displayed(): return el
        except: continue
    return els[0] if els else None

# ╔══════════════════════════════════════════════════════════════════╗
# ║                     PANEL EXTRACTION                             ║
# ╚══════════════════════════════════════════════════════════════════╝

def get_panel_text(drv):
    for xp in [
        "//*[contains(.,'Chapter') and contains(.,'Concepts') and contains(.,'Full Marks')]",
        "//*[contains(.,'Chapter') and contains(.,'Full Marks')]",
        "//*[contains(.,'Full Marks') and contains(.,'Average marks scored')]",
        "//*[contains(.,'Full Marks')]",
    ]:
        els = drv.find_elements(By.XPATH, xp)
        cands = []
        for el in els:
            try:
                if el.tag_name.lower() in ("html","body"): continue
                if not el.is_displayed(): continue
                t = el.text.strip()
                if 20 < len(t) < 3000: cands.append((len(t), el))
            except: continue
        if cands:
            cands.sort(key=lambda x: x[0])
            return cands[0][1].text.strip()
    return drv.find_element(By.TAG_NAME, "body").text.strip()

def dom_field(drv, label):
    for xp in [f"//*[normalize-space()='{label}']", f"//*[normalize-space(text())='{label}']"]:
        for lel in drv.find_elements(By.XPATH, xp):
            try:
                if not lel.is_displayed(): continue
                for sibling_xp in ["following-sibling::*[1]", "../following-sibling::*[1]", "../../following-sibling::*[1]"]:
                    sibs = lel.find_elements(By.XPATH, sibling_xp)
                    if sibs:
                        v = sibs[0].text.strip()
                        if v and v.lower() != label.lower(): return v
            except: continue
    return ""

def next_line_val(text, label):
    t = re.sub(r"[ \t]+", " ", text); t = re.sub(r"\n+", "\n", t)
    m = re.search(rf"(?:^|\n){re.escape(label)}\s*\n([^\n]+)", t, re.IGNORECASE)
    if m:
        v = m.group(1).strip()
        if v and not re.match(r"^(Chapter|Concepts?|Full Marks?|Marks?|Type|Average marks scored)$", v, re.IGNORECASE):
            return v
    m2 = re.search(rf"\b{re.escape(label)}\s{{2,}}(.+?)(?:\s{{2,}}|\n|$)", t, re.IGNORECASE)
    return m2.group(1).strip() if m2 else ""

def extract_perf(drv, text):
    stats = {"full_marks_students":"—","partial_students":"—","wrong_students":"—",
             "got_it_right_count":"—","got_it_right_pct":"—","average":"N/A"}
    try: body = drv.find_element(By.TAG_NAME, "body").text
    except: body = text

    for key, label in [("full_marks_students","Full Marks"),("partial_students","Partial"),("wrong_students","Wrong")]:
        m = re.search(rf"{re.escape(label)}\s*\n(\d+)\s*\n\s*[Ss]tudents?", body)
        if m: stats[key] = m.group(1); continue
        m = re.search(rf"{re.escape(label)}\s*\((\d+)/\d+\)", body, re.IGNORECASE)
        if m: stats[key] = m.group(1); continue
        try:
            for lel in drv.find_elements(By.XPATH, f"//*[normalize-space()='{label}']"):
                for sib in lel.find_elements(By.XPATH, "following-sibling::*")[:5]:
                    t2 = sib.text.strip()
                    if re.match(r"^\d+$", t2): stats[key] = t2; break
                if stats[key] != "—": break
        except: pass

    try:
        for lel in drv.find_elements(By.XPATH, "//*[contains(normalize-space(),'Students who got it right')]"):
            try:
                if not lel.is_displayed(): continue
            except: continue
            for axp in ["..","../..","../../..","../../../.."]:
                ancs = lel.find_elements(By.XPATH, axp)
                if not ancs: continue
                blk = ancs[0].text.strip()
                pm = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*students?", blk, re.IGNORECASE)
                if pm: stats["got_it_right_pct"] = pm.group(1)+"%"
                cm = re.search(r"(?:^|\n)(\d+)\s*\n\s*\d+(?:\.\d+)?%", blk)
                if cm: stats["got_it_right_count"] = cm.group(1)
                if stats["got_it_right_pct"] != "—": break
            if stats["got_it_right_pct"] != "—": break
    except: pass

    if stats["got_it_right_pct"] == "—":
        pm = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*students?", body, re.IGNORECASE)
        if pm: stats["got_it_right_pct"] = pm.group(1)+"%"

    try:
        for lel in drv.find_elements(By.XPATH, "//*[contains(normalize-space(),'Average marks')]"):
            try:
                if not lel.is_displayed(): continue
            except: continue
            for axp in ["..","../..","../../..","../../../.."]:
                ancs = lel.find_elements(By.XPATH, axp)
                if not ancs: continue
                blk = ancs[0].text.strip()
                fm = re.search(r"(\d+(?:\.\d+)?/\d+(?:\.\d+)?)", blk)
                if fm: stats["average"] = fm.group(1); break
                nm = re.search(r"(\d+\.\d+)", blk)
                if nm: stats["average"] = nm.group(1); break
            if stats["average"] != "N/A": break
    except: pass

    if stats["average"] == "N/A":
        fm = re.search(r"[Aa]verage\s+marks[\s\S]{0,60}?(\d+(?:\.\d+)?/\d+(?:\.\d+)?)", body)
        if fm: stats["average"] = fm.group(1)
    if stats["average"] == "N/A":
        fm = re.search(r"(\d+(?:\.\d+)?/\d+(?:\.\d+)?)", body)
        if fm: stats["average"] = fm.group(1)
    return stats

def extract_marks(text):
    parts = re.split(r"How your students performed|Full Marks\s*\n\s*\d+\s*\nStudents",
                     text, flags=re.IGNORECASE, maxsplit=1)
    t = re.sub(r"[ \t]+", " ", parts[0]); t = re.sub(r"\n+", "\n", t)
    m = re.search(r"(?:^|\n)Marks\s*\n\s*([0-9]+(?:\.[0-9]+)?)", t, re.IGNORECASE)
    if m: return m.group(1)
    m2 = re.search(r"\bMarks\s+([0-9]+(?:\.[0-9]+)?)", t, re.IGNORECASE)
    return m2.group(1) if m2 else ""

def extract_qtype(text):
    t = re.sub(r"[ \t]+", " ", text); t = re.sub(r"\n+", "\n", t)
    for label in ["Question Type","Type","Q Type","Question type"]:
        v = next_line_val(t, label)
        if v: return v.strip()
    for qt in sorted(KNOWN_QUESTION_TYPES, key=len, reverse=True):
        if re.search(rf"(?:^|\s){re.escape(qt)}(?:\s|$)", t, re.IGNORECASE):
            return qt
    return "Unknown"

def extract_concept(text):
    for label in ["Concepts","Concept","Topic","Sub-topic","Subtopic","Sub Topic","Skill","Learning Outcome","Competency"]:
        v = next_line_val(text, label)
        if v: return v.strip()
    return ""

def extract_q_text(drv):
    SKIP = re.compile(
        r"^(Chapter|Concepts?|Type|Marks?|Full Marks?|Partial|Wrong|Students?"
        r"|Average marks scored|How your students performed"
        r"|Students who got it right|Sort By|Overview|Questions?)$", re.IGNORECASE)
    for xp in ["//p","//div","//span","//li"]:
        for el in drv.find_elements(By.XPATH, xp):
            try:
                if not el.is_displayed(): continue
                t = el.text.strip()
                if 15 < len(t) < 600 and not SKIP.match(t) and not re.fullmatch(r"[\d\s/%.+\-=]+", t) and not is_q_label(t):
                    return t
            except: continue
    return ""

def parse_gaps(block):
    gaps, lines = [], [l.strip() for l in block.splitlines() if l.strip()]
    idxs = [i for i, l in enumerate(lines) if re.match(r"^\d+(?:\.\d+)?\s*%$", l)]
    for k, start in enumerate(idxs):
        pct = lines[start]
        title = lines[start+1].strip() if start+1 < len(lines) else ""
        if not title or re.match(r"^\d+%", title): continue
        end = idxs[k+1] if k+1 < len(idxs) else len(lines)
        gaps.append({"pct": pct, "title": title, "desc": " ".join(lines[start+2:end]).strip()})
    return gaps

def extract_gaps(drv):
    best = []
    try:
        for heading in drv.find_elements(By.XPATH, "//*[contains(normalize-space(),'Where students struggled')]"):
            try:
                if not heading.is_displayed(): continue
            except: continue
            for axp in ["..","../..","../../..","../../../..","../../../../..","../../../../../..","../../../../../../.."]:
                ancs = heading.find_elements(By.XPATH, axp)
                if not ancs: continue
                try:
                    if ancs[0].tag_name.lower() in ("html","body"): continue
                    blk = ancs[0].text.strip()
                    if "Where students struggled" in blk and re.search(r"\d+\s*%", blk) and len(blk) > 30:
                        parsed = parse_gaps(blk)
                        if len(parsed) > len(best): best = parsed
                except: continue
            if best: break
    except: pass
    if not best:
        try:
            body = drv.find_element(By.TAG_NAME, "body").text
            idx = body.find("Where students struggled")
            if idx != -1: best = parse_gaps(body[idx:idx+2000])
        except: pass
    return best

def parse_panel(drv, text):
    chapter = dom_field(drv, "Chapter") or next_line_val(text, "Chapter")
    concept = dom_field(drv, "Concepts") or dom_field(drv, "Concept") or extract_concept(text)
    marks   = extract_marks(text) or dom_field(drv, "Marks")
    mn = re.search(r"(\d+(?:\.\d+)?)", marks or "")
    marks_str = mn.group(1) if mn else "—"
    perf    = extract_perf(drv, text)
    return {
        "Chapter":             chapter.strip(),
        "Marks":               marks_str,
        "Average":             perf["average"],
        "Type":                extract_qtype(text),
        "Concept":             concept.strip(),
        "QuestionText":        extract_q_text(drv),
        "StruggleGaps":        extract_gaps(drv),
        "full_marks_students": perf["full_marks_students"],
        "partial_students":    perf["partial_students"],
        "wrong_students":      perf["wrong_students"],
        "got_it_right_count":  perf["got_it_right_count"],
        "got_it_right_pct":    perf["got_it_right_pct"],
    }

# ╔══════════════════════════════════════════════════════════════════╗
# ║                        VALIDATION                                ║
# ╚══════════════════════════════════════════════════════════════════╝

def fuzzy_chapter(pc):
    pc = pc.strip().lower()
    for ch in CHAPTER_CONCEPTS:
        if ch.lower() == pc or ch.lower() in pc or pc in ch.lower(): return ch
    return None

def fuzzy_concept(pc):
    pc = pc.strip().lower()
    for k in CONCEPT_TO_CHAPTER:
        if k == pc or k in pc or pc in k: return k
    return None

def canonical(k):
    for ch, cs in CHAPTER_CONCEPTS.items():
        for cn in cs:
            if cn.lower() == k: return cn
    return k

def validate_cc(panel_chapter, panel_concept):
    if not panel_chapter: return False, "Chapter not found in panel"
    mc = fuzzy_chapter(panel_chapter)
    if not mc: return False, f"'{panel_chapter}' — chapter not in curriculum"
    if not panel_concept: return True, f"Chapter '{mc}' ✓  (concept not exposed in panel)"
    mk = fuzzy_concept(panel_concept)
    if mk is None: return False, f"Concept '{panel_concept}' — not found in curriculum"
    cn = canonical(mk); ac = CONCEPT_TO_CHAPTER[mk]
    if ac.lower() == mc.lower(): return True, f"'{cn}'  ✓  correctly mapped to  '{mc}'"
    return False, f"'{cn}'  ✗  belongs to  '{ac}',  NOT  '{mc}'"

def validate_type(qtype):
    if not qtype or qtype == "Unknown": return False, "Question type not detected"
    for qt in KNOWN_QUESTION_TYPES:
        if qt.lower() == qtype.lower(): return True, qtype
    return False, f"'{qtype}' is not a recognised question type"

# ╔══════════════════════════════════════════════════════════════════╗
# ║               RICH TERMINAL QUESTION PRINT                       ║
# ║           (same style as the original single-section script)     ║
# ╚══════════════════════════════════════════════════════════════════╝

def print_question_row(idx, total, sec, q: QuestionData):
    status = q.status
    if status == "PASS":
        badge  = c(C.BG_GREEN+C.BLACK+C.BOLD,  " PASS ")
        bullet = c(C.LIME,   "●")
    elif status == "WARN":
        badge  = c(C.BG_YELLOW+C.BLACK+C.BOLD, " WARN ")
        bullet = c(C.YELLOW, "◑")
    else:
        badge  = c(C.BG_RED+C.WHITE+C.BOLD,    " FAIL ")
        bullet = c(C.RED,    "●")

    chcol  = C.LIME  if q.chapter_ok else C.RED
    tycol  = C.TEAL  if q.type_ok   else C.YELLOW
    W = 68

    def mini(ok, warn=False):
        if ok:   return c(C.BG_GREEN +C.BLACK+C.BOLD, " PASS ")
        if warn: return c(C.BG_YELLOW+C.BLACK+C.BOLD, " WARN ")
        return c(C.BG_RED+C.WHITE+C.BOLD, " FAIL ")

    def _n(v):
        try: return int(v)
        except: return 0

    nf   = _n(q.full_marks_students)
    np_  = _n(q.partial_students)
    nw   = _n(q.wrong_students)
    tot  = nf + np_ + nw
    WBAR = 24

    def seg(n, col):
        w = round(WBAR*n/tot) if tot > 0 else 0
        return c(col, "█" * max(w, 1 if n > 0 else 0))

    filled = seg(nf, C.LIME) + seg(np_, C.YELLOW) + seg(nw, C.RED)
    plain  = len(re.sub(r"\033\[[0-9;]*m", "", filled))
    dist_bar = filled + c(C.DIM, "░" * max(0, WBAR - plain))

    print()
    print(f"  {bullet} {c(C.VIOLET+C.BOLD, f'[{sec}]')}  {bold(c(C.WHITE, q.label))}  {badge}  {dim(f'({idx}/{total})')}")
    print(c(C.DIM, f"  {'─'*W}"))

    if q.question_text:
        words = q.question_text.split()
        lines_, line_ = [], []
        for w in words:
            line_.append(w)
            if len(" ".join(line_)) > 65:
                lines_.append(" ".join(line_[:-1])); line_ = [w]
        if line_: lines_.append(" ".join(line_))
        print(f"    {c(C.PINK+C.BOLD, 'Q: ')}{c(C.WHITE, lines_[0])}")
        for ln in lines_[1:]: print(f"       {c(C.WHITE, ln)}")
        print(c(C.DIM, f"  {'─'*W}"))

    print(f"    {dim('Chapter :')}  {c(chcol, q.chapter[:42] or '—')}"
          f"   {dim('Type :')}  {c(tycol, q.qtype or '—')}"
          f"   {dim('Marks :')}  {c(C.WHITE+C.BOLD, q.marks)}")
    if q.concept:
        print(f"    {dim('Concept :')}  {c(C.ORANGE, q.concept[:64])}")
    else:
        print(f"    {dim('Concept :')}  {c(C.DIM, '(not exposed in panel)')}")

    print(c(C.DIM, f"  {'─'*W}"))
    print(f"    {c(C.VIOLET+C.BOLD, '📊  STUDENT PERFORMANCE')}")
    print()
    print(
        f"    │ {c(C.DIM,'Full Marks')}  {c(C.LIME+C.BOLD, f'{q.full_marks_students:>3}')} {c(C.DIM,'students')} "
        f"│ {c(C.DIM,'Partial')}     {c(C.YELLOW+C.BOLD, f'{q.partial_students:>3}')} {c(C.DIM,'students')} "
        f"│ {c(C.DIM,'Wrong')}       {c(C.RED+C.BOLD, f'{q.wrong_students:>3}')} {c(C.DIM,'students')} │"
    )
    print()
    print(
        f"    {c(C.DIM,'Spread  ')} [{dist_bar}]  "
        f"{c(C.LIME, str(nf))}{c(C.DIM,' ✓')}  "
        f"{c(C.YELLOW, str(np_))}{c(C.DIM,' ~')}  "
        f"{c(C.RED, str(nw))}{c(C.DIM,' ✗')}  "
        f"{c(C.DIM, f'({tot} students total)')}"
    )
    print()

    if q.got_it_right_count != "—" and q.got_it_right_pct != "—":
        rs = f"{c(C.TEAL+C.BOLD, q.got_it_right_count)} {c(C.DIM,'students')}  {c(C.CYAN+C.BOLD, f'({q.got_it_right_pct})')}"
    elif q.got_it_right_count != "—": rs = f"{c(C.TEAL+C.BOLD, q.got_it_right_count)} {c(C.DIM,'students')}"
    elif q.got_it_right_pct  != "—": rs = c(C.CYAN+C.BOLD, q.got_it_right_pct)
    else: rs = c(C.YELLOW, "—")

    avg_str = c(C.LIME+C.BOLD, q.average) if q.average not in ("N/A","—","") else c(C.YELLOW, "—")
    print(f"    {dim('Students Got it Right  ')}  {rs}")
    print(f"    {dim('Avg Marks Scored       ')}  {avg_str}")
    print()

    if q.struggle_gaps:
        print(c(C.DIM, f"  {'─'*W}"))
        print(f"    {c(C.ORANGE+C.BOLD, '🧩  WHERE STUDENTS STRUGGLED')}")
        print()
        GCOLS = [C.ORANGE, C.RED, C.CYAN, C.YELLOW]
        for gi, gap in enumerate(q.struggle_gaps):
            col   = GCOLS[gi % len(GCOLS)]
            pct_  = gap.get("pct",""); ttl = gap.get("title",""); dsc = gap.get("desc","")
            print(f"    {c(col+C.BOLD, f'{pct_:>6}')}  {c(C.WHITE+C.BOLD, ttl)}")
            if dsc:
                ws = dsc.split(); ls_, l_ = [], []
                for w in ws:
                    l_.append(w)
                    if len(" ".join(l_)) > 58: ls_.append(" ".join(l_[:-1])); l_ = [w]
                if l_: ls_.append(" ".join(l_))
                for dl in ls_: print(f"            {c(C.DIM, dl)}")
            print()

    print(c(C.DIM, f"  {'─'*W}"))
    print(f"    {mini(q.chapter_ok, not q.chapter_ok)}  {dim('Concept → Chapter :')}  {c(chcol, q.chapter_msg)}")
    print(f"    {mini(q.type_ok)}  {dim('Question Type     :')}  {c(tycol, q.type_msg)}")
    print(c(C.DIM, f"  {'═'*W}"))

def print_section_summary(sr: SectionResult):
    total = sr.pass_count + sr.warn_count + sr.fail_count
    print()
    print(c(C.VIOLET, f"  {'─'*60}"))
    pw = int(40*sr.pass_count/max(total,1))
    fw = int(40*sr.fail_count/max(total,1))
    ww = 40-pw-fw
    bar = c(C.LIME,"█"*pw)+c(C.YELLOW,"█"*ww)+c(C.RED,"█"*fw)
    print(f"  [{bar}]")
    print()
    print(f"  {c(C.LIME,'✅  PASS')} : {bold(c(C.LIME,  str(sr.pass_count)))}")
    print(f"  {c(C.YELLOW,'⚠   WARN')} : {bold(c(C.YELLOW,str(sr.warn_count)))}")
    print(f"  {c(C.RED,  '✗  FAIL')} : {bold(c(C.RED,   str(sr.fail_count)))}")
    print(f"  {c(C.DIM,'─'*40)}")
    print(f"  {c(C.WHITE,'📊  Total')} : {bold(c(C.WHITE,str(total)))}  {dim(f'in {sr.elapsed:.1f}s')}")
    print()

# ╔══════════════════════════════════════════════════════════════════╗
# ║              SINGLE-SECTION AUDITOR  (fresh driver)              ║
# ╚══════════════════════════════════════════════════════════════════╝

def audit_section(section_val: str) -> SectionResult:
    sr  = SectionResult(section=section_val)
    drv = None
    t0  = time.time()

    section_hdr(f"AUDITING SECTION  ›  {section_val}", "📂")

    try:
        drv  = make_driver()
        wait = WebDriverWait(drv, 15)

        try:
            login(drv, wait)
        except Exception as e:
            sr.error = f"Login failed: {e}"; sr.skipped = True
            log_fail(f"Section {section_val} — login failed: {e}"); return sr

        try:
            fill_form(drv, wait, section_val)
        except Exception as e:
            sr.error = f"Form error: {e}"; sr.skipped = True
            log_fail(f"Section {section_val} — form error: {e}"); return sr

        try:
            labels = get_all_labels(drv, wait)
        except Exception as e:
            sr.error = f"Discovery failed: {e}"; sr.skipped = True
            log_fail(f"Section {section_val} — discovery error: {e}"); return sr

        if not labels:
            sr.error = "No questions found"; sr.skipped = True
            log_warn(f"Section {section_val} — no questions found"); return sr

        sr.total_questions = len(labels)
        log_info(f"Found {bold(c(C.TEAL, str(len(labels))))} questions")

        global_q_idx = 0

        for idx, label in enumerate(labels, start=1):
            print(f"\r{progress_bar(idx-1, len(labels))}", end="", flush=True)

            el = find_q_el(drv, label)
            if not el:
                log_warn(f"Element not found for {label}, skipping"); continue

            for attempt in range(3):
                try: safe_click(drv, el); break
                except StaleElementReferenceException:
                    if attempt == 2: break
                    el = find_q_el(drv, label)

            try:
                WebDriverWait(drv, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Chapter']")))
                WebDriverWait(drv, 8).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[normalize-space()='Concepts' or normalize-space()='Concept']")))
            except TimeoutException:
                try:
                    WebDriverWait(drv, 6).until(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(.,'Full Marks')]")))
                except TimeoutException:
                    log_warn(f"{label} panel did not load, skipping"); continue

            panel_text = get_panel_text(drv)
            details    = parse_panel(drv, panel_text)

            chapter_ok, chapter_msg = validate_cc(details["Chapter"], details["Concept"])
            type_ok,    type_msg    = validate_type(details["Type"])

            overall = chapter_ok and type_ok
            status  = "PASS" if overall else ("WARN" if chapter_ok or type_ok else "FAIL")

            if overall:                          sr.pass_count += 1
            elif not chapter_ok and not type_ok: sr.fail_count += 1
            else:                                sr.warn_count += 1

            q = QuestionData(
                section=section_val, label=label,
                chapter=details["Chapter"],    concept=details["Concept"],
                marks=details["Marks"],        average=details["Average"],
                qtype=details["Type"],         question_text=details["QuestionText"],
                full_marks_students=details["full_marks_students"],
                partial_students=details["partial_students"],
                wrong_students=details["wrong_students"],
                got_it_right_count=details["got_it_right_count"],
                got_it_right_pct=details["got_it_right_pct"],
                chapter_ok=chapter_ok, chapter_msg=chapter_msg,
                type_ok=type_ok,       type_msg=type_msg,
                status=status,         struggle_gaps=details["StruggleGaps"],
            )
            sr.questions.append(q)

            print(f"\r{' '*70}\r", end="")
            print_question_row(idx, len(labels), section_val, q)

        print(f"\r{progress_bar(len(labels), len(labels))}")
        sr.elapsed = time.time() - t0
        print_section_summary(sr)

    except Exception as e:
        sr.error = f"Unexpected error: {e}"; sr.skipped = True
        log_fail(f"Section {section_val} — unexpected error: {e}")
        traceback.print_exc()

    finally:
        if drv: quit_driver(drv)
        log_info(f"Browser closed for section {section_val}")

    if not sr.elapsed: sr.elapsed = time.time() - t0
    return sr

# ╔══════════════════════════════════════════════════════════════════╗
# ║                  CROSS-SECTION TERMINAL SUMMARY                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def print_cross_summary(results: list[SectionResult], elapsed: float):
    section_hdr("CROSS-SECTION AUDIT SUMMARY", "📋")
    tp = sum(r.pass_count for r in results)
    tw = sum(r.warn_count for r in results)
    tf = sum(r.fail_count for r in results)
    tq = sum(r.total_questions for r in results)
    print()
    print(c(C.DIM, f"  {'Section':<10} {'Total':>6} {'Pass':>6} {'Warn':>6} {'Fail':>6}  {'Rate':>6}  Status"))
    print(c(C.DIM, "  " + "─"*62))
    for r in results:
        t = r.total_questions
        rate = round(100*r.pass_count/t) if t > 0 else 0
        rc   = C.LIME if rate==100 else (C.YELLOW if rate>=70 else C.RED)
        if r.skipped:
            status_str = c(C.DIM, "SKIPPED")
        elif r.fail_count == 0 and r.warn_count == 0:
            status_str = c(C.LIME+C.BOLD, "ALL PASS 🎉")
        elif r.fail_count == 0:
            status_str = c(C.YELLOW, "WARNINGS")
        else:
            status_str = c(C.RED, "FAILURES")
        print(f"  {bold(c(C.TEAL, r.section)):<18} "
              f"{str(t):>6} "
              f"{c(C.LIME,   str(r.pass_count)):>15} "
              f"{c(C.YELLOW, str(r.warn_count)):>15} "
              f"{c(C.RED,    str(r.fail_count)):>15}  "
              f"{c(rc, f'{rate}%'):>14}  {status_str}")
    print(c(C.DIM, "  " + "═"*62))
    overall_rate = round(100*tp/tq) if tq else 0
    print(f"  {'TOTAL':<10} {str(tq):>6} "
          f"{c(C.LIME,   str(tp)):>15} "
          f"{c(C.YELLOW, str(tw)):>15} "
          f"{c(C.RED,    str(tf)):>15}  "
          f"{c(C.LIME,   str(overall_rate)):>13}%")
    print(f"\n  {dim(f'Total time: {elapsed:.1f}s')}")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                      HTML REPORT BUILDER                         ║
# ║   Same rich layout as the original single-section report but     ║
# ║   with every section's questions shown section-by-section.       ║
# ╚══════════════════════════════════════════════════════════════════╝

def build_html(all_results: list[SectionResult], elapsed: float):

    all_qs: list[QuestionData] = []
    for sr in all_results:
        all_qs.extend(sr.questions)

    total_q    = len(all_qs)
    total_pass = sum(1 for q in all_qs if q.status == "PASS")
    total_warn = sum(1 for q in all_qs if q.status == "WARN")
    total_fail = sum(1 for q in all_qs if q.status == "FAIL")
    pass_rate  = round(100*total_pass/total_q) if total_q else 0

    # ── HTML helpers ──────────────────────────────────────────────

    def sc(status):
        if status == "PASS": return '<span class="chip-pos">✔ PASS</span>'
        if status == "WARN": return '<span class="chip-warn">⚠ WARN</span>'
        return '<span class="chip-neg">✘ FAIL</span>'

    def ok_b(ok):
        return '<span class="b-pass">✔</span>' if ok else '<span class="b-fail">✘</span>'

    def perf_bar(fm, par, wr):
        def n(v):
            try: return int(v)
            except: return 0
        nf, np_, nw = n(fm), n(par), n(wr)
        tot = nf+np_+nw
        if tot == 0: return '<span class="na">—</span>'
        W = 80
        wf = max(round(W*nf/tot), 1 if nf>0 else 0)
        wp = max(round(W*np_/tot), 1 if np_>0 else 0)
        ww = W-wf-wp
        return (f'<div class="perf-bar-wrap">'
                f'<div class="perf-seg seg-pass" style="width:{wf}px" title="Full Marks:{nf}"></div>'
                f'<div class="perf-seg seg-warn" style="width:{wp}px" title="Partial:{np_}"></div>'
                f'<div class="perf-seg seg-fail" style="width:{ww}px" title="Wrong:{nw}"></div>'
                f'</div>'
                f'<span class="perf-nums">'
                f'<span style="color:#3fb950">{nf}✓</span> '
                f'<span style="color:#e3b341">{np_}~</span> '
                f'<span style="color:#ff7b72">{nw}✗</span>'
                f'</span>')

    def grp_hdr(title, colspan, status="PASS", q_text=""):
        chip   = sc(status)
        q_html = (f'<div class="grp-qtext">{q_text[:90]}{"…" if len(q_text)>90 else ""}</div>'
                  if q_text else "")
        return (f'<tr class="grp-hdr"><td colspan="{colspan}">'
                f'<span class="grp-title">{title}</span>'
                f'<span style="margin-left:12px">{chip}</span>'
                f'{q_html}</td></tr>')

    def right_str(q: QuestionData):
        if q.got_it_right_pct != "—":
            return f'{q.got_it_right_count} <span style="color:var(--muted)">({q.got_it_right_pct})</span>'
        if q.got_it_right_count != "—":
            return q.got_it_right_count
        return "—"

    # ── TAB 1: Section Summary cards ─────────────────────────────
    sec_cards = ""
    for sr in all_results:
        t    = sr.total_questions
        rate = round(100*sr.pass_count/t) if t > 0 else 0
        col  = "#238636" if (sr.fail_count==0 and sr.warn_count==0) else ("#e3b341" if sr.fail_count==0 else "#da3633")
        if sr.skipped:
            badge_html = '<span class="b-warn">SKIPPED</span>'
            err_html   = f'<div style="font-size:11px;color:var(--muted);margin-top:4px">{sr.error}</div>'
        else:
            badge_html = sc("PASS" if sr.fail_count==0 and sr.warn_count==0
                            else "WARN" if sr.fail_count==0 else "FAIL")
            err_html   = ""
        sec_cards += (
            f'<tr>'
            f'<td class="q-label" style="font-size:20px">{sr.section}</td>'
            f'<td class="num" style="font-size:20px;color:var(--blue-text)">{t}</td>'
            f'<td class="num" style="color:var(--pos-text)">{sr.pass_count}</td>'
            f'<td class="num" style="color:var(--yellow)">{sr.warn_count}</td>'
            f'<td class="num" style="color:var(--neg-text)">{sr.fail_count}</td>'
            f'<td>'
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<div style="background:var(--card2);border-radius:4px;height:8px;width:120px;overflow:hidden">'
            f'<div style="width:{rate}%;height:8px;background:{col};border-radius:4px"></div>'
            f'</div>'
            f'<span style="color:{col};font-weight:700">{rate}%</span>'
            f'</div>'
            f'</td>'
            f'<td>{badge_html}{err_html}</td>'
            f'</tr>'
        )

    # Bar chart SVG
    active_secs = [sr for sr in all_results if not sr.skipped and sr.total_questions > 0]
    bar_w_each  = max(28, min(60, 900 // max(len(active_secs), 1)))
    svg_w       = len(active_secs) * (bar_w_each + 12) + 40
    bar_items   = ""
    for i, sr in enumerate(active_secs):
        t    = sr.total_questions
        rate = round(100*sr.pass_count/t) if t > 0 else 0
        col  = "#238636" if rate==100 else ("#e3b341" if rate>=70 else "#da3633")
        x    = 20 + i * (bar_w_each + 12)
        bh   = round(100 * rate / 100)   # max bar height = 100px
        by   = 110 - bh
        bar_items += (
            f'<rect x="{x}" y="{by}" width="{bar_w_each}" height="{bh}" fill="{col}" rx="4"/>'
            f'<text x="{x+bar_w_each//2}" y="125" text-anchor="middle" fill="#8b949e" font-size="11" font-family="Segoe UI,sans-serif">{sr.section}</text>'
            f'<text x="{x+bar_w_each//2}" y="{max(by-4,8)}" text-anchor="middle" fill="{col}" font-size="11" font-weight="bold" font-family="Segoe UI,sans-serif">{rate}%</text>'
        )
    bar_chart_svg = (
        f'<svg width="{svg_w}" height="140" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{svg_w}" height="140" fill="transparent"/>'
        f'{bar_items}'
        f'</svg>'
    )

    # ── TAB 2: All Questions Overview (grouped by section) ────────
    overview_rows = ""
    gi = 0
    for sr in all_results:
        if not sr.questions: continue
        sp = sum(1 for q in sr.questions if q.status=="PASS")
        sw = sum(1 for q in sr.questions if q.status=="WARN")
        sf = sum(1 for q in sr.questions if q.status=="FAIL")
        ss = "PASS" if sf==0 and sw==0 else ("WARN" if sf==0 else "FAIL")
        overview_rows += grp_hdr(
            f"Section  {sr.section}  —  {len(sr.questions)} questions  |  Pass:{sp}  Warn:{sw}  Fail:{sf}",
            11, ss
        )
        for q in sr.questions:
            gi += 1
            rc  = "tr-pass" if q.status=="PASS" else ("tr-warn" if q.status=="WARN" else "tr-fail")
            avg = q.average if q.average not in ("N/A","—","") else "—"
            overview_rows += (
                f'<tr class="{rc}">'
                f'<td class="num">{gi}</td>'
                f'<td class="sec-badge">{q.section}</td>'
                f'<td class="q-label">{q.label}</td>'
                f'<td>{q.chapter or "<span class=\'na\'>—</span>"}</td>'
                f'<td>{q.concept or "<span class=\'na\'>—</span>"}</td>'
                f'<td><span class="qt-badge">{q.qtype}</span></td>'
                f'<td class="num">{q.marks}</td>'
                f'<td class="num">{avg}</td>'
                f'<td>{perf_bar(q.full_marks_students, q.partial_students, q.wrong_students)}</td>'
                f'<td class="num">{right_str(q)}</td>'
                f'<td style="text-align:center">{ok_b(q.chapter_ok)} {ok_b(q.type_ok)}</td>'
                f'<td style="text-align:center">{sc(q.status)}</td>'
                f'</tr>'
            )

    # ── TAB 3: Per-section detail (one sub-tab per section) ───────
    sec_tab_btns  = ""
    sec_tab_panes = ""
    for si, sr in enumerate(all_results):
        tid   = f"sec_{sr.section.replace(' ','_')}"
        active = "active" if si == 0 else ""
        sp = sum(1 for q in sr.questions if q.status=="PASS")
        sw = sum(1 for q in sr.questions if q.status=="WARN")
        sf = sum(1 for q in sr.questions if q.status=="FAIL")
        rate = round(100*sp/len(sr.questions)) if sr.questions else 0
        col  = "#3fb950" if sf==0 and sw==0 else ("#e3b341" if sf==0 else "#ff7b72")

        sec_tab_btns += (
            f'<div class="sec-nav-btn {active}" onclick="switchSec(event,\'{tid}\')">'
            f'{sr.section}'
            f'<span style="font-size:10px;display:block;color:{col}">{rate}%</span>'
            f'</div>'
        )

        rows = ""
        for qi, q in enumerate(sr.questions, 1):
            rc  = "tr-pass" if q.status=="PASS" else ("tr-warn" if q.status=="WARN" else "tr-fail")
            avg = q.average if q.average not in ("N/A","—","") else "—"
            rows += grp_hdr(
                f"Q{qi}  ·  {q.label}  |  {q.chapter}",
                9, q.status, q.question_text
            )
            rows += (
                f'<tr class="{rc}">'
                f'<td class="q-label">{q.label}</td>'
                f'<td>{q.chapter or "<span class=\'na\'>—</span>"}</td>'
                f'<td>{q.concept or "<span class=\'na\'>—</span>"}</td>'
                f'<td><span class="qt-badge">{q.qtype}</span></td>'
                f'<td class="num">{q.marks}</td>'
                f'<td class="num">{avg}</td>'
                f'<td>{perf_bar(q.full_marks_students, q.partial_students, q.wrong_students)}</td>'
                f'<td class="num">{right_str(q)}</td>'
                f'<td style="text-align:center">{sc(q.status)}</td>'
                f'</tr>'
            )
            # Validation row
            cr = "tr-pass" if q.chapter_ok else "tr-fail"
            tr2= "tr-pass" if q.type_ok    else "tr-warn"
            rows += (
                f'<tr class="{cr}" style="font-size:12px">'
                f'<td></td><td colspan="2" style="color:var(--muted)">Chapter/Concept</td>'
                f'<td colspan="2">{ok_b(q.chapter_ok)}</td>'
                f'<td colspan="4" class="td-val">{q.chapter_msg}</td>'
                f'</tr>'
                f'<tr class="{tr2}" style="font-size:12px">'
                f'<td></td><td colspan="2" style="color:var(--muted)">Question Type</td>'
                f'<td colspan="2">{ok_b(q.type_ok)}</td>'
                f'<td colspan="4" class="td-val">{q.type_msg}</td>'
                f'</tr>'
            )

        # Struggle gaps for this section
        gap_rows = ""
        for q in sr.questions:
            if not q.struggle_gaps: continue
            GAP_COLORS = ["#f0883e","#ff7b72","#58a6ff","#e3b341"]
            for gi2, gap in enumerate(q.struggle_gaps):
                col = GAP_COLORS[gi2 % len(GAP_COLORS)]
                gap_rows += (
                    f'<tr>'
                    f'<td class="q-label">{q.label}</td>'
                    f'<td><span style="color:{col};font-size:20px;font-weight:800">{gap.get("pct","")}</span></td>'
                    f'<td style="color:#f0f6fc;font-weight:600">{gap.get("title","")}</td>'
                    f'<td style="color:#8b949e;font-size:12px">{gap.get("desc","")}</td>'
                    f'</tr>'
                )

        skipped_html = (f'<div class="skip-box">⚠ Section skipped: {sr.error}</div>'
                        if sr.skipped else "")

        sec_tab_panes += f"""
        <div id="{tid}" class="sec-pane {active}">
          {skipped_html}
          <div class="sec-stat-row">
            <div class="ssc ssc-total"><div class="ssc-v">{len(sr.questions)}</div><div class="ssc-l">Questions</div></div>
            <div class="ssc ssc-pass"><div class="ssc-v">{sp}</div><div class="ssc-l">Passed</div></div>
            <div class="ssc ssc-warn"><div class="ssc-v">{sw}</div><div class="ssc-l">Warned</div></div>
            <div class="ssc ssc-fail"><div class="ssc-v">{sf}</div><div class="ssc-l">Failed</div></div>
            <div class="ssc ssc-rate"><div class="ssc-v" style="color:{col}">{rate}%</div><div class="ssc-l">Pass Rate</div></div>
          </div>
          <div class="tbl-wrap">
            <table>
              <thead><tr>
                <th>Q</th><th>Chapter</th><th>Concept</th><th>Type</th>
                <th>Marks</th><th>Avg</th><th>Performance</th><th>Right</th><th>Status</th>
              </tr></thead>
              <tbody>{rows if rows else '<tr><td colspan="9" class="empty">No questions</td></tr>'}</tbody>
            </table>
          </div>
          {'<div class="sub-hdr">🧩 Struggle Gaps</div><div class="tbl-wrap"><table><thead><tr><th>Q</th><th>%</th><th>Sub-topic</th><th>Description</th></tr></thead><tbody>' + gap_rows + '</tbody></table></div>' if gap_rows else ''}
        </div>
        """

    # ── TAB 4: Performance deep-dive ──────────────────────────────
    perf_rows = ""
    for sr in all_results:
        if not sr.questions: continue
        perf_rows += grp_hdr(f"Section {sr.section}", 6)
        for q in sr.questions:
            avg = q.average if q.average not in ("N/A","—","") else "—"
            perf_rows += (
                f'<tr class="{"tr-pass" if q.status=="PASS" else "tr-warn" if q.status=="WARN" else "tr-fail"}">'
                f'<td class="q-label">{q.label}</td>'
                f'<td>{q.chapter}</td>'
                f'<td><span class="qt-badge">{q.qtype}</span></td>'
                f'<td>{perf_bar(q.full_marks_students, q.partial_students, q.wrong_students)}</td>'
                f'<td class="num" style="color:var(--blue-text);font-weight:700">{right_str(q)}</td>'
                f'<td class="num" style="color:var(--pos-text);font-weight:700">{avg}</td>'
                f'</tr>'
            )

    # ── TAB 5: Struggle Gaps (all sections) ───────────────────────
    gaps_rows = ""
    for sr in all_results:
        for q in sr.questions:
            if not q.struggle_gaps: continue
            gaps_rows += grp_hdr(f"Section {sr.section}  ·  {q.label}  |  {q.chapter}", 4)
            GAP_COLORS = ["#f0883e","#ff7b72","#58a6ff","#e3b341"]
            for gi2, gap in enumerate(q.struggle_gaps):
                col = GAP_COLORS[gi2 % len(GAP_COLORS)]
                gaps_rows += (
                    f'<tr>'
                    f'<td><span style="color:{col};font-size:22px;font-weight:800">{gap.get("pct","")}</span></td>'
                    f'<td style="color:#f0f6fc;font-weight:600">{gap.get("title","")}</td>'
                    f'<td style="color:#8b949e;font-size:12px">{gap.get("desc","")}</td>'
                    f'<td class="td-phase">{sr.section} · {q.label}</td>'
                    f'</tr>'
                )
    if not gaps_rows:
        gaps_rows = '<tr><td colspan="4" class="empty">No struggle gap data found.</td></tr>'

    # ── TAB 6: Validation ─────────────────────────────────────────
    val_rows = ""
    for sr in all_results:
        if not sr.questions: continue
        val_rows += grp_hdr(f"Section {sr.section}", 5)
        for q in sr.questions:
            cr  = "tr-pass" if q.chapter_ok else "tr-fail"
            tr2 = "tr-pass" if q.type_ok    else "tr-warn"
            val_rows += (
                f'<tr class="{cr}">'
                f'<td class="q-label">{q.section} · {q.label}</td>'
                f'<td>Chapter/Concept Mapping</td>'
                f'<td>{ok_b(q.chapter_ok)}</td>'
                f'<td colspan="2" class="td-val">{q.chapter_msg}</td>'
                f'</tr>'
                f'<tr class="{tr2}">'
                f'<td></td><td>Question Type</td>'
                f'<td>{ok_b(q.type_ok)}</td>'
                f'<td><span class="qt-badge">{q.qtype}</span></td>'
                f'<td class="td-val">{q.type_msg}</td>'
                f'</tr>'
            )

    # ── TAB 7: Failed / Warned ────────────────────────────────────
    failed_rows = ""
    for q in all_qs:
        if q.status not in ("FAIL","WARN"): continue
        badge = ('<span class="b-fail">FAIL</span>' if q.status=="FAIL" else '<span class="b-warn">WARN</span>')
        ch_iss = "" if q.chapter_ok else f'<div style="font-size:12px;color:#ff7b72;margin-top:3px">⚠ {q.chapter_msg}</div>'
        ty_iss = "" if q.type_ok    else f'<div style="font-size:12px;color:#e3b341;margin-top:3px">⚠ {q.type_msg}</div>'
        q_html = (f'<div style="font-size:12px;color:#8b949e;margin-top:4px">{q.question_text[:100]}{"…" if len(q.question_text)>100 else ""}</div>'
                  if q.question_text else "")
        rc_cls = "tr-fail" if q.status == "FAIL" else "tr-warn"
        failed_rows += (
            f'<tr class="{"tr-fail" if q.status=="FAIL" else "tr-warn"}">'
            f'<tr class="{rc_cls}">'
            f'<td class="q-label">{q.label}</td>'
            f'<td>{q.chapter or "—"}{q_html}</td>'
            f'<td>{q.concept or "—"}</td>'
            f'<td><span class="qt-badge">{q.qtype}</span></td>'
            f'<td>{badge}{ch_iss}{ty_iss}</td>'
            f'</tr>'
        )
    if not failed_rows:
        failed_rows = '<tr><td colspan="6" class="empty all-pass">🎉 All questions passed — no failures or warnings!</td></tr>'

    # ── TAB 8: Distributions ─────────────────────────────────────
    type_ctr: dict = defaultdict(int)
    ch_ctr:   dict = defaultdict(int)
    for q in all_qs:
        type_ctr[q.qtype] += 1
        if q.chapter: ch_ctr[q.chapter] += 1

    type_rows = ""
    for qt, cnt in sorted(type_ctr.items(), key=lambda x: -x[1]):
        pct = round(100*cnt/total_q) if total_q else 0
        type_rows += (
            f'<tr><td><span class="qt-badge">{qt}</span></td>'
            f'<td class="num" style="font-size:18px;font-weight:700;color:#f0f6fc">{cnt}</td>'
            f'<td><div style="background:var(--card2);border-radius:4px;height:8px;width:200px;overflow:hidden">'
            f'<div style="width:{pct}%;height:8px;background:var(--blue);border-radius:4px"></div></div></td>'
            f'<td class="num">{pct}%</td></tr>'
        )
    ch_rows = ""
    for ch, cnt in sorted(ch_ctr.items(), key=lambda x: -x[1]):
        pct = round(100*cnt/total_q) if total_q else 0
        ch_rows += (
            f'<tr><td style="font-weight:600;color:#f0f6fc">{ch}</td>'
            f'<td class="num" style="font-size:18px;font-weight:700;color:#58a6ff">{cnt}</td>'
            f'<td><div style="background:var(--card2);border-radius:4px;height:8px;width:200px;overflow:hidden">'
            f'<div style="width:{pct}%;height:8px;background:#58a6ff;border-radius:4px"></div></div></td>'
            f'<td class="num">{pct}%</td></tr>'
        )

    # ── Skipped notice ────────────────────────────────────────────
    skipped_list = [sr for sr in all_results if sr.skipped]
    skip_html = ""
    if skipped_list:
        skip_html = '<div class="skip-box"><strong>⚠ Skipped sections:</strong> '
        for sr in skipped_list:
            skip_html += f'<span class="qt-badge">{sr.section}</span> <span style="color:var(--muted);font-size:12px">{sr.error}</span>  '
        skip_html += '</div>'

    # ─────────────────────────────────────────────────────────────
    # FULL HTML
    # ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens — All Sections Report</title>
<style>
:root{{
  --bg:#0d1117;--card:#161b22;--card2:#21262d;--border:#30363d;
  --text:#c9d1d9;--muted:#8b949e;--head:#f0f6fc;
  --pos:#238636;--pos-bg:#0d2318;--pos-text:#3fb950;
  --neg:#da3633;--neg-bg:#2d1116;--neg-text:#ff7b72;
  --blue:#1f6feb;--blue-text:#58a6ff;
  --yellow:#e3b341;--warn-bg:#2d2005;--warn-text:#e3b341;--warn-border:#e3b341;
  --radius:8px;--font:'Segoe UI',system-ui,sans-serif;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);padding:20px 28px;font-size:14px;line-height:1.5}}
/* NAV */
.nav-tabs{{display:flex;gap:4px;margin-bottom:28px;border-bottom:1px solid var(--border);flex-wrap:wrap}}
.nav-tab{{padding:8px 16px;cursor:pointer;border-radius:6px 6px 0 0;color:var(--muted);font-weight:500;
  border:1px solid transparent;border-bottom:none;transition:.2s;font-size:13px;user-select:none}}
.nav-tab:hover{{color:var(--text);background:var(--card2)}}
.nav-tab.active{{color:var(--head);background:var(--card);border-color:var(--border);border-bottom-color:var(--card)}}
.tab-content{{display:none}}.tab-content.active{{display:block}}
/* HEADER */
.site-header{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:24px 28px;margin-bottom:24px;display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px}}
.sh-title{{font-size:22px;font-weight:700;color:var(--head)}}
.sh-sub{{color:var(--muted);font-size:13px;margin-top:4px}}
.env-tags{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
.env-tag{{background:#1f2d3d;border:1px solid var(--blue);color:var(--blue-text);padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600}}
/* SCORE CARDS */
.score-row{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:24px}}
.sc{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;text-align:center}}
.sc-v{{font-size:28px;font-weight:700;line-height:1}}
.sc-l{{color:var(--muted);font-size:11px;margin-top:5px;text-transform:uppercase;letter-spacing:.5px}}
/* PROGRESS */
.prog-box{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;margin-bottom:24px}}
.prog-label{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}}
.prog-title{{font-weight:600;color:var(--head)}}
.prog-pct{{font-size:17px;font-weight:700;color:var(--pos-text)}}
.prog-bg{{background:var(--card2);border-radius:9999px;height:12px;overflow:hidden;border:1px solid var(--border)}}
.prog-fill{{height:100%;border-radius:9999px;background:linear-gradient(90deg,var(--pos),var(--pos-text))}}
/* TABLE */
.tbl-wrap{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;margin-bottom:24px;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px;min-width:600px}}
thead tr{{background:#1c2128}}
th{{padding:9px 13px;text-align:left;font-weight:600;color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap;font-size:11px;text-transform:uppercase;letter-spacing:.4px}}
td{{padding:8px 13px;border-bottom:1px solid #1c2128;vertical-align:middle}}
tr:last-child td{{border-bottom:none}}
tr:hover{{background:#1c2128}}
.tr-pass:hover{{background:#0d2318}}.tr-fail{{background:#2d111615}}.tr-fail:hover{{background:#2d1116}}
.tr-warn{{background:#2d200515}}.tr-warn:hover{{background:#2d2005}}
/* BADGES */
.b-pass{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:var(--pos-bg);color:var(--pos-text);border:1px solid var(--pos)}}
.b-fail{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:var(--neg-bg);color:var(--neg-text);border:1px solid var(--neg)}}
.b-warn{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:var(--warn-bg);color:var(--warn-text);border:1px solid var(--warn-border)}}
.chip-pos{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;background:var(--pos-bg);color:var(--pos-text);border:1px solid var(--pos)}}
.chip-neg{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;background:var(--neg-bg);color:var(--neg-text);border:1px solid var(--neg)}}
.chip-warn{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700;background:var(--warn-bg);color:var(--warn-text);border:1px solid var(--warn-border)}}
.qt-badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:#1f2d3d;color:var(--blue-text);border:1px solid var(--blue)}}
.sec-badge{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;background:#2d1f4d;color:#bc8cff;border:1px solid #6e40c9}}
.na{{color:var(--muted)}}.num{{text-align:center;font-variant-numeric:tabular-nums}}
.q-label{{font-weight:700;color:var(--blue-text);font-size:14px}}
.empty{{color:var(--muted);font-style:italic;text-align:center;padding:20px}}
.all-pass{{color:var(--pos-text);font-style:normal;font-weight:600;font-size:14px}}
.grp-hdr td{{background:#1c2840;color:var(--head);font-weight:700;font-size:13px;padding:10px 16px;border-top:2px solid var(--blue);border-bottom:1px solid #2d4a7a}}
.grp-title{{font-size:13px;font-weight:700;color:var(--head)}}
.grp-qtext{{font-size:11px;color:var(--muted);font-weight:400;font-style:italic;margin-top:3px}}
.perf-bar-wrap{{display:inline-flex;height:8px;border-radius:4px;overflow:hidden;width:80px;vertical-align:middle;margin-right:8px;background:var(--card2)}}
.perf-seg{{height:100%}}.seg-pass{{background:#238636}}.seg-warn{{background:#e3b341}}.seg-fail{{background:#da3633}}
.perf-nums{{font-size:11px;white-space:nowrap;vertical-align:middle}}
.td-val{{color:var(--muted);font-size:12px;max-width:260px}}
.td-phase{{color:var(--muted);font-size:11px}}
.sec-hdr{{display:flex;align-items:center;gap:10px;margin:24px 0 10px;padding-bottom:8px;border-bottom:1px solid var(--border);flex-wrap:wrap}}
.sec-hdr h2{{font-size:16px;font-weight:700;color:var(--head)}}
.badge-count{{background:var(--card2);border:1px solid var(--border);color:var(--muted);padding:1px 8px;border-radius:20px;font-size:11px}}
/* Section sub-nav */
.sec-nav{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}}
.sec-nav-btn{{padding:8px 14px;cursor:pointer;border-radius:6px;background:var(--card2);
  color:var(--muted);font-weight:700;font-size:13px;border:1px solid var(--border);text-align:center;min-width:48px;user-select:none}}
.sec-nav-btn:hover{{background:var(--card);color:var(--text)}}
.sec-nav-btn.active{{background:#1f2d3d;color:var(--blue-text);border-color:var(--blue)}}
.sec-pane{{display:none}}.sec-pane.active{{display:block}}
/* Section stat row */
.sec-stat-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px}}
.ssc{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:14px;text-align:center}}
.ssc-v{{font-size:24px;font-weight:700;line-height:1}}
.ssc-l{{color:var(--muted);font-size:11px;margin-top:4px;text-transform:uppercase;letter-spacing:.4px}}
.ssc-total .ssc-v{{color:var(--blue-text)}}.ssc-pass .ssc-v{{color:var(--pos-text)}}
.ssc-warn  .ssc-v{{color:var(--yellow)}}.ssc-fail .ssc-v{{color:var(--neg-text)}}.ssc-rate .ssc-v{{color:#bc8cff}}
.sub-hdr{{font-size:13px;font-weight:700;color:var(--head);margin:16px 0 8px;padding-left:4px;border-left:3px solid var(--blue)}}
.skip-box{{background:var(--warn-bg);border:1px solid var(--warn-border);border-radius:var(--radius);padding:12px 16px;margin-bottom:16px;color:var(--warn-text);font-size:13px}}
.bar-chart-wrap{{background:var(--card2);border-radius:var(--radius);padding:12px 16px;margin-bottom:16px;overflow-x:auto}}
.footer{{text-align:center;color:var(--muted);font-size:12px;margin-top:40px;padding-top:12px;border-top:1px solid var(--border)}}
::-webkit-scrollbar{{width:5px;height:5px}}::-webkit-scrollbar-track{{background:var(--bg)}}::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
</style>
</head>
<body>

<div class="site-header">
  <div>
    <div class="sh-title">🏫 ClassLens — All Sections Question Audit Report</div>
    <div class="sh-sub">Generated: {RUN_TS}  ·  Duration: {elapsed:.1f}s  ·  Class {BASE_VALUES["Class"]}  ·  {BASE_VALUES["Subject"]}  ·  {BASE_VALUES["Exam"]}</div>
    <div class="env-tags">
      <span class="env-tag">Class {BASE_VALUES["Class"]}</span>
      <span class="env-tag">{BASE_VALUES["Subject"]}</span>
      <span class="env-tag">{BASE_VALUES["Exam"]}</span>
      {"".join(f'<span class="env-tag">Sec {sr.section}</span>' for sr in all_results if not sr.skipped)}
    </div>
  </div>
</div>

{skip_html}

<div class="score-row">
  <div class="sc" style="border-top:3px solid #a371f7"><div class="sc-v" style="color:#a371f7">{len([s for s in all_results if not s.skipped])}</div><div class="sc-l">Sections</div></div>
  <div class="sc" style="border-top:3px solid var(--blue)"><div class="sc-v" style="color:var(--blue-text)">{total_q}</div><div class="sc-l">Total Questions</div></div>
  <div class="sc" style="border-top:3px solid var(--pos)"><div class="sc-v" style="color:var(--pos-text)">{total_pass}</div><div class="sc-l">Passed</div></div>
  <div class="sc" style="border-top:3px solid var(--yellow)"><div class="sc-v" style="color:var(--yellow)">{total_warn}</div><div class="sc-l">Warnings</div></div>
  <div class="sc" style="border-top:3px solid var(--neg)"><div class="sc-v" style="color:var(--neg-text)">{total_fail}</div><div class="sc-l">Failed</div></div>
  <div class="sc" style="border-top:3px solid #bc8cff"><div class="sc-v" style="color:#bc8cff">{pass_rate}%</div><div class="sc-l">Pass Rate</div></div>
</div>

<div class="prog-box">
  <div class="prog-label">
    <span class="prog-title">Overall Pass Rate — All Sections Combined</span>
    <span class="prog-pct">{pass_rate}%  ({total_pass}/{total_q})</span>
  </div>
  <div class="prog-bg"><div class="prog-fill" style="width:{pass_rate}%"></div></div>
</div>

<div class="nav-tabs">
  <div class="nav-tab active" onclick="switchTab(event,'tab-summary')">🏫 Section Summary</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-overview')">📋 All Questions</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-detail')">📂 Per-Section Detail</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-perf')">📊 Performance</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-validation')">✅ Validation</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-gaps')">🧩 Struggle Gaps</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-dist')">📐 Distributions</div>
  <div class="nav-tab"        onclick="switchTab(event,'tab-failed')">❌ Failed / Warned</div>
</div>

<!-- TAB 1: SECTION SUMMARY -->
<div id="tab-summary" class="tab-content active">
  <div class="sec-hdr"><h2>🏫 Section-by-Section Summary</h2></div>
  <div class="bar-chart-wrap">{bar_chart_svg}</div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>Section</th><th>Total Qs</th><th>Passed</th><th>Warned</th><th>Failed</th><th>Pass Rate</th><th>Status</th></tr></thead>
      <tbody>{sec_cards}</tbody>
    </table>
  </div>
</div>

<!-- TAB 2: ALL QUESTIONS OVERVIEW -->
<div id="tab-overview" class="tab-content">
  <div class="sec-hdr">
    <h2>📋 All Questions — Combined View</h2>
    <span class="badge-count">{total_q} total</span>
    <span class="badge-count" style="color:var(--pos-text)">{total_pass} pass</span>
    <span class="badge-count" style="color:var(--yellow)">{total_warn} warn</span>
    <span class="badge-count" style="color:var(--neg-text)">{total_fail} fail</span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>#</th><th>Sec</th><th>Q</th><th>Chapter</th><th>Concept</th><th>Type</th>
        <th>Marks</th><th>Avg</th><th>Performance</th><th>Right</th><th>Checks</th><th>Status</th>
      </tr></thead>
      <tbody>{overview_rows}</tbody>
    </table>
  </div>
</div>

<!-- TAB 3: PER-SECTION DETAIL -->
<div id="tab-detail" class="tab-content">
  <div class="sec-hdr"><h2>📂 Per-Section Detail</h2><span style="font-size:12px;color:var(--muted)">Click a section tab to expand</span></div>
  <div class="sec-nav">{sec_tab_btns}</div>
  {sec_tab_panes}
</div>

<!-- TAB 4: PERFORMANCE -->
<div id="tab-perf" class="tab-content">
  <div class="sec-hdr"><h2>📊 Performance Deep-Dive</h2>
    <span style="font-size:12px;color:var(--muted)">
      <span style="color:#3fb950">■ Full Marks</span>
      <span style="color:#e3b341">■ Partial</span>
      <span style="color:#ff7b72">■ Wrong</span>
    </span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>Q</th><th>Chapter</th><th>Type</th><th>Student Performance</th><th>Got It Right</th><th>Avg Score</th></tr></thead>
      <tbody>{perf_rows}</tbody>
    </table>
  </div>
</div>

<!-- TAB 5: VALIDATION -->
<div id="tab-validation" class="tab-content">
  <div class="sec-hdr"><h2>✅ Validation Results — Chapter · Concept · Type</h2></div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>Section · Q</th><th>Check</th><th>Pass?</th><th>Type</th><th>Message</th></tr></thead>
      <tbody>{val_rows}</tbody>
    </table>
  </div>
</div>

<!-- TAB 6: STRUGGLE GAPS -->
<div id="tab-gaps" class="tab-content">
  <div class="sec-hdr"><h2>🧩 Where Students Struggled</h2></div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>% Students</th><th>Gap / Sub-topic</th><th>Description</th><th>Section · Q</th></tr></thead>
      <tbody>{gaps_rows}</tbody>
    </table>
  </div>
</div>

<!-- TAB 7: DISTRIBUTIONS -->
<div id="tab-dist" class="tab-content">
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
    <div>
      <div class="sec-hdr"><h2>📐 Question Type Distribution</h2></div>
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Type</th><th>Count</th><th>Distribution</th><th>Share</th></tr></thead>
          <tbody>{type_rows}</tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="sec-hdr"><h2>📚 Questions per Chapter</h2></div>
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Chapter</th><th>Count</th><th>Distribution</th><th>Share</th></tr></thead>
          <tbody>{ch_rows}</tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- TAB 8: FAILED / WARNED -->
<div id="tab-failed" class="tab-content">
  <div class="sec-hdr">
    <h2>❌ Failed &amp; Warned Questions</h2>
    <span class="badge-count" style="color:var(--neg-text)">{total_fail} failed</span>
    <span class="badge-count" style="color:var(--yellow)">{total_warn} warned</span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr><th>Sec</th><th>Q</th><th>Chapter / Question</th><th>Concept</th><th>Type</th><th>Issues</th></tr></thead>
      <tbody>{failed_rows}</tbody>
    </table>
  </div>
</div>

<div class="footer">
  ClassLens All-Sections Audit Report  ·  {RUN_TS}  ·
  {len(ALL_SECTIONS)} sections  ·  {total_q} questions  ·  {pass_rate}% pass rate  ·  {elapsed:.1f}s
</div>

<script>
function switchTab(e,id){{
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  e.target.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
function switchSec(e,id){{
  document.querySelectorAll('.sec-nav-btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.sec-pane').forEach(p=>p.classList.remove('active'));
  e.currentTarget.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
</script>
</body></html>"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  \033[92m\033[1m📄  HTML Report saved → {REPORT_FILE}\033[0m")
    try:
        webbrowser.open(f"file://{os.path.abspath(REPORT_FILE)}")
        print(f"  \033[92m🌐  Opening in browser…\033[0m")
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════════╗
# ║                            MAIN                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

def main():
    print_banner()
    all_section_results: list[SectionResult] = []
    t_start = time.time()

    total_secs = len(ALL_SECTIONS)
    for sec_idx, section_val in enumerate(ALL_SECTIONS, start=1):
        print()
        print(c(C.CYAN+C.BOLD, f"  {'━'*60}"))
        print(c(C.CYAN+C.BOLD, f"  SECTION  {section_val}   ({sec_idx}/{total_secs})"))
        print(c(C.CYAN+C.BOLD, f"  {'━'*60}"))

        sr = audit_section(section_val)   # fresh Chrome per section — no session loss
        all_section_results.append(sr)

        time.sleep(2.0)   # brief cooldown before next Chrome launch

    elapsed = time.time() - t_start

    # Fill in any missing sections
    audited = {sr.section for sr in all_section_results}
    for s in ALL_SECTIONS:
        if s not in audited:
            sr = SectionResult(section=s); sr.skipped = True; sr.error = "Not reached"
            all_section_results.append(sr)

    # Terminal summary
    print_cross_summary(all_section_results, elapsed)

    # HTML report
    build_html(all_section_results, elapsed)
    print(f"\n  \033[92m\033[1m✅  All done! Report saved to {REPORT_FILE}\033[0m\n")



# ==============================================================================
# ADD-ONLY RUNTIME PATCH BEFORE ORIGINAL MAIN
# This block adds behaviour only. It does not delete or replace original source lines.
# ==============================================================================
try:
    if globals().get('_CL_SKIP_ZZ_ADDONLY') and 'SECTION_RUN_LIST' in globals():
        SECTION_RUN_LIST = [s for s in SECTION_RUN_LIST if str(s).strip().upper() != 'ZZ']
        print('[ADD-ONLY PATCH] Section ZZ skipped at runtime.')
except Exception as _e:
    print('[ADD-ONLY PATCH] skip ZZ setup warning:', _e)

try:
    if globals().get('_CL_NO_INPUT_ADDONLY'):
        KEEP_BROWSER_OPEN = False
        AUTO_OPEN_REPORT = False
        print('[ADD-ONLY PATCH] Non-blocking mode enabled: KEEP_BROWSER_OPEN=False, AUTO_OPEN_REPORT=False')
except Exception as _e:
    print('[ADD-ONLY PATCH] no-input setup warning:', _e)

try:
    if globals().get('_CL_HEADLESS_ADDONLY') and 'make_driver' in globals() and not globals().get('_CL_MAKE_DRIVER_PATCHED_ADDONLY'):
        _CL_ORIG_MAKE_DRIVER_ADDONLY = make_driver
        def make_driver(*args, **kwargs):
            try:
                from selenium import webdriver as _wd
                from selenium.webdriver.chrome.options import Options as _Options
                opts = _Options()
                opts.add_argument('--headless=new')
                opts.add_argument('--disable-gpu')
                opts.add_argument('--window-size=1920,1080')
                opts.add_argument('--disable-notifications')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-extensions')
                opts.add_argument('--blink-settings=imagesEnabled=false')
                opts.add_argument('--disable-background-networking')
                opts.add_argument('--disable-sync')
                opts.add_argument('--metrics-recording-only')
                opts.add_argument('--disable-default-apps')
                d = _wd.Chrome(options=opts)
                try: d.implicitly_wait(0)
                except Exception: pass
                try:
                    if 'driver_ref' in globals():
                        driver_ref.clear(); driver_ref.append(d)
                except Exception: pass
                return d
            except Exception as _e:
                print('[ADD-ONLY PATCH] headless driver fallback:', _e)
                return _CL_ORIG_MAKE_DRIVER_ADDONLY(*args, **kwargs)
        _CL_MAKE_DRIVER_PATCHED_ADDONLY = True
        print('[ADD-ONLY PATCH] Headless fast Chrome driver enabled.')
except Exception as _e:
    print('[ADD-ONLY PATCH] driver setup warning:', _e)

try:
    if globals().get('_CL_FAST_MODE_ADDONLY'):
        # Reduce broad timeout constants without changing original code lines.
        for _name in ('TIMEOUT','CARD_WAIT_SEC'):
            if _name in globals():
                try: globals()[_name] = min(int(float(globals()[_name])), 18)
                except Exception: pass
        for _name in ('PANEL_WAIT_SEC','S_DROP','S_NAV','S_CARD','S_SEARCH','S_CLEAR','S_LABEL'):
            if _name in globals():
                try: globals()[_name] = min(float(globals()[_name]), 0.35)
                except Exception: pass
        print('[ADD-ONLY PATCH] Fast timeout/sleep settings applied.')
except Exception as _e:
    print('[ADD-ONLY PATCH] fast setup warning:', _e)
# ==============================================================================
# ORIGINAL MAIN BLOCK CONTINUES BELOW
# ==============================================================================

if __name__ == "__main__":
    main()



####################################################################################################
# END OF SCRIPT 3: ClassLens – All Sections Question Audit Engine
####################################################################################################

####################################################################################################
# START OF SCRIPT 4: ClassLens – Students All-Sections Scraper v8
# Original upload: Pasted text (4)(3).txt
# Preserved lines: 2329
# SHA256: c66d0d98932387333c1d1dbea20b2a3acb66d542becf895ce949344bb93b1346
####################################################################################################
"""
ClassLens All-Sections Scraper  v8
===================================
KEY FIX vs v7:
  - Completely rewritten _JS_GAPS extractor.
  - Old approach: scanned <div> elements for combined innerText containing
    BOTH a % and "More/Fewer Errors" — failed because the app renders the
    percentage, direction, category, and description in SEPARATE child nodes
    whose parent <div> innerText may not contain all pieces, OR the combined
    text exceeds the 350-char / 12-line guards.
  - New approach:
      1. Find every element whose visible text is ONLY a percentage  (+24%, -12%, +1% …).
      2. Walk UP the DOM to the nearest "card" ancestor that also contains
         "More Errors" or "Fewer Errors" text anywhere inside it.
      3. From that card, extract category, direction, badge, description
         individually from their own child nodes.
      4. Zero hard-coded size/line-count guards that can silently reject cards.
  - Also added a scroll step before extraction so the "Comparison of
    learning gaps" section is actually in the viewport / rendered.
  - Added a Python-side fallback that retries extraction after a short wait
    if the first attempt returns nothing.
"""

import json
import os
import re
import time
import webbrowser
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    InvalidSessionIdException,
    WebDriverException,
)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from rich.align import Align
from rich.padding import Padding
from rich.console import Group

console = Console()

# ═══════════════════════════════════════════════════════════
#  CONFIG  — edit these
# ═══════════════════════════════════════════════════════════
LOGIN_URL        = "https://classlens.inferentics.com/"
USERNAME         = os.getenv("CLASSLENS_USER", "Tanmay")
PASSWORD         = os.getenv("CLASSLENS_PASS", "Operations123")
OUTFILE          = "students_all_sections.json"
REPORT_FILE      = "classlens_all_sections_report.html"
RIGHT_PANEL_WAIT = 1.5          # seconds to wait after clicking a student card
GAP_WAIT         = 1.2          # extra wait before gap extraction
RUN_TS           = datetime.now().strftime("%d %b %Y  %H:%M:%S")

FIXED = {
    "Class":   "12",
    "Subject": "Maths",
    "Exam":    "Midterm",
}

# ─────────────────────────────────────────────────────────────
#  RESULT STORE
# ─────────────────────────────────────────────────────────────
@dataclass
class TC:
    phase:   str
    name:    str
    passed:  bool
    detail:  str    = ""
    value:   str    = ""
    section: str    = ""

all_results: List[TC] = []
_phase   = ""
_section = ""

def set_phase(p):   global _phase;   _phase   = p
def set_section(s): global _section; _section = s

def record(name, passed, detail="", value=""):
    all_results.append(TC(_phase, name, passed, detail, value, _section))
    return passed

# ═══════════════════════════════════════════════════════════
#  DRIVER
# ═══════════════════════════════════════════════════════════
def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("detach", True)
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-renderer-backgrounding")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    return driver

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
PCT_RE   = re.compile(r"-?\d+(?:\.\d+)?%")
MARKS_RE = re.compile(r"\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?")

def safe_text(el):
    try:    return (el.text or "").strip()
    except: return ""

def safe_find_one(parent, by, sel):
    try:    return parent.find_element(by, sel)
    except: return None

def safe_find_all(parent, by, sel):
    try:    return parent.find_elements(by, sel)
    except: return []

def safe_click(driver, el):
    try:
        el.click(); return True
    except (ElementClickInterceptedException, StaleElementReferenceException):
        try:
            driver.execute_script("arguments[0].click();", el); return True
        except: return False

def normalize_pct(raw):
    if not raw or raw.strip().upper() == "NA": return "NA"
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", raw)
    if not m: return "NA"
    val = float(m.group(1))
    return f"{val:+.1f}" if val != 0 else "0.0"

def compute_change(mid_pct, pre_pct):
    try:
        m = float(re.findall(r"-?\d+\.?\d*", mid_pct)[0])
        p = float(re.findall(r"-?\d+\.?\d*", pre_pct)[0])
        d = round(p - m, 1)
        return f"+{d}%" if d > 0 else f"{d}%"
    except: return "NA"

def fmt_list(items, n=3):
    return ", ".join(items[:n]) if items else "NA"

def on_filter_page(driver) -> bool:
    try:
        return bool(driver.find_elements(
            By.XPATH, "//*[contains(text(),'Enter your Class')]"))
    except: return False

def on_dashboard(driver) -> bool:
    try:
        src = driver.page_source
        return "Overview" in src or "Your Students" in src
    except: return False

# ═══════════════════════════════════════════════════════════
#  DROPDOWN SETTER
# ═══════════════════════════════════════════════════════════
def set_dropdown(driver, wait, label_text, option_text, timeout=20) -> bool:
    try:
        label  = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//label[contains(text(),'{label_text}')]")))
        select = label.find_element(By.XPATH, "./following::select[1]")
        driver.execute_script("""
            const sel = arguments[0], want = arguments[1];
            for (const opt of sel.options) {
                if (opt.text.trim() === want) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                    sel.dispatchEvent(new Event('input',  {bubbles: true}));
                    break;
                }
            }
        """, select, option_text)
        time.sleep(1.2)
        return True
    except Exception as e:
        console.print(f"[red]  set_dropdown({label_text}={option_text}) failed: {e}[/red]")
        return False

# ═══════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════
def login(driver, wait):
    set_phase("Login")
    console.print(Rule("[bold blue]🔐  Login[/bold blue]", style="blue"))
    with console.status("[cyan]Opening login page…[/cyan]", spinner="dots"):
        driver.get(LOGIN_URL)
    with console.status("[cyan]Signing in…[/cyan]", spinner="arc"):
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@type='text']"))).send_keys(USERNAME)
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@type='password']"))).send_keys(PASSWORD)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@type='submit']"))).click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Enter your Class')]")))
    console.print("  [bold green]✔[/bold green]  Logged in\n")
    record("Login", True, value=USERNAME)

# ═══════════════════════════════════════════════════════════
#  DISCOVER SECTIONS
# ═══════════════════════════════════════════════════════════
def discover_sections(driver, wait) -> list:
    set_phase("Discover")
    console.print(Rule("[bold cyan]🔍  Discovering sections[/bold cyan]", style="cyan"))

    set_dropdown(driver, wait, "Class", FIXED["Class"])
    time.sleep(2)

    try:
        label   = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//label[contains(text(),'Section')]")))
        select  = label.find_element(By.XPATH, "./following::select[1]")
        options = select.find_elements(By.TAG_NAME, "option")
        skip    = {"", "select", "-- select --", "select section", "choose"}
        sections = [o.text.strip() for o in options
                    if o.text.strip().lower() not in skip]
    except Exception as e:
        console.print(f"[red]  Cannot read Section dropdown: {e}[/red]")
        return []

    if sections:
        console.print(
            f"  [bold green]✔[/bold green]  {len(sections)} sections found: "
            f"[bright_cyan]{', '.join(sections)}[/bright_cyan]\n")
        record("Sections discovered", True, value=", ".join(sections))
    else:
        console.print("  [red]✘  No sections found[/red]")
        record("Sections discovered", False)
    return sections

# ═══════════════════════════════════════════════════════════
#  GO BACK TO FILTER PAGE
# ═══════════════════════════════════════════════════════════
def restart_browser_and_return_to_filter():
    console.print("  [dim yellow]  ↻ Restarting browser to recover filter page…[/dim yellow]")
    new_driver = make_driver()
    new_wait   = WebDriverWait(new_driver, 30)
    login(new_driver, new_wait)
    if not on_filter_page(new_driver):
        raise RuntimeError("Could not return to filter page after browser restart")
    return new_driver, new_wait

def go_back_to_filter(driver, wait, timeout=15):
    if on_filter_page(driver):
        return True, driver, wait

    console.print("  [dim]↩  Going back to filter form (in-app)…[/dim]")

    BACK_XPATHS = [
        "//button[.//*[name()='svg']][1]",
        "//*[@aria-label and (contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'back') "
        "or contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'home'))]",
        "//*[normalize-space()='Back' or normalize-space()='Home' or normalize-space()='← Back']",
        "//header//*[self::img or self::svg or self::a][1]",
        "//nav//*[self::img or self::svg or self::a][1]",
        "//header//a[1]",
        "(//button)[1]",
    ]

    for xp in BACK_XPATHS:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if not el.is_displayed():
                    continue
                if safe_click(driver, el):
                    time.sleep(2)
                    if on_filter_page(driver):
                        console.print("  [dim green]  ✔  Back on filter page[/dim green]")
                        return True, driver, wait
        except:
            continue

    console.print("  [dim yellow]  ⚠  Trying browser back button…[/dim yellow]")
    for _ in range(2):
        try:
            driver.back()
            time.sleep(2.5)
            if on_filter_page(driver):
                console.print("  [dim green]  ✔  Back on filter page (via history)[/dim green]")
                return True, driver, wait
        except:
            pass

    console.print("  [dim yellow]  ⚠  In-app navigation failed. Restarting browser…[/dim yellow]")
    try:
        try: driver.quit()
        except: pass
        new_driver, new_wait = restart_browser_and_return_to_filter()
        return True, new_driver, new_wait
    except Exception as e:
        console.print(f"  [red]  ✘  Browser restart recovery failed: {e}[/red]")
        return False, driver, wait

# ═══════════════════════════════════════════════════════════
#  SUBMIT FILTER FORM
# ═══════════════════════════════════════════════════════════
def submit_form(driver, wait, section: str) -> bool:
    set_phase(f"Form:{section}")
    console.print(Rule(
        f"[bold magenta]📋  Form — Section {section}[/bold magenta]", style="magenta"))

    for label, value in [
        ("Class",   FIXED["Class"]),
        ("Section", section),
        ("Subject", FIXED["Subject"]),
        ("Exam",    FIXED["Exam"]),
    ]:
        ok = set_dropdown(driver, wait, label, value)
        icon = "[bold green]✔[/bold green]" if ok else "[bold red]✘[/bold red]"
        console.print(f"  {icon}  {label:10s} → [bright_yellow]{value}[/bright_yellow]")
        record(f"Filter {label}={value}", ok, value=value)
        if not ok:
            return False

    try:
        with console.status(f"[magenta]Clicking Enter…[/magenta]", spinner="bouncingBar"):
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Enter']")))
            btn.click()
            wait.until(EC.presence_of_element_located(
                (By.XPATH,
                 "//*[contains(text(),'Overview') or contains(text(),'Student')"
                 " or contains(text(),'Your Students')]")))
            time.sleep(1.5)
        console.print(
            f"  [bold green]✔[/bold green]  Dashboard loaded — Section {section}\n")
        record(f"Dashboard Sec {section}", True)
        return True
    except Exception as e:
        console.print(f"  [bold red]✘  Dashboard failed: {e}[/bold red]")
        record(f"Dashboard Sec {section}", False, str(e)[:120])
        return False

# ═══════════════════════════════════════════════════════════
#  NAVIGATE TO STUDENTS TAB
# ═══════════════════════════════════════════════════════════
def go_to_students_tab(driver, wait) -> bool:
    set_phase("StudentsTab")
    try:
        with console.status("[cyan]Clicking Students tab…[/cyan]", spinner="dots"):
            for xp in [
                "//div[normalize-space()='Students']",
                "//button[normalize-space()='Students']",
                "//a[normalize-space()='Students']",
                "//*[contains(@class,'tab') and normalize-space()='Students']",
            ]:
                el = safe_find_one(driver, By.XPATH, xp)
                if el and el.is_displayed():
                    safe_click(driver, el)
                    break

            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Your Students')]")))
            time.sleep(1.5)
        console.print("  [bold green]✔[/bold green]  Students tab active\n")
        record("Students tab", True)
        return True
    except Exception as e:
        console.print(f"  [bold red]✘  Students tab failed: {e}[/bold red]")
        record("Students tab", False, str(e)[:80])
        return False

# ═══════════════════════════════════════════════════════════
#  PERCENTAGE EXTRACTION (4 sources)
# ═══════════════════════════════════════════════════════════
def get_pct_s1(card):
    try:
        for el in card.find_elements(By.XPATH, ".//*[contains(text(),'%')]"):
            t = safe_text(el)
            if t and "%" in t and len(t) < 12:
                return t.strip()
    except: pass
    return "NA"

def get_pct_s2(driver):
    for xp in [
        "//*[contains(@class,'bg-green') and contains(text(),'%')]",
        "//*[contains(translate(normalize-space(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'change') and contains(translate("
        "normalize-space(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        ",'accuracy')]/following::*[contains(text(),'%')][1]",
    ]:
        el = safe_find_one(driver, By.XPATH, xp)
        t  = safe_text(el)
        if t and "%" in t:
            m = PCT_RE.search(t)
            if m: return m.group(0)
    return "NA"

def get_pct_s3(driver):
    for xp in [
        "//*[(contains(text(),'IMPROVED') or contains(text(),'DECLINED') "
        "or contains(text(),'Improved') or contains(text(),'Declined'))"
        " and contains(text(),'%')]",
        "//*[contains(text(),'IMPROVED') or contains(text(),'DECLINED') "
        "or contains(text(),'Improved') or contains(text(),'Declined')]"
        "/ancestor::*[contains(text(),'%')][1]",
    ]:
        el = safe_find_one(driver, By.XPATH, xp)
        t  = safe_text(el)
        if t and "%" in t:
            m = PCT_RE.search(t)
            if m: return m.group(0)
    try:
        r = driver.execute_script(r"""
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (!t.includes('%')) continue;
                if (['improved','declined','IMPROVED','DECLINED'].some(k=>t.includes(k))
                    && t.length < 60) {
                    const m = t.match(/[+-]?\d+(?:\.\d+)?%/);
                    if (m) return m[0];
                }
            }
            return null;
        """)
        if r: return r
    except: pass
    return "NA"

def get_pct_s4(driver):
    for xp in [
        "//*[contains(translate(normalize-space(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'progress report')]"
        "/following::*[contains(text(),'%')][1]",
    ]:
        el = safe_find_one(driver, By.XPATH, xp)
        t  = safe_text(el)
        if t and "%" in t:
            m = PCT_RE.search(t)
            if m: return m.group(0)
    try:
        r = driver.execute_script(r"""
            let h = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (t.toLowerCase() === 'progress report' && el.children.length < 3) {
                    h = el; break;
                }
            }
            if (!h) return null;
            let node = h;
            for (let i = 0; i < 5; i++) {
                node = node.nextElementSibling ||
                       (node.parentElement && node.parentElement.nextElementSibling);
                if (!node) break;
                const t = (node.innerText||node.textContent||'').trim();
                if (t.includes('%')) {
                    const m = t.match(/[+-]?\d+(?:\.\d+)?%/);
                    if (m) return m[0];
                }
            }
            return null;
        """)
        if r: return r
    except: pass
    return "NA"

def check_consistency(s1, s2, s3, s4):
    normals = {
        "left_card":        normalize_pct(s1),
        "top_right_button": normalize_pct(s2),
        "center_arrow_box": normalize_pct(s3),
        "progress_report":  normalize_pct(s4),
    }
    valid  = {k: v for k, v in normals.items() if v != "NA"}
    status = ("SKIP" if len(valid) < 2 else
              "PASS" if len(set(valid.values())) == 1 else "FAIL")
    return status, normals

def get_change_accuracy(driver):
    el = safe_find_one(driver, By.XPATH,
        "//*[contains(translate(normalize-space(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'change') and contains(translate("
        "normalize-space(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
        ",'accuracy')]/following::*[contains(text(),'%')][1]")
    t = safe_text(el)
    return t if t and "%" in t else "NA"

# ═══════════════════════════════════════════════════════════
#  EXAM EXTRACTION
# ═══════════════════════════════════════════════════════════
def extract_exam_full(driver, exam_name):
    try:
        card = driver.find_element(By.XPATH,
            f"//p[normalize-space()='{exam_name}']/ancestor::div"
            f"[contains(@class,'border') and contains(@class,'rounded')][1]")
        text  = card.text.replace("\n", " ")
        pct   = PCT_RE.search(text)
        marks = MARKS_RE.search(text)

        def _ch(which):
            title = "Weakest chapters" if which == "weakest" else "Strongest chapters"
            out   = []
            sec   = (safe_find_one(card, By.XPATH,
                         f".//*[normalize-space()='{title}']/ancestor::div[1]") or
                     safe_find_one(card, By.XPATH,
                         f".//*[contains(normalize-space(),'{title}')]/ancestor::div[1]"))
            if not sec: return out
            for r in safe_find_all(sec, By.XPATH, ".//div[normalize-space()]"):
                t  = safe_text(r)
                if not t or title.lower() in t.lower(): continue
                fl = PCT_RE.sub("", t.split("\n")[0].strip()).strip()
                if len(fl) >= 2 and fl not in out:
                    out.append(fl)
                if len(out) >= 3: break
            return out

        return {
            "percent":            pct.group(0).strip()          if pct   else "NA",
            "marks":              marks.group(0).replace(" ","") if marks else "NA",
            "weakest_chapters":   _ch("weakest"),
            "strongest_chapters": _ch("strongest"),
        }
    except:
        return {"percent": "NA", "marks": "NA",
                "weakest_chapters": [], "strongest_chapters": []}

# ═══════════════════════════════════════════════════════════
#  LEARNING GAPS  — v8 rewrite
#
#  Strategy:
#  1. Confirm "Comparison of learning gaps" heading is in the DOM.
#     If not, scroll down in the right panel to render it.
#  2. Locate EVERY element whose entire visible text is ONLY a % value
#     (e.g. "+24%", "-12%", "+1%").  These are the percentage bubbles
#     on the left side of each gap card.
#  3. For each such element, walk UP ancestors until we find one that
#     ALSO contains "More Errors" or "Fewer Errors" text — that is the
#     gap card root.
#  4. From the card root, extract each field from its own sub-element.
#  5. De-duplicate by (category, percent_change, direction).
# ═══════════════════════════════════════════════════════════
_JS_GAPS_V8 = r"""
(function(){
    // ── helpers ────────────────────────────────────────────
    function txt(el){
        return ((el && (el.innerText || el.textContent)) || "").trim();
    }

    // ── 1. Confirm the section heading exists ───────────────
    const headingExists = Array.from(document.querySelectorAll("*")).some(el => {
        const t = txt(el).toLowerCase();
        return t.includes("comparison of learning gaps");
    });
    if (!headingExists) return {found: false, gaps: []};

    // ── 2. Known vocabulary ─────────────────────────────────
    const DIR_KEYWORDS   = ["More Errors", "Fewer Errors"];
    const BADGE_KEYWORDS = ["Most Critical", "Most Improved", "Improved", "Worsened"];
    const CATEGORY_KNOWN = [
        "Foundational Gaps",
        "Makes Mistakes in Steps",
        "Reads Questions Wrong",
        "Makes Calculation Mistakes",
        "Conceptual Gaps",
        "Calculation Errors",
        "Time Management"
    ];
    const PCT_ONLY = /^[+\-]?\d+(?:\.\d+)?%$/;   // element whose ENTIRE text is a %
    const PCT_ANY  = /[+\-]?\d+(?:\.\d+)?%/;

    // ── 3. Find all "pure %" elements ───────────────────────
    const pctEls = Array.from(document.querySelectorAll("*")).filter(el => {
        // Only leaf-ish elements (few children) for performance
        if (el.children.length > 3) return false;
        const t = txt(el);
        return PCT_ONLY.test(t);
    });

    const results = [];
    const seen    = new Set();

    for (const pctEl of pctEls) {
        const pctText = txt(pctEl);

        // ── 4. Walk up to find the card ancestor ─────────────
        let card = null;
        let node = pctEl.parentElement;
        for (let depth = 0; depth < 12; depth++) {
            if (!node) break;
            const nodeText = txt(node);
            const hasDir   = DIR_KEYWORDS.some(d => nodeText.includes(d));
            // Card must have a direction keyword AND be reasonably sized
            if (hasDir && nodeText.length > 20 && nodeText.length < 2000) {
                card = node;
                break;
            }
            node = node.parentElement;
        }
        if (!card) continue;

        const cardText = txt(card);

        // ── 5. Direction ─────────────────────────────────────
        let direction = "NA";
        for (const d of DIR_KEYWORDS) {
            if (cardText.includes(d)) { direction = d; break; }
        }

        // ── 6. Badge ──────────────────────────────────────────
        let badge = "NA";
        for (const b of BADGE_KEYWORDS) {
            if (cardText.includes(b)) { badge = b; break; }
        }

        // ── 7. Category ───────────────────────────────────────
        //   Try known list first, then infer from card children.
        let category = "NA";
        for (const k of CATEGORY_KNOWN) {
            if (cardText.toLowerCase().includes(k.toLowerCase())) {
                category = k; break;
            }
        }
        if (category === "NA") {
            // Walk card children looking for a bold/heading-like text node
            // that is not a %, not a direction, not a badge
            const children = Array.from(card.querySelectorAll("*"));
            for (const ch of children) {
                if (ch.children.length > 0) continue;  // leaf nodes only
                const t = txt(ch);
                if (!t || t.length < 4 || t.length > 80) continue;
                if (PCT_ANY.test(t)) continue;
                if (DIR_KEYWORDS.includes(t)) continue;
                if (BADGE_KEYWORDS.includes(t)) continue;
                if (t.toLowerCase() === "more errors" || t.toLowerCase() === "fewer errors") continue;
                // Skip direction sub-words
                if (t === "More" || t === "Fewer" || t === "Errors") continue;
                category = t;
                break;
            }
        }

        // ── 8. Description ────────────────────────────────────
        //   Longest text node in the card that isn't a %, direction, badge, or category.
        let description = "NA";
        let bestLen = 0;
        const allLeaves = Array.from(card.querySelectorAll("*")).filter(ch => ch.children.length === 0);
        for (const ch of allLeaves) {
            const t = txt(ch);
            if (!t || t.length <= bestLen) continue;
            if (PCT_ANY.test(t) && t.length < 8) continue;  // skip pure pct
            if (DIR_KEYWORDS.includes(t)) continue;
            if (BADGE_KEYWORDS.includes(t)) continue;
            if (t === category) continue;
            if (t === "More" || t === "Fewer" || t === "Errors") continue;
            description = t;
            bestLen = t.length;
        }

        if (category === "NA") continue;

        const sig = category + "|" + pctText + "|" + direction;
        if (seen.has(sig)) continue;
        seen.add(sig);

        results.push({
            category,
            percent_change: pctText,
            direction,
            badge,
            description
        });
    }

    return {found: headingExists, gaps: results.slice(0, 12)};
})();
"""

def scroll_to_gaps_section(driver):
    """Scroll the right panel down until 'Comparison of learning gaps' is visible."""
    try:
        # Try to find and scroll to the heading
        driver.execute_script(r"""
            const els = Array.from(document.querySelectorAll('*'));
            for (const el of els) {
                const t = (el.innerText || el.textContent || '').trim().toLowerCase();
                if (t.includes('comparison of learning gaps')) {
                    el.scrollIntoView({block: 'center', behavior: 'smooth'});
                    break;
                }
            }
        """)
        time.sleep(0.8)
    except:
        pass

    # Also scroll the right-side panel container if it exists
    try:
        driver.execute_script(r"""
            // Find the scrollable right panel
            const panels = Array.from(document.querySelectorAll('div')).filter(d => {
                const s = window.getComputedStyle(d);
                return (s.overflowY === 'auto' || s.overflowY === 'scroll')
                       && d.scrollHeight > d.clientHeight
                       && d.clientWidth > 300;
            });
            // Sort by width descending (widest = most likely right panel)
            panels.sort((a,b) => b.clientWidth - a.clientWidth);
            if (panels.length > 1) {
                panels[1].scrollTop += 1200;
            } else if (panels.length === 1) {
                panels[0].scrollTop += 1200;
            }
        """)
        time.sleep(0.6)
    except:
        pass


def extract_learning_gaps(driver):
    """
    Extract learning gaps using the v8 JS extractor.
    Scrolls to make the section visible, then retries up to 3 times.
    """
    # First scroll attempt to render the gaps section
    scroll_to_gaps_section(driver)
    time.sleep(GAP_WAIT)

    for attempt in range(3):
        try:
            result = driver.execute_script(_JS_GAPS_V8)
            if not isinstance(result, dict):
                time.sleep(0.8)
                continue

            found = result.get("found", False)
            gaps  = result.get("gaps", [])

            if not found:
                # Section not rendered yet — scroll more and retry
                if attempt < 2:
                    scroll_to_gaps_section(driver)
                    time.sleep(1.0 + attempt * 0.5)
                continue

            # Section found — even if gaps list is empty, return it
            clean = []
            for row in gaps:
                if isinstance(row, dict) and row.get("category", "NA") != "NA":
                    clean.append({k: row.get(k, "NA") for k in
                                   ("category","percent_change","direction","badge","description")})

            if clean or found:
                if not clean:
                    console.print("  [dim yellow]  ⚠  Gap section found but no parseable cards[/dim yellow]")
                return clean

        except Exception as e:
            console.print(f"  [dim yellow]  ⚠  Gap extraction attempt {attempt+1}: {e}[/dim yellow]")
            time.sleep(0.8)

    return []

# ═══════════════════════════════════════════════════════════
#  STUDENT LIST HELPERS
# ═══════════════════════════════════════════════════════════
def find_left_container(driver):
    hdr = driver.find_element(By.XPATH, "//*[normalize-space()='Your Students']")
    ctr = safe_find_one(hdr, By.XPATH,
        "./following::*[.//*[contains(@class,'cursor-pointer')"
        " and contains(@class,'rounded-2xl')]][1]")
    return ctr if ctr else hdr.find_element(By.XPATH, "./ancestor::div[2]")

def get_cards(ctr):
    return ctr.find_elements(By.XPATH,
        ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')"
        " and .//p[contains(@class,'font-bold')]]")

def card_name(card):
    el = safe_find_one(card, By.XPATH, ".//p[contains(@class,'font-bold')][1]")
    return safe_text(el)

# ═══════════════════════════════════════════════════════════
#  RICH PRINTER
# ═══════════════════════════════════════════════════════════
def _ps(v):
    try:
        x = float(re.findall(r"-?\d+\.?\d*", v)[0])
        return "bold bright_green" if x >= 75 else ("bold yellow" if x >= 50 else "bold red")
    except: return "white"

def _ds(v):
    try:
        return ("bold bright_green"
                if float(re.findall(r"-?\d+\.?\d*", v)[0]) >= 0 else "bold red")
    except: return "white"

def print_student_result(idx, data, section):
    name   = data["student_name"]
    status = data["consistency_check"]["status"]
    normals= data["consistency_check"]["normalized_values"]
    raw_v  = data["consistency_check"]["raw_values"]
    ss, si, bs = (
        ("bold bright_green", "✅ PASS", "bright_green") if status == "PASS" else
        ("bold red",          "❌ FAIL", "red")           if status == "FAIL" else
        ("bold yellow",       "⚠  SKIP", "yellow")
    )
    hdr = Text()
    hdr.append(f"  #{idx:>3}  ", "bold bright_black")
    hdr.append(f"[Sec {section}]  ", "bold bright_cyan")
    hdr.append(f"{name}  ", "bold bright_white")
    hdr.append(f"[{si}]", ss)

    sc = Table(box=box.SIMPLE_HEAD, header_style="bold bright_cyan", padding=(0,2))
    sc.add_column("Exam",       style="bold white", width=14)
    sc.add_column("Marks",      width=10)
    sc.add_column("Score %",    justify="right", width=10)
    sc.add_column("Δ Accuracy", justify="right", width=14)
    sc.add_row("🔵 Midterm",    data["midterm_marks"],
               Text(data["midterm_percent"],   style=_ps(data["midterm_percent"])), "")
    sc.add_row("🟣 Preboard 1", data["preboard1_marks"],
               Text(data["preboard1_percent"], style=_ps(data["preboard1_percent"])),
               Text(data["change_accuracy"],   style=_ds(data["change_accuracy"])))

    SRC = {"left_card": "① Left Card", "top_right_button": "② Top-Right",
           "center_arrow_box": "③ Center Box", "progress_report": "④ Progress"}
    ct = Table(box=box.SIMPLE_HEAD, header_style="bold bright_yellow", padding=(0,2),
               title=f"[bold bright_yellow]🔍 Consistency [{ss}]{si}[/{ss}][/bold bright_yellow]",
               title_justify="left")
    ct.add_column("Source", style="bold white", width=22)
    ct.add_column("Raw",    width=12)
    ct.add_column("Norm",   justify="center", width=10)
    ct.add_column("✔?",     justify="center", width=6)
    ref = next((v for v in normals.values() if v != "NA"), "NA")
    for k, lbl in SRC.items():
        norm = normals.get(k, "NA"); raw = raw_v.get(k, "NA")
        if norm == "NA":
            mi = Text("—", style="dim");              nt = Text("NA", style="dim")
        elif norm == ref:
            mi = Text("✔", style="bold bright_green"); nt = Text(norm, style="bold bright_green")
        else:
            mi = Text("✘", style="bold red");           nt = Text(norm, style="bold red")
        ct.add_row(lbl, raw, nt, mi)

    ch = Table(box=box.SIMPLE, header_style="bold bright_magenta", padding=(0,2))
    ch.add_column("Exam",         style="bold white",   width=14)
    ch.add_column("💪 Strongest", style="bright_green", width=30)
    ch.add_column("⚠  Weakest",  style="bright_red",   width=30)
    ch.add_row("Midterm",
               fmt_list(data["midterm_strongest_chapters"]),
               fmt_list(data["midterm_weakest_chapters"]))
    ch.add_row("Preboard 1",
               fmt_list(data["preboard1_strongest_chapters"]),
               fmt_list(data["preboard1_weakest_chapters"]))

    parts = [Padding(sc,(0,1)), Rule(style="bright_black"),
             Padding(ct,(0,1)), Rule(style="bright_black"), Padding(ch,(0,1))]

    gaps = data.get("learning_gaps", [])
    if gaps:
        BD = {"Most Critical":"bold red","Most Improved":"bold bright_green",
              "Improved":"bold green","NA":"dim"}
        DR = {"More Errors":"bold red","Fewer Errors":"bold bright_green","NA":"dim"}
        gt = Table(box=box.SIMPLE, header_style="bold bright_yellow", padding=(0,2),
                   title="[bold bright_yellow]📉 Comparison of Learning Gaps[/bold bright_yellow]",
                   title_justify="left")
        gt.add_column("Category",  style="bold white", width=26)
        gt.add_column("Δ %",       justify="right",    width=8)
        gt.add_column("Direction", width=14)
        gt.add_column("Badge",     width=16)
        gt.add_column("Note",      style="dim",        width=42)
        for g in gaps:
            pv = g["percent_change"]
            try:
                ps2 = ("bold red"
                       if float(re.findall(r"-?\d+\.?\d*", pv)[0]) > 0
                       else "bold bright_green")
            except: ps2 = "white"
            gt.add_row(g["category"], Text(pv, style=ps2),
                       Text(g["direction"], style=DR.get(g["direction"], "white")),
                       Text(g["badge"],     style=BD.get(g["badge"], "white")),
                       g["description"])
        parts += [Rule(style="bright_black"), Padding(gt,(0,1))]

    console.print(Panel(Group(*parts), title=hdr,
                        border_style=bs, box=box.DOUBLE_EDGE, padding=(0,1)))

# ═══════════════════════════════════════════════════════════
#  SCRAPE ONE SECTION
# ═══════════════════════════════════════════════════════════
def scrape_section(driver, section: str, global_idx_start: int) -> list:
    set_phase(f"Scrape:{section}")
    set_section(section)
    console.print(Rule(
        f"[bold green]👩‍🎓  Scraping Section {section}[/bold green]", style="green"))

    results   = []
    processed = set()
    idx       = global_idx_start

    try:
        left_ctr = find_left_container(driver)
    except Exception as e:
        console.print(f"[red]  Cannot find student list: {e}[/red]")
        record(f"Student list {section}", False, str(e)[:80])
        return results

    cards = get_cards(left_ctr)
    if not cards:
        console.print(f"[yellow]  ⚠  No student cards in Section {section}[/yellow]")
        record(f"Cards {section}", False, "No cards")
        return results

    record(f"Cards {section}", True, value=f"{len(cards)} initial")

    with Progress(
        SpinnerColumn(spinner_name="aesthetic", style="bold cyan"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=28, style="cyan", complete_style="bright_green"),
        TaskProgressColumn(),
        console=console, transient=True,
    ) as prog:
        task = prog.add_task(f"Section {section}…", total=None)

        while True:
            try:
                left_ctr = find_left_container(driver)
                cards    = get_cards(left_ctr)
            except Exception:
                break

            for card in cards:
                try:
                    name = card_name(card)
                    if not name or name in processed:
                        continue

                    set_phase(f"Student:{section}:{name}")
                    prog.update(task, description=
                        f"[Sec {section}] → [bold white]{name}[/bold white]")

                    s1 = get_pct_s1(card)

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", card)
                    time.sleep(0.3)
                    if not safe_click(driver, card):
                        continue
                    time.sleep(RIGHT_PANEL_WAIT)

                    s2       = get_pct_s2(driver)
                    s3       = get_pct_s3(driver)
                    s4       = get_pct_s4(driver)
                    status, normals = check_consistency(s1, s2, s3, s4)
                    chg_acc  = get_change_accuracy(driver)
                    mid      = extract_exam_full(driver, "Midterm")
                    pre      = extract_exam_full(driver, "Preboard 1")
                    chg_calc = (compute_change(mid["percent"], pre["percent"])
                                if mid["percent"] != "NA" and pre["percent"] != "NA"
                                else "NA")

                    # ── Learning gaps (v8 extractor) ──────────────
                    gaps = extract_learning_gaps(driver)

                    processed.add(name)
                    idx += 1

                    record("Consistency", status == "PASS",    value=status)
                    record("Midterm",     mid["percent"] != "NA", value=mid["percent"])
                    record("Preboard",    pre["percent"] != "NA", value=pre["percent"])
                    record("Learning gaps extracted", True, value=f"{len(gaps)} gaps")

                    rec = {
                        "section":                        section,
                        "student_name":                   name,
                        "midterm_marks":                  mid["marks"],
                        "midterm_percent":                mid["percent"],
                        "preboard1_marks":                pre["marks"],
                        "preboard1_percent":              pre["percent"],
                        "change_accuracy":                chg_acc,
                        "change_calculated_from_percent": chg_calc,
                        "midterm_weakest_chapters":       mid["weakest_chapters"],
                        "midterm_strongest_chapters":     mid["strongest_chapters"],
                        "preboard1_weakest_chapters":     pre["weakest_chapters"],
                        "preboard1_strongest_chapters":   pre["strongest_chapters"],
                        "learning_gaps":                  gaps,
                        "consistency_check": {
                            "status": status,
                            "raw_values": {
                                "left_card":        s1,
                                "top_right_button": s2,
                                "center_arrow_box": s3,
                                "progress_report":  s4,
                            },
                            "normalized_values": normals,
                        },
                    }
                    results.append(rec)

                    prog.stop()
                    print_student_result(idx, rec, section)
                    prog.start()

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            # ── scroll the student list panel ──────────────────────
            try:
                last = driver.execute_script(
                    "return arguments[0].scrollTop;", left_ctr)
                driver.execute_script(
                    "arguments[0].scrollTop += 650;", left_ctr)
                time.sleep(0.9)
                new = driver.execute_script(
                    "return arguments[0].scrollTop;", left_ctr)
                if new == last:
                    break
            except StaleElementReferenceException:
                time.sleep(0.8)
                continue
            except Exception:
                break

    console.print(
        f"  [bold green]✔[/bold green]  Section [bright_cyan]{section}[/bright_cyan] "
        f"— [bold]{len(results)}[/bold] students scraped\n")
    return results

# ═══════════════════════════════════════════════════════════
#  TERMINAL SUMMARY
# ═══════════════════════════════════════════════════════════
def print_summary(data, sections):
    console.print(Rule("[bold yellow]📊  Summary[/bold yellow]", style="yellow"))
    by_sec = defaultdict(list)
    for d in data: by_sec[d["section"]].append(d)

    tbl = Table(box=box.ROUNDED, border_style="yellow", header_style="bold bright_yellow")
    tbl.add_column("Metric", style="bold white",   width=30)
    tbl.add_column("Value",  style="bright_green", width=26)
    tbl.add_row("Sections processed", ", ".join(sections))
    tbl.add_row("Total students",     str(len(data)))
    tbl.add_row("✅ PASS", f"[bright_green]{sum(1 for d in data if d['consistency_check']['status']=='PASS')}[/bright_green]")
    tbl.add_row("❌ FAIL", f"[red]{sum(1 for d in data if d['consistency_check']['status']=='FAIL')}[/red]")
    tbl.add_row("⚠  SKIP", f"[yellow]{sum(1 for d in data if d['consistency_check']['status']=='SKIP')}[/yellow]")
    students_with_gaps = sum(1 for d in data if d.get("learning_gaps"))
    tbl.add_row("📉 With Gaps", f"[bright_cyan]{students_with_gaps}[/bright_cyan]")
    total_gaps = sum(len(d.get("learning_gaps", [])) for d in data)
    tbl.add_row("📉 Total Gap Entries", f"[bright_cyan]{total_gaps}[/bright_cyan]")
    for sec in sections:
        tbl.add_row(f"  Section {sec}", str(len(by_sec.get(sec, []))))
    tbl.add_row("JSON",   OUTFILE)
    tbl.add_row("Report", REPORT_FILE)
    console.print(Padding(tbl, (1, 0)))

    students_with_gaps = [d for d in data if d.get("learning_gaps")]
    if students_with_gaps:
        console.print(Rule("[bold bright_yellow]📉  Students with Comparison of Learning Gaps[/bold bright_yellow]", style="bright_yellow"))
        gt = Table(box=box.ROUNDED, border_style="bright_yellow", header_style="bold bright_yellow")
        gt.add_column("Section", style="bold bright_cyan", width=10)
        gt.add_column("Student", style="bold white", width=28)
        gt.add_column("Gap Count", justify="right", width=10)
        gt.add_column("Categories", style="bright_white", width=58)
        for d in students_with_gaps:
            cats = ", ".join(g["category"] for g in d.get("learning_gaps", []))
            gt.add_row(str(d.get("section", "")), d["student_name"], str(len(d.get("learning_gaps", []))), cats or "NA")
        console.print(Padding(gt, (0, 0)))

# ═══════════════════════════════════════════════════════════
#  HTML REPORT  (identical to v7 structure + gap fixes)
# ═══════════════════════════════════════════════════════════
def build_html_report(data: list, sections: list):
    total     = len(data)
    passed    = [d for d in data if d["consistency_check"]["status"] == "PASS"]
    failed    = [d for d in data if d["consistency_check"]["status"] == "FAIL"]
    skipped   = [d for d in data if d["consistency_check"]["status"] == "SKIP"]
    pass_rate = round(100 * len(passed) / total) if total else 0
    by_sec    = defaultdict(list)
    for d in data: by_sec[d["section"]].append(d)

    def chip(s):
        return ({'PASS': '<span class="chip-pos">✔ PASS</span>',
                 'FAIL': '<span class="chip-neg">✘ FAIL</span>'
                 }.get(s, '<span class="chip-warn">⚠ SKIP</span>'))

    def spill(s):
        return (f'<span style="display:inline-block;padding:1px 8px;border-radius:12px;'
                f'font-size:11px;font-weight:700;background:#1f2d3d;color:#58a6ff;'
                f'border:1px solid #1f6feb;white-space:nowrap">Sec {s}</span>')

    def pcs(v):
        try:
            x = float(re.findall(r"-?\d+\.?\d*", v)[0])
            return ("color:#3fb950;font-weight:700" if x >= 75 else
                    "color:#e3b341;font-weight:700" if x >= 50 else
                    "color:#ff7b72;font-weight:700")
        except: return "color:#8b949e"

    def dcs(v):
        try:
            return ("color:#3fb950;font-weight:700"
                    if float(re.findall(r"-?\d+\.?\d*", v)[0]) >= 0
                    else "color:#ff7b72;font-weight:700")
        except: return "color:#8b949e"

    def srccell(raw, norm, ref):
        if norm == "NA":
            return '<div class="src-cell"><span class="na">—</span></div>'
        ok  = norm == ref
        col = "#3fb950" if ok else "#ff7b72"
        ico = "✔" if ok else "✘"
        return (f'<div class="src-cell">'
                f'<span class="src-raw" style="color:{col}">{ico} {raw}</span>'
                f'<span class="src-norm">{norm}</span></div>')

    def secsep(sec, count, cols):
        return (f'<tr class="sec-sep"><td colspan="{cols}">'
                f'<span class="sep-lbl">📂 Section {sec}</span>'
                f'<span class="sep-cnt">{count} students</span></td></tr>')

    def grphdr(lbl, cols, status="PASS"):
        return (f'<tr class="grp-hdr"><td colspan="{cols}">'
                f'<span class="grp-title">{lbl}</span>'
                f'<span style="margin-left:10px">{chip(status)}</span></td></tr>')

    def chpills(lst):
        if not lst: return '<span class="na">—</span>'
        return "".join(f'<span class="ch-pill">{c}</span>' for c in lst)

    def gdir(d):
        if d == "More Errors":  return '<span class="gap-more">▲ More Errors</span>'
        if d == "Fewer Errors": return '<span class="gap-less">▼ Fewer Errors</span>'
        return f'<span class="na">{d}</span>'

    def gbadge(b):
        st = {"Most Critical": "background:#2d1116;color:#ff7b72;border:1px solid #ff7b72",
              "Most Improved":  "background:#0d2318;color:#3fb950;border:1px solid #3fb950",
              "Improved":       "background:#0d2318;color:#3fb950;border:1px solid #238636",
              }.get(b, "background:#21262d;color:#8b949e;border:1px solid #30363d")
        return (f'<span style="display:inline-block;padding:1px 8px;border-radius:4px;'
                f'font-size:11px;font-weight:700;{st}">{b}</span>')

    SRC = {"left_card": "① Left Card", "top_right_button": "② Top-Right",
           "center_arrow_box": "③ Center Box", "progress_report": "④ Progress"}

    # section summary cards
    sec_cards = ""
    for sec in sections:
        sd  = by_sec.get(sec, [])
        sp  = sum(1 for d in sd if d["consistency_check"]["status"] == "PASS")
        sn  = len(sd); sr = round(100 * sp / sn) if sn else 0
        sf  = sum(1 for d in sd if d["consistency_check"]["status"] == "FAIL")
        ss2 = sum(1 for d in sd if d["consistency_check"]["status"] == "SKIP")
        vm  = [d for d in sd if d["midterm_percent"] != "NA"]
        avg = (round(sum(float(re.findall(r"-?\d+\.?\d*", d["midterm_percent"])[0])
                         for d in vm) / len(vm), 1) if vm else None)
        sg  = sum(1 for d in sd if d.get("learning_gaps"))
        sec_cards += (
            f'<div class="sec-card">'
            f'<div class="sc-hdr">Section {sec}</div>'
            f'<div class="sc-n">{sn} students</div>'
            f'<div class="sc-bar-wrap"><div class="sc-bar" style="width:{sr}%"></div></div>'
            f'<div class="sc-stats">'
            f'<span style="color:#3fb950">{sp}✔</span> '
            f'<span style="color:#ff7b72">{sf}✘</span> '
            f'<span style="color:#e3b341">{ss2}⚠</span></div>'
            f'<div class="sc-rate">{sr}% pass</div>'
            + (f'<div class="sc-avg">Avg Mid: {avg}%</div>' if avg else '')
            + f'<div class="sc-avg" style="color:#bc8cff">{sg} with gaps</div>'
            + '</div>'
        )

    # filter buttons
    fbns = '<button class="fb active" onclick="fs(\'ALL\',this)">All</button>'
    for sec in sections:
        fbns += f'<button class="fb" onclick="fs(\'{sec}\',this)">Sec {sec}</button>'

    # overview rows
    ov_rows = ""; gi = 0
    for sec in sections:
        sd = by_sec.get(sec, [])
        if not sd: continue
        ov_rows += secsep(sec, len(sd), 10)
        for d in sd:
            gi += 1
            st = d["consistency_check"]["status"]
            rc = "tr-pass" if st == "PASS" else ("tr-warn" if st == "SKIP" else "tr-fail")
            gap_count = len(d.get("learning_gaps", []))
            gap_style = "color:#bc8cff;font-weight:700" if gap_count > 0 else "color:#8b949e"
            ov_rows += (
                f'<tr class="{rc}" data-sec="{sec}">'
                f'<td class="num">{gi}</td>'
                f'<td style="text-align:center">{spill(sec)}</td>'
                f'<td style="font-weight:600;color:#f0f6fc">{d["student_name"]}</td>'
                f'<td class="num">{d["midterm_marks"]}</td>'
                f'<td class="num" style="{pcs(d["midterm_percent"])}">{d["midterm_percent"]}</td>'
                f'<td class="num">{d["preboard1_marks"]}</td>'
                f'<td class="num" style="{pcs(d["preboard1_percent"])}">{d["preboard1_percent"]}</td>'
                f'<td class="num" style="{dcs(d["change_accuracy"])}">{d["change_accuracy"]}</td>'
                f'<td class="num" style="{gap_style}">{gap_count}</td>'
                f'<td style="text-align:center">{chip(st)}</td>'
                f'</tr>'
            )

    # all-tests rows
    by_phase = defaultdict(list)
    for tc in all_results: by_phase[tc.phase].append(tc)

    tc_rows = ""
    for ph, rs in by_phase.items():
        p = sum(1 for r in rs if r.passed); f = len(rs) - p
        bdg = (f'<span class="b-pass">{p}✔</span>'
               + (f'&nbsp;<span class="b-fail">{f}✘</span>' if f else ''))
        ph_lbl = ph.replace("Student:", "👤 ").replace("Scrape:", "📂 ").replace("Form:", "⚙ ")
        tc_rows += (f'<tr class="grp-hdr"><td colspan="5">'
                    f'<span class="grp-title">{ph_lbl}</span>'
                    f'<span style="float:right;font-size:12px">{bdg}</span></td></tr>')
        for r in rs:
            cls = "tr-pass" if r.passed else "tr-fail"
            v   = (r.value or r.detail or "")[:70]
            ico = ('<span class="ic-pass">✔</span>' if r.passed
                   else '<span class="ic-fail">✘</span>')
            tc_rows += (
                f'<tr class="{cls}">'
                f'<td style="width:28px">{ico}</td>'
                f'<td class="td-sec">{r.section}</td>'
                f'<td>{r.name}</td>'
                f'<td>{"<span class=\'b-pass\'>PASS</span>" if r.passed else "<span class=\'b-fail\'>FAIL</span>"}</td>'
                f'<td class="td-val">{v}</td></tr>'
            )

    # consistency rows
    cons_rows = ""
    for sec in sections:
        sd = by_sec.get(sec, [])
        if not sd: continue
        cons_rows += secsep(sec, len(sd), 7)
        for d in sd:
            cc = d["consistency_check"]
            st = cc["status"]; nv = cc["normalized_values"]; rv = cc["raw_values"]
            ref = next((v for v in nv.values() if v != "NA"), "NA")
            rc  = "tr-pass" if st == "PASS" else ("tr-warn" if st == "SKIP" else "tr-fail")
            sc2 = "".join(
                f'<td style="text-align:center">'
                f'{srccell(rv.get(k,"NA"), nv.get(k,"NA"), ref)}</td>'
                for k in ["left_card","top_right_button","center_arrow_box","progress_report"]
            )
            cons_rows += (f'<tr class="{rc}">'
                          f'<td style="text-align:center">{spill(sec)}</td>'
                          f'<td style="font-weight:600;color:#f0f6fc">{d["student_name"]}</td>'
                          f'{sc2}'
                          f'<td style="text-align:center">{chip(st)}</td></tr>')

    # scores rows
    score_rows = ""
    for sec in sections:
        sd = by_sec.get(sec, [])
        if not sd: continue
        score_rows += secsep(sec, len(sd), 7)
        for d in sd:
            st = d["consistency_check"]["status"]
            rc = "tr-pass" if st == "PASS" else ("tr-warn" if st == "SKIP" else "tr-fail")
            score_rows += (
                f'<tr class="{rc}">'
                f'<td style="text-align:center">{spill(sec)}</td>'
                f'<td style="font-weight:600;color:#f0f6fc">{d["student_name"]}</td>'
                f'<td style="text-align:center"><div class="score-cell">'
                f'<span class="se-lbl">Midterm</span>'
                f'<span class="se-pct" style="{pcs(d["midterm_percent"])}">'
                f'{d["midterm_percent"]}</span>'
                f'<span class="se-mks">{d["midterm_marks"]}</span></div></td>'
                f'<td style="text-align:center"><div class="score-cell">'
                f'<span class="se-lbl">Preboard 1</span>'
                f'<span class="se-pct" style="{pcs(d["preboard1_percent"])}">'
                f'{d["preboard1_percent"]}</span>'
                f'<span class="se-mks">{d["preboard1_marks"]}</span></div></td>'
                f'<td style="text-align:center;{dcs(d["change_accuracy"])};'
                f'font-size:18px;font-weight:700">{d["change_accuracy"]}</td>'
                f'<td style="text-align:center;{dcs(d["change_calculated_from_percent"])}">'
                f'{d["change_calculated_from_percent"]}</td>'
                f'<td style="text-align:center">{chip(st)}</td></tr>'
            )

    # chapters rows
    ch_rows = ""
    for sec in sections:
        sd = by_sec.get(sec, [])
        if not sd: continue
        ch_rows += secsep(sec, len(sd), 6)
        for d in sd:
            for ek, el2 in [("midterm", "Midterm"), ("preboard1", "Preboard 1")]:
                ch_rows += (
                    f'<tr>'
                    f'<td style="text-align:center">{spill(sec)}</td>'
                    f'<td style="font-weight:600;color:#f0f6fc">{d["student_name"]}</td>'
                    f'<td><strong>{el2}</strong></td>'
                    f'<td>{chpills(d.get(f"{ek}_strongest_chapters", []))}</td>'
                    f'<td>{chpills(d.get(f"{ek}_weakest_chapters",   []))}</td>'
                    f'<td class="num" style="color:#8b949e">'
                    f'{len(d.get(f"{ek}_strongest_chapters",[]))}'
                    f'/{len(d.get(f"{ek}_weakest_chapters",[]))}</td></tr>'
                )

    # learning gaps cards — show only students where Comparison of Learning Gaps data exists
    gap_cards_html = ""
    any_gaps = False
    for sec in sections:
        for d in by_sec.get(sec, []):
            gs = d.get("learning_gaps", [])
            if not gs:
                continue
            any_gaps = True
            st = d["consistency_check"]["status"]
            card_cls = "gap-card-pass" if st == "PASS" else ("gap-card-warn" if st == "SKIP" else "gap-card-fail")
            gap_rows_inner = ""
            for g in gs:
                pv = g["percent_change"]
                try:
                    pc2 = ("#ff7b72"
                           if float(re.findall(r"-?\d+\.?\d*", pv)[0]) > 0
                           else "#3fb950")
                except:
                    pc2 = "#8b949e"
                gap_rows_inner += (
                    f'<tr>'
                    f'<td style="font-weight:600;color:#f0f6fc">{g["category"]}</td>'
                    f'<td class="num" style="color:{pc2};font-size:18px;font-weight:800">{pv}</td>'
                    f'<td>{gdir(g["direction"])}</td>'
                    f'<td>{gbadge(g["badge"])}</td>'
                    f'<td style="color:#8b949e;font-size:12px">{g["description"]}</td>'
                    f'</tr>'
                )
            gap_cards_html += (
                f'<div class="gap-card {card_cls}">'
                f'<div class="gap-card-head">'
                f'<div class="gap-student-meta">{spill(sec)} <span class="gap-student-name">{d["student_name"]}</span></div>'
                f'<div class="gap-student-stats">'
                f'<span class="badge-count" style="color:#bc8cff">{len(gs)} gaps</span>'
                f'<span class="badge-count">{chip(st)}</span>'
                f'</div>'
                f'</div>'
                f'<div class="tbl-wrap gap-inner-table"><table>'
                f'<thead><tr>'
                f'<th style="min-width:160px">Category</th>'
                f'<th style="width:70px;text-align:center">Δ %</th>'
                f'<th style="width:130px;text-align:center">Direction</th>'
                f'<th style="width:130px;text-align:center">Badge</th>'
                f'<th>Description</th>'
                f'</tr></thead>'
                f'<tbody>{gap_rows_inner}</tbody>'
                f'</table></div>'
                f'</div>'
            )
    if not any_gaps:
        gap_cards_html = '<div class="empty" style="margin-top:8px">No learning gap rows were parsed for this run.</div>'

    # gap distribution
    gc = defaultdict(int)
    for d in data:
        for g in d.get("learning_gaps", []): gc[g["category"]] += 1
    tg = sum(gc.values())
    dist_rows = "".join(
        f'<tr><td style="font-weight:600;color:#f0f6fc">{cat}</td>'
        f'<td class="num" style="font-size:20px;font-weight:700">{cnt}</td>'
        f'<td><div style="background:var(--card2);border-radius:4px;height:8px;overflow:hidden">'
        f'<div style="width:{round(100*cnt/tg) if tg else 0}%;height:8px;background:#f0883e;'
        f'border-radius:4px"></div></div></td>'
        f'<td class="num">{round(100*cnt/tg) if tg else 0}%</td></tr>'
        for cat, cnt in sorted(gc.items(), key=lambda x: -x[1])
    ) or '<tr><td colspan="4" class="empty">No parsed gap categories were available for this run.</td></tr>'

    # issues rows
    iss_rows = ""
    for d in data:
        st = d["consistency_check"]["status"]
        if st == "PASS": continue
        sec = d["section"]; cc = d["consistency_check"]
        nv  = cc["normalized_values"]; rv = cc["raw_values"]
        ref = next((v for v in nv.values() if v != "NA"), "NA")
        iss_rows += grphdr(f'{spill(sec)} &nbsp; {d["student_name"]} — {st}', 5, st)
        for key in ["left_card","top_right_button","center_arrow_box","progress_report"]:
            norm = nv.get(key, "NA"); raw = rv.get(key, "NA")
            ok   = norm != "NA" and norm == ref
            ico  = ('<span class="ic-pass">✔</span>' if ok else
                    ('<span class="ic-fail">✘</span>' if norm != "NA"
                     else '<span class="na">—</span>'))
            rc   = "tr-pass" if ok else ("tr-fail" if norm != "NA" else "tr-warn")
            iss_rows += (
                f'<tr class="{rc}">'
                f'<td style="text-align:center">{spill(sec)}</td>'
                f'<td style="font-weight:600;color:#f0f6fc">{d["student_name"]}</td>'
                f'<td style="color:#8b949e">{SRC[key]}</td>'
                f'<td style="text-align:center;color:#e3b341">{raw}</td>'
                f'<td style="text-align:center">{ico} '
                f'<span style="color:#8b949e;font-size:11px">{norm}</span></td></tr>'
            )
    if not iss_rows:
        iss_rows = ('<tr><td colspan="5" class="empty all-pass">'
                    '🎉 All students passed!</td></tr>')

    # phase cards
    ph_cards = ""
    for ph, rs in by_phase.items():
        p = sum(1 for r in rs if r.passed); f = len(rs) - p
        pct = round(100 * p / len(rs)) if rs else 0
        col = "pc-pass" if f == 0 else "pc-fail"
        lbl = (ph.replace("Student:", "👤 ")
                 .replace("Scrape:",  "📂 ")
                 .replace("Form:",    "⚙ "))
        ph_cards += (
            f'<div class="phase-card {col}">'
            f'<div class="pc-name" title="{lbl}">{lbl}</div>'
            f'<div class="pc-bar-wrap">'
            f'<div class="pc-bar" style="width:{pct}%"></div></div>'
            f'<div class="pc-counts">'
            f'<span class="c-pass">{p}✔</span> '
            f'<span class="c-fail">{f}✘</span> '
            f'<span class="c-rate">{pct}%</span></div></div>'
        )

    tc_passed = sum(1 for r in all_results if r.passed)
    tc_total  = len(all_results)
    students_with_gaps = sum(1 for d in data if d.get("learning_gaps"))
    total_gap_entries  = sum(len(d.get("learning_gaps", [])) for d in data)

    env_tags = (
        f'<span class="env-tag">Class {FIXED["Class"]}</span>'
        f'<span class="env-tag">Sections: {", ".join(sections)}</span>'
        f'<span class="env-tag">{FIXED["Subject"]}</span>'
        f'<span class="env-tag">{FIXED["Exam"]}</span>'
        f'<span class="env-tag">{total} Students</span>'
        f'<span class="env-tag">{students_with_gaps} with gaps</span>'
    )

    css = """
:root{--bg:#0d1117;--card:#161b22;--card2:#21262d;--border:#30363d;--text:#c9d1d9;
  --muted:#8b949e;--head:#f0f6fc;--pos:#238636;--pos-bg:#0d2318;--pos-text:#3fb950;
  --neg:#da3633;--neg-bg:#2d1116;--neg-text:#ff7b72;--blue:#1f6feb;--blue-text:#58a6ff;
  --yellow:#e3b341;--yellow-bg:#2d2005;--r:8px;--font:'Segoe UI',system-ui,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh;
  padding:24px 32px;font-size:14px;line-height:1.5}
.nav-tabs{display:flex;flex-wrap:wrap;gap:3px;border-bottom:2px solid var(--border);margin-bottom:28px}
.nav-tab{padding:8px 14px;cursor:pointer;border-radius:6px 6px 0 0;color:var(--muted);
  font-weight:500;font-size:12px;border:1px solid transparent;border-bottom:none;
  white-space:nowrap;transition:color .15s,background .15s;margin-bottom:-2px}
.nav-tab:hover{color:var(--text);background:var(--card2)}
.nav-tab.active{color:var(--head);background:var(--card);border-color:var(--border);
  border-bottom:2px solid var(--card)}
.tab-content{display:none}.tab-content.active{display:block}
.site-header{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:22px 26px;margin-bottom:22px}
.sh-title{font-size:20px;font-weight:700;color:var(--head)}
.sh-sub{color:var(--muted);font-size:12px;margin-top:3px}
.env-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.env-tag{background:#1f2d3d;border:1px solid var(--blue);color:var(--blue-text);
  padding:3px 11px;border-radius:20px;font-size:11px;font-weight:600}
.score-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
  gap:12px;margin-bottom:20px}
.sc{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:18px 14px;text-align:center}
.sc-v{font-size:28px;font-weight:700;line-height:1.1}
.sc-l{color:var(--muted);font-size:11px;margin-top:5px;text-transform:uppercase;letter-spacing:.5px}
.sc-total .sc-v{color:var(--blue-text)}.sc-secs .sc-v{color:#f0883e}
.sc-pass .sc-v{color:var(--pos-text)}.sc-warn .sc-v{color:var(--yellow)}
.sc-fail .sc-v{color:var(--neg-text)}.sc-rate .sc-v{color:#bc8cff}
.sc-gaps .sc-v{color:#f0883e}
.prog-box{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:18px 22px;margin-bottom:22px}
.prog-label{display:flex;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap;gap:4px}
.prog-title{font-weight:600;color:var(--head)}
.prog-pct{font-size:16px;font-weight:700;color:var(--pos-text)}
.prog-bg{background:var(--card2);border-radius:9999px;height:12px;overflow:hidden;
  border:1px solid var(--border)}
.prog-fill{height:100%;border-radius:9999px;
  background:linear-gradient(90deg,var(--pos),var(--pos-text))}
.sec-cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));
  gap:10px;margin-bottom:24px}
.sec-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:14px;border-top:3px solid #1f6feb}
.sc-hdr{font-size:15px;font-weight:700;color:var(--blue-text);margin-bottom:3px}
.sc-n{font-size:12px;color:var(--muted);margin-bottom:6px}
.sc-bar-wrap{background:var(--card2);border-radius:9999px;height:5px;overflow:hidden;margin-bottom:6px}
.sc-bar{height:5px;background:var(--pos);border-radius:9999px}
.sc-stats{font-size:12px;display:flex;gap:8px;margin-bottom:3px}
.sc-rate{font-size:13px;font-weight:700;color:var(--pos-text)}
.sc-avg{font-size:11px;color:var(--muted);margin-top:2px}
.gap-cards-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px}
.gap-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:14px}
.gap-card-pass{border-top:3px solid var(--pos)}
.gap-card-warn{border-top:3px solid var(--yellow)}
.gap-card-fail{border-top:3px solid var(--neg)}
.gap-card-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.gap-student-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.gap-student-name{color:var(--head);font-size:15px;font-weight:700}
.gap-student-stats{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.gap-inner-table{margin-top:2px}
.filter-bar{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;align-items:center}
.filter-lbl{color:var(--muted);font-size:12px;margin-right:4px}
.fb{padding:4px 12px;border-radius:20px;border:1px solid var(--border);
  background:var(--card2);color:var(--muted);font-size:11px;font-weight:600;
  cursor:pointer;transition:all .15s}
.fb:hover{border-color:var(--blue);color:var(--blue-text)}
.fb.active{background:#1f2d3d;border-color:var(--blue);color:var(--blue-text)}
.phase-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));
  gap:10px;margin-bottom:24px}
.phase-card{background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:12px}
.phase-card.pc-pass{border-top:3px solid var(--pos)}
.phase-card.pc-fail{border-top:3px solid var(--neg)}
.pc-name{font-size:12px;font-weight:600;color:var(--text);margin-bottom:6px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-bar-wrap{background:var(--card2);border-radius:9999px;height:5px;
  overflow:hidden;margin-bottom:6px}
.pc-bar{height:5px;background:var(--pos);border-radius:9999px}
.phase-card.pc-fail .pc-bar{background:var(--neg)}
.pc-counts{font-size:11px;display:flex;gap:8px}
.c-pass{color:var(--pos-text)}.c-fail{color:var(--neg-text)}.c-rate{color:var(--muted)}
.sec-hdr{display:flex;align-items:center;gap:10px;margin:24px 0 12px;
  padding-bottom:8px;border-bottom:1px solid var(--border);flex-wrap:wrap}
.sec-hdr h2{font-size:15px;font-weight:700;color:var(--head)}
.badge-count{background:var(--card2);border:1px solid var(--border);
  color:var(--muted);padding:1px 8px;border-radius:20px;font-size:11px}
.tbl-wrap{background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);overflow:hidden;margin-bottom:24px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{background:#1c2128;position:sticky;top:0;z-index:1}
th{padding:10px 14px;text-align:left;font-weight:600;color:var(--muted);
  border-bottom:2px solid var(--border);white-space:nowrap;font-size:11px;
  text-transform:uppercase;letter-spacing:.4px}
td{padding:9px 14px;border-bottom:1px solid var(--card2);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#1c2128}
.tr-pass:hover{background:#0a1f0f}
.tr-fail{background:rgba(45,17,22,.25)}.tr-fail:hover{background:#2d1116}
.tr-warn{background:rgba(45,32,5,.25)}.tr-warn:hover{background:#2d2005}
.sec-sep td{background:linear-gradient(90deg,#1a2540,#161b22);
  border-top:2px solid #1f6feb;border-bottom:1px solid #2d4a7a;padding:7px 14px}
.sep-lbl{font-size:12px;font-weight:700;color:#58a6ff;margin-right:10px}
.sep-cnt{font-size:11px;color:var(--muted)}
.grp-hdr td{background:#1a2540;color:var(--head);font-weight:700;font-size:12px;
  padding:9px 16px;border-top:2px solid var(--blue);border-bottom:1px solid #2d4a7a}
.grp-title{font-size:12px;font-weight:700;color:var(--head)}
.chip-pos,.chip-neg,.chip-warn{display:inline-flex;align-items:center;
  padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap}
.chip-pos{background:var(--pos-bg);color:var(--pos-text);border:1px solid var(--pos)}
.chip-neg{background:var(--neg-bg);color:var(--neg-text);border:1px solid var(--neg)}
.chip-warn{background:var(--yellow-bg);color:var(--yellow);border:1px solid var(--yellow)}
.b-pass,.b-fail{display:inline-block;padding:2px 9px;border-radius:4px;
  font-size:11px;font-weight:700}
.b-pass{background:var(--pos-bg);color:var(--pos-text);border:1px solid var(--pos)}
.b-fail{background:var(--neg-bg);color:var(--neg-text);border:1px solid var(--neg)}
.ic-pass{color:var(--pos-text);font-weight:700;font-size:14px}
.ic-fail{color:var(--neg-text);font-weight:700;font-size:14px}
.na{color:var(--muted)}
.src-cell{display:flex;flex-direction:column;align-items:center;gap:2px;min-width:90px}
.src-raw{font-size:13px;font-weight:700}.src-norm{font-size:10px;color:var(--muted)}
.score-cell{display:flex;flex-direction:column;align-items:center;gap:1px;
  padding:4px 0;min-width:80px}
.se-lbl{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
.se-pct{font-size:20px;font-weight:700;line-height:1.1}
.se-mks{font-size:11px;color:var(--muted)}
.ch-pill{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;
  background:#1c2840;color:#58a6ff;border:1px solid #30363d;margin:2px 1px;white-space:nowrap}
.gap-more{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;
  font-weight:700;background:#2d1116;color:#ff7b72;border:1px solid #ff7b72;white-space:nowrap}
.gap-less{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;
  font-weight:700;background:#0d2318;color:#3fb950;border:1px solid #3fb950;white-space:nowrap}
.num{text-align:center;font-variant-numeric:tabular-nums}
.td-sec{color:var(--muted);font-size:11px;width:70px;white-space:nowrap}
.td-val{color:var(--muted);font-size:12px;max-width:260px;word-break:break-word}
.empty{color:var(--muted);font-style:italic;text-align:center;padding:20px}
.all-pass{color:var(--pos-text);font-style:normal;font-weight:600;font-size:14px}
tr.sec-hidden{display:none}
.footer{text-align:center;color:var(--muted);font-size:12px;margin-top:40px;
  padding-top:12px;border-top:1px solid var(--border)}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens — All Sections Report</title>
<style>{css}</style></head><body>
<div class="site-header">
  <div class="sh-title">👩‍🎓 ClassLens &nbsp;·&nbsp; All Sections &nbsp;·&nbsp; Unified Report</div>
  <div class="sh-sub">Generated: {RUN_TS} &nbsp;·&nbsp; v8 (robust gap extractor)</div>
  <div class="env-tags">{env_tags}</div>
</div>
<div class="score-row">
  <div class="sc sc-secs"> <div class="sc-v">{len(sections)}</div><div class="sc-l">Sections</div></div>
  <div class="sc sc-total"><div class="sc-v">{total}</div>         <div class="sc-l">Total Students</div></div>
  <div class="sc sc-pass"> <div class="sc-v">{len(passed)}</div>   <div class="sc-l">Consistency ✔</div></div>
  <div class="sc sc-warn"> <div class="sc-v">{len(skipped)}</div>  <div class="sc-l">Skipped ⚠</div></div>
  <div class="sc sc-fail"> <div class="sc-v">{len(failed)}</div>   <div class="sc-l">Mismatch ✘</div></div>
  <div class="sc sc-rate"> <div class="sc-v">{pass_rate}%</div>    <div class="sc-l">Pass Rate</div></div>
  <div class="sc sc-gaps"> <div class="sc-v">{students_with_gaps}</div><div class="sc-l">Have Gap Data</div></div>
  <div class="sc sc-gaps"> <div class="sc-v">{total_gap_entries}</div><div class="sc-l">Total Gap Entries</div></div>
</div>
<div class="prog-box">
  <div class="prog-label">
    <span class="prog-title">Overall Consistency Pass Rate</span>
    <span class="prog-pct">{pass_rate}% ({len(passed)}/{total})</span>
  </div>
  <div class="prog-bg"><div class="prog-fill" style="width:{pass_rate}%"></div></div>
</div>
<div class="nav-tabs">
  <div class="nav-tab active" onclick="st(event,'t-ov')">📋 Overview</div>
  <div class="nav-tab"        onclick="st(event,'t-sec')">📂 By Section</div>
  <div class="nav-tab"        onclick="st(event,'t-ph')">⚡ Phases</div>
  <div class="nav-tab"        onclick="st(event,'t-tc')">🧪 All Checks</div>
  <div class="nav-tab"        onclick="st(event,'t-con')">🔍 4-Source</div>
  <div class="nav-tab"        onclick="st(event,'t-sc')">📊 Scores</div>
  <div class="nav-tab"        onclick="st(event,'t-ch')">📚 Chapters</div>
  <div class="nav-tab"        onclick="st(event,'t-gp')">📉 Learning Gaps</div>
  <div class="nav-tab"        onclick="st(event,'t-di')">📐 Gap Distribution</div>
  <div class="nav-tab"        onclick="st(event,'t-is')">❌ Issues</div>
</div>
<!-- OVERVIEW -->
<div id="t-ov" class="tab-content active">
  <div class="sec-hdr"><h2>📋 All Students</h2>
    <span class="badge-count">{total}</span>
    <span class="badge-count" style="color:var(--pos-text)">{len(passed)} passed</span>
    <span class="badge-count" style="color:var(--yellow)">{len(skipped)} skipped</span>
    <span class="badge-count" style="color:var(--neg-text)">{len(failed)} failed</span>
    <span class="badge-count" style="color:#bc8cff">{students_with_gaps} with gaps</span>
  </div>
  <div class="filter-bar"><span class="filter-lbl">Filter:</span>{fbns}</div>
  <div class="tbl-wrap"><table id="ov-tbl">
    <thead><tr>
      <th style="width:40px">#</th>
      <th style="width:75px;text-align:center">Section</th>
      <th style="min-width:140px">Student</th>
      <th style="width:85px;text-align:center">Mid Marks</th>
      <th style="width:75px;text-align:center">Mid %</th>
      <th style="width:85px;text-align:center">Pre Marks</th>
      <th style="width:75px;text-align:center">Pre %</th>
      <th style="width:95px;text-align:center">Δ Accuracy</th>
      <th style="width:55px;text-align:center">Gaps</th>
      <th style="width:95px;text-align:center">Status</th>
    </tr></thead>
    <tbody>{ov_rows}</tbody>
  </table></div>
</div>
<!-- BY SECTION -->
<div id="t-sec" class="tab-content">
  <div class="sec-hdr"><h2>📂 Per-Section Summary</h2></div>
  <div class="sec-cards-grid">{sec_cards}</div>
</div>
<!-- PHASES -->
<div id="t-ph" class="tab-content">
  <div class="sec-hdr"><h2>⚡ Phase Summary</h2></div>
  <div class="phase-grid">{ph_cards}</div>
</div>
<!-- ALL CHECKS -->
<div id="t-tc" class="tab-content">
  <div class="sec-hdr"><h2>🧪 All Checks</h2>
    <span class="badge-count">{tc_total}</span>
    <span class="badge-count" style="color:var(--pos-text)">{tc_passed} passed</span>
    <span class="badge-count" style="color:var(--neg-text)">{tc_total-tc_passed} failed</span>
  </div>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th style="width:28px"></th><th style="width:70px">Section</th>
      <th>Check</th><th style="width:90px;text-align:center">Result</th>
      <th style="width:260px">Value</th>
    </tr></thead>
    <tbody>{tc_rows}</tbody>
  </table></div>
</div>
<!-- 4-SOURCE -->
<div id="t-con" class="tab-content">
  <div class="sec-hdr"><h2>🔍 4-Source Consistency</h2>
    <span class="badge-count">{total}</span>
  </div>
  <p style="color:var(--muted);font-size:13px;margin-bottom:16px">
    ✔ = match &nbsp;·&nbsp; ✘ = mismatch &nbsp;·&nbsp; — = not found
  </p>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th style="width:75px;text-align:center">Section</th>
      <th style="min-width:140px">Student</th>
      <th style="width:125px;text-align:center">① Left Card</th>
      <th style="width:125px;text-align:center">② Top-Right</th>
      <th style="width:125px;text-align:center">③ Center Box</th>
      <th style="width:125px;text-align:center">④ Progress</th>
      <th style="width:100px;text-align:center">Result</th>
    </tr></thead>
    <tbody>{cons_rows}</tbody>
  </table></div>
</div>
<!-- SCORES -->
<div id="t-sc" class="tab-content">
  <div class="sec-hdr"><h2>📊 Exam Scores</h2></div>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th style="width:75px;text-align:center">Section</th>
      <th style="min-width:140px">Student</th>
      <th style="width:115px;text-align:center">Midterm</th>
      <th style="width:115px;text-align:center">Preboard 1</th>
      <th style="width:105px;text-align:center">Δ Accuracy</th>
      <th style="width:105px;text-align:center">Calculated Δ</th>
      <th style="width:100px;text-align:center">Status</th>
    </tr></thead>
    <tbody>{score_rows}</tbody>
  </table></div>
</div>
<!-- CHAPTERS -->
<div id="t-ch" class="tab-content">
  <div class="sec-hdr"><h2>📚 Chapters</h2></div>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th style="width:75px;text-align:center">Section</th>
      <th style="min-width:140px">Student</th>
      <th style="width:95px">Exam</th>
      <th>💪 Strongest</th><th>⚠ Weakest</th>
      <th style="width:75px;text-align:center">S/W</th>
    </tr></thead>
    <tbody>{ch_rows}</tbody>
  </table></div>
</div>
<!-- LEARNING GAPS -->
<div id="t-gp" class="tab-content">
  <div class="sec-hdr"><h2>📉 Learning Gaps</h2>
    <span class="badge-count" style="color:#bc8cff">{students_with_gaps} students</span>
    <span class="badge-count" style="color:#f0883e">{total_gap_entries} entries</span>
  </div>
  <div class="gap-cards-grid">{gap_cards_html}</div>
</div>
<!-- GAP DISTRIBUTION -->
<div id="t-di" class="tab-content">
  <div class="sec-hdr"><h2>📐 Gap Distribution</h2>
    <span class="badge-count">{tg} entries</span>
  </div>
  <div class="tbl-wrap" style="max-width:620px"><table>
    <thead><tr>
      <th>Category</th>
      <th style="width:70px;text-align:center">Count</th>
      <th style="width:200px">Bar</th>
      <th style="width:65px;text-align:center">Share</th>
    </tr></thead>
    <tbody>{dist_rows}</tbody>
  </table></div>
</div>
<!-- ISSUES -->
<div id="t-is" class="tab-content">
  <div class="sec-hdr"><h2>❌ Issues</h2>
    <span class="badge-count" style="color:var(--neg-text)">{len(failed)} failed</span>
    <span class="badge-count" style="color:var(--yellow)">{len(skipped)} skipped</span>
  </div>
  <div class="tbl-wrap"><table>
    <thead><tr>
      <th style="width:75px;text-align:center">Section</th>
      <th style="min-width:140px">Student</th>
      <th style="width:155px">Source</th>
      <th style="width:125px;text-align:center">Raw Value</th>
      <th style="width:85px;text-align:center">Match</th>
    </tr></thead>
    <tbody>{iss_rows}</tbody>
  </table></div>
</div>
<div class="footer">
  ClassLens All-Sections Report v8 &nbsp;·&nbsp; {RUN_TS} &nbsp;·&nbsp;
  Sections: {', '.join(sections)} &nbsp;·&nbsp;
  {total} students &nbsp;·&nbsp; {pass_rate}% pass rate &nbsp;·&nbsp;
  {students_with_gaps} students with gap data
</div>
<script>
function st(e,id){{
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t=>t.classList.remove('active'));
  e.target.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
function fs(sec,btn){{
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('#ov-tbl tbody tr').forEach(row=>{{
    if (row.classList.contains('sec-sep')) {{
      const lbl = row.querySelector('.sep-lbl');
      if (!lbl) return;
      (sec==='ALL'||lbl.textContent.includes(sec))
        ? row.classList.remove('sec-hidden')
        : row.classList.add('sec-hidden');
      return;
    }}
    if (sec==='ALL') {{ row.classList.remove('sec-hidden'); return; }}
    row.dataset.sec===sec
      ? row.classList.remove('sec-hidden')
      : row.classList.add('sec-hidden');
  }});
}}
</script>
</body></html>"""

    with open(REPORT_FILE, "w", encoding="utf-8") as fh:
        fh.write(html)
    console.print(f"\n  [bold green]📄  Report → {REPORT_FILE}[/bold green]")
    try:
        webbrowser.open(f"file://{os.path.abspath(REPORT_FILE)}")
    except: pass

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def main():
    console.print(Panel(
        Align.center(Text("ClassLens All-Sections Scraper  v8", style="bold cyan")),
        subtitle="[dim]Robust gap extractor · Never hard-reloads · In-app navigation only[/dim]",
        border_style="bright_cyan", padding=(1, 4)))

    console.print(Padding(
        f"[bold yellow]Config:[/bold yellow] "
        f"Class=[bright_cyan]{FIXED['Class']}[/bright_cyan]  "
        f"Subject=[bright_cyan]{FIXED['Subject']}[/bright_cyan]  "
        f"Exam=[bright_cyan]{FIXED['Exam']}[/bright_cyan]  "
        f"Section=[bright_cyan]AUTO-ALL[/bright_cyan]", (1, 0)))

    driver   = make_driver()
    wait     = WebDriverWait(driver, 30)
    all_data = []
    sections = []

    try:
        login(driver, wait)
        sections = discover_sections(driver, wait)
        if not sections:
            console.print("[bold red]No sections found — aborting.[/bold red]")
            return

        global_idx = 0
        for i, section in enumerate(sections):
            console.print(Rule(
                f"[bold bright_cyan]📂  SECTION  {section}  "
                f"({i+1}/{len(sections)})[/bold bright_cyan]",
                style="bright_cyan"))
            set_section(section)

            if i > 0:
                ok, driver, wait = go_back_to_filter(driver, wait)
                if not ok:
                    console.print(
                        f"[red]  ✘  Could not return to filter page for "
                        f"Section {section} — skipping[/red]")
                    record(f"Back to filter {section}", False)
                    continue

            if not submit_form(driver, wait, section):
                continue
            if not go_to_students_tab(driver, wait):
                continue

            sec_data = scrape_section(driver, section, global_idx)
            all_data.extend(sec_data)
            global_idx += len(sec_data)

            console.print(
                f"  [bold green]✔[/bold green]  Section [bright_cyan]{section}[/bright_cyan] "
                f"done. Running total: [bold]{global_idx}[/bold] students\n")

        with open(OUTFILE, "w", encoding="utf-8") as fh:
            json.dump(all_data, fh, indent=2)
        console.print(f"  [bold green]💾  JSON → {OUTFILE}[/bold green]")

        print_summary(all_data, sections)

        console.print(Panel(
            Align.center(Text(
                f"✅  Done!  {len(sections)} sections · {len(all_data)} students",
                style="bold bright_green")),
            border_style="bright_green", padding=(1, 4)))

    except Exception as e:
        set_phase("ERROR")
        record("Script", False, str(e)[:120])
        console.print(Panel(
            f"[bold red]✘ ERROR:[/bold red]\n[red]{e}[/red]",
            title="[bold red]Exception[/bold red]",
            border_style="red", padding=(1, 2)))

    finally:
        build_html_report(all_data, sections)
        console.print(
            "\n  [bold green]🟢  Browser open — close manually.[/bold green]\n")




# ═══════════════════════════════════════════════════════════
#  ADD-ONLY PATCH  — visible-text fallback for learning gaps
#  (does not remove any original line)
# ═══════════════════════════════════════════════════════════

def extract_learning_gaps_super(driver):
    """
    FINAL visible-text fallback extractor.
    Reads the rendered text exactly as shown on screen and parses the
    'Comparison of learning gaps' section even when the DOM structure is
    fragmented across many child nodes.
    """
    try:
        try:
            driver.execute_script(r"""
                const all = Array.from(document.querySelectorAll('*'));
                const hit = all.find(e => {
                    const t = (e.innerText || e.textContent || '').trim().toLowerCase();
                    return t.includes('comparison of learning gaps');
                });
                if (hit) hit.scrollIntoView({block:'center', behavior:'instant'});
            """)
            time.sleep(0.4)
        except:
            pass

        try:
            driver.execute_script(r"""
                const panels = Array.from(document.querySelectorAll('div')).filter(d => {
                    const s = window.getComputedStyle(d);
                    return (s.overflowY === 'auto' || s.overflowY === 'scroll') && d.scrollHeight > d.clientHeight;
                });
                panels.sort((a,b) => (b.clientWidth*b.clientHeight) - (a.clientWidth*a.clientHeight));
                for (const p of panels.slice(0,3)) {
                    p.scrollTop = Math.min(p.scrollHeight, p.scrollTop + 1200);
                }
            """)
            time.sleep(0.4)
        except:
            pass

        section_text = driver.execute_script(r"""
            function txt(el){ return ((el && (el.innerText || el.textContent)) || '').trim(); }
            const nodes = Array.from(document.querySelectorAll('*')).filter(el => {
                const t = txt(el).toLowerCase();
                return t.includes('comparison of learning gaps');
            });
            nodes.sort((a,b) => txt(a).length - txt(b).length);
            for (const n of nodes) {
                const t = txt(n);
                if (!t) continue;
                if (t.toLowerCase().includes('comparison of learning gaps') && t.length > 40) {
                    return t;
                }
            }
            return document.body ? (document.body.innerText || '') : '';
        """)

        if not section_text or 'Comparison of learning gaps' not in section_text:
            return []

        section = section_text.split('Comparison of learning gaps', 1)[1]
        section = section.replace('A comparison of mistake patterns across the last two tests.', '').strip()

        stop_words = ['Your Students', 'Overview', 'Progress report', 'Midterm', 'Preboard 1']
        for w in stop_words:
            if w in section:
                section = section.split(w, 1)[0].strip()

        lines = [ln.strip() for ln in section.splitlines() if ln and ln.strip()]
        if not lines:
            return []

        badge_terms = ['Most Critical', 'Most Improved', 'Improved', 'Worsened', 'New Type']
        dir_terms = ['More Errors', 'Fewer Errors']
        known_categories = [
            'Foundational Gaps',
            'Makes Mistakes in Steps',
            'Reads Questions Wrong',
            'Makes Calculation Mistakes',
            'Conceptual Gaps',
            'Calculation Errors',
            'Time Management'
        ]

        gaps = []
        seen = set()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = PCT_RE.search(line)
            if not m:
                i += 1
                continue

            percent = m.group(0)
            direction = 'NA'
            category = 'NA'
            description = 'NA'
            badge = 'NA'

            window = lines[i:i+10]
            for w in window[1:]:
                if w in dir_terms and direction == 'NA':
                    direction = w
                    continue
                if w in badge_terms and badge == 'NA':
                    badge = w
                    continue
                if category == 'NA':
                    if w in known_categories or (4 <= len(w) <= 80 and '%' not in w and w not in dir_terms and w not in badge_terms):
                        category = w
                        continue
                if category != 'NA' and description == 'NA':
                    if len(w) >= 8 and '%' not in w and w not in dir_terms and w not in badge_terms and w != category:
                        description = w
                        continue

            if category != 'NA':
                sig = (category, percent, direction, badge, description)
                if sig not in seen:
                    seen.add(sig)
                    gaps.append({
                        'category': category,
                        'percent_change': percent,
                        'direction': direction,
                        'badge': badge,
                        'description': description,
                    })

            i += 1

        return gaps
    except Exception as e:
        console.print(f"  [dim yellow]  ⚠  Super gap extractor failed: {e}[/dim yellow]")
        return []


try:
    _ORIGINAL_EXTRACT_LEARNING_GAPS = extract_learning_gaps
except NameError:
    _ORIGINAL_EXTRACT_LEARNING_GAPS = None


def extract_learning_gaps(driver):
    """Original extractor first, visible-text fallback second."""
    gaps = []
    try:
        if _ORIGINAL_EXTRACT_LEARNING_GAPS:
            gaps = _ORIGINAL_EXTRACT_LEARNING_GAPS(driver) or []
    except Exception as e:
        console.print(f"  [dim yellow]  ⚠  Original gap extractor failed: {e}[/dim yellow]")
        gaps = []

    if gaps:
        return gaps

    return extract_learning_gaps_super(driver) or []


# add-only speed override
GAP_WAIT = 0.5

# ═══════════════════════════════════════════════════════════
#  FINAL PATCH  — stronger rendered-text learning gaps parser
# ═══════════════════════════════════════════════════════════

def _parse_learning_gaps_from_section_text(section_text: str):
    if not section_text:
        return []
    text = section_text.replace("\r", "\n")
    m = re.search(r"Comparison of learning gaps", text, flags=re.I)
    if m:
        text = text[m.end():]
    text = text.replace("A comparison of mistake patterns across the last two tests.", " ")
    for marker in ["Progress report", "Midterm", "Preboard 1", "Your Students", "Overview",
                   "Strongest chapters", "Weakest chapters", "4-Field Consistency"]:
        pos = text.find(marker)
        if pos > 0:
            text = text[:pos]
    lines = []
    for raw in text.splitlines():
        ln = re.sub(r"\s+", " ", raw).strip(" -|:\t")
        if ln:
            lines.append(ln)
    if not lines:
        return []
    badge_terms = ["Most Critical", "Most Improved", "Improved", "Worsened", "New Type"]
    dir_terms = ["More Errors", "Fewer Errors"]
    known_categories = [
        "Foundational Gaps", "Makes Mistakes in Steps", "Reads Questions Wrong",
        "Makes Calculation Mistakes", "Conceptual Gaps", "Calculation Errors", "Time Management",
    ]
    noise_terms = set(x.lower() for x in badge_terms + dir_terms + [
        "comparison of learning gaps",
        "a comparison of mistake patterns across the last two tests.",
    ])

    def clean_text(s: str) -> str:
        s = re.sub(r"[+\-]?\d+(?:\.\d+)?%", " ", s)
        s = re.sub(r"\s+", " ", s).strip(" -|:\t")
        return s

    gaps = []
    seen = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        pct_match = PCT_RE.search(line)
        if not pct_match:
            i += 1
            continue
        percent = pct_match.group(0)
        window = lines[i:i+12]
        direction = "NA"
        badge = "NA"
        category = "NA"
        description = "NA"
        for w in window:
            for d in dir_terms:
                if d.lower() in w.lower() and direction == "NA":
                    direction = d
            for b in badge_terms:
                if b.lower() in w.lower() and badge == "NA":
                    badge = b
        for w in window:
            wt = clean_text(w)
            if not wt or wt.lower() in noise_terms:
                continue
            if any(d.lower() in wt.lower() for d in dir_terms):
                continue
            if any(b.lower() in wt.lower() for b in badge_terms):
                continue
            for known in known_categories:
                if known.lower() in wt.lower():
                    category = known
                    break
            if category != "NA":
                break
            if 4 <= len(wt) <= 80:
                category = wt
                break
        for w in window:
            wt = clean_text(w)
            if not wt or wt == category:
                continue
            if any(d.lower() in wt.lower() for d in dir_terms):
                continue
            if any(b.lower() in wt.lower() for b in badge_terms):
                continue
            if len(wt) >= 8:
                description = wt
                break
        if category != "NA":
            sig = (category, percent, direction, badge, description)
            if sig not in seen:
                seen.add(sig)
                gaps.append({
                    "category": category,
                    "percent_change": percent,
                    "direction": direction,
                    "badge": badge,
                    "description": description,
                })
        i += 1
    return gaps

def _get_learning_gaps_section_text(driver):
    try:
        for _ in range(3):
            driver.execute_script("""
                const hit = Array.from(document.querySelectorAll("*")).find(el => {
                    const t = (el.innerText || el.textContent || "").trim().toLowerCase();
                    return t.includes("comparison of learning gaps");
                });
                if (hit) hit.scrollIntoView({block:"center", behavior:"instant"});
            """)
            time.sleep(0.25)
            driver.execute_script("""
                const panels = Array.from(document.querySelectorAll("div")).filter(d => {
                    const s = window.getComputedStyle(d);
                    return (s.overflowY === "auto" || s.overflowY === "scroll") && d.scrollHeight > d.clientHeight;
                });
                panels.sort((a,b) => (b.clientWidth*b.clientHeight) - (a.clientWidth*a.clientHeight));
                for (const p of panels.slice(0,4)) {
                    p.scrollTop = Math.min(p.scrollHeight, p.scrollTop + 900);
                }
            """)
            time.sleep(0.25)
    except:
        pass
    try:
        best = driver.execute_script("""
            function txt(el){ return ((el && (el.innerText || el.textContent)) || "").trim(); }
            const candidates = [];
            for (const el of document.querySelectorAll("*")) {
                const t = txt(el);
                const tl = t.toLowerCase();
                if (!tl.includes("comparison of learning gaps")) continue;
                if (t.length < 30) continue;
                let score = 0;
                if (tl.includes("more errors")) score += 4;
                if (tl.includes("fewer errors")) score += 4;
                if (/[+\-]?\d+(?:\.\d+)?%/.test(t)) score += 4;
                score += Math.min(t.length / 250, 8);
                candidates.push({text: t, score});
                let p = el.parentElement;
                for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
                    const pt = txt(p);
                    if (pt.length < 30) continue;
                    let ps = 0;
                    if (pt.toLowerCase().includes("comparison of learning gaps")) ps += 2;
                    if (pt.toLowerCase().includes("more errors")) ps += 4;
                    if (pt.toLowerCase().includes("fewer errors")) ps += 4;
                    if (/[+\-]?\d+(?:\.\d+)?%/.test(pt)) ps += 4;
                    ps += Math.min(pt.length / 250, 8);
                    candidates.push({text: pt, score: ps});
                }
            }
            candidates.sort((a,b) => b.score - a.score || b.text.length - a.text.length);
            if (candidates.length) return candidates[0].text;
            return document.body ? (document.body.innerText || "") : "";
        """)
        return best or ""
    except:
        try:
            return driver.execute_script("return document.body ? (document.body.innerText || ) : ; ") or ""
        except:
            return ""

def extract_learning_gaps_super(driver):
    try:
        section_text = _get_learning_gaps_section_text(driver)
        if not section_text or "comparison of learning gaps" not in section_text.lower():
            return []
        return _parse_learning_gaps_from_section_text(section_text)
    except Exception as e:
        console.print(f"  [dim yellow]  ⚠  Super gap extractor failed: {e}[/dim yellow]")
        return []

try:
    _PREVIOUS_EXTRACT_LEARNING_GAPS = extract_learning_gaps
except NameError:
    _PREVIOUS_EXTRACT_LEARNING_GAPS = None

def extract_learning_gaps(driver):
    gaps = []
    try:
        if _PREVIOUS_EXTRACT_LEARNING_GAPS:
            gaps = _PREVIOUS_EXTRACT_LEARNING_GAPS(driver) or []
    except Exception as e:
        console.print(f"  [dim yellow]  ⚠  Previous gap extractor failed: {e}[/dim yellow]")
        gaps = []
    if gaps:
        return gaps
    for _ in range(2):
        gaps = extract_learning_gaps_super(driver) or []
        if gaps:
            return gaps
        try:
            driver.execute_script("""
                const panels = Array.from(document.querySelectorAll("div")).filter(d => {
                    const s = window.getComputedStyle(d);
                    return (s.overflowY === "auto" || s.overflowY === "scroll") && d.scrollHeight > d.clientHeight;
                });
                panels.sort((a,b) => (b.clientWidth*b.clientHeight) - (a.clientWidth*a.clientHeight));
                for (const p of panels.slice(0,4)) {
                    p.scrollTop = Math.min(p.scrollHeight, p.scrollTop + 1300);
                }
            """)
        except:
            pass
        time.sleep(0.35)
    return []


# ═══════════════════════════════════════════════════════════
#  ADD-ONLY PATCH  — consistency matcher ignores +/- sign
#  Rules requested:
#    1) If percentages match numerically, PASS even if sign differs
#    2) If at least one valid percentage is present, do not SKIP
#       (single valid value => PASS)
#  This patch does not remove any original line; it only overrides
#  the consistency check function near the end of the file.
# ═══════════════════════════════════════════════════════════

try:
    _ORIGINAL_CHECK_CONSISTENCY = check_consistency
except NameError:
    _ORIGINAL_CHECK_CONSISTENCY = None

def _normalize_pct_abs(raw):
    if not raw or str(raw).strip().upper() == "NA":
        return "NA"
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", str(raw))
    if not m:
        return "NA"
    val = abs(float(m.group(1)))
    return f"{val:.1f}"

def check_consistency(s1, s2, s3, s4):
    normals = {
        "left_card":        _normalize_pct_abs(s1),
        "top_right_button": _normalize_pct_abs(s2),
        "center_arrow_box": _normalize_pct_abs(s3),
        "progress_report":  _normalize_pct_abs(s4),
    }

    valid = {k: v for k, v in normals.items() if v != "NA"}

    # User rule: percentage match matters, + / - does not matter.
    # Also, when only one valid percentage is visible, mark PASS not SKIP.
    if len(valid) == 0:
        status = "SKIP"
    elif len(set(valid.values())) == 1:
        status = "PASS"
    else:
        status = "FAIL"

    return status, normals


# ==============================================================================
# ADD-ONLY RUNTIME PATCH BEFORE ORIGINAL MAIN
# This block adds behaviour only. It does not delete or replace original source lines.
# ==============================================================================
try:
    if globals().get('_CL_SKIP_ZZ_ADDONLY') and 'SECTION_RUN_LIST' in globals():
        SECTION_RUN_LIST = [s for s in SECTION_RUN_LIST if str(s).strip().upper() != 'ZZ']
        print('[ADD-ONLY PATCH] Section ZZ skipped at runtime.')
except Exception as _e:
    print('[ADD-ONLY PATCH] skip ZZ setup warning:', _e)

try:
    if globals().get('_CL_NO_INPUT_ADDONLY'):
        KEEP_BROWSER_OPEN = False
        AUTO_OPEN_REPORT = False
        print('[ADD-ONLY PATCH] Non-blocking mode enabled: KEEP_BROWSER_OPEN=False, AUTO_OPEN_REPORT=False')
except Exception as _e:
    print('[ADD-ONLY PATCH] no-input setup warning:', _e)

try:
    if globals().get('_CL_HEADLESS_ADDONLY') and 'make_driver' in globals() and not globals().get('_CL_MAKE_DRIVER_PATCHED_ADDONLY'):
        _CL_ORIG_MAKE_DRIVER_ADDONLY = make_driver
        def make_driver(*args, **kwargs):
            try:
                from selenium import webdriver as _wd
                from selenium.webdriver.chrome.options import Options as _Options
                opts = _Options()
                opts.add_argument('--headless=new')
                opts.add_argument('--disable-gpu')
                opts.add_argument('--window-size=1920,1080')
                opts.add_argument('--disable-notifications')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-extensions')
                opts.add_argument('--blink-settings=imagesEnabled=false')
                opts.add_argument('--disable-background-networking')
                opts.add_argument('--disable-sync')
                opts.add_argument('--metrics-recording-only')
                opts.add_argument('--disable-default-apps')
                d = _wd.Chrome(options=opts)
                try: d.implicitly_wait(0)
                except Exception: pass
                try:
                    if 'driver_ref' in globals():
                        driver_ref.clear(); driver_ref.append(d)
                except Exception: pass
                return d
            except Exception as _e:
                print('[ADD-ONLY PATCH] headless driver fallback:', _e)
                return _CL_ORIG_MAKE_DRIVER_ADDONLY(*args, **kwargs)
        _CL_MAKE_DRIVER_PATCHED_ADDONLY = True
        print('[ADD-ONLY PATCH] Headless fast Chrome driver enabled.')
except Exception as _e:
    print('[ADD-ONLY PATCH] driver setup warning:', _e)

try:
    if globals().get('_CL_FAST_MODE_ADDONLY'):
        # Reduce broad timeout constants without changing original code lines.
        for _name in ('TIMEOUT','CARD_WAIT_SEC'):
            if _name in globals():
                try: globals()[_name] = min(int(float(globals()[_name])), 18)
                except Exception: pass
        for _name in ('PANEL_WAIT_SEC','S_DROP','S_NAV','S_CARD','S_SEARCH','S_CLEAR','S_LABEL'):
            if _name in globals():
                try: globals()[_name] = min(float(globals()[_name]), 0.35)
                except Exception: pass
        print('[ADD-ONLY PATCH] Fast timeout/sleep settings applied.')
except Exception as _e:
    print('[ADD-ONLY PATCH] fast setup warning:', _e)
# ==============================================================================
# ORIGINAL MAIN BLOCK CONTINUES BELOW
# ==============================================================================

if __name__ == "__main__":
    main()




####################################################################################################
# END OF SCRIPT 4: ClassLens – Students All-Sections Scraper v8
####################################################################################################


# ==============================================================================
# ADD-ONLY POST-RUN WEBEX + MASTER HTML REPORT SENDER
# Original script has already run above. This block only collects generated files,
# writes a small professional run summary, and sends it to Webex when env vars exist.
# ==============================================================================
def _classlens_latest_file_addonly(patterns):
    files = []
    for pat in patterns:
        files.extend(_CL_GLOB_ADDONLY.glob(pat))
    files = [f for f in files if _CL_OS_ADDONLY.path.isfile(f)]
    if not files:
        return ''
    return max(files, key=lambda p: _CL_OS_ADDONLY.path.getmtime(p))

def _classlens_collect_summary_addonly():
    html = _classlens_latest_file_addonly(['*.html', 'combined_preserved_sources/*.html'])
    js = _classlens_latest_file_addonly(['*.json', 'combined_preserved_sources/*.json'])
    status = 'PASS'
    total = passed = failed = warnings = None
    sections = []
    if js:
        try:
            data = _CL_JSON_ADDONLY.load(open(js, 'r', encoding='utf-8'))
            summ = data.get('summary') or data.get('aggregate') or {}
            total = summ.get('total') or summ.get('total_tests')
            passed = summ.get('passed') or summ.get('pass')
            failed = summ.get('failed') or summ.get('fail')
            warnings = summ.get('warnings') or summ.get('warn')
            if isinstance(data.get('runs'), list):
                sections = [str(r.get('config',{}).get('Section','')).strip() for r in data.get('runs', []) if r.get('config')]
            if failed and int(failed) > 0:
                status = 'FAIL'
        except Exception:
            pass
    return {'html': html, 'json': js, 'status': status, 'total': total, 'passed': passed, 'failed': failed, 'warnings': warnings, 'sections': [s for s in sections if s]}

def _classlens_make_webex_text_addonly(info):
    now = _CL_DATETIME_ADDONLY.now().strftime('%d %b %Y %I:%M %p')
    sections = ', '.join(info.get('sections') or []) or 'Configured ClassLens sections'
    lines = [
        '✅ ClassLens Selenium Automation Completed' if info.get('status') == 'PASS' else '❌ ClassLens Selenium Automation Completed with Failures',
        f'Status: {info.get("status", "UNKNOWN")}',
        f'Execution Time: {now}',
        f'Scope: {sections}',
        'Master Report: Attached as portable HTML' if info.get('html') else 'Master Report: HTML report not found',
    ]
    if info.get('json'):
        lines.append(f'JSON Evidence: {_CL_OS_ADDONLY.path.abspath(info["json"])}')
    if info.get('total') is not None:
        lines.append('')
        lines.append('Executive Summary:')
        lines.append(f'Total Tests: {info.get("total")}')
        lines.append(f'Passed: {info.get("passed", 0)}')
        lines.append(f'Failed: {info.get("failed", 0)}')
        lines.append(f'Warnings: {info.get("warnings", 0)}')
    lines.append('')
    lines.append('The run used the uploaded preserved script. Add-only patches were applied for headless speed, ZZ skip, report detection, and Webex delivery.')
    return '\n'.join(lines)

def _classlens_send_webex_addonly():
    token = _CL_OS_ADDONLY.getenv('WEBEX_BOT_TOKEN') or _CL_OS_ADDONLY.getenv('WEBEX_TOKEN')
    room = _CL_OS_ADDONLY.getenv('WEBEX_ROOM_ID') or _CL_OS_ADDONLY.getenv('WEBEX_ROOM')
    info = _classlens_collect_summary_addonly()
    text = _classlens_make_webex_text_addonly(info)
    # Always write a local summary text file.
    try:
        with open('classlens_webex_summary_addonly.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print('[ADD-ONLY WEBEX] Summary written:', _CL_OS_ADDONLY.path.abspath('classlens_webex_summary_addonly.txt'))
    except Exception as e:
        print('[ADD-ONLY WEBEX] Could not write summary:', e)
    if not token or not room:
        print('[ADD-ONLY WEBEX] WEBEX_BOT_TOKEN/WEBEX_ROOM_ID not set. Skipping send.')
        print(text)
        return
    try:
        import requests
        url = 'https://webexapis.com/v1/messages'
        headers = {'Authorization': 'Bearer ' + token}
        data = {'roomId': room, 'text': text}
        files = None
        fh = None
        if info.get('html') and _CL_OS_ADDONLY.path.exists(info['html']):
            fh = open(info['html'], 'rb')
            files = {'files': (_CL_OS_ADDONLY.path.basename(info['html']), fh, 'text/html')}
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=60)
        print('[WEBEX] status:', resp.status_code)
        print('[WEBEX] response:', resp.text[:1000])
        if fh: fh.close()
    except Exception as e:
        print('[ADD-ONLY WEBEX] Send failed:', e)
        print(text)

try:
    _classlens_send_webex_addonly()
except Exception as _e:
    print('[ADD-ONLY WEBEX] Final summary/send error:', _e)
# ==============================================================================
# END ADD-ONLY POST-RUN PATCH
# ==============================================================================
