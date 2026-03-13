"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         ClassLens – Chapters Tab  •  Full Automated Test Suite              ║
║                                                                              ║
║  Run:  python test_chapters_tab.py                                           ║
║                                                                              ║
║  What it tests:                                                              ║
║   Phase 1  Login                                                             ║
║   Phase 2  Filter selection (Class / Section / Subject / Exam / Compare)    ║
║   Phase 3  Chapters tab navigation + all 4 nav tabs visible                 ║
║   Phase 4  Dynamic chapter card discovery + sort order + sort label         ║
║   Phase 5  Per-chapter (clicks every card):                                 ║
║              • Card list badge  % readable                                  ║
║              • "Change in chapter average" badge % readable                 ║
║              • CONSISTENCY: card badge == change badge  (PASS/FAIL)         ║
║              • Midterm panel:  accuracy %, struggling count, weak count,    ║
║                                weakest concepts list, strongest concepts     ║
║              • Preboard 1 panel: same checks                                ║
║              • "Why this chapter" explanation present                        ║
║              • IMPROVED / DECLINED chip present                              ║
║              • New / Improved / Declined pill badges on concepts             ║
║              • Struggling students section – attempts expand + prints list  ║
║   Phase 6  Search box: filter, clear-restore, no-match                      ║
║   Phase 7  Static UI labels (all key labels visible after opening a card)   ║
║                                                                              ║
║  Output:  colour-coded per test  +  final consistency table  +  summary     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ══════════════════════════════════════════════════════════════════
# ❶  CONFIGURATION  –  edit these to test different class/section
# ══════════════════════════════════════════════════════════════════
LOGIN_URL    = "https://classlens.inferentics.com/login"
CHAPTERS_URL = "https://classlens.inferentics.com/?exams=Midterm%2CPreboard+1&screen=chapters"

USERNAME = os.getenv("CLASSLENS_USER", "sajan")
PASSWORD = os.getenv("CLASSLENS_PASS", "Operations123")

VALUES = {
    "Class":        "12",
    "Section":      "Q",
    "Subject":      "MATHS",
    "Exam":         "Midterm",
    "CompareLeft":  "Midterm",
    "CompareRight": "Preboard 1",
}

EXAM_LABELS   = ["Midterm", "Preboard 1"]   # the two comparison columns
NAV_TABS      = ["Overview", "Chapters", "Questions", "Students"]

# ══════════════════════════════════════════════════════════════════
# ❷  RESULT STORE
# ══════════════════════════════════════════════════════════════════
@dataclass
class Result:
    name:   str
    passed: bool
    detail: str = ""

results: List[Result] = []

def record(name: str, passed: bool, detail: str = "") -> bool:
    results.append(Result(name, passed, detail))
    icon = "✅" if passed else "❌"
    print(f"  {icon}  {name}" + (f"  →  {detail}" if detail else ""))
    return passed

def sec(title: str):
    print(f"\n{'═'*74}\n  {title}\n{'═'*74}")

def sub(title: str):
    print(f"\n  {'─'*68}\n  {title}\n  {'─'*68}")

# ══════════════════════════════════════════════════════════════════
# ❸  UTILITY HELPERS
# ══════════════════════════════════════════════════════════════════
def type_safely(el, text: str):
    el.click()
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.DELETE)
    el.send_keys(text)

def safe_text(el) -> str:
    try:    return (el.text or "").strip()
    except: return ""

def safe_attr(el, attr: str) -> str:
    try:    return (el.get_attribute(attr) or "").strip()
    except: return ""

def arrow_to_sign(s: str) -> str:
    """Convert ↑↓▲▼ to +/- so sign-aware % extraction works."""
    return (s.replace("↑", "+").replace("↓", "-")
             .replace("▲", "+").replace("▼", "-"))

def extract_pct(text: str) -> Optional[str]:
    """
    Extract the first signed percentage from any text blob.
    Handles: +11.3%  -0.6%  ↑11.3%  ↓0.6%  11.3% (→ +11.3%)
    Returns canonical string like '+11.3%' or '-0.6%', else None.
    """
    if not text:
        return None
    t = arrow_to_sign(text)
    t = re.sub(r"\s+", "", t)
    m = re.search(r"([+\-])(\d+\.?\d*)%", t)
    if m:
        return f"{m.group(1)}{m.group(2)}%"
    m2 = re.search(r"(\d+\.?\d*)%", t)
    if m2:
        return f"+{m2.group(1)}%"
    return None

def extract_num(pct: str) -> Optional[float]:
    if not pct:
        return None
    m = re.search(r"[+\-]?\d+\.?\d*", pct)
    return float(m.group()) if m else None

def js_select(driver, sel_el, wanted: str) -> bool:
    return bool(driver.execute_script("""
        const sel = arguments[0], want = arguments[1].trim();
        for (const opt of sel.options) {
            if (opt.textContent.trim() === want) {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('input',  { bubbles: true }));
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
        }
        return false;
    """, sel_el, wanted))

def wait_select_option(driver, idx: int, text: str, timeout: int = 30):
    WebDriverWait(driver, timeout).until(
        lambda d: (
            len(d.find_elements(By.TAG_NAME, "select")) > idx and
            text in [
                o.text.strip()
                for o in d.find_elements(By.TAG_NAME, "select")[idx]
                          .find_elements(By.TAG_NAME, "option")
            ]
        )
    )

def wait_for_chapters_page(driver, timeout: int = 30):
    """Wait until at least one ±% element is visible (chapter cards loaded)."""
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.XPATH,
            "//*[contains(text(),'%') and ("
            "contains(text(),'+') or contains(text(),'-') or "
            "contains(text(),'↑') or contains(text(),'↓'))]")) > 0
    )

# ══════════════════════════════════════════════════════════════════
# ❹  DYNAMIC CHAPTER CARD DISCOVERY
# ══════════════════════════════════════════════════════════════════
def discover_cards(driver) -> List[dict]:
    """
    Dynamically find all chapter cards in the left panel.
    No hardcoded names – works for any class/section/subject.

    Returns: [{ 'name': str, 'pct': str, 'el': WebElement|None }]

    Strategy A: find short ±% badge elements → walk up DOM to find
                the row container whose text contains the chapter name.
    Strategy B: sibling scan on ±% elements.
    Strategy C: page-source regex fallback.
    """
    print("\n  🔎  Discovering chapter cards dynamically …")
    cards: List[dict] = []
    seen:  set         = set()

    IGNORE_NAMES = {
        "chapter", "chapters", "sort chapters", "search chapter",
        "chapter avg: high to low", "chapter avg",
    }

    # ── Strategy A ────────────────────────────────────────────────
    badge_els = driver.find_elements(By.XPATH,
        "//*["
        "  (contains(text(),'+') or contains(text(),'-') or "
        "   contains(text(),'↑') or contains(text(),'↓')) and "
        "  contains(text(),'%') and "
        "  string-length(normalize-space(text())) < 12"
        "]"
    )
    for badge in badge_els:
        pct = extract_pct(safe_text(badge))
        if not pct:
            continue
        for level in range(1, 8):
            try:
                container = badge.find_element(By.XPATH, "/".join([".."] * level))
                ct   = safe_text(container)
                name = re.sub(r"[+\-↑↓▲▼]?\d+\.?\d*\s*%", "", ct).strip()
                name = re.sub(r"[↑↓▲▼]", "", name).strip()
                if (
                    4 < len(name) <= 72
                    and not re.fullmatch(r"[\d\s.]+", name)
                    and name not in seen
                    and name.lower() not in IGNORE_NAMES
                ):
                    seen.add(name)
                    cards.append({"name": name, "pct": pct, "el": container})
                    break
            except Exception:
                continue

    # ── Strategy B ────────────────────────────────────────────────
    if not cards:
        print("  ℹ️   Strategy A: 0 found – trying Strategy B …")
        for el in driver.find_elements(By.XPATH,
                "//*[contains(text(),'%') and string-length(normalize-space(text())) < 15]"):
            pct = extract_pct(safe_text(el))
            if not pct:
                continue
            try:
                parent = el.find_element(By.XPATH, "..")
                for sib in parent.find_elements(By.XPATH, "./*"):
                    st = safe_text(sib)
                    if (st and "%" not in st and 4 < len(st) <= 72
                            and st not in seen):
                        seen.add(st)
                        cards.append({"name": st, "pct": pct, "el": parent})
                        break
            except Exception:
                continue

    # ── Strategy C  (page-source regex) ──────────────────────────
    if not cards:
        print("  ℹ️   Strategy B: 0 found – trying Strategy C (page-source regex) …")
        src = driver.page_source
        pattern = re.compile(
            r">([A-Z][A-Za-z &\-]{3,60}?)<"
            r"(?:(?!</ul>).){0,400}?>"
            r"([+\-↑↓]\d+\.?\d*\s*%)<",
            re.DOTALL,
        )
        for m in pattern.finditer(src):
            name = m.group(1).strip()
            pct  = extract_pct(m.group(2))
            if pct and name not in seen and 3 < len(name) <= 72:
                seen.add(name)
                el = None
                try:
                    el = driver.find_element(By.XPATH,
                        f"//*[contains(text(),'{name.split()[0]}')]"
                        f"/ancestor::*[3]")
                except Exception:
                    pass
                cards.append({"name": name, "pct": pct, "el": el})

    # ── Print discovery result ────────────────────────────────────
    print(f"\n  ✅  {len(cards)} chapter card(s) discovered:")
    for c in cards:
        colour = "🟢" if "+" in c["pct"] else "🔴"
        print(f"       {colour}  {c['name']:<54}  {c['pct']}")
    return cards

# ══════════════════════════════════════════════════════════════════
# ❺  CLICK A CHAPTER CARD
# ══════════════════════════════════════════════════════════════════
def click_card(driver, card: dict) -> bool:
    name  = card["name"]
    first = name.split()[0]
    last  = name.replace("&", "and").split()[-1]

    def try_click(el) -> bool:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el)
            time.sleep(0.3)
            try:    el.click()
            except: driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            return False

    if card.get("el") and try_click(card["el"]):
        return True

    for xp in [
        f"//*[normalize-space(text())='{name}']",
        f"//*[contains(normalize-space(text()),'{name}')]",
        f"//*[contains(text(),'{first}') and contains(text(),'{last}')]",
        f"//*[contains(text(),'{first}')]"
        f"/parent::*[.//*[contains(text(),'%')]]",
        f"//*[contains(text(),'{first}')]/ancestor::*[2]",
        f"//*[contains(text(),'{first}')]/ancestor::*[3]",
    ]:
        try:
            for candidate in driver.find_elements(By.XPATH, xp):
                t = safe_text(candidate)
                if first in t and len(t) < 200 and try_click(candidate):
                    return True
        except Exception:
            continue
    return False

# ══════════════════════════════════════════════════════════════════
# ❻  READ % FROM CARD LIST BADGE  (Location 1)
# ══════════════════════════════════════════════════════════════════
def read_card_badge(driver, card: dict) -> Optional[str]:
    name  = card["name"]
    first = name.split()[0]

    for xp in [
        f"//*[normalize-space(text())='{name}']"
        f"/following-sibling::*[contains(text(),'%')][1]",
        f"//*[contains(text(),'{first}')]"
        f"/following-sibling::*[contains(text(),'%')][1]",
        f"//*[normalize-space(text())='{name}']"
        f"/parent::*//*[contains(text(),'%')"
        f" and string-length(normalize-space(text()))<12][1]",
    ]:
        try:
            for e in driver.find_elements(By.XPATH, xp):
                p = extract_pct(safe_text(e))
                if p:
                    return p
        except Exception:
            continue

    # page-source scan near chapter name
    src = driver.page_source
    m = re.search(
        re.escape(name) + r".{0,200}?([+\-↑↓]\d+\.?\d*)\s*%",
        src, re.DOTALL,
    )
    if m:
        return extract_pct(m.group(1) + "%")

    return card.get("pct")   # fallback to discovery value

# ══════════════════════════════════════════════════════════════════
# ❼  READ % FROM "CHANGE IN CHAPTER AVERAGE" BADGE  (Location 2)
# ══════════════════════════════════════════════════════════════════
def read_change_badge(driver) -> Optional[str]:
    """
    The green/red pill badge in the top-right of the detail panel.
    Label text: "Change in chapter average"
    Badge shows: ↑11.3%  or  ↓0.6%
    """
    for xp in [
        "//*[contains(text(),'Change in chapter')]"
        "/following-sibling::*[1]",
        "//*[contains(text(),'Change in chapter')]"
        "/following-sibling::*[contains(text(),'%')][1]",
        "//*[contains(text(),'Change in chapter')]"
        "/following::*[contains(text(),'%')][1]",
        "//*[contains(text(),'Change in chapter')]"
        "/parent::*//*[contains(text(),'%')"
        " and string-length(normalize-space(text()))<15][1]",
        # Badge may be a button/span with arrow icon + number + %
        "//*[contains(text(),'Change in chapter')]"
        "/following::*[(contains(text(),'↑') or contains(text(),'↓')"
        "  or contains(text(),'+') or contains(text(),'-'))"
        " and contains(text(),'%')][1]",
    ]:
        try:
            for e in driver.find_elements(By.XPATH, xp):
                t = safe_text(e)
                if "%" in t:
                    p = extract_pct(t)
                    if p:
                        return p
        except Exception:
            continue

    # page-source forward scan from label
    src = driver.page_source
    for phrase in ["Change in chapter average", "Change in chapter"]:
        idx = src.find(phrase)
        if idx >= 0:
            region = src[idx: idx + 400]
            m = re.search(r"([+\-↑↓▲▼])\s*(\d+\.?\d*)\s*%", region)
            if m:
                sign = arrow_to_sign(m.group(1))
                return f"{sign}{m.group(2)}%"
            m2 = re.search(r"(\d+\.?\d*)\s*%", region)
            if m2:
                return f"+{m2.group(1)}%"
    return None

# ══════════════════════════════════════════════════════════════════
# ❽  READ ONE EXAM PANEL  (Midterm  or  Preboard 1)
# ══════════════════════════════════════════════════════════════════
def read_exam_panel(driver, exam_label: str) -> dict:
    """
    Locate the exam panel by its header label, then extract:
      accuracy, struggling_count, weak_concepts_count,
      weakest_concepts (list), strongest_concepts (list of dicts)
    """
    data = {
        "label":              exam_label,
        "accuracy":           None,
        "struggling_count":   None,
        "weak_concepts_count": None,
        "weakest_concepts":   [],
        "strongest_concepts": [],
    }

    # ── Find panel container ──────────────────────────────────────
    panel = None
    label_els = driver.find_elements(By.XPATH,
        f"//*[normalize-space(text())='{exam_label}' or "
        f"    contains(normalize-space(text()),'{exam_label}')]")
    for lel in label_els:
        for lvl in range(1, 9):
            try:
                anc = lel.find_element(By.XPATH, "/".join([".."] * lvl))
                at  = safe_text(anc)
                if "ACCURACY" in at and "Struggling" in at:
                    panel = anc
                    break
            except Exception:
                break
        if panel:
            break

    if not panel:
        return data

    pt = safe_text(panel)

    # ── Accuracy % ────────────────────────────────────────────────
    # The large number shown as "73%" or "84.3%"
    acc = re.findall(r"(\d{2,3}\.?\d*)\s*%", pt)
    if acc:
        # Largest number closest to ACCURACY label
        data["accuracy"] = max(acc, key=lambda x: float(x)) + "%"

    # ── Struggling students count ─────────────────────────────────
    m = re.search(r"Struggling\s+students?\s*\n?\s*(\d+)", pt, re.IGNORECASE)
    if m:
        data["struggling_count"] = int(m.group(1))
    else:
        try:
            for se in panel.find_elements(By.XPATH,
                    ".//*[contains(text(),'Struggling')]"):
                parent_t = safe_text(se.find_element(By.XPATH, ".."))
                nums = re.findall(r"\b(\d+)\b", parent_t)
                if nums:
                    data["struggling_count"] = int(nums[0])
                    break
        except Exception:
            pass

    # ── Weak Concepts count ───────────────────────────────────────
    m2 = re.search(r"Weak\s+Concepts?\s*\n?\s*(\d+)", pt, re.IGNORECASE)
    if m2:
        data["weak_concepts_count"] = int(m2.group(1))
    else:
        try:
            for we in panel.find_elements(By.XPATH,
                    ".//*[contains(text(),'Weak Concept') or "
                    "     contains(text(),'Weak concept')]"):
                parent_t = safe_text(we.find_element(By.XPATH, ".."))
                nums = re.findall(r"\b(\d+)\b", parent_t)
                if nums:
                    data["weak_concepts_count"] = int(nums[0])
                    break
        except Exception:
            pass

    # ── Weakest Concepts (numbered list) ─────────────────────────
    try:
        wh_els = panel.find_elements(By.XPATH,
            ".//*[contains(text(),'Weakest Concepts') or "
            "     contains(text(),'Weakest concepts')]")
        if wh_els:
            following = panel.find_elements(By.XPATH,
                ".//*[contains(text(),'Weakest') or "
                "     contains(text(),'weakest')]"
                "/following::*")
            concepts: List[str] = []
            for el in following[:60]:
                t = safe_text(el)
                if not t:
                    continue
                if any(k in t for k in ["Strongest", "strongest", "STRONGEST"]):
                    break
                if (3 < len(t) < 65
                        and not re.fullmatch(r"[\d\s.]+", t)
                        and t not in {"Weakest Concepts", "Weakest concepts"}
                        and t not in concepts):
                    concepts.append(t)
            data["weakest_concepts"] = concepts[:6]
    except Exception:
        pass

    # ── Strongest Concepts (bullet list with % and pill badges) ───
    try:
        sh_els = panel.find_elements(By.XPATH,
            ".//*[contains(text(),'Strongest Concepts') or "
            "     contains(text(),'Strongest concepts')]")
        if sh_els:
            following = panel.find_elements(By.XPATH,
                ".//*[contains(text(),'Strongest') or "
                "     contains(text(),'strongest')]"
                "/following::*")
            concepts_raw: List[str] = []
            for el in following[:80]:
                t = safe_text(el)
                if not t or len(t) > 80:
                    continue
                if t in {"Strongest Concepts", "Strongest concepts"}:
                    continue
                # Include concept names AND their % scores AND pill badges
                if (2 < len(t) < 65
                        and not re.fullmatch(r"[\d\s.]+", t)
                        and t not in concepts_raw):
                    concepts_raw.append(t)
            data["strongest_concepts"] = concepts_raw[:12]
    except Exception:
        pass

    return data


def print_panel(data: dict, chapter: str):
    """Pretty-print one exam panel's extracted data."""
    lbl = data["label"]
    print(f"\n    ┌─── {lbl} Panel  [{chapter}] {'─'*(42-len(lbl)-len(chapter))}")
    print(f"    │  Accuracy            : {data['accuracy'] or 'N/A'}")
    print(f"    │  Struggling students : {data['struggling_count'] if data['struggling_count'] is not None else 'N/A'}")
    print(f"    │  Weak Concepts       : {data['weak_concepts_count'] if data['weak_concepts_count'] is not None else 'N/A'}")
    if data["weakest_concepts"]:
        print(f"    │  Weakest Concepts    :")
        for i, c in enumerate(data["weakest_concepts"], 1):
            print(f"    │    {i}. {c}")
    else:
        print(f"    │  Weakest Concepts    : (none extracted)")
    if data["strongest_concepts"]:
        print(f"    │  Strongest Concepts  :")
        for c in data["strongest_concepts"]:
            pct_m = re.search(r"\d{2,3}%", c)
            print(f"    │    • {c}")
    else:
        print(f"    │  Strongest Concepts  : (none extracted)")
    print(f"    └{'─'*52}")

# ══════════════════════════════════════════════════════════════════
# ❾  STRUGGLING STUDENTS EXPAND
# ══════════════════════════════════════════════════════════════════
def try_expand_struggling(driver, chapter: str):
    """
    Attempt to click the ⓘ / expand button next to 'Struggling students'
    and print the resulting student list.
    """
    print(f"\n    👥  Expanding Struggling Students section …")
    triggers = []

    # Try ⓘ icon (svg / info button) after the Struggling students label
    for xp in [
        "//*[contains(text(),'Struggling')]"
        "/following-sibling::*[self::button or self::svg or "
        "  contains(@class,'icon') or contains(@class,'info') or "
        "  @role='button'][1]",

        "//*[contains(text(),'Struggling')]"
        "/parent::*[contains(@class,'clickable') or @role='button' or "
        "           contains(@class,'link')]",

        "//*[contains(text(),'Struggling')]"
        "/following::*[self::button][1]",

        # Sometimes the whole row is clickable
        "//*[contains(text(),'Struggling students') or "
        "    contains(text(),'Struggling Students')]"
        "/parent::*",
    ]:
        try:
            els = driver.find_elements(By.XPATH, xp)
            if els:
                triggers = els
                break
        except Exception:
            continue

    if not triggers:
        print(f"    ℹ️   No expand trigger found – section may not be collapsible")
        record(f"[{chapter}] Struggling students section expandable", False,
               "No clickable trigger found")
        return

    try:
        t = triggers[0]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", t)
        time.sleep(0.3)
        t.click()
        time.sleep(1.0)

        # Read whatever appeared after clicking
        follow_els = driver.find_elements(By.XPATH,
            "//*[contains(text(),'Struggling')]"
            "/following::*[position()<=40]")
        names: List[str] = []
        for fe in follow_els:
            ft = safe_text(fe)
            if (ft and 2 < len(ft) < 50
                    and "Struggling" not in ft
                    and "Weak" not in ft
                    and "Concept" not in ft
                    and not re.fullmatch(r"[\d\s.%]+", ft)
                    and ft not in names):
                names.append(ft)

        print(f"    ✅  Section expanded.  Students found: {names[:10] or '(none parsed)'}")
        record(f"[{chapter}] Struggling students section expandable", True,
               f"Items: {names[:5]}")
    except Exception as e:
        print(f"    ⚠️   Expand failed: {e}")
        record(f"[{chapter}] Struggling students section expandable", False, str(e))

# ══════════════════════════════════════════════════════════════════
# ❿  BROWSER DRIVER SETUP
# ══════════════════════════════════════════════════════════════════
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option("detach", True)   # keep browser open after script ends

driver = webdriver.Chrome(options=chrome_options)
wait   = WebDriverWait(driver, 30)


# ══════════════════════════════════════════════════════════════════
# PHASE 1 – LOGIN
# ══════════════════════════════════════════════════════════════════
sec("PHASE 1 – LOGIN")
try:
    driver.get(LOGIN_URL)
    u_el = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email']")))
    p_el = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='password']")))
    type_safely(u_el, USERNAME)
    type_safely(p_el, PASSWORD)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']"))).click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(.,'Enter your Class')]")))
    record("Login successful", True, f"user={USERNAME}")
except Exception as e:
    record("Login successful", False, str(e))
    print("\n🔴  Login failed – cannot continue.")
    raise SystemExit(1)


# ══════════════════════════════════════════════════════════════════
# PHASE 2 – FILTER SELECTION
# ══════════════════════════════════════════════════════════════════
sec("PHASE 2 – FILTER SELECTION")
try:
    wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

    filter_steps = [
        (0, "Class",        VALUES["Class"]),
        (1, "Section",      VALUES["Section"]),
        (2, "Subject",      VALUES["Subject"]),
        (3, "Exam",         VALUES["Exam"]),
        (4, "Compare Left", VALUES["CompareLeft"]),
        (5, "Compare Right",VALUES["CompareRight"]),
    ]
    for idx, label, value in filter_steps:
        if idx > 0:
            wait_select_option(driver, idx, value)
        ok = js_select(driver,
                       driver.find_elements(By.TAG_NAME, "select")[idx],
                       value)
        record(f"Filter '{label}' = '{value}'", ok)
        time.sleep(0.5)

    old_url = driver.current_url
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Enter']"))).click()
    wait.until(lambda d: d.current_url != old_url)
    record("Dashboard loaded after Enter", True, driver.current_url)

except Exception as e:
    record("Filter selection", False, str(e))


# ══════════════════════════════════════════════════════════════════
# PHASE 3 – CHAPTERS TAB NAVIGATION
# ══════════════════════════════════════════════════════════════════
sec("PHASE 3 – CHAPTERS TAB NAVIGATION")
try:
    driver.get(CHAPTERS_URL)
    wait.until(lambda d: "screen=chapters" in d.current_url)
    wait_for_chapters_page(driver)
    time.sleep(2.5)   # allow React to fully render all cards
    record("Chapters URL loaded", True, driver.current_url)

    for tab in NAV_TABS:
        els = driver.find_elements(By.XPATH, f"//*[normalize-space()='{tab}']")
        record(f"Nav tab '{tab}' visible", len(els) >= 1)

except Exception as e:
    record("Chapters tab navigation", False, str(e))


# ══════════════════════════════════════════════════════════════════
# PHASE 4 – CHAPTER CARD DISCOVERY + SORT ORDER
# ══════════════════════════════════════════════════════════════════
sec("PHASE 4 – CHAPTER CARD DISCOVERY + SORT ORDER")

chapter_cards = discover_cards(driver)
record("At least 1 chapter card discovered",
       len(chapter_cards) >= 1, f"Total discovered: {len(chapter_cards)}")

# Sort order: values should be descending (High → Low)
pct_nums  = [extract_num(c["pct"]) for c in chapter_cards]
pct_clean = [n for n in pct_nums if n is not None]
if len(pct_clean) >= 2:
    is_desc = all(
        pct_clean[i] >= pct_clean[i + 1]
        for i in range(len(pct_clean) - 1)
    )
    record("Chapter list sorted High → Low (descending)", is_desc,
           f"values: {pct_clean}")
else:
    record("Chapter list sorted High → Low (descending)", False,
           "Not enough numeric values to check")

sort_els = driver.find_elements(By.XPATH, "//*[contains(text(),'Chapter Avg')]")
record("Sort label 'Chapter Avg: High to Low' present", len(sort_els) >= 1)


# ══════════════════════════════════════════════════════════════════
# PHASE 5 – PER-CHAPTER DETAIL PANEL VALIDATION
# ══════════════════════════════════════════════════════════════════
sec("PHASE 5 – PER-CHAPTER DETAIL PANEL VALIDATION")

print("""
  ┌───────────────────────────────────────────────────────────────────────┐
  │  For every chapter card:                                              │
  │    • Card list badge %  ==  "Change in chapter average" badge %       │
  │    • Both exam panels: accuracy, struggling count, weak count         │
  │    • Weakest Concepts list printed                                    │
  │    • Strongest Concepts list printed                                  │
  │    • Struggling students section expand attempted                     │
  └───────────────────────────────────────────────────────────────────────┘
""")

consistency_rows: List[dict] = []

for card in chapter_cards:
    ch = card["name"]
    sub(f"  {ch}   (card shows: {card['pct']})")

    # ── Read card badge % (before clicking) ──────────────────────
    pct_card = read_card_badge(driver, card)
    record(f"[{ch}] Card list badge % readable",
           pct_card is not None, f"value: {pct_card}")

    # ── Click the card ────────────────────────────────────────────
    clicked = click_card(driver, card)
    record(f"[{ch}] Card clickable", clicked)
    if not clicked:
        consistency_rows.append({
            "name": ch, "pct_card": pct_card, "pct_badge": None,
            "match": False, "skip": True,
        })
        continue
    time.sleep(1.5)

    src = driver.page_source

    # ── Read "Change in chapter average" badge % ─────────────────
    pct_badge = read_change_badge(driver)
    record(f"[{ch}] 'Change in chapter average' badge % readable",
           pct_badge is not None, f"value: {pct_badge}")

    # ── CONSISTENCY CHECK ─────────────────────────────────────────
    both_found = pct_card is not None and pct_badge is not None
    values     = [v for v in [pct_card, pct_badge] if v is not None]
    all_same   = (len(set(values)) == 1) if len(values) > 1 else False
    ok         = both_found and all_same

    record(
        f"[{ch}] ✦ CONSISTENCY  card={pct_card}  badge={pct_badge}",
        ok,
        "MATCH ✓" if ok else f"MISMATCH ✗  card={pct_card}  badge={pct_badge}",
    )
    consistency_rows.append({
        "name": ch, "pct_card": pct_card, "pct_badge": pct_badge,
        "match": ok, "skip": False,
    })

    # ── "Why this chapter" explanation ───────────────────────────
    record(f"[{ch}] 'Why this chapter' explanation present",
           any(k in src for k in ["Why this chapter", "Why This Chapter",
                                   "why this chapter"]))

    # ── IMPROVED / DECLINED chip ──────────────────────────────────
    record(f"[{ch}] IMPROVED / DECLINED chip present",
           any(k in src for k in ["IMPROVED", "DECLINED",
                                   "Improved", "Declined"]))

    # ── Both exam panels visible ──────────────────────────────────
    for exam in EXAM_LABELS:
        record(f"[{ch}] '{exam}' panel header visible", exam in src)

    # ── Read + print both exam panels ────────────────────────────
    print(f"\n  📊  Exam panel details for  '{ch}':")
    for exam in EXAM_LABELS:
        pd = read_exam_panel(driver, exam)
        print_panel(pd, ch)

        record(f"[{ch}][{exam}] Accuracy % present",
               pd["accuracy"] is not None, f"{pd['accuracy']}")

        record(f"[{ch}][{exam}] Struggling students count (numeric)",
               pd["struggling_count"] is not None, f"count={pd['struggling_count']}")

        record(f"[{ch}][{exam}] Weak Concepts count (numeric)",
               pd["weak_concepts_count"] is not None, f"count={pd['weak_concepts_count']}")

        record(f"[{ch}][{exam}] Weakest Concepts list has ≥1 item",
               len(pd["weakest_concepts"]) >= 1,
               f"{pd['weakest_concepts']}")

        record(f"[{ch}][{exam}] Strongest Concepts list has ≥1 item",
               len(pd["strongest_concepts"]) >= 1,
               f"{pd['strongest_concepts'][:3]}")

    # ── Pill badges on strongest concepts ────────────────────────
    pill_els = driver.find_elements(By.XPATH,
        "//*[normalize-space()='New' or normalize-space()='Improved' or "
        "    normalize-space()='Declined' or normalize-space()='new' or "
        "    normalize-space()='improved' or normalize-space()='declined' or "
        "    normalize-space()='IMPROVED' or normalize-space()='NEW']")
    pills = list({safe_text(e) for e in pill_els if safe_text(e)})
    record(f"[{ch}] Concept pill badges (New/Improved/Declined) visible",
           len(pills) >= 1, f"found: {pills}")

    # ── Struggling students expand ────────────────────────────────
    try_expand_struggling(driver, ch)


# ══════════════════════════════════════════════════════════════════
# PHASE 6 – SEARCH BOX FUNCTIONALITY
# ══════════════════════════════════════════════════════════════════
sec("PHASE 6 – SEARCH BOX FUNCTIONALITY")

driver.get(CHAPTERS_URL)
wait_for_chapters_page(driver)
time.sleep(1.5)

fresh_cards = discover_cards(driver)

# Find the search input (try placeholder-based, then first input)
sb = None
for inp in driver.find_elements(By.TAG_NAME, "input"):
    ph = safe_attr(inp, "placeholder").lower()
    if "chapter" in ph or "search" in ph:
        sb = inp
        break
if not sb:
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    if all_inputs:
        sb = all_inputs[0]

record("Search input box present", sb is not None,
       f"placeholder='{safe_attr(sb, 'placeholder') if sb else 'N/A'}'")

if sb and fresh_cards:
    def clear_search():
        sb.click()
        sb.send_keys(Keys.CONTROL, "a")
        sb.send_keys(Keys.DELETE)
        time.sleep(1.0)

    test_ch    = fresh_cards[0]["name"]
    search_kw  = test_ch.split()[0]          # first full word – avoids & issues
    other_ch   = fresh_cards[-1]["name"] if len(fresh_cards) > 1 else None

    # ── Test A: filter by first word of first chapter ─────────────
    clear_search()
    sb.send_keys(search_kw)
    time.sleep(1.2)
    record(f"Search '{search_kw}' → '{test_ch}' still visible",
           test_ch in driver.page_source)

    if other_ch and other_ch.split()[0].lower() != search_kw.lower():
        other_vis = driver.find_elements(By.XPATH,
            f"//*[normalize-space()='{other_ch}']")
        hidden = (all(not e.is_displayed() for e in other_vis)
                  if other_vis else True)
        record(f"Search '{search_kw}' → '{other_ch}' filtered out", hidden)

    # ── Test B: clear restores all chapters ──────────────────────
    clear_search()
    src_clear = driver.page_source
    missing = [c["name"] for c in fresh_cards
               if c["name"] not in src_clear]
    record("Search cleared → all chapters restored",
           len(missing) == 0,
           f"Missing: {missing}" if missing else "all present")

    # ── Test C: no-match hides everything ────────────────────────
    clear_search()
    sb.send_keys("ZZZNOMATCH99")
    time.sleep(1.0)
    vis = driver.find_elements(By.XPATH,
          f"//*[normalize-space()='{test_ch}']")
    gone = all(not e.is_displayed() for e in vis) if vis else True
    record("Search 'ZZZNOMATCH99' → chapter cards hidden", gone)
    clear_search()


# ══════════════════════════════════════════════════════════════════
# PHASE 7 – STATIC UI LABELS
# ══════════════════════════════════════════════════════════════════
sec("PHASE 7 – STATIC UI LABELS")

# Reload and click first card so the detail panel is open
driver.get(CHAPTERS_URL)
wait_for_chapters_page(driver)
time.sleep(1.5)

label_cards    = discover_cards(driver)
panel_open     = False
if label_cards:
    panel_open = click_card(driver, label_cards[0])
    if panel_open:
        time.sleep(1.5)
        print(f"  ℹ️   Clicked '{label_cards[0]['name']}' to open detail panel")
    else:
        print("  ⚠️   Could not click first card – detail labels may be absent")

record("First card clicked (detail panel open)", panel_open)

src = driver.page_source

label_checks = [
    # ── List-panel labels (always visible) ──────────────────────
    ("Sort label 'Chapter Avg' present",
     ["Chapter Avg", "chapter avg"]),
    ("Nav tab 'Chapters'",
     ["Chapters"]),
    ("Nav tab 'Overview'",
     ["Overview"]),
    ("Nav tab 'Questions'",
     ["Questions"]),
    ("Nav tab 'Students'",
     ["Students"]),
    # ── Detail-panel labels (visible after card click) ───────────
    ("'Midterm' column header",
     ["Midterm", "midterm", "MIDTERM"]),
    ("'Preboard 1' column header",
     ["Preboard 1", "Preboard1", "preboard 1"]),
    ("'ACCURACY' metric label",
     ["ACCURACY", "Accuracy", "accuracy"]),
    ("'Struggling students' label",
     ["Struggling students", "Struggling Students", "Struggling"]),
    ("'Weak Concepts' label",
     ["Weak Concepts", "Weak concepts", "Weak Concept"]),
    ("'Weakest Concepts' section label",
     ["Weakest Concepts", "Weakest concepts", "weakest concepts"]),
    ("'Strongest Concepts' section label",
     ["Strongest Concepts", "Strongest concepts", "strongest concepts"]),
    ("'Why this chapter' explanation",
     ["Why this chapter", "Why This Chapter", "why this chapter"]),
    ("IMPROVED / DECLINED status chip",
     ["IMPROVED", "DECLINED", "Improved", "Declined"]),
    ("'Change in chapter average' label",
     ["Change in chapter average", "Change in chapter", "change in chapter"]),
    ("Concept pill badges (New / Improved / Declined)",
     ["New", "Improved", "Declined", "NEW", "IMPROVED"]),
]

for label, keywords in label_checks:
    record(label, any(k in src for k in keywords))


# ══════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════
passed_list = [r for r in results if r.passed]
failed_list = [r for r in results if not r.passed]

# ── Consistency table ─────────────────────────────────────────────
print(f"\n{'═'*74}")
print("  % CONSISTENCY TABLE")
print(f"  Card list badge  vs  'Change in chapter average' badge")
print(f"{'═'*74}")
W = 50
print(f"  {'Chapter':<{W}}  {'Card':>9}  {'Badge':>9}  Result")
print(f"  {'─'*W}  {'─'*9}  {'─'*9}  ──────")
for row in consistency_rows:
    if row["skip"]:
        status = "⏭  SKIP"
    else:
        status = "✅ PASS" if row["match"] else "❌ FAIL"
    print(
        f"  {row['name']:<{W}} "
        f" {(row['pct_card']  or 'N/A'):>9} "
        f" {(row['pct_badge'] or 'N/A'):>9}  {status}"
    )

# ── Overall summary ───────────────────────────────────────────────
print(f"\n{'═'*74}")
print("  OVERALL TEST SUMMARY")
print(f"{'═'*74}")
print(f"  Chapters discovered : {len(chapter_cards)}")
print(f"  Total test cases    : {len(results)}")
print(f"  ✅  Passed          : {len(passed_list)}")
print(f"  ❌  Failed          : {len(failed_list)}")

if failed_list:
    print(f"\n  FAILED TESTS  ({len(failed_list)} total):")
    print(f"  {'─'*70}")
    for r in failed_list:
        print(f"  ❌  {r.name}")
        if r.detail:
            print(f"        ↳  {r.detail}")

print(f"\n  {'🎉  ALL TESTS PASSED' if not failed_list else '⚠️   SOME TESTS FAILED – see list above'}")
print(f"{'═'*74}\n")
print("🟢  Browser kept open (detach=True).  Close manually when done.")
