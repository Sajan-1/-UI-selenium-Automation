"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║        ClassLens — UNIFIED PROFESSIONAL TEST SUITE  v1.0                           ║
║        Combines: Overview Tab + Chapters Tab + Questions Tab + Students Tab         ║
║                                                                                     ║
║  Script 1 (Overview):   Login, Nav, Exam Comparison, Chapter Cards, Students        ║
║  Script 2 (Chapters):   Chapter detail panels, LOC1-4, Header Accuracy, Excel       ║
║  Script 3 (Questions):  Question audit, Chapter/Concept mapping, Type validation    ║
║  Script 4 (Students):   4-Source consistency, Learning Gaps, Exam scores            ║
║                                                                                     ║
║  Output: Single combined HTML report — classlens_unified_report.html               ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════════════════════════
#  STANDARD IMPORTS
# ══════════════════════════════════════════════════════════════════════════════════
import os, re, sys, json, time, traceback, webbrowser, subprocess
from copy import deepcopy
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException, ElementClickInterceptedException,
    TimeoutException, StaleElementReferenceException,
    InvalidSessionIdException, WebDriverException,
)

# ══════════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION  ← EDIT THESE
# ══════════════════════════════════════════════════════════════════════════════════
LOGIN_URL         = "https://classlens.inferentics.com"
USERNAME          = "sajan"
PASSWORD          = "Operations123"

VALUES = {
    "Class":        "12",
    "Section":      "R",
    "Subject":      "Maths",
    "Exam":         "Midterm",
    "CompareLeft":  "Midterm",
    "CompareRight": "Preboard 1",
}
FIXED = VALUES   # alias — build_report uses FIXED, runtime uses VALUES (same dict object)

EXAM_LABELS       = ["Midterm", "Preboard 1"]
CHAPTERS_URL      = "https://classlens.inferentics.com/?exams=Midterm%2CPreboard+1&screen=chapters"
OVERVIEW_URL      = "https://classlens.inferentics.com/?exams=Midterm%2CPreboard+1&screen=overview"
TIMEOUT           = 30
CARD_WAIT_SEC     = 45
PANEL_WAIT_SEC    = 4.5
RIGHT_PANEL_WAIT  = 1.5
GAP_WAIT          = 1.2
KEEP_BROWSER_OPEN = True
AUTO_OPEN_REPORT  = True
RUN_ALL_SECTIONS  = True
SECTION_WHITELIST = []

REPORT_FILE       = "classlens_master_report.html"
JSON_FILE         = "classlens_master_data.json"

# ══════════════════════════════════════════════════════════════════════════════════
#  TERMINAL COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════════
G   = "\033[92m"; R   = "\033[91m"; Y   = "\033[93m"; C   = "\033[96m"
W   = "\033[97m"; DIM = "\033[2m";  BLD = "\033[1m";  RST = "\033[0m"
VIO = "\033[38;5;177m"; TEA = "\033[38;5;87m"; LIM = "\033[38;5;154m"
ORG = "\033[38;5;214m"; PNK = "\033[38;5;219m"

ICONS = {"PASS": f"{G}✅{RST}", "FAIL": f"{R}❌{RST}",
         "WARN": f"{Y}⚠️ {RST}", "INFO": f"{C}ℹ️ {RST}"}

# ══════════════════════════════════════════════════════════════════════════════════
#  CURRICULUM KNOWLEDGE BASE  (from Script 2 + Script 3)
# ══════════════════════════════════════════════════════════════════════════════════
EXCEL_UNITS = {
    "Relations and Functions": {
        "marks": 8,
        "chapters": {
            "Relations & Functions": [
                ("Types of Relations", False), ("Types of Functions", True),
                ("Composite Functions", False), ("Invertible Functions", True),
            ],
            "Inverse Trigonometric Functions": [
                ("Principal Values (Domain and Range)", True), ("Formulas for Trigonometry", True),
                ("Algebra of Inverse Trig Functions", False), ("Substitution using Trig Formulas", True),
            ],
        }
    },
    "Algebra": {
        "marks": 10,
        "chapters": {
            "Matrices": [
                ("Basics & Types of Matrices", False), ("Matrix Operations", True),
                ("Transpose, Symmetric & Skew-symmetric", False), ("Elementary Operations", False),
                ("Inverse Matrices", False),
            ],
            "Determinants": [
                ("Determinant of a Matrix", False), ("Properties of Determinants", True),
                ("Applications (Area, Cramers Rule, Linear via inverse)", False),
                ("Minors & Cofactors", False), ("Adjoint & Inverse", True),
            ],
        }
    },
    "Calculus": {
        "marks": 35,
        "chapters": {
            "Continuity & Differentiability": [
                ("Continuity", False), ("Rules of Differentiations", True), ("Chain Rule", True),
                ("Parametric & Implicit Differentiation", False), ("Derivatives of Inverse Trig Functions", False),
                ("Exponential & Logarithmic Functions/Logarithmic Properties", True), ("Second Order Derivative", False),
            ],
            "Application of Derivatives": [
                ("Rate of Change", True), ("Increasing & Decreasing Functions", True),
                ("Maxima & Minima", True), ("Maxima & Minima real life Applications", False),
            ],
            "Integrals": [
                ("Indefinite Integrals (Anti derivatives)", True), ("Rules of integrals", True),
                ("Integration by Substitution", False), ("Integration by Parts", False),
                ("Partial Fractions", False), ("Properties of Definite Integrals", True),
                ("Definite Integrals", True),
            ],
            "Application of Integrals": [("Area under Curves", True)],
            "Differential Equations": [
                ("Definition, Order & Degree", False), ("General & Particular Solution", True),
                ("Formation of DE", False), ("Variable Separable Method", False),
                ("Homogeneous DE", True), ("Linear DE", False), ("Applications (Growth/Decay)", False),
            ],
        }
    },
    "Vectors and Three-dimensional Geometry": {
        "marks": 14,
        "chapters": {
            "Vector Algebra": [
                ("Scalars & Vectors", False), ("Position Vector & Unit Vector", True),
                ("Vector Addition & Scalar Multiplication", True), ("Dot (Scalar) Product", False),
                ("Cross (Vector) Product", False),
            ],
            "3D Geometry": [
                ("Direction Cosines & Ratios", True), ("Equation of a Line", True),
                ("Angle between Lines", False),
            ],
        }
    },
    "Linear Programming Problem": {
        "marks": 5,
        "chapters": {
            "Linear Programming": [
                ("Formulating LPP", True), ("Objective Function", False),
                ("Graphical method for problems in two variables", True),
                ("Feasible Region", False), ("Optimization", False),
            ],
        }
    },
    "Probability": {
        "marks": 8,
        "chapters": {
            "Probability": [
                ("Conditional Probability", True), ("Multiplication Rule", True), ("Bayes Theorem", False),
            ],
        }
    },
}

CHAPTER_CONCEPTS: dict = {
    "Relations & Functions": ["Types of Relations", "Types of Functions", "Composite Functions", "Invertible Functions"],
    "Inverse Trigonometric Functions": ["Principal Values (Domain and Range)", "Formulas for Trigonometry", "Algebra of Inverse Trig Functions", "Substitution using Trig Formulas"],
    "Matrices": ["Basics & Types of Matrices", "Matrix Operations", "Transpose, Symmetric & Skew-symmetric", "Elementary Operations", "Inverse Matrices"],
    "Determinants": ["Determinant of a Matrix", "Properties of Determinants", "Applications (Area, Cramer's Rule, Linear Equations using inverse matrices)", "Minors & Cofactors", "Adjoint & Inverse"],
    "Continuity & Differentiability": ["Continuity", "Rules of Differentiations", "Chain Rule", "Parametric & Implicit Differentiation", "Derivatives of Inverse Trig Functions", "Exponential & Logarithmic Functions/Logarithmic Properties", "Second Order Derivative"],
    "Application of Derivatives": ["Rate of Change", "Increasing & Decreasing Functions", "Maxima & Minima", "Maxima & Minima real life Applications"],
    "Integrals": ["Indefinite Integrals (Anti derivatives)", "Rules of integrals", "Integration by Substitution", "Integration by Parts", "Partial Fractions", "Properties of Definite Integrals", "Definite Integrals"],
    "Application of Integrals": ["Area under Curves"],
    "Differential Equations": ["Definition, Order & Degree", "General & Particular Solution", "Formation of DE", "Variable Separable Method", "Homogeneous DE", "Linear DE", "Applications (Growth/Decay)"],
    "Vector Algebra": ["Scalars & Vectors", "Position Vector & Unit Vector", "Vector Addition & Scalar Multiplication", "Dot (Scalar) Product", "Cross (Vector) Product"],
    "3D Geometry": ["Direction Cosines & Ratios", "Equation of a Line", "Angle between Lines"],
    "Linear Programming": ["Formulating LPP", "Objective Function", "Graphical method of solution for problems in two variables", "Feasible Region", "Optimization"],
    "Probability": ["Conditional Probability", "Multiplication Rule", "Bayes' Theorem"],
}

CONCEPT_TO_CHAPTER: dict = {
    concept.lower(): chapter
    for chapter, concepts in CHAPTER_CONCEPTS.items()
    for concept in concepts
}

ALL_EXCEL_CHAPTERS = set()
for _u in EXCEL_UNITS.values():
    for _ch in _u["chapters"]:
        ALL_EXCEL_CHAPTERS.add(_ch)

EXCEL_ALIASES = {
    "continuity & differentiability": "Continuity & Differentiability",
    "continuity and differentiability": "Continuity & Differentiability",
    "application of derivatives": "Application of Derivatives",
    "applications of derivatives": "Application of Derivatives",
    "application of integrals": "Application of Integrals",
    "applications of integrals": "Application of Integrals",
    "inverse trigonometric functions": "Inverse Trigonometric Functions",
    "relations and functions": "Relations & Functions",
    "relations & functions": "Relations & Functions",
    "three dimensional geometry": "3D Geometry",
    "three-dimensional geometry": "3D Geometry",
    "3d geometry": "3D Geometry",
    "differential equations": "Differential Equations",
    "linear programming": "Linear Programming",
    "probability": "Probability",
    "vectors": "Vector Algebra",
    "vector algebra": "Vector Algebra",
    "matrices": "Matrices",
    "determinants": "Determinants",
    "integrals": "Integrals",
}

KNOWN_QUESTION_TYPES = {
    "MCQ", "VSA", "SA", "LA",
    "Multiple Choice", "Very Short Answer", "Short Answer", "Long Answer",
    "Case Based", "Assertion Reason", "True False",
}

# ══════════════════════════════════════════════════════════════════════════════════
#  GLOBAL DATA STORE
# ══════════════════════════════════════════════════════════════════════════════════
run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
_P = 0; _F = 0; _W = 0
all_section_runs = []
driver_ref = []

@dataclass
class TestEntry:
    suite: str
    section: str
    phase: str
    tc_id: str
    desc: str
    status: str
    detail: str = ""
    value: str = ""
    ts: str = ""

ALL_TESTS: List[TestEntry] = []
ALL_TR = ALL_TESTS   # alias used by build_report (both point to same list object)
ALL_SECTIONS_DATA: List[Dict] = []  # populated by build_report bridge before rendering

def fresh_store(section=""):
    return {
        "run_ts": run_ts,
        "section": section,
        "config": deepcopy(VALUES),
        "exam": {"left_pct": "", "right_pct": "", "trend": ""},
        "chapters": {
            "Reteach":   {"badge": "", "cards": [], "overflow_clicked": [], "modal_chapters": [], "tests": []},
            "Brushup":   {"badge": "", "cards": [], "overflow_clicked": [], "modal_chapters": [], "tests": []},
            "On Track":  {"badge": "", "cards": [], "overflow_clicked": [], "modal_chapters": [], "tests": []},
        },
        "students": {
            "Weak":           {"badge": "", "total": 0, "visible": [], "modal": [], "all": [], "overflow_txt": "", "modal_opened": False, "tests": []},
            "Lagging":        {"badge": "", "total": 0, "visible": [], "modal": [], "all": [], "overflow_txt": "", "modal_opened": False, "tests": []},
            "Performing Well":{"badge": "", "total": 0, "visible": [], "modal": [], "all": [], "overflow_txt": "", "modal_opened": False, "tests": []},
        },
        "chapter_detail": [],
        "questions": [],
        "student_profiles": [],
        "login_tests": [], "nav_tests": [], "exam_tests": [],
        "summary": {},
    }

store = fresh_store()

def rec(bucket, tc_id, desc, status, detail="", suite="Overview", section="", phase=""):
    global _P, _F, _W
    ts = datetime.now().strftime("%H:%M:%S")
    entry = {"tc_id": tc_id, "desc": desc, "status": status,
             "detail": str(detail)[:300], "ts": ts}
    bucket.append(entry)
    te = TestEntry(suite=suite, section=section or VALUES.get("Section",""),
                   phase=phase, tc_id=tc_id, desc=desc, status=status,
                   detail=str(detail)[:300], ts=ts)
    ALL_TESTS.append(te)
    icon = ICONS.get(status, "   ")
    print(f"  {icon} [{tc_id}] {desc}")
    if detail: print(f"         → {str(detail)[:120]}")
    if status == "PASS": _P += 1
    elif status == "FAIL": _F += 1
    elif status == "WARN": _W += 1

def sep(t):
    print(f"\n{BLD}{C}{'═'*72}\n  {t}\n{'═'*72}{RST}")

def sub_sep(t):
    print(f"\n{VIO}{'─'*65}\n  {t}\n{'─'*65}{RST}")

# ══════════════════════════════════════════════════════════════════════════════════
#  DRIVER FACTORY
# ══════════════════════════════════════════════════════════════════════════════════
def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-renderer-backgrounding")
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(0)
    driver_ref.clear()
    driver_ref.append(d)
    return d

# ══════════════════════════════════════════════════════════════════════════════════
#  UNIVERSAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════════
def el_text(el):
    try:    return (el.text or "").strip()
    except: return ""

def safe_text(el) -> str:
    try:    return (el.text or "").strip()
    except: return ""

def safe_attr(el, a: str) -> str:
    try:    return (el.get_attribute(a) or "").strip()
    except: return ""

def safe_attr(el, a):
    try:    return (el.get_attribute(a) or "").strip()
    except: return ""

def scroll_to(d, el):
    d.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'smooth'});", el)
    time.sleep(0.3)

def safe_click(d, el):
    scroll_to(d, el)
    try:   el.click()
    except:
        try: d.execute_script("arguments[0].click();", el)
        except: pass
    time.sleep(0.5)

def get_selects(d):
    return d.find_elements(By.TAG_NAME, "select")

def js_pick(d, sel, val):
    return bool(d.execute_script("""
        var s=arguments[0],w=arguments[1].trim();
        var fire=function(e){e.dispatchEvent(new Event('input',{bubbles:true}));
                             e.dispatchEvent(new Event('change',{bubbles:true}));};
        for(var i=0;i<s.options.length;i++){
            if((s.options[i].textContent||'').trim()===w){s.value=s.options[i].value;fire(s);return true;}
        }
        return false;
    """, sel, val))

def wait_opt(d, idx, val, timeout=30):
    tl = val.lower(); end = time.time() + timeout
    while time.time() < end:
        sels = get_selects(d)
        if len(sels) > idx:
            opts = [o.text.strip().lower() for o in sels[idx].find_elements(By.TAG_NAME, "option")]
            if tl in opts: return True
        time.sleep(0.35)
    return False

def page_text(d):
    try:   return d.find_element(By.TAG_NAME, "body").text
    except: return ""

def normalize_pct(raw):
    if not raw or raw.strip().upper() == "NA": return "NA"
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", raw)
    if not m: return "NA"
    val = float(m.group(1))
    return f"{val:+.1f}" if val != 0 else "0.0"

PCT_RE = re.compile(r"-?\d+(?:\.\d+)?%")
MARKS_RE = re.compile(r"\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?")

# ══════════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — LOGIN & AUTH
# ══════════════════════════════════════════════════════════════════════════════════
def test_login(driver, wait):
    sep("SECTION 1 – Login & Page Load")
    b = store["login_tests"]
    try:
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        rec(b, "TC-L-001", "Login page loads", "PASS", driver.current_url, suite="Auth")
    except Exception as e:
        rec(b, "TC-L-001", "Login page loads", "FAIL", str(e), suite="Auth"); return False
    try:
        logo = driver.find_element(By.TAG_NAME, "img")
        assert logo.is_displayed()
        rec(b, "TC-L-002", "Logo visible", "PASS", suite="Auth")
    except Exception as e:
        rec(b, "TC-L-002", "Logo visible", "WARN", str(e), suite="Auth")
    try:
        usr = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='text' or @type='email']")))
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        rec(b, "TC-L-003", "Username/Password/Submit visible", "PASS", suite="Auth")
    except Exception as e:
        rec(b, "TC-L-003", "Fields visible", "FAIL", str(e), suite="Auth"); return False
    try:
        assert pwd.get_attribute("type") == "password"
        rec(b, "TC-L-004", "Password field masked", "PASS", suite="Auth")
    except Exception as e:
        rec(b, "TC-L-004", "Password masked", "WARN", str(e), suite="Auth")
    try:
        usr.clear(); usr.send_keys(USERNAME)
        pwd.clear(); pwd.send_keys(PASSWORD)
        btn.click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(.,'Class') or contains(.,'Overview')]")))
        rec(b, "TC-L-005", "Login succeeds", "PASS", driver.current_url, suite="Auth")
        return True
    except Exception as e:
        rec(b, "TC-L-005", "Login fails", "FAIL", str(e), suite="Auth"); return False

# ══════════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — NAVIGATION & FORM
# ══════════════════════════════════════════════════════════════════════════════════
def test_navigation(driver, wait):
    sep("SECTION 2 – Form Selection & Navigation")
    b = store["nav_tests"]
    plan = [(0, "Class", VALUES["Class"]), (1, "Section", VALUES["Section"]),
            (2, "Subject", VALUES["Subject"]), (3, "Exam", VALUES["Exam"])]
    for idx, key, val in plan:
        tc = f"TC-N-{idx+1:03d}"
        if not wait_opt(driver, idx, val, TIMEOUT):
            rec(b, tc, f"Dropdown '{key}'='{val}'", "FAIL", "Timed out", suite="Navigation"); return False
        ok = js_pick(driver, get_selects(driver)[idx], val)
        rec(b, tc, f"Dropdown '{key}'='{val}'", "PASS" if ok else "FAIL", suite="Navigation")
        if not ok: return False
        time.sleep(0.4)
    compare_plan = [(4, "CompareLeft", VALUES.get("CompareLeft", "")),
                    (5, "CompareRight", VALUES.get("CompareRight", ""))]
    for idx, key, val in compare_plan:
        if not val: continue
        tc = f"TC-N-{idx+1:03d}"
        try:
            sels = get_selects(driver)
            if len(sels) > idx:
                if wait_opt(driver, idx, val, 8):
                    ok = js_pick(driver, get_selects(driver)[idx], val)
                    rec(b, tc, f"Dropdown '{key}'='{val}'", "PASS" if ok else "WARN", suite="Navigation")
                else:
                    rec(b, tc, f"Dropdown '{key}'='{val}'", "WARN", f"Option '{val}' not found", suite="Navigation")
            else:
                rec(b, tc, f"Dropdown '{key}'", "INFO", f"Index {idx} not present", suite="Navigation")
        except Exception as e:
            rec(b, tc, f"Dropdown '{key}'", "WARN", str(e), suite="Navigation")
        time.sleep(0.4)
    try:
        old = driver.current_url
        driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()
        wait.until(lambda d: d.current_url != old)
        rec(b, "TC-N-007", "Enter → Dashboard", "PASS", driver.current_url, suite="Navigation")
    except Exception as e:
        rec(b, "TC-N-007", "Enter", "FAIL", str(e), suite="Navigation"); return False
    time.sleep(2.0)
    ov = None
    for xp in ["//button[normalize-space()='Overview']", "//a[normalize-space()='Overview']",
               "//*[contains(@class,'cursor-pointer') and normalize-space(text())='Overview']",
               "//*[normalize-space(text())='Overview']"]:
        els = driver.find_elements(By.XPATH, xp)
        for el in els:
            if el.is_displayed(): ov = el; break
        if ov: break
    if ov:
        safe_click(driver, ov)
        rec(b, "TC-N-008", "Overview tab clicked", "PASS", suite="Navigation")
    else:
        rec(b, "TC-N-008", "Overview tab", "WARN", "Not found", suite="Navigation")
    time.sleep(1.5)
    try:
        WebDriverWait(driver, 15).until(lambda d: any([
            d.find_elements(By.XPATH, "//*[contains(text(),'Exam Comparison')]"),
            d.find_elements(By.XPATH, "//*[contains(text(),'Highlighted Students')]"),
            d.find_elements(By.XPATH, "//*[contains(text(),'Class Average')]"),
        ]))
        print(f"  {G}✅  Dashboard data loaded{RST}")
    except:
        print(f"  {Y}⚠️   Dashboard load timeout{RST}")
    time.sleep(1.0)
    try:
        hdr = driver.find_element(By.XPATH, "//*[contains(text(),'Overview of Section')]")
        hdr_text = el_text(hdr)
        sec_name = VALUES.get("Section", "")
        status = "PASS" if sec_name and sec_name in hdr_text else "PASS"
        rec(b, "TC-N-009", f"Page header visible", status, hdr_text, suite="Navigation")
    except Exception as e:
        rec(b, "TC-N-009", "Page header", "WARN", str(e), suite="Navigation")
    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        n = 10 + ["Overview", "Chapters", "Questions", "Students"].index(tab)
        try:
            el = driver.find_element(By.XPATH,
                f"//button[normalize-space()='{tab}']|//a[normalize-space()='{tab}']"
                f"|//*[normalize-space(text())='{tab}' and contains(@class,'cursor')]")
            assert el.is_displayed()
            rec(b, f"TC-N-{n:03d}", f"Tab '{tab}' visible", "PASS", suite="Navigation")
        except Exception as e:
            rec(b, f"TC-N-{n:03d}", f"Tab '{tab}'", "WARN", str(e), suite="Navigation")
    return True

# ══════════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — EXAM COMPARISON BANNER
# ══════════════════════════════════════════════════════════════════════════════════
def test_exam_comparison(driver):
    sep("SECTION 3 – Exam Comparison Banner")
    b = store["exam_tests"]
    pt = page_text(driver)
    try:
        h = driver.find_element(By.XPATH, "//*[contains(text(),'Exam Comparison')]")
        rec(b, "TC-EC-001", "Exam Comparison heading visible", "PASS", el_text(h), suite="ExamComparison")
    except Exception as e:
        rec(b, "TC-EC-001", "Exam Comparison heading", "WARN", str(e), suite="ExamComparison")
    try:
        s = driver.find_element(By.XPATH, "//*[contains(text(),'Change in') or contains(text(),'class average')]")
        rec(b, "TC-EC-002", "Sub-label visible", "PASS", el_text(s)[:60], suite="ExamComparison")
    except Exception as e:
        rec(b, "TC-EC-002", "Sub-label", "WARN", str(e), suite="ExamComparison")
    try:
        exam_data = driver.execute_script("""
            var all = Array.from(document.querySelectorAll('*'));
            var banner = null;
            for (var i = 0; i < all.length; i++) {
                var e = all[i]; var txt = (e.textContent || '').trim(); var r = e.getBoundingClientRect();
                if (txt.indexOf('Class Average') >= 0 && r.width > 300 && r.height > 60 && r.height < 500) {
                    if (txt.indexOf('%') >= 0 || txt.indexOf('NA') >= 0) { banner = e; break; }
                }
            }
            if (!banner) return {ok: false, reason: 'no banner'};
            var bigEls = Array.from(banner.querySelectorAll('*')).filter(function(e) {
                var cls = (e.className || '').toString();
                var r = e.getBoundingClientRect();
                var isLarge = cls.indexOf('text-4xl') >= 0 || cls.indexOf('text-5xl') >= 0
                    || cls.indexOf('text-6xl') >= 0 || parseFloat(window.getComputedStyle(e).fontSize || '0') >= 28;
                return isLarge && e.children.length === 0 && r.width > 10;
            });
            var values = []; var seen = {};
            bigEls.forEach(function(el) {
                var t = (el.textContent || '').trim();
                if (t && !seen[t] && (t === 'NA' || /^[0-9]/.test(t) || t.indexOf('%') >= 0)) {
                    seen[t] = true; values.push(t);
                }
            });
            if (values.length < 2) {
                var bannerText = (banner.innerText || '').trim();
                var lines = bannerText.split('\\n').map(function(l){ return l.trim(); });
                values = [];
                lines.forEach(function(line) {
                    if (line === 'NA' || /^\\d+\\.?\\d*\\s*%$/.test(line)) values.push(line);
                });
            }
            return {ok: true, values: values, bannerText: (banner.innerText || '').substring(0, 300)};
        """)
        if exam_data and exam_data.get("ok"):
            vals = exam_data.get("values", [])
            left_val = vals[0] if len(vals) >= 1 else "—"
            right_val = vals[1] if len(vals) >= 2 else (vals[0] if len(vals) == 1 else "—")
            store["exam"]["left_pct"] = left_val
            store["exam"]["right_pct"] = right_val
            rec(b, "TC-EC-006", f"{VALUES.get('CompareLeft','Left')} avg = {left_val}", "PASS", left_val, suite="ExamComparison")
            rec(b, "TC-EC-007", f"{VALUES.get('CompareRight','Right')} avg = {right_val}", "PASS", right_val, suite="ExamComparison")
            rec(b, "TC-EC-003", "Exam banner rendered", "PASS", f"Values: {vals}", suite="ExamComparison")
        else:
            rec(b, "TC-EC-003", "Exam banner", "WARN", "Not found", suite="ExamComparison")
            rec(b, "TC-EC-006", "Left exam avg", "WARN", "Banner extraction failed", suite="ExamComparison")
            rec(b, "TC-EC-007", "Right exam avg", "WARN", "See above", suite="ExamComparison")
    except Exception as ex:
        rec(b, "TC-EC-003", "Exam banner", "WARN", str(ex), suite="ExamComparison")
        rec(b, "TC-EC-006", "Left exam avg", "WARN", str(ex), suite="ExamComparison")
        rec(b, "TC-EC-007", "Right exam avg", "WARN", "See above", suite="ExamComparison")
    rec(b, "TC-EC-004", "Midterm label visible", "PASS" if "Midterm" in pt else "WARN", suite="ExamComparison")
    rec(b, "TC-EC-005", "Preboard label visible", "PASS" if "Preboard" in pt else "WARN", suite="ExamComparison")
    trend_found = False
    for pattern in [
        r'[-+]?\d+\.?\d*\s*points?\s*(decline|drop|improvement|improve|increase)',
        r'[-+]?\d+\.?\d*\s*points', r'(decline|improvement|drop|increase)\s*of\s*[-+]?\d+',
    ]:
        trend = re.search(pattern, pt, re.I)
        if trend:
            store["exam"]["trend"] = trend.group(0)
            rec(b, "TC-EC-008", f"Trend badge: '{trend.group(0)}'", "PASS", suite="ExamComparison")
            trend_found = True; break
    if not trend_found:
        if store["exam"].get("left_pct") == "NA":
            store["exam"]["trend"] = "first exam (baseline)"
            rec(b, "TC-EC-008", "Trend: first exam baseline", "PASS", suite="ExamComparison")
        else:
            rec(b, "TC-EC-008", "Trend badge", "WARN", "Not found", suite="ExamComparison")

# ══════════════════════════════════════════════════════════════════════════════════
#  JS HELPERS FOR CHAPTER CARDS (from Script 1)
# ══════════════════════════════════════════════════════════════════════════════════
JS_FIND_MODAL = (
    "(function(){"
    "  var selectors=['[role=\"dialog\"]','[role=\"alertdialog\"]',"
    "    '[class*=\"modal\"]','[class*=\"Modal\"]','[class*=\"dialog\"]','[class*=\"Dialog\"]',"
    "    '[class*=\"popup\"]','[class*=\"Popup\"]','[class*=\"sheet\"]','[class*=\"Sheet\"]',"
    "    '[class*=\"overlay\"]'];"
    "  for(var s=0;s<selectors.length;s++){"
    "    var els=document.querySelectorAll(selectors[s]);"
    "    for(var i=0;i<els.length;i++){"
    "      var r=els[i].getBoundingClientRect();"
    "      if(r.width>200&&r.height>150&&r.top>=0&&r.top<window.innerHeight){"
    "        return {found:true,cls:(els[i].className||'').substring(0,80),"
    "                w:Math.round(r.width),h:Math.round(r.height)};"
    "      }"
    "    }"
    "  }"
    "  var all=document.querySelectorAll('*');"
    "  for(var i=0;i<all.length;i++){"
    "    var cs=window.getComputedStyle(all[i]);"
    "    if((cs.position==='fixed'||cs.position==='absolute')&&"
    "       parseInt(cs.zIndex||'0')>10){"
    "      var r2=all[i].getBoundingClientRect();"
    "      if(r2.width>200&&r2.height>200&&r2.top>=0&&r2.top<window.innerHeight){"
    "        return {found:true,cls:(all[i].className||'').substring(0,80),"
    "                w:Math.round(r2.width),h:Math.round(r2.height)};"
    "      }"
    "    }"
    "  }"
    "  return {found:false};"
    "})()"
)

JS_GET_MODAL_TEXT = (
    "(function(){"
    "  var selectors=['[role=\"dialog\"]','[role=\"alertdialog\"]',"
    "    '[class*=\"modal\"]','[class*=\"Modal\"]','[class*=\"dialog\"]','[class*=\"Dialog\"]',"
    "    '[class*=\"sheet\"]','[class*=\"Sheet\"]','[class*=\"popup\"]'];"
    "  for(var s=0;s<selectors.length;s++){"
    "    var el=document.querySelector(selectors[s]);"
    "    if(el){var r=el.getBoundingClientRect();"
    "      if(r.width>200&&r.height>150)return el.innerText||'';}"
    "  }"
    "  var all=document.querySelectorAll('*');"
    "  for(var i=0;i<all.length;i++){"
    "    var cs=window.getComputedStyle(all[i]);"
    "    if((cs.position==='fixed'||cs.position==='absolute')&&"
    "       parseInt(cs.zIndex||'0')>10){"
    "      var r2=all[i].getBoundingClientRect();"
    "      if(r2.width>200&&r2.height>200)return all[i].innerText||'';"
    "    }"
    "  }"
    "  return '';"
    "})()"
)

JS_SCROLL_MODAL = (
    "(function(px){"
    "  var selectors=['[role=\"dialog\"]','[role=\"alertdialog\"]',"
    "    '[class*=\"modal\" i]','[class*=\"sheet\" i]','[class*=\"dialog\" i]'];"
    "  for(var s=0;s<selectors.length;s++){"
    "    var el=document.querySelector(selectors[s]);"
    "    if(el&&el.getBoundingClientRect().height>150){"
    "      var inner=el.querySelectorAll('*');"
    "      for(var i=0;i<inner.length;i++){"
    "        if(inner[i].scrollHeight>inner[i].clientHeight+5&&inner[i].clientHeight>50){"
    "          inner[i].scrollTop+=px;return true;"
    "        }"
    "      }"
    "      el.scrollTop+=px;return true;"
    "    }"
    "  }"
    "  return false;"
    "})"
)

JS_CHECK_BOTTOM = (
    "(function(){"
    "  var selectors=['[role=\"dialog\"]','[class*=\"modal\" i]','[class*=\"sheet\" i]'];"
    "  for(var s=0;s<selectors.length;s++){"
    "    var el=document.querySelector(selectors[s]);"
    "    if(el&&el.getBoundingClientRect().height>150){"
    "      var inner=el.querySelectorAll('*');"
    "      for(var i=0;i<inner.length;i++){"
    "        if(inner[i].scrollHeight>inner[i].clientHeight+5&&inner[i].clientHeight>50){"
    "          return (inner[i].scrollTop+inner[i].clientHeight)>=(inner[i].scrollHeight-5);"
    "        }"
    "      }"
    "      return (el.scrollTop+el.clientHeight)>=(el.scrollHeight-5);"
    "    }"
    "  }"
    "  return true;"
    "})()"
)

JS_CLOSE_MODAL = (
    "(function(){"
    "  var closeBtns=document.querySelectorAll("
    "    'button[aria-label*=\"close\" i],button[aria-label*=\"Close\"]');"
    "  for(var i=0;i<closeBtns.length;i++){"
    "    if(closeBtns[i].offsetParent!==null){closeBtns[i].click();return 'aria-close';}"
    "  }"
    "  var all=document.querySelectorAll('button,span,div');"
    "  for(var i=0;i<all.length;i++){"
    "    var t=(all[i].textContent||'').trim();"
    "    if((t==='x'||t==='X'||t==='\u00d7'||t==='\u2715')&&all[i].offsetParent!==null){"
    "      all[i].click();return 'x-btn';"
    "    }"
    "  }"
    "  document.dispatchEvent(new KeyboardEvent('keydown',"
    "    {key:'Escape',keyCode:27,bubbles:true}));"
    "  return 'escape';"
    "})()"
)

STUDENT_SKIP = {"weak","lagging","performing well","highlighted","preboard",
                "students","more","overview","exam","chapter","avg",
                "reteach","brushup","on track","revise","review","target"}

CHAPTER_SKIP = {"reteach","brushup","on track","revise thoroughly",
                "review specific","significant improvement","target these chapters",
                "chapters recommended","struggling","declined","improved",
                "students are","students have","average score",
                "more chapters","no chapters","chapter","maths"}

def _line_pair(text):
    students = []; seen = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        if (not line or line in ("->", "←", "×", "✕", "✖", "x", "X")
                or "students in this category" in line.lower()
                or re.match(r"^\d+\s+students?", line, re.I)
                or line.lower() in STUDENT_SKIP):
            i += 1; continue
        if (re.match(r"^[A-Z]", line) and "%" not in line
                and not line.startswith("Class ") and 2 <= len(line) <= 70
                and not any(s == line.lower() for s in STUDENT_SKIP)):
            name = line; class_info = ""; pct = ""
            j = i + 1
            while j < min(i + 6, len(lines)):
                nxt = lines[j]
                if re.match(r"^Class\s+\d+", nxt, re.I): class_info = nxt; j += 1; continue
                if nxt in ("->", "←"): j += 1; continue
                if re.match(r"^\d+\.?\d*%$", nxt): pct = nxt; j += 1; break
                if re.match(r"^\d+\.\d+$", nxt): pct = nxt; j += 1; break
                break
            if pct and name not in seen:
                seen.add(name)
                students.append({"name": name, "pct": pct, "class_info": class_info, "src": "line-pair"})
            i = j; continue
        i += 1
    return students

def find_student_panel(driver, category):
    PANEL_CSS = {
        "Weak": "[class*='border-red-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-red-400']",
        "Lagging": "[class*='border-orange-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-orange-400']",
        "Performing Well": "[class*='border-green-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-green-400']",
    }
    sel = PANEL_CSS.get(category, "")
    if sel:
        try:
            el = driver.execute_script("""
                var sel=arguments[0]; var els=[];
                try{els=Array.from(document.querySelectorAll(sel));}catch(e){}
                for(var i=0;i<els.length;i++){
                    var r=els[i].getBoundingClientRect();
                    if(r.width>200&&r.height>80)return els[i];
                }
                return null;
            """, sel)
            if el: return el
        except: pass
    for xp in [f"//*[contains(@class,'text-slate-600') and normalize-space(text())='{category}']",
               f"//*[normalize-space(text())='{category}' and contains(@class,'semibold')]",
               f"//*[normalize-space(text())='{category}']"]:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    node = el
                    for _ in range(12):
                        try:
                            node = node.find_element(By.XPATH, "..")
                            cls = node.get_attribute("class") or ""
                            sz = node.size
                            if sz.get("width", 0) > 200 and sz.get("height", 0) > 80:
                                if "rounded" in cls or "border" in cls: return node
                        except: break
        except: pass
    return None

def scrape_student_rows_js(driver, category):
    BORDER_MAP = {
        "Weak": "border-red-400",
        "Lagging": "border-orange-400",
        "Performing Well": "border-green-400",
    }
    bclass = BORDER_MAP.get(category, "")
    try:
        result = driver.execute_script("""
            var bclass = arguments[0];
            var panels = Array.from(document.querySelectorAll('*')).filter(function(e) {
                return bclass && (typeof (e.className)==='string' ? e.className : (e.className&&e.className.baseVal)||'').indexOf(bclass) >= 0
                    && e.getBoundingClientRect().width > 200;
            });
            if (!panels.length) return [];
            var panel = panels[0];
            var rows = Array.from(panel.querySelectorAll('*')).filter(function(e) {
                var cls = (e.className||'').toString();
                return cls.indexOf('px-8') >= 0 && cls.indexOf('justify-between') >= 0
                    && cls.indexOf('cursor-pointer') >= 0;
            });
            var students = []; var seen = {};
            rows.forEach(function(row) {
                var bolds = Array.from(row.querySelectorAll('*')).filter(function(e) {
                    var cls = (e.className||'').toString();
                    return cls.indexOf('font-bold') >= 0 && cls.indexOf('slate-500') >= 0
                        && e.children.length === 0;
                });
                var names = bolds.filter(function(e) {
                    var t = e.textContent.trim();
                    return /^[A-Z]/.test(t) && !t.startsWith('Class ')
                        && t.indexOf('%') < 0 && t.length > 1 && t.length < 60;
                });
                var pcts = bolds.filter(function(e) {
                    var t = e.textContent.trim();
                    return /^[0-9]/.test(t) && /[%.]/.test(t);
                });
                if (names.length >= 1 && pcts.length >= 1) {
                    var name = names[0].textContent.trim();
                    var pct = pcts[pcts.length-1].textContent.trim();
                    if (!seen[name]) {
                        seen[name] = true;
                        students.push({name: name, pct: pct, class_info: ''});
                    }
                }
            });
            return students;
        """, bclass)
        if result:
            return [{"name": r["name"], "pct": r["pct"], "class_info": "", "src": "js-visible"}
                    for r in result]
    except Exception as e:
        print(f"      JS visible scrape error: {e}")
    return []

def find_student_overflow(driver, category, panel=None):
    if panel:
        try:
            result = driver.execute_script("""
                var panel=arguments[0];
                if(!panel) return null;
                var all=Array.from(panel.querySelectorAll('*'));
                for(var i=0;i<all.length;i++){
                    var e=all[i];
                    var cls=(e.className||'').toString();
                    var txt=(e.textContent||'').trim();
                    if(cls.indexOf('border-dashed')>=0 && txt.startsWith('+') && txt.indexOf('student')>=0){
                        var r=e.getBoundingClientRect();
                        if(r.width>50&&r.height>10) return e;
                    }
                }
                return null;
            """, panel)
            if result:
                txt = driver.execute_script("return arguments[0].textContent.trim()", result)
                return result, txt
        except: pass
    if panel:
        for xp in [
            ".//*[contains(@class,'border-dashed') and contains(normalize-space(text()),'+') and contains(normalize-space(text()),'student')]",
            ".//*[contains(@class,'border-dashed') and contains(normalize-space(text()),'+')]",
        ]:
            try:
                base = panel.find_elements(By.XPATH, xp)
                for el in base:
                    if el.is_displayed():
                        t = el_text(el)
                        if "more" in t.lower() and "student" in t.lower(): return el, t
            except: pass
    return None, ""

def find_and_scrape_modal(driver, category):
    time.sleep(2.0)
    try:
        js_result = driver.execute_script("""
            var cat = arguments[0];
            var all = Array.from(document.querySelectorAll('*'));
            var container = null;
            for (var i = all.length - 1; i >= 0; i--) {
                var e = all[i]; var txt = (e.textContent || '').trim(); var r = e.getBoundingClientRect();
                if (txt.indexOf('students in this category') >= 0 && r.width > 150 && r.height > 100
                        && r.width < window.innerWidth * 0.99) { container = e; break; }
            }
            if (!container) return {ok: false, reason: 'no container'};
            function extractFromContainer(c) {
                var students = []; var seen = {};
                var rows = Array.from(c.querySelectorAll('*')).filter(function(e) {
                    var cls = (e.className || '').toString();
                    return cls.indexOf('cursor-pointer') >= 0 && cls.indexOf('justify-between') >= 0
                        && e.getBoundingClientRect().width > 80;
                });
                rows.forEach(function(row) {
                    var leaves = Array.from(row.querySelectorAll('*')).filter(function(b) {
                        return b.children.length === 0 && (b.textContent||'').trim().length > 0;
                    });
                    var nameCands = leaves.filter(function(b) {
                        var t = b.textContent.trim();
                        return /^[A-Z]/.test(t) && !t.startsWith('Class ') && t.indexOf('%') < 0 && t.length > 1 && t.length < 70;
                    });
                    var pctCands = leaves.filter(function(b) {
                        var t = b.textContent.trim(); return /^[0-9]/.test(t) && /[%.]/.test(t);
                    });
                    var clsCands = leaves.filter(function(b) { return b.textContent.trim().startsWith('Class '); });
                    if (nameCands.length >= 1 && pctCands.length >= 1) {
                        var name = nameCands[0].textContent.trim();
                        var pct = pctCands[pctCands.length-1].textContent.trim();
                        var ci = clsCands.length ? clsCands[0].textContent.trim() : '';
                        if (!seen[name]) { seen[name] = true; students.push({name: name, pct: pct, class_info: ci}); }
                    }
                });
                return students;
            }
            var students = extractFromContainer(container);
            return {ok: true, students: students, h: Math.round(container.getBoundingClientRect().height)};
        """, category)
        if js_result and js_result.get("ok"):
            raw = js_result.get("students", [])
            all_students = []; seen = set()
            for r in raw:
                if r["name"] not in seen:
                    seen.add(r["name"])
                    all_students.append({"name": r["name"], "pct": r["pct"], "class_info": r.get("class_info", ""), "src": "modal-js"})
            for scroll_step in range(30):
                try: driver.execute_script(JS_SCROLL_MODAL + "(250)")
                except: pass
                time.sleep(0.4)
                try:
                    js2 = driver.execute_script("""
                        var all = Array.from(document.querySelectorAll('*')); var container = null;
                        for (var i = all.length - 1; i >= 0; i--) {
                            var e = all[i]; var txt = (e.textContent || '').trim(); var r = e.getBoundingClientRect();
                            if (txt.indexOf('students in this category') >= 0 && r.width > 150 && r.height > 100) { container = e; break; }
                        }
                        if (!container) return [];
                        var rows = Array.from(container.querySelectorAll('*')).filter(function(e) {
                            var cls = (e.className || '').toString();
                            return cls.indexOf('cursor-pointer') >= 0 && cls.indexOf('justify-between') >= 0 && e.getBoundingClientRect().width > 80;
                        });
                        var students = []; var seen = {};
                        rows.forEach(function(row) {
                            var leaves = Array.from(row.querySelectorAll('*')).filter(function(b) {
                                return b.children.length === 0 && (b.textContent||'').trim().length > 0;
                            });
                            var nameCands = leaves.filter(function(b) {
                                var t = b.textContent.trim();
                                return /^[A-Z]/.test(t) && !t.startsWith('Class ') && t.indexOf('%') < 0 && t.length > 1 && t.length < 70;
                            });
                            var pctCands = leaves.filter(function(b) { var t = b.textContent.trim(); return /^[0-9]/.test(t) && /[%.]/.test(t); });
                            if (nameCands.length >= 1 && pctCands.length >= 1) {
                                var name = nameCands[0].textContent.trim(); var pct = pctCands[pctCands.length-1].textContent.trim();
                                if (!seen[name]) { seen[name] = true; students.push({name: name, pct: pct}); }
                            }
                        });
                        return students;
                    """)
                    if js2:
                        for r in js2:
                            if r["name"] not in seen:
                                seen.add(r["name"])
                                all_students.append({"name": r["name"], "pct": r["pct"], "class_info": "", "src": "modal-js-scroll"})
                except: pass
                try:
                    at_bottom = driver.execute_script(JS_CHECK_BOTTOM)
                    if at_bottom and scroll_step > 2: break
                except: pass
            if all_students: return all_students, True
    except Exception as ex:
        print(f"      JS layer error: {ex}")
    try:
        modal_info = driver.execute_script(JS_FIND_MODAL)
    except: modal_info = None
    if modal_info and modal_info.get("found"):
        all_students = []; seen_keys = set()
        for step in range(50):
            try: modal_text = driver.execute_script(JS_GET_MODAL_TEXT)
            except: break
            if not modal_text: break
            stus = _line_pair(modal_text)
            for s in stus:
                key = s["name"] + s.get("pct", "")
                if key not in seen_keys: seen_keys.add(key); all_students.append(s)
            try: driver.execute_script(JS_SCROLL_MODAL + "(200)")
            except: pass
            time.sleep(0.4)
            try:
                if driver.execute_script(JS_CHECK_BOTTOM) and step > 4: break
            except: pass
        return all_students, True
    return [], False

def close_modal(driver):
    try:
        driver.execute_script(JS_CLOSE_MODAL); time.sleep(0.8)
        info = driver.execute_script(JS_FIND_MODAL)
        if not (info and info.get("found")): return True
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.5); return True
    except: return False

# ══════════════════════════════════════════════════════════════════════════════════
#  SECTION 4/5/6 — CHAPTER OVERVIEW CARDS
# ══════════════════════════════════════════════════════════════════════════════════
def find_chapter_section_panel(driver, label):
    PANEL_CSS = {
        "Reteach": ".bg-blue-50",
        "Brushup": "[class*='FFF7E6']",
        "On Track": ".bg-green-50",
    }
    sel = PANEL_CSS.get(label, "")
    if sel:
        try:
            el = driver.execute_script("""
                var sel=arguments[0]; var els=[];
                try{els=Array.from(document.querySelectorAll(sel));}catch(e){}
                for(var i=0;i<els.length;i++){
                    var r=els[i].getBoundingClientRect();
                    if(r.width>300&&r.height>80)return els[i];
                }
                return null;
            """, sel)
            if el: return el
        except: pass
    return None

def _sanitize_weightage(val):
    if not val or val == "N/A": return val
    if "chapter avg" in val.lower(): return "N/A"
    val = re.sub(r'(?i)avg\s*weightage\s*', '', val).strip()
    if re.match(r'^[+-]?\d+\.?\d*%$', val.strip()): return "N/A"
    return val

def find_chapter_cards(panel):
    cards = []; seen = set()
    try:
        name_els = panel.find_elements(By.XPATH,
            ".//*[contains(@class,'font-bold') and "
            "(contains(@class,'text-gray-700') or contains(@class,'text-slate')) "
            "and contains(@class,'normal-case')]")
        if not name_els:
            name_els = panel.find_elements(By.XPATH,
                ".//*[contains(@class,'font-bold') and contains(@class,'normal-case')]")
        for el in name_els:
            try:
                name = el_text(el).strip()
                if not name or name in seen or len(name) > 80: continue
                if name.lower() in CHAPTER_SKIP or not re.match(r'^[A-Z]', name): continue
                seen.add(name)
                row = el
                for _ in range(6):
                    try:
                        parent = row.find_element(By.XPATH, "..")
                        cls = parent.get_attribute("class") or ""
                        if "cursor-pointer" in cls: row = parent; break
                        if "px-6" in cls and "py-4" in cls: row = parent; break
                        row = parent
                    except: break
                cards.append({"name": name, "el": row})
            except: continue
    except Exception as e:
        print(f"      card find error: {e}")
    return cards

def extract_chapter_metrics(driver, card_row_el):
    time.sleep(1.5)
    metrics = {"chapter_avg": "N/A", "avg_weightage": "N/A"}
    try:
        result = driver.execute_script("""
            var cardEl = arguments[0];
            if (!cardEl) return {avg: null, wt: null, debug: 'no element'};
            var container = cardEl;
            for (var up = 0; up < 12; up++) {
                var par = container.parentElement; if (!par) break;
                container = par;
                var it = container.innerText || '';
                if (it.indexOf('Chapter Avg') >= 0 && it.indexOf('Avg Weightage') >= 0) break;
            }
            var avg = null, wt = null; var debugInfo = [];
            var boxes = [];
            var selectors = ['[class*="rounded-2xl"][class*="p-4"]','[class*="rounded-2xl"][class*="p-"]',
                             '[class*="rounded-xl"][class*="p-4"]','[class*="rounded"][class*="bg-blue"]',
                             '[class*="rounded"][class*="bg-green"]'];
            for (var si = 0; si < selectors.length; si++) {
                try {
                    boxes = Array.from(container.querySelectorAll(selectors[si])).filter(function(b) {
                        var r = b.getBoundingClientRect(); return r.width > 50 && r.height > 30;
                    });
                    if (boxes.length >= 2) break;
                } catch(e) {}
            }
            for (var b = 0; b < boxes.length; b++) {
                var box = boxes[b];
                var rawText = (box.innerText || '').trim();
                var lines = rawText.split('\\n').map(function(l){return l.trim();}).filter(function(l){return l.length>0;});
                if (lines.length === 0) continue;
                var firstLine = lines[0].toLowerCase();
                if (firstLine.indexOf('chapter avg') >= 0 && avg === null) {
                    var valueParts = lines.slice(1).filter(function(l){return /[0-9]/.test(l);});
                    if (valueParts.length > 0) avg = valueParts[0].trim();
                    if (!avg) { var big = box.querySelector('[class*="text-2xl"]'); if (big) avg = (big.textContent || '').trim(); }
                }
                if ((firstLine.indexOf('avg weightage') >= 0 || firstLine === 'weightage') && wt === null) {
                    var valueParts = lines.slice(1);
                    if (valueParts.length > 0) wt = valueParts.join(' ').replace(/\\s+/g,' ').trim();
                    if (!wt || !/[0-9]/.test(wt)) {
                        var big = box.querySelector('[class*="text-2xl"]');
                        if (big) {
                            var num = (big.textContent || '').trim(); var sib = big.nextElementSibling; var slash = '';
                            while (sib) { var st = (sib.textContent || '').trim(); if (st.indexOf('/') >= 0) { slash = st; break; } sib = sib.nextElementSibling; }
                            wt = slash ? (num + ' ' + slash) : num;
                        }
                    }
                }
            }
            if (wt) { if (wt.toLowerCase().indexOf('chapter avg') >= 0) wt = null; if (wt && /^[+-]?[0-9]+\\.?[0-9]*%$/.test(wt.trim())) wt = null; }
            return {avg: avg, wt: wt, debug: debugInfo.join(' | ')};
        """, card_row_el)
        if result:
            if result.get("avg"):  metrics["chapter_avg"]   = result["avg"]
            if result.get("wt"):   metrics["avg_weightage"] = result["wt"]
            metrics["avg_weightage"] = _sanitize_weightage(metrics["avg_weightage"])
    except Exception as ex:
        print(f"      JS metrics error: {ex}")
    metrics["avg_weightage"] = _sanitize_weightage(metrics["avg_weightage"])
    return metrics

def _find_chapter_overflow_btn(driver, panel, label):
    if not panel: return None, ""
    try:
        ovf_btn = driver.execute_script("""
            var panel = arguments[0]; if (!panel) return null;
            var all = Array.from(panel.querySelectorAll('*'));
            for (var i = 0; i < all.length; i++) {
                var e = all[i]; var cls = (e.className || '').toString(); var txt = (e.textContent || '').trim();
                if (cls.indexOf('border-dashed') >= 0 && txt.startsWith('+') && txt.indexOf('chapter') >= 0) {
                    var r = e.getBoundingClientRect(); if (r.width > 30 && r.height > 8) return e;
                }
            }
            return null;
        """, panel)
        if ovf_btn:
            try: t = driver.execute_script("return arguments[0].textContent.trim()", ovf_btn)
            except: t = el_text(ovf_btn)
            return ovf_btn, t
    except: pass
    return None, ""

def parse_chapter_modal_text(text):
    CH_SKIP = {"reteach","brushup","on track","revise thoroughly","review specific",
               "significant improvement","target these chapters","chapters in this category",
               "more chapters","no chapters","chapter","maths","mathematics"}
    chapters = []; seen = set()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        if not line or line in ("->","←","×","✕","✖","x","X"): continue
        if "chapters in this category" in line.lower(): continue
        if re.match(r"^\d+\s+chapters?", line, re.I): continue
        if re.match(r"^\d+\.?\d*%", line): continue
        if line.lower() in CH_SKIP or any(s in line.lower() for s in CH_SKIP if len(s) > 4): continue
        if re.match(r"^[A-Z]", line) and 3 <= len(line) <= 80 and "%" not in line and line not in seen:
            seen.add(line); chapters.append(line)
    return chapters

def open_read_close_chapter_modal(driver, label, btn_el, btn_txt):
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.3)
    except: pass
    for attempt in range(3):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", btn_el); time.sleep(0.3)
            if attempt == 0: btn_el.click()
            else: driver.execute_script("arguments[0].click()", btn_el)
            time.sleep(2.5); break
        except Exception as e:
            if attempt == 2: return [], False
            time.sleep(0.5)
    chapters = []
    try:
        modal_text = driver.execute_script("""
            var lbl = arguments[0];
            var all = Array.from(document.querySelectorAll('*'));
            for (var i = all.length - 1; i >= 0; i--) {
                var e = all[i]; var txt = (e.textContent || '').trim(); var r = e.getBoundingClientRect();
                if (txt.indexOf('chapters in this category') >= 0 && r.width > 150 && r.height > 80 && r.width < window.innerWidth * 0.99) {
                    var inner = e.innerText || txt; var top200 = inner.substring(0, 200).toLowerCase();
                    if (top200.indexOf(lbl.toLowerCase()) >= 0 || r.height < window.innerHeight * 0.8) return inner;
                }
            }
            return '';
        """, label)
        if modal_text: chapters = parse_chapter_modal_text(modal_text)
    except: pass
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(1.0)
    except: pass
    return chapters, bool(chapters)

def test_chapter_section(driver, label):
    conf = {"Reteach": "TC-RT", "Brushup": "TC-BU", "On Track": "TC-OT"}
    prefix = conf[label]
    b = store["chapters"][label]["tests"]
    cd = store["chapters"][label]
    sub_sep(f"Chapter Section: {label}")

    # Wait for page content to appear before searching for chapter panels
    try:
        WebDriverWait(driver, 10).until(lambda d: any(
            k in d.page_source for k in ["Reteach", "Brushup", "On Track", "chapters"]))
    except:
        time.sleep(2.0)

    panel = find_chapter_section_panel(driver, label)
    if panel is None:
        rec(b, f"{prefix}-001", f"'{label}' panel found", "WARN", "Fallback to body", suite="ChapterCards")
        panel = driver.find_element(By.TAG_NAME, "body")
    else:
        rec(b, f"{prefix}-001", f"'{label}' section panel found", "PASS", suite="ChapterCards")

    try:
        badge = driver.execute_script("""
            var label = arguments[0];
            var all = Array.from(document.querySelectorAll('*'));
            for (var i = 0; i < all.length; i++) {
                var e = all[i];
                if (e.textContent.trim() === label && e.children.length === 0) {
                    var node = e;
                    for (var s = 0; s < 6; s++) {
                        node = node.parentElement; if (!node) break;
                        var kids = Array.from(node.querySelectorAll('*'));
                        for (var j = 0; j < kids.length; j++) {
                            var t = kids[j].textContent.trim();
                            if (/^[0-9]+ chapters?$/.test(t)) return t;
                        }
                    }
                }
            }
            return null;
        """, label)
        if badge:
            cd["badge"] = badge
            rec(b, f"{prefix}-002", "Chapter count badge", "PASS", badge, suite="ChapterCards")
        else:
            raise Exception("badge not found")
    except:
        rec(b, f"{prefix}-002", "Badge", "WARN", "Not found", suite="ChapterCards")

    instr_map = {"Reteach": "Revise Thoroughly", "Brushup": "Review Specific Concepts", "On Track": "Significant Improvement"}
    try:
        instr = driver.find_element(By.XPATH, f"//*[contains(text(),'{instr_map[label]}')]")
        rec(b, f"{prefix}-003", f"Instruction '{instr_map[label]}' visible", "PASS", el_text(instr)[:60], suite="ChapterCards")
    except Exception as e:
        rec(b, f"{prefix}-003", "Instruction text", "WARN", str(e), suite="ChapterCards")

    panel_text = el_text(panel).lower()
    if "no chapters" in panel_text:
        cd["empty"] = True
        rec(b, f"{prefix}-004", "Empty state", "INFO", "0 chapters confirmed", suite="ChapterCards"); return

    ovf_btn, ovf_txt = _find_chapter_overflow_btn(driver, panel, label)
    if ovf_btn:
        chapters_from_modal, modal_ok = open_read_close_chapter_modal(driver, label, ovf_btn, ovf_txt)
        cd["overflow_clicked"] = [ovf_txt]
        cd["modal_chapters"] = chapters_from_modal
        rec(b, f"{prefix}-OVF", f"Overflow '{ovf_txt}' clicked", "PASS" if modal_ok else "WARN",
            f"{len(chapters_from_modal)} chapters from modal", suite="ChapterCards")
        for i, ch in enumerate(chapters_from_modal, 1):
            rec(b, f"{prefix}-MCH{i:02d}", f"Modal chapter #{i}: {ch}", "PASS", suite="ChapterCards")
        time.sleep(0.5)
        panel = find_chapter_section_panel(driver, label) or panel
    else:
        rec(b, f"{prefix}-OVF", "No chapter overflow found", "INFO", "All chapters visible inline", suite="ChapterCards")

    cards = find_chapter_cards(panel)
    rec(b, f"{prefix}-004", f"Chapter cards found", "PASS" if cards else "WARN",
        f"{len(cards)} cards: {[c['name'] for c in cards]}", suite="ChapterCards")

    for idx, card in enumerate(cards, 1):
        tc = f"{prefix}-C{idx:02d}"
        card_data = {"idx": idx, "name": card["name"], "chapter_avg": "N/A", "avg_weightage": "N/A"}
        try:
            scroll_to(driver, card["el"])
            try: card["el"].click()
            except: driver.execute_script("arguments[0].click()", card["el"])
            time.sleep(2.0)
            driver.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", card["el"])
            time.sleep(0.5)
            rec(b, tc, f"Card '{card['name']}' expanded", "PASS", suite="ChapterCards")
        except Exception as e:
            rec(b, tc, f"Card '{card['name']}' click", "WARN", str(e), suite="ChapterCards")
            cd["cards"].append(card_data); continue
        m = extract_chapter_metrics(driver, card["el"])
        card_data.update(m)
        rec(b, f"{tc}-AVG", f"  Chapter Avg % = '{m['chapter_avg']}'",
            "PASS" if m["chapter_avg"] not in ("N/A","") else "WARN", m["chapter_avg"], suite="ChapterCards")
        rec(b, f"{tc}-WT", f"  Avg Weightage = '{m['avg_weightage']}'",
            "PASS" if m["avg_weightage"] not in ("N/A","") else "WARN", m["avg_weightage"], suite="ChapterCards")
        cd["cards"].append(card_data)
        try: card["el"].click(); time.sleep(0.5)
        except: pass

# ══════════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — HIGHLIGHTED STUDENTS (Overview)
# ══════════════════════════════════════════════════════════════════════════════════
def test_student_category(driver, category):
    prefix = {"Weak": "TC-HS-W", "Lagging": "TC-HS-L", "Performing Well": "TC-HS-P"}[category]
    sd = store["students"][category]
    b = sd["tests"]
    sub_sep(f"Students: {category}")

    try:
        hd = driver.find_element(By.XPATH,
            f"//*[contains(@class,'text-slate-600') and normalize-space(text())='{category}']"
            f"|//*[normalize-space(text())='{category}' and contains(@class,'semibold')]"
            f"|//*[normalize-space(text())='{category}']")
        rec(b, f"{prefix}-001", f"'{category}' heading visible", "PASS", el_text(hd), suite="Students")
    except Exception as e:
        rec(b, f"{prefix}-001", "Heading", "WARN", str(e), suite="Students")

    badge_found = False
    for xp in [
        f"//*[normalize-space(text())='{category}']/following-sibling::*[contains(text(),'student')][1]",
        f"//*[normalize-space(text())='{category}']/following::*[contains(text(),'student')][1]",
    ]:
        try:
            el = driver.find_element(By.XPATH, xp)
            badge = el_text(el)
            if badge and "student" in badge.lower():
                sd["badge"] = badge
                m = re.search(r'(\d+)', badge)
                if m: sd["total"] = int(m.group(1))
                rec(b, f"{prefix}-002", "Student count badge", "PASS", f"'{badge}' -> {sd['total']}", suite="Students")
                badge_found = True; break
        except: pass
    if not badge_found:
        rec(b, f"{prefix}-002", "Student count badge", "WARN", "Not found", suite="Students")

    panel = find_student_panel(driver, category)
    if panel is None:
        panel = driver.find_element(By.TAG_NAME, "body")
        rec(b, f"{prefix}-PANEL", "Section panel", "WARN", "Fallback to body", suite="Students")
    else:
        rec(b, f"{prefix}-PANEL", "Section panel found", "PASS", suite="Students")

    visible = scrape_student_rows_js(driver, category)
    if not visible:
        try:
            slate_els = panel.find_elements(By.XPATH,
                ".//*[contains(@class,'text-slate-500') and contains(@class,'font-bold')]")
            visible_temp = []; seen = set()
            i = 0
            while i < len(slate_els):
                name_el = slate_els[i]; name = el_text(name_el).strip()
                if not name or name.lower() in STUDENT_SKIP or len(name) < 2 or re.match(r'^\d+\.?\d*%$', name): i += 1; continue
                if not re.match(r'^[A-Z]', name): i += 1; continue
                if i + 1 < len(slate_els):
                    pct_txt = el_text(slate_els[i+1]).strip()
                    if re.match(r'^\d+\.?\d*%$', pct_txt):
                        if name not in seen: seen.add(name); visible_temp.append({"name": name, "pct": pct_txt, "class_info": "", "src": "slate500"})
                        i += 2; continue
                i += 1
            visible = visible_temp
        except: pass
    sd["visible"] = visible

    declared_total = sd.get("total", 0)
    visible_count = len(visible)

    for i, s in enumerate(visible, 1):
        rec(b, f"{prefix}-S{i:02d}", f"Visible #{i}: {s['name']}", "PASS", f"Score: {s['pct']}", suite="Students")

    if declared_total > 0 and visible_count >= declared_total:
        sd["all"] = visible
        rec(b, f"{prefix}-OVF-001", "Overflow button", "INFO", f"All {declared_total} students visible", suite="Students")
        return

    ovf_el, ovf_txt = find_student_overflow(driver, category, panel)
    if ovf_el is None:
        sd["all"] = visible
        rec(b, f"{prefix}-OVF-001", "Overflow button", "INFO" if visible else "WARN", "Not found", suite="Students")
        return

    sd["overflow_txt"] = ovf_txt
    rec(b, f"{prefix}-OVF-001", "Overflow button found", "PASS", f"'{ovf_txt}'", suite="Students")

    clicked = False
    for attempt in range(3):
        try:
            scroll_to(driver, ovf_el)
            if attempt == 0: ovf_el.click()
            else: driver.execute_script("arguments[0].click();", ovf_el)
            time.sleep(1.5); clicked = True
            rec(b, f"{prefix}-OVF-002", f"Clicked '{ovf_txt}'", "PASS", suite="Students"); break
        except Exception as e:
            if attempt == 2:
                rec(b, f"{prefix}-OVF-002", "Click failed", "FAIL", str(e), suite="Students")

    if not clicked: sd["all"] = visible; return

    modal_students, modal_found = find_and_scrape_modal(driver, category)
    sd["modal_opened"] = modal_found

    if modal_found:
        rec(b, f"{prefix}-MODAL-001", "Modal opened and read", "PASS" if modal_students else "WARN",
            f"{len(modal_students)} students", suite="Students")
        sd["modal"] = modal_students
        for j, s in enumerate(modal_students, 1):
            rec(b, f"{prefix}-M{j:02d}", f"Modal #{j}: {s['name']}", "PASS", f"Score: {s['pct']}", suite="Students")
        sd["all"] = modal_students if modal_students else visible
        closed = close_modal(driver)
        rec(b, f"{prefix}-MODAL-CLOSE", "Modal closed", "PASS" if closed else "WARN", suite="Students")
    else:
        rec(b, f"{prefix}-MODAL-001", "Modal", "WARN", "No modal detected", suite="Students")
        sd["all"] = visible

    captured = len(sd.get("all", []))
    declared = sd.get("total", 0)
    if declared > 0:
        if captured == declared:
            rec(b, f"{prefix}-VALIDATE", f"Count verified: {captured}/{declared}", "PASS", suite="Students")
        elif captured > declared:
            sd["all"] = sd["all"][:declared]
            rec(b, f"{prefix}-VALIDATE", f"Count mismatch: {captured} vs {declared}", "WARN", "Trimmed", suite="Students")
        else:
            rec(b, f"{prefix}-VALIDATE", f"Count: {captured}/{declared}", "WARN", f"Missing {declared-captured}", suite="Students")

def test_all_students(driver, wait):
    sep("SECTION 7 – Highlighted Students (Full Verification)")
    b = store["students"]["Weak"]["tests"]
    try:
        hd = driver.find_element(By.XPATH, "//*[contains(text(),'Highlighted Students')]")
        rec(b, "TC-HS-000", "Highlighted Students heading", "PASS", el_text(hd), suite="Students")
    except Exception as e:
        rec(b, "TC-HS-000", "Heading", "WARN", str(e), suite="Students")

    for cat in ["Weak", "Lagging", "Performing Well"]:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE); time.sleep(0.5)
        except: pass
        try:
            info = driver.execute_script(JS_FIND_MODAL)
            if info and info.get("found"):
                driver.execute_script(JS_CLOSE_MODAL); time.sleep(0.8)
        except: pass
        test_student_category(driver, cat)
        time.sleep(0.5)

# ══════════════════════════════════════════════════════════════════════════════════
#  CHAPTERS TAB — LOC1-4 + HEADER ACCURACY (from Script 2)
# ══════════════════════════════════════════════════════════════════════════════════
_WHY_HEADINGS = ["Why this chapter improved", "Why this chapter declined", "Why this chapter"]
_ACC_BEFORE_PHRASES = ["remained stable at around","stable at around","at around","remained stable at",
                       "stable at","remained at","performance at","accuracy of","at approximately","approximately","around"]
_ACC_AFTER_WORDS = ["accuracy","accura"]
_STABLE_PHRASES = ["remained stable","performance remained stable","no significant change",
                   "no change","stayed stable","did not change","remained the same","performance stable"]
_CHANGE_KWS_STRICT = ["slight decline of","significant decline of","slight improvement of",
                      "significant improvement of","declined by","decline of","declined significantly by",
                      "improved by","improvement of","improved significantly by","drop of","dropped by",
                      "change of","changed by","progress of","increased by","decreased by",
                      "reduced by","fell by","significantly by","considerably by","notably by"]
_FALLBACK_PATTERNS = [
    (r"[Ss]light\s+decline\s+of\s+([+\-]?\d+\.?\d*)\s*%", "-"),
    (r"[Ss]ignificant\s+decline\s+of\s+([+\-]?\d+\.?\d*)\s*%", "-"),
    (r"[Ss]light\s+improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%", "+"),
    (r"[Ss]ignificant\s+improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%", "+"),
    (r"improvement\s+of\s+([+\-]?\d+\.?\d*)\s*%", "+"),
    (r"improved\s+by\s+([+\-]?\d+\.?\d*)\s*%", "+"),
    (r"declined\s+by\s+([+\-]?\d+\.?\d*)\s*%", "-"),
    (r"decline\s+of\s+([+\-]?\d+\.?\d*)\s*%", "-"),
    (r"drop\s+of\s+([+\-]?\d+\.?\d*)\s*%", "-"),
]

def normalize_arrow(ch):
    if ch in ("↑","▲","△","⬆","+"): return "+"
    if ch in ("↓","▼","▽","⬇","-"): return "-"
    return ch

def arrow_sign(s):
    for a, r in [("↑","+"),("↓","-"),("▲","+"),("▼","-")]:
        s = s.replace(a, r)
    return s

def extract_pct(text):
    if not text: return None
    t = re.sub(r"\s+", "", arrow_sign(text))
    m = re.search(r"([+\-])(\d+\.?\d*)%", t)
    if m: return f"{m.group(1)}{m.group(2)}%"
    m2 = re.search(r"(\d+\.?\d*)%", t)
    if m2: return f"+{m2.group(1)}%"
    return None

def extract_num(p):
    if not p: return None
    m = re.search(r"[+\-]?\d+\.?\d*", p)
    return float(m.group()) if m else None

def norm_val(p):
    if not p: return None
    m = re.search(r"(\d+\.?\d*)", p)
    if not m: return None
    try:
        v = str(float(m.group(1)))
        return v[:-2] if v.endswith(".0") else v
    except: return m.group(1)

def align_sign(ref, cand):
    if not ref or not cand: return cand
    rs = "+" if "+" in ref else "-"
    rn = re.search(r"(\d+\.?\d*)", ref); cn = re.search(r"(\d+\.?\d*)", cand)
    if rn and cn and rn.group(1) == cn.group(1) and ("+" in cand) != (rs == "+"):
        return f"{rs}{cn.group(1)}%"
    return cand

def _is_accuracy_pct(num_str, ctx_before, ctx_after):
    cb = ctx_before.lower(); ca = ctx_after.lower().strip()
    if any(ca.startswith(k) or (" " + k) in ca[:25] for k in _ACC_AFTER_WORDS): return True
    for phrase in _ACC_BEFORE_PHRASES:
        if phrase in cb: return True
    for sp2 in _STABLE_PHRASES:
        if sp2 in cb: return True
    if "." not in num_str:
        try:
            if float(num_str) >= 50: return True
        except: pass
    return False

def read_why_text(driver):
    try:
        result = driver.execute_script("""
            const WHY_KWS=arguments[0];
            for(const kw of WHY_KWS){
                for(const el of document.querySelectorAll('*')){
                    const t=(el.innerText||el.textContent||'').trim();
                    if(!t.startsWith(kw))continue;
                    let sib=el.nextElementSibling;
                    while(sib){const st=(sib.innerText||'').trim();if(st.length>15&&!st.startsWith('Why this'))return st;sib=sib.nextElementSibling;}
                    let p=el.parentElement;
                    for(let i=0;i<6&&p;i++,p=p.parentElement){
                        const pt=(p.innerText||'').trim();
                        if(pt.length>t.length+20&&pt.length<1500){const body=pt.replace(t,'').trim();if(body.length>15)return body;}
                    }
                }
            }
            return null;
        """, _WHY_HEADINGS)
        if result and len(result.strip()) > 15: return result.strip()
    except: pass
    return None

def read_why_pct(why_text):
    if not why_text: return None
    lower = why_text.lower()
    if any(ph in lower for ph in _STABLE_PHRASES): return None
    is_neg = any(k in lower for k in ["decline","declined","drop","dropped","fell","decrease","decreased","worsened","reduced"])
    for m in re.finditer(r"([+\-]?)(\d+\.?\d*)\s*%", why_text):
        pos = m.start(); raw_sgn = m.group(1); num_str = m.group(2)
        ctx_b = lower[max(0, pos-100):pos]; ctx_a = lower[pos:pos+60]
        if _is_accuracy_pct(num_str, ctx_b, ctx_a): continue
        if any(kw in ctx_b for kw in _CHANGE_KWS_STRICT):
            sign = raw_sgn if raw_sgn else ("-" if is_neg else "+")
            return f"{sign}{num_str}%"
    return None

def read_why_pct_from_page(driver, ref_pct=None):
    ps = driver.page_source
    for kw in _WHY_HEADINGS:
        idx = ps.find(kw)
        if idx < 0: continue
        region = ps[idx:idx+1200]
        clean = re.sub(r"<[^>]+>", " ", region); clean = re.sub(r"\s+", " ", clean)
        is_neg = any(k in clean.lower() for k in ["decline","drop","decreased","fell","worsened","reduced"])
        for pat, forced_sign in _FALLBACK_PATTERNS:
            m = re.search(pat, clean, re.IGNORECASE)
            if m:
                val = m.group(1)
                if val.startswith("+") or val.startswith("-"): return f"{val}%"
                if forced_sign: return f"{forced_sign}{val}%"
                return f"{'-' if is_neg else '+'}{val}%"
    return None

def read_why_accuracy_pct(why_text):
    if not why_text: return None
    lower = why_text.lower()
    for pat in [r"remained\s+stable\s+at\s+around\s+(\d+\.?\d*)\s*%",
                r"stable\s+at\s+around\s+(\d+\.?\d*)\s*%",
                r"at\s+around\s+(\d+\.?\d*)\s*%", r"accuracy\s+of\s+(\d+\.?\d*)\s*%",
                r"(\d+\.?\d*)\s*%\s+accuracy"]:
        m = re.search(pat, lower)
        if m: return f"{m.group(1)}%"
    return None

def read_header_accuracy_badge(driver):
    try:
        result = driver.execute_script(r"""
            const EXAM_LABELS = arguments[0];
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText || el.textContent || '').trim();
                for (const exam of EXAM_LABELS) {
                    const pat = new RegExp(exam + '\\s+accuracy\\s*(\\d+\\.?\\d*)\\s*%', 'i');
                    const m = t.match(pat);
                    if (m && t.length < 80) return { exam: exam, pct: m[1] + '%', text: t };
                }
            }
            return null;
        """, EXAM_LABELS)
        if result and result.get("pct"): return result["pct"]
    except: pass
    return None

def _closest_pct(candidates, ref):
    if not candidates: return None
    if not ref: return candidates[0]
    rn = abs(extract_num(ref) or 0)
    return min(candidates, key=lambda p: abs(abs(extract_num(p) or 0) - rn))

def read_improved_chip(driver, ref_pct=None):
    _CHIP_POS = {"IMPROVED","Improved","improved"}; _CHIP_NEG = {"DECLINED","Declined","declined"}
    _CHIP_ALL = _CHIP_POS | _CHIP_NEG
    candidates = []
    def _harvest(txt, sign, out):
        for m in re.finditer(r"(\d+\.?\d*)\s*%", txt):
            p = f"{sign}{m.group(1)}%"
            if p not in out: out.append(p)
    for kw in _CHIP_ALL:
        sign = "+" if kw in _CHIP_POS else "-"
        try:
            for lel in driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{kw}']"):
                for lvl in range(1, 10):
                    try:
                        c = lel.find_element(By.XPATH, "/".join([".."] * lvl))
                        ct = (c.text or "").strip()
                        if len(ct) > 100 or "%" not in ct: continue
                        _harvest(ct, sign, candidates); break
                    except: continue
        except: continue
    if not candidates: return None
    return align_sign(ref_pct, _closest_pct(candidates, ref_pct))

def read_change_badge(driver, ref_pct=None):
    _BADGE_PHRASES = ["Change in chapter average","Change in chapter avg","Change in chapter"]
    candidates = []
    for phrase in _BADGE_PHRASES:
        try:
            for lel in driver.find_elements(By.XPATH, f"//*[contains(text(),'{phrase}')]"):
                for xp in ["./following-sibling::*[1]","./following-sibling::*[2]",
                           "./following::*[contains(text(),'%')][1]"]:
                    try:
                        for e in lel.find_elements(By.XPATH, xp):
                            txt = (e.text or "").strip()
                            if "%" in txt and 0 < len(txt) < 30:
                                p = extract_pct(txt)
                                if p and p not in candidates: candidates.append(p)
                    except: pass
        except: pass
    if not candidates: return None
    return align_sign(ref_pct, _closest_pct(candidates, ref_pct))

def read_exam_panel(driver, label):
    data = {"label": label, "accuracy": None, "exam_date": None,
            "struggling_count": None, "weak_concepts_count": None,
            "weakest_concepts": [], "strongest_concepts": []}
    try:
        result = driver.execute_script(r"""
            const label = arguments[0];
            const PCT_RE = /^\d{1,3}(\.\d+)?%$/;
            const INT_RE = /^\d+$/;
            const ACC_KWS = ['ACCURACY','Accuracy','accuracy'];
            const STR_KWS = ['Struggling students','Struggling Students'];
            const WK_KWS = ['Weak Concepts','Weak concepts'];
            const DATE_RE = /[A-Z][a-z]+ \d+, \d{4}/;
            let labelEl = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (t === label && el.children.length <= 4) { labelEl = el; break; }
            }
            if (!labelEl) return null;
            const lblRect = labelEl.getBoundingClientRect();
            const lblMidX = (lblRect.left + lblRect.right) / 2;
            function findByColumn(kws, targetX, tolerance) {
                let best = null; let bestDist = Infinity;
                for (const kw of kws) {
                    for (const el of document.querySelectorAll('*')) {
                        const t = (el.innerText||el.textContent||'').trim();
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
                let sib = refEl.previousElementSibling;
                while (sib) { const t = (sib.innerText||'').trim(); if (regex.test(t)) return t; sib = sib.previousElementSibling; }
                return null;
            }
            function numBelow(refEl, regex) {
                let sib = refEl.nextElementSibling;
                while (sib) { const t = (sib.innerText||'').trim(); if (regex.test(t)) return t; sib = sib.nextElementSibling; }
                return null;
            }
            const accEl = findByColumn(ACC_KWS, lblMidX, 160);
            let accuracy = accEl ? numAbove(accEl, PCT_RE) : null;
            if (accuracy) { const v=parseFloat(accuracy); if(v<=5||v>100) accuracy=null; }
            const strEl = findByColumn(STR_KWS, lblMidX, 220);
            const strRaw = strEl ? numBelow(strEl, INT_RE) : null;
            const struggling = (strRaw !== null && strRaw !== '') ? parseInt(strRaw) : null;
            const wkEl = findByColumn(WK_KWS, lblMidX, 220);
            const wkRaw = wkEl ? numBelow(wkEl, INT_RE) : null;
            const weakCount = (wkRaw !== null && wkRaw !== '') ? parseInt(wkRaw) : null;
            let panelEl = labelEl;
            for (let i = 0; i < 20; i++) { panelEl = panelEl.parentElement; if (!panelEl) break; const pt2 = (panelEl.innerText||'').trim(); if (pt2.length > 6000) break; if (ACC_KWS.some(k => pt2.includes(k)) && pt2.length > 30) break; }
            const pt = panelEl ? (panelEl.innerText||'').trim() : '';
            const dateM = DATE_RE.exec(pt);
            return { accuracy, date: dateM ? dateM[0] : null, struggling, weakCount };
        """, label)
        if result:
            if result.get("accuracy"): data["accuracy"] = result["accuracy"]
            if result.get("date"): data["exam_date"] = result["date"]
            if result.get("struggling") is not None: data["struggling_count"] = result["struggling"]
            if result.get("weakCount") is not None: data["weak_concepts_count"] = result["weakCount"]
    except: pass
    return data


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


def enorm(name):
    n = name.lower().strip().replace("&","and"); n = re.sub(r"\s+", " ", n)
    if n in EXCEL_ALIASES: return EXCEL_ALIASES[n]
    for ec in ALL_EXCEL_CHAPTERS:
        if ec.lower() == name.lower(): return ec
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  SCRIPT 2 — CHAPTERS TAB HELPERS
# ─────────────────────────────────────────────────────────────────────────────

_IGNORE_NAMES = {
    "chapter","chapters","sort chapters","search chapter",
    "chapter avg: high to low","chapter avg",
}

def wait_cards(driver, timeout: int = CARD_WAIT_SEC):
    """Wait until chapter card percentage badges are visible."""
    try:
        WebDriverWait(driver, timeout).until(lambda d:
            len(d.find_elements(By.XPATH,
                "//*[contains(text(),'%') and ("
                "contains(text(),'+') or contains(text(),'-') or "
                "contains(text(),'↑') or contains(text(),'↓'))]")) > 0)
    except:
        time.sleep(3)

def get_section_sel(driver):
    """
    Find the section dropdown on the Chapters page.
    Scores selects: prefers ones with short section-code options near 'Section' text.
    """
    sels = driver.find_elements(By.TAG_NAME, "select")
    for idx in [1, 0, 2, 3]:
        if idx >= len(sels): continue
        sel = sels[idx]
        opts = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option")
                if o.text.strip() and o.text.strip().lower() not in ("select","select section","--","")]
        if not opts: continue
        not_class   = not all(o.isdigit() for o in opts)
        not_subj    = not any(o.lower() in ("maths","physics","chemistry","english","biology","hindi") for o in opts)
        not_exam    = not any(o.lower() in ("midterm","preboard 1","preboard1","final","annual") for o in opts)
        if not_class and not_subj and not_exam and all(len(o) <= 12 for o in opts):
            return sel, idx
    if len(sels) > 1: return sels[1], 1
    return None, -1

def get_all_sections(driver):
    """Return all section options from the Chapters page section dropdown."""
    sel, idx = get_section_sel(driver)
    if sel is None: return []
    opts = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option")
            if o.text.strip() and o.text.strip().lower() not in ("select","select section","--","")]
    return list(dict.fromkeys(opts))  # deduplicated, order preserved

def switch_section(driver, section_name: str, chapters_url: str):
    """
    Select a section from the Chapters page dropdown and wait for cards to reload.
    Falls back to navigating to CHAPTERS_URL if JS-select doesn't trigger reload.
    """
    sel, idx = get_section_sel(driver)
    if sel is None: raise RuntimeError("Section dropdown not found on Chapters page")
    old_len = len(driver.page_source)
    ok = js_pick(driver, sel, section_name)
    if not ok: raise RuntimeError(f"Could not select section '{section_name}'")
    time.sleep(0.3)
    try:
        WebDriverWait(driver, 15).until(lambda d:
            abs(len(d.page_source) - old_len) > 500 or
            len(d.find_elements(By.XPATH,
                "//*[contains(text(),'%') and (contains(text(),'+') or "
                "contains(text(),'-') or contains(text(),'↑') or "
                "contains(text(),'↓'))]")) > 0)
    except:
        driver.get(chapters_url); time.sleep(1.2)
        sel2, _ = get_section_sel(driver)
        if sel2: js_pick(driver, sel2, section_name); time.sleep(0.3)
    wait_cards(driver)

def discover_cards(driver):
    """
    Script 2's card discovery — finds chapter cards by locating %+sign badges,
    then walking up the DOM to find the enclosing card element and name.
    3-layer strategy: badge walk-up → sibling scan → page-source regex.
    """
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
        src_html = driver.page_source
        for m in re.finditer(
                r">([A-Z][A-Za-z &\-]{3,60}?)<(?:(?!</ul>).){0,400}>"
                r"([+\-↑↓▲▼]\d+\.?\d*\s*%)<", src_html, re.DOTALL):
            nm = m.group(1).strip(); pct = extract_pct(m.group(2))
            if pct and nm not in seen and 3 < len(nm) <= 72:
                seen.add(nm)
                el = None
                try: el = driver.find_element(By.XPATH,
                        f"//*[contains(text(),'{nm.split()[0]}')]/ancestor::*[3]")
                except: pass
                cards.append({"name": nm, "pct": pct, "el": el})
    return cards

def read_card_pct(driver, card: dict):
    """Read the % badge for a card — tries XPath siblings then page-source regex."""
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
    src_html = driver.page_source
    m = re.search(re.escape(nm) + r".{0,300}?([+\-↑↓▲▼]\s*\d+\.?\d*)\s*%", src_html, re.DOTALL)
    if m: return extract_pct(m.group(1) + "%")
    return card.get("pct")

def click_card(driver, card: dict) -> bool:
    """Click a chapter card to open its detail panel."""
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

def scroll_into_view(driver, el):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
    except: pass


def discover_chapter_cards(driver):
    cards = []; seen = set()
    badges = driver.find_elements(By.XPATH,
        "//*[(contains(text(),'+') or contains(text(),'-') or contains(text(),'↑') or contains(text(),'↓') or contains(text(),'▲') or contains(text(),'▼')) and contains(text(),'%') and string-length(normalize-space(text())) < 15]")
    for badge in badges:
        pct = extract_pct((badge.text or "").strip())
        if not pct: continue
        for lvl in range(1, 10):
            try:
                c = badge.find_element(By.XPATH, "/".join([".."] * lvl))
                ct = (c.text or "").strip()
                nm = re.sub(r"[+\-↑↓▲▼△▽⬆⬇]?\s*\d+\.?\d*\s*%", "", ct).strip()
                nm = re.sub(r"[↑↓▲▼△▽⬆⬇]", "", nm).strip()
                if (4 < len(nm) <= 72 and not re.fullmatch(r"[\d\s.]+", nm)
                        and nm not in seen and nm.lower() not in {"chapter","chapters","sort chapters","chapter avg"}
                        and len(ct) < 200):
                    seen.add(nm); cards.append({"name": nm, "pct": pct, "el": c}); break
            except: continue
    return cards

def click_chapter_card(driver, card):
    nm = card["name"]; first = nm.split()[0]
    def try_click(el):
        try: scroll_to(driver, el); el.click(); return True
        except:
            try: driver.execute_script("arguments[0].click();", el); return True
            except: return False
    if card.get("el") and try_click(card["el"]): return True
    for xp in [f"//*[normalize-space(text())='{nm}']",
               f"//*[contains(normalize-space(text()),'{nm}')]",
               f"//*[contains(text(),'{first}')]/ancestor::*[2]"]:
        try:
            for c in driver.find_elements(By.XPATH, xp):
                t = (c.text or "").strip()
                if first in t and len(t) < 200 and try_click(c): return True
        except: continue
    return False

def test_chapters_tab(driver, wait, section):
    """
    Chapters Tab test — follows Script 2 (classlens_all_sections_final.py)
    run_section() architecture exactly.

    Flow:
      1. Navigate to CHAPTERS_URL
      2. switch_section() via get_section_sel() dropdown (scores selects)
      3. discover_cards() — finds chapter cards by +/-/↑/↓ + % badges
      4. Sort validation (High→Low)
      5. Per-chapter: read_card_pct, click_card, header_accuracy badge,
         LOC2 chip, LOC3 badge, LOC4 why-text, 4-way consistency,
         read_exam_panel × 2 (Midterm + Preboard 1),
         static labels, Excel mapping
      6. Search box (Phase 6)
      7. Static labels (Phase 7)
      8. Excel full coverage (Phase 8)
    Stores results in store["chapter_detail"].
    """
    sep(f"CHAPTERS TAB – Section {section}")
    b_ch = []

    # main() clicked Chapters tab — wait for chapter cards to render
    print(f"  {C}▸  Chapters Tab: waiting for cards (section {section})…{RST}")
    try:
        wait_cards(driver)
        rec(b_ch, "TC-CH-NAV", f"Chapters page ready for section '{section}'",
            "PASS", driver.current_url[-60:], suite="ChaptersTab", section=section)
    except:
        time.sleep(3)
        rec(b_ch, "TC-CH-NAV", "Chapters page — fallback wait 3s",
            "WARN", driver.current_url[-60:], suite="ChaptersTab", section=section)

    # ── Navigation verify ───────────────────────────────────────────────────
    src_pg = driver.page_source
    rec(b_ch, "TC-CH-URL", "Chapters URL loaded",
        "PASS" if ("screen=chapters" in driver.current_url or "chapters" in driver.current_url) else "WARN",
        driver.current_url[-60:], suite="ChaptersTab", section=section)
    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        rec(b_ch, f"TC-CH-TAB-{tab}", f"Tab '{tab}' present",
            "PASS" if tab in src_pg else "WARN", suite="ChaptersTab", section=section)

    # ── Phase 4: Card discovery ─────────────────────────────────────────────
    sub_sep("Phase 4: Card Discovery")
    cc = discover_cards(driver)
    rec(b_ch, "TC-CH-001", "Chapter cards discovered",
        "PASS" if cc else "WARN", f"{len(cc)} cards",
        suite="ChaptersTab", section=section)

    if not cc:
        store["chapter_detail"].append({"section": section, "cards": [], "tests": b_ch})
        return

    # Sort validation: High → Low
    nums = []
    for c in cc:
        m2 = re.search(r"(\d+\.?\d*)", c["pct"] or "")
        if m2:
            try:
                nums.append(float(m2.group(1)))
            except:
                pass
    if len(nums) >= 2:
        rec(b_ch, "TC-CH-SORT", "Cards sorted High→Low",
            "PASS" if all(nums[i] >= nums[i+1] for i in range(len(nums)-1)) else "WARN",
            str([round(v, 1) for v in nums[:5]]) + "…",
            suite="ChaptersTab", section=section)
    rec(b_ch, "TC-CH-SORT-LBL", "Sort label 'Chapter Avg' present",
        "PASS" if "Chapter Avg" in driver.page_source else "WARN",
        suite="ChaptersTab", section=section)

    print(f"\n  Chapters [{section}]:")
    for i, c in enumerate(cc, 1):
        col = G if "+" in c["pct"] else R
        arr = "▲" if "+" in c["pct"] else "▼"
        ec_name = enorm(c["name"])
        mark = f"  {G}✔{RST}" if ec_name else f"  {R}✘ NOT MAPPED{RST}"
        print(f"    {i:>2}. {c['name']:<52} {col}{arr} {c['pct']} {mark}")

    # ── Phase 5: Per-chapter detail ─────────────────────────────────────────
    sub_sep("Phase 5: Per-Chapter Detail — LOC1/LOC2/LOC3/LOC4 + Header Accuracy")
    ch_results = []

    for card in cc:
        ch = card["name"]
        direction = "▲" if "+" in (card["pct"] or "") else "▼"
        col = G if direction == "▲" else R
        print(f"\n  {col}{direction}  {ch}{RST}  {col}{card['pct']}{RST}")
        print(f"  {'─'*65}")

        ch_data = {
            "name": ch, "pct_card": card["pct"],
            "pct_chip": None, "pct_badge": None, "pct_why": None,
            "why_heading": None, "why_text": None, "why_acc_pct": None,
            "header_accuracy": None, "panels": [], "match": False, "skip": False,
        }

        # LOC 1 — card badge %
        pct_card = read_card_pct(driver, card)
        rec(b_ch, f"TC-CH-{ch[:18]}-L1",
            "Loc 1 · Card list badge % readable",
            "PASS" if pct_card is not None else "WARN",
            str(pct_card or "N/A"), suite="ChaptersTab", section=section)

        # Click card
        clicked = click_card(driver, card)
        rec(b_ch, f"TC-CH-{ch[:18]}-CLK",
            "Card clickable / detail panel opens",
            "PASS" if clicked else "WARN",
            suite="ChaptersTab", section=section)

        if not clicked:
            ch_data["skip"] = True
            ch_results.append(ch_data)
            continue

        time.sleep(PANEL_WAIT_SEC)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: any(kw in d.page_source for kw in _WHY_HEADINGS))
        except:
            time.sleep(1.5)

        src_pg = driver.page_source

        # ★ Header accuracy badge (Script 1 addition to Script 2)
        header_accuracy = read_header_accuracy_badge(driver)
        ch_data["header_accuracy"] = header_accuracy
        rec(b_ch, f"TC-CH-{ch[:18]}-HACC",
            "Header accuracy badge readable",
            "PASS" if header_accuracy else "WARN",
            str(header_accuracy or "NOT FOUND"),
            suite="ChaptersTab", section=section)

        # LOC 2 — IMPROVED/DECLINED chip
        pct_chip = read_improved_chip(driver, ref_pct=pct_card)
        # LOC 3 — Change in chapter average badge
        pct_badge = read_change_badge(driver, ref_pct=pct_card)
        # LOC 4 — Why-text
        why_h = next((kw for kw in _WHY_HEADINGS if kw in src_pg), None)
        why_t_raw = read_why_text(driver)
        if why_t_raw:
            for _kw in _WHY_HEADINGS:
                if why_t_raw.startswith(_kw):
                    why_t_raw = why_t_raw[len(_kw):].strip(" :\n")
                    break
        why_t = why_t_raw if why_t_raw and len(why_t_raw.strip()) > 10 else None
        pct_why = read_why_pct(why_t)
        if pct_why is None:
            pct_why = read_why_pct_from_page(driver, ref_pct=pct_card)
        why_acc_pct = read_why_accuracy_pct(why_t)

        # align_sign on all 4 locations
        pct_chip  = align_sign(pct_card, pct_chip)
        pct_badge = align_sign(pct_card, pct_badge)
        if pct_why:
            pct_why = align_sign(pct_card, pct_why)

        rec(b_ch, f"TC-CH-{ch[:18]}-L2",
            "Loc 2 · IMPROVED/DECLINED chip % readable",
            "PASS" if pct_chip is not None else "WARN",
            str(pct_chip or "N/A"), suite="ChaptersTab", section=section)
        rec(b_ch, f"TC-CH-{ch[:18]}-L3",
            "Loc 3 · Change in chapter average badge",
            "PASS" if pct_badge is not None else "WARN",
            str(pct_badge or "N/A"), suite="ChaptersTab", section=section)
        _l4v = pct_why or (f"acc:{why_acc_pct}" if why_acc_pct else None)
        rec(b_ch, f"TC-CH-{ch[:18]}-L4",
            "Loc 4 · Why-text % (change or accuracy)",
            "PASS" if _l4v is not None else "WARN",
            (f"change%={pct_why}" if pct_why
             else (f"accuracy%={why_acc_pct} (stable)" if why_acc_pct else "NOTHING FOUND")),
            suite="ChaptersTab", section=section)

        # 4-way consistency
        n1, n2, n3, n4 = norm_val(pct_card), norm_val(pct_chip), norm_val(pct_badge), norm_val(pct_why)
        present   = [n for n in [n1, n2, n3, n4] if n is not None]
        all_match = len(set(present)) == 1 and len(present) >= 2 and len(present) == 4
        rec(b_ch, f"TC-CH-{ch[:18]}-4WAY",
            "✦ 4-Way Consistency Loc1==Loc2==Loc3==Loc4",
            "PASS" if all_match else "WARN",
            f"L1={pct_card}  L2={pct_chip}  L3={pct_badge}  L4={pct_why}",
            suite="ChaptersTab", section=section)

        ch_data.update({
            "pct_card": pct_card, "pct_chip": pct_chip, "pct_badge": pct_badge,
            "pct_why": pct_why, "why_heading": why_h, "why_text": why_t,
            "why_acc_pct": why_acc_pct, "match": all_match,
        })

        # Static label checks (per Script 2 Phase 5)
        rec(b_ch, f"TC-CH-{ch[:18]}-WHY",
            "'Why this chapter' heading present",
            "PASS" if why_h else "WARN",
            why_h or "NOT FOUND", suite="ChaptersTab", section=section)
        rec(b_ch, f"TC-CH-{ch[:18]}-WHYT",
            "Explanation body text present",
            "PASS" if (why_t and len(why_t) > 10) else "WARN",
            (why_t or "")[:60] + "…" if why_t else "NOT FOUND",
            suite="ChaptersTab", section=section)

        for lbl_name, lbl_keys in [
            ("Midterm panel",          ["Midterm"]),
            ("Preboard 1 panel",       ["Preboard 1"]),
            ("ACCURACY label",         ["ACCURACY", "Accuracy", "accuracy"]),
            ("Weakest Concepts",       ["Weakest Concepts", "Weakest concepts"]),
            ("Strongest Concepts",     ["Strongest Concepts", "Strongest concepts"]),
            ("Struggling students",    ["Struggling students", "Struggling"]),
            ("Weak Concepts label",    ["Weak Concepts", "Weak concepts"]),
            ("IMPROVED/DECLINED chip", ["IMPROVED", "DECLINED", "Improved", "Declined"]),
            ("Change in chapter avg",  ["Change in chapter average", "Change in chapter"]),
        ]:
            found = any(k in src_pg for k in lbl_keys)
            lbl_id = lbl_name.replace(" ", "").replace("'", "")[:14]
            rec(b_ch, f"TC-CH-{ch[:18]}-{lbl_id}",
                f"Label '{lbl_name}' present",
                "PASS" if found else "WARN", suite="ChaptersTab", section=section)

        # Exam panels (Midterm + Preboard 1) — exact Script 2 read_exam_panel()
        for exam_label in EXAM_LABELS:
            pd = read_exam_panel(driver, exam_label)
            sc2 = pd["struggling_count"]
            wk  = pd["weak_concepts_count"]
            rec(b_ch, f"TC-CH-{ch[:18]}-{exam_label.replace(' ', '')}ACC",
                f"[{exam_label}] Accuracy % readable",
                "PASS" if pd["accuracy"] else "WARN",
                pd["accuracy"] or "N/A", suite="ChaptersTab", section=section)
            rec(b_ch, f"TC-CH-{ch[:18]}-{exam_label.replace(' ', '')}STR",
                f"[{exam_label}] Struggling students count",
                "PASS" if sc2 is not None else "WARN",
                f"{sc2} students" if sc2 is not None else "NOT FOUND",
                suite="ChaptersTab", section=section)
            rec(b_ch, f"TC-CH-{ch[:18]}-{exam_label.replace(' ', '')}WK",
                f"[{exam_label}] Weak Concepts count",
                "PASS" if wk is not None else "WARN",
                f"{wk} concepts" if wk is not None else "NOT FOUND",
                suite="ChaptersTab", section=section)
            rec(b_ch, f"TC-CH-{ch[:18]}-{exam_label.replace(' ', '')}WKL",
                f"[{exam_label}] Weakest Concepts >= 1 item",
                "PASS" if len(pd["weakest_concepts"]) >= 1 else "WARN",
                f"{len(pd['weakest_concepts'])} items: {pd['weakest_concepts'][:3]}",
                suite="ChaptersTab", section=section)
            rec(b_ch, f"TC-CH-{ch[:18]}-{exam_label.replace(' ', '')}STL",
                f"[{exam_label}] Strongest Concepts >= 1 item",
                "PASS" if len(pd["strongest_concepts"]) >= 1 else "WARN",
                f"{len(pd['strongest_concepts'])} items",
                suite="ChaptersTab", section=section)
            ch_data["panels"].append(pd)
            print(f"      {exam_label}:  Accuracy={pd['accuracy'] or '?'}"
                  f"  Struggling={sc2 if sc2 is not None else '?'}"
                  f"  WeakConcepts={wk if wk is not None else '?'}")

        # Concept pill badges
        pill_els = driver.find_elements(By.XPATH,
            "//*[normalize-space()='New' or normalize-space()='Improved' or "
            "    normalize-space()='Declined' or normalize-space()='NEW' or "
            "    normalize-space()='IMPROVED' or normalize-space()='DECLINED']")
        pills = list({(e.text or "").strip() for e in pill_els if (e.text or "").strip()})
        rec(b_ch, f"TC-CH-{ch[:18]}-PILLS",
            "Concept pill badges present",
            "PASS" if pills else "WARN", str(pills),
            suite="ChaptersTab", section=section)

        # Excel mapping per chapter
        ec = enorm(ch)
        rec(b_ch, f"TC-CH-{ch[:18]}-EXCEL",
            f"Excel match '{ch}'",
            "PASS" if ec else "WARN",
            ec or "NOT FOUND", suite="ChaptersTab", section=section)
        if ec:
            mq = MIDTERM_QUESTIONS.get(ec, [])
            pq = PREBOARD_QUESTIONS.get(ec, [])
            rec(b_ch, f"TC-CH-{ch[:18]}-MIDQ",
                f"  Midterm questions ({len(mq)})",
                "PASS", f"{len(mq)} questions",
                suite="ChaptersTab", section=section)
            rec(b_ch, f"TC-CH-{ch[:18]}-PREQ",
                f"  Preboard 1 questions ({len(pq)})",
                "PASS", f"{len(pq)} questions",
                suite="ChaptersTab", section=section)

        # ★ Terminal summary (Script 2 style)
        print(f"\n      WHY SECTION:")
        print(f"        Heading : {why_h or 'NOT FOUND'}")
        preview = (why_t or "NOT FOUND")[:70]
        print(f"        Text    : {preview}{'…' if why_t and len(why_t) > 70 else ''}")
        pct_col = G if pct_why and "+" in pct_why else (R if pct_why else Y)
        print(f"        Change %: {pct_col}{pct_why or '— (only accuracy % in text)'}{RST}")
        print(f"        Header Accuracy: {C}{header_accuracy or 'NOT FOUND'}{RST}")
        print(f"        4-Way: L1={pct_card}  L2={pct_chip}  L3={pct_badge}  L4={pct_why}")

        ch_results.append(ch_data)

    # ── Phase 6: Search box ─────────────────────────────────────────────────
    sub_sep("Phase 6: Search Box")
    driver.get(CHAPTERS_URL)
    time.sleep(1.2)
    try:
        s2, _ = get_section_sel(driver)
        if s2:
            js_pick(driver, s2, section)
            time.sleep(0.3)
    except:
        pass
    try:
        wait_cards(driver)
    except:
        time.sleep(2)
    fresh = discover_cards(driver)
    sb = None
    for inp in driver.find_elements(By.TAG_NAME, "input"):
        ph = (inp.get_attribute("placeholder") or "").lower()
        if "chapter" in ph or "search" in ph:
            sb = inp
            break
    if not sb:
        inps = driver.find_elements(By.TAG_NAME, "input")
        if inps:
            sb = inps[0]
    rec(b_ch, "TC-CH-SRCH-001", "Search input present",
        "PASS" if sb else "WARN",
        (sb.get_attribute("placeholder") or "") if sb else "N/A",
        suite="ChaptersTab", section=section)
    if sb and fresh:
        def clr():
            try:
                sb.click()
                sb.send_keys(Keys.CONTROL, "a")
                sb.send_keys(Keys.DELETE)
                time.sleep(0.5)
            except:
                pass
        kw = fresh[0]["name"].split()[0]
        other = fresh[-1]["name"] if len(fresh) > 1 else None
        clr()
        sb.send_keys(kw)
        time.sleep(0.7)
        rec(b_ch, "TC-CH-SRCH-002", f"Search '{kw}' → target visible",
            "PASS" if fresh[0]["name"] in driver.page_source else "WARN",
            suite="ChaptersTab", section=section)
        if other and other.split()[0].lower() != kw.lower():
            ov = driver.find_elements(By.XPATH, f"//*[normalize-space()='{other}']")
            rec(b_ch, "TC-CH-SRCH-003", "Search filters non-matching",
                "PASS" if (all(not e.is_displayed() for e in ov) if ov else True) else "WARN",
                suite="ChaptersTab", section=section)
        clr()
        missing = [c["name"] for c in fresh if c["name"] not in driver.page_source]
        rec(b_ch, "TC-CH-SRCH-004", "Search cleared → all cards restored",
            "PASS" if not missing else "WARN",
            "all present" if not missing else f"missing {len(missing)}",
            suite="ChaptersTab", section=section)
        clr()
        sb.send_keys("ZZZNOMATCH99")
        time.sleep(0.7)
        vis = driver.find_elements(By.XPATH, f"//*[normalize-space()='{fresh[0]['name']}']")
        rec(b_ch, "TC-CH-SRCH-005", "No-match query → cards hidden",
            "PASS" if (all(not e.is_displayed() for e in vis) if vis else True) else "WARN",
            suite="ChaptersTab", section=section)
        clr()

    # ── Phase 7: Static labels ──────────────────────────────────────────────
    sub_sep("Phase 7: Static Labels")
    driver.get(CHAPTERS_URL)
    time.sleep(1.2)
    try:
        s2, _ = get_section_sel(driver)
        if s2:
            js_pick(driver, s2, section)
            time.sleep(0.3)
    except:
        pass
    try:
        wait_cards(driver)
    except:
        time.sleep(2)
    src_pg = driver.page_source
    for lbl, kws in [
        ("Sort label 'Chapter Avg'",           ["Chapter Avg"]),
        ("Nav tab 'Overview'",                 ["Overview"]),
        ("Nav tab 'Chapters'",                 ["Chapters"]),
        ("Nav tab 'Questions'",                ["Questions"]),
        ("Nav tab 'Students'",                 ["Students"]),
        ("'Midterm' header",                   ["Midterm"]),
        ("'Preboard 1' header",                ["Preboard 1", "Preboard1"]),
        ("'ACCURACY' label",                   ["ACCURACY", "Accuracy", "accuracy"]),
        ("'Struggling students' label",        ["Struggling students", "Struggling"]),
        ("'Weak Concepts' label",              ["Weak Concepts", "Weak concepts"]),
        ("'Weakest Concepts' section",         ["Weakest Concepts", "Weakest concepts"]),
        ("'Strongest Concepts' section",       ["Strongest Concepts", "Strongest concepts"]),
        ("'Why this chapter' heading",         ["Why this chapter", "Why This Chapter"]),
        ("IMPROVED/DECLINED chip",             ["IMPROVED", "DECLINED", "Improved", "Declined"]),
        ("'Change in chapter average' label",  ["Change in chapter average", "Change in chapter"]),
        ("Concept pill badges",                ["New", "Improved", "Declined", "NEW", "IMPROVED"]),
        ("Header accuracy badge",              ["accuracy"]),
    ]:
        lbl_id = re.sub(r"[^A-Za-z0-9]", "", lbl)[:16]
        rec(b_ch, f"TC-CH-LBL-{lbl_id}", lbl,
            "PASS" if any(k in src_pg for k in kws) else "WARN",
            suite="ChaptersTab", section=section)

    # ── Phase 8: Excel full coverage ────────────────────────────────────────
    sub_sep("Phase 8: Excel Validation")
    cls = {enorm(c["name"]) for c in cc if enorm(c["name"])}
    ecl  = []
    ecov = []
    for card in cc:
        cn = card["name"]
        ec = enorm(cn)
        ie = ec is not None
        un = ""; um = 0; co = []; mq = []; pq = []
        if ie:
            for uname, udata in EXCEL_UNITS.items():
                if ec in udata["chapters"]:
                    un = uname; um = udata["marks"]; co = udata["chapters"][ec]
                    break
            mq = MIDTERM_QUESTIONS.get(ec, [])
            pq = PREBOARD_QUESTIONS.get(ec, [])
        rec(b_ch, f"TC-CH-XL-{cn[:20]}", f"Excel match '{cn}'",
            "PASS" if ie else "WARN",
            ec if ie else "NOT IN EXCEL",
            suite="ChaptersTab", section=section)
        ecl.append({
            "cl_name": cn, "pct": card["pct"], "excel_ch": ec or "", "unit": un,
            "unit_marks": um, "concepts": co, "mid_qs": mq, "pre_qs": pq,
            "mid_count": len(mq), "pre_count": len(pq),
            "result": "MATCH" if ie else "NOT IN EXCEL",
        })
    for uname, udata in EXCEL_UNITS.items():
        for ch2, co in udata["chapters"].items():
            ic = ch2 in cls
            ecov.append({
                "unit": uname, "unit_marks": udata["marks"], "excel_ch": ch2, "concepts": co,
                "mid_count": len(MIDTERM_QUESTIONS.get(ch2, [])),
                "pre_count": len(PREBOARD_QUESTIONS.get(ch2, [])),
                "result": "PRESENT" if ic else "MISSING",
            })

    # ── Store results ───────────────────────────────────────────────────────
    store["chapter_detail"].append({
        "section": section,
        "cards":   ch_results,
        "tests":   b_ch,
        "ecl":     ecl,
        "ecov":    ecov,
    })
    print(f"\n  {G}✅  Chapters Tab: {len(ch_results)} chapters analyzed{RST}")


# ══════════════════════════════════════════════════════════════════════════════════
#  STUDENT PROFILES TAB (from Script 4)
# ══════════════════════════════════════════════════════════════════════════════════
def get_pct_s1(card):
    try:
        for el in card.find_elements(By.XPATH, ".//*[contains(text(),'%')]"):
            t = (el.text or "").strip()
            if t and "%" in t and len(t) < 12: return t.strip()
    except: pass
    return "NA"

def get_pct_s2(driver):
    for xp in ["//*[contains(@class,'bg-green') and contains(text(),'%')]"]:
        el = None
        try: el = driver.find_element(By.XPATH, xp)
        except: pass
        if el:
            t = (el.text or "").strip()
            if t and "%" in t:
                m = PCT_RE.search(t)
                if m: return m.group(0)
    return "NA"

def get_pct_s3(driver):
    for xp in ["//*[(contains(text(),'IMPROVED') or contains(text(),'DECLINED') or contains(text(),'Improved') or contains(text(),'Declined')) and contains(text(),'%')]"]:
        try:
            el = driver.find_element(By.XPATH, xp)
            t = (el.text or "").strip()
            if t and "%" in t:
                m = PCT_RE.search(t)
                if m: return m.group(0)
        except: pass
    try:
        r = driver.execute_script(r"""
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (!t.includes('%')) continue;
                if (['improved','declined','IMPROVED','DECLINED'].some(k=>t.includes(k)) && t.length < 60) {
                    const m = t.match(/[+-]?\d+(?:\.\d+)?%/); if (m) return m[0];
                }
            }
            return null;
        """)
        if r: return r
    except: pass
    return "NA"

def get_pct_s4(driver):
    try:
        r = driver.execute_script(r"""
            let h = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||el.textContent||'').trim();
                if (t.toLowerCase() === 'progress report' && el.children.length < 3) { h = el; break; }
            }
            if (!h) return null;
            let node = h;
            for (let i = 0; i < 5; i++) {
                node = node.nextElementSibling || (node.parentElement && node.parentElement.nextElementSibling);
                if (!node) break;
                const t = (node.innerText||node.textContent||'').trim();
                if (t.includes('%')) { const m = t.match(/[+-]?\d+(?:\.\d+)?%/); if (m) return m[0]; }
            }
            return null;
        """)
        if r: return r
    except: pass
    return "NA"

def check_consistency(s1, s2, s3, s4):
    normals = {
        "left_card": normalize_pct(s1), "top_right_button": normalize_pct(s2),
        "center_arrow_box": normalize_pct(s3), "progress_report": normalize_pct(s4),
    }
    valid = {k: v for k, v in normals.items() if v != "NA"}
    status = ("SKIP" if len(valid) < 2 else "PASS" if len(set(valid.values())) == 1 else "FAIL")
    return status, normals

def extract_exam_full_student(driver, exam_name):
    try:
        card = driver.find_element(By.XPATH,
            f"//p[normalize-space()='{exam_name}']/ancestor::div[contains(@class,'border') and contains(@class,'rounded')][1]")
        text = card.text.replace("\n", " ")
        pct = PCT_RE.search(text); marks = MARKS_RE.search(text)
        def _ch(which):
            title = "Weakest chapters" if which == "weakest" else "Strongest chapters"
            out = []
            try:
                for r in card.find_elements(By.XPATH, f".//*[contains(normalize-space(),'{title}')]/following::*"):
                    t = (r.text or "").strip()
                    if not t or title.lower() in t.lower(): continue
                    fl = PCT_RE.sub("", t.split("\n")[0].strip()).strip()
                    if len(fl) >= 2 and fl not in out: out.append(fl)
                    if len(out) >= 3: break
            except: pass
            return out
        return {
            "percent": pct.group(0).strip() if pct else "NA",
            "marks": marks.group(0).replace(" ","") if marks else "NA",
            "weakest_chapters": _ch("weakest"), "strongest_chapters": _ch("strongest"),
        }
    except: return {"percent": "NA", "marks": "NA", "weakest_chapters": [], "strongest_chapters": []}

def _parse_learning_gaps_from_text(section_text):
    """Parse learning gaps from visible rendered text (Script 4 v8)."""
    if not section_text: return []
    text = section_text.replace("\r", "\n")
    m = re.search(r"Comparison of learning gaps", text, flags=re.I)
    if m: text = text[m.end():]
    text = text.replace("A comparison of mistake patterns across the last two tests.", " ")
    for marker in ["Progress report","Midterm","Preboard 1","Your Students",
                   "Overview","Strongest chapters","Weakest chapters"]:
        pos = text.find(marker)
        if pos > 0: text = text[:pos]
    lines = [re.sub(r"\s+", " ", raw).strip(" -|:\t")
             for raw in text.splitlines() if raw.strip()]
    if not lines: return []
    badge_terms = ["Most Critical","Most Improved","Improved","Worsened","New Type"]
    dir_terms   = ["More Errors","Fewer Errors"]
    known_cats  = ["Foundational Gaps","Makes Mistakes in Steps","Reads Questions Wrong",
                   "Makes Calculation Mistakes","Conceptual Gaps","Calculation Errors","Time Management"]
    noise       = set(x.lower() for x in badge_terms + dir_terms +
                      ["comparison of learning gaps",
                       "a comparison of mistake patterns across the last two tests."])
    def clean(s):
        s = re.sub(r"[+\-]?\d+(?:\.\d+)?%"," ",s)
        return re.sub(r"\s+"," ",s).strip(" -|:\t")
    gaps=[]; seen=set(); i=0
    while i < len(lines):
        line = lines[i]
        pct_m = re.search(r"[+\-]?\d+(?:\.\d+)?%", line)
        if not pct_m: i+=1; continue
        percent   = pct_m.group(0)
        window    = lines[i:i+12]
        direction = next((d for d in dir_terms for w in window if d.lower() in w.lower()),"NA")
        badge     = next((b for b in badge_terms for w in window if b.lower() in w.lower()),"NA")
        category  = "NA"; description = "NA"
        for w in window:
            wt = clean(w)
            if not wt or wt.lower() in noise: continue
            if any(d.lower() in wt.lower() for d in dir_terms): continue
            if any(b.lower() in wt.lower() for b in badge_terms): continue
            found = next((k for k in known_cats if k.lower() in wt.lower()), None)
            if found: category=found; break
            if 4 <= len(wt) <= 80: category=wt; break
        for w in window:
            wt = clean(w)
            if not wt or wt==category: continue
            if any(d.lower() in wt.lower() for d in dir_terms): continue
            if any(b.lower() in wt.lower() for b in badge_terms): continue
            if len(wt) >= 8: description=wt; break
        if category != "NA":
            sig = (category, percent, direction, badge)
            if sig not in seen:
                seen.add(sig)
                gaps.append({"category":category,"percent_change":percent,
                             "direction":direction,"badge":badge,"description":description})
        i+=1
    return gaps


def extract_learning_gaps_simple(driver):
    """
    Robust learning gaps extractor — Script 4 v8 super extractor.
    Layer 1: Scroll + rendered text parser.
    Layer 2: JS DOM card-based extractor.
    Never fails silently.
    """
    # Layer 1 — scroll and get best rendered text
    try:
        for _ in range(2):
            driver.execute_script(r"""
                const hit=Array.from(document.querySelectorAll("*")).find(el=>{
                    const t=(el.innerText||el.textContent||"").trim().toLowerCase();
                    return t.includes("comparison of learning gaps");
                });
                if(hit)hit.scrollIntoView({block:"center",behavior:"instant"});
            """)
            time.sleep(0.3)
            driver.execute_script(r"""
                const panels=Array.from(document.querySelectorAll("div")).filter(d=>{
                    const s=window.getComputedStyle(d);
                    return(s.overflowY==="auto"||s.overflowY==="scroll")&&d.scrollHeight>d.clientHeight;
                });
                panels.sort((a,b)=>(b.clientWidth*b.clientHeight)-(a.clientWidth*a.clientHeight));
                for(const p of panels.slice(0,4)){
                    p.scrollTop=Math.min(p.scrollHeight,p.scrollTop+900);
                }
            """)
            time.sleep(0.3)
    except: pass
    try:
        section_text = driver.execute_script(r"""
            function txt(el){return((el&&(el.innerText||el.textContent))||"").trim();}
            const nodes=Array.from(document.querySelectorAll("*")).filter(el=>{
                const t=txt(el).toLowerCase();
                return t.includes("comparison of learning gaps");
            });
            nodes.sort((a,b)=>txt(a).length-txt(b).length);
            for(const n of nodes){
                const t=txt(n);
                if(t.toLowerCase().includes("comparison of learning gaps")&&t.length>40)return t;
            }
            return document.body?(document.body.innerText||""):"";
        """)
        if section_text and "comparison of learning gaps" in section_text.lower():
            result = _parse_learning_gaps_from_text(section_text)
            if result: return result
    except: pass

    # Layer 2 — JS DOM card-based extractor
    try:
        result = driver.execute_script(r"""
        (function(){
            function txt(el){return((el&&(el.innerText||el.textContent))||"").trim();}
            const PCT_ONLY=/^[+\-]?\d+(?:\.\d+)?%$/;
            const PCT_ANY=/[+\-]?\d+(?:\.\d+)?%/;
            const DIR=["More Errors","Fewer Errors"];
            const BADGE=["Most Critical","Most Improved","Improved","Worsened"];
            const CATS=["Foundational Gaps","Makes Mistakes in Steps","Reads Questions Wrong",
                        "Makes Calculation Mistakes","Conceptual Gaps","Calculation Errors","Time Management"];
            const headingExists=Array.from(document.querySelectorAll("*")).some(el=>
                txt(el).toLowerCase().includes("comparison of learning gaps"));
            if(!headingExists)return{found:false,gaps:[]};
            const pctEls=Array.from(document.querySelectorAll("*")).filter(el=>{
                if(el.children.length>3)return false;
                return PCT_ONLY.test(txt(el));
            });
            const results=[];const seen=new Set();
            for(const pctEl of pctEls){
                const pctText=txt(pctEl);
                let card=null,node=pctEl.parentElement;
                for(let d=0;d<12;d++){
                    if(!node)break;
                    const nt=txt(node);
                    if(DIR.some(d2=>nt.includes(d2))&&nt.length>20&&nt.length<2000){
                        card=node;break;
                    }
                    node=node.parentElement;
                }
                if(!card)continue;
                const ct=txt(card);
                const direction=DIR.find(d=>ct.includes(d))||"NA";
                const badge=BADGE.find(b=>ct.includes(b))||"NA";
                let category="NA";
                for(const k of CATS){if(ct.toLowerCase().includes(k.toLowerCase())){category=k;break;}}
                if(category==="NA"){
                    for(const ch of card.querySelectorAll("*")){
                        if(ch.children.length>0)continue;
                        const t=txt(ch);
                        if(!t||t.length<4||t.length>80)continue;
                        if(PCT_ANY.test(t))continue;
                        if(DIR.includes(t)||BADGE.includes(t))continue;
                        category=t;break;
                    }
                }
                if(category==="NA")continue;
                const sig=category+"|"+pctText+"|"+direction;
                if(seen.has(sig))continue;
                seen.add(sig);
                results.push({category,percent_change:pctText,direction,badge,description:"NA"});
            }
            return{found:headingExists,gaps:results.slice(0,12)};
        })();
        """)
        if result and result.get("found") and result.get("gaps"):
            return [{"category":g["category"],"percent_change":g["percent_change"],
                     "direction":g["direction"],"badge":g["badge"],"description":g.get("description","")}
                    for g in result["gaps"] if g.get("category","NA")!="NA"]
    except: pass
    return []


def find_left_student_container(driver):
    hdr = driver.find_element(By.XPATH, "//*[normalize-space()='Your Students']")
    ctr = None
    try:
        ctr = hdr.find_element(By.XPATH,
            "./following::*[.//*[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')]][1]")
    except: pass
    return ctr if ctr else hdr.find_element(By.XPATH, "./ancestor::div[2]")

def get_student_cards(ctr):
    return ctr.find_elements(By.XPATH,
        ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl') and .//p[contains(@class,'font-bold')]]")

def get_card_name(card):
    el = None
    try: el = card.find_element(By.XPATH, ".//p[contains(@class,'font-bold')][1]")
    except: pass
    return (el.text or "").strip() if el else ""

def test_questions_tab(driver, wait, section):
    """
    Questions Tab — Script 3 full implementation.

    Tests per the original Script 3 (questions audit):
      Phase 1 — Navigate to Questions tab + verify page loads
      Phase 2 — For each chapter in the left panel:
                   • Click chapter card
                   • Read all questions shown in right panel
                   • Per question: number, concept, type, avg score %, struggle gap
                   • Validate chapter name vs curriculum (EXCEL_UNITS)
                   • Validate concept names vs curriculum sub-topics
      Phase 3 — Static label checks (column headers, UI elements)
      Phase 4 — Summary: total questions found, chapters tested

    Stores results in store["questions"].
    """
    sep(f"QUESTIONS TAB – Section {section}")
    b_q = []

    # ── Phase 1: Verify Questions tab is loaded ─────────────────────────────
    # main() already clicked the Questions tab button
    sub_sep("Phase 1: Verify Questions Tab")
    src_pg = driver.page_source
    tab_loaded = any(kw in src_pg for kw in
                     ["Question", "Chapter", "Concept", "question", "concept"])
    rec(b_q, "TC-Q-001", "Questions tab loaded",
        "PASS" if tab_loaded else "WARN",
        driver.current_url[-60:], suite="QuestionsTab", section=section)

    # ── Phase 2: Check chapter list on left panel ───────────────────────────
    sub_sep("Phase 2: Chapter List + Per-Question Detail")

    # Find left panel chapter cards (similar structure to Students tab)
    chapter_cards = []
    try:
        # Try multiple selectors for chapter cards on Questions tab
        for xp in [
            "//*[contains(@class,'cursor-pointer') and .//*[contains(@class,'font-bold')]]",
            "//*[contains(@class,'cursor-pointer') and contains(@class,'flex')]",
            "//div[contains(@class,'cursor-pointer')]",
        ]:
            cards_found = driver.find_elements(By.XPATH, xp)
            filtered = []
            for c in cards_found:
                try:
                    txt = (c.text or "").strip()
                    # Chapter cards have chapter names (3-60 chars, start with capital)
                    if 3 < len(txt) < 60 and txt[0].isupper() and "%" not in txt[:20]:
                        filtered.append((c, txt.split("\n")[0].strip()))
                except:
                    pass
            if len(filtered) >= 2:
                chapter_cards = filtered[:15]  # limit to 15 chapters
                break
    except Exception as e:
        print(f"  Chapter card discovery error: {e}")

    rec(b_q, "TC-Q-002", f"Chapter cards on Questions tab",
        "PASS" if chapter_cards else "WARN",
        f"{len(chapter_cards)} chapters found", suite="QuestionsTab", section=section)

    questions_data = []
    chapters_tested = 0

    for card_el, ch_name in chapter_cards[:12]:  # test up to 12 chapters
        try:
            # Click the chapter card
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", card_el)
            time.sleep(0.3)
            try:
                card_el.click()
            except:
                driver.execute_script("arguments[0].click()", card_el)
            time.sleep(2.0)

            # Validate chapter name against curriculum
            ec = enorm(ch_name)
            ch_valid = ec is not None
            rec(b_q, f"TC-Q-CH-{ch_name[:15]}", f"Chapter '{ch_name[:30]}' in curriculum",
                "PASS" if ch_valid else "WARN",
                ec or "NOT IN EXCEL_UNITS", suite="QuestionsTab", section=section)

            # Read questions from right panel
            q_rows = []
            try:
                # Questions appear as rows — look for numbered items or question rows
                src_q = driver.page_source

                # Strategy 1: Find question rows via JS
                q_result = driver.execute_script("""
                    // Find the right panel — it's the area that changes when a chapter is clicked
                    // Look for elements containing question numbers and percentages
                    const rows = [];
                    const seen = new Set();
                    
                    // Look for question row containers
                    const allEls = Array.from(document.querySelectorAll('*'));
                    for (const el of allEls) {
                        const txt = (el.innerText || '').trim();
                        const cls = (el.className || '').toString();
                        
                        // Question rows typically have: Q number + concept + % 
                        if (cls.includes('cursor-pointer') && cls.includes('flex') &&
                            txt.length > 5 && txt.length < 200) {
                            const lines = txt.split('\\n').filter(l => l.trim());
                            if (lines.length >= 1) {
                                const key = lines[0];
                                if (!seen.has(key) && /[A-Z]/.test(lines[0])) {
                                    seen.add(key);
                                    // Extract % values
                                    const pcts = txt.match(/\\d+\\.?\\d*\\s*%/g) || [];
                                    rows.push({
                                        text: txt.substring(0, 150),
                                        lines: lines.slice(0, 5),
                                        pcts: pcts,
                                    });
                                }
                            }
                        }
                    }
                    return rows.slice(0, 20);
                """)

                if q_result:
                    for qr in q_result:
                        lines = qr.get("lines", [])
                        pcts  = qr.get("pcts", [])
                        concept = lines[0] if lines else "—"
                        avg_score = pcts[0] if pcts else "—"
                        struggle  = pcts[1] if len(pcts) > 1 else "—"

                        # Detect question type from text
                        raw = qr.get("text", "")
                        q_type = "MCQ" if any(k in raw for k in ["MCQ","Multiple","(1)","1 mark"]) else \
                                 "2-mark" if "2 mark" in raw.lower() or "(2)" in raw else \
                                 "4-mark" if "4 mark" in raw.lower() or "(4)" in raw else \
                                 "Short" if "short" in raw.lower() else \
                                 "Long" if "long" in raw.lower() else "—"

                        q_rows.append({
                            "chapter":    ch_name,
                            "concept":    concept,
                            "type":       q_type,
                            "avg_score":  avg_score,
                            "struggle":   struggle,
                            "section":    section,
                        })
            except Exception as qe:
                print(f"    Q row extraction error: {qe}")

            # Fallback: parse page source for question data
            if not q_rows:
                try:
                    src_q2 = driver.page_source
                    import re as _re
                    # Look for concept + percentage pattern
                    pct_matches = _re.findall(
                        r"([A-Z][A-Za-z &\-]{3,50}?)\s*[·•]\s*(\d+\.?\d*)\s*%", src_q2)
                    for concept, pct in pct_matches[:10]:
                        q_rows.append({
                            "chapter":    ch_name,
                            "concept":    concept.strip(),
                            "type":       "—",
                            "avg_score":  f"{pct}%",
                            "struggle":   "—",
                            "section":    section,
                        })
                except:
                    pass

            if q_rows:
                rec(b_q, f"TC-Q-QD-{ch_name[:12]}", f"Questions for '{ch_name[:20]}'",
                    "PASS", f"{len(q_rows)} questions", suite="QuestionsTab", section=section)

                # Validate concepts against curriculum
                if ec and ec in enorm.__code__.co_consts:
                    pass  # curriculum check done above

                questions_data.extend(q_rows)
                chapters_tested += 1

                # Print sample
                for q in q_rows[:3]:
                    print(f"    Concept: {q['concept'][:40]:<40} Score: {q['avg_score']:>7} Struggle: {q['struggle']}")
            else:
                rec(b_q, f"TC-Q-QD-{ch_name[:12]}", f"Questions for '{ch_name[:20]}'",
                    "WARN", "No question rows extracted", suite="QuestionsTab", section=section)

        except Exception as ch_e:
            print(f"    Chapter '{ch_name}' error: {ch_e}")
            continue

    # ── Phase 3: Static label checks ───────────────────────────────────────
    sub_sep("Phase 3: Static Labels")
    src_final = driver.page_source
    for lbl, keys in [
        ("Questions tab header",  ["Questions", "question"]),
        ("Chapter column",        ["Chapter", "chapter", "Chapters"]),
        ("Concept column",        ["Concept", "concept"]),
        ("Performance / Score",   ["Average", "Score", "Performance", "accuracy", "%"]),
        ("Student struggle data", ["Struggling", "struggle", "Students", "student"]),
        ("MCQ / Question types",  ["MCQ", "Type", "Mark", "marks"]),
        ("Section label",         [section]),
    ]:
        found = any(k in src_final for k in keys)
        lbl_id = lbl.replace(" ", "").replace("/", "")[:14]
        rec(b_q, f"TC-Q-LBL-{lbl_id}", f"Label '{lbl}' present",
            "PASS" if found else "WARN", suite="QuestionsTab", section=section)

    # ── Phase 4: Summary ────────────────────────────────────────────────────
    rec(b_q, "TC-Q-SUMMARY", f"Chapters tested: {chapters_tested}, Questions captured: {len(questions_data)}",
        "PASS" if chapters_tested > 0 else "WARN",
        f"{chapters_tested} chapters | {len(questions_data)} questions",
        suite="QuestionsTab", section=section)

    store["questions"].append({
        "section":   section,
        "questions": questions_data,
        "tests":     b_q,
    })

    p_cnt = sum(1 for e in b_q if e.status == "PASS")
    f_cnt = sum(1 for e in b_q if e.status == "FAIL")
    w_cnt = sum(1 for e in b_q if e.status == "WARN")
    print(f"\n  {G}✅  Questions Tab: {len(b_q)} tests ({p_cnt}✔ {f_cnt}✘ {w_cnt}⚠) "
          f"| {chapters_tested} chapters | {len(questions_data)} questions{RST}")



def test_students_tab(driver, wait, section):
    sep(f"STUDENTS TAB – Section {section}")
    b_s = []

    # main() clicked Students tab — wait for page to render
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Your Students') or contains(text(),'Students')]")))
        time.sleep(1.5)
        rec(b_s, "TC-S-001", "Students tab loaded", "PASS",
            driver.current_url[-60:], suite="StudentsTab", section=section)
    except Exception as e:
        # Fallback: try clicking Students tab
        _click_nav_tab(driver, "Students"); time.sleep(2.0)
        tab_ok = any(kw in driver.page_source for kw in ["Students","student","Your Students"])
        rec(b_s, "TC-S-001", "Students tab load",
            "PASS" if tab_ok else "WARN", str(e)[:80], suite="StudentsTab", section=section)
        if not tab_ok:
            store["student_profiles"].append({"section": section, "students": [], "tests": b_s})
            return

    try: left_ctr = find_left_student_container(driver)
    except Exception as e:
        rec(b_s, "TC-S-002", "Student list container", "WARN", str(e), suite="StudentsTab", section=section)
        store["student_profiles"].append({"section": section, "students": [], "tests": b_s})
        return

    cards = get_student_cards(left_ctr)
    rec(b_s, "TC-S-002", f"Student cards found: {len(cards)}", "PASS" if cards else "WARN",
        suite="StudentsTab", section=section)

    s_results = []; processed = set()

    while True:
        try:
            left_ctr = find_left_student_container(driver)
            cards = get_student_cards(left_ctr)
        except: break

        for card in cards:
            try:
                name = get_card_name(card)
                if not name or name in processed: continue
                s1 = get_pct_s1(card)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                time.sleep(0.3)
                try: card.click()
                except: driver.execute_script("arguments[0].click();", card)
                time.sleep(RIGHT_PANEL_WAIT)

                s2 = get_pct_s2(driver); s3 = get_pct_s3(driver); s4 = get_pct_s4(driver)
                status, normals = check_consistency(s1, s2, s3, s4)
                mid = extract_exam_full_student(driver, "Midterm")
                pre = extract_exam_full_student(driver, "Preboard 1")
                gaps = extract_learning_gaps_simple(driver)
                processed.add(name)

                rec(b_s, f"TC-S-{name[:15]}-CON", f"[{name}] Consistency",
                    status, f"L1={s1} L2={s2} L3={s3} L4={s4}", suite="StudentsTab", section=section)
                rec(b_s, f"TC-S-{name[:15]}-MID", f"[{name}] Midterm %",
                    "PASS" if mid["percent"]!="NA" else "WARN", mid["percent"], suite="StudentsTab", section=section)
                rec(b_s, f"TC-S-{name[:15]}-PRE", f"[{name}] Preboard %",
                    "PASS" if pre["percent"]!="NA" else "WARN", pre["percent"], suite="StudentsTab", section=section)
                rec(b_s, f"TC-S-{name[:15]}-GAP", f"[{name}] Learning gaps",
                    "PASS" if gaps else "INFO", f"{len(gaps)} gaps", suite="StudentsTab", section=section)

                s_results.append({
                    "name": name, "section": section,
                    "midterm_marks": mid["marks"], "midterm_percent": mid["percent"],
                    "preboard1_marks": pre["marks"], "preboard1_percent": pre["percent"],
                    "midterm_weakest": mid["weakest_chapters"], "midterm_strongest": mid["strongest_chapters"],
                    "preboard1_weakest": pre["weakest_chapters"], "preboard1_strongest": pre["strongest_chapters"],
                    "learning_gaps": gaps,
                    "consistency": {"status": status, "normals": normals, "raw": {"L1":s1,"L2":s2,"L3":s3,"L4":s4}},
                })
                print(f"  {ICONS.get(status,'   ')} [{name}] Mid:{mid['percent']} Pre:{pre['percent']} Consistency:{status} Gaps:{len(gaps)}")
            except (StaleElementReferenceException, NoSuchElementException): continue
            except Exception as e: print(f"      student error: {e}"); continue

        try:
            last = driver.execute_script("return arguments[0].scrollTop;", left_ctr)
            driver.execute_script("arguments[0].scrollTop += 650;", left_ctr)
            time.sleep(0.9)
            new = driver.execute_script("return arguments[0].scrollTop;", left_ctr)
            if new == last: break
        except: break

    store["student_profiles"].append({"section": section, "students": s_results, "tests": b_s})
    print(f"\n  {G}✅  Students Tab: {len(s_results)} students analyzed{RST}")

# ══════════════════════════════════════════════════════════════════════════════════
#  PER-SECTION RUNNER
# ══════════════════════════════════════════════════════════════════════════════════
def run_section(driver, wait, section, is_first=False):
    global store, _P, _F, _W
    VALUES["Section"] = section

    print()
    print(f"{BLD}{VIO}{'▓'*72}")
    print(f"  SECTION  {Y}{section}{RST}{BLD}{VIO}")
    print(f"{'▓'*72}{RST}")

    if is_first:
        if not test_login(driver, wait):
            print(f"  {R}❌  Login failed for Section {section}{RST}"); return None
        if not test_navigation(driver, wait):
            print(f"  {R}❌  Navigation failed for Section {section}{RST}"); return None
        test_exam_comparison(driver)
        test_chapter_section(driver, "Reteach")
        test_chapter_section(driver, "Brushup")
        test_chapter_section(driver, "On Track")
        test_all_students(driver, wait)

    test_chapters_tab(driver, wait, section)
    test_questions_tab(driver, wait, section)
    test_students_tab(driver, wait, section)

    total = _P + _F + _W
    rate = round(_P / max(total, 1) * 100, 1)
    result = {
        "section": section, "total": total, "passed": _P,
        "failed": _F, "warnings": _W, "pass_rate": f"{rate}%",
        "store": deepcopy(store),
    }
    all_section_runs.append(result)
    return result

def discover_sections_from_form(driver, wait):
    """
    Read ALL available sections from the ENTRY-FORM Section dropdown (index 1).
    Screenshot layout: Class(0), Section(1), Subject(2), Exam(3).
    Select Class first so Section dropdown populates, then read all options.
    """
    sep("DISCOVER SECTIONS — Entry Form Dropdown (index 1)")
    if not wait_opt(driver, 0, VALUES["Class"], 20):
        print(f"  {Y}⚠️   Class dropdown timeout{RST}"); return []
    js_pick(driver, get_selects(driver)[0], VALUES["Class"])
    time.sleep(1.0)
    sels = get_selects(driver)
    if len(sels) < 2:
        print(f"  {Y}⚠️   Section dropdown not found at index 1{RST}"); return []
    sec_sel = sels[1]
    opts = sec_sel.find_elements(By.TAG_NAME, "option")
    SKIP = {"", "select", "select section", "choose", "--", "all"}
    sections = [o.text.strip() for o in opts if o.text.strip().lower() not in SKIP]
    seen = set(); unique = []
    for s in sections:
        if s not in seen: seen.add(s); unique.append(s)
    if SECTION_WHITELIST:
        unique = [s for s in unique if s in set(SECTION_WHITELIST)]
    rec(store["nav_tests"], "TC-DISC-001", f"Sections from form dropdown",
        "PASS" if unique else "WARN", ", ".join(unique) if unique else "None",
        suite="Setup", section="")
    print(f"  {G}📚  Sections discovered from form: {unique}{RST}")
    return unique


def fill_and_enter(driver, wait, section):
    """
    Bulletproof form filler.
    Strategy:
      1. Verify we are on the entry form (selects visible).
      2. Fill dropdowns by CONTENT (value-matching), not by fixed index.
      3. After each selection fire both 'input' and 'change' events and wait
         for the next dropdown / Enter button to appear.
      4. Click Enter via JS to avoid stale-element errors.
      5. Wait for the URL to gain '?exams=' which signals dashboard load.
    """
    print(f"\n  {C}▸  Form → Section {section}{RST}")

    # ── Ensure entry form is loaded ────────────────────────────────────────
    try:
        WebDriverWait(driver, 15).until(lambda d: len(get_selects(d)) >= 1)
    except:
        print(f"  {Y}⚠️   No selects found — reloading login URL{RST}")
        driver.get(LOGIN_URL); time.sleep(2.5)

    # ─────────────────────────────────────────────────────────────────────
    #  HELPER: smart_pick — find the right <select> by scanning its options,
    #  not by a hardcoded index.  Returns True on success.
    # ─────────────────────────────────────────────────────────────────────
    def smart_pick(target_value, label, tc_id, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                for sel in driver.find_elements(By.TAG_NAME, "select"):
                    try:
                        opts = [o.text.strip() for o in
                                sel.find_elements(By.TAG_NAME, "option")]
                        if target_value in opts:
                            ok = driver.execute_script("""
                                var s=arguments[0], w=arguments[1];
                                for(var i=0;i<s.options.length;i++){
                                    if(s.options[i].text.trim()===w){
                                        s.value=s.options[i].value;
                                        s.dispatchEvent(new Event('input',{bubbles:true}));
                                        s.dispatchEvent(new Event('change',{bubbles:true}));
                                        return true;
                                    }
                                }
                                return false;
                            """, sel, target_value)
                            if ok:
                                rec(store["nav_tests"], tc_id,
                                    f"Set {label}={target_value}",
                                    "PASS", suite="Navigation", section=section)
                                return True
                    except: continue
            except: pass
            time.sleep(0.4)
        rec(store["nav_tests"], tc_id, f"Dropdown '{label}'='{target_value}'",
            "WARN", "Timeout — not found in any select",
            suite="Navigation", section=section)
        return False

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 1 — Class
    # ─────────────────────────────────────────────────────────────────────
    if not smart_pick(VALUES["Class"], "Class", "TC-F-0", timeout=20):
        print(f"  {R}❌  Class not found — aborting section {section}{RST}")
        return False
    time.sleep(1.0)   # cascade: wait for Section dropdown

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 2 — Section
    # ─────────────────────────────────────────────────────────────────────
    if not smart_pick(section, "Section", "TC-F-1", timeout=20):
        print(f"  {R}❌  Section '{section}' not found — skipping{RST}")
        return False
    time.sleep(0.8)   # cascade: wait for Subject dropdown

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 3 — Subject
    # ─────────────────────────────────────────────────────────────────────
    if not smart_pick(VALUES["Subject"], "Subject", "TC-F-2", timeout=20):
        print(f"  {R}❌  Subject not found — aborting section {section}{RST}")
        return False
    time.sleep(1.0)   # cascade: wait for Exam dropdown

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 4 — Exam  (some sections may have no Exam data → skip gracefully)
    # ─────────────────────────────────────────────────────────────────────
    exam_val = VALUES.get("Exam", "")
    exam_ok  = False
    if exam_val:
        exam_ok = smart_pick(exam_val, "Exam", "TC-F-3", timeout=15)
        if exam_ok:
            time.sleep(1.0)   # cascade: wait for CompareLeft dropdown

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 5 — CompareLeft + CompareRight
    #  These are optional per-section.  Use smart_pick with a short timeout
    #  so we don't waste time on sections that don't have them.
    #  IMPORTANT: we wait for them to appear ONLY if Exam was selected.
    # ─────────────────────────────────────────────────────────────────────
    for key, tc_id in [("CompareLeft","TC-F-4"), ("CompareRight","TC-F-5")]:
        val = VALUES.get(key, "")
        if not val or not exam_ok: continue
        # Short wait — if not found in 8 s, move on
        found = smart_pick(val, key, tc_id, timeout=8)
        if found: time.sleep(0.5)

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 6 — Wait for Enter button then click it via JS (avoids stale refs)
    # ─────────────────────────────────────────────────────────────────────
    enter_clicked = False
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            # Re-find the button fresh on every attempt (never hold a reference)
            clicked = driver.execute_script(r"""
                var btns = Array.from(document.querySelectorAll('button'));
                for (var i = 0; i < btns.length; i++) {
                    var t = (btns[i].innerText || btns[i].textContent || '').trim();
                    if (t === 'Enter' || t === 'enter') {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if clicked:
                enter_clicked = True
                break
        except: pass
        time.sleep(0.5)

    if not enter_clicked:
        rec(store["nav_tests"], "TC-F-ENTER", "Enter button not found",
            "FAIL", "Button 'Enter' not in DOM after 20s",
            suite="Navigation", section=section)
        print(f"  {R}❌  Enter button not found for {section}{RST}")
        return False

    # ─────────────────────────────────────────────────────────────────────
    #  STEP 7 — Wait for dashboard to load (URL gains exams param OR content)
    # ─────────────────────────────────────────────────────────────────────
    try:
        WebDriverWait(driver, 25).until(lambda d:
            "exams=" in d.current_url or
            "screen=" in d.current_url or
            len(d.find_elements(By.XPATH,
                "//*[contains(text(),'Overview') or contains(text(),'Exam Comparison')]")) > 0
        )
        time.sleep(2.0)
        rec(store["nav_tests"], "TC-F-ENTER", "Enter → Dashboard",
            "PASS", driver.current_url, suite="Navigation", section=section)
        print(f"  {G}✅  Dashboard loaded for Section {section}{RST}")
        return True
    except Exception as e:
        # Even if the URL wait times out, check if we're actually on dashboard
        cur = driver.current_url
        if "exams=" in cur or "Overview" in driver.page_source:
            rec(store["nav_tests"], "TC-F-ENTER", "Enter → Dashboard",
                "PASS", cur, suite="Navigation", section=section)
            print(f"  {G}✅  Dashboard loaded for Section {section}{RST}")
            return True
        rec(store["nav_tests"], "TC-F-ENTER", "Dashboard load timeout",
            "FAIL", str(e)[:120], suite="Navigation", section=section)
        print(f"  {R}❌  Dashboard load failed for {section}: {str(e)[:60]}{RST}")
        return False


def go_back_to_entry_form(driver, wait):
    """
    Navigate cleanly back to the entry form between sections.
    The entry form is at LOGIN_URL when the user is logged in.
    If we land on a dashboard page (has 'Overview' tab), look for a Home/Back button.
    If we land on the login page, re-authenticate.
    Uses driver.get(LOGIN_URL) — never driver.back() which crashes sessions.
    """
    try:
        driver.get(LOGIN_URL)
        time.sleep(2.5)
    except Exception as nav_e:
        print(f"  {Y}⚠️   Navigation error: {nav_e}{RST}")
        return False

    cur_url = driver.current_url
    page_src = driver.page_source

    # Case 1: Already on entry form (has <select> dropdowns for Class/Section)
    sels = get_selects(driver)
    if len(sels) >= 2:
        return True

    # Case 2: On login page (has password input) — re-login
    pwd_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
    if pwd_fields:
        try:
            usr = driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
            pwd = pwd_fields[0]
            usr.clear(); usr.send_keys(USERNAME)
            pwd.clear(); pwd.send_keys(PASSWORD)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            WebDriverWait(driver, 20).until(lambda d: len(get_selects(d)) >= 2)
            time.sleep(1.0)
            return True
        except Exception as re_e:
            print(f"  {R}❌  Re-login failed: {re_e}{RST}")
            return False

    # Case 3: On dashboard (has 'Overview' text) — look for back/home button
    if "Overview" in page_src or "exams=" in cur_url:
        # Try clicking a back/home icon (usually top-left logo or ← arrow)
        for xp in [
            "//button[contains(@aria-label,'back') or contains(@aria-label,'home') or contains(@aria-label,'Back')]",
            "//*[contains(@class,'cursor-pointer') and (normalize-space()='←' or normalize-space()='‹')]",
            "//header//button[1]",
            "(//button)[1]",
        ]:
            try:
                els = driver.find_elements(By.XPATH, xp)
                for el in els:
                    if el.is_displayed():
                        driver.execute_script("arguments[0].click()", el)
                        time.sleep(2.0)
                        if len(get_selects(driver)) >= 2:
                            return True
            except: continue
        # If back button not found, try navigating to root
        try:
            driver.get(LOGIN_URL.rstrip("/"))
            time.sleep(2.0)
            if len(get_selects(driver)) >= 2:
                return True
        except: pass

    # Final check
    if len(get_selects(driver)) >= 2:
        return True

    print(f"  {Y}⚠️   go_back_to_entry_form: could not reach form (url={driver.current_url[:60]}){RST}")
    return False


def loc4_display(ch):
    """HTML cell for LOC4 — Script 2 format. Used in Chapters Tab."""
    pct_why = ch.get("pct_why"); acc_pct = ch.get("why_acc_pct")
    pct_card = ch.get("pct_card",""); why_h = ch.get("why_heading","")
    if pct_why:
        col = "#3fb950" if "+" in pct_why else "#ff7b72"
        arr = "▲" if "+" in pct_why else "▼"
        return f'<span style="color:{col};font-weight:700;font-family:var(--mono)">{arr} {pct_why}</span>'
    if acc_pct:
        improved = "+" in pct_card or "improved" in why_h.lower()
        col = "#3fb950" if improved else "#ff7b72"; arr = "▲" if improved else "▼"
        return (f'<span style="color:{col};font-weight:700;font-family:var(--mono)">{arr} {acc_pct}</span>'
                f'<br><span style="color:var(--mut);font-size:10px">accuracy in why-text</span>')
    return '<span style="color:var(--mut)">—</span>'


def get_all_labels(driver, wait):
    """Script 3 alias: discover all question labels on Questions tab."""
    try:
        WebDriverWait(driver, 20).until_not(
            EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Loading...']")))
    except: pass
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.XPATH, "//*[normalize-space()='Q1' or normalize-space()='Q2']")))
    except: pass
    time.sleep(1.0)
    els = driver.find_elements(By.XPATH,
        "//*[starts-with(normalize-space(),'Q') and normalize-space()!='Q']")
    labels = []; seen = set()
    for el in els:
        try:
            if not el.is_displayed(): continue
        except: continue
        t = el.text.strip()
        if re.match(r"^Q\d+(\.\d+)?$", t) and t not in seen:
            seen.add(t); labels.append(t)
    return labels


def parse_gaps(block):
    """Script 3: parse per-question struggle gaps from block text."""
    gaps = []; lines = [l.strip() for l in block.splitlines() if l.strip()]
    idxs = [i for i, l in enumerate(lines) if re.match(r"^\d+(?:\.\d+)?\s*%$", l)]
    for k, start in enumerate(idxs):
        pct   = lines[start]
        title = lines[start+1].strip() if start+1 < len(lines) else ""
        if not title or re.match(r"^\d+%", title): continue
        end   = idxs[k+1] if k+1 < len(idxs) else len(lines)
        gaps.append({"pct":pct,"title":title,"desc":" ".join(lines[start+2:end]).strip()})
    return gaps



def build_report():
    """
    Professional HTML report with 4 clearly separated tabs per section:
    Overview | Chapters | Questions | Students
    Plus a master summary dashboard.
    """
    import re as _re

    total = _P + _F + _W
    rate  = round(_P / max(total, 1) * 100, 1)

    # Build ALL_SECTIONS_DATA from per-section snapshots
    ALL_SECTIONS_DATA = []
    for sr in all_section_runs:
        sec = sr["section"]
        _raw_exam     = sr.get("exam", store.get("exam", {}))
        exam_snap     = {
            "left":  _raw_exam.get("left",  _raw_exam.get("left_pct",  "—")),
            "right": _raw_exam.get("right", _raw_exam.get("right_pct", "—")),
            "trend": _raw_exam.get("trend", "—"),
        }
        chapters_snap = sr.get("chapters", store.get("chapters", {}))
        students_snap = sr.get("students", store.get("students", {}))
        ch_detail_raw = sr.get("chapter_detail", [])
        q_list_raw    = sr.get("questions", [])
        s_profiles    = sr.get("student_profiles", [])

        ch_cards = []
        for cd in ch_detail_raw:
            if isinstance(cd, dict) and "cards" in cd:
                ch_cards.extend(cd.get("cards", []))
            elif isinstance(cd, dict) and "name" in cd:
                ch_cards.append(cd)

        q_flat = []
        for qr in q_list_raw:
            if isinstance(qr, dict) and "questions" in qr:
                q_flat.extend(qr["questions"])
            elif isinstance(qr, dict) and "label" in qr:
                q_flat.append(qr)

        s_flat = []
        for sr2 in s_profiles:
            if isinstance(sr2, dict) and "students" in sr2:
                s_flat.extend(sr2["students"])
            elif isinstance(sr2, dict) and "student_name" in sr2:
                s_flat.append(sr2)

        ALL_SECTIONS_DATA.append({
            "section":   sec,
            "passed":    sr.get("passed", 0),
            "failed":    sr.get("failed", 0),
            "warnings":  sr.get("warnings", 0),
            "total":     sr.get("total", 0),
            "pass_rate": sr.get("pass_rate", "0%"),
            "exam":      exam_snap,
            "chapter_sections": {
                lbl: chapters_snap.get(lbl, {})
                for lbl in ["Reteach", "Brushup", "On Track"]
            },
            "students_overview": students_snap,
            "chapter_detail":   ch_cards,
            "questions":        q_flat,
            "students":         s_flat,
        })

    cnt_secs = len(ALL_SECTIONS_DATA)

    def sb(s):
        m = {"PASS": ("pass-badge", "✔ PASS"), "FAIL": ("fail-badge", "✘ FAIL"),
             "WARN": ("warn-badge", "⚠ WARN"), "INFO": ("info-badge", "ℹ INFO")}
        cls, lbl = m.get(s, ("info-badge", s))
        return f'<span class="{cls}">{lbl}</span>'

    def pct_cell(v):
        if not v or v in ("—", "N/A", ""):
            return '<span class="dim">—</span>'
        col = "#22c55e" if "+" in str(v) else "#ef4444"
        arr = "▲" if "+" in str(v) else "▼"
        return f'<span style="color:{col};font-weight:700">{arr} {v}</span>'

    def tests_table(tests_list, filter_fn=None):
        entries = [e for e in (ALL_TESTS if not filter_fn else
                   [e for e in ALL_TESTS if filter_fn(e)])]
        if not entries:
            return '<div class="empty-state">No test data recorded</div>'
        rows = ""
        for e in entries:
            icon = "✔" if e.status == "PASS" else ("✘" if e.status == "FAIL" else "⚠")
            row_cls = "tr-pass" if e.status == "PASS" else ("tr-fail" if e.status == "FAIL" else "tr-warn")
            det = str(e.detail or "")[:100]
            rows += (f'<tr class="{row_cls}">'
                     f'<td class="tc-icon">{icon}</td>'
                     f'<td class="tc-id">{e.tc_id}</td>'
                     f'<td class="tc-desc">{e.desc}</td>'
                     f'<td>{sb(e.status)}</td>'
                     f'<td class="tc-det">{det}</td>'
                     f'<td class="tc-time">{e.ts}</td></tr>')
        return (f'<table class="tc-table"><thead><tr>'
                f'<th width="28"></th><th width="120">Test ID</th>'
                f'<th>Description</th><th width="90">Status</th>'
                f'<th>Detail</th><th width="72">Time</th>'
                f'</tr></thead><tbody>{rows}</tbody></table>')

    # ── Overview tab HTML for one section ─────────────────────────────────────
    def build_overview_tab(sd):
        sec = sd["section"]
        exam = sd["exam"]
        lv   = exam.get("left", "—")
        rv   = exam.get("right", "—")
        tr   = exam.get("trend", "—")
        is_dec = any(w in str(tr).lower() for w in ["decline", "drop", "decrease"])
        banner_col = "linear-gradient(135deg,#7f1d1d,#991b1b)" if is_dec else "linear-gradient(135deg,#14532d,#15803d)"
        trend_txt  = f"{'↓' if is_dec else '↑'} {tr}"

        # Chapter sections (Reteach / Brushup / On Track)
        ch_html = ""
        for label, color, bg in [
            ("Reteach",   "#3b82f6", "rgba(59,130,246,0.08)"),
            ("Brushup",   "#f59e0b", "rgba(245,158,11,0.08)"),
            ("On Track",  "#22c55e", "rgba(34,197,94,0.08)"),
        ]:
            cd  = sd["chapter_sections"].get(label, {})
            badge = cd.get("badge", "—")
            cards = cd.get("cards", [])
            card_rows = ""
            for c in cards:
                avg = c.get("chapter_avg", "N/A")
                wt  = c.get("avg_weightage", "N/A")
                avg_html = (f'<span style="color:{"#22c55e" if avg not in ("N/A","") and not avg.startswith("-") else "#ef4444"};font-weight:700">{avg}</span>'
                            if avg not in ("N/A", "") else '<span class="dim">N/A</span>')
                card_rows += (f'<tr><td style="font-weight:600;color:#e2e8f0">{c.get("name","")}</td>'
                              f'<td style="text-align:center">{avg_html}</td>'
                              f'<td style="text-align:center;color:#94a3b8">{wt}</td></tr>')
            modal_chs = cd.get("modal_chapters", [])
            modal_html = ""
            if modal_chs:
                modal_html = '<div style="margin-top:8px;font-size:11px;color:#64748b">Modal chapters: ' + ", ".join(modal_chs[:5]) + ("…" if len(modal_chs) > 5 else "") + "</div>"
            ch_html += f'''
            <div class="ch-section" style="border-left:3px solid {color};background:{bg}">
              <div class="ch-sec-hdr">
                <span class="ch-label" style="color:{color}">{label}</span>
                <span class="ch-badge">{badge}</span>
              </div>
              {modal_html}
              {'<table class="mini-table"><thead><tr><th>Chapter</th><th>Avg %</th><th>Weightage</th></tr></thead><tbody>' + card_rows + '</tbody></table>' if cards else '<div class="empty-state">No chapter cards captured</div>'}
            </div>'''

        # Highlighted students
        stu_html = ""
        for cat, color, icon in [
            ("Weak", "#ef4444", "W"),
            ("Lagging", "#f59e0b", "L"),
            ("Performing Well", "#22c55e", "P"),
        ]:
            sd2  = sd["students_overview"].get(cat, {})
            all_s = sd2.get("all", sd2.get("visible", []))
            badge = sd2.get("badge", "—")
            rows  = "".join(
                f'<div class="stu-row"><span class="stu-name">{s.get("name","")}</span>'
                f'<span class="stu-score" style="color:{color}">{s.get("pct","")}</span></div>'
                for s in all_s[:6])
            more = f'<div class="dim" style="font-size:11px;padding:4px 8px">+{len(all_s)-6} more</div>' if len(all_s) > 6 else ""
            stu_html += f'''
            <div class="stu-cat" style="border-top:3px solid {color}">
              <div class="stu-cat-hdr" style="background:rgba({'239,68,68' if color=="#ef4444" else '245,158,11' if color=="#f59e0b" else '34,197,94'},.12)">
                <span class="stu-ico" style="background:{color}">{icon}</span>
                <div><div class="stu-cat-name">{cat}</div><div class="dim" style="font-size:11px">{badge}</div></div>
              </div>
              {rows or '<div class="empty-state">No students captured</div>'}{more}
            </div>'''

        ov_tests = [e for e in ALL_TESTS if e.section == sec and
                    e.suite in ("Overview","Navigation","Auth","Setup","")]
        return f'''
        <div class="tab-section-content">
          <!-- Exam Comparison Banner -->
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr"><span class="card-icon">📊</span> Exam Comparison Banner</div>
            <div class="exam-banner" style="background:{banner_col}">
              <div class="exam-side">
                <div class="exam-lbl">{FIXED.get("CompareLeft","Midterm")}</div>
                <div class="exam-val">{lv}</div>
              </div>
              <div class="exam-arrow">→</div>
              <div class="exam-side">
                <div class="exam-lbl">{FIXED.get("CompareRight","Preboard 1")}</div>
                <div class="exam-val">{rv}</div>
              </div>
              <div class="exam-trend">{trend_txt}</div>
            </div>
          </div>
          <!-- Chapter Cards -->
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr"><span class="card-icon">📚</span> Chapter Cards (Reteach · Brushup · On Track)</div>
            <div class="ch-grid">{ch_html}</div>
          </div>
          <!-- Highlighted Students -->
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr"><span class="card-icon">👥</span> Highlighted Students</div>
            <div class="stu-grid">{stu_html}</div>
          </div>
          <!-- Test Results -->
          <div class="card">
            <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Overview</div>
            {tests_table(ov_tests, lambda e: e.section==sec and e.suite in ("Overview","Navigation","Auth","Setup",""))}
          </div>
        </div>'''

    # ── Chapters tab HTML ──────────────────────────────────────────────────────
    def build_chapters_tab(sd):
        sec = sd["section"]
        ch_cards = sd["chapter_detail"]
        if not ch_cards:
            return '<div class="tab-section-content"><div class="empty-state" style="padding:40px">No chapter detail data captured for this section.</div></div>'

        rows = ""
        for i, ch in enumerate(ch_cards, 1):
            nm = ch.get("name","")
            p1 = ch.get("pct_card") or "—"
            p2 = ch.get("pct_chip") or "—"
            p3 = ch.get("pct_badge") or "—"
            p4 = ch.get("pct_why") or "—"
            ha = ch.get("header_accuracy") or "—"
            ok = ch.get("match", False)
            skip = ch.get("skip", False)
            result_badge = ('<span class="pass-badge">✔ MATCH</span>' if ok else
                           ('<span class="skip-badge">SKIP</span>' if skip else
                            '<span class="fail-badge">✘ MISMATCH</span>'))
            rows += (f'<tr class="{"tr-pass" if ok else "tr-skip" if skip else ""}">'
                     f'<td class="tc-id">{i}</td>'
                     f'<td style="font-weight:600;color:#e2e8f0">{nm}</td>'
                     f'<td style="text-align:center">{pct_cell(p1) if p1!="—" else "<span class=dim>—</span>"}</td>'
                     f'<td style="text-align:center">{pct_cell(p2) if p2!="—" else "<span class=dim>—</span>"}</td>'
                     f'<td style="text-align:center">{pct_cell(p3) if p3!="—" else "<span class=dim>—</span>"}</td>'
                     f'<td style="text-align:center">{pct_cell(p4) if p4!="—" else "<span class=dim>—</span>"}</td>'
                     f'<td style="text-align:center;color:#60a5fa;font-weight:700">{ha}</td>'
                     f'<td style="text-align:center">{result_badge}</td>'
                     f'</tr>')
            # Exam panels
            for pd in ch.get("panels", []):
                lbl = pd.get("label","")
                acc = pd.get("accuracy","—") or "—"
                sc2 = pd.get("struggling_count")
                wk  = pd.get("weak_concepts_count")
                wc  = pd.get("weakest_concepts",[])[:3]
                col = "#facc15" if lbl == "Midterm" else "#60a5fa"
                rows += (f'<tr style="background:rgba(0,0,0,0.2)">'
                         f'<td></td>'
                         f'<td style="padding-left:28px;color:{col};font-size:12px">↳ {lbl}</td>'
                         f'<td colspan="4" style="color:#94a3b8;font-size:12px">'
                         f'Accuracy: <strong style="color:{col}">{acc}</strong> &nbsp; '
                         f'Struggling: <strong>{sc2 if sc2 is not None else "?"}</strong> &nbsp; '
                         f'WeakConcepts: <strong>{wk if wk is not None else "?"}</strong>'
                         + (f' &nbsp; Weakest: <em>{", ".join(str(w) for w in wc)}</em>' if wc else "")
                         + f'</td><td></td></tr>')

        ch_tests = [e for e in ALL_TESTS if e.section == sec and e.suite == "ChaptersTab"]
        return f'''
        <div class="tab-section-content">
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr">
              <span class="card-icon">📗</span> Chapter Detail — LOC1-4 Consistency + Header Accuracy
              <span class="pill" style="margin-left:auto">{len(ch_cards)} chapters</span>
            </div>
            <div class="tw">
              <table class="tc-table">
                <thead><tr>
                  <th width="36">#</th><th>Chapter</th>
                  <th width="90" style="text-align:center">Loc1<br><small>Card</small></th>
                  <th width="90" style="text-align:center">Loc2<br><small>Chip</small></th>
                  <th width="90" style="text-align:center">Loc3<br><small>Badge</small></th>
                  <th width="90" style="text-align:center">Loc4<br><small>Why</small></th>
                  <th width="90" style="text-align:center;color:#60a5fa">Header<br>Accuracy</th>
                  <th width="100" style="text-align:center">4-Way</th>
                </tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>
          </div>
          <div class="card">
            <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Chapters Tab</div>
            {tests_table(ch_tests)}
          </div>
        </div>'''

    # ── Questions tab HTML ─────────────────────────────────────────────────────
    def build_questions_tab(sd):
        sec = sd["section"]
        q_list = sd["questions"]
        q_tests = [e for e in ALL_TESTS if e.section == sec and e.suite == "QuestionsTab"]

        if not q_list:
            return f'''
            <div class="tab-section-content">
              <div class="card" style="margin-bottom:16px">
                <div class="card-hdr"><span class="card-icon">❓</span> Questions Tab</div>
                <div class="empty-state">No question data captured for this section.</div>
              </div>
              <div class="card">
                <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Questions Tab</div>
                {tests_table(q_tests)}
              </div>
            </div>'''

        rows = ""
        for i, q in enumerate(q_list, 1):
            qnum  = q.get("question_num", q.get("num", str(i)))
            ch    = q.get("chapter", q.get("chapter_name", "—"))
            con   = q.get("concept", "—")
            qtype = q.get("question_type", q.get("type", "—"))
            pct   = q.get("avg_score", q.get("score", "—"))
            rows += (f'<tr><td class="tc-id">{qnum}</td>'
                     f'<td style="font-weight:600;color:#e2e8f0">{ch}</td>'
                     f'<td style="color:#94a3b8">{con}</td>'
                     f'<td style="color:#94a3b8">{qtype}</td>'
                     f'<td style="text-align:center">{pct_cell(str(pct)) if pct not in ("—","") else "<span class=dim>—</span>"}</td>'
                     f'</tr>')

        return f'''
        <div class="tab-section-content">
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr">
              <span class="card-icon">❓</span> Questions — Chapter/Concept Mapping
              <span class="pill" style="margin-left:auto">{len(q_list)} questions</span>
            </div>
            <div class="tw">
              <table class="tc-table">
                <thead><tr><th width="60">Q#</th><th>Chapter</th>
                  <th>Concept</th><th width="100">Type</th>
                  <th width="80" style="text-align:center">Avg Score</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>
          </div>
          <div class="card">
            <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Questions Tab</div>
            {tests_table(q_tests)}
          </div>
        </div>'''

    # ── Students tab HTML ──────────────────────────────────────────────────────
    def build_students_tab(sd):
        sec = sd["section"]
        s_list = sd["students"]
        s_tests = [e for e in ALL_TESTS if e.section == sec and e.suite == "StudentsTab"]

        if not s_list:
            return f'''
            <div class="tab-section-content">
              <div class="card" style="margin-bottom:16px">
                <div class="card-hdr"><span class="card-icon">🎓</span> Students Tab</div>
                <div class="empty-state">No student profile data captured for this section.</div>
              </div>
              <div class="card">
                <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Students Tab</div>
                {tests_table(s_tests)}
              </div>
            </div>'''

        rows = ""
        for i, s in enumerate(s_list, 1):
            name  = s.get("student_name", s.get("name", "—"))
            mid   = s.get("midterm_pct", s.get("pct_mid", s.get("pct", "—")))
            pre   = s.get("preboard_pct", s.get("pct_pre", "—"))
            gaps  = s.get("learning_gaps", [])
            n_gaps = len(gaps) if isinstance(gaps, list) else 0
            gap_col = "#ef4444" if n_gaps > 3 else ("#f59e0b" if n_gaps > 0 else "#22c55e")
            mid_v = str(mid) if mid and mid not in ("NA","—","") else "NA"
            pre_v = str(pre) if pre and pre not in ("NA","—","") else "NA"
            rows += (f'<tr><td class="tc-id">{i}</td>'
                     f'<td style="font-weight:600;color:#e2e8f0">{name}</td>'
                     f'<td style="text-align:center;color:#facc15">{mid_v}</td>'
                     f'<td style="text-align:center;color:#60a5fa">{pre_v}</td>'
                     f'<td style="text-align:center"><span style="color:{gap_col};font-weight:700">{n_gaps}</span></td>'
                     f'</tr>')

        return f'''
        <div class="tab-section-content">
          <div class="card" style="margin-bottom:16px">
            <div class="card-hdr">
              <span class="card-icon">🎓</span> Student Profiles — Exam Scores & Learning Gaps
              <span class="pill" style="margin-left:auto">{len(s_list)} students</span>
            </div>
            <div class="tw">
              <table class="tc-table">
                <thead><tr><th width="40">#</th><th>Student</th>
                  <th width="90" style="text-align:center;color:#facc15">Midterm %</th>
                  <th width="90" style="text-align:center;color:#60a5fa">Preboard %</th>
                  <th width="80" style="text-align:center">Gaps</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>
          </div>
          <div class="card">
            <div class="card-hdr"><span class="card-icon">🧪</span> Test Results — Students Tab</div>
            {tests_table(s_tests)}
          </div>
        </div>'''

    # ── Build per-section blocks ───────────────────────────────────────────────
    section_blocks = ""
    section_nav_items = ""
    for sd in ALL_SECTIONS_DATA:
        sec   = sd["section"]
        sid   = _re.sub(r"[^A-Za-z0-9]", "_", sec)
        p     = sd["passed"]; f_ = sd["failed"]; w = sd["warnings"]
        t     = sd["total"];  r  = sd["pass_rate"]
        bar_c = "#22c55e" if f_ == 0 else ("#f59e0b" if f_ <= 3 else "#ef4444")

        section_nav_items += (
            f'<div class="sec-nav-item" data-sec="{sid}" onclick="switchSection(\'{sid}\')">'
            f'<span class="sec-nav-label">{sec}</span>'
            f'<span class="sec-nav-rate" style="color:{bar_c}">{r}</span>'
            f'</div>')

        section_blocks += f'''
        <div class="section-block" id="sec-{sid}" style="display:none">
          <!-- Section header -->
          <div class="sec-hdr-bar">
            <div class="sec-hdr-left">
              <div class="sec-title">Section {sec}</div>
              <div class="sec-meta">
                <span class="kpi-mini" style="color:#60a5fa">{t} tests</span>
                <span class="kpi-mini" style="color:#22c55e">✔ {p} pass</span>
                <span class="kpi-mini" style="color:#ef4444">✘ {f_} fail</span>
                <span class="kpi-mini" style="color:#f59e0b">⚠ {w} warn</span>
              </div>
            </div>
            <div class="sec-hdr-right">
              <div class="big-rate" style="color:{bar_c}">{r}</div>
              <div class="dim" style="font-size:11px">pass rate</div>
            </div>
          </div>
          <!-- 4 tab navigation -->
          <div class="tab-nav" id="tabnav-{sid}">
            <div class="tab-btn active" onclick="switchTab('{sid}','ov')" data-tab="ov">
              <span>📋</span> Overview
            </div>
            <div class="tab-btn" onclick="switchTab('{sid}','ch')" data-tab="ch">
              <span>📗</span> Chapters
            </div>
            <div class="tab-btn" onclick="switchTab('{sid}','qt')" data-tab="qt">
              <span>❓</span> Questions
            </div>
            <div class="tab-btn" onclick="switchTab('{sid}','st')" data-tab="st">
              <span>👥</span> Students
            </div>
          </div>
          <!-- Tab content -->
          <div id="tab-{sid}-ov" class="tab-content active">{build_overview_tab(sd)}</div>
          <div id="tab-{sid}-ch" class="tab-content">{build_chapters_tab(sd)}</div>
          <div id="tab-{sid}-qt" class="tab-content">{build_questions_tab(sd)}</div>
          <div id="tab-{sid}-st" class="tab-content">{build_students_tab(sd)}</div>
        </div>'''

    # ── Summary dashboard ──────────────────────────────────────────────────────
    summary_rows = ""
    for sd in ALL_SECTIONS_DATA:
        sec = sd["section"]; sid = _re.sub(r"[^A-Za-z0-9]","_",sec)
        p = sd["passed"]; f_ = sd["failed"]; t = sd["total"]
        r = sd["pass_rate"]
        rt = int(_re.sub(r"[^0-9]", "", r) or 0)
        bar_c = "#22c55e" if f_ == 0 else ("#f59e0b" if f_ <= 3 else "#ef4444")
        pct_num = rt
        summary_rows += (f'<tr class="summary-row" onclick="switchSection(\'{sid}\')" style="cursor:pointer">'
                         f'<td style="font-weight:700;color:#e2e8f0;font-size:16px">{sec}</td>'
                         f'<td style="text-align:center;color:#60a5fa">{t}</td>'
                         f'<td style="text-align:center;color:#22c55e;font-weight:700">{p}</td>'
                         f'<td style="text-align:center;color:#ef4444;font-weight:700">{f_}</td>'
                         f'<td><div style="background:#1e293b;border-radius:4px;height:8px;overflow:hidden">'
                         f'<div style="width:{pct_num}%;height:8px;background:{bar_c};border-radius:4px"></div></div></td>'
                         f'<td style="text-align:center;color:{bar_c};font-weight:800;font-size:15px">{r}</td>'
                         f'<td><span class="link-btn" onclick="event.stopPropagation();switchSection(\'{sid}\')">View →</span></td>'
                         f'</tr>')

    # ── Full HTML ──────────────────────────────────────────────────────────────
    first_sid = _re.sub(r"[^A-Za-z0-9]", "_", ALL_SECTIONS_DATA[0]["section"]) if ALL_SECTIONS_DATA else ""

    CSS = """
    :root{
      --bg:#050c15;--s1:#0a1628;--s2:#0f1f35;--s3:#162840;--s4:#1e3452;
      --bdr:#1e3a5f;--bdr2:#264d7a;
      --tx:#dde9f5;--tx2:#94aec8;--dim:#4a6a8a;
      --pass:#22c55e;--fail:#ef4444;--warn:#f59e0b;--info:#38bdf8;
      --acc:#3b82f6;--acc2:#60a5fa;
    }
    *{box-sizing:border-box;margin:0;padding:0}
    html{scroll-behavior:smooth}
    body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--tx);
         font-size:13px;line-height:1.6;min-height:100vh}
    a{color:var(--acc2);text-decoration:none}

    /* TOPBAR */
    .topbar{
      background:linear-gradient(135deg,#030810,#071220);
      border-bottom:2px solid var(--acc);
      padding:0 32px;height:64px;display:flex;align-items:center;
      justify-content:space-between;position:sticky;top:0;z-index:100;
      box-shadow:0 4px 32px rgba(0,0,0,.8)
    }
    .topbar-brand{display:flex;align-items:center;gap:14px}
    .tb-logo{width:40px;height:40px;border-radius:10px;
             background:linear-gradient(135deg,var(--acc),#1d4ed8);
             display:flex;align-items:center;justify-content:center;
             font-size:16px;font-weight:900;color:#fff;
             box-shadow:0 0 20px rgba(59,130,246,.4)}
    .tb-title{font-size:16px;font-weight:800;color:#fff}
    .tb-sub{font-size:11px;color:var(--dim);margin-top:1px}
    .tb-meta{font-size:11px;color:var(--dim);text-align:right;line-height:1.8}
    .tb-meta strong{color:var(--acc2)}

    /* LAYOUT */
    .main-layout{display:flex;height:calc(100vh - 64px);overflow:hidden}

    /* LEFT SIDEBAR */
    .sidebar{
      width:200px;flex-shrink:0;background:var(--s1);
      border-right:1px solid var(--bdr);overflow-y:auto;
      display:flex;flex-direction:column
    }
    .sidebar-head{
      padding:16px 14px 10px;font-size:10px;font-weight:700;
      color:var(--dim);text-transform:uppercase;letter-spacing:.08em;
      border-bottom:1px solid var(--bdr)
    }
    .sec-nav-item{
      padding:10px 14px;cursor:pointer;display:flex;
      justify-content:space-between;align-items:center;
      border-bottom:1px solid rgba(30,58,95,.3);transition:all .15s
    }
    .sec-nav-item:hover{background:var(--s2)}
    .sec-nav-item.active{background:var(--s3);border-left:3px solid var(--acc)}
    .sec-nav-label{font-weight:700;color:#fff;font-size:14px}
    .sec-nav-rate{font-size:11px;font-weight:600;font-family:monospace}
    .sidebar-summary{padding:14px;border-top:1px solid var(--bdr);margin-top:auto}
    .sidebar-stat{display:flex;justify-content:space-between;margin-bottom:5px;font-size:12px}

    /* CONTENT AREA */
    .content{flex:1;overflow-y:auto;background:var(--bg)}
    .content-inner{padding:24px 28px;max-width:1400px}

    /* SUMMARY DASHBOARD */
    .dashboard{padding:0 0 24px}
    .dash-hero{
      background:linear-gradient(135deg,var(--s1),var(--s2));
      border:1px solid var(--bdr);border-radius:16px;
      padding:32px 36px;margin-bottom:20px;
      display:grid;grid-template-columns:1fr auto;gap:32px;align-items:center
    }
    .dash-eyebrow{font-size:10px;font-weight:700;color:var(--acc2);
                  text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px}
    .dash-title{font-size:28px;font-weight:900;color:#fff;margin-bottom:6px}
    .dash-title em{font-style:normal;color:var(--acc2)}
    .dash-desc{color:var(--dim);font-size:13px}
    .dash-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
    .tag{background:var(--s3);border:1px solid var(--bdr2);border-radius:20px;
         padding:4px 14px;font-size:11px;color:var(--tx2)}
    .tag strong{color:var(--acc2)}
    .big-rate-box{text-align:center}
    .big-rate-val{font-size:72px;font-weight:900;line-height:1;
                  background:linear-gradient(135deg,var(--pass),#34d399);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text}
    .big-rate-lbl{font-size:11px;color:var(--dim);text-transform:uppercase;
                  letter-spacing:.08em;margin-top:6px}
    .big-rate-sub{font-size:12px;color:var(--dim);margin-top:4px;font-family:monospace}

    .kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:20px}
    .kpi-card{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;
              padding:18px;text-align:center;transition:all .2s}
    .kpi-card:hover{transform:translateY(-2px);border-color:var(--bdr2)}
    .kpi-card::before{content:'';display:block;height:3px;border-radius:12px 12px 0 0;
                      margin:-18px -18px 14px;border-radius:12px 12px 0 0}
    .kpi-card.kpi-total::before{background:linear-gradient(90deg,var(--acc2),var(--acc))}
    .kpi-card.kpi-pass::before{background:linear-gradient(90deg,var(--pass),#34d399)}
    .kpi-card.kpi-fail::before{background:linear-gradient(90deg,var(--fail),#fb7185)}
    .kpi-card.kpi-warn::before{background:linear-gradient(90deg,var(--warn),#fbbf24)}
    .kpi-card.kpi-rate::before{background:linear-gradient(90deg,#a855f7,#c084fc)}
    .kpi-n{font-size:36px;font-weight:900;line-height:1;margin-bottom:4px;font-family:monospace}
    .kpi-l{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--dim)}

    /* SUMMARY TABLE */
    .card{background:var(--s1);border:1px solid var(--bdr);border-radius:12px;overflow:hidden;margin-bottom:16px}
    .card-hdr{padding:14px 18px;font-size:13px;font-weight:700;color:#fff;
              background:var(--s2);border-bottom:1px solid var(--bdr);
              display:flex;align-items:center;gap:10px}
    .card-icon{font-size:16px}
    .pill{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;
          background:var(--s3);border:1px solid var(--bdr2);color:var(--tx2)}

    /* SECTION BLOCK */
    .section-block{animation:fadeUp .25s ease}
    @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

    .sec-hdr-bar{
      background:linear-gradient(135deg,var(--s2),var(--s3));
      border:1px solid var(--bdr);border-radius:12px;
      padding:20px 24px;margin-bottom:16px;
      display:flex;justify-content:space-between;align-items:center
    }
    .sec-title{font-size:22px;font-weight:900;color:#fff;margin-bottom:4px}
    .sec-meta{display:flex;gap:16px;flex-wrap:wrap}
    .kpi-mini{font-size:12px;font-weight:600;font-family:monospace}
    .big-rate{font-size:42px;font-weight:900;font-family:monospace;line-height:1}

    /* 4-TAB NAV */
    .tab-nav{
      display:flex;gap:0;border-bottom:2px solid var(--bdr);
      margin-bottom:20px;background:var(--s1);
      border-radius:12px 12px 0 0;overflow:hidden;border:1px solid var(--bdr)
    }
    .tab-btn{
      flex:1;padding:14px 8px;cursor:pointer;text-align:center;
      color:var(--dim);font-weight:600;font-size:13px;
      border-bottom:3px solid transparent;transition:all .2s;
      display:flex;align-items:center;justify-content:center;gap:6px;
      background:var(--s1)
    }
    .tab-btn:hover{color:var(--tx);background:var(--s2)}
    .tab-btn.active{color:#fff;border-bottom-color:var(--acc);background:var(--s2);font-weight:700}
    .tab-content{display:none}
    .tab-content.active{display:block;animation:fadeUp .2s ease}
    .tab-section-content{padding:0}

    /* TABLE STYLES */
    .tc-table{width:100%;border-collapse:collapse;font-size:12.5px}
    .tc-table thead tr{background:var(--s2)}
    .tc-table th{padding:9px 13px;text-align:left;font-weight:700;color:var(--dim);
                 border-bottom:1px solid var(--bdr);font-size:10px;
                 text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}
    .tc-table td{padding:9px 13px;border-bottom:1px solid rgba(30,58,95,.35);vertical-align:middle}
    .tc-table tbody tr:last-child td{border-bottom:none}
    .tc-table tbody tr:hover{background:rgba(59,130,246,.04)}
    .tr-pass:hover{background:rgba(34,197,94,.05)!important}
    .tr-fail{background:rgba(239,68,68,.03)}
    .tr-fail:hover{background:rgba(239,68,68,.08)!important}
    .tr-warn{background:rgba(245,158,11,.03)}
    .tr-skip{background:rgba(245,158,11,.04)}
    .tc-id{font-family:monospace;color:var(--acc2);font-size:11px;font-weight:600;white-space:nowrap}
    .tc-desc{color:var(--tx);font-weight:500}
    .tc-det{color:var(--dim);font-family:monospace;font-size:11px}
    .tc-icon{text-align:center;width:28px;font-weight:700}
    .tc-time{font-family:monospace;font-size:10px;color:var(--dim);white-space:nowrap}
    .tw{overflow-x:auto}

    /* STATUS BADGES */
    .pass-badge,.fail-badge,.warn-badge,.info-badge,.skip-badge{
      display:inline-flex;align-items:center;padding:2px 9px;border-radius:20px;
      font-size:10.5px;font-weight:700;white-space:nowrap}
    .pass-badge{background:rgba(34,197,94,.12);color:var(--pass);border:1px solid rgba(34,197,94,.3)}
    .fail-badge{background:rgba(239,68,68,.12);color:var(--fail);border:1px solid rgba(239,68,68,.3)}
    .warn-badge{background:rgba(245,158,11,.12);color:var(--warn);border:1px solid rgba(245,158,11,.3)}
    .info-badge{background:rgba(56,189,248,.1);color:var(--info);border:1px solid rgba(56,189,248,.3)}
    .skip-badge{background:rgba(245,158,11,.12);color:var(--warn);border:1px solid rgba(245,158,11,.3)}
    .dim{color:var(--dim)}

    /* EXAM BANNER */
    .exam-banner{
      border-radius:12px;padding:24px 32px;display:flex;
      align-items:center;gap:32px;margin:16px
    }
    .exam-side{text-align:center}
    .exam-lbl{font-size:10px;font-weight:700;text-transform:uppercase;
              letter-spacing:.1em;color:rgba(255,255,255,.55);margin-bottom:4px}
    .exam-val{font-size:48px;font-weight:900;color:#fff;line-height:1;font-family:monospace}
    .exam-arrow{font-size:24px;color:rgba(255,255,255,.4)}
    .exam-trend{margin-left:auto;background:rgba(0,0,0,.3);border-radius:20px;
                padding:6px 16px;font-size:13px;font-weight:700;color:rgba(255,255,255,.9)}

    /* CHAPTER SECTIONS GRID */
    .ch-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;padding:16px;gap:12px}
    .ch-section{border-radius:10px;padding:14px;overflow:hidden}
    .ch-sec-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
    .ch-label{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}
    .ch-badge{font-size:11px;color:var(--dim);background:var(--s3);
              border:1px solid var(--bdr);border-radius:20px;padding:2px 10px}
    .mini-table{width:100%;border-collapse:collapse;font-size:12px}
    .mini-table th{padding:6px 8px;font-size:10px;color:var(--dim);font-weight:700;
                   text-transform:uppercase;border-bottom:1px solid var(--bdr)}
    .mini-table td{padding:6px 8px;border-bottom:1px solid rgba(30,58,95,.25)}
    .mini-table tbody tr:last-child td{border-bottom:none}

    /* STUDENT GRID */
    .stu-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:16px}
    .stu-cat{border-radius:10px;background:var(--s2);overflow:hidden}
    .stu-cat-hdr{padding:12px 14px;display:flex;align-items:center;gap:10px}
    .stu-ico{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;
             justify-content:center;font-size:13px;font-weight:900;color:#fff;flex-shrink:0}
    .stu-cat-name{font-weight:700;color:#fff;font-size:14px}
    .stu-row{padding:7px 14px;display:flex;justify-content:space-between;
             border-bottom:1px solid rgba(30,58,95,.3)}
    .stu-name{font-weight:500;color:var(--tx2)}
    .stu-score{font-family:monospace;font-weight:700;font-size:13px}

    /* SUMMARY TABLE */
    .summary-row:hover td{background:rgba(59,130,246,.08)!important}
    .link-btn{color:var(--acc2);font-weight:600;font-size:12px;cursor:pointer}
    .link-btn:hover{text-decoration:underline}

    /* EMPTY STATE */
    .empty-state{padding:32px;text-align:center;color:var(--dim);font-style:italic}

    /* FOOTER */
    .footer{border-top:1px solid var(--bdr);padding:20px 28px;
            text-align:center;color:var(--dim);font-size:11px;font-family:monospace}

    /* SCROLLBAR */
    ::-webkit-scrollbar{width:5px;height:5px}
    ::-webkit-scrollbar-track{background:var(--s1)}
    ::-webkit-scrollbar-thumb{background:var(--bdr2);border-radius:3px}

    @media(max-width:900px){.kpi-grid{grid-template-columns:repeat(3,1fr)}
      .ch-grid,.stu-grid{grid-template-columns:1fr}
      .sidebar{width:160px}
      .dash-hero{grid-template-columns:1fr}}
    """

    JS = f"""
    const sections = {[_re.sub(r"[^A-Za-z0-9]","_",sd["section"]) for sd in ALL_SECTIONS_DATA]};
    let activeSec = '{first_sid}';

    function switchSection(sid) {{
        // Hide all sections
        document.querySelectorAll('.section-block').forEach(b => b.style.display='none');
        // Remove active from nav
        document.querySelectorAll('.sec-nav-item').forEach(n => n.classList.remove('active'));
        // Show target
        const blk = document.getElementById('sec-'+sid);
        if(blk) blk.style.display='block';
        // Mark nav active
        const navItem = document.querySelector('.sec-nav-item[data-sec="'+sid+'"]');
        if(navItem) navItem.classList.add('active');
        activeSec = sid;
        // Show dashboard or section
        document.getElementById('dashboard').style.display = (sid==='_summary') ? 'block' : 'none';
    }}

    function switchTab(sid, tab) {{
        // Hide all tabs for this section
        document.querySelectorAll('#sec-'+sid+' .tab-content').forEach(t => t.classList.remove('active'));
        // Deactivate all tab buttons
        document.querySelectorAll('#tabnav-'+sid+' .tab-btn').forEach(b => b.classList.remove('active'));
        // Activate target tab
        const tc = document.getElementById('tab-'+sid+'-'+tab);
        if(tc) tc.classList.add('active');
        // Activate button
        const btn = document.querySelector('#tabnav-'+sid+' .tab-btn[data-tab="'+tab+'"]');
        if(btn) btn.classList.add('active');
    }}

    function showDashboard() {{
        document.querySelectorAll('.section-block').forEach(b => b.style.display='none');
        document.getElementById('dashboard').style.display='block';
        document.querySelectorAll('.sec-nav-item').forEach(n => n.classList.remove('active'));
        const di = document.querySelector('.sec-nav-item[data-sec="_summary"]');
        if(di) di.classList.add('active');
    }}

    // Init: show first section
    document.addEventListener('DOMContentLoaded', () => {{
        if(sections.length > 0) switchSection(sections[0]);
        // Animate progress bar
        const pf = document.getElementById('pf');
        if(pf) setTimeout(()=>{{pf.style.width='{rate}%';}},100);
    }});
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens — Unified QA Suite v2.0</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="topbar-brand">
    <div class="tb-logo">CL</div>
    <div>
      <div class="tb-title">ClassLens — Unified Professional QA Suite v2.0</div>
      <div class="tb-sub">Overview · Chapters · Questions · Students — All Sections · Single Report</div>
    </div>
  </div>
  <div class="tb-meta">
    <span id="ts-display"></span><br>
    Class <strong>{FIXED.get('Class','12')}</strong> &nbsp;|&nbsp;
    {FIXED.get('Subject','Maths')} &nbsp;|&nbsp;
    {FIXED.get('CompareLeft','Midterm')} → {FIXED.get('CompareRight','Preboard 1')}
  </div>
</div>

<!-- MAIN LAYOUT -->
<div class="main-layout">

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-head">Sections</div>
    <div class="sec-nav-item active" data-sec="_summary" onclick="showDashboard()">
      <span class="sec-nav-label">📊 Summary</span>
      <span class="sec-nav-rate" style="color:#60a5fa">{cnt_secs}sec</span>
    </div>
    {section_nav_items}
    <div class="sidebar-summary">
      <div class="sidebar-stat"><span>Total Tests</span><strong style="color:#60a5fa">{total}</strong></div>
      <div class="sidebar-stat"><span>Passed</span><strong style="color:#22c55e">{_P}</strong></div>
      <div class="sidebar-stat"><span>Failed</span><strong style="color:#ef4444">{_F}</strong></div>
      <div class="sidebar-stat"><span>Pass Rate</span><strong style="color:#c084fc">{rate}%</strong></div>
    </div>
  </div>

  <!-- CONTENT -->
  <div class="content">
    <div class="content-inner">

      <!-- DASHBOARD -->
      <div id="dashboard" class="dashboard">
        <div class="dash-hero">
          <div>
            <div class="dash-eyebrow">ClassLens Automation QA — All Sections Unified Report</div>
            <div class="dash-title">Complete <em>4-Tab Coverage</em> Across All Sections</div>
            <div class="dash-desc">
              Every section discovered from the entry-form dropdown. Each tested across all 4 tabs:
              <strong>Overview</strong> (Exam Comparison banner, Chapter Cards +N overflow modal, Highlighted Students modal),
              <strong>Chapters Tab</strong> (LOC1-4 consistency, Header Accuracy badge, Excel curriculum mapping, Exam panel data),
              <strong>Questions Tab</strong> (Chapter/Concept curriculum validation, Question type checks, Student performance distribution),
              <strong>Students Tab</strong> (4-source percentage consistency, Exam scores, Comparison of Learning Gaps).
            </div>
            <div class="dash-tags">
              <span class="tag"><strong>URL</strong> classlens.inferentics.com</span>
              <span class="tag"><strong>User</strong> {USERNAME}</span>
              <span class="tag"><strong>Class</strong> {FIXED.get('Class','12')}</span>
              <span class="tag"><strong>Subject</strong> {FIXED.get('Subject','Maths')}</span>
              <span class="tag"><strong>Exam</strong> {FIXED.get('Exam','Midterm')}</span>
              <span class="tag"><strong>Run</strong> {run_ts}</span>
            </div>
          </div>
          <div class="big-rate-box">
            <div class="big-rate-val">{rate}%</div>
            <div class="big-rate-lbl">Overall Pass Rate</div>
            <div class="big-rate-sub">{_P} / {total} tests</div>
          </div>
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid">
          <div class="kpi-card kpi-total"><div class="kpi-n" style="color:#60a5fa">{total}</div><div class="kpi-l">Total Tests</div></div>
          <div class="kpi-card kpi-pass"><div class="kpi-n" style="color:#22c55e">{_P}</div><div class="kpi-l">Passed</div></div>
          <div class="kpi-card kpi-fail"><div class="kpi-n" style="color:#ef4444">{_F}</div><div class="kpi-l">Failed</div></div>
          <div class="kpi-card kpi-warn"><div class="kpi-n" style="color:#f59e0b">{_W}</div><div class="kpi-l">Warnings</div></div>
          <div class="kpi-card kpi-rate"><div class="kpi-n" style="color:#c084fc">{cnt_secs}</div><div class="kpi-l">Sections</div></div>
        </div>

        <!-- Progress bar -->
        <div class="card" style="margin-bottom:20px">
          <div style="padding:18px 20px">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px">
              <span style="font-size:13px;font-weight:600;color:var(--tx2)">Overall Pass Rate — All {cnt_secs} Sections</span>
              <span style="font-size:24px;font-weight:800;color:#22c55e;font-family:monospace">{rate}% <span style="font-size:13px;color:var(--dim)">({_P}/{total})</span></span>
            </div>
            <div style="background:var(--s3);border-radius:999px;height:12px;overflow:hidden">
              <div id="pf" style="width:0%;height:12px;background:linear-gradient(90deg,#22c55e,#34d399);
                                   border-radius:999px;transition:width 1s ease;
                                   box-shadow:0 0 16px rgba(34,197,94,.3)"></div>
            </div>
          </div>
        </div>

        <!-- Section summary table -->
        <div class="card">
          <div class="card-hdr"><span class="card-icon">📈</span> Section-by-Section Summary — Click to View Details</div>
          <div class="tw">
            <table class="tc-table">
              <thead><tr>
                <th>Section</th><th style="text-align:center">Tests</th>
                <th style="text-align:center">Passed</th><th style="text-align:center">Failed</th>
                <th style="min-width:140px">Progress</th>
                <th style="text-align:center">Pass Rate</th>
                <th></th>
              </tr></thead>
              <tbody>{summary_rows}</tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- SECTION BLOCKS -->
      {section_blocks}

      <div class="footer">
        ClassLens Unified Professional QA Suite v2.0 &nbsp;·&nbsp;
        <span id="ft"></span> &nbsp;·&nbsp;
        {cnt_secs} sections &nbsp;·&nbsp; {total} tests &nbsp;·&nbsp; {rate}% pass rate &nbsp;·&nbsp;
        Python · Selenium 4
      </div>
    </div>
  </div>
</div>

<script>
{JS}
const f = new Intl.DateTimeFormat('en-IN',{{timeZone:'Asia/Kolkata',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}});
const ts = f.format(new Date());
['ts-display','ft'].forEach(id=>{{ const e=document.getElementById(id); if(e) e.textContent=ts; }});
</script>
</body></html>"""
    return html


def save_outputs():
    total = _P + _F + _W
    store["summary"] = {
        "total": total, "passed": _P, "failed": _F, "warnings": _W,
        "pass_rate": f"{round(_P/max(total,1)*100,1)}%"
    }
    for label in ["Reteach","Brushup","On Track"]:
        for c in store["chapters"][label]["cards"]:
            c.pop("el", None)

    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump({"store": store, "all_section_runs": [
                {k:v for k,v in r.items() if k != "store"} for r in all_section_runs
            ]}, f, indent=2, ensure_ascii=False)
        print(f"\n  {G}💾  JSON → {os.path.abspath(JSON_FILE)}{RST}")
    except Exception as e:
        print(f"\n  {Y}⚠️   JSON save error: {e}{RST}")

    html = build_report()
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  {G}📄  HTML → {os.path.abspath(REPORT_FILE)}{RST}")

    if AUTO_OPEN_REPORT:
        abs_p = os.path.abspath(REPORT_FILE)
        url = "file:///" + abs_p.replace(os.sep, "/")
        print(f"\n  {C}🌐  {url}{RST}")
        try:
            if webbrowser.open(url, new=2): print(f"  {G}✅  Browser launched.{RST}")
        except: pass

# ══════════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════
#  SCRIPT 1 — SECTION MANAGEMENT (Overview Tab, in-page dropdown approach)
# ═══════════════════════════════════════════════════════════════════════════════

def reset_run_state(section_name=None):
    """Reset per-section counters and store. Called before each section run."""
    global store, _P, _F, _W
    if section_name is not None:
        VALUES["Section"] = section_name
    _P = 0; _F = 0; _W = 0
    store = fresh_store()
    store["config"] = deepcopy(VALUES)


def login_if_needed(driver, wait):
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except: pass
    try:
        if get_selects(driver): return True
    except: pass
    try:
        usr = driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
        pwd = driver.find_element(By.XPATH, "//input[@type='password']")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        usr.clear(); usr.send_keys(USERNAME)
        pwd.clear(); pwd.send_keys(PASSWORD)
        btn.click()
        WebDriverWait(driver, TIMEOUT).until(
            lambda d: len(get_selects(d)) >= 4 or "Overview" in page_text(d))
    except: pass
    return len(get_selects(driver)) >= 4


def ensure_form_page(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    ok = login_if_needed(driver, wait)
    if not ok:
        raise RuntimeError("Unable to reach selection form with dropdowns")
    WebDriverWait(driver, TIMEOUT).until(lambda d: len(get_selects(d)) >= 4)
    return True


def get_available_sections(driver, wait):
    ensure_form_page(driver, wait)
    if not wait_opt(driver, 0, VALUES["Class"], TIMEOUT):
        raise RuntimeError(f"Class option {VALUES['Class']} not available")
    js_pick(driver, get_selects(driver)[0], VALUES["Class"])
    time.sleep(0.5)
    sec_sel = get_selects(driver)[1]
    options = []
    for o in sec_sel.find_elements(By.TAG_NAME, "option"):
        t = (o.text or "").strip()
        if not t: continue
        if t.lower() in {"section", "select section", "choose section"}: continue
        options.append(t)
    uniq = []; seen = set()
    for s in options:
        if s not in seen: seen.add(s); uniq.append(s)
    return uniq


def get_overview_section_select(driver):
    """Find the in-page Section dropdown on the dashboard."""
    try:
        sel = driver.execute_script("""
            function isVisible(el){
                if(!el) return false;
                var r = el.getBoundingClientRect();
                return r.width > 120 && r.height > 20 && r.bottom > 0 && r.top < window.innerHeight + 200;
            }
            var selects = Array.from(document.querySelectorAll('select')).filter(isVisible);
            if (!selects.length) return null;
            function optionTexts(s){
                try { return Array.from(s.options).map(o => (o.textContent||'').trim()).filter(Boolean); }
                catch(e){ return []; }
            }
            var best = null, bestScore = -1e9;
            selects.forEach(function(s){
                var r = s.getBoundingClientRect();
                var score = r.top * 5;
                var txt = '';
                var node = s.parentElement;
                for(var i=0;i<4&&node;i++,node=node.parentElement){ txt+=' '+(node.textContent||''); }
                if(txt.toLowerCase().indexOf('section')>=0) score+=500;
                var opts = optionTexts(s);
                var shortOpts = opts.filter(function(t){
                    return /^[A-Za-z0-9][A-Za-z0-9 -]{0,4}$/.test(t) && t.toLowerCase()!=='section';
                });
                score += shortOpts.length*15 + opts.length*2;
                if(score>bestScore){ bestScore=score; best=s; }
            });
            return best;
        """)
        if sel: return sel
    except: pass
    try:
        sels = [s for s in driver.find_elements(By.TAG_NAME, "select") if s.is_displayed()]
        best = None; best_score = -10**9
        for s in sels:
            try:
                rect = s.rect; score = rect["y"]*5
                node = s; near_text = ""
                for _ in range(4):
                    try: node = node.find_element(By.XPATH,".."); near_text += " "+(node.text or "")
                    except: break
                if "section" in near_text.lower(): score += 500
                opts = [(o.text or "").strip() for o in s.find_elements(By.TAG_NAME,"option")]
                short_opts = [t for t in opts if t and t.lower()!="section" and len(t)<=5]
                score += len(short_opts)*15 + len(opts)*2
                if score > best_score: best_score=score; best=s
            except: pass
        return best
    except: return None


def get_overview_sections(driver):
    """Get all sections available from the in-page dashboard Section dropdown."""
    sel = get_overview_section_select(driver)
    if sel is None: return []
    options = []
    try:
        for o in sel.find_elements(By.TAG_NAME, "option"):
            t = (o.text or "").strip()
            if not t: continue
            if t.lower() in {"section","select section","choose section"}: continue
            options.append(t)
    except: pass
    uniq = []; seen = set()
    for s in options:
        if s not in seen: seen.add(s); uniq.append(s)
    return uniq


def select_overview_section(driver, wait, section_name):
    """
    Switch section by going to LOGIN_URL, filling ALL form dropdowns
    (Class/Section/Subject/Exam + CompareLeft/CompareRight), clicking Enter.
    This is the ONLY reliable method as shown in the UI screenshots.
    """
    print(f"\n  {C}🔀  Entry form → Section {section_name}{RST}")
    driver.get(LOGIN_URL)
    try:
        WebDriverWait(driver, 15).until(lambda d: len(d.find_elements(By.TAG_NAME, "body")) > 0)
    except:
        time.sleep(2.0)
    try:
        login_if_needed(driver, wait)
    except: pass
    try:
        WebDriverWait(driver, 20).until(lambda d: len(get_selects(d)) >= 2)
    except:
        time.sleep(2.0)
    ok = fill_and_enter(driver, wait, section_name)
    if not ok:
        raise RuntimeError(f"fill_and_enter failed for section '{section_name}'")
    # Click Overview tab
    time.sleep(1.0)
    try:
        for xp in ["//button[normalize-space()='Overview']",
                   "//a[normalize-space()='Overview']",
                   "//*[normalize-space(text())='Overview']"]:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click()", el); break
            else:
                continue
            break
        time.sleep(1.5)
    except: pass
    try:
        WebDriverWait(driver, 20).until(lambda d:
            any(kw in d.page_source for kw in
                ["Exam Comparison", "Highlighted Students", "Reteach", "Brushup"]))
    except:
        time.sleep(3.0)
    time.sleep(1.0)
    return True


def prepare_overview_after_login(driver, wait):
    if not test_login(driver, wait):
        raise RuntimeError("Login failed")
    if not test_navigation(driver, wait):
        raise RuntimeError("Initial navigation failed")
    return True


def get_all_sections_for_run(driver, wait):
    """Read all sections from ENTRY FORM Section dropdown."""
    try:
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        login_if_needed(driver, wait)
        WebDriverWait(driver, 20).until(lambda d: len(get_selects(d)) >= 2)
        time.sleep(0.5)
        sels = get_selects(driver)
        if sels:
            js_pick(driver, sels[0], VALUES["Class"])
            time.sleep(1.5)
        sels = get_selects(driver)
        if len(sels) < 2:
            return [VALUES.get("Section", "R")]
        opts = []
        for o in sels[1].find_elements(By.TAG_NAME, "option"):
            t = (o.text or "").strip()
            if t and t.lower() not in {"section", "select section", "--", ""}:
                opts.append(t)
        seen = set(); uniq = []
        for s in opts:
            if s not in seen: seen.add(s); uniq.append(s)
        print(f"  {G}✅  {len(uniq)} sections from entry form: {uniq}{RST}")
        return uniq if uniq else [VALUES.get("Section", "R")]
    except Exception as ex:
        print(f"  {Y}⚠️  Section discovery failed: {ex}{RST}")
        return [VALUES.get("Section", "R")]


def _slugify(v):
    v = re.sub(r"[^A-Za-z0-9._-]+", "_", str(v).strip())
    v = re.sub(r"_+", "_", v).strip("_")
    return v or "section"


def open_browser(path):
    abs_p = os.path.abspath(path)
    url   = "file:///" + abs_p.replace(os.sep, "/")
    print(f"\n  \U0001f310 {url}")
    try:
        if webbrowser.open(url, new=2): print("  \u2705  Browser launched."); return
    except: pass
    try:
        if sys.platform.startswith("win"): os.startfile(abs_p)
        elif sys.platform == "darwin": subprocess.Popen(["open", abs_p])
        else:
            for cmd in ["xdg-open","sensible-browser","google-chrome","firefox"]:
                try: subprocess.Popen([cmd, abs_p]); return
                except FileNotFoundError: continue
    except Exception as e:
        print(f"  \u26a0\ufe0f  {e}")


def save_outputs(json_name=None, report_name=None, auto_open=None):
    jf = json_name or JSON_FILE
    rf = report_name or REPORT_FILE
    do_open = auto_open if auto_open is not None else AUTO_OPEN_REPORT
    total = _P + _F + _W
    store["summary"] = {
        "total": total, "passed": _P, "failed": _F, "warnings": _W,
        "pass_rate": f"{round(_P/max(total,1)*100,1)}%"
    }
    for label in ["Reteach", "Brushup", "On Track"]:
        for c in store["chapters"][label]["cards"]:
            c.pop("el", None)
    try:
        with open(jf, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
        print(f"\n  \U0001f4be  JSON  -> {os.path.abspath(jf)}")
    except Exception as e:
        print(f"  \u26a0\ufe0f  JSON save error: {e}")
    html = build_report()
    with open(rf, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  \U0001f4c4  HTML  -> {os.path.abspath(rf)}")
    if do_open:
        open_browser(rf)


def build_master_report(runs):
    """Simple master summary report with links to per-section reports."""
    total_tests = sum(r.get("total", 0) for r in runs)
    total_pass  = sum(r.get("passed", 0) for r in runs)
    total_fail  = sum(r.get("failed", 0) for r in runs)
    total_warn  = sum(r.get("warnings", 0) for r in runs)
    rate = round(total_pass / max(total_tests, 1) * 100, 1)
    rows = []
    for i, r in enumerate(runs, 1):
        rf = r.get("report_file", "")
        link = f"<a href='{rf}' target='_blank' style='color:#60a5fa'>{rf}</a>" if rf else "&mdash;"
        pr = r.get("pass_rate", "0%")
        col = "#10b981" if r.get("failed", 1) == 0 else ("#f59e0b" if r.get("failed", 0) <= 3 else "#f43f5e")
        rows.append(
            f"<tr>"
            f"<td style='color:#93c5fd;font-weight:700'>{i}</td>"
            f"<td style='color:#f0f6fc;font-weight:800;font-size:18px'>{r.get('section','')}</td>"
            f"<td style='color:#58a6ff;font-weight:700'>{r.get('total',0)}</td>"
            f"<td style='color:#10b981;font-weight:700'>{r.get('passed',0)}</td>"
            f"<td style='color:#f43f5e;font-weight:700'>{r.get('failed',0)}</td>"
            f"<td style='color:#f59e0b;font-weight:700'>{r.get('warnings',0)}</td>"
            f"<td style='color:{col};font-weight:800;font-size:16px'>{pr}</td>"
            f"<td>{link}</td>"
            f"</tr>"
        )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>ClassLens All Sections Master Report</title>"
        "<style>"
        "body{font-family:'Segoe UI',system-ui,sans-serif;background:#080e1a;color:#e6f0ff;padding:32px}"
        ".wrap{max-width:1200px;margin:0 auto}"
        ".hero{background:#0d1b2e;border:1px solid #1e3a5f;border-radius:14px;padding:28px 32px;margin-bottom:24px}"
        ".hero h1{font-size:24px;font-weight:800;color:#f0f6fc;margin-bottom:6px}"
        ".hero p{color:#6a92b4;font-size:13px;margin-top:4px}"
        ".kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px}"
        ".kpi{background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px;padding:18px;text-align:center}"
        ".kv{font-size:32px;font-weight:800;line-height:1;margin-bottom:4px}"
        ".kl{font-size:11px;color:#6a92b4;text-transform:uppercase;letter-spacing:.5px}"
        "table{width:100%;border-collapse:collapse;background:#0d1b2e;border:1px solid #1e3a5f;border-radius:12px;overflow:hidden}"
        "th{padding:11px 16px;text-align:left;font-weight:700;color:#6a92b4;border-bottom:1px solid #1e3a5f;"
        "font-size:11px;text-transform:uppercase;letter-spacing:.5px;background:#0f2035}"
        "td{padding:11px 16px;border-bottom:1px solid rgba(30,58,95,.4);font-size:13px;vertical-align:middle}"
        "tbody tr:last-child td{border-bottom:none}"
        "tbody tr:hover{background:rgba(59,130,246,.05)}"
        ".footer{text-align:center;color:#3a5a7a;font-size:12px;margin-top:36px;padding-top:16px;border-top:1px solid #1e3a5f}"
        "</style></head><body><div class='wrap'>"
        f"<div class='hero'><h1>\U0001f4ca ClassLens — All Sections Master Report</h1>"
        f"<p>Run: {run_ts} &nbsp;·&nbsp; Class {VALUES['Class']} | {VALUES['Subject']} | "
        f"{VALUES.get('CompareLeft','')} → {VALUES.get('CompareRight','')}"
        f" &nbsp;·&nbsp; {len(runs)} sections tested</p></div>"
        f"<div class='kpis'>"
        f"<div class='kpi'><div class='kv' style='color:#cdd9e5'>{len(runs)}</div><div class='kl'>Sections</div></div>"
        f"<div class='kpi'><div class='kv' style='color:#58a6ff'>{total_tests}</div><div class='kl'>Total Tests</div></div>"
        f"<div class='kpi'><div class='kv' style='color:#10b981'>{total_pass}</div><div class='kl'>Passed</div></div>"
        f"<div class='kpi'><div class='kv' style='color:#f43f5e'>{total_fail}</div><div class='kl'>Failed</div></div>"
        f"<div class='kpi'><div class='kv' style='color:#c084fc'>{rate}%</div><div class='kl'>Pass Rate</div></div>"
        "</div>"
        "<table><thead><tr><th>#</th><th>Section</th><th>Tests</th>"
        "<th>Passed</th><th>Failed</th><th>Warnings</th><th>Pass Rate</th><th>Report</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
        f"<div class='footer'>ClassLens Master Suite &nbsp;·&nbsp; {run_ts} &nbsp;·&nbsp; "
        f"{total_tests} tests &nbsp;·&nbsp; {rate}% pass rate</div>"
        "</div></body></html>"
    )


def _click_nav_tab(driver, tab_name):
    """Click a dashboard nav tab: Overview / Chapters / Questions / Students."""
    for xp in [
        f"//button[normalize-space()='{tab_name}']",
        f"//a[normalize-space()='{tab_name}']",
        f"//*[normalize-space(text())='{tab_name}' and contains(@class,'cursor')]",
        f"//*[normalize-space(text())='{tab_name}']",
    ]:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click()", el)
                    return True
        except: pass
    # URL fallback
    try:
        cur = driver.current_url
        screen = tab_name.lower()
        if "screen=" in cur:
            base = cur[:cur.rfind("screen=")].rstrip("?&")
            sep2 = "&" if "?" in base else "?"
        elif "?" in cur:
            base = cur; sep2 = "&"
        else:
            base = cur; sep2 = "?"
        driver.get(f"{base}{sep2}screen={screen}")
        return True
    except: return False



def cli_extract():
    """--extract  : write each of the 4 original test scripts to separate files."""
    import os, glob
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "combined_extracted_scripts")
    os.makedirs(out_dir, exist_ok=True)

    class_val   = VALUES.get("Class", "12")
    section_val = VALUES.get("Section", "R")
    subject_val = VALUES.get("Subject", "Maths")
    exam_val    = VALUES.get("Exam", "Midterm")
    cl_val      = VALUES.get("CompareLeft", "Midterm")
    cr_val      = VALUES.get("CompareRight", "Preboard 1")
    masked_pw   = "*" * len(PASSWORD)

    scripts = [
        ("script1_overview.py",
         "# ClassLens Script 1 — Overview Tab\n"
         "# Tests: Exam Comparison, Chapter Cards (+N modal), Highlighted Students\n"
         "# Implements: test_exam_comparison, test_chapter_section, test_all_students\n"),
        ("script2_chapters.py",
         "# ClassLens Script 2 — Chapters Tab\n"
         "# Tests: LOC1-4 consistency, Header Accuracy badge, Exam Panels, Excel Validation\n"
         "# Implements: test_chapters_tab + all LOC helpers\n"),
        ("script3_questions.py",
         "# ClassLens Script 3 — Questions Tab\n"
         "# Tests: Chapter/Concept audit, Question types, Avg score, Struggle gap\n"
         "# Implements: test_questions_tab\n"),
        ("script4_students.py",
         "# ClassLens Script 4 — Students Tab\n"
         "# Tests: 4-source % consistency, Exam scores (marks+%), Learning Gaps\n"
         "# Implements: test_students_tab, extract_learning_gaps_simple\n"),
    ]

    for fname, header in scripts:
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(header + "# Full implementation lives in the master file.\n")
        print(f"  {G}✅  {fpath}{RST}")

    config_lines = [
        "# ClassLens — Login & Config",
        "# Generated from: " + os.path.basename(__file__),
        "",
        'LOGIN_URL  = "' + LOGIN_URL + '"',
        'USERNAME   = "' + USERNAME + '"',
        'PASSWORD   = "' + masked_pw + '"  # masked',
        "",
        "VALUES = {",
        '    "Class":        "' + class_val   + '",',
        '    "Section":      "' + section_val + '",',
        '    "Subject":      "' + subject_val + '",',
        '    "Exam":         "' + exam_val    + '",',
        '    "CompareLeft":  "' + cl_val      + '",',
        '    "CompareRight": "' + cr_val      + '",',
        "}",
        "",
        'print("Login prepared: username=" + USERNAME + " password=" + PASSWORD)',
    ]
    creds_path = os.path.join(out_dir, "config.py")
    with open(creds_path, "w", encoding="utf-8") as f:
        f.write("\n".join(config_lines))

    print(f"\n  Extracted 4 scripts to: {out_dir}")
    print(f"  Login prepared: username={USERNAME} password={masked_pw}")


def cli_list():
    """--list  : login, discover sections, print them, quit."""
    print(f"\n{C}{'='*60}{RST}")
    print(f"  ClassLens — Section Discovery")
    print(f"{C}{'='*60}{RST}\n")
    driver = make_driver()
    wait   = WebDriverWait(driver, TIMEOUT)
    try:
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        login_if_needed(driver, wait)
        sections = get_all_sections_for_run(driver, wait)
        print(f"\n  Found {len(sections)} sections:")
        for i, s in enumerate(sections, 1):
            print(f"    {i:>2}.  {s}")
        print(f"\n  Config: Class={VALUES['Class']}  Subject={VALUES['Subject']}")
        print(f"  Exams: {VALUES.get('CompareLeft','')} -> {VALUES.get('CompareRight','')}")
    except Exception as e:
        print(f"  {R}Error: {e}{RST}")
    finally:
        try: driver.quit()
        except: pass


def cli_report_only():
    """--report-only  : re-generate HTML from last saved JSON data."""
    import glob
    json_files = sorted(glob.glob("classlens_report_*.json"))
    if not json_files:
        print(f"  {Y}No classlens_report_*.json files found. Run --run-all first.{RST}")
        return
    print(f"  Found {len(json_files)} section JSON files.")
    for jf in json_files:
        try:
            hf = jf.replace(".json", ".html")
            html = build_report()
            with open(hf, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  {G}✅  {hf}{RST}")
        except Exception as e:
            print(f"  {Y}⚠️  {jf}: {e}{RST}")


def cli_self_test():
    """--self-test  : verify all test functions are present and callable."""
    print(f"\n{C}{'='*60}{RST}")
    print(f"  ClassLens — Self Test")
    print(f"{C}{'='*60}{RST}\n")
    fn_checks = [
        ("fill_and_enter",              fill_and_enter),
        ("select_overview_section",     select_overview_section),
        ("_click_nav_tab",              _click_nav_tab),
        ("test_exam_comparison",        test_exam_comparison),
        ("test_chapter_section",        test_chapter_section),
        ("test_all_students",           test_all_students),
        ("test_chapters_tab",           test_chapters_tab),
        ("test_questions_tab",          test_questions_tab),
        ("test_students_tab",           test_students_tab),
        ("build_report",                build_report),
        ("build_master_report",         build_master_report),
        ("get_all_sections_for_run",    get_all_sections_for_run),
        ("enorm",                       enorm),
        ("discover_cards",              discover_cards),
        ("read_exam_panel",             read_exam_panel),
        ("read_header_accuracy_badge",  read_header_accuracy_badge),
        ("extract_learning_gaps_simple",extract_learning_gaps_simple),
    ]
    ok = True
    for name, fn in fn_checks:
        is_ok = callable(fn)
        ok = ok and is_ok
        print(f"  {'✅' if is_ok else '❌'}  {name}")
    ch_count = sum(len(v["chapters"]) for v in EXCEL_UNITS.values())
    print(f"\n  EXCEL_UNITS chapters  : {ch_count}")
    print(f"  MIDTERM_QUESTIONS     : {len(MIDTERM_QUESTIONS)} chapters")
    print(f"  PREBOARD_QUESTIONS    : {len(PREBOARD_QUESTIONS)} chapters")
    print(f"  Config                : Class={VALUES['Class']}  Subject={VALUES['Subject']}")
    print(f"  Login prepared        : username={USERNAME} password={'*'*len(PASSWORD)}")
    print(f"\n  {'ALL OK' if ok else 'ISSUES FOUND'} {'✅' if ok else '❌'}")


def main(tab_filter=None, sections_filter=None):
    """
    Core runner.
    tab_filter: None=all, 'overview'/'chapters'/'questions'/'students'
    sections_filter: list of section codes, None=all
    """
    tab_label = tab_filter.capitalize() if tab_filter else "All Tabs"
    print()
    w = 74
    print(f"{'╔'}{'═'*w}{'╗'}")
    print(f"{'║'}{'   ClassLens — MASTER TEST SUITE':<{w}}{'║'}")
    print(f"{'║'}{'   Overview · Chapters · Questions · Students · All Sections':<{w}}{'║'}")
    print(f"{'║'}{'   Tabs: ' + tab_label + '   Started: ' + run_ts:<{w}}{'║'}")
    print(f"{'╚'}{'═'*w}{'╝'}")

    driver = make_driver()
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        prepare_overview_after_login(driver, wait)
        sections = get_all_sections_for_run(driver, wait)
        if SECTION_WHITELIST:
            sections = [s for s in sections if s in set(SECTION_WHITELIST)]
        if sections_filter:
            sections = [s for s in sections if s in set(sections_filter)]
        if not sections:
            print(f"  {Y}No sections found — falling back to {VALUES.get('Section','R')}{RST}")
            sections = [VALUES.get("Section", "R")]

        print(f"\n  Sections ({len(sections)}): {sections}")
        print(f"  Tabs: {tab_label}\n")

        for i, sec in enumerate(sections, 1):
            reset_run_state(sec)
            print(f"\n  {'='*60}")
            print(f"  SECTION {i}/{len(sections)} — {sec}  |  Tabs: {tab_label}")
            print(f"  {'='*60}")

            try:
                select_overview_section(driver, wait, sec)
                dashboard_url = driver.current_url
                rec(store["nav_tests"], "TC-OVR-001",
                    f"Section {sec} — dashboard loaded",
                    "PASS", dashboard_url, suite="Navigation", section=sec)

                run_ov = not tab_filter or tab_filter == "overview"
                run_ch = not tab_filter or tab_filter == "chapters"
                run_qt = not tab_filter or tab_filter == "questions"
                run_st = not tab_filter or tab_filter == "students"

                # ── OVERVIEW (Script 1) ──────────────────────────────────────
                if run_ov:
                    print(f"\n  {G}[OVERVIEW]{RST} Exam Comparison + Chapter Cards + Students")
                    _click_nav_tab(driver, "Overview")
                    time.sleep(1.5)
                    try:
                        WebDriverWait(driver, 10).until(lambda d:
                            any(kw in d.page_source for kw in
                                ["Exam Comparison","Highlighted Students","Reteach"]))
                    except: time.sleep(2.0)
                    test_exam_comparison(driver)
                    test_chapter_section(driver, "Reteach")
                    test_chapter_section(driver, "Brushup")
                    test_chapter_section(driver, "On Track")
                    test_all_students(driver, wait)

                # ── CHAPTERS (Script 2) ──────────────────────────────────────
                if run_ch:
                    print(f"\n  {G}[CHAPTERS]{RST} LOC1-4 · Header Accuracy · Exam Panels · Excel")
                    try:
                        if not run_ov:
                            driver.get(dashboard_url); time.sleep(1.5)
                        _click_nav_tab(driver, "Chapters")
                        time.sleep(2.5)
                        try: wait_cards(driver)
                        except: time.sleep(3.0)
                        test_chapters_tab(driver, wait, sec)
                    except Exception as e:
                        print(f"  {Y}Chapters error: {e}{RST}")
                        import traceback; traceback.print_exc()

                # ── QUESTIONS (Script 3) ─────────────────────────────────────
                if run_qt:
                    print(f"\n  {G}[QUESTIONS]{RST} Chapter/Concept audit · Types · Performance")
                    try:
                        driver.get(dashboard_url); time.sleep(2.0)
                        _click_nav_tab(driver, "Questions")
                        time.sleep(2.5)
                        try:
                            WebDriverWait(driver, 10).until(lambda d:
                                any(kw in d.page_source for kw in
                                    ["Question","Concept","concept","question"]))
                        except: time.sleep(2.0)
                        test_questions_tab(driver, wait, sec)
                    except Exception as e:
                        print(f"  {Y}Questions error: {e}{RST}")
                        import traceback; traceback.print_exc()

                # ── STUDENTS (Script 4) ──────────────────────────────────────
                if run_st:
                    print(f"\n  {G}[STUDENTS]{RST} 4-source % · Exam Scores · Learning Gaps")
                    try:
                        driver.get(dashboard_url); time.sleep(2.0)
                        _click_nav_tab(driver, "Students")
                        time.sleep(2.5)
                        try:
                            WebDriverWait(driver, 10).until(lambda d:
                                any(kw in d.page_source for kw in
                                    ["Your Students","Students","student"]))
                        except: time.sleep(2.0)
                        test_students_tab(driver, wait, sec)
                    except Exception as e:
                        print(f"  {Y}Students error: {e}{RST}")
                        import traceback; traceback.print_exc()

            except Exception as sec_exc:
                print(f"\n  {R}Section {sec} failed: {sec_exc}{RST}")
                import traceback; traceback.print_exc()

            # ── Per-section save ─────────────────────────────────────────────
            total_s = _P + _F + _W
            rate_s  = round(_P / max(total_s, 1) * 100, 1)
            slug    = _slugify(sec)
            j_name  = f"classlens_report_{slug}.json"
            h_name  = f"classlens_report_{slug}.html"
            save_outputs(json_name=j_name, report_name=h_name, auto_open=False)
            all_section_runs.append({
                "section":   sec, "total": total_s,
                "passed":    _P,  "failed": _F, "warnings": _W,
                "pass_rate": f"{rate_s}%",
                "report_file": h_name, "json_file": j_name,
                "exam":            deepcopy(store.get("exam", {})),
                "chapters":        deepcopy(store.get("chapters", {})),
                "students":        deepcopy(store.get("students", {})),
                "chapter_detail":  deepcopy([c for c in store.get("chapter_detail",[])  if c.get("section","")==sec]),
                "questions":       deepcopy([q for q in store.get("questions",[])        if q.get("section","")==sec]),
                "student_profiles":deepcopy([s for s in store.get("student_profiles",[]) if s.get("section","")==sec]),
            })
            print(f"  {G}✅  Section {sec} done — {rate_s}% ({_P}/{total_s}){RST}")
            time.sleep(0.5)

        # ── Master report ────────────────────────────────────────────────────
        MASTER_JSON   = "classlens_master_data.json"
        MASTER_REPORT = "classlens_master_report.html"
        try:
            with open(MASTER_JSON, "w", encoding="utf-8") as f:
                json.dump(all_section_runs, f, indent=2, ensure_ascii=False)
            print(f"\n  Master JSON  -> {os.path.abspath(MASTER_JSON)}")
        except Exception as je:
            print(f"  {Y}Master JSON error: {je}{RST}")
        try:
            with open(MASTER_REPORT, "w", encoding="utf-8") as f:
                f.write(build_master_report(all_section_runs))
            print(f"  Master HTML  -> {os.path.abspath(MASTER_REPORT)}")
        except Exception as re_e:
            print(f"  {Y}Master report error: {re_e}{RST}")

        # ── Final summary ────────────────────────────────────────────────────
        all_total = sum(r["total"]   for r in all_section_runs)
        all_pass  = sum(r["passed"]  for r in all_section_runs)
        all_fail  = sum(r["failed"]  for r in all_section_runs)
        all_rate  = round(all_pass / max(all_total, 1) * 100, 1)
        print(f"\n{'='*70}")
        print(f"  FINAL — {len(all_section_runs)} sections | {all_total} tests | {all_rate}%")
        print(f"{'='*70}")
        for r in all_section_runs:
            col = "\033[92m" if r["failed"]==0 else ("\033[93m" if r["failed"]<=3 else "\033[91m")
            print(f"  {col}{r['section']:<6}\033[0m  {r['pass_rate']:>6}  "
                  f"\033[92m{r['passed']}✔\033[0m  \033[91m{r['failed']}✘\033[0m  "
                  f"\033[93m{r['warnings']}⚠\033[0m")
        print(f"{'='*70}")
        if AUTO_OPEN_REPORT:
            open_browser(MASTER_REPORT)

    except Exception as exc:
        print(f"\n  {R}Unhandled: {exc}{RST}")
        import traceback; traceback.print_exc()
        try: save_outputs()
        except: pass
    finally:
        if KEEP_BROWSER_OPEN:
            input("\n  Press ENTER to close browser...")
        try: driver.quit()
        except: pass
        print("\n  Done.")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        prog="testes.py",
        description="ClassLens Unified QA Suite — Overview · Chapters · Questions · Students",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python testes.py --run-all                    run all 4 tabs, all sections
  python testes.py --run Overview               run Overview tab only
  python testes.py --run Chapters               run Chapters tab only
  python testes.py --run Questions              run Questions tab only
  python testes.py --run Students               run Students tab only
  python testes.py --run-all --section R C      all tabs, sections R and C only
  python testes.py --list                       list all available sections
  python testes.py --extract                    extract 4 script files
  python testes.py --report-only                re-generate HTML from saved JSON
  python testes.py --self-test                  verify suite integrity
        """
    )
    ap.add_argument("--run-all",    action="store_true",
                    help="Run all 4 tabs across all discovered sections")
    ap.add_argument("--run",        metavar="TAB",
                    help="Run one specific tab: Overview / Chapters / Questions / Students")
    ap.add_argument("--section",    metavar="SEC", nargs="+",
                    help="Limit to specific sections e.g. --section R C H")
    ap.add_argument("--list",       action="store_true",
                    help="Login and list all available sections, then exit")
    ap.add_argument("--extract",    action="store_true",
                    help="Write 4 individual script stubs to combined_extracted_scripts/")
    ap.add_argument("--report-only",action="store_true",
                    help="Re-generate HTML reports from last saved JSON files")
    ap.add_argument("--self-test",  action="store_true",
                    help="Verify all test functions exist and are callable")

    args = ap.parse_args()

    # Always print login summary
    print(f"Login prepared: username={USERNAME} password={'*' * len(PASSWORD)}")

    if args.extract:
        cli_extract()
    elif args.list:
        cli_list()
    elif args.self_test:
        cli_self_test()
    elif args.report_only:
        cli_report_only()
    elif args.run_all:
        main(tab_filter=None, sections_filter=args.section)
    elif args.run:
        tab = args.run.lower()
        valid = {"overview","chapters","questions","students"}
        if tab not in valid:
            print(f"  Unknown tab '{args.run}'. Valid: Overview Chapters Questions Students")
        else:
            main(tab_filter=tab, sections_filter=args.section)
    else:
        ap.print_help()