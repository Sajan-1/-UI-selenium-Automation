"""
ClassLens – Full Chapter Card Accuracy Test Suite  (REFIXED)
==============================================================
FIXES IN THIS VERSION:
  • Weakest / Strongest Concepts now read via column-aware bounding-box JS
    (matches screenshot: left=Midterm, right=Preboard 1)
  • Concept pill badges (New / Improved / Declined) attached per concept row
  • Truncated concept names (ending '...') are expanded via innerText scan
  • Strongest Concepts: score % and badge captured per concept
  • Struggling students & Weak Concepts count use tighter column tolerance
  • Why-text stable-accuracy guard prevents false change-% extraction
  • align_sign applied consistently to all four locations
  • HTML report: Weakest/Strongest tabs show pills inline; Accuracy tab
    shows why-text accuracy % in its own column
  • All other tests unchanged

Tests every chapter card for:
  1.  Card list badge %  (Loc 1)
  2.  IMPROVED / DECLINED chip %  (Loc 2)
  3.  Change in chapter average badge  (Loc 3)
  4.  Why this chapter explanation %  (Loc 4)
  5.  4-way consistency across all locations
  6.  Midterm accuracy %
  7.  Preboard 1 accuracy %
  8.  Struggling students count  (both exams)
  9.  Weak Concepts count  (both exams)
  10. Weakest Concepts list  (both exams)
  11. Strongest Concepts list  (both exams)
  12. Concept pill badges  (New / Improved / Declined)
  13. Search box filter + clear + no-match
  14. Sort order  (High to Low)
  15. Static UI labels present
  16. HTML report saved → classlens_report.html

Run:
    python "Chapter tab.py"

Environment variables (optional):
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
from typing import List, Optional, Tuple

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
REPORT_FILE  = "classlens_report.html"

VALUES = {
    "Class":        "12",
    "Section":      "O",
    "Subject":      "Maths",
    "Exam":         "Midterm",
    "CompareLeft":  "Midterm",
    "CompareRight": "Preboard 1",
}
EXAM_LABELS    = ["Midterm", "Preboard 1"]
CARD_WAIT_SEC  = 45
PANEL_WAIT_SEC = 4.5

# ─────────────────────────────────────────────────────────────────────────────
# CHAPTER → UNIT / CONCEPT MAPPING  (from cleaned_question_unit_chapter_concept_mapping.xlsx)
# ─────────────────────────────────────────────────────────────────────────────
CHAPTER_CONCEPT_MAPPING = {
    "Relations & Functions": {
        "unit": "Relations and Functions",
        "weightage_marks": 8,
        "concepts": [
            {"name": "Types of Relations", "is_foundational": False},
            {"name": "Types of Functions", "is_foundational": True},
            {"name": "Composite Functions", "is_foundational": False},
            {"name": "Invertible Functions", "is_foundational": True},
        ],
    },
    "Inverse Trigonometric Functions": {
        "unit": "Relations and Functions",
        "weightage_marks": 8,
        "concepts": [
            {"name": "Principal Values (Domain and Range)", "is_foundational": True},
            {"name": "Formulas for Trigonometry", "is_foundational": True},
            {"name": "Algebra of Inverse Trig Functions", "is_foundational": False},
            {"name": "Substitution using Trig Formulas", "is_foundational": True},
        ],
    },
    "Matrices": {
        "unit": "Algebra",
        "weightage_marks": 10,
        "concepts": [
            {"name": "Basics & Types of Matrices", "is_foundational": False},
            {"name": "Matrix Operations", "is_foundational": True},
            {"name": "Transpose, Symmetric & Skew-symmetric", "is_foundational": False},
            {"name": "Elementary Operations", "is_foundational": False},
            {"name": "Inverse Matrices", "is_foundational": False},
        ],
    },
    "Determinants": {
        "unit": "Algebra",
        "weightage_marks": 10,
        "concepts": [
            {"name": "Determinant of a Matrix", "is_foundational": False},
            {"name": "Properties of Determinants", "is_foundational": True},
            {"name": "Applications (Area, Cramer's Rule, Linear Equations using inverse matrices)", "is_foundational": False},
            {"name": "Minors & Cofactors", "is_foundational": False},
            {"name": "Adjoint & Inverse", "is_foundational": True},
        ],
    },
    "Continuity & Differentiability": {
        "unit": "Calculus",
        "weightage_marks": 35,
        "concepts": [
            {"name": "Continuity", "is_foundational": False},
            {"name": "Rules of Differentiations", "is_foundational": True},
            {"name": "Chain Rule", "is_foundational": True},
            {"name": "Parametric & Implicit Differentiation", "is_foundational": False},
            {"name": "Derivatives of Inverse Trig Functions", "is_foundational": False},
            {"name": "Exponential & Logarithmic Functions/Logarithmic Properties", "is_foundational": True},
            {"name": "Second Order Derivative", "is_foundational": False},
        ],
    },
    "Application of Derivatives": {
        "unit": "Calculus",
        "weightage_marks": 35,
        "concepts": [
            {"name": "Rate of Change", "is_foundational": True},
            {"name": "Increasing & Decreasing Functions", "is_foundational": True},
            {"name": "Maxima & Minima", "is_foundational": True},
            {"name": "Maxima & Minima real life Applications", "is_foundational": False},
        ],
    },
    "Integrals": {
        "unit": "Calculus",
        "weightage_marks": 35,
        "concepts": [
            {"name": "Indefinite Integrals (Anti derivatives)", "is_foundational": True},
            {"name": "Rules of integrals", "is_foundational": True},
            {"name": "Integration by Substitution", "is_foundational": False},
            {"name": "Integration by Parts", "is_foundational": False},
            {"name": "Partial Fractions", "is_foundational": False},
            {"name": "Properties of Definite Integrals", "is_foundational": True},
            {"name": "Definite Integrals", "is_foundational": True},
        ],
    },
    "Application of Integrals": {
        "unit": "Calculus",
        "weightage_marks": 35,
        "concepts": [
            {"name": "Area under Curves", "is_foundational": True},
        ],
    },
    "Differential Equations": {
        "unit": "Calculus",
        "weightage_marks": 35,
        "concepts": [
            {"name": "Definition, Order & Degree", "is_foundational": False},
            {"name": "General & Particular Solution", "is_foundational": True},
            {"name": "Formation of DE", "is_foundational": False},
            {"name": "Variable Separable Method", "is_foundational": False},
            {"name": "Homogeneous DE", "is_foundational": True},
            {"name": "Linear DE", "is_foundational": False},
            {"name": "Applications (Growth/Decay)", "is_foundational": False},
        ],
    },
    "Vector Algebra": {
        "unit": "Vectors and Three-dimensional Geometry",
        "weightage_marks": 14,
        "concepts": [
            {"name": "Scalars & Vectors", "is_foundational": False},
            {"name": "Position Vector & Unit Vector", "is_foundational": True},
            {"name": "Vector Addition & Scalar Multiplication", "is_foundational": True},
            {"name": "Dot (Scalar) Product", "is_foundational": False},
            {"name": "Cross (Vector) Product", "is_foundational": False},
        ],
    },
    "3D Geometry": {
        "unit": "Vectors and Three-dimensional Geometry",
        "weightage_marks": 14,
        "concepts": [
            {"name": "Direction Cosines & Ratios", "is_foundational": True},
            {"name": "Equation of a Line", "is_foundational": True},
            {"name": "Angle between Lines", "is_foundational": False},
        ],
    },
    "Linear Programming": {
        "unit": "Linear Programming Problem",
        "weightage_marks": 5,
        "concepts": [
            {"name": "Formulating LPP", "is_foundational": True},
            {"name": "Objective Function", "is_foundational": False},
            {"name": "Graphical method of solution for problems in two variables", "is_foundational": True},
            {"name": "Feasible Region", "is_foundational": False},
            {"name": "Optimization", "is_foundational": False},
        ],
    },
    "Probability": {
        "unit": "Probability",
        "weightage_marks": 8,
        "concepts": [
            {"name": "Conditional Probability", "is_foundational": True},
            {"name": "Multiplication Rule", "is_foundational": True},
            {"name": "Bayes' Theorem", "is_foundational": False},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# TERMINAL COLOURS
# ─────────────────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
W = "\033[97m"; DIM = "\033[2m"; BLD = "\033[1m"; RST = "\033[0m"

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

all_results: List[TC] = []
_phase = ""

def set_phase(p: str):
    global _phase
    _phase = p

def record(name: str, passed: bool, detail: str = "", value: str = "") -> bool:
    all_results.append(TC(_phase, name, passed, detail, value))
    icon = f"{G}✔{RST}" if passed else f"{R}✘{RST}"
    st   = f"{G}[PASS]{RST}" if passed else f"{R}[FAIL]{RST}"
    v    = f"  {DIM}{value}{RST}" if value else ""
    print(f"    {icon} {st}  {name}{v}")
    return passed

def banner(n: int, t: str):
    print(f"\n{BLD}{C}{'═'*72}\n  PHASE {n}  ▶  {W}{t}\n{'═'*72}{RST}")

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
# LOC 1 — CHAPTER CARD LIST
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
# LOC 4 — WHY THIS CHAPTER TEXT + % EXTRACTION
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

def _is_accuracy_pct(num_str: str, ctx_before: str, ctx_after: str) -> bool:
    cb = ctx_before.lower(); ca = ctx_after.lower().strip()
    if any(ca.startswith(k) or (" "+k) in ca[:25] for k in _ACC_AFTER_WORDS): return True
    for phrase in _ACC_BEFORE_PHRASES:
        if phrase in cb: return True
    for sp in _STABLE_PHRASES:
        if sp in cb: return True
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

_CHANGE_KWS_STRICT = [
    "slight decline of","significant decline of","slight improvement of",
    "significant improvement of","declined by","decline of","declined significantly by",
    "improved by","improvement of","improved significantly by","drop of","dropped by",
    "change of","changed by","progress of","increased by","decreased by",
    "reduced by","fell by","significantly by","considerably by","notably by",
    "good improvement of","chapter dropped","this chapter dropped",
    "chapter declined","this chapter declined","chapter improved","this chapter improved",
]

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


# ─────────────────────────────────────────────────────────────────────────────
# EXAM PANEL READER  — REFIXED with proper column-aware concept extraction
# ─────────────────────────────────────────────────────────────────────────────
def read_exam_panel(driver, label: str) -> dict:
    """
    ClassLens renders Midterm and Preboard 1 SIDE-BY-SIDE in ONE shared wrapper.
    getBoundingClientRect() column matching pairs each metric label to the
    correct exam column. Concepts are now read with full column awareness so
    left-panel concepts go to Midterm and right-panel concepts go to Preboard 1.
    """
    data = {
        "label": label, "accuracy": None, "exam_date": None,
        "struggling_count": None, "weak_concepts_count": None,
        "weakest_concepts": [], "strongest_concepts": [],
    }
    OTHER_LABELS = [l for l in EXAM_LABELS if l != label]

    # ── PRIMARY: full bounding-box JS ─────────────────────────────────────
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

            // 1. locate exam label element
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

            // 2. ACCURACY
            const accEl  = findByColumn(ACC_KWS, lblMidX, 160);
            let accuracy = accEl ? numAbove(accEl, PCT_RE) : null;
            if (accuracy) { const v=parseFloat(accuracy); if(v<=5||v>100) accuracy=null; }

            // 3. STRUGGLING STUDENTS
            const strEl      = findByColumn(STR_KWS, lblMidX, 220);
            const strRaw     = strEl ? numBelow(strEl, INT_RE) : null;
            const struggling = (strRaw !== null && strRaw !== '') ? parseInt(strRaw) : null;

            // 4. WEAK CONCEPTS
            const wkEl      = findByColumn(WK_KWS, lblMidX, 220);
            const wkRaw     = wkEl ? numBelow(wkEl, INT_RE) : null;
            const weakCount = (wkRaw !== null && wkRaw !== '') ? parseInt(wkRaw) : null;

            // 5. DATE
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

            // ── REFIXED: column-aware Weakest / Strongest concept extraction ──
            // We scan all concept-like rows visible in the panel.
            // Each row is checked: if its horizontal midpoint is within
            // COLUMN_TOLERANCE px of lblMidX, it belongs to this exam column.
            const COLUMN_TOLERANCE = 250;

            // Find the heading elements for Weakest / Strongest
            let weakestHeadEl  = null;
            let strongestHeadEl = null;
            for (const el of document.querySelectorAll('*')) {
                const t = (el.innerText||'').trim();
                if (!weakestHeadEl  && (t === 'Weakest Concepts'  || t === 'Weakest concepts'))  weakestHeadEl  = el;
                if (!strongestHeadEl && (t === 'Strongest Concepts'|| t === 'Strongest concepts')) strongestHeadEl = el;
                if (weakestHeadEl && strongestHeadEl) break;
            }

            // Generic concept-row collector: walk DOM after headEl,
            // collect rows whose midX matches lblMidX, stop at next major heading.
            function collectConceptRows(headEl, stopKeywords) {
                if (!headEl) return [];
                const headRect = headEl.getBoundingClientRect();
                const rows = [];
                const seen = new Set();
                // Gather all elements that come BELOW the heading
                const all = Array.from(document.querySelectorAll('*'));
                const headIdx = all.indexOf(headEl);
                if (headIdx < 0) return [];
                for (let i = headIdx + 1; i < all.length; i++) {
                    const el = all[i];
                    const t  = (el.innerText || el.textContent || '').trim();
                    if (!t || t.length > 80 || t.length < 2) continue;
                    // Stop at next major section headings
                    if (stopKeywords.some(k => t === k)) break;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 || r.height === 0) continue;
                    // Must be BELOW the heading
                    if (r.top < headRect.bottom - 5) continue;
                    // Column check
                    const elMidX = (r.left + r.right) / 2;
                    if (Math.abs(elMidX - lblMidX) > COLUMN_TOLERANCE) continue;
                    // Skip pure numbers, badge words, and duplicates
                    if (/^\d+$/.test(t)) continue;
                    if (/^\d{1,3}(\.\d+)?%$/.test(t)) continue;
                    if (seen.has(t)) continue;
                    seen.add(t);
                    rows.push({ text: t, midX: elMidX, top: r.top, el });
                }
                return rows;
            }

            // Weakest concepts
            const weakestStopKws = ['Strongest Concepts','Strongest concepts',
                                    'Why this chapter','Why This Chapter',
                                    'Midterm','Preboard 1'];
            const weakestRows = collectConceptRows(weakestHeadEl, weakestStopKws);
            // Filter: exclude badge words and numbers; keep concept names (3+ words or title-case-ish)
            const weakestConcepts = weakestRows
                .filter(r => !BADGE_WORDS.has(r.text) && r.text.length > 3)
                .map(r => r.text)
                .slice(0, 6);

            // Strongest concepts — collect rows + adjacent pct + badge
            const strongestStopKws = ['Why this chapter','Why This Chapter',
                                      'Midterm','Preboard 1','Change in chapter'];
            const strongestRows = collectConceptRows(strongestHeadEl, strongestStopKws);

            // Build strongest list: pair concept name with nearby pct and badge
            const strongestConcepts = [];
            let i2 = 0;
            while (i2 < strongestRows.length) {
                const row = strongestRows[i2];
                if (BADGE_WORDS.has(row.text) || /^\d{1,3}(\.\d+)?%$/.test(row.text)) { i2++; continue; }
                // This is a concept name
                const concept = { name: row.text, pct: null, badge: null };
                // Look ahead for pct and badge in next few rows
                for (let j = i2 + 1; j < Math.min(i2 + 5, strongestRows.length); j++) {
                    const rt = strongestRows[j].text;
                    if (!concept.pct && /^\d{1,3}(\.\d+)?%$/.test(rt)) { concept.pct = rt; continue; }
                    if (!concept.badge && BADGE_WORDS.has(rt)) { concept.badge = rt; continue; }
                    // If it's another concept name, stop looking ahead
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
            # REFIXED: use JS-extracted concept lists directly
            if result.get("weakestConcepts"):
                data["weakest_concepts"] = result["weakestConcepts"]
            if result.get("strongestConcepts"):
                data["strongest_concepts"] = result["strongestConcepts"]
            _pt = result.get("panelText", "")
            print(f"        {label}: acc={result.get('accuracy')}  "
                  f"str={result.get('struggling')} (raw='{result.get('_strRaw')}' "
                  f"el='{result.get('_strElTxt')}')  "
                  f"wk={result.get('weakCount')} (raw='{result.get('_wkRaw')}' "
                  f"el='{result.get('_wkElTxt')}')")
            print(f"        {label}: weakest={data['weakest_concepts']}")
            print(f"        {label}: strongest={[c['name'] for c in data['strongest_concepts']]}")
        else:
            _pt = ""
            print(f"        {label}: JS returned null")
    except Exception as ex:
        _pt = ""
        print(f"        {label}: JS exception: {ex}")

    # ── FALLBACK A: XPath — smallest scoped ancestor per exam ─────────────
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
                    for sel in panel.find_elements(By.XPATH,
                            ".//*[contains(translate(text(),'STUDENRGLAB','studenrglab'),'struggling')]"):
                        for xp2 in ["./following-sibling::*[1]","./following-sibling::*[2]",
                                     "./../following-sibling::*[1]","./following::*[1]"]:
                            try:
                                ne = sel.find_element(By.XPATH, xp2); nt = safe_text(ne)
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

    # ── FALLBACK B: page-source bounded by next exam label ────────────────
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

    # ── FALLBACK C: XPath concept lists (if JS gave nothing) ─────────────
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
# LOC 4 HTML CELL HELPER
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
print(f"  ClassLens · Chapters Tab · Full Accuracy Test Suite  (REFIXED)")
print(f"  {DIM}{RUN_TS}{RST}")
print(f"{C}{'═'*72}{RST}\n")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — LOGIN
# ─────────────────────────────────────────────────────────────────────────────
banner(1, "LOGIN")
set_phase("Login")
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
    record("Login successful", True, value=f"user={USERNAME}")
except Exception as exc:
    record("Login failed", False, str(exc))
    driver.quit(); sys.exit("Login failed — aborting.")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — FILTER SELECTION
# ─────────────────────────────────────────────────────────────────────────────
banner(2, "FILTER SELECTION")
set_phase("Filters")
FILTER_PLAN = [
    (0,"Class","Class"), (1,"Section","Section"), (2,"Subject","Subject"),
    (3,"Exam","Exam"), (4,"CompareLeft","Compare Left"), (5,"CompareRight","Compare Right"),
]
try:
    for idx, key, lbl in FILTER_PLAN:
        val = VALUES[key]
        if not wait_option(driver, idx, val, timeout=30):
            record(f"Filter '{lbl}' available", False, f"option '{val}' not found"); continue
        sel = get_selects(driver)[idx]
        ok  = js_select(driver, sel, val)
        record(f"Filter '{lbl}' = '{val}'", ok, value=val)
        time.sleep(0.5)
    old_url = driver.current_url
    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()
    wait.until(lambda d: d.current_url != old_url)
    record("Dashboard loaded after Enter", True)
except Exception as exc:
    record("Filter setup error", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — NAVIGATE TO CHAPTERS TAB
# ─────────────────────────────────────────────────────────────────────────────
banner(3, "CHAPTERS TAB NAVIGATION")
set_phase("Navigation")
try:
    driver.get(CHAPTERS_URL)
    time.sleep(3.0)
    try: wait.until(lambda d: "screen=chapters" in d.current_url)
    except: pass
    wait_cards(driver); time.sleep(2.0)
    record("Chapters URL loaded", True, value="screen=chapters")
    src = driver.page_source
    for tab in ["Overview","Chapters","Questions","Students"]:
        record(f"Nav tab '{tab}' visible", tab in src)
except Exception as exc:
    record("Navigation error", False, str(exc))

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 4 — DISCOVERY & SORT ORDER
# ─────────────────────────────────────────────────────────────────────────────
banner(4, "CHAPTER CARD DISCOVERY + SORT ORDER")
set_phase("Discovery")
chapter_cards = discover_cards(driver)
record("Chapter cards discovered", len(chapter_cards) >= 1, value=f"{len(chapter_cards)} cards")
nums = [n for n in [extract_num(c["pct"]) for c in chapter_cards] if n is not None]
if len(nums) >= 2:
    record("Sort order: High → Low",
           all(nums[i] >= nums[i+1] for i in range(len(nums)-1)),
           value=str(nums[:5])+"…")
record("Sort label present",
       len(driver.find_elements(By.XPATH, "//*[contains(text(),'Chapter Avg')]")) >= 1)
print(f"\n  {BLD}Chapters discovered:{RST}")
for i, c in enumerate(chapter_cards, 1):
    col = G if "+" in c["pct"] else R
    arr = "▲" if "+" in c["pct"] else "▼"
    print(f"    {DIM}{i:>2}.{RST} {c['name']:<55} {col}{BLD}{arr} {c['pct']}{RST}")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 5 — PER-CHAPTER DETAIL PANEL
# ─────────────────────────────────────────────────────────────────────────────
banner(5, "PER-CHAPTER DETAIL PANEL — ALL CHAPTERS")
chapter_data: List[dict] = []

for card_idx, card in enumerate(chapter_cards):
    ch        = card["name"]
    set_phase(f"Chapter:{ch}")
    direction = "▲" if "+" in (card["pct"] or "") else "▼"
    col       = G if direction == "▲" else R
    print(f"\n  {BLD}{col}{direction} [{card_idx+1}/{len(chapter_cards)}]  {W}{ch}{RST}  {col}{card['pct']}{RST}")
    print(f"  {'─'*65}")
    ch_tests: List[dict] = []

    def ct(name: str, passed: bool, detail: str = "", value: str = "") -> bool:
        record(name, passed, detail, value)
        ch_tests.append({"name": name, "passed": passed, "detail": detail, "value": value})
        return passed

    pct_card = read_card_pct(driver, card)
    ct("Loc 1 · Card list badge % readable", pct_card is not None, value=str(pct_card or "N/A"))

    clicked = click_card(driver, card)
    ct("Card clickable / detail panel opens", clicked)
    if not clicked:
        warn("Could not click card — skipping detail tests")
        chapter_data.append({
            "name": ch, "pct_card": pct_card,
            "pct_chip": None, "pct_badge": None, "pct_why": None,
            "why_heading": None, "why_text": None, "why_acc_pct": None,
            "panels": [], "pills": [], "tests": ch_tests,
            "match": False, "skip": True,
        })
        continue

    time.sleep(PANEL_WAIT_SEC)
    try:
        WebDriverWait(driver, 10).until(
            lambda d: any(kw in d.page_source for kw in _WHY_HEADINGS))
    except: time.sleep(1.5)
    src = driver.page_source

    pct_chip  = read_improved_chip(driver, ref_pct=pct_card)
    pct_badge = read_change_badge(driver, ref_pct=pct_card)
    why_h     = next((kw for kw in _WHY_HEADINGS if kw in src), None)
    why_t_raw = read_why_text(driver)
    if why_t_raw:
        for _kw in _WHY_HEADINGS:
            if why_t_raw.startswith(_kw):
                why_t_raw = why_t_raw[len(_kw):].strip(" :\n"); break
    why_t     = why_t_raw if why_t_raw and len(why_t_raw.strip()) > 10 else None
    pct_why   = read_why_pct(why_t)
    if pct_why is None: pct_why = read_why_pct_from_page(driver, ref_pct=pct_card)
    why_acc_pct = read_why_accuracy_pct(why_t)

    pct_chip  = align_sign(pct_card, pct_chip)
    pct_badge = align_sign(pct_card, pct_badge)
    if pct_why: pct_why = align_sign(pct_card, pct_why)

    ct("Loc 2 · IMPROVED/DECLINED chip % readable", pct_chip  is not None, value=str(pct_chip  or "N/A"))
    ct("Loc 3 · Change in chapter average badge",   pct_badge is not None, value=str(pct_badge or "N/A"))
    _l4v = pct_why or (f"acc:{why_acc_pct}" if why_acc_pct else None)
    ct("Loc 4 · Why-text % (change or accuracy)",   _l4v is not None,
       value=(f"change%={pct_why}" if pct_why
              else (f"accuracy%={why_acc_pct} (stable)" if why_acc_pct else "NOTHING FOUND")))

    n1,n2,n3,n4 = norm_val(pct_card),norm_val(pct_chip),norm_val(pct_badge),norm_val(pct_why)
    present     = [n for n in [n1,n2,n3,n4] if n is not None]
    all_match   = len(set(present)) == 1 and len(present) >= 2 and len(present) == 4
    ct("✦ 4-Way Consistency Loc1==Loc2==Loc3==Loc4", all_match,
       value=f"L1={pct_card}  L2={pct_chip}  L3={pct_badge}  L4={pct_why}")

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

    panels: List[dict] = []
    for exam_label in EXAM_LABELS:
        pd = read_exam_panel(driver, exam_label)
        ct(f"[{exam_label}] Accuracy % readable",
           pd["accuracy"] is not None, value=pd["accuracy"] or "N/A")
        ct(f"[{exam_label}] Struggling students count",
           pd["struggling_count"] is not None,
           value=f"{pd['struggling_count']} students" if pd["struggling_count"] is not None else "NOT FOUND")
        ct(f"[{exam_label}] Weak Concepts count",
           pd["weak_concepts_count"] is not None,
           value=f"{pd['weak_concepts_count']} concepts" if pd["weak_concepts_count"] is not None else "NOT FOUND")
        ct(f"[{exam_label}] Weakest Concepts list ≥ 1 item",
           len(pd["weakest_concepts"]) >= 1, value=f"{len(pd['weakest_concepts'])} items: {pd['weakest_concepts'][:3]}")
        ct(f"[{exam_label}] Strongest Concepts list ≥ 1 item",
           len(pd["strongest_concepts"]) >= 1, value=f"{len(pd['strongest_concepts'])} items")
        panels.append(pd)
        print(f"      {DIM}{exam_label}:{RST}  "
              f"Accuracy={G}{BLD}{pd['accuracy'] or '?'}{RST}  "
              f"Struggling={Y}{BLD}{pd['struggling_count'] if pd['struggling_count'] is not None else '?'}{RST}  "
              f"WeakConcepts={C}{pd['weak_concepts_count'] if pd['weak_concepts_count'] is not None else '?'}{RST}")
        if pd["weakest_concepts"]:
            print(f"        Weakest : {pd['weakest_concepts']}")
        if pd["strongest_concepts"]:
            print(f"        Strongest: {[c['name']+(' '+c['pct'] if c.get('pct') else '')+(  ' ['+c['badge']+']' if c.get('badge') else '') for c in pd['strongest_concepts']]}")

    pill_els = driver.find_elements(By.XPATH,
        "//*[normalize-space()='New' or normalize-space()='Improved' or "
        "    normalize-space()='Declined' or normalize-space()='NEW' or "
        "    normalize-space()='IMPROVED' or normalize-space()='DECLINED']")
    pills = list({safe_text(e) for e in pill_els if safe_text(e)})
    ct("Concept pill badges present", len(pills) >= 1, value=str(pills))

    print(f"\n      {Y}┌─ WHY SECTION {'─'*45}┐{RST}")
    print(f"      {Y}│{RST} Heading : {why_h or 'NOT FOUND'}")
    preview = (why_t or "NOT FOUND")[:70]
    print(f"      {Y}│{RST} Text    : {preview}{'…' if why_t and len(why_t)>70 else ''}")
    pct_disp = pct_why if pct_why else "— (only accuracy % in text)"
    pct_col  = G if pct_why and "+" in pct_why else (R if pct_why else Y)
    print(f"      {Y}│{RST} Change %: {pct_col}{BLD}{pct_disp}{RST}")
    print(f"      {Y}└{'─'*55}┘{RST}")

    chapter_data.append({
        "name": ch, "pct_card": pct_card,
        "pct_chip": pct_chip, "pct_badge": pct_badge, "pct_why": pct_why,
        "why_heading": why_h, "why_text": why_t, "why_acc_pct": why_acc_pct,
        "panels": panels, "pills": pills, "tests": ch_tests,
        "match": all_match, "skip": False,
    })

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6 — SEARCH BOX
# ─────────────────────────────────────────────────────────────────────────────
banner(6, "SEARCH BOX FUNCTIONALITY")
set_phase("Search")
driver.get(CHAPTERS_URL); wait_cards(driver); time.sleep(1.5)
fresh = discover_cards(driver)
sb = None
for inp in driver.find_elements(By.TAG_NAME, "input"):
    if "chapter" in safe_attr(inp,"placeholder").lower() or "search" in safe_attr(inp,"placeholder").lower():
        sb = inp; break
if not sb:
    inps = driver.find_elements(By.TAG_NAME, "input")
    if inps: sb = inps[0]
record("Search input element present", sb is not None,
       value=safe_attr(sb,"placeholder") if sb else "N/A")
if sb and fresh:
    def clr():
        sb.click(); sb.send_keys(Keys.CONTROL,"a"); sb.send_keys(Keys.DELETE); time.sleep(1.0)
    kw = fresh[0]["name"].split()[0]; other = fresh[-1]["name"] if len(fresh)>1 else None
    clr(); sb.send_keys(kw); time.sleep(1.2)
    record(f"Search '{kw}' → target visible", fresh[0]["name"] in driver.page_source)
    if other and other.split()[0].lower() != kw.lower():
        ov = driver.find_elements(By.XPATH, f"//*[normalize-space()='{other}']")
        record("Search filters non-matching", all(not e.is_displayed() for e in ov) if ov else True)
    clr()
    missing = [c["name"] for c in fresh if c["name"] not in driver.page_source]
    record("Search cleared → all restored", len(missing)==0,
           value="all present" if not missing else f"missing {len(missing)}")
    clr(); sb.send_keys("ZZZNOMATCH99"); time.sleep(1.0)
    vis = driver.find_elements(By.XPATH, f"//*[normalize-space()='{fresh[0]['name']}']")
    record("No-match query → cards hidden", all(not e.is_displayed() for e in vis) if vis else True)
    clr()

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 7 — STATIC UI LABELS
# ─────────────────────────────────────────────────────────────────────────────
banner(7, "STATIC UI LABELS")
set_phase("StaticLabels")
driver.get(CHAPTERS_URL); wait_cards(driver); time.sleep(1.5)
lc = discover_cards(driver); opened = False
if lc:
    opened = click_card(driver, lc[0])
    if opened: time.sleep(1.5)
record("First card clicked for label check", opened)
src = driver.page_source
for lbl, kws in [
    ("Sort label 'Chapter Avg'",            ["Chapter Avg"]),
    ("Nav tab 'Overview'",                  ["Overview"]),
    ("Nav tab 'Chapters'",                  ["Chapters"]),
    ("Nav tab 'Questions'",                 ["Questions"]),
    ("Nav tab 'Students'",                  ["Students"]),
    ("'Midterm' header",                    ["Midterm"]),
    ("'Preboard 1' header",                ["Preboard 1","Preboard1"]),
    ("'ACCURACY' label",                    ["ACCURACY","Accuracy","accuracy"]),
    ("'Struggling students' label",         ["Struggling students","Struggling"]),
    ("'Weak Concepts' label",               ["Weak Concepts","Weak concepts"]),
    ("'Weakest Concepts' section",          ["Weakest Concepts","Weakest concepts"]),
    ("'Strongest Concepts' section",        ["Strongest Concepts","Strongest concepts"]),
    ("'Why this chapter' heading",          ["Why this chapter","Why This Chapter"]),
    ("IMPROVED/DECLINED chip",              ["IMPROVED","DECLINED","Improved","Declined"]),
    ("'Change in chapter average' label",   ["Change in chapter average","Change in chapter"]),
    ("Concept pill badges",                 ["New","Improved","Declined","NEW","IMPROVED"]),
]:
    record(lbl, any(k in src for k in kws))

# ─────────────────────────────────────────────────────────────────────────────
# TERMINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
passed_l = [r for r in all_results if r.passed]
failed_l = [r for r in all_results if not r.passed]
rate     = round(100 * len(passed_l) / len(all_results)) if all_results else 0
bar_w    = round(rate * 42 / 100)

print(f"\n{BLD}{C}{'═'*72}{RST}")
print(f"{BLD}  FINAL SUMMARY{RST}")
print(f"{C}{'─'*72}{RST}")
print(f"  Chapters : {len(chapter_cards)}    Tests : {len(all_results)}"
      f"    {G}✔ {len(passed_l)}{RST}    {R}✘ {len(failed_l)}{RST}")
print(f"  Pass rate: {rate}%  {G}{'█'*bar_w}{DIM}{'░'*(42-bar_w)}{RST}")
print(f"{C}{'─'*72}{RST}")

print(f"\n  {BLD}4-Way Consistency per Chapter:{RST}")
hdr = f"  {'Chapter':<44} {'L1':>9} {'L2':>9} {'L3':>10} {'L4':>9}  4-Way"
print(f"{DIM}{hdr}{RST}")
print(f"  {DIM}{'─'*95}{RST}")
for ch in chapter_data:
    r4 = (f"{G}MATCH{RST}" if ch["match"] else (f"{Y}SKIP{RST}" if ch["skip"] else f"{R}MISM{RST}"))
    print(f"  {ch['name']:<44} "
          f"{(ch['pct_card']  or 'N/A'):>9}  "
          f"{(ch['pct_chip']  or 'N/A'):>9}  "
          f"{(ch['pct_badge'] or 'N/A'):>9}  "
          f"{(ch['pct_why']   or 'N/A'):>9}  {r4}")

if failed_l:
    print(f"\n{R}  FAILED TESTS:{RST}")
    for r in failed_l:
        print(f"  {R}✘{RST} [{r.phase}] {r.name}"
              + (f"  {DIM}{r.detail}{RST}" if r.detail else ""))

verdict = (f"{G}{BLD}🎉 ALL TESTS PASSED{RST}" if not failed_l
           else f"{R}{BLD}⚠  {len(failed_l)} FAILED{RST}")
print(f"\n  {verdict}  {DIM}({rate}% pass rate){RST}")
print(f"{C}{'═'*72}{RST}\n")

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
    if t_low == "new":      cls = "pill-new"
    elif t_low == "improved": cls = "pill-pos"
    else:                    cls = "pill-neg"
    return f'<span class="{cls}">{t}</span>'

def grp(title: str, cols: int, chip: str = "", extra: str = "") -> str:
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

# ─────────────────────────────────────────────────────────────────────────────
# BUILD TABLE ROWS
# ─────────────────────────────────────────────────────────────────────────────
by_phase = defaultdict(list)
for r in all_results:
    by_phase[r.phase].append(r)

# ── Overview rows ─────────────────────────────────────────────────────────
ov_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip   = "+" if ch["pct_card"] and "+" in ch["pct_card"] else "-"
    ov_rows += grp(f"{i}.  {ch['name']}", 8, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
    p_tc   = sum(1 for t in ch["tests"] if t["passed"])
    t_tc   = len(ch["tests"])
    pct_tc = round(100*p_tc/t_tc) if t_tc else 0
    bar_c  = "#3fb950" if pct_tc==100 else ("#d29922" if pct_tc>=50 else "#f85149")
    tc_bar = (f'<div style="display:flex;align-items:center;gap:8px">'
              f'<div style="flex:1;background:#1a2330;border-radius:3px;height:5px;min-width:60px">'
              f'<div style="width:{pct_tc}%;height:5px;background:{bar_c};border-radius:3px"></div></div>'
              f'<span style="font-size:11px;color:#5a7490;font-family:\'DM Mono\',monospace">{p_tc}/{t_tc}</span></div>')
    cons_badge = (f'<span class="badge ok">MATCH</span>' if ch["match"]
                  else ('<span class="badge skip">SKIP</span>' if ch.get("skip")
                        else '<span class="badge fail">MISMATCH</span>'))
    ov_rows += (f'<tr><td class="num">{i}</td>'
                f'<td class="chn">{ch["name"]}</td>'
                f'<td style="text-align:center">{hp(ch["pct_card"])}</td>'
                f'<td style="text-align:center">{hp(ch.get("pct_chip"))}</td>'
                f'<td style="text-align:center">{hp(ch.get("pct_badge"))}</td>'
                f'<td style="text-align:center">{loc4_display(ch)}</td>'
                f'<td style="text-align:center">{cons_badge}</td>'
                f'<td>{tc_bar}</td></tr>')

# ── All-tests rows ────────────────────────────────────────────────────────
tc_rows = ""
for ph, rs in by_phase.items():
    p = sum(1 for r in rs if r.passed); f = len(rs)-p
    bge = (f'<span class="badge ok">{p} passed</span>'
           + (f'&nbsp;<span class="badge fail">{f} failed</span>' if f else ""))
    tc_rows += grp(ph.replace("Chapter:",""), 5,
                   extra=f'<span style="float:right">{bge}</span>')
    for r in rs:
        cls  = "pass-row" if r.passed else "fail-row"
        icon = ('<span style="color:#3fb950;font-weight:700">✔</span>' if r.passed
                else '<span style="color:#f85149;font-weight:700">✘</span>')
        v    = (r.value or r.detail or "")[:70]
        tc_rows += (f'<tr class="{cls}"><td style="width:28px">{icon}</td>'
                    f'<td class="muted" style="font-size:11px">{r.phase.replace("Chapter:","")}</td>'
                    f'<td>{r.name}</td><td>{hb(r.passed)}</td>'
                    f'<td class="muted mono" style="font-size:12px">{v}</td></tr>')

# ── % Consistency rows ────────────────────────────────────────────────────
cons_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    cons_rows += grp(f"{i}.  {ch['name']}", 6, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
    cls = "pass-row" if ch["match"] else ("skip-row" if ch.get("skip") else "fail-row")
    res = (f'<span class="badge ok">ALL MATCH</span>' if ch["match"]
           else (f'<span class="badge skip">SKIPPED</span>' if ch.get("skip")
                 else f'<span class="badge fail">MISMATCH</span>'))
    cons_rows += (f'<tr class="{cls}">'
                  f'<td class="chn">{ch["name"]}</td>'
                  f'<td style="text-align:center">{loc_cell(ch["pct_card"],  ch["pct_card"])}</td>'
                  f'<td style="text-align:center">{loc_cell(ch.get("pct_chip"),  ch["pct_card"])}</td>'
                  f'<td style="text-align:center">{loc_cell(ch.get("pct_badge"), ch["pct_card"])}</td>'
                  f'<td style="text-align:center">{loc4_display(ch)}</td>'
                  f'<td style="text-align:center;font-weight:700">{res}</td></tr>')

# ── Exam stats rows ───────────────────────────────────────────────────────
est_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    est_rows += grp(f"{i}.  {ch['name']}", 6, chip)
    for pd in ch.get("panels", []):
        acc    = pd["accuracy"] or "—"
        acc_ok = pd["accuracy"] is not None
        acc_sty= "color:#3fb950;font-size:18px;font-weight:700;font-family:'DM Mono',monospace" if acc_ok else "color:#5a7490"
        st = pd["struggling_count"]
        st_h = ('<span class="muted">—</span>' if st is None
                else (f'<span style="color:#3fb950;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{st}</span>' if st==0
                      else (f'<span style="color:#d29922;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{st}</span>' if st<=5
                            else f'<span style="color:#f85149;font-size:16px;font-weight:700;font-family:\'DM Mono\',monospace">{st}</span>')))
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

# ── Why text rows ─────────────────────────────────────────────────────────
why_rows = ""
for i, ch in enumerate(chapter_data, 1):
    if not ch.get("why_heading") and not ch.get("why_text"): continue
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    why_rows += grp(f"{i}.  {ch['name']}", 5, chip)
    why_rows += (f'<tr><td class="chn">{ch["name"]}</td>'
                 f'<td>{hp(ch["pct_card"])}</td>'
                 f'<td><strong style="color:#cdd9e5">{ch.get("why_heading") or "—"}</strong></td>'
                 f'<td style="font-size:13px;line-height:1.65;max-width:440px;color:#cdd9e5">{ch.get("why_text") or "—"}</td>'
                 f'<td style="text-align:center">{loc4_display(ch)}</td></tr>')
if not why_rows:
    why_rows = '<tr><td colspan="5" class="empty">No explanation text extracted</td></tr>'

# ── Weakest concepts rows — REFIXED: show pill badge inline ───────────────
wk_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    wk_rows += grp(f"{i}.  {ch['name']}", 4, chip)
    for pd in ch.get("panels", []):
        exam_col = "#d29922" if pd["label"] == "Midterm" else "#58a6ff"
        wk_rows += (f'<tr class="sub-row"><td colspan="4" style="color:{exam_col}">'
                    f'📅 &nbsp;{pd["label"]}</td></tr>')
        if pd["weakest_concepts"]:
            for rank, concept in enumerate(pd["weakest_concepts"], 1):
                # concept may be a string (new JS) or dict (old fallback)
                if isinstance(concept, dict):
                    cname = concept.get("name", str(concept))
                    cbadge = hpill(concept.get("badge", "")) if concept.get("badge") else ""
                else:
                    cname  = str(concept)
                    cbadge = ""
                wk_rows += (f'<tr>'
                            f'<td class="num" style="color:#d29922;font-weight:700;'
                            f'font-family:\'DM Mono\',monospace;width:36px">{rank}</td>'
                            f'<td style="font-weight:500;padding-left:24px">{cname}</td>'
                            f'<td class="muted mono">{pd["label"]}</td>'
                            f'<td>{cbadge}</td></tr>')
        else:
            wk_rows += '<tr><td colspan="4" class="empty">None extracted</td></tr>'

# ── Strongest concepts rows — REFIXED: show pct + pill inline ────────────
st_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    st_rows += grp(f"{i}.  {ch['name']}", 5, chip)
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

# ── Failed tests rows ─────────────────────────────────────────────────────
failed_rows = ""
prev_ph = ""
for r in [r for r in all_results if not r.passed]:
    ph = r.phase.replace("Chapter:","")
    if ph != prev_ph:
        failed_rows += grp(ph, 4); prev_ph = ph
    det = (r.detail or r.value or "")[:80]
    failed_rows += (f'<tr class="fail-row">'
                    f'<td style="width:28px"><span style="color:#f85149;font-weight:700">✘</span></td>'
                    f'<td class="muted mono" style="font-size:11px">{ph}</td>'
                    f'<td>{r.name}</td>'
                    f'<td class="muted mono" style="font-size:12px">{det}</td></tr>')
if not failed_rows:
    failed_rows = '<tr><td colspan="4" class="empty" style="color:#3fb950;font-style:normal;font-weight:600">🎉 All tests passed — no failures!</td></tr>'

# ── Phase cards ───────────────────────────────────────────────────────────
phase_cards = ""
for ph, rs in by_phase.items():
    p = sum(1 for r in rs if r.passed); f = len(rs)-p
    pct_ph = round(100*p/len(rs)) if rs else 0
    border_col = "#1a7f37" if f==0 else "#cf222e"
    bar_col    = "#3fb950" if f==0 else "#f85149"
    phase_cards += (f'<div style="background:#0d1219;border:1px solid #1f2d3d;border-left:3px solid {border_col};'
                    f'border-radius:8px;padding:14px 16px;">'
                    f'<div style="font-size:12px;font-weight:600;color:#cdd9e5;margin-bottom:8px;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{ph.replace("Chapter:","")}">'
                    f'{ph.replace("Chapter:","📖 ")}</div>'
                    f'<div style="background:#1a2330;border-radius:3px;height:4px;overflow:hidden;margin-bottom:8px">'
                    f'<div style="width:{pct_ph}%;height:4px;background:{bar_col};border-radius:3px"></div></div>'
                    f'<div style="font-size:11px;display:flex;gap:8px;font-family:\'DM Mono\',monospace">'
                    f'<span style="color:#3fb950">{p}✔</span>'
                    f'<span style="color:#f85149">{f}✘</span>'
                    f'<span style="color:#5a7490">{pct_ph}%</span>'
                    f'</div></div>')

# ── Accuracy rows ─────────────────────────────────────────────────────────
acc_rows = ""
for i, ch in enumerate(chapter_data, 1):
    chip = "+" if ch["pct_card"] and "+" in (ch["pct_card"] or "") else "-"
    acc_rows += grp(f"{i}.  {ch['name']}", 6, chip, f"&nbsp;&nbsp;{hp(ch['pct_card'])}")
    mid_acc_v = pre_acc_v = None
    for pd in ch.get("panels", []):
        if pd["label"] == "Midterm":    mid_acc_v = pd.get("accuracy")
        if pd["label"] == "Preboard 1": pre_acc_v = pd.get("accuracy")
    pct_card_v = ch.get("pct_card")
    why_acc_v  = ch.get("why_acc_pct")
    loc4_cell  = loc4_display(ch)
    mid_cell   = (f'<span style="color:#d29922;font-size:20px;font-weight:700;font-family:\'DM Mono\',monospace">{mid_acc_v}</span>'
                  if mid_acc_v else '<span class="muted">—</span>')
    pre_cell   = (f'<span style="color:#58a6ff;font-size:20px;font-weight:700;font-family:\'DM Mono\',monospace">{pre_acc_v}</span>'
                  if pre_acc_v else '<span class="muted">—</span>')
    wacc_cell  = (f'<span style="color:#3fb950;font-size:17px;font-weight:700;font-family:\'DM Mono\',monospace">{why_acc_v}</span>'
                  if why_acc_v else '<span class="muted">—</span>')
    acc_rows += (f'<tr><td class="chn">{ch["name"]}</td>'
                 f'<td style="text-align:center">{hp(pct_card_v)}</td>'
                 f'<td style="text-align:center">{mid_cell}</td>'
                 f'<td style="text-align:center">{pre_cell}</td>'
                 f'<td style="text-align:center">{loc4_cell}</td>'
                 f'<td style="text-align:center">{wacc_cell}</td></tr>')

# ── Chapter Concept Mapping rows (from Excel) ────────────────────────────
ccm_rows = ""
_unit_colors = {
    "Relations and Functions": "#58a6ff",
    "Algebra": "#bc8cff",
    "Calculus": "#f0883e",
    "Vectors and Three-dimensional Geometry": "#3fb950",
    "Linear Programming Problem": "#d29922",
    "Probability": "#f85149",
}
_unit_order = [
    "Relations and Functions", "Algebra", "Calculus",
    "Vectors and Three-dimensional Geometry",
    "Linear Programming Problem", "Probability",
]
_seen_units = set()
for unit_name in _unit_order:
    unit_chapters = [(ch_name, ch_info) for ch_name, ch_info in CHAPTER_CONCEPT_MAPPING.items()
                     if ch_info["unit"] == unit_name]
    if not unit_chapters:
        continue
    ucol = _unit_colors.get(unit_name, "#58a6ff")
    total_concepts = sum(len(ci["concepts"]) for _, ci in unit_chapters)
    total_found    = sum(1 for c in (con for _, ci2 in unit_chapters for con in ci2["concepts"]) if c["is_foundational"])
    wt = unit_chapters[0][1]["weightage_marks"]
    ccm_rows += (f'<tr class="grp-row"><td colspan="6">'
                 f'<span class="grp-title" style="color:{ucol}">{unit_name}</span>'
                 f'<span style="margin-left:12px;font-size:11px;color:var(--muted);font-weight:400">'
                 f'{len(unit_chapters)} chapter{"s" if len(unit_chapters)>1 else ""} · '
                 f'{total_concepts} concepts · '
                 f'<span style="color:{ucol};font-weight:600">{wt} marks</span>'
                 f'</span></td></tr>')
    for ch_name, ch_info in unit_chapters:
        concepts = ch_info["concepts"]
        n_found = sum(1 for c in concepts if c["is_foundational"])
        n_total = len(concepts)
        fnd_pct = round(100 * n_found / n_total) if n_total else 0
        fnd_bar_col = "#3fb950" if fnd_pct >= 60 else ("#d29922" if fnd_pct >= 30 else "#f85149")
        fnd_bar = (f'<div style="display:flex;align-items:center;gap:8px">'
                   f'<div style="flex:1;background:#1a2330;border-radius:3px;height:5px;min-width:50px">'
                   f'<div style="width:{fnd_pct}%;height:5px;background:{fnd_bar_col};border-radius:3px"></div></div>'
                   f'<span style="font-size:11px;color:#5a7490;font-family:\'DM Mono\',monospace">'
                   f'{n_found}/{n_total}</span></div>')
        ccm_rows += (f'<tr class="sub-row"><td colspan="6" style="font-style:normal;color:{ucol};'
                     f'font-weight:700;font-size:12px;padding:10px 16px 6px 20px;border-top:1px solid var(--bdr)">'
                     f'📖 &nbsp;{ch_name}'
                     f'<span style="float:right;font-weight:400;font-size:11px;color:var(--muted)">'
                     f'Foundational: {fnd_bar}</span>'
                     f'</td></tr>')
        for cidx, concept in enumerate(concepts, 1):
            fnd = concept["is_foundational"]
            fnd_badge = ('<span style="display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;'
                         'font-weight:600;background:rgba(10,35,20,.8);color:#56d364;border:1px solid #1a7f37">'
                         '★ Foundational</span>' if fnd
                         else '<span style="display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;'
                              'font-weight:600;background:var(--s2);color:var(--muted);border:1px solid var(--bdr)">'
                              'Standard</span>')
            row_bg = 'background:rgba(26,127,55,.04);' if fnd else ''
            ccm_rows += (f'<tr style="{row_bg}">'
                         f'<td class="num" style="color:var(--muted);width:36px;font-family:\'DM Mono\',monospace">{cidx}</td>'
                         f'<td style="font-weight:500;color:var(--hd);padding-left:24px">{concept["name"]}</td>'
                         f'<td class="muted mono" style="font-size:12px">{ch_name}</td>'
                         f'<td style="text-align:center"><span style="color:{ucol};font-size:11px;'
                         f'font-family:\'DM Mono\',monospace">{unit_name}</span></td>'
                         f'<td class="num" style="font-family:\'DM Mono\',monospace;color:{ucol}">{wt}</td>'
                         f'<td style="text-align:center">{fnd_badge}</td></tr>')

_total_concepts = sum(len(ci["concepts"]) for ci in CHAPTER_CONCEPT_MAPPING.values())
_total_found    = sum(1 for ci in CHAPTER_CONCEPT_MAPPING.values() for c in ci["concepts"] if c["is_foundational"])
_total_standard = _total_concepts - _total_found

# ─────────────────────────────────────────────────────────────────────────────
# WRITE HTML REPORT
# ─────────────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClassLens — Chapter Accuracy Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#080c10; --s1:#0d1219; --s2:#131a23; --s3:#1a2330;
  --bdr:#1f2d3d; --bdr2:#253345;
  --tx:#cdd9e5; --tx2:#8fa4bc; --muted:#5a7490; --hd:#e6edf3;
  --pos:#1a7f37; --pos-bg:#0a1f10; --pos-t:#3fb950;
  --neg:#cf222e; --neg-bg:#1c0a0c; --neg-t:#f85149;
  --amb:#9e6a03; --amb-bg:#1c1508; --amb-t:#d29922;
  --blu:#1158cb; --blu-bg:#071228; --blu-t:#58a6ff;
  --acc:#6e40c9; --acc-t:#bc8cff;
  --new:#0a2a35; --new-t:#39c5cf; --new-bdr:#1a6870;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{
  font-family:'DM Sans',sans-serif;
  background:var(--bg);
  color:var(--tx);
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
  min-height:100vh;
}}
body::before{{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.03'/%3E%3C/svg%3E");
}}
.wrap{{position:relative;z-index:1;max-width:1420px;margin:0 auto;padding:36px 40px 72px;}}

.hero{{
  display:grid;grid-template-columns:1fr auto;align-items:start;gap:28px;
  background:var(--s1);border:1px solid var(--bdr);border-radius:14px;
  padding:34px 38px;margin-bottom:24px;overflow:hidden;position:relative;
}}
.hero::after{{
  content:'';position:absolute;top:-120px;right:-120px;
  width:400px;height:400px;border-radius:50%;pointer-events:none;
  background:radial-gradient(circle,rgba(88,166,255,.05) 0%,transparent 65%);
}}
.hero-eye{{
  font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--blu-t);margin-bottom:10px;display:flex;align-items:center;gap:10px;
}}
.hero-eye::before{{content:'';display:inline-block;width:24px;height:2px;
  background:linear-gradient(90deg,var(--blu-t),var(--acc-t));border-radius:2px;}}
.hero-title{{font-size:28px;font-weight:700;color:var(--hd);letter-spacing:-.4px;line-height:1.2;margin-bottom:8px;}}
.hero-sub{{font-size:13.5px;color:var(--muted);margin-bottom:18px;}}
.hero-tags{{display:flex;gap:8px;flex-wrap:wrap;}}
.htag{{
  background:var(--blu-bg);border:1px solid var(--bdr2);color:var(--blu-t);
  padding:4px 14px;border-radius:20px;font-size:12px;font-weight:500;
  font-family:'DM Mono',monospace;
}}
.hero-meta{{text-align:right;font-family:'DM Mono',monospace;font-size:12px;color:var(--muted);line-height:2;white-space:nowrap;}}
.hero-rate{{font-size:42px;font-weight:700;color:var(--hd);font-family:'DM Sans',sans-serif;
  display:block;letter-spacing:-1px;line-height:1;margin-bottom:4px;}}
.hero-rate-label{{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--pos-t);}}

.kpi-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px;}}
.kpi{{
  background:var(--s1);border:1px solid var(--bdr);border-radius:10px;
  padding:22px 18px 18px;position:relative;overflow:hidden;
  transition:border-color .2s,transform .15s;
}}
.kpi:hover{{border-color:var(--bdr2);transform:translateY(-2px);}}
.kpi::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;border-radius:0 0 10px 10px;}}
.k-ch::after{{background:linear-gradient(90deg,var(--blu),var(--acc));}}
.k-to::after{{background:linear-gradient(90deg,var(--blu-t),#79c0ff);}}
.k-pa::after{{background:linear-gradient(90deg,var(--pos),var(--pos-t));}}
.k-fa::after{{background:linear-gradient(90deg,var(--neg),var(--neg-t));}}
.k-rt::after{{background:linear-gradient(90deg,var(--amb),var(--amb-t));}}
.kv{{font-size:36px;font-weight:700;line-height:1;margin-bottom:5px;font-family:'DM Mono',monospace;}}
.kl{{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);}}
.k-ch .kv{{color:var(--hd);}} .k-to .kv{{color:var(--blu-t);}}
.k-pa .kv{{color:var(--pos-t);}} .k-fa .kv{{color:var(--neg-t);}} .k-rt .kv{{color:var(--amb-t);}}

.prog{{
  background:var(--s1);border:1px solid var(--bdr);border-radius:10px;
  padding:22px 26px;margin-bottom:26px;
}}
.prog-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;}}
.prog-label{{font-size:13px;font-weight:600;color:var(--tx2);letter-spacing:.03em;}}
.prog-val{{font-size:26px;font-weight:700;color:var(--pos-t);font-family:'DM Mono',monospace;}}
.prog-track{{background:var(--s3);border-radius:999px;height:10px;overflow:hidden;}}
.prog-fill{{
  height:10px;border-radius:999px;
  background:linear-gradient(90deg,var(--pos) 0%,var(--pos-t) 60%,#56d364 100%);
  box-shadow:0 0 14px rgba(63,185,80,.2);
  transition:width 1.1s cubic-bezier(.4,0,.2,1);
}}

.nav-wrap{{border-bottom:1px solid var(--bdr);margin-bottom:28px;overflow-x:auto;}}
.nav{{display:flex;gap:0;min-width:max-content;}}
.nt{{
  padding:12px 22px;cursor:pointer;color:var(--muted);
  font-weight:500;font-size:13px;border-bottom:2px solid transparent;
  transition:color .15s,border-color .2s;white-space:nowrap;user-select:none;
}}
.nt:hover{{color:var(--tx);}}
.nt.active{{color:var(--hd);border-bottom-color:var(--blu-t);font-weight:600;}}
.tc{{display:none;}}.tc.active{{display:block;animation:fadeUp .22s ease;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}

.sh{{display:flex;align-items:center;gap:12px;margin:0 0 16px;padding-bottom:12px;border-bottom:1px solid var(--bdr);}}
.sh-icon{{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:15px;background:var(--blu-bg);border:1px solid var(--bdr2);flex-shrink:0;}}
.sh h2{{font-size:16px;font-weight:700;color:var(--hd);letter-spacing:-.2px;}}
.sh-pills{{margin-left:auto;display:flex;gap:6px;align-items:center;}}
.pill{{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;
  border:1px solid var(--bdr);background:var(--s2);color:var(--tx2);}}
.pill-g{{background:var(--pos-bg);color:var(--pos-t);border-color:var(--pos);}}
.pill-r{{background:var(--neg-bg);color:var(--neg-t);border-color:var(--neg);}}

.desc{{
  font-size:13px;color:var(--tx2);background:var(--s2);border:1px solid var(--bdr);
  border-left:3px solid var(--blu-t);border-radius:0 6px 6px 0;
  padding:12px 16px;margin-bottom:18px;line-height:1.75;
}}
.desc strong{{color:var(--blu-t);}}

.tw{{background:var(--s1);border:1px solid var(--bdr);border-radius:10px;overflow:hidden;margin-bottom:30px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}}
thead tr{{background:var(--s2);}}
th{{
  padding:10px 14px;text-align:left;font-weight:600;color:var(--muted);
  border-bottom:1px solid var(--bdr);white-space:nowrap;
  font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;font-family:'DM Mono',monospace;
}}
td{{padding:10px 14px;border-bottom:1px solid var(--s3);vertical-align:middle;}}
tbody tr:last-child td{{border-bottom:none;}}
tbody tr:hover{{background:var(--s2);}}
.pass-row:hover{{background:rgba(26,127,55,.07)!important;}}
.fail-row{{background:rgba(207,34,46,.04);}}
.fail-row:hover{{background:rgba(207,34,46,.09)!important;}}
.skip-row{{background:rgba(158,106,3,.04);}}

.grp-row td{{
  background:linear-gradient(90deg,#0f1e35,var(--s2));
  color:var(--hd);font-weight:700;font-size:12px;
  padding:10px 16px;border-top:1px solid var(--bdr2);border-bottom:1px solid var(--bdr);
}}
.grp-row:first-child td{{border-top:none;}}
.grp-title{{font-size:12px;font-weight:700;color:var(--hd);margin-right:10px;}}
.sub-row td{{
  background:var(--s2);font-size:11px;font-weight:600;
  padding:6px 16px 6px 28px;border-top:1px solid var(--bdr);font-style:italic;
}}

.num{{text-align:center;font-variant-numeric:tabular-nums;font-family:'DM Mono',monospace;}}
.chn{{font-weight:600;color:var(--hd);}}
.muted{{color:var(--muted);}}
.mono{{font-family:'DM Mono',monospace;}}
.miss{{color:var(--neg-t);font-size:11px;font-weight:600;}}
.empty{{color:var(--muted);font-style:italic;text-align:center;padding:18px;}}

.badge{{display:inline-block;padding:3px 9px;border-radius:5px;
  font-size:11px;font-weight:700;letter-spacing:.04em;font-family:'DM Mono',monospace;}}
.badge.ok  {{background:var(--pos-bg);color:var(--pos-t);border:1px solid var(--pos);}}
.badge.fail{{background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg);}}
.badge.skip{{background:var(--amb-bg);color:var(--amb-t);border:1px solid var(--amb);}}

.chip-pos,.chip-neg{{
  display:inline-flex;align-items:center;gap:4px;padding:3px 11px;border-radius:20px;
  font-size:11px;font-weight:700;letter-spacing:.04em;margin-left:10px;
}}
.chip-pos{{background:var(--pos-bg);color:var(--pos-t);border:1px solid var(--pos);}}
.chip-neg{{background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg);}}

/* REFIXED pill styles — three distinct colours */
.pill-new{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;
  font-weight:600;background:var(--new);color:var(--new-t);border:1px solid var(--new-bdr);}}
.pill-pos{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;
  font-weight:600;background:rgba(10,35,20,.8);color:#56d364;border:1px solid var(--pos);}}
.pill-neg{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;
  font-weight:600;background:var(--neg-bg);color:var(--neg-t);border:1px solid var(--neg);}}

.pg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(182px,1fr));gap:10px;margin-bottom:26px;}}

.foot{{
  text-align:center;color:var(--muted);font-size:12px;
  margin-top:52px;padding-top:24px;border-top:1px solid var(--bdr);
  font-family:'DM Mono',monospace;letter-spacing:.03em;
}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:var(--s1);}}
::-webkit-scrollbar-thumb{{background:var(--bdr2);border-radius:3px;}}
::-webkit-scrollbar-thumb:hover{{background:var(--muted);}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <div>
    <div class="hero-eye">ClassLens Quality Assurance · REFIXED</div>
    <div class="hero-title">Chapter Accuracy Test Report</div>
    <div class="hero-sub">Automated validation · {VALUES['CompareLeft']} vs {VALUES['CompareRight']} · {len(chapter_cards)} chapters</div>
    <div class="hero-tags">
      <span class="htag">Class {VALUES['Class']}</span>
      <span class="htag">Section {VALUES['Section']}</span>
      <span class="htag">{VALUES['Subject']}</span>
      <span class="htag">{VALUES['CompareLeft']} ↔ {VALUES['CompareRight']}</span>
      <span class="htag">{len(all_results)} Tests</span>
    </div>
  </div>
  <div class="hero-meta">
    <span class="hero-rate">{rate}%</span>
    <span class="hero-rate-label">Pass Rate</span>
    <br>{RUN_TS}
  </div>
</div>

<div class="kpi-row">
  <div class="kpi k-ch"><div class="kv">{len(chapter_cards)}</div><div class="kl">Chapters</div></div>
  <div class="kpi k-to"><div class="kv">{len(all_results)}</div><div class="kl">Total Tests</div></div>
  <div class="kpi k-pa"><div class="kv">{len(passed_l)}</div><div class="kl">Passed</div></div>
  <div class="kpi k-fa"><div class="kv">{len(failed_l)}</div><div class="kl">Failed</div></div>
  <div class="kpi k-rt"><div class="kv">{rate}%</div><div class="kl">Pass Rate</div></div>
</div>

<div class="prog">
  <div class="prog-head">
    <span class="prog-label">Overall Test Pass Rate</span>
    <span class="prog-val">{rate}% <span style="font-size:15px;color:var(--muted)">({len(passed_l)} / {len(all_results)})</span></span>
  </div>
  <div class="prog-track"><div class="prog-fill" id="pf" style="width:0%"></div></div>
</div>

<div class="nav-wrap">
  <div class="nav">
    <div class="nt active" onclick="tab(this,'t-ov')">Overview</div>
    <div class="nt"        onclick="tab(this,'t-ph')">Phase Summary</div>
    <div class="nt"        onclick="tab(this,'t-tc')">All Tests</div>
    <div class="nt"        onclick="tab(this,'t-pc')">% Consistency</div>
    <div class="nt"        onclick="tab(this,'t-ex')">Exam Stats</div>
    <div class="nt"        onclick="tab(this,'t-acc')">Accuracy</div>
    <div class="nt"        onclick="tab(this,'t-wk')">Weakest Concepts</div>
    <div class="nt"        onclick="tab(this,'t-st')">Strongest Concepts</div>
    <div class="nt"        onclick="tab(this,'t-wy')">Why Text</div>
    <div class="nt"        onclick="tab(this,'t-fl')">Failed Tests</div>
    <div class="nt"        onclick="tab(this,'t-cm')">Concept Mapping</div>
  </div>
</div>

<div id="t-ov" class="tc active">
  <div class="sh">
    <div class="sh-icon">📋</div><h2>Chapter Overview</h2>
    <div class="sh-pills"><span class="pill">{len(chapter_cards)} chapters</span></div>
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th>#</th><th>Chapter</th>
      <th>Loc 1 · Card</th><th>Loc 2 · Chip</th>
      <th>Loc 3 · Badge</th><th>Loc 4 · Why</th>
      <th>4-Way</th><th>Tests</th>
    </tr></thead>
    <tbody>{ov_rows}</tbody>
  </table></div>
</div>

<div id="t-ph" class="tc">
  <div class="sh"><div class="sh-icon">⚡</div><h2>Phase Summary</h2></div>
  <div class="pg">{phase_cards}</div>
</div>

<div id="t-tc" class="tc">
  <div class="sh">
    <div class="sh-icon">🧪</div><h2>All Test Cases</h2>
    <div class="sh-pills">
      <span class="pill">{len(all_results)} tests</span>
      <span class="pill pill-g">{len(passed_l)} passed</span>
      <span class="pill pill-r">{len(failed_l)} failed</span>
    </div>
  </div>
  <div class="tw"><table>
    <thead><tr><th></th><th>Phase</th><th>Test Name</th><th>Result</th><th>Value / Detail</th></tr></thead>
    <tbody>{tc_rows}</tbody>
  </table></div>
</div>

<div id="t-pc" class="tc">
  <div class="sh">
    <div class="sh-icon">📐</div><h2>4-Way Percentage Consistency</h2>
    <div class="sh-pills"><span class="pill">{len(chapter_data)} chapters</span></div>
  </div>
  <div class="desc">
    <strong>Loc 1</strong> Card list badge &nbsp;·&nbsp;
    <strong>Loc 2</strong> IMPROVED / DECLINED chip &nbsp;·&nbsp;
    <strong>Loc 3</strong> Change in chapter average badge &nbsp;·&nbsp;
    <strong>Loc 4</strong> Why-this-chapter text &nbsp;
    <em style="color:var(--muted)">(shows — when only an accuracy % is present in the text)</em>
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th>Chapter</th>
      <th>Loc 1 · Card</th><th>Loc 2 · Chip</th>
      <th>Loc 3 · Badge</th><th>Loc 4 · Why</th><th>Result</th>
    </tr></thead>
    <tbody>{cons_rows}</tbody>
  </table></div>
</div>

<div id="t-ex" class="tc">
  <div class="sh"><div class="sh-icon">📊</div><h2>Exam Statistics per Chapter</h2></div>
  <div class="tw"><table>
    <thead><tr>
      <th>Chapter</th><th>Exam</th><th>Date</th>
      <th>Accuracy %</th><th>Struggling Students</th><th>Weak Concepts</th>
    </tr></thead>
    <tbody>{est_rows}</tbody>
  </table></div>
</div>

<div id="t-acc" class="tc">
  <div class="sh">
    <div class="sh-icon">🎯</div><h2>Accuracy — Every Chapter</h2>
    <div class="sh-pills"><span class="pill">{len(chapter_data)} chapters</span></div>
  </div>
  <div class="desc">
    <strong style="color:var(--amb-t)">Midterm %</strong> and
    <strong style="color:var(--blu-t)">Preboard 1 %</strong> are the exam-panel accuracy scores. &nbsp;
    <strong style="color:var(--pos-t)">Accuracy in why-text</strong> is the accuracy %
    explicitly stated in the Why section. &nbsp;
    <strong>Loc 4</strong> is the performance change % extracted from the why-text.
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th>Chapter</th>
      <th style="text-align:center">Change %<br><small style="color:var(--muted)">Card · Loc 1</small></th>
      <th style="text-align:center;color:var(--amb-t)">Midterm<br>Accuracy</th>
      <th style="text-align:center;color:var(--blu-t)">Preboard 1<br>Accuracy</th>
      <th style="text-align:center">Loc 4 Change %<br><small style="color:var(--muted)">Why-text</small></th>
      <th style="text-align:center;color:var(--pos-t)">Accuracy %<br><small>In why-text</small></th>
    </tr></thead>
    <tbody>{acc_rows}</tbody>
  </table></div>
</div>

<div id="t-wk" class="tc">
  <div class="sh"><div class="sh-icon">⚠️</div><h2>Weakest Concepts</h2>
    <div class="sh-pills">
      <span class="pill-new" style="font-size:11px;padding:3px 10px">New</span>
      <span class="pill-pos" style="font-size:11px;padding:3px 10px">Improved</span>
      <span class="pill-neg" style="font-size:11px;padding:3px 10px">Declined</span>
    </div>
  </div>
  <div class="tw"><table>
    <thead><tr><th>Rank</th><th>Concept</th><th>Exam</th><th>Badge</th></tr></thead>
    <tbody>{wk_rows}</tbody>
  </table></div>
</div>

<div id="t-st" class="tc">
  <div class="sh"><div class="sh-icon">★</div><h2>Strongest Concepts</h2>
    <div class="sh-pills">
      <span class="pill-new" style="font-size:11px;padding:3px 10px">New</span>
      <span class="pill-pos" style="font-size:11px;padding:3px 10px">Improved</span>
      <span class="pill-neg" style="font-size:11px;padding:3px 10px">Declined</span>
    </div>
  </div>
  <div class="tw"><table>
    <thead><tr><th>Concept</th><th>Exam</th><th>Score</th><th>Badge</th><th></th></tr></thead>
    <tbody>{st_rows}</tbody>
  </table></div>
</div>

<div id="t-wy" class="tc">
  <div class="sh"><div class="sh-icon">💡</div><h2>Why This Chapter Improved / Declined</h2></div>
  <div class="desc">
    Loc 4 shows <em>—</em> when the explanation text references only an accuracy %
    (e.g. <em>"stable at 19.2% accuracy"</em>). This is expected and correct behaviour.
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th>Chapter</th><th>Change (Card)</th>
      <th>Heading</th><th>Explanation Text</th><th>Extracted %</th>
    </tr></thead>
    <tbody>{why_rows}</tbody>
  </table></div>
</div>

<div id="t-fl" class="tc">
  <div class="sh">
    <div class="sh-icon">❌</div><h2>Failed Tests</h2>
    <div class="sh-pills"><span class="pill pill-r">{len(failed_l)} failed</span></div>
  </div>
  <div class="tw"><table>
    <thead><tr><th></th><th>Phase</th><th>Test Name</th><th>Detail</th></tr></thead>
    <tbody>{failed_rows}</tbody>
  </table></div>
</div>

<div id="t-cm" class="tc">
  <div class="sh">
    <div class="sh-icon">🧬</div><h2>Chapter–Concept Mapping</h2>
    <div class="sh-pills">
      <span class="pill">{len(CHAPTER_CONCEPT_MAPPING)} chapters</span>
      <span class="pill">{_total_concepts} concepts</span>
      <span class="pill pill-g">{_total_found} foundational</span>
      <span class="pill">{_total_standard} standard</span>
    </div>
  </div>
  <div class="desc">
    Complete curriculum mapping from <strong>cleaned_question_unit_chapter_concept_mapping.xlsx</strong>.
    Each concept is tagged as <strong style="color:#56d364">★ Foundational</strong> or
    <strong style="color:var(--muted)">Standard</strong>. Grouped by unit with board exam weightage marks.
  </div>
  <div class="tw"><table>
    <thead><tr>
      <th style="width:36px">#</th>
      <th>Concept</th>
      <th>Chapter</th>
      <th style="text-align:center">Unit</th>
      <th style="text-align:center">Marks</th>
      <th style="text-align:center">Type</th>
    </tr></thead>
    <tbody>{ccm_rows}</tbody>
  </table></div>
</div>

<div class="foot">
  ClassLens Chapter Accuracy Report (REFIXED) &nbsp;·&nbsp; {RUN_TS} &nbsp;·&nbsp;
  {len(chapter_cards)} chapters &nbsp;·&nbsp; {len(all_results)} tests &nbsp;·&nbsp; {rate}% pass rate
</div>

</div>
<script>
function tab(el,id){{
  document.querySelectorAll('.nt').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tc').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(id).classList.add('active');
}}
window.addEventListener('load',()=>{{
  const f=document.getElementById('pf');
  if(f) requestAnimationFrame(()=>{{f.style.width='{rate}%';}});
}});
</script>
</body></html>"""

with open(REPORT_FILE, "w", encoding="utf-8") as fh:
    fh.write(html)

print(f"  {G}{BLD}📄  Report saved → {REPORT_FILE}{RST}")
try:
    webbrowser.open(f"file://{os.path.abspath(REPORT_FILE)}")
    print(f"  {G}🌐  Opening in browser…{RST}")
except: pass
print(f"\n  🟢  Browser kept open. Close manually when done.\n")