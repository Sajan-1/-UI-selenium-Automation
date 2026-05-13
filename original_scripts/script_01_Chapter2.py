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
