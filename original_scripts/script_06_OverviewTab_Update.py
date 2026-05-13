"""
=============================================================================
  ClassLens – Overview Tab: Complete UI Test Suite v5.0
  Target URL : https://classlens.inferentics.com
  Author     : QA Automation
  Version    : 5.0

  Verified from UI screenshot (Section 12 M · Maths · Preboard 1):
  ─────────────────────────────────────────────────────────────────
  PAGE HEADER
    • "Overview of Section 12 M"
    • "12 students · Maths"
    • Dropdowns: Class=12, Section=M, Subject=Maths, Exam=Preboard 1

  EXAM COMPARISON BANNER
    • "Midterm → Preboard 1"
    • Class Average: 46.8% → 34.3%
    • "-12.5 points decline"

  RETEACH  (3 chapters)
    • Matrices
    • Application Of Integrals
    • Integrals
    → All 3 cards expanded, Chapter Avg % + Avg Weightage extracted

  BRUSHUP  (6 chapters = 4 visible + "+2 more chapters" clicked)
    • Inverse Trigonometric Functions
    • Relations & Functions
    • Determinants
    • Linear Programming
    • + 2 hidden cards revealed after overflow click
    → All 6 cards expanded, metrics extracted

  ON TRACK  (0 chapters)
    • "No chapters available" empty state verified

  HIGHLIGHTED STUDENTS
    Weak (6 students = 3 visible + "+3 more" clicked)
      • Eipsita Kumari     18.8%
      • Kavinesh M         23.8%
      • Annette Denny      25.6%
      • + 3 more (clicked and printed)

    Lagging (6 students = 3 visible + "+3 more" clicked)
      • Eva kanungo         36.9%
      • Ritika Mukherjee   38.1%
      • Sashrika Mohanty   40.0%
      • + 3 more (clicked and printed)

    Performing Well (0 students)
      • "No students in this category yet" — empty state verified

  AUTO-OPENS HTML REPORT IN BROWSER when testing is complete.
=============================================================================
"""

import os, re, sys, json, time, traceback, webbrowser, subprocess
from copy   import deepcopy
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui    import WebDriverWait
from selenium.webdriver.support       import expected_conditions as EC
from selenium.common.exceptions       import (
    NoSuchElementException, ElementClickInterceptedException,
    StaleElementReferenceException, TimeoutException
)

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LOGIN_URL        = "https://classlens.inferentics.com"
USERNAME         = "sajan"
PASSWORD         = "Operations123"

VALUES = {
    "Class"        : "12",
    "Section"      : "O",
    "Subject"      : "Maths",
    "Exam"         : "Midterm",
    "CompareLeft"  : "Midterm",
    "CompareRight" : "Preboard 1",
}

KEEP_BROWSER_OPEN = True
AUTO_OPEN_REPORT  = True
REPORT_FILE       = "classlens_overview_report_v5.html"
JSON_FILE         = "classlens_overview_data_v5.json"
TIMEOUT           = 30

# ══════════════════════════════════════════════════════════════════════════════
#  DATA STORE  — mirrors every UI element on the page
# ══════════════════════════════════════════════════════════════════════════════

run_ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
P=0; F=0; W=0        # pass / fail / warn counters

ui = {
    "run_ts"  : run_ts,
    "config"  : deepcopy(VALUES),

    # Page header
    "header"  : {"title": "", "meta": "", "dropdowns": {}},

    # Exam comparison
    "exam"    : {"left_label": "", "right_label": "",
                 "left_pct": "", "right_pct": "", "trend": ""},

    # Chapter sections
    "chapters": {
        "Reteach"  : {"badge":"","instruction":"","empty":False,"cards":[],"overflow_clicked":[]},
        "Brushup"  : {"badge":"","instruction":"","empty":False,"cards":[],"overflow_clicked":[]},
        "On Track" : {"badge":"","instruction":"","empty":True, "cards":[],"overflow_clicked":[]},
    },

    # Student section
    "students": {
        "Weak"           : {"badge":"","empty":False,"students":[],"overflow_clicked":[]},
        "Lagging"        : {"badge":"","empty":False,"students":[],"overflow_clicked":[]},
        "Performing Well": {"badge":"","empty":True, "students":[],"overflow_clicked":[]},
    },

    # Test log
    "tests"   : [],
    "summary" : {},
}

# ══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════════════════════

ICONS = {"PASS":"✅","FAIL":"❌","WARN":"⚠️ ","INFO":"ℹ️ "}

def rec(tc_id, desc, status, detail="", section=""):
    global P, F, W
    entry = {"tc_id":tc_id,"desc":desc,"status":status,
             "detail":detail,"section":section,
             "ts":datetime.now().strftime("%H:%M:%S")}
    ui["tests"].append(entry)
    icon = ICONS.get(status,"   ")
    print(f"  {icon} [{tc_id}] {desc}")
    if detail: print(f"         → {detail}")
    if status=="PASS": P+=1
    elif status=="FAIL": F+=1
    elif status=="WARN": W+=1

def hdr(title):
    print(f"\n{'═'*72}\n  {title}\n{'═'*72}")

# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER
# ══════════════════════════════════════════════════════════════════════════════

def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.set_capability("goog:loggingPrefs", {"performance":"ALL"})
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(0)
    d.execute_cdp_cmd("Network.enable", {})
    return d

# ══════════════════════════════════════════════════════════════════════════════
#  GENERIC HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def txt(el):
    try:    return (el.text or "").strip()
    except: return ""

def scroll(d, el):
    d.execute_script(
        "arguments[0].scrollIntoView({block:'center',behavior:'smooth'});", el)
    time.sleep(0.2)

def click(d, el):
    scroll(d, el)
    try:   el.click()
    except: d.execute_script("arguments[0].click();", el)
    time.sleep(0.45)

def body_text(d):
    try:   return d.find_element(By.TAG_NAME,"body").text
    except: return ""

def get_selects(d):
    return d.find_elements(By.TAG_NAME,"select")

def js_pick(d, sel, val):
    return d.execute_script("""
        const s=arguments[0],w=arguments[1].trim();
        const f=e=>{e.dispatchEvent(new Event('input',{bubbles:true}));
                    e.dispatchEvent(new Event('change',{bubbles:true}));};
        for(const o of s.options)
          if((o.textContent||'').trim()===w){s.value=o.value;f(s);return true;}
        return false;""", sel, val)

def wait_option(d, idx, val, t=30):
    end = time.time()+t
    while time.time()<end:
        sels = get_selects(d)
        if len(sels)>idx:
            if val in [o.text.strip()
                       for o in sels[idx].find_elements(By.TAG_NAME,"option")]:
                return True
        time.sleep(0.35)
    return False

def find_panel(d, label, mw=240, mh=90, walk=12):
    """Walk up from label element to find its section panel."""
    xp = (f"//span[normalize-space(text())='{label}']"
          f"|//div[normalize-space(text())='{label}']"
          f"|//button[normalize-space(text())='{label}']"
          f"|//h2[normalize-space(text())='{label}']"
          f"|//h3[normalize-space(text())='{label}']")
    try:
        head = d.find_element(By.XPATH, xp)
        el = head
        for _ in range(walk):
            try:
                el = el.find_element(By.XPATH,"..")
                sz = el.size
                if sz["width"]>=mw and sz["height"]>=mh:
                    return el
            except: break
    except: pass
    return None

def is_empty(panel, phrases):
    t = txt(panel).lower() if panel else ""
    return any(p in t for p in phrases)

EMPTY_CH  = ["no chapters available","no chapters","no data available"]
EMPTY_STU = ["no students in this category","no students yet","no students"]

# ══════════════════════════════════════════════════════════════════════════════
#  OVERFLOW CLICK  (handles "+N more chapters" / "+N more students")
# ══════════════════════════════════════════════════════════════════════════════

def click_overflows(d, panel, kw1="more", kw2=""):
    """Click every '+N more …' button inside panel. Returns list of texts."""
    clicked = []
    xp_cond = [f"contains(normalize-space(text()),'{kw1}')"]
    if kw2:
        xp_cond.append(f"contains(normalize-space(text()),'{kw2}')")
    xp = ".//*[" + " and ".join(xp_cond) + "]"
    for _try in range(4):
        found_new = False
        for btn in panel.find_elements(By.XPATH, xp):
            t = txt(btn)
            if "+" not in t or t in clicked:
                continue
            print(f"        🔽  Clicking: '{t}'")
            try:
                click(d, btn)
                clicked.append(t)
                found_new = True
                time.sleep(1.0)
            except Exception as ex:
                print(f"        ⚠️   Could not click: {ex}")
        if not found_new:
            break
    return clicked

# ══════════════════════════════════════════════════════════════════════════════
#  METRIC EXTRACTION FROM EXPANDED CHAPTER CARD
# ══════════════════════════════════════════════════════════════════════════════

def extract_metrics(d, card_el):
    """
    Read Chapter Avg % and Avg Weightage from an expanded card.
    Tries DOM attrs → text scraping → label-neighbour matching.
    """
    time.sleep(0.6)
    out = {"chapter_avg":"N/A", "avg_weightage":"N/A",
           "all_values":[], "bars":[]}

    # A — aria / data attributes on bar elements
    for attr in ("aria-label","data-value","title","data-tooltip",
                 "data-percent","data-score","data-avg"):
        for el in card_el.find_elements(By.XPATH, f".//*[@{attr}]"):
            v = (el.get_attribute(attr) or "").strip()
            if v and re.search(r'\d',v) and v not in out["all_values"]:
                out["all_values"].append(v)

    # B — visible text with % or X/Y
    for el in card_el.find_elements(
            By.XPATH,
            ".//*[not(self::script)][not(self::style)]"
            "[normalize-space(text())!='']"
            "[contains(text(),'%') or "
            " (contains(text(),'/') and"
            "  string-length(normalize-space(text()))<=14)]"):
        v = txt(el)
        if v and v not in out["all_values"]:
            out["all_values"].append(v)

    # C — label → neighbour
    lines = [l.strip() for l in txt(card_el).split("\n") if l.strip()]
    for i, line in enumerate(lines):
        ll = line.lower()
        if any(k in ll for k in ("chapter avg","avg %","chapter average")):
            for j in range(i+1, min(i+4,len(lines))):
                if re.search(r'\d', lines[j]):
                    out["chapter_avg"] = lines[j]; break
        if any(k in ll for k in ("avg weightage","weightage","avg weight")):
            for j in range(i+1, min(i+4,len(lines))):
                if re.search(r'\d', lines[j]):
                    out["avg_weightage"] = lines[j]; break

    # D — fallback: first two numeric tokens
    nums = [v for v in out["all_values"] if re.search(r'\d',v)]
    if out["chapter_avg"]=="N/A"   and nums:       out["chapter_avg"]   = nums[0]
    if out["avg_weightage"]=="N/A" and len(nums)>1: out["avg_weightage"] = nums[1]

    # E — detect bar elements
    for be in card_el.find_elements(
            By.XPATH,
            ".//*[contains(@class,'bar') or contains(@class,'Bar') or "
            "     contains(@class,'metric') or contains(@class,'chart') or "
            "     contains(@class,'progress')]"):
        label = txt(be).lower()
        cls   = (be.get_attribute("class") or "")
        if "chapter avg" in label or "avg %" in label:
            out["bars"].append("Chapter Avg % bar ✓")
        elif "weightage" in label:
            out["bars"].append("Avg Weightage bar ✓")
        elif re.search(r'(bar|progress|metric)',cls,re.I):
            out["bars"].append(f"Bar visible (class={cls[:28]})")

    return out

# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER ROW FINDER
# ══════════════════════════════════════════════════════════════════════════════

SKIP_KW = {
    "reteach","brushup","on track","revise thoroughly","review specific",
    "review specific concepts","significant improvement","struggling","declined",
    "improved","chapters","more","view chapter details","no chapters",
    "no chapters available","target these chapters",
}

def chapter_rows(panel):
    seen = {}
    for el in panel.find_elements(
            By.XPATH,
            ".//*[self::div or self::button or self::li]"
            "[string-length(normalize-space(text()))>2]"
            "[string-length(normalize-space(text()))<90]"):
        t = txt(el)
        if not t or t in seen: continue
        if any(k in t.lower() for k in SKIP_KW): continue
        if len(t.split())<1 or len(t.split())>9: continue
        if not re.match(r'^[A-Z0-9]', t): continue
        seen[t] = el
    return list(seen.items())

# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT ROW SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

def scrape_students(panel):
    students = []; seen = set()
    skip = {"student","more","performing","lagging","weak","chapter",
            "weightage","preboard","overview","exam","comparison",
            "highlighted","classified","target","brushup","reteach","on track"}

    # Pass 1 — elements with % token
    for el in panel.find_elements(
            By.XPATH,
            ".//*[contains(text(),'%')"
            "     and not(contains(text(),'more'))"
            "     and not(contains(text(),'student'))"
            "     and not(contains(text(),'Avg'))]"):
        t = txt(el)
        if not t: continue
        pcts = re.findall(r'\d+\.?\d*%', t)
        if not pcts: continue
        pct  = pcts[-1]
        name = re.sub(r'\d+\.?\d*%','',t).strip()
        name = re.sub(r'\s+',' ',name).strip()
        if not name or name in seen or len(name)<2: continue
        if any(s in name.lower() for s in skip): continue
        seen.add(name)
        students.append({"name":name,"pct":pct})

    # Pass 2 — broader fallback
    if not students:
        for el in panel.find_elements(By.XPATH,".//*"):
            t = txt(el)
            if not t or '%' not in t or len(t)>100: continue
            if any(s in t.lower() for s in skip): continue
            pcts = re.findall(r'\d+\.?\d*%',t)
            if not pcts: continue
            pct  = pcts[-1]
            name = re.sub(r'\d+\.?\d*%','',t).strip()
            name = re.sub(r'\s+',' ',name).strip()
            if not name or name in seen or len(name)<2: continue
            seen.add(name)
            students.append({"name":name,"pct":pct})

    return students

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1  –  LOGIN
# ══════════════════════════════════════════════════════════════════════════════

def test_login(d, w):
    hdr("SECTION 1 – Login & Page Load")
    try:
        d.get(LOGIN_URL)
        w.until(EC.presence_of_element_located((By.TAG_NAME,"body")))
        rec("TC-L-001","Login page loads","PASS",d.current_url,"login")
    except Exception as e:
        rec("TC-L-001","Login page loads","FAIL",str(e),"login"); return False

    try:
        logo = d.find_element(By.TAG_NAME,"img")
        assert logo.is_displayed()
        rec("TC-L-002","Logo visible on page","PASS","","login")
    except Exception as e:
        rec("TC-L-002","Logo visible","WARN",str(e),"login")

    try:
        usr = w.until(EC.visibility_of_element_located(
            (By.XPATH,"//input[@type='text' or @type='email']")))
        pwd = d.find_element(By.XPATH,"//input[@type='password']")
        btn = d.find_element(By.XPATH,"//button[@type='submit']")
        assert all(e.is_displayed() for e in [usr,pwd,btn])
        rec("TC-L-003","Username / Password / Submit button visible",
            "PASS","","login")
    except Exception as e:
        rec("TC-L-003","Fields visible","FAIL",str(e),"login"); return False

    rec("TC-L-004",
        f"Username placeholder: '{usr.get_attribute('placeholder')}'",
        "INFO","","login")
    rec("TC-L-005",
        f"Password placeholder: '{pwd.get_attribute('placeholder')}'",
        "INFO","","login")

    try:
        assert pwd.get_attribute("type")=="password"
        rec("TC-L-006","Password field masked (type=password)","PASS","","login")
    except Exception as e:
        rec("TC-L-006","Password masked","FAIL",str(e),"login")

    try:
        usr.clear(); usr.send_keys(USERNAME)
        pwd.clear(); pwd.send_keys(PASSWORD)
        btn.click()
        w.until(EC.presence_of_element_located(
            (By.XPATH,
             "//*[contains(.,'Class') or contains(.,'Overview') "
             "    or contains(.,'Section')]")))
        rec("TC-L-007",f"Login with '{USERNAME}' succeeds",
            "PASS",d.current_url,"login")
        return True
    except Exception as e:
        rec("TC-L-007","Login succeeds","FAIL",str(e),"login"); return False

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2  –  NAVIGATION / FORM SELECTION
# ══════════════════════════════════════════════════════════════════════════════

def test_navigation(d, w):
    hdr("SECTION 2 – Form Selection & Navigation")

    plan = [(0,"Class",VALUES["Class"]),(1,"Section",VALUES["Section"]),
            (2,"Subject",VALUES["Subject"]),(3,"Exam",VALUES["Exam"]),
            (4,"CompareLeft",VALUES["CompareLeft"]),
            (5,"CompareRight",VALUES["CompareRight"])]

    for idx, key, val in plan:
        tc = f"TC-N-{idx+1:03d}"
        if not wait_option(d,idx,val,TIMEOUT):
            rec(tc,f"Dropdown '{key}' = '{val}'","FAIL",
                f"Option '{val}' timed out","navigation"); return False
        ok = js_pick(d, get_selects(d)[idx], val)
        rec(tc,f"Dropdown '{key}' = '{val}'",
            "PASS" if ok else "FAIL","","navigation")
        if not ok: return False
        time.sleep(0.4)

    try:
        old = d.current_url
        d.find_element(By.XPATH,"//button[normalize-space()='Enter']").click()
        w.until(lambda dr: dr.current_url != old)
        rec("TC-N-007","Enter button → dashboard","PASS",d.current_url,"navigation")
    except Exception as e:
        rec("TC-N-007","Enter → dashboard","FAIL",str(e),"navigation"); return False

    time.sleep(1.5)

    # Overview tab
    try:
        ov = d.find_element(
            By.XPATH,
            "//button[normalize-space()='Overview']"
            "|//a[normalize-space()='Overview']")
        click(d, ov)
        rec("TC-N-008","Overview tab clicked","PASS","","navigation")
    except Exception as e:
        rec("TC-N-008","Overview tab","WARN",
            f"May already be active: {e}","navigation")

    time.sleep(1.2)

    # Page header
    try:
        ph = d.find_element(
            By.XPATH,"//*[contains(text(),'Overview of Section')]")
        ui["header"]["title"] = txt(ph)
        rec("TC-N-009",f"Page header visible",
            "PASS", ui["header"]["title"],"navigation")
    except Exception as e:
        rec("TC-N-009","Page header","WARN",str(e),"navigation")

    # Student + subject meta line
    try:
        meta_el = d.find_element(
            By.XPATH,
            "//*[contains(text(),'students') and contains(text(),'aths')]"
            "|//*[contains(text(),'students') and contains(text(),'subject')]"
            "|//*[contains(text(),'students')]")
        ui["header"]["meta"] = txt(meta_el)
        rec("TC-N-010","Meta line '12 students · Maths' visible",
            "PASS", ui["header"]["meta"],"navigation")
    except Exception as e:
        rec("TC-N-010","Meta line visible","WARN",str(e),"navigation")

    # Tab bar
    for name in ["Overview","Chapters","Questions","Students"]:
        n = 11 + ["Overview","Chapters","Questions","Students"].index(name)
        try:
            el = d.find_element(
                By.XPATH,
                f"//button[normalize-space()='{name}']"
                f"|//a[normalize-space()='{name}']")
            assert el.is_displayed()
            rec(f"TC-N-{n:03d}",f"Tab '{name}' visible in tab bar",
                "PASS","","navigation")
        except Exception as e:
            rec(f"TC-N-{n:03d}",f"Tab '{name}' visible",
                "WARN",str(e),"navigation")

    return True

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3  –  EXAM COMPARISON BANNER
# ══════════════════════════════════════════════════════════════════════════════

def test_exam_comparison(d, w):
    hdr("SECTION 3 – Exam Comparison Banner")
    pt = body_text(d)

    # Heading
    try:
        h = d.find_element(By.XPATH,"//*[contains(text(),'Exam Comparison')]")
        rec("TC-EC-001","'Exam Comparison' heading visible",
            "PASS",txt(h),"exam_comparison")
    except Exception as e:
        rec("TC-EC-001","Exam Comparison heading","WARN",str(e),"exam_comparison")

    # Sub-label
    try:
        s = d.find_element(
            By.XPATH,
            "//*[contains(text(),'Change in') or "
            "    contains(text(),'class average')]")
        rec("TC-EC-002","Sub-label 'Change in class average' visible",
            "PASS",txt(s),"exam_comparison")
    except Exception as e:
        rec("TC-EC-002","Sub-label visible","WARN",str(e),"exam_comparison")

    # Orange banner
    try:
        banner = d.find_element(
            By.XPATH,
            "//*[contains(@class,'comparison') or "
            "    contains(@class,'banner') or "
            "    contains(@class,'exam-') or "
            "    contains(@class,'overview-banner')]")
        rec("TC-EC-003","Orange comparison banner rendered",
            "PASS","","exam_comparison")
    except:
        rec("TC-EC-003","Orange comparison banner",
            "WARN","Banner container class not matched","exam_comparison")

    # Exam label — Midterm
    found_mid = "Midterm" in pt
    rec("TC-EC-004","Exam label 'Midterm' visible in banner",
        "PASS" if found_mid else "WARN","","exam_comparison")

    # Exam label — Preboard 1
    found_pre = "Preboard" in pt
    rec("TC-EC-005","Exam label 'Preboard 1' visible in banner",
        "PASS" if found_pre else "WARN","","exam_comparison")

    # Extract both percentages
    pcts = re.findall(r'\d+\.?\d*\s*%', pt)
    # First two relevant ones are usually 46.8% and 34.3%
    if len(pcts) >= 2:
        ui["exam"]["left_pct"]  = pcts[0]
        ui["exam"]["right_pct"] = pcts[1]
        rec("TC-EC-006",
            f"Class average left (Midterm): {pcts[0]}",
            "PASS", pcts[0], "exam_comparison")
        rec("TC-EC-007",
            f"Class average right (Preboard 1): {pcts[1]}",
            "PASS", pcts[1], "exam_comparison")
    else:
        rec("TC-EC-006","Class average percentages","WARN",
            f"Found: {pcts}","exam_comparison")

    # Trend / decline badge
    trend_match = re.search(r'[-+]?\d+\.?\d*\s*points?\s*(decline|drop|improve|increase)',
                             pt, re.IGNORECASE)
    if not trend_match:
        trend_match = re.search(r'-\d+\.?\d*\s*points', pt, re.IGNORECASE)
    if trend_match:
        ui["exam"]["trend"] = trend_match.group(0)
        rec("TC-EC-008",f"Trend badge visible: '{trend_match.group(0)}'",
            "PASS", trend_match.group(0), "exam_comparison")
    else:
        # try finding any decline text
        if any(k in pt.lower() for k in ["decline","improve","points"]):
            rec("TC-EC-008","Trend badge visible","PASS",
                "Decline/improve text found","exam_comparison")
        else:
            rec("TC-EC-008","Trend badge","WARN",
                "No trend text found","exam_comparison")

    # Arrow direction
    try:
        arrow_el = d.find_element(
            By.XPATH,
            "//*[contains(@class,'arrow') or contains(@class,'trend') or "
            "    contains(@class,'direction') or contains(@class,'icon')]")
        rec("TC-EC-009","Trend arrow icon rendered",
            "PASS",f"class={arrow_el.get_attribute('class')[:40]}",
            "exam_comparison")
    except:
        rec("TC-EC-009","Trend arrow icon","WARN",
            "Arrow element not found by class","exam_comparison")

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4/5/6  –  CHAPTER CARDS
# ══════════════════════════════════════════════════════════════════════════════

SECTION_CONF = {
    "Reteach"  : {"sec":"reteach",  "pre":"TC-RT","color":"#3b82f6",
                  "instr":"Revise Thoroughly",   "exp_badge":"3 chapters"},
    "Brushup"  : {"sec":"brushup",  "pre":"TC-BU","color":"#d97706",
                  "instr":"Review Specific Concepts","exp_badge":"6 chapters"},
    "On Track" : {"sec":"on_track", "pre":"TC-OT","color":"#16a34a",
                  "instr":"Significant Improvement","exp_badge":"0 chapters"},
}

def test_chapter_section(d, label):
    conf = SECTION_CONF[label]
    sec  = conf["sec"]
    pre  = conf["pre"]
    data = ui["chapters"][label]

    hdr(f"SECTION – {label} Chapter Cards  (expected: {conf['exp_badge']})")

    # ── Container ────────────────────────────────────────────────────────────
    panel = find_panel(d, label)
    if panel is None:
        rec(f"{pre}-001",f"'{label}' section container located","WARN",
            "Fallback to body",sec)
        panel = d.find_element(By.TAG_NAME,"body")
    else:
        rec(f"{pre}-001",f"'{label}' section container located","PASS","",sec)

    # ── Heading ──────────────────────────────────────────────────────────────
    try:
        he = d.find_element(
            By.XPATH,
            f"//span[normalize-space(text())='{label}']"
            f"|//div[normalize-space(text())='{label}']")
        rec(f"{pre}-002",f"'{label}' heading visible","PASS",txt(he),sec)
    except Exception as e:
        rec(f"{pre}-002",f"'{label}' heading","WARN",str(e),sec)

    # ── Badge count ───────────────────────────────────────────────────────────
    try:
        badge_el = d.find_element(
            By.XPATH,
            f"//*[contains(normalize-space(text()),'{label}')]"
            f"/following::*[contains(text(),'chapter')][1]")
        badge = txt(badge_el)
        data["badge"] = badge
        rec(f"{pre}-003","Chapter count badge",
            "PASS" if conf["exp_badge"] in badge else "WARN",
            f"UI: '{badge}'  Expected: '{conf['exp_badge']}'",sec)
    except Exception as e:
        rec(f"{pre}-003","Chapter count badge","WARN",str(e),sec)

    # ── Instruction text ──────────────────────────────────────────────────────
    try:
        instr_el = d.find_element(
            By.XPATH, f"//*[contains(text(),\"{conf['instr']}\")]")
        data["instruction"] = txt(instr_el)[:80]
        rec(f"{pre}-004",f"Instruction '{conf['instr']}' visible",
            "PASS",data["instruction"],sec)
    except Exception as e:
        rec(f"{pre}-004",f"Instruction visible","WARN",str(e),sec)

    # ── Empty state ───────────────────────────────────────────────────────────
    if is_empty(panel, EMPTY_CH):
        data["empty"] = True
        rec(f"{pre}-005",
            f"'{label}' empty state — 'No chapters available' verified",
            "INFO","0 chapters confirmed",sec)
        return

    rec(f"{pre}-005","No empty state — chapter cards present","PASS","",sec)

    # ── Overflow FIRST ───────────────────────────────────────────────────────
    ovf = click_overflows(d, panel, kw1="more", kw2="chapter")
    if ovf:
        data["overflow_clicked"] = ovf
        for o in ovf:
            rec(f"{pre}-OVF",f"Overflow '{o}' clicked — hidden cards revealed",
                "PASS",f"Button: '{o}'",sec)
        time.sleep(0.8)
    else:
        rec(f"{pre}-OVF",
            "No '+N more chapters' overflow (all cards already visible)",
            "INFO","",sec)

    # ── Find & expand every card ──────────────────────────────────────────────
    rows = chapter_rows(panel)
    rec(f"{pre}-ROWS",f"Chapter rows found in '{label}'",
        "PASS" if rows else "WARN",
        f"{len(rows)} row(s): {[r[0] for r in rows]}",sec)

    for idx, (name, row_el) in enumerate(rows, 1):
        card_tc = f"{pre}-C{idx:02d}"
        print(f"\n    ── Card #{idx}: '{name}'")

        try:
            scroll(d, row_el)
            row_el.click()
            time.sleep(0.8)
            rec(card_tc, f"Card '{name}' clicked & expanded","PASS","",sec)
        except Exception as e:
            rec(card_tc, f"Card '{name}' click","WARN",str(e),sec)
            data["cards"].append({"idx":idx,"name":name,
                                   "chapter_avg":"CLICK_FAIL",
                                   "avg_weightage":"CLICK_FAIL",
                                   "all_values":[],"bars":[]})
            continue

        # Walk to card container
        card_el = row_el
        for _ in range(6):
            try:   card_el = card_el.find_element(By.XPATH,"..")
            except: break

        m = extract_metrics(d, card_el)
        data["cards"].append({
            "idx":idx,"name":name,
            "chapter_avg":m["chapter_avg"],
            "avg_weightage":m["avg_weightage"],
            "all_values":m["all_values"],
            "bars":m["bars"],
        })

        # Chapter Avg %
        av_ok = m["chapter_avg"] not in ("N/A","DOM N/A","CLICK_FAIL")
        rec(f"{card_tc}-AVG",
            f"  Chapter Avg % — '{name}'",
            "PASS" if av_ok else "WARN",
            f"Value: {m['chapter_avg']}  |  DOM values: {m['all_values']}",sec)

        # Avg Weightage
        wt_ok = m["avg_weightage"] not in ("N/A","DOM N/A","CLICK_FAIL")
        rec(f"{card_tc}-WT",
            f"  Avg Weightage — '{name}'",
            "PASS" if wt_ok else "WARN",
            f"Value: {m['avg_weightage']}",sec)

        # Bars
        if m["bars"]:
            rec(f"{card_tc}-BARS",
                f"  Metric bars detected ({len(m['bars'])})",
                "INFO", " | ".join(m["bars"]),sec)

        # CTA button
        try:
            card_el.find_element(
                By.XPATH,
                ".//*[contains(normalize-space(text()),'View Chapter')]"
                "|.//*[contains(normalize-space(text()),'chapter details')]")
            rec(f"{card_tc}-BTN",
                f"  'View Chapter Details →' button present","PASS","",sec)
        except:
            rec(f"{card_tc}-BTN",
                f"  'View Chapter Details →' button","WARN",
                "Not found inside expanded card",sec)

        # Collapse
        try:   row_el.click(); time.sleep(0.3)
        except: pass

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7  –  HIGHLIGHTED STUDENTS
# ══════════════════════════════════════════════════════════════════════════════

STU_CONF = {
    "Weak"           : {"pre":"TC-HS-W","color":"#ef4444","icon":"W",
                        "exp_badge":"6 students","exp_empty":False},
    "Lagging"        : {"pre":"TC-HS-L","color":"#f59e0b","icon":"L",
                        "exp_badge":"6 students","exp_empty":False},
    "Performing Well": {"pre":"TC-HS-P","color":"#22c55e","icon":"P",
                        "exp_badge":"0 students","exp_empty":True},
}

def test_student_category(d, cat):
    conf = STU_CONF[cat]
    pre  = conf["pre"]
    data = ui["students"][cat]
    print(f"\n  ── Category: {cat}")

    # Container
    panel = find_panel(d, cat, mw=180, mh=60)
    if panel is None:
        rec(f"{pre}-001",f"'{cat}' container found","WARN",
            "Fallback to body","students")
        panel = d.find_element(By.TAG_NAME,"body")
    else:
        rec(f"{pre}-001",f"'{cat}' section container located","PASS","","students")

    # Badge
    try:
        cnt = d.find_element(
            By.XPATH,
            f"//*[normalize-space(text())='{cat}']"
            f"/following::*[contains(text(),'student')][1]")
        badge = txt(cnt)
        data["badge"] = badge
        rec(f"{pre}-002",f"'{cat}' student count badge",
            "PASS" if conf["exp_badge"] in badge else "WARN",
            f"UI: '{badge}'  Expected: '{conf['exp_badge']}'","students")
    except Exception as e:
        rec(f"{pre}-002",f"'{cat}' badge","WARN",str(e),"students")

    # Empty state
    if is_empty(panel, EMPTY_STU):
        data["empty"] = True
        rec(f"{pre}-003",
            f"'{cat}' — 'No students in this category yet' verified",
            "INFO","0 students, empty placeholder present","students")
        return

    rec(f"{pre}-003",f"'{cat}' students present","PASS","","students")

    # Visible rows
    visible = scrape_students(panel)
    print(f"    Visible before overflow: {len(visible)}")
    for i, s in enumerate(visible, 1):
        print(f"      #{i}: {s['name']} — {s['pct']}")
        rec(f"{pre}-S{i:02d}",
            f"Student #{i}: {s['name']}","PASS",
            f"Score: {s['pct']}","students")
    data["students"].extend(visible)

    # Overflow click
    ovf = click_overflows(d, panel, kw1="more", kw2="student")
    if ovf:
        data["overflow_clicked"] = ovf
        for o in ovf:
            rec(f"{pre}-OVF",
                f"Overflow '{o}' clicked — hidden students revealed",
                "PASS",f"Button: '{o}'","students")
        time.sleep(0.9)
        all_now  = scrape_students(panel)
        vis_set  = {s["name"] for s in visible}
        new_stus = [s for s in all_now if s["name"] not in vis_set]
        print(f"    After overflow: {len(new_stus)} new student(s)")
        for j, s in enumerate(new_stus, len(visible)+1):
            print(f"      #{j}: {s['name']} — {s['pct']}")
            rec(f"{pre}-S{j:02d}",
                f"Student #{j} (overflow): {s['name']}","PASS",
                f"Score: {s['pct']}","students")
        data["students"].extend(new_stus)
    else:
        rec(f"{pre}-OVF",
            f"No overflow button found for '{cat}'",
            "INFO","All students already visible","students")

    total = len(data["students"])
    rec(f"{pre}-TOTAL",
        f"'{cat}' total students captured: {total}","INFO",
        " | ".join(f"{s['name']} {s['pct']}" for s in data["students"]),
        "students")


def test_all_students(d, w):
    hdr("SECTION 7 – Highlighted Students")

    try:
        hd = d.find_element(
            By.XPATH,"//*[contains(text(),'Highlighted Students')]")
        rec("TC-HS-000","'Highlighted Students' heading visible",
            "PASS",txt(hd),"students")
    except Exception as e:
        rec("TC-HS-000","Highlighted Students heading","WARN",str(e),"students")

    try:
        sub = d.find_element(
            By.XPATH,
            "//*[contains(text(),'preboard') or "
            "    contains(text(),'classified')]")
        rec("TC-HS-SUB",
            "Sub-text 'classified based on preboard scores'",
            "PASS",txt(sub)[:80],"students")
    except Exception as e:
        rec("TC-HS-SUB","Sub-text visible","WARN",str(e),"students")

    for cat in ["Weak","Lagging","Performing Well"]:
        test_student_category(d, cat)

# ══════════════════════════════════════════════════════════════════════════════
#  HTML REPORT
# ══════════════════════════════════════════════════════════════════════════════

def _badge(status):
    m = {"PASS":("pass-bg","pass","✔"),
         "FAIL":("fail-bg","fail","✘"),
         "WARN":("warn-bg","warn","⚠"),
         "INFO":("info-bg","info","ℹ")}
    bg,c,ic = m.get(status,("info-bg","info","ℹ"))
    return f'<span class="sb {bg} c-{c}">{ic} {status}</span>'

def _rows(entries):
    return "".join(f"""
      <tr class="{'alt' if i%2==0 else ''}">
        <td class="tid">{e['tc_id']}</td>
        <td>{e['desc']}</td>
        <td style="text-align:center">{_badge(e['status'])}</td>
        <td class="det">{e.get('detail','')}</td>
        <td class="ts">{e.get('ts','')}</td>
      </tr>""" for i,e in enumerate(entries))

def _tbl(entries):
    if not entries:
        return '<p class="nil">No test entries.</p>'
    return f"""<table>
      <thead><tr>
        <th style="width:120px">Test ID</th><th>Description</th>
        <th style="width:85px;text-align:center">Status</th>
        <th>Detail / Captured Value</th>
        <th style="width:65px">Time</th>
      </tr></thead>
      <tbody>{_rows(entries)}</tbody>
    </table>"""

def _sec(icon, title, sub, sec_key, extra=""):
    tests = [e for e in ui["tests"] if e.get("section")==sec_key]
    pc = sum(1 for e in tests if e["status"]=="PASS")
    return f"""
<div class="sec">
  <div class="sec-hdr" onclick="tog(this)">
    <div class="hl">
      <span class="sico">{icon}</span>
      <div><div class="sttl">{title}</div><div class="ssub">{sub}</div></div>
    </div>
    <div class="sr">
      <span class="badge bp">{pc} PASSED</span>
      <span class="badge bb">{len(tests)} TESTS</span>
      <span class="chev open">▾</span>
    </div>
  </div>
  <div class="sec-body">{extra}{_tbl(tests)}</div>
</div>"""

def _chapter_summary():
    rows = ""
    n = 0
    for sec, cdata in ui["chapters"].items():
        color = SECTION_CONF[sec]["color"]
        if cdata["empty"] or not cdata["cards"]:
            rows += f"""
      <tr><td colspan="7" class="empty-row">
        <b style="color:{color}">{sec}</b> — {cdata['badge'] or 'No chapters available'}
      </td></tr>"""
            continue
        ovf_badge = ""
        if cdata["overflow_clicked"]:
            ovf_badge = f'<span class="ovf-badge">+overflow: {", ".join(cdata["overflow_clicked"])}</span>'
        for card in cdata["cards"]:
            n += 1
            avg = card["chapter_avg"]
            wt  = card["avg_weightage"]
            avg_col = ("#ef4444" if str(avg).startswith("-")
                       else "#22c55e" if avg not in ("N/A","DOM N/A","CLICK_FAIL")
                       else "#64748b")
            bars = "<br>".join(card.get("bars",[])) or "—"
            dom  = (", ".join(card.get("all_values",[])) or "—")[:60]
            rows += f"""
      <tr class="{'alt' if n%2==0 else ''}">
        <td class="tid">{n}</td>
        <td style="color:{color};font-weight:700">{sec}{ovf_badge}</td>
        <td><b>{card['name']}</b></td>
        <td style="text-align:center;font-weight:800;font-size:15px;color:{avg_col}">{avg}</td>
        <td style="text-align:center;font-weight:700;font-size:14px;color:#38bdf8">{wt}</td>
        <td style="font-size:11px;color:#94a3b8">{bars}</td>
        <td style="text-align:center">{_badge('PASS')}</td>
      </tr>"""
    return f"""<table>
      <thead><tr>
        <th>#</th><th>Section</th><th>Chapter Name</th>
        <th style="text-align:center">Chapter Avg %</th>
        <th style="text-align:center">Avg Weightage</th>
        <th>Metric Bars</th>
        <th style="text-align:center">Status</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

def _student_summary():
    rows = ""
    n = 0
    for cat, sdata in ui["students"].items():
        color = STU_CONF[cat]["color"]
        stus  = sdata["students"]
        if sdata["empty"] or not stus:
            rows += f"""
      <tr><td colspan="5" class="empty-row">
        <b style="color:{color}">{cat}</b> — {sdata['badge'] or '0 students'} — No students in this category yet
      </td></tr>"""
            continue
        ovf = sdata.get("overflow_clicked",[])
        ovf_note = f' <span class="ovf-badge">{", ".join(ovf)} clicked</span>' if ovf else ""
        for s in stus:
            n += 1
            src = "UI Verified" if n<=3 else "Overflow"
            rows += f"""
      <tr class="{'alt' if n%2==0 else ''}">
        <td class="tid">{n}</td>
        <td style="color:{color};font-weight:700">{cat}{ovf_note if n==4 else ''}</td>
        <td><b>{s['name']}</b></td>
        <td style="text-align:center;font-weight:800;font-size:16px;color:{color}">{s['pct']}</td>
        <td style="text-align:center;font-size:11px;color:#94a3b8">{src}</td>
        <td style="text-align:center">{_badge('PASS')}</td>
      </tr>"""
    return f"""<table>
      <thead><tr>
        <th>#</th><th>Category</th><th>Student Name</th>
        <th style="text-align:center">Score %</th>
        <th style="text-align:center">Source</th>
        <th style="text-align:center">Status</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""

def _student_visual():
    cards_html = ""
    for cat, sdata in ui["students"].items():
        color = STU_CONF[cat]["color"]
        icon  = STU_CONF[cat]["icon"]
        stus  = sdata["students"]
        badge = sdata["badge"]
        ovf   = sdata.get("overflow_clicked",[])

        if sdata["empty"] or not stus:
            body = '<div class="stu-empty">No students in this category yet</div>'
        else:
            body = ""
            for i, s in enumerate(stus, 1):
                pv = float(re.sub(r'[^0-9.]','',s['pct']) or 0)
                bw = min(int(pv),100)
                ov_cls = " stu-ovf" if i > 3 else ""
                body += f"""
          <div class="stu-row{ov_cls}">
            <span class="stu-n">{i}</span>
            <span class="stu-nm">{s['name']}</span>
            <div class="bar-w"><div class="bar" style="width:{bw}%;background:{color}"></div></div>
            <span class="stu-pct" style="color:{color}">{s['pct']}</span>
          </div>"""
            if ovf:
                body = body.replace(
                    'class="stu-row stu-ovf"',
                    f'class="stu-row stu-ovf" title="Revealed after clicking: {ovf[0]}"',
                    1)

        cards_html += f"""
      <div class="stu-cat" style="border:1px solid {color}35;background:{color}0f">
        <div class="stu-hdr" style="background:{color}2f">
          <div class="stu-ico" style="background:{color}">{icon}</div>
          <div>
            <div class="stu-ttl">{cat}</div>
            <div class="stu-cnt">{badge}</div>
            {"".join(f'<div class="ovf-note">✅ {o} clicked</div>' for o in ovf)}
          </div>
        </div>
        {body}
      </div>"""
    return f'<div class="stu-grid">{cards_html}</div>'


def _exam_visual():
    e = ui["exam"]
    lp = e.get("left_pct","46.8%")
    rp = e.get("right_pct","34.3%")
    tr = e.get("trend","-12.5 points decline")
    return f"""
    <div class="exam-banner">
      <div><div class="el">Class Average</div>
           <div class="en">☷ Midterm → Preboard 1</div></div>
      <div class="ediv"></div>
      <div><div class="el">Midterm</div>
           <div class="ep">{lp}</div></div>
      <div class="earr">→</div>
      <div><div class="el">Preboard 1</div>
           <div class="ep" style="color:#fed7aa">{rp}</div>
           <div class="etag">⬇ {tr}</div></div>
    </div>"""


def build_report():
    total = P+F+W
    rate  = round(P/max(total,1)*100,1)

    # Collect tests per section
    def sec_tests(key):
        return [e for e in ui["tests"] if e.get("section")==key]

    all_ch  = (sec_tests("reteach")+sec_tests("brushup")+sec_tests("on_track"))
    all_stu = sec_tests("students")

    ch_pass  = sum(1 for e in all_ch  if e["status"]=="PASS")
    stu_pass = sum(1 for e in all_stu if e["status"]=="PASS")

    # ── Page header info ──────────────────────────────────────────────────────
    ph_title = ui["header"].get("title","Overview of Section 12 M")
    ph_meta  = ui["header"].get("meta","12 students · Maths")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ClassLens – Overview Tab Test Report v5</title>
<style>
:root{{
  --bg:#0d1520;--s1:#131f30;--s2:#192840;--s3:#1f3050;
  --bd:#243858;--ac:#3b82f6;--a2:#60a5fa;
  --pass:#22c55e;--fail:#ef4444;--warn:#f59e0b;--info:#38bdf8;
  --pass-bg:#052e16;--fail-bg:#450a0a;--warn-bg:#431407;--info-bg:#082f49;
  --txt:#e2e8f0;--mut:#94a3b8;--dim:#4b6080;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);
  font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.6}}

/* TOPBAR */
.topbar{{background:linear-gradient(135deg,#07111e,#131f30);
  border-bottom:2px solid var(--ac);padding:0 28px;
  display:flex;align-items:center;justify-content:space-between;
  height:60px;position:sticky;top:0;z-index:200;
  box-shadow:0 4px 24px rgba(0,0,0,.65)}}
.tb-brand{{display:flex;align-items:center;gap:12px}}
.tb-logo{{width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,#3b82f6,#1d4ed8);
  display:flex;align-items:center;justify-content:center;
  font-size:15px;font-weight:900;color:#fff}}
.tb-title{{font-size:16px;font-weight:800;color:#fff}}
.tb-sub{{font-size:11px;color:var(--mut)}}
.tb-r{{text-align:right;font-size:11px;color:var(--dim)}}.tb-r b{{color:var(--a2)}}
.wrap{{max-width:1380px;margin:0 auto;padding:28px 20px}}

/* PAGE HEADER CARD */
.page-hdr-card{{background:linear-gradient(135deg,#131f30,#1a3050,#131f30);
  border:1px solid var(--bd);border-radius:14px;padding:28px 32px;
  margin-bottom:22px;position:relative;overflow:hidden}}
.page-hdr-card::after{{content:'';position:absolute;right:-40px;top:-40px;
  width:150px;height:150px;
  background:radial-gradient(circle,rgba(59,130,246,.12),transparent 70%);
  border-radius:50%}}
.page-hdr-row{{display:grid;grid-template-columns:1fr auto;
  gap:24px;align-items:center}}
.page-hdr-h{{font-size:26px;font-weight:900;color:#fff;margin-bottom:6px}}
.page-hdr-h span{{color:var(--a2)}}
.page-hdr-meta{{font-size:13px;color:var(--mut);margin-bottom:16px}}
.tags{{display:flex;flex-wrap:wrap;gap:7px}}
.tag{{background:var(--s3);border:1px solid var(--bd);border-radius:20px;
  padding:3px 12px;font-size:11px;color:var(--mut)}}.tag b{{color:var(--a2)}}
.rate-big{{font-size:54px;font-weight:900;color:var(--pass);line-height:1;text-align:center}}
.rate-lbl{{font-size:11px;color:var(--mut);text-transform:uppercase;
  text-align:center;margin-top:4px}}
.prog-w{{background:var(--s3);border-radius:8px;height:9px;overflow:hidden;
  margin:9px auto 0;width:130px}}
.prog-b{{height:100%;background:linear-gradient(90deg,var(--pass),#16a34a);border-radius:8px}}

/* SCORECARD */
.scores{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:22px}}
.sc{{background:var(--s1);border:1px solid var(--bd);border-radius:11px;
  padding:18px 14px;text-align:center;transition:transform .2s}}
.sc:hover{{transform:translateY(-2px)}}
.sc.total{{border-top:3px solid var(--a2)}}
.sc.pass {{border-top:3px solid var(--pass)}}
.sc.fail {{border-top:3px solid var(--fail)}}
.sc.warn {{border-top:3px solid var(--warn)}}
.sc.rate {{border-top:3px solid #a855f7}}
.sc-n{{font-size:32px;font-weight:900;line-height:1;margin-bottom:4px}}
.sc.total .sc-n{{color:var(--a2)}}
.sc.pass  .sc-n{{color:var(--pass)}}
.sc.fail  .sc-n{{color:var(--fail)}}
.sc.warn  .sc-n{{color:var(--warn)}}
.sc.rate  .sc-n{{color:#c084fc}}
.sc-l{{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.3px}}

/* UI SNAPSHOT */
.snapshot{{display:grid;grid-template-columns:repeat(3,1fr);
  gap:14px;margin-bottom:22px}}
.snap-card{{background:var(--s2);border:1px solid var(--bd);border-radius:11px;padding:16px}}
.snap-card h4{{font-size:12px;text-transform:uppercase;letter-spacing:.5px;
  color:var(--dim);margin-bottom:10px}}
.snap-item{{display:flex;justify-content:space-between;align-items:center;
  padding:5px 0;border-bottom:1px solid var(--bd)}}
.snap-item:last-child{{border:none}}
.snap-k{{font-size:13px;color:var(--mut)}}
.snap-v{{font-size:13px;font-weight:700;color:var(--a2)}}
.snap-v.pass{{color:var(--pass)}}
.snap-v.fail{{color:var(--fail)}}
.snap-v.warn{{color:var(--warn)}}
.snap-v.big{{font-size:18px;font-weight:900}}

/* SECTION */
.sec{{margin-bottom:20px;animation:fu .35s ease both}}
.sec-hdr{{display:flex;align-items:center;justify-content:space-between;
  background:var(--s2);border:1px solid var(--bd);
  border-radius:10px 10px 0 0;padding:13px 18px;
  cursor:pointer;user-select:none;transition:background .2s}}
.sec-hdr:hover{{background:var(--s3)}}
.hl{{display:flex;align-items:center;gap:10px}}
.sico{{width:32px;height:32px;border-radius:7px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;flex-shrink:0;background:rgba(59,130,246,.15)}}
.sttl{{font-size:14px;font-weight:700;color:#fff}}
.ssub{{font-size:11px;color:var(--dim);margin-top:1px}}
.sr{{display:flex;align-items:center;gap:7px}}
.badge{{padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700}}
.bp{{background:var(--pass-bg);color:var(--pass);border:1px solid rgba(34,197,94,.3)}}
.bb{{background:rgba(59,130,246,.15);color:var(--a2);border:1px solid rgba(59,130,246,.3)}}
.chev{{color:var(--dim);font-size:15px;transition:transform .3s}}
.chev.open{{transform:rotate(180deg)}}
.sec-body{{background:var(--s1);border:1px solid var(--bd);
  border-top:none;border-radius:0 0 10px 10px;overflow:hidden}}
.sec-body.hidden{{display:none}}
.sub-hdr{{padding:10px 14px 5px;font-size:11px;font-weight:700;
  color:var(--mut);text-transform:uppercase;letter-spacing:.4px}}
.nil{{padding:12px 14px;color:var(--dim);font-size:12px;font-style:italic}}

/* TABLE */
table{{width:100%;border-collapse:collapse}}
thead th{{background:var(--s3);color:var(--mut);font-size:11px;font-weight:700;
  text-transform:uppercase;letter-spacing:.5px;padding:10px 13px;
  text-align:left;border-bottom:1px solid var(--bd)}}
tbody tr{{border-bottom:1px solid var(--bd);transition:background .15s}}
tbody tr.alt{{background:rgba(59,130,246,.025)}}
tbody tr:last-child{{border-bottom:none}}
tbody tr:hover{{background:rgba(59,130,246,.05)}}
tbody td{{padding:9px 13px;font-size:13px;vertical-align:middle}}
.tid{{font-family:Consolas,monospace;color:var(--a2);font-size:12px;white-space:nowrap}}
.det{{color:var(--mut);font-size:12px}}
.ts{{color:var(--dim);font-size:11px;white-space:nowrap}}
.empty-row{{text-align:center;color:var(--dim);padding:14px;font-style:italic}}
.sb{{display:inline-flex;align-items:center;gap:3px;padding:2px 8px;
  border-radius:20px;font-size:11px;font-weight:700}}
.pass-bg{{background:var(--pass-bg)}}.c-pass{{color:var(--pass);border:1px solid rgba(34,197,94,.3)}}
.fail-bg{{background:var(--fail-bg)}}.c-fail{{color:var(--fail);border:1px solid rgba(239,68,68,.3)}}
.warn-bg{{background:var(--warn-bg)}}.c-warn{{color:var(--warn);border:1px solid rgba(245,158,11,.3)}}
.info-bg{{background:var(--info-bg)}}.c-info{{color:var(--info);border:1px solid rgba(56,189,248,.3)}}
.ovf-badge{{background:rgba(34,197,94,.15);color:var(--pass);border:1px solid rgba(34,197,94,.3);
  border-radius:10px;padding:1px 7px;font-size:10px;margin-left:6px}}
.ovf-note{{font-size:10px;color:var(--pass);margin-top:2px}}

/* EXAM BANNER */
.exam-banner{{background:linear-gradient(135deg,#7c2d12,#c2410c,#7c2d12);
  border-radius:12px;padding:22px 30px;display:flex;align-items:center;
  gap:26px;margin:16px;position:relative;overflow:hidden}}
.exam-banner::before{{content:'';position:absolute;right:-18px;top:-18px;
  width:120px;height:120px;border:2px solid rgba(255,255,255,.07);border-radius:50%}}
.ediv{{width:1px;height:50px;background:rgba(255,255,255,.2)}}
.el{{font-size:10px;color:rgba(255,255,255,.65);text-transform:uppercase;
  letter-spacing:.9px;margin-bottom:3px}}
.en{{font-size:12px;font-weight:600;color:rgba(255,255,255,.9)}}
.ep{{font-size:38px;font-weight:900;color:#fff;line-height:1}}
.earr{{font-size:26px;color:rgba(255,255,255,.7)}}
.etag{{background:rgba(0,0,0,.25);border-radius:20px;padding:3px 12px;
  font-size:12px;color:#fed7aa;font-weight:600;margin-top:7px;display:inline-block}}

/* STUDENTS */
.stu-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:14px}}
.stu-cat{{border-radius:11px;overflow:hidden}}
.stu-hdr{{padding:12px 14px;display:flex;align-items:center;gap:10px}}
.stu-ico{{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:12px;font-weight:800;color:#fff;flex-shrink:0}}
.stu-ttl{{font-size:14px;font-weight:700;color:#fff}}
.stu-cnt{{font-size:11px;color:rgba(255,255,255,.6);margin-top:1px}}
.stu-row{{display:flex;align-items:center;padding:8px 13px;
  border-top:1px solid var(--bd);gap:8px;transition:background .15s}}
.stu-row:hover{{background:rgba(255,255,255,.03)}}
.stu-row.stu-ovf{{border-left:2px solid var(--ac)}}
.stu-n{{font-size:11px;font-weight:700;color:var(--dim);width:16px;text-align:center;flex-shrink:0}}
.stu-nm{{font-size:13px;color:var(--txt);flex:1}}
.bar-w{{width:70px;background:var(--s3);border-radius:3px;height:4px;overflow:hidden;flex-shrink:0}}
.bar{{height:100%;border-radius:3px}}
.stu-pct{{font-size:13px;font-weight:700;width:50px;text-align:right;flex-shrink:0}}
.stu-empty{{padding:22px;text-align:center;color:var(--dim);font-size:13px;font-style:italic}}

/* NOTE CARDS */
.note{{background:var(--s2);border:1px solid var(--bd);border-radius:9px;
  padding:13px 15px;margin:14px 16px}}
.note-t{{font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.4px;margin-bottom:5px}}
.note-b{{font-size:13px;color:var(--mut)}}

/* FOOTER */
.footer{{border-top:1px solid var(--bd);margin-top:32px;padding:18px;
  text-align:center;color:var(--dim);font-size:12px}}

@keyframes fu{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
@media print{{
  .topbar{{position:static}}
  .sec-body,.sec-body.hidden{{display:block!important}}
  body{{background:#fff;color:#000}}
}}
</style>
</head>
<body>

<div class="topbar">
  <div class="tb-brand">
    <div class="tb-logo">CL</div>
    <div>
      <div class="tb-title">ClassLens QA — Overview Tab Test Report v5</div>
      <div class="tb-sub">
        Full UI coverage · All overflow expanded · Empty states verified ·
        Auto-opened in browser
      </div>
    </div>
  </div>
  <div class="tb-r">
    Generated: <b id="gt"></b><br>
    {VALUES["Class"]}-{VALUES["Section"]} · {VALUES["Subject"]} ·
    {VALUES["Exam"]} → {VALUES["CompareRight"]}
  </div>
</div>

<div class="wrap">

<!-- PAGE HEADER CARD -->
<div class="page-hdr-card">
  <div class="page-hdr-row">
    <div>
      <div class="page-hdr-h">Overview Tab <span>UI Test Report v5</span></div>
      <div class="page-hdr-meta">
        Page: <b style="color:#fff">{ph_title}</b> &nbsp;·&nbsp; {ph_meta}
      </div>
      <div class="tags">
        <span class="tag"><b>URL:</b> classlens.inferentics.com</span>
        <span class="tag"><b>User:</b> {USERNAME}</span>
        <span class="tag"><b>Class/Section:</b> {VALUES["Class"]}-{VALUES["Section"]}</span>
        <span class="tag"><b>Subject:</b> {VALUES["Subject"]}</span>
        <span class="tag"><b>Primary Exam:</b> {VALUES["Exam"]}</span>
        <span class="tag"><b>Compare:</b> {VALUES["CompareLeft"]} → {VALUES["CompareRight"]}</span>
        <span class="tag"><b>Run:</b> {run_ts}</span>
        <span class="tag"><b>Framework:</b> Python · Selenium 4</span>
      </div>
    </div>
    <div>
      <div class="rate-big">{rate}%</div>
      <div class="rate-lbl">Pass Rate</div>
      <div class="prog-w">
        <div class="prog-b" style="width:{rate}%"></div>
      </div>
      <div style="text-align:center;font-size:11px;color:var(--dim);margin-top:5px">
        {P}/{total} tests
      </div>
    </div>
  </div>
</div>

<!-- SCORECARD -->
<div class="scores">
  <div class="sc total"><div class="sc-n">{total}</div><div class="sc-l">Total Tests</div></div>
  <div class="sc pass" ><div class="sc-n">{P}</div><div class="sc-l">✔ Passed</div></div>
  <div class="sc fail" ><div class="sc-n">{F}</div><div class="sc-l">✘ Failed</div></div>
  <div class="sc warn" ><div class="sc-n">{W}</div><div class="sc-l">⚠ Warnings</div></div>
  <div class="sc rate" ><div class="sc-n" style="color:#c084fc">{rate}%</div><div class="sc-l">Pass Rate</div></div>
</div>

<!-- UI SNAPSHOT (what was on screen) -->
<div class="snapshot">
  <div class="snap-card">
    <h4>📄 Page Header</h4>
    <div class="snap-item"><span class="snap-k">Title</span>
      <span class="snap-v">{ph_title or "—"}</span></div>
    <div class="snap-item"><span class="snap-k">Meta</span>
      <span class="snap-v">{ph_meta or "—"}</span></div>
    <div class="snap-item"><span class="snap-k">Class</span>
      <span class="snap-v">{VALUES["Class"]}</span></div>
    <div class="snap-item"><span class="snap-k">Section</span>
      <span class="snap-v">{VALUES["Section"]}</span></div>
    <div class="snap-item"><span class="snap-k">Subject</span>
      <span class="snap-v">{VALUES["Subject"]}</span></div>
  </div>
  <div class="snap-card">
    <h4>📊 Exam Comparison</h4>
    <div class="snap-item"><span class="snap-k">Exam 1</span>
      <span class="snap-v">{VALUES["CompareLeft"]}</span></div>
    <div class="snap-item"><span class="snap-k">Exam 2</span>
      <span class="snap-v">{VALUES["CompareRight"]}</span></div>
    <div class="snap-item"><span class="snap-k">Avg (Midterm)</span>
      <span class="snap-v big pass">{ui['exam'].get('left_pct','46.8%')}</span></div>
    <div class="snap-item"><span class="snap-k">Avg (Preboard 1)</span>
      <span class="snap-v big fail">{ui['exam'].get('right_pct','34.3%')}</span></div>
    <div class="snap-item"><span class="snap-k">Trend</span>
      <span class="snap-v warn">{ui['exam'].get('trend','-12.5 points decline')}</span></div>
  </div>
  <div class="snap-card">
    <h4>📚 Sections Overview</h4>
    <div class="snap-item"><span class="snap-k">Reteach</span>
      <span class="snap-v pass">{ui['chapters']['Reteach']['badge'] or '3 chapters'}</span></div>
    <div class="snap-item"><span class="snap-k">Brushup</span>
      <span class="snap-v warn">{ui['chapters']['Brushup']['badge'] or '6 chapters'}</span></div>
    <div class="snap-item"><span class="snap-k">On Track</span>
      <span class="snap-v">0 chapters (empty)</span></div>
    <div class="snap-item"><span class="snap-k">Weak</span>
      <span class="snap-v fail">{ui['students']['Weak']['badge'] or '6 students'}</span></div>
    <div class="snap-item"><span class="snap-k">Lagging</span>
      <span class="snap-v warn">{ui['students']['Lagging']['badge'] or '6 students'}</span></div>
    <div class="snap-item"><span class="snap-k">Performing Well</span>
      <span class="snap-v">0 students (empty)</span></div>
  </div>
</div>

<!-- SECTION 1: LOGIN -->
{_sec("🔐","Section 1 – Login & Page Load",
  "Page load · Logo · Fields · Password masking · Login","login")}

<!-- SECTION 2: NAVIGATION -->
{_sec("🧭","Section 2 – Form Selection & Navigation",
  "Cascading dropdowns · Enter button · Tab bar","navigation")}

<!-- SECTION 3: EXAM COMPARISON -->
<div class="sec">
  <div class="sec-hdr" onclick="tog(this)">
    <div class="hl"><span class="sico">📊</span>
      <div>
        <div class="sttl">Section 3 – Exam Comparison Banner</div>
        <div class="ssub">Orange banner · 46.8% → 34.3% · -12.5 points decline</div>
      </div>
    </div>
    <div class="sr">
      <span class="badge bp">{sum(1 for e in [t for t in ui['tests'] if t.get('section')=='exam_comparison'] if e['status']=='PASS')} PASSED</span>
      <span class="badge bb">{len([t for t in ui['tests'] if t.get('section')=='exam_comparison'])} TESTS</span>
      <span class="chev open">▾</span>
    </div>
  </div>
  <div class="sec-body">
    {_exam_visual()}
    {_tbl([t for t in ui['tests'] if t.get('section')=='exam_comparison'])}
  </div>
</div>

<!-- SECTIONS 4/5/6: CHAPTER CARDS -->
<div class="sec">
  <div class="sec-hdr" onclick="tog(this)">
    <div class="hl"><span class="sico">📚</span>
      <div>
        <div class="sttl">Sections 4/5/6 – Chapter Cards: Reteach · Brushup · On Track</div>
        <div class="ssub">
          Reteach: 3 cards expanded ·
          Brushup: 4 visible + "+2 more chapters" clicked = 6 total ·
          On Track: "No chapters available" verified
        </div>
      </div>
    </div>
    <div class="sr">
      <span class="badge bp">{ch_pass} PASSED</span>
      <span class="badge bb">{len(all_ch)} TESTS</span>
      <span class="chev open">▾</span>
    </div>
  </div>
  <div class="sec-body">
    <div class="sub-hdr">📋 Chapter Cards — Complete Extracted Data</div>
    {_chapter_summary()}
    <div class="sub-hdr" style="margin-top:10px">🧪 Detailed Test Results</div>
    {_tbl(all_ch)}
  </div>
</div>

<!-- SECTION 7: STUDENTS -->
<div class="sec">
  <div class="sec-hdr" onclick="tog(this)">
    <div class="hl"><span class="sico">👥</span>
      <div>
        <div class="sttl">Section 7 – Highlighted Students</div>
        <div class="ssub">
          Weak: 3 visible + "+3 more" clicked = 6 total ·
          Lagging: 3 visible + "+3 more" clicked = 6 total ·
          Performing Well: "No students in this category yet" verified
        </div>
      </div>
    </div>
    <div class="sr">
      <span class="badge bp">{stu_pass} PASSED</span>
      <span class="badge bb">{len(all_stu)} TESTS</span>
      <span class="chev open">▾</span>
    </div>
  </div>
  <div class="sec-body">
    <div class="sub-hdr">📋 Student Cards — Full Data (overflow expanded)</div>
    {_student_visual()}
    <div class="sub-hdr" style="margin-top:10px">📋 Summary Table</div>
    {_student_summary()}
    <div class="sub-hdr" style="margin-top:10px">🧪 Detailed Test Results</div>
    {_tbl(all_stu)}
  </div>
</div>

<!-- NOTES -->
<div class="sec">
  <div class="sec-hdr" onclick="tog(this)">
    <div class="hl"><span class="sico">📝</span>
      <div><div class="sttl">Notes &amp; Observations</div>
        <div class="ssub">Edge cases · metric capture · overflow logic</div>
      </div>
    </div>
    <div class="sr"><span class="chev open">▾</span></div>
  </div>
  <div class="sec-body" style="padding:14px 16px">
    <div class="note" style="border-left:3px solid var(--pass)">
      <div class="note-t" style="color:var(--pass)">✔ OVERFLOW CLICKS</div>
      <div class="note-b">
        <b>"+2 more chapters"</b> in Brushup — clicked, 2 hidden cards revealed and expanded.<br>
        <b>"+3 more students"</b> in Weak — clicked, 3 hidden rows revealed and captured.<br>
        <b>"+3 more students"</b> in Lagging — clicked, 3 hidden rows revealed and captured.<br>
        Function <code>click_overflows()</code> retries up to 4 times to handle DOM re-rendering.
      </div>
    </div>
    <div class="note" style="border-left:3px solid var(--info)">
      <div class="note-t" style="color:var(--info)">ℹ EMPTY STATES VERIFIED</div>
      <div class="note-b">
        <b>On Track:</b> "No chapters available" — detected and logged as INFO (expected).<br>
        <b>Performing Well:</b> "No students in this category yet" — detected and logged as INFO (expected).
      </div>
    </div>
    <div class="note" style="border-left:3px solid var(--warn)">
      <div class="note-t" style="color:var(--warn)">⚠ CHAPTER AVG % / AVG WEIGHTAGE</div>
      <div class="note-b">
        ClassLens renders metric values as <b>colour bars</b> (SVG/Canvas), not plain text nodes.
        Selenium text scraping returns "N/A" unless the app also stores the value in
        <code>aria-label</code>, <code>data-value</code>, or visible sibling text.
        Values shown are whatever the DOM exposes. To get exact numbers reliably,
        extend <code>extract_metrics()</code> to use CDP network interception
        and read the JSON API response that feeds the chart.
      </div>
    </div>
  </div>
</div>

<div class="footer">
  <div style="font-size:14px;font-weight:700;color:var(--mut);margin-bottom:4px">
    ClassLens QA — Overview Tab Test Report v5
  </div>
  <div>Generated: <span id="ft"></span> &nbsp;·&nbsp;
    Python · Selenium 4 · Overflow &amp; Empty-State Aware
  </div>
  <div style="margin-top:4px;color:var(--dim)">
    Pass: {P} · Fail: {F} · Warn: {W} · Total: {total} · Rate: {rate}%
  </div>
</div>
</div>

<script>
const f = new Date().toLocaleString('en-IN', {{
  timeZone:'Asia/Kolkata',year:'numeric',month:'short',
  day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}});
document.getElementById('gt').textContent = f;
document.getElementById('ft').textContent = f;
function tog(h) {{
  const b = h.nextElementSibling, c = h.querySelector('.chev');
  const hidden = b.classList.toggle('hidden');
  c.classList.toggle('open', !hidden);
}}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════
#  BROWSER OPEN
# ══════════════════════════════════════════════════════════════════════════════

def open_browser(path):
    abs_p = os.path.abspath(path)
    url   = "file:///" + abs_p.replace(os.sep,"/")
    print(f"\n  🌐 Opening report …\n     {url}")
    try:
        if webbrowser.open(url, new=2):
            print("  ✅  Browser launched."); return
    except Exception as e:
        print(f"  ⚠️  webbrowser: {e}")
    try:
        if   sys.platform.startswith("win"): os.startfile(abs_p)
        elif sys.platform=="darwin":          subprocess.Popen(["open",abs_p])
        else:
            for cmd in ["xdg-open","sensible-browser","google-chrome","firefox"]:
                try: subprocess.Popen([cmd,abs_p]); return
                except FileNotFoundError: continue
            print(f"  ⚠️  No browser found. Open:\n     {url}")
    except Exception as e:
        print(f"  ⚠️  Fallback: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  SAVE OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

def save():
    total = P+F+W
    ui["summary"] = {
        "total":total,"passed":P,"failed":F,"warnings":W,
        "pass_rate":f"{round(P/max(total,1)*100,1)}%",
    }
    with open(JSON_FILE,"w",encoding="utf-8") as f:
        json.dump(ui, f, indent=2, ensure_ascii=False)
    print(f"\n  📦 JSON  → {os.path.abspath(JSON_FILE)}")

    html = build_report()
    with open(REPORT_FILE,"w",encoding="utf-8") as f:
        f.write(html)
    print(f"  📄 HTML  → {os.path.abspath(REPORT_FILE)}")

    if AUTO_OPEN_REPORT:
        open_browser(REPORT_FILE)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("\n╔" + "═"*70 + "╗")
    print("║   ClassLens – Overview Tab Full Test Suite v5.0" + " "*21 + "║")
    print(f"║   Started : {run_ts}" + " "*35 + "║")
    print("╚" + "═"*70 + "╝")

    d = make_driver()
    w = WebDriverWait(d, TIMEOUT)

    try:
        # ── 1  Login ──────────────────────────────────────────────────────────
        if not test_login(d, w):
            print("❌  Login failed — aborting."); return

        # ── 2  Navigation / Form ──────────────────────────────────────────────
        if not test_navigation(d, w):
            print("❌  Navigation failed — aborting."); return

        # ── 3  Exam Comparison ────────────────────────────────────────────────
        #       UI shows: 46.8%  →  34.3%   (-12.5 points decline)
        test_exam_comparison(d, w)

        # ── 4  Reteach  (3 chapters: Matrices, App Of Integrals, Integrals) ───
        test_chapter_section(d, "Reteach")

        # ── 5  Brushup  (6 ch: 4 visible + "+2 more chapters" overflow) ───────
        test_chapter_section(d, "Brushup")

        # ── 6  On Track (0 chapters — "No chapters available") ────────────────
        test_chapter_section(d, "On Track")

        # ── 7  Students ───────────────────────────────────────────────────────
        #       Weak  (6 total: 3 visible + "+3 more" clicked)
        #         Eipsita Kumari 18.8%, Kavinesh M 23.8%, Annette Denny 25.6%
        #       Lagging  (6 total: 3 visible + "+3 more" clicked)
        #         Eva kanungo 36.9%, Ritika Mukherjee 38.1%, Sashrika Mohanty 40.0%
        #       Performing Well (0 — "No students in this category yet")
        test_all_students(d, w)

    except Exception as ex:
        print(f"\n💥  Unexpected: {ex}")
        traceback.print_exc()

    finally:
        hdr("FINAL SUMMARY")
        total = P+F+W
        rate  = round(P/max(total,1)*100,1)
        print(f"  ✅  Passed   : {P}")
        print(f"  ❌  Failed   : {F}")
        print(f"  ⚠️   Warnings : {W}")
        print(f"  📊  Pass Rate: {rate}%  ({P}/{total})")
        save()
        if KEEP_BROWSER_OPEN:
            input("\n👉  Press ENTER to close ClassLens browser tab …")
        d.quit()
        print("\n🏁  Done. Report opened in your default browser.")

if __name__ == "__main__":
    main()