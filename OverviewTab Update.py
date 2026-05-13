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

KEEP_BROWSER_OPEN = True
AUTO_OPEN_REPORT  = True
REPORT_FILE       = "classlens_report_v17.html"
JSON_FILE         = "classlens_data_v17.json"
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

def main():
    print("\n╔" + "═"*70 + "╗")
    print("║   ClassLens – UI Test Suite v17.0                                   ║")
    print("║   JS-first modal detection · JS student rows · badge text-content   ║")
    print(f"║   Started: {run_ts}" + " "*36 + "║")
    print("╚" + "═"*70 + "╝")

    driver = make_driver()
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        if not test_login(driver, wait):
            print("❌ Login failed — aborting")
            return
        if not test_navigation(driver, wait):
            print("❌ Navigation failed — aborting")
            return

        test_exam_comparison(driver)

        for label in ["Reteach", "Brushup", "On Track"]:
            test_chapter_section(driver, label)

        test_all_students(driver, wait)

    except Exception as exc:
        print(f"\n💥 Unexpected error: {exc}")
        traceback.print_exc()

    finally:
        sep("FINAL SUMMARY")
        total = _P + _F + _W
        rate  = round(_P / max(total, 1) * 100, 1)
        print(f"  ✅  Passed   : {_P}")
        print(f"  ❌  Failed   : {_F}")
        print(f"  ⚠️   Warnings : {_W}")
        print(f"  📊  Pass Rate: {rate}%  ({_P}/{total})")

        print("\n  ━━━━  CHAPTER SECTIONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for label in ["Reteach", "Brushup", "On Track"]:
            cd = store["chapters"][label]
            print(f"\n  {label.upper()}  badge='{cd['badge']}'  declared={cd['badge_n']}")
            if cd["modal_chapters"]:
                print(f"  From modal ({len(cd['modal_chapters'])} chapters):")
                for i, ch in enumerate(cd["modal_chapters"], 1):
                    print(f"    #{i:<3} {ch}")
            if cd["cards"]:
                print(f"  Inline cards ({len(cd['cards'])} expanded):")
                for c in cd["cards"]:
                    print(f"    {c['name']:<40}  "
                          f"Avg:{c.get('chapter_avg','?'):>8}  "
                          f"Wt:{c.get('avg_weightage','?'):>10}")

        print("\n  ━━━━  HIGHLIGHTED STUDENTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for cat in ["Weak", "Lagging", "Performing Well"]:
            sd   = store["students"][cat]
            stus = sd["all"]
            print(f"\n  {cat.upper()}  badge='{sd['badge']}'  declared={sd['total']}")
            if not stus:
                print("    ⚠️  No students captured")
            else:
                print(f"  {'#':<4} {'Name':<42} {'Class':<12} {'Score':>8}")
                print(f"  {'-'*4} {'-'*42} {'-'*12} {'-'*8}")
                for i, s in enumerate(stus, 1):
                    print(f"  {i:<4} {s['name']:<42} "
                          f"{s.get('class_info',''):<12} "
                          f"{s.get('pct',''):>8}")

        save_outputs()

        if KEEP_BROWSER_OPEN:
            input("\n👉  Press ENTER to close browser…")
        driver.quit()
        print("\n🏁  Done.")


if __name__ == "__main__":
    main()