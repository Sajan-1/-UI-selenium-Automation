
# ==============================================================================
# ADD-ONLY PATCH INSERTED BY MASTER RUNNER
# Suppress individual webbrowser.open() calls when running under the combined
# master report so only one final master dashboard opens after all tests finish.
# Original script content starts immediately after this block; no original line is
# removed or edited.
# ==============================================================================
import os as __cl_master_os
if __cl_master_os.environ.get("CLASSLENS_MASTER_SINGLE_REPORT", "") == "1":
    try:
        import webbrowser as __cl_master_webbrowser
        def __cl_master_suppress_open(url, *args, **kwargs):
            print(f"[MASTER SINGLE REPORT] Suppressed individual report popup: {url}")
            return True
        __cl_master_webbrowser.open = __cl_master_suppress_open
        __cl_master_webbrowser.open_new = __cl_master_suppress_open
        __cl_master_webbrowser.open_new_tab = __cl_master_suppress_open
    except Exception as __cl_master_exc:
        print(f"[MASTER SINGLE REPORT] Browser-popup suppress patch failed: {__cl_master_exc}")
# ==============================================================================
# END ADD-ONLY PATCH INSERTED BY MASTER RUNNER
# ==============================================================================

# ==============================================================================
# ADD-ONLY FAST/HEADLESS PATCH INSERTED BY MASTER RUNNER
# Original script content starts after this block. No original line is removed.
# ==============================================================================
import os as __cl_fast_os
if __cl_fast_os.environ.get("CLASSLENS_FAST_MODE", "1") == "1":
    try:
        import time as __cl_fast_time
        __cl_fast_original_sleep = __cl_fast_time.sleep
        __cl_fast_max_sleep = float(__cl_fast_os.environ.get("CLASSLENS_FAST_MAX_SLEEP", "0.35"))
        def __cl_fast_sleep(seconds):
            try:
                seconds = float(seconds)
            except Exception:
                seconds = 0
            return __cl_fast_original_sleep(min(seconds, __cl_fast_max_sleep))
        __cl_fast_time.sleep = __cl_fast_sleep
        print(f"[FAST MODE] time.sleep capped at {__cl_fast_max_sleep}s")
    except Exception as __cl_fast_exc:
        print(f"[FAST MODE] sleep patch failed: {__cl_fast_exc}")

    try:
        from selenium.webdriver.chrome.options import Options as __cl_fast_Options
        __cl_fast_old_init = __cl_fast_Options.__init__
        def __cl_fast_options_init(self, *args, **kwargs):
            __cl_fast_old_init(self, *args, **kwargs)
            try:
                if __cl_fast_os.environ.get("CLASSLENS_HEADLESS", "1") == "1":
                    self.add_argument("--headless=new")
                self.add_argument("--disable-gpu")
                self.add_argument("--no-sandbox")
                self.add_argument("--window-size=1920,1080")
                self.add_argument("--disable-dev-shm-usage")
                self.add_argument("--disable-notifications")
                self.add_argument("--log-level=3")
            except Exception as __cl_fast_opt_exc:
                print(f"[FAST MODE] chrome option patch failed: {__cl_fast_opt_exc}")
        __cl_fast_Options.__init__ = __cl_fast_options_init
        print("[FAST MODE] Chrome Options patched for headless/speed.")
    except Exception as __cl_fast_exc:
        print(f"[FAST MODE] Chrome Options patch failed: {__cl_fast_exc}")
# ==============================================================================
# END ADD-ONLY FAST/HEADLESS PATCH
# ==============================================================================
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


if __name__ == "__main__":
    main()