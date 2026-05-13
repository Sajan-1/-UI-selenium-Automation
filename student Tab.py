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

if __name__ == "__main__":
    main()