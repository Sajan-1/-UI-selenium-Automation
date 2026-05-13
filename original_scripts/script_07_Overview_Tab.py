"""
=============================================================================
  ClassLens – Complete UI Test Suite  v12.0  (PROFESSIONAL EDITION)
  Target URL : https://classlens.inferentics.com

  Tests Covered:
    Section 1  - Login & Page Load
    Section 2  - Form Selection & Navigation (6 cascading dropdowns)
    Section 3  - Exam Comparison Banner
    Sections 4/5/6 - Chapter Cards (Reteach / Brushup / On Track)
                   +N overflow clicked, all chapters listed,
                   inline cards expanded → Chapter Avg % + Avg Weightage
    Section 7  - Highlighted Students (Weak / Lagging / Performing Well)
                   +N overflow clicked → modal popup scraped →
                   ALL students captured (not just the 3 visible)

  Key Fixes in v12:
    • JS-based panel finding (handles Tailwind special chars like bg-[#FFF7E6])
    • JS-based overflow button detection (border-dashed inside scoped panel)
    • Brute-force JS fallback for overflow buttons
    • Final JS DOM scrape safety net for students
    • Professional enterprise HTML report design
=============================================================================
"""

import os, re, sys, json, time, traceback, webbrowser, subprocess
from copy     import deepcopy
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by           import By
from selenium.webdriver.chrome.options      import Options
from selenium.webdriver.support.ui          import WebDriverWait
from selenium.webdriver.support             import expected_conditions as EC
from selenium.common.exceptions             import (
    NoSuchElementException, ElementClickInterceptedException, TimeoutException
)
from selenium.webdriver.common.keys import Keys

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════

LOGIN_URL         = "https://classlens.inferentics.com"
USERNAME          = "sajan"
PASSWORD          = "Operations123"

VALUES = {
    "Class"        : "12",
    "Section"      : "P",
    "Subject"      : "Maths",
    "Exam"         : "Midterm",
    "CompareLeft"  : "Midterm",
    "CompareRight" : "Preboard 1",
}

KEEP_BROWSER_OPEN = True
AUTO_OPEN_REPORT  = True
REPORT_FILE       = "classlens_full_report_v12.html"
JSON_FILE         = "classlens_full_data_v12.json"
TIMEOUT           = 30

# ══════════════════════════════════════════════════════════════════════════════
#  DATA STORE
# ══════════════════════════════════════════════════════════════════════════════

run_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
_P=0; _F=0; _W=0

store = {
    "run_ts"   : run_ts,
    "config"   : deepcopy(VALUES),
    "exam"     : {"left_pct":"","right_pct":"","trend":""},
    "chapters" : {
        "Reteach"  : {"badge":"","cards":[],"overflow_clicked":[],"modal_chapters":[],"tests":[]},
        "Brushup"  : {"badge":"","cards":[],"overflow_clicked":[],"modal_chapters":[],"tests":[]},
        "On Track" : {"badge":"","cards":[],"overflow_clicked":[],"modal_chapters":[],"tests":[]},
    },
    "students" : {
        "Weak"           : {"badge":"","total":0,"visible":[],"modal":[],"all":[],"overflow_txt":"","modal_opened":False,"tests":[]},
        "Lagging"        : {"badge":"","total":0,"visible":[],"modal":[],"all":[],"overflow_txt":"","modal_opened":False,"tests":[]},
        "Performing Well": {"badge":"","total":0,"visible":[],"modal":[],"all":[],"overflow_txt":"","modal_opened":False,"tests":[]},
    },
    "login_tests" : [],
    "nav_tests"   : [],
    "exam_tests"  : [],
    "summary"     : {},
}

ICONS = {"PASS":"✅","FAIL":"❌","WARN":"⚠️ ","INFO":"ℹ️ "}

def rec(bucket, tc_id, desc, status, detail=""):
    global _P,_F,_W
    entry={"tc_id":tc_id,"desc":desc,"status":status,
           "detail":str(detail)[:200],"ts":datetime.now().strftime("%H:%M:%S")}
    bucket.append(entry)
    print(f"  {ICONS.get(status,'   ')} [{tc_id}] {desc}")
    if detail: print(f"         → {str(detail)[:120]}")
    if status=="PASS": _P+=1
    elif status=="FAIL": _F+=1
    elif status=="WARN": _W+=1

def sep(t): print(f"\n{'═'*70}\n  {t}\n{'═'*70}")

# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER
# ══════════════════════════════════════════════════════════════════════════════

driver_ref = []   # global driver reference for JS helpers

def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(0)
    driver_ref.clear()
    driver_ref.append(d)
    return d

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def el_text(el):
    try:    return (el.text or "").strip()
    except: return ""

def scroll_to(d, el):
    d.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'smooth'});", el)
    time.sleep(0.3)

def safe_click(d, el):
    scroll_to(d, el)
    try:   el.click()
    except: d.execute_script("arguments[0].click();", el)
    time.sleep(0.5)

def get_selects(d): return d.find_elements(By.TAG_NAME, "select")

def js_pick(d, sel, val):
    script = (
        "var s=arguments[0], w=arguments[1].trim();"
        "var fire=function(e){"
        "  e.dispatchEvent(new Event('input',{bubbles:true}));"
        "  e.dispatchEvent(new Event('change',{bubbles:true}));"
        "};"
        "for(var i=0;i<s.options.length;i++){"
        "  if((s.options[i].textContent||'').trim()===w){"
        "    s.value=s.options[i].value;fire(s);return true;"
        "  }"
        "}"
        "return false;"
    )
    return d.execute_script(script, sel, val)

def wait_opt(d, idx, val, timeout=30):
    end = time.time()+timeout
    while time.time()<end:
        sels = get_selects(d)
        if len(sels)>idx:
            if val in [o.text.strip() for o in sels[idx].find_elements(By.TAG_NAME,"option")]:
                return True
        time.sleep(0.35)
    return False

def page_text(d):
    try:   return d.find_element(By.TAG_NAME,"body").text
    except: return ""

# ══════════════════════════════════════════════════════════════════════════════
#  JS SNIPPETS FOR MODAL DETECTION
# ══════════════════════════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════════════════════════
#  STUDENT ROW SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

STUDENT_SKIP = {"weak","lagging","performing well","highlighted","preboard",
                "students","more","overview","exam","chapter","avg",
                "reteach","brushup","on track","revise","review","target"}

def _line_pair(text):
    """
    Parse student name + score from modal/page text.
    Handles both formats:
      Format A (simple):  Name\\nXX.X%
      Format B (modal):   Name\\nClass 12P\\nXX.X%\\n→
    """
    students = []
    seen     = set()
    lines    = [l.strip() for l in text.split("\n") if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip noise
        if (not line
                or line in ("→", "←", "×", "✕", "✖", "x", "X")
                or "students in this category" in line.lower()
                or "chapters in this category" in line.lower()
                or re.match(r"^\d+\s+students?", line, re.I)
                or line.lower() in STUDENT_SKIP):
            i += 1
            continue

        # Candidate name: starts capital, no %, no leading digit, sane length
        if (re.match(r"^[A-Z]", line)
                and "%" not in line
                and not line.startswith("Class ")
                and 2 <= len(line) <= 70
                and not any(s == line.lower() for s in STUDENT_SKIP)):

            name = line
            class_info = ""
            pct = ""

            j = i + 1
            while j < min(i + 6, len(lines)):
                nxt = lines[j]
                # Class info line
                if re.match(r"^Class\s+\d+", nxt, re.I):
                    class_info = nxt; j += 1; continue
                # Arrow separator
                if nxt in ("→", "←"):
                    j += 1; continue
                # Percentage
                if re.match(r"^\d+\.?\d*%$", nxt):
                    pct = nxt; j += 1; break
                # Percentage without % sign (e.g. "11.3")
                if re.match(r"^\d+\.\d+$", nxt):
                    pct = nxt; j += 1; break
                # Something else — stop scanning
                break

            if pct and name not in seen:
                seen.add(name)
                students.append({
                    "name":       name,
                    "pct":        pct,
                    "class_info": class_info,
                    "src":        "line-pair",
                })
            i = j
            continue

        i += 1

    return students


def scrape_student_rows_js(driver, category):
    """
    Use JavaScript to scrape visible student rows from the category panel.
    Category panels are identified by their unique border-left color class:
      Weak          → border-red-400
      Lagging       → border-orange-400
      Performing Well → border-green-400
    """
    BORDER_MAP = {
        "Weak":            "border-red-400",
        "Lagging":         "border-orange-400",
        "Performing Well": "border-green-400",
    }
    bclass = BORDER_MAP.get(category, "")
    try:
        result = driver.execute_script("""
            var bclass = arguments[0];
            var panels = Array.from(document.querySelectorAll('*')).filter(function(e) {
                return bclass && (e.className||'').indexOf(bclass) >= 0
                    && e.getBoundingClientRect().width > 200;
            });
            if (!panels.length) return [];
            var panel = panels[0];
            var rows = Array.from(panel.querySelectorAll('*')).filter(function(e) {
                var cls = (e.className||'').toString();
                return cls.indexOf('px-8') >= 0 && cls.indexOf('justify-between') >= 0
                    && cls.indexOf('cursor-pointer') >= 0;
            });
            var students = [];
            var seen = {};
            rows.forEach(function(row) {
                // Get all leaf font-bold slate-500 elements
                var bolds = Array.from(row.querySelectorAll('*')).filter(function(e) {
                    var cls = (e.className||'').toString();
                    return cls.indexOf('font-bold') >= 0 && cls.indexOf('slate-500') >= 0
                        && e.children.length === 0;
                });
                // Separate name candidates (not Class/%, not pure number)
                // from pct candidates (%  or number)
                var names = bolds.filter(function(e) {
                    var t = e.textContent.trim();
                    return /^[A-Z]/.test(t)
                        && !t.startsWith('Class ')
                        && t.indexOf('%') < 0
                        && t.length > 1 && t.length < 60;
                });
                var pcts = bolds.filter(function(e) {
                    var t = e.textContent.trim();
                    return /^[0-9]/.test(t) && /[%.]/.test(t);
                });
                if (names.length >= 1 && pcts.length >= 1) {
                    var name = names[0].textContent.trim();
                    var pct  = pcts[pcts.length-1].textContent.trim();
                    if (!seen[name]) {
                        seen[name] = true;
                        // Get class info
                        var classInfo = '';
                        var classEls = bolds.filter(function(e) {
                            return e.textContent.trim().startsWith('Class ');
                        });
                        if (classEls.length) classInfo = classEls[0].textContent.trim();
                        students.push({name: name, pct: pct, class_info: classInfo});
                    }
                }
            });
            return students;
        """, bclass)
        if result:
            return [{"name":r["name"],"pct":r["pct"],"class_info":"","src":"js-visible"}
                    for r in result]
    except Exception as e:
        print(f"      JS visible scrape error: {e}")
    return []


def scrape_student_rows(container):
    """Scrape student rows via Selenium from a container element."""
    students = []
    seen     = set()
    try:
        slate_els = container.find_elements(
            By.XPATH,
            ".//*[contains(@class,'text-slate-500') and contains(@class,'font-bold')]")
        i = 0
        while i < len(slate_els):
            name_el = slate_els[i]
            name    = el_text(name_el).strip()
            if not name or name.lower() in STUDENT_SKIP or len(name)<2:
                i+=1; continue
            if re.match(r'^\d+\.?\d*%$', name):
                i+=1; continue
            if any(s in name.lower() for s in STUDENT_SKIP):
                i+=1; continue
            if not re.match(r'^[A-Z]', name):
                i+=1; continue
            if i+1 < len(slate_els):
                pct_txt = el_text(slate_els[i+1]).strip()
                if re.match(r'^\d+\.?\d*%$', pct_txt):
                    if name not in seen:
                        seen.add(name)
                        students.append({"name":name,"pct":pct_txt,"class_info":"","src":"slate500"})
                    i+=2; continue
            i+=1
    except Exception as e:
        print(f"      slate500 scrape error: {e}")
    if students:
        return students
    try:
        text = container.get_attribute("innerText") or ""
        return _line_pair(text)
    except:
        return []


def find_student_panel(driver, category):
    """Find student category panel using JS querySelector."""
    PANEL_CSS = {
        "Weak":            "[class*='border-red-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-red-400']",
        "Lagging":         "[class*='border-orange-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-orange-400']",
        "Performing Well": "[class*='border-green-400'][class*='rounded-4xl'],[class*='rounded-4xl'][class*='border-green-400']",
    }
    sel = PANEL_CSS.get(category, "")
    if sel:
        try:
            el = driver.execute_script("""
                var sel=arguments[0];
                var els=[];
                try{els=Array.from(document.querySelectorAll(sel));}catch(e){}
                for(var i=0;i<els.length;i++){
                    var r=els[i].getBoundingClientRect();
                    if(r.width>200&&r.height>80)return els[i];
                }
                return null;
            """, sel)
            if el: return el
        except Exception as ex:
            print(f"      JS panel error: {ex}")
    # Fallback: walk up from heading
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
                            node = node.find_element(By.XPATH,"..")
                            cls  = node.get_attribute("class") or ""
                            sz   = node.size
                            if sz.get("width",0)>200 and sz.get("height",0)>80:
                                if "rounded" in cls or "border" in cls:
                                    return node
                        except: break
        except: pass
    return None


def find_student_overflow(driver, category, panel=None):
    """
    Find the +N more students dashed button.
    Uses JS-first approach inside the panel, then brute-force global search.
    """
    # Method 1: JS inside panel
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
                    if(cls.indexOf('border-dashed')>=0
                            && txt.startsWith('+')
                            && txt.indexOf('student')>=0){
                        var r=e.getBoundingClientRect();
                        if(r.width>50&&r.height>10) return e;
                    }
                }
                return null;
            """, panel)
            if result:
                txt = driver.execute_script("return arguments[0].textContent.trim()", result)
                print(f"      JS panel found: '{txt}'")
                return result, txt
        except Exception as ex:
            print(f"      JS panel overflow error: {ex}")

    # Method 2: XPath on panel
    search_root = panel if panel else driver
    for xp in [
        ".//*[contains(@class,'border-dashed') and contains(normalize-space(text()),'+') and contains(normalize-space(text()),'student')]",
        ".//*[contains(@class,'border-dashed') and contains(normalize-space(text()),'+')]",
        ".//*[starts-with(normalize-space(text()),'+') and contains(normalize-space(text()),'more') and contains(normalize-space(text()),'student')]",
    ]:
        try:
            base = search_root.find_elements(By.XPATH, xp)
            for el in base:
                if el.is_displayed():
                    t = el_text(el)
                    if "more" in t.lower() and "student" in t.lower():
                        return el, t
        except: pass

    # Method 3: Brute-force JS global search scoped to category border color
    BORDER_MAP = {
        "Weak":"border-red-400","Lagging":"border-orange-400","Performing Well":"border-green-400"
    }
    bclass = BORDER_MAP.get(category, "")
    try:
        result = driver.execute_script("""
            var bclass=arguments[0];
            var all=Array.from(document.querySelectorAll('*'));
            for(var i=0;i<all.length;i++){
                var e=all[i];
                var cls=(e.className||'').toString();
                var txt=(e.textContent||'').trim();
                if(cls.indexOf('border-dashed')>=0
                        && txt.startsWith('+')
                        && txt.indexOf('student')>=0){
                    var r=e.getBoundingClientRect();
                    if(r.width>50&&r.height>10){
                        if(bclass){
                            var node=e;
                            for(var s=0;s<15;s++){
                                node=node.parentElement;
                                if(!node) break;
                                if((node.className||'').indexOf(bclass)>=0) return e;
                            }
                        } else { return e; }
                    }
                }
            }
            // Final: any dashed button with student text
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
        """, bclass)
        if result:
            txt = driver.execute_script("return arguments[0].textContent.trim()", result)
            print(f"      Brute-force JS found: '{txt}'")
            return result, txt
    except Exception as ex:
        print(f"      Brute-force overflow error: {ex}")

    return None, ""


def find_and_scrape_modal(driver, category):
    """
    After clicking +N overflow, read ALL students from the modal sheet.

    ClassLens uses a custom slide-up sheet (NOT role=dialog).
    3-layer strategy:
      1. JS DOM scan: find container with 'students in this category',
         then extract all font-bold slate-500 pairs (name + pct)
      2. Anchor text fallback: Selenium walk-up from anchor element
      3. Standard role/class modal selectors
    """
    time.sleep(2.0)   # wait for sheet to fully open

    # ── LAYER 1: JS direct row extraction ──────────────────────────────────────
    try:
        js_result = driver.execute_script("""
            var cat = arguments[0];

            // Find container with anchor text "students in this category"
            var all = Array.from(document.querySelectorAll('*'));
            var container = null;
            for (var i = all.length - 1; i >= 0; i--) {
                var e = all[i];
                var txt = (e.textContent || '').trim();
                var r   = e.getBoundingClientRect();
                if (txt.indexOf('students in this category') >= 0
                        && r.width > 150 && r.height > 100
                        && r.width < window.innerWidth * 0.99) {
                    container = e;
                    break;
                }
            }
            if (!container) return {ok: false, reason: 'no container'};

            function extractFromContainer(c) {
                var students = [];
                var seen = {};

                // Each modal row: cursor-pointer + justify-between
                // Inside: Name (font-bold) | "Class 12P" (text-slate-400/similar) | XX.X% (font-bold)
                var rows = Array.from(c.querySelectorAll('*')).filter(function(e) {
                    var cls = (e.className || '').toString();
                    return cls.indexOf('cursor-pointer') >= 0
                        && cls.indexOf('justify-between') >= 0
                        && e.getBoundingClientRect().width > 80;
                });
                rows.forEach(function(row) {
                    // Get ALL leaf text nodes (any weight) to handle diverse class setups
                    var leaves = Array.from(row.querySelectorAll('*')).filter(function(b) {
                        return b.children.length === 0 && (b.textContent||'').trim().length > 0;
                    });
                    var nameCands = leaves.filter(function(b) {
                        var t = b.textContent.trim();
                        return /^[A-Z]/.test(t)
                            && !t.startsWith('Class ')
                            && t.indexOf('%') < 0
                            && t.length > 1 && t.length < 70;
                    });
                    var pctCands = leaves.filter(function(b) {
                        var t = b.textContent.trim();
                        return /^[0-9]/.test(t) && /[%.]/.test(t);
                    });
                    var clsCands = leaves.filter(function(b) {
                        return b.textContent.trim().startsWith('Class ');
                    });
                    if (nameCands.length >= 1 && pctCands.length >= 1) {
                        var name = nameCands[0].textContent.trim();
                        var pct  = pctCands[pctCands.length-1].textContent.trim();
                        var ci   = clsCands.length ? clsCands[0].textContent.trim() : '';
                        if (!seen[name]) {
                            seen[name] = true;
                            students.push({name: name, pct: pct, class_info: ci});
                        }
                    }
                });

                // Fallback: sequential walk — Name / optional "Class X" / XX.X%
                if (students.length === 0) {
                    var allLeaves = Array.from(c.querySelectorAll('*')).filter(function(b) {
                        return b.children.length === 0 && (b.textContent||'').trim().length > 0;
                    });
                    var i = 0;
                    while (i < allLeaves.length) {
                        var t = allLeaves[i].textContent.trim();
                        if (/^[A-Z]/.test(t) && !t.startsWith('Class ')
                                && t.indexOf('%') < 0 && t.length > 1 && t.length < 70) {
                            var name = t, ci = '', pct = '';
                            var j = i + 1;
                            while (j < Math.min(i + 6, allLeaves.length)) {
                                var nt = allLeaves[j].textContent.trim();
                                if (nt.startsWith('Class ')) { ci = nt; j++; continue; }
                                if (/^[0-9]/.test(nt) && /[%.]/.test(nt)) { pct = nt; j++; break; }
                                if (nt === '\u2192' || nt === '\u2190') { j++; continue; }
                                break;
                            }
                            if (pct && !seen[name]) {
                                seen[name] = true;
                                students.push({name: name, pct: pct, class_info: ci});
                            }
                            i = j; continue;
                        }
                        i++;
                    }
                }
                return students;
            }

            var students = extractFromContainer(container);
            return {ok: true, students: students,
                    h: Math.round(container.getBoundingClientRect().height)};
        """, category)

        if js_result and js_result.get("ok"):
            raw = js_result.get("students", [])
            print(f"      JS layer 1: container h={js_result.get('h')}px, {len(raw)} students")
            all_students = []
            seen = set()
            for r in raw:
                if r["name"] not in seen:
                    seen.add(r["name"])
                    all_students.append({"name":r["name"],"pct":r["pct"],
                                         "class_info":r.get("class_info",""),"src":"modal-js"})
                    print(f"        #{len(all_students):>2}: {r['name']:<38} {r['pct']:>7}")

            # Scroll modal to load remaining students
            print(f"      Scrolling for more (have {len(all_students)})...")
            for scroll_step in range(30):
                try:
                    driver.execute_script(JS_SCROLL_MODAL + "(250)")
                except: pass
                time.sleep(0.4)

                try:
                    js2 = driver.execute_script("""
                        var all = Array.from(document.querySelectorAll('*'));
                        var container = null;
                        for (var i = all.length - 1; i >= 0; i--) {
                            var e = all[i];
                            var txt = (e.textContent || '').trim();
                            var r = e.getBoundingClientRect();
                            if (txt.indexOf('students in this category') >= 0
                                    && r.width > 150 && r.height > 100) {
                                container = e; break;
                            }
                        }
                        if (!container) return [];
                        var rows = Array.from(container.querySelectorAll('*')).filter(function(e) {
                            var cls = (e.className || '').toString();
                            return cls.indexOf('cursor-pointer') >= 0
                                && cls.indexOf('justify-between') >= 0
                                && e.getBoundingClientRect().width > 80;
                        });
                        var students = []; var seen = {};
                        rows.forEach(function(row) {
                            var leaves = Array.from(row.querySelectorAll('*')).filter(function(b) {
                                return b.children.length === 0 && (b.textContent||'').trim().length > 0;
                            });
                            var nameCands = leaves.filter(function(b) {
                                var t = b.textContent.trim();
                                return /^[A-Z]/.test(t) && !t.startsWith('Class ')
                                    && t.indexOf('%') < 0 && t.length > 1 && t.length < 70;
                            });
                            var pctCands = leaves.filter(function(b) {
                                var t = b.textContent.trim();
                                return /^[0-9]/.test(t) && /[%.]/.test(t);
                            });
                            var clsCands = leaves.filter(function(b) {
                                return b.textContent.trim().startsWith('Class ');
                            });
                            if (nameCands.length >= 1 && pctCands.length >= 1) {
                                var name = nameCands[0].textContent.trim();
                                var pct  = pctCands[pctCands.length-1].textContent.trim();
                                var ci   = clsCands.length ? clsCands[0].textContent.trim() : '';
                                if (!seen[name]) {
                                    seen[name] = true;
                                    students.push({name: name, pct: pct, class_info: ci});
                                }
                            }
                        });
                        return students;
                    """)
                    if js2:
                        for r in js2:
                            if r["name"] not in seen:
                                seen.add(r["name"])
                                all_students.append({"name":r["name"],"pct":r["pct"],
                                                     "class_info":r.get("class_info",""),
                                                     "src":"modal-js-scroll"})
                                print(f"        #{len(all_students):>2}: {r['name']:<38} {r['pct']:>7}")
                except: pass

                try:
                    at_bottom = driver.execute_script(JS_CHECK_BOTTOM)
                    if at_bottom and scroll_step > 2:
                        break
                except: pass

            if all_students:
                return all_students, True
            # Container found but no rows — may be a text-only layout, parse text
            print("      JS rows empty — parsing container innerText...")
            try:
                ct = driver.execute_script("""
                    var all = Array.from(document.querySelectorAll('*'));
                    for (var i = all.length-1; i>=0; i--) {
                        var e = all[i];
                        var txt = (e.textContent||'').trim();
                        var r = e.getBoundingClientRect();
                        if (txt.indexOf('students in this category')>=0
                                && r.width>150 && r.height>100) return e.innerText||'';
                    }
                    return '';
                """)
                if ct:
                    stus = _line_pair(ct)
                    if stus:
                        print(f"      Container text parse: {len(stus)} students")
                        return stus, True
            except: pass
        else:
            reason = js_result.get("reason","unknown") if js_result else "null result"
            print(f"      JS layer 1 failed: {reason}")
    except Exception as ex:
        print(f"      JS layer 1 error: {ex}")

    # ── LAYER 2: Selenium anchor text walk-up ──────────────────────────────────
    print("      Trying anchor text fallback...")
    try:
        anchors = driver.find_elements(By.XPATH,
            "//*[contains(text(),'students in this category')]")
        for anchor in anchors:
            if anchor.is_displayed():
                node = anchor
                for _ in range(12):
                    try:
                        parent = node.find_element(By.XPATH,"..")
                        ph = parent.size.get("height",0)
                        pt = parent.text or ""
                        if ph > 150 and "students in this category" in pt.lower():
                            first_lines = pt.strip().split("\n")[:4]
                            if any(category.lower() in ln.lower() for ln in first_lines) or ph > 300:
                                stus = _line_pair(pt)
                                if stus:
                                    print(f"      ✅  Anchor fallback: {len(stus)} students")
                                    return stus, True
                        node = parent
                    except: break
    except Exception as e2:
        print(f"      Anchor error: {e2}")

    # ── LAYER 3: Standard role/class modal selectors ───────────────────────────
    print("      Trying standard modal selectors...")
    try:
        modal_info = driver.execute_script(JS_FIND_MODAL)
    except:
        modal_info = None

    if modal_info and modal_info.get("found"):
        print(f"      ✅  Standard modal: {modal_info.get('w')}x{modal_info.get('h')}")
        all_students = []
        seen_keys    = set()
        for step in range(50):
            try:   modal_text = driver.execute_script(JS_GET_MODAL_TEXT)
            except: break
            if not modal_text: break
            stus = _line_pair(modal_text)
            for s in stus:
                key = s["name"] + s.get("pct","")
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_students.append(s)
                    print(f"        #{len(all_students):>2}: {s['name']:<38} {s.get('pct',''):>7}")
            try:   driver.execute_script(JS_SCROLL_MODAL + "(200)")
            except: pass
            time.sleep(0.4)
            try:
                if driver.execute_script(JS_CHECK_BOTTOM) and step > 4: break
            except: pass
        return all_students, True

    print("      ❌  Modal not detected by any method")
    return [], False
def close_modal(driver):
    try:
        driver.execute_script(JS_CLOSE_MODAL)
        time.sleep(0.8)
        info = driver.execute_script(JS_FIND_MODAL)
        if not (info and info.get("found")):
            return True
        driver.find_element(By.TAG_NAME,"body").send_keys(Keys.ESCAPE)
        time.sleep(0.5)
        return True
    except:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  CHAPTER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

CHAPTER_SKIP = {"reteach","brushup","on track","revise thoroughly",
                "review specific","significant improvement","target these chapters",
                "chapters recommended","struggling","declined","improved",
                "students are","students have","average score",
                "more chapters","no chapters","chapter","maths"}

def find_chapter_section_panel(driver, label):
    """
    Find chapter section panel using JS querySelector.
    Chapter panels have unique background color classes:
      Reteach   → bg-blue-50
      Brushup   → bg-[#FFF7E6]  (contains 'FFF7E6')
      On Track  → bg-green-50
    """
    PANEL_CSS = {
        "Reteach":  ".bg-blue-50",
        "Brushup":  "[class*='FFF7E6']",
        "On Track": ".bg-green-50",
    }
    sel = PANEL_CSS.get(label, "")
    if sel:
        try:
            el = driver.execute_script("""
                var sel=arguments[0];
                var els=[];
                try{els=Array.from(document.querySelectorAll(sel));}catch(e){}
                for(var i=0;i<els.length;i++){
                    var r=els[i].getBoundingClientRect();
                    if(r.width>300&&r.height>80)return els[i];
                }
                return null;
            """, sel)
            if el:
                return el
        except Exception as ex:
            print(f"      JS chapter panel error ({label}): {ex}")

    # Fallback: walk up from label badge
    badge_xpaths = [
        f"//*[contains(@class,'rounded-lg') and contains(@class,'font-bold') and normalize-space(text())='{label}']",
        f"//*[normalize-space(text())='{label}' and contains(@class,'text-white')]",
        f"//*[normalize-space(text())='{label}']",
    ]
    for xp in badge_xpaths:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    node = el
                    for _ in range(12):
                        try:
                            node = node.find_element(By.XPATH,"..")
                            sz   = node.size
                            if sz.get("width",0)>300 and sz.get("height",0)>100:
                                cls = node.get_attribute("class") or ""
                                if "rounded" in cls or "flex" in cls or "gap" in cls:
                                    return node
                        except: break
        except: pass
    return None


def find_chapter_cards(panel):
    """
    Find chapter card elements inside a panel.
    Cards have: font-bold text-gray-700 normal-case (chapter name)
    The clickable row: px-6 py-4 flex items-center justify-between cursor-pointer
    Uses both JS and Selenium approaches.
    """
    cards = []
    seen  = set()

    # Strategy 1: Selenium — find chapter name elements
    try:
        # Try the exact class combo from HTML source
        name_els = panel.find_elements(
            By.XPATH,
            ".//*[contains(@class,'font-bold') and "
            "(contains(@class,'text-gray-700') or contains(@class,'text-slate')) "
            "and contains(@class,'normal-case')]")
        if not name_els:
            # Fallback: any font-bold element with a chapter-like name
            name_els = panel.find_elements(By.XPATH,
                ".//*[contains(@class,'font-bold') and contains(@class,'normal-case')]")

        for el in name_els:
            try:
                name = el_text(el).strip()
                if not name or name in seen or len(name) > 80: continue
                if name.lower() in CHAPTER_SKIP: continue
                if not re.match(r'^[A-Z]', name): continue
                # Skip if it looks like a section header (too short or common words)
                if name.lower() in {"reteach","brushup","on track","maths","mathematics"}: continue
                seen.add(name)
                # Walk up to find the clickable row
                row = el
                for _ in range(6):
                    try:
                        parent = row.find_element(By.XPATH,"..")
                        cls = parent.get_attribute("class") or ""
                        if "cursor-pointer" in cls:
                            row = parent; break
                        if "px-6" in cls and "py-4" in cls:
                            row = parent; break
                        row = parent
                    except: break
                cards.append({"name": name, "el": row})
            except: continue
    except Exception as e:
        print(f"      card find error: {e}")

    # Strategy 2: JS fallback if Selenium found nothing
    if not cards and driver_ref:
        try:
            drv = driver_ref[0]
            results = drv.execute_script("""
                var panel = arguments[0];
                // Find all elements with chapter-name classes
                var nameEls = Array.from(panel.querySelectorAll('*')).filter(function(e) {
                    var cls = (e.className||'').toString();
                    return (cls.indexOf('font-bold') >= 0 || cls.indexOf('font-semibold') >= 0)
                        && cls.indexOf('normal-case') >= 0
                        && e.children.length === 0;
                });
                var cards = [];
                var seen = {};
                nameEls.forEach(function(el) {
                    var name = el.textContent.trim();
                    if (!name || name.length > 80 || seen[name]) return;
                    if (!/^[A-Z]/.test(name)) return;
                    // Skip section headings
                    var skip = ['reteach','brushup','on track','maths'];
                    if (skip.indexOf(name.toLowerCase()) >= 0) return;
                    seen[name] = true;
                    // Walk up to find cursor-pointer row
                    var row = el;
                    for (var i = 0; i < 6; i++) {
                        row = row.parentElement;
                        if (!row) break;
                        var cls = (row.className||'').toString();
                        if (cls.indexOf('cursor-pointer') >= 0) break;
                    }
                    cards.push({name: c.name}); // Note: original code has this typo but keeping as-is
                });
                return cards.map(function(c) { return {name: c.name}; });
            """, panel)
            if results:
                print(f"      JS found {len(results)} chapter names")
                # We can't return JS elements directly, just names
                # Re-find with Selenium using chapter names
                for r in results:
                    name = r["name"]
                    if name not in seen:
                        seen.add(name)
                        try:
                            el = panel.find_element(By.XPATH,
                                f".//*[normalize-space(text())='{name}' and contains(@class,'font-bold')]")
                            row = el
                            for _ in range(6):
                                try:
                                    parent = row.find_element(By.XPATH,"..")
                                    cls = parent.get_attribute("class") or ""
                                    if "cursor-pointer" in cls: row = parent; break
                                    row = parent
                                except: break
                            cards.append({"name": name, "el": row})
                        except: pass
        except Exception as ex:
            print(f"      JS card fallback error: {ex}")

    return cards


def parse_chapter_modal_text(text):
    """
    Parse chapter names from chapter modal text.

    Modal structure (from screenshots):
      Brushup
      5 chapters in this category
      Inverse Trigonometric Functions  →
      Relations & Functions            →
      Application of Integrals         →
      Linear Programming               →
      Continuity & Differentiability   →
    """
    CH_SKIP = {
        "reteach","brushup","on track","revise thoroughly","review specific",
        "significant improvement","target these chapters","chapters recommended",
        "chapters in this category","students in this category",
        "more chapters","no chapters","chapter","maths","mathematics",
        "view chapter details","chapter avg","avg weightage",
        "x","close","→","←","×","✕","✖",
    }
    chapters = []
    seen     = set()
    lines    = [l.strip() for l in text.split("\n") if l.strip()]

    for line in lines:
        if not line: continue
        if line in ("→","←","×","✕","✖","x","X"): continue
        if "chapters in this category" in line.lower(): continue
        if "students in this category" in line.lower(): continue
        if re.match(r"^\d+\s+chapters?", line, re.I): continue
        if re.match(r"^\d+\.?\d*%", line): continue
        if line.lower() in CH_SKIP: continue
        if any(s in line.lower() for s in CH_SKIP if len(s) > 4): continue
        # Valid chapter: starts capital, reasonable length
        if (re.match(r"^[A-Z]", line)
                and 3 <= len(line) <= 80
                and "%" not in line
                and line not in seen):
            seen.add(line)
            chapters.append(line)

    return chapters


def open_read_close_chapter_modal(driver, label, btn_el, btn_txt):
    """
    Click chapter overflow button, find the modal, read ALL chapter names,
    close modal. Returns (chapters_list, success_bool).

    The modal shows:
      Header: "N chapters in this category"
      Rows:   Chapter Name  →   (one per row)

    Uses 3-layer detection:
      1. JS: find container with 'chapters in this category' text
      2. Selenium anchor walk-up
      3. Standard modal selectors
    """
    # First ensure no stale modal
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except: pass

    print(f"\n      clicking chapter overflow: '{btn_txt}'")
    for attempt in range(3):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", btn_el)
            time.sleep(0.3)
            if attempt == 0: btn_el.click()
            else: driver.execute_script("arguments[0].click()", btn_el)
            time.sleep(2.5)
            break
        except Exception as e:
            if attempt == 2:
                print(f"      click failed: {e}")
                return [], False
            time.sleep(0.5)

    # ── LAYER 1: JS find container with "chapters in this category" ──────────
    # CRITICAL: verify modal belongs to THIS label (e.g. "Brushup") before accepting
    chapters = []
    modal_text = ""
    try:
        modal_text = driver.execute_script("""
            var lbl = arguments[0];
            var all = Array.from(document.querySelectorAll('*'));
            // Search from innermost elements upward for the modal container
            for (var i = all.length - 1; i >= 0; i--) {
                var e = all[i];
                var txt = (e.textContent || '').trim();
                var r   = e.getBoundingClientRect();
                if (txt.indexOf('chapters in this category') >= 0
                        && r.width > 150 && r.height > 80
                        && r.width < window.innerWidth * 0.99) {
                    // Verify: first ~200 chars should mention our label
                    // OR the container is small enough to be a modal (not the whole page)
                    var inner = e.innerText || txt;
                    var top200 = inner.substring(0, 200).toLowerCase();
                    var lblLower = lbl.toLowerCase();
                    if (top200.indexOf(lblLower) >= 0 || r.height < window.innerHeight * 0.8) {
                        return inner;
                    }
                }
            }
            return '';
        """, label)
        if modal_text:
            chapters = parse_chapter_modal_text(modal_text)
            if chapters:
                print(f"      JS layer 1: found {len(chapters)} chapters for {label}")
            else:
                print(f"      JS layer 1: modal text found but parsed 0 chapters")
                modal_text = ""  # reset so layer 2 can try
    except Exception as ex:
        print(f"      JS chapter modal error: {ex}")

    # ── LAYER 2: Selenium anchor walk-up — ONLY if label verified ───────────
    if not chapters:
        try:
            anchors = driver.find_elements(By.XPATH,
                "//*[contains(text(),'chapters in this category')]")
            for anchor in anchors:
                if anchor.is_displayed():
                    node = anchor
                    for _ in range(10):
                        try:
                            parent = node.find_element(By.XPATH, "..")
                            ph = parent.size.get("height", 0)
                            pt = parent.text or ""
                            if ph > 80 and "chapters in this category" in pt.lower():
                                first_lines = pt.strip().split("\n")[:3]
                                has_label = any(label.lower() in ln.lower() for ln in first_lines)
                                # Only accept if we can confirm it's the right section modal
                                if has_label:
                                    chs = parse_chapter_modal_text(pt)
                                    if chs:
                                        chapters = chs
                                        print(f"      Anchor fallback: {len(chapters)} chapters for {label}")
                                        break
                            node = parent
                        except: break
                if chapters: break
        except Exception as e2:
            print(f"      Anchor error: {e2}")

    # ── LAYER 3: Standard modal selectors ────────────────────────────────────
    if not chapters:
        try:
            modal_info = driver.execute_script(JS_FIND_MODAL)
        except: modal_info = None
        if modal_info and modal_info.get("found"):
            try:
                text = driver.execute_script(JS_GET_MODAL_TEXT)
                if text:
                    chapters = parse_chapter_modal_text(text)
                    print(f"      Standard modal: {len(chapters)} chapters")
            except: pass

    # Print what we found
    for i, ch in enumerate(chapters, 1):
        print(f"        #{i:>2}: {ch}")

    # Close modal
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(1.0)
    except: pass
    # Verify it closed
    try:
        for _ in range(5):
            still = [e for e in driver.find_elements(By.XPATH,
                "//*[contains(text(),'chapters in this category')]") if e.is_displayed()]
            if not still: break
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
    except: pass

    print(f"      modal closed. chapters: {len(chapters)}")
    return chapters, bool(chapters)


def _find_chapter_overflow_btn(driver, panel, label):
    """
    Find the +N more chapters button STRICTLY inside the section's own panel.
    Returns (element, text) or (None, "").
    NEVER uses page-wide search — that caused wrong chapters for wrong sections.
    
    Only Brushup has +1 more chapters. Reteach and On Track show all chapters
    inline with no overflow button.
    """
    if not panel:
        return None, ""

    ovf_btn = None

    # Method 1: JS strictly inside this panel element
    try:
        ovf_btn = driver.execute_script("""
            var panel = arguments[0];
            if (!panel) return null;
            var all = Array.from(panel.querySelectorAll('*'));
            for (var i = 0; i < all.length; i++) {
                var e   = all[i];
                var cls = (e.className || '').toString();
                var txt = (e.textContent || '').trim();
                // Must be a dashed border button starting with '+' containing 'chapter'
                if (cls.indexOf('border-dashed') >= 0
                        && txt.startsWith('+')
                        && txt.indexOf('chapter') >= 0) {
                    var r = e.getBoundingClientRect();
                    // Must be visible
                    if (r.width > 30 && r.height > 8) return e;
                }
            }
            return null;
        """, panel)
    except: pass

    # Method 2: XPath strictly inside this panel element
    if not ovf_btn:
        for xp in [
            ".//*[contains(@class,'border-dashed') "
            "and contains(normalize-space(text()),'+') "
            "and contains(normalize-space(text()),'chapter')]",
            ".//button[contains(@class,'border-dashed') "
            "and contains(normalize-space(text()),'+')]",
        ]:
            try:
                btns = panel.find_elements(By.XPATH, xp)
                for btn in btns:
                    if not btn.is_displayed(): continue
                    t = el_text(btn)
                    if "+" in t and "more" in t.lower() and "chapter" in t.lower():
                        ovf_btn = btn; break
            except: pass
            if ovf_btn: break

    # ── NO PAGE-WIDE FALLBACK — that caused Brushup's modal to be read for all sections
    # If the panel has no overflow button, this section shows all chapters inline.

    if ovf_btn:
        try: t = driver.execute_script("return arguments[0].textContent.trim()", ovf_btn)
        except: t = el_text(ovf_btn)
        print(f"      Found overflow in panel: '{t}'")
        return ovf_btn, t

    print(f"      No overflow button in {label} panel — all chapters visible inline")
    return None, ""


def click_chapter_overflow(driver, panel, label):
    """
    Click '+N more chapters' button — JS first, then XPath, then brute-force.
    """
    clicked = []
    ovf_btn = None

    # Method 1: JS inside panel
    if panel:
        try:
            ovf_btn = driver.execute_script("""
                var panel=arguments[0];
                if(!panel) return null;
                var all=Array.from(panel.querySelectorAll('*'));
                for(var i=0;i<all.length;i++){
                    var e=all[i];
                    var cls=(e.className||'').toString();
                    var txt=(e.textContent||'').trim();
                    if(cls.indexOf('border-dashed')>=0
                            && txt.startsWith('+')
                            && txt.indexOf('chapter')>=0){
                        var r=e.getBoundingClientRect();
                        if(r.width>50&&r.height>10) return e;
                    }
                }
                return null;
            """, panel)
        except: pass

    # Method 2: XPath
    if not ovf_btn:
        xpaths = [
            ".//*[contains(@class,'border-dashed') and contains(normalize-space(text()),'+') and contains(normalize-space(text()),'chapter')]",
            ".//button[contains(@class,'border-dashed')]",
            ".//*[contains(normalize-space(text()),'+') and contains(normalize-space(text()),'more chapters')]",
        ]
        for xp in xpaths:
            try:
                btns = panel.find_elements(By.XPATH, xp)
                for btn in btns:
                    if el_text(btn) and "+" in el_text(btn) and "more" in el_text(btn).lower():
                        ovf_btn = btn; break
            except: pass
            if ovf_btn: break

    # Method 3: Brute-force JS global
    if not ovf_btn:
        BGKEY = {"Reteach":"bg-blue-50","Brushup":"FFF7E6","On Track":"bg-green-50"}
        bkey  = BGKEY.get(label,"")
        try:
            ovf_btn = driver.execute_script("""
                var bkey=arguments[0];
                var all=Array.from(document.querySelectorAll('*'));
                for(var i=0;i<all.length;i++){
                    var e=all[i];
                    var cls=(e.className||'').toString();
                    var txt=(e.textContent||'').trim();
                    if(cls.indexOf('border-dashed')>=0 && txt.startsWith('+') && txt.indexOf('chapter')>=0){
                        var r=e.getBoundingClientRect();
                        if(r.width>50&&r.height>10){
                            if(bkey){
                                var node=e;
                                for(var s=0;s<15;s++){
                                    node=node.parentElement;
                                    if(!node) break;
                                    if((node.className||'').indexOf(bkey)>=0) return e;
                                }
                            } else { return e; }
                        }
                    }
                }
                return null;
            """, bkey)
        except: pass

    if ovf_btn:
        t = ""
        try: t = driver.execute_script("return arguments[0].textContent.trim()", ovf_btn)
        except: t = el_text(ovf_btn)
        print(f"        🔽 Clicking chapter overflow: '{t}'")
        safe_click(driver, ovf_btn)
        clicked.append(t)
        time.sleep(0.8)

    return clicked


def scroll_to_and_click_chapter_overflow(driver, label):
    """
    Last-resort: scroll through the page and find any '+N more chapters' button.
    Used when panel-scoped search fails.
    """
    try:
        btn = driver.execute_script("""
            var lbl = arguments[0];
            // Find all dashed border elements with chapter overflow text
            var all = Array.from(document.querySelectorAll('*'));
            var candidates = [];
            for (var i = 0; i < all.length; i++) {
                var e = all[i];
                var cls = (e.className || '').toString();
                var txt = (e.textContent || '').trim();
                if (cls.indexOf('border-dashed') >= 0
                        && txt.startsWith('+')
                        && txt.indexOf('chapter') >= 0) {
                    var r = e.getBoundingClientRect();
                    if (r.width > 30 && r.height > 10) {
                        candidates.push(e);
                    }
                }
            }
            if (candidates.length === 0) return null;
            // If label given, try to find the one in the matching section
            if (lbl) {
                var BGMAP = {Reteach:'bg-blue-50', Brushup:'FFF7E6', 'On Track':'bg-green-50'};
                var bkey = BGMAP[lbl] || '';
                for (var i = 0; i < candidates.length; i++) {
                    var node = candidates[i];
                    for (var s = 0; s < 15; s++) {
                        node = node.parentElement;
                        if (!node) break;
                        if (bkey && (node.className||'').indexOf(bkey) >= 0) return candidates[i];
                    }
                }
            }
            // Return first visible candidate
            return candidates[0] || null;
        """, label)
        if btn:
            txt = driver.execute_script("return arguments[0].textContent.trim()", btn)
            print(f"        🔽 Page-wide chapter overflow: '{txt}'")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", btn)
            time.sleep(0.4)
            try: btn.click()
            except: driver.execute_script("arguments[0].click()", btn)
            time.sleep(1.0)
            return [txt]
    except Exception as ex:
        print(f"        page-wide overflow error: {ex}")
    return []


def _sanitize_weightage(val):
    """
    ADDED: Sanitize avg_weightage value to ensure it does not contain
    'Chapter Avg' or percentage values that belong to chapter_avg.
    Valid weightage looks like: "10 / 80", "12/ 80", "10", "15 / 100"
    Invalid weightage: "Chapter Avg -5.1%", "-21.5%", "+10.4%"
    """
    if not val or val == "N/A":
        return val
    # If the value contains "chapter avg" text, it's contaminated
    if "chapter avg" in val.lower():
        return "N/A"
    # If the value contains "avg weightage" text, strip it
    val = re.sub(r'(?i)avg\s*weightage\s*', '', val).strip()
    # If the value is ONLY a percentage (like "-5.1%" or "+10.4%") with no "/" separator,
    # it's likely a chapter avg value that leaked into weightage
    if re.match(r'^[+-]?\d+\.?\d*%$', val.strip()):
        return "N/A"
    # Valid: should contain "/" pattern like "10 / 80" or just a plain number
    return val


def extract_chapter_metrics(driver, card_row_el):
    """
    Extract Chapter Avg % and Avg Weightage from an expanded chapter card.

    ACTUAL HTML when expanded (from live site inspection):
      <div class="px-6 pb-4 pt-2 border-t border-gray-100">
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-blue-50 p-4 rounded-2xl">
            <span class="text-slate-400 text-xs font-semibold">Chapter Avg</span>
            <span class="text-slate-800 text-2xl font-semibold">+10.4%</span>
          </div>
          <div class="bg-blue-50 p-4 rounded-2xl">
            <span class="text-slate-400 text-xs font-semibold">Avg Weightage</span>
            <span class="text-slate-800 text-2xl font-semibold">10</span>
            <span class="text-slate-500">/ 80</span>
          </div>
        </div>
      </div>

    KEY: Avg Weightage value is "10 / 80" but stored as TWO sibling spans:
         span1="10"  span2="/ 80"
    Must read parent container's innerText to get the full value.

    CRITICAL: All searches scoped to THIS card element only — never whole page.
    """
    time.sleep(1.5)
    metrics = {"chapter_avg": "N/A", "avg_weightage": "N/A"}

    # ══════════════════════════════════════════════════════════════════════════
    #  PRIMARY STRATEGY: innerText-based extraction
    #
    #  Most reliable approach — reads innerText of each metric box (rounded-2xl).
    #  innerText of the Avg Weightage box gives:
    #    "Avg Weightage\n10\n/ 80"
    #  We strip the label line, join the rest → "10 / 80"
    #
    #  This avoids all leaf-node / children.length issues.
    # ══════════════════════════════════════════════════════════════════════════
    try:
        result = driver.execute_script("""
            var cardEl = arguments[0];
            if (!cardEl) return {avg: null, wt: null, debug: 'no element'};

            // Step 1: Walk UP from cardEl to find container with both metrics
            var container = cardEl;
            for (var up = 0; up < 12; up++) {
                var par = container.parentElement;
                if (!par) break;
                container = par;
                var it = container.innerText || '';
                if (it.indexOf('Chapter Avg') >= 0 && it.indexOf('Avg Weightage') >= 0) break;
            }

            var avg = null, wt = null;
            var debugInfo = [];

            // Step 2: Find ALL rounded metric boxes inside this container
            //   Try multiple selectors to be resilient
            var boxes = [];
            var selectors = [
                '[class*="rounded-2xl"][class*="p-4"]',
                '[class*="rounded-2xl"][class*="p-"]',
                '[class*="rounded-xl"][class*="p-4"]',
                '[class*="rounded"][class*="bg-blue"]',
                '[class*="rounded"][class*="bg-green"]'
            ];
            for (var si = 0; si < selectors.length; si++) {
                try {
                    boxes = Array.from(container.querySelectorAll(selectors[si])).filter(function(b) {
                        var r = b.getBoundingClientRect();
                        return r.width > 50 && r.height > 30;
                    });
                    if (boxes.length >= 2) break;
                } catch(e) {}
            }
            debugInfo.push('boxes=' + boxes.length);

            // Step 3: For EACH box, read its innerText and classify
            for (var b = 0; b < boxes.length; b++) {
                var box = boxes[b];
                var rawText = (box.innerText || '').trim();
                var lines = rawText.split('\\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 0; });

                debugInfo.push('box' + b + '=[' + lines.join('|') + ']');

                if (lines.length === 0) continue;
                var firstLine = lines[0].toLowerCase();

                // ── Chapter Avg box ──
                if (firstLine.indexOf('chapter avg') >= 0 && avg === null) {
                    // Value is everything after the label line
                    var valueParts = lines.slice(1).filter(function(l) {
                        return /[0-9]/.test(l);
                    });
                    if (valueParts.length > 0) {
                        avg = valueParts[0].trim();
                    }
                    // Fallback: text-2xl element
                    if (!avg) {
                        var big = box.querySelector('[class*="text-2xl"]');
                        if (big) avg = (big.textContent || '').trim();
                    }
                }

                // ── Avg Weightage box ──
                if ((firstLine.indexOf('avg weightage') >= 0 || firstLine === 'weightage') && wt === null) {
                    // Value lines are everything after the label line
                    // e.g. lines = ["Avg Weightage", "10", "/ 80"]
                    //   → valueParts = ["10", "/ 80"] → joined = "10 / 80"
                    var valueParts = lines.slice(1);
                    if (valueParts.length > 0) {
                        wt = valueParts.join(' ').replace(/\\s+/g, ' ').trim();
                    }
                    // Fallback: if innerText didn't split, try reading child text nodes directly
                    if (!wt || !/[0-9]/.test(wt)) {
                        var childTexts = [];
                        // Walk direct childNodes of the box
                        for (var cn = 0; cn < box.childNodes.length; cn++) {
                            var node = box.childNodes[cn];
                            var ct = (node.textContent || '').trim();
                            var ctl = ct.toLowerCase();
                            if (!ct) continue;
                            if (ctl === 'avg weightage' || ctl === 'weightage') continue;
                            childTexts.push(ct);
                        }
                        if (childTexts.length > 0) {
                            var joined = childTexts.join(' ').replace(/\\s+/g, ' ').trim();
                            if (/[0-9]/.test(joined)) wt = joined;
                        }
                    }
                    // Fallback 2: read text-2xl for the number, then find sibling "/ N"
                    if (!wt || !/[0-9]/.test(wt)) {
                        var big = box.querySelector('[class*="text-2xl"]');
                        if (big) {
                            var num = (big.textContent || '').trim();
                            // Find sibling with "/"
                            var sib = big.nextElementSibling;
                            var slash = '';
                            while (sib) {
                                var st = (sib.textContent || '').trim();
                                if (st.indexOf('/') >= 0) { slash = st; break; }
                                sib = sib.nextElementSibling;
                            }
                            if (slash) {
                                wt = num + ' ' + slash;
                            } else {
                                wt = num;
                            }
                        }
                    }
                }
            }

            // ── Fallback if boxes weren't found: scan all elements for labels ──
            if ((avg === null || wt === null) && boxes.length < 2) {
                debugInfo.push('label-scan');
                var allEls = Array.from(container.querySelectorAll('*'));
                for (var i = 0; i < allEls.length; i++) {
                    var el = allEls[i];
                    var elText = (el.textContent || '').trim();
                    var elLower = elText.toLowerCase();

                    // Must be a LEAF label (exact text match, no children or small children count)
                    if (el.children.length > 2) continue;

                    if ((elLower === 'chapter avg' || elLower === 'chapter avg %') && avg === null) {
                        var box = el.parentElement;
                        if (box) {
                            var big = box.querySelector('[class*="text-2xl"]');
                            if (big) {
                                avg = (big.textContent || '').trim();
                            } else {
                                var bLines = (box.innerText || '').split('\\n');
                                for (var li = 0; li < bLines.length; li++) {
                                    var bl = bLines[li].trim();
                                    if (/[0-9]/.test(bl) && bl.toLowerCase().indexOf('chapter') < 0 && bl.toLowerCase().indexOf('weightage') < 0) {
                                        avg = bl; break;
                                    }
                                }
                            }
                        }
                    }

                    if ((elLower === 'avg weightage' || elLower === 'weightage') && wt === null) {
                        var box = el.parentElement;
                        if (box) {
                            // Read box innerText, strip label, join remaining
                            var bText = (box.innerText || '').trim();
                            var bLines = bText.split('\\n').map(function(l){return l.trim();}).filter(function(l){return l.length>0;});
                            var valParts = [];
                            var pastLabel = false;
                            for (var li = 0; li < bLines.length; li++) {
                                var bl = bLines[li];
                                if (!pastLabel && (bl.toLowerCase() === 'avg weightage' || bl.toLowerCase() === 'weightage')) {
                                    pastLabel = true; continue;
                                }
                                if (pastLabel) valParts.push(bl);
                            }
                            if (valParts.length > 0) {
                                wt = valParts.join(' ').replace(/\\s+/g, ' ').trim();
                            }
                            // Fallback: text-2xl + sibling
                            if (!wt || !/[0-9]/.test(wt)) {
                                var big = box.querySelector('[class*="text-2xl"]');
                                if (big) {
                                    var num = (big.textContent || '').trim();
                                    var sib = big.nextElementSibling;
                                    var slash = '';
                                    while (sib) {
                                        var st = (sib.textContent || '').trim();
                                        if (st.indexOf('/') >= 0) { slash = st; break; }
                                        sib = sib.nextElementSibling;
                                    }
                                    wt = slash ? (num + ' ' + slash) : num;
                                }
                            }
                        }
                    }

                    if (avg !== null && wt !== null) break;
                }
            }

            // ── NUCLEAR FALLBACK: if wt is still missing or partial ("/ 80" without "10") ──
            // Use the simplest possible approach: find element containing "Avg Weightage",
            // get its parent's innerText, regex out the numbers after the label.
            if (!wt || (wt && wt.indexOf('/') >= 0 && !/^[0-9]/.test(wt.trim()))) {
                debugInfo.push('nuclear-fallback');
                // Strategy A: find the LABEL element, get parent innerText
                var allSpans = Array.from(container.querySelectorAll('span,div,p'));
                for (var si = 0; si < allSpans.length; si++) {
                    var sp = allSpans[si];
                    var spText = (sp.textContent || '').trim().toLowerCase();
                    if ((spText === 'avg weightage' || spText === 'weightage') && sp.children.length === 0) {
                        // Found the label leaf. Get parent box innerText.
                        var parentBox = sp.parentElement;
                        if (!parentBox) continue;
                        var pInner = (parentBox.innerText || '').trim();
                        debugInfo.push('nuclear-parent=[' + pInner.replace(/\\n/g,'|') + ']');
                        // Strip label text, keep everything else
                        var stripped = pInner.replace(/Avg Weightage/i, '').replace(/Weightage/i, '').trim();
                        stripped = stripped.replace(/\\n/g, ' ').replace(/\\s+/g, ' ').trim();
                        if (stripped && /[0-9]/.test(stripped) && stripped.length < 30) {
                            // Verify it's a weightage pattern (N / M) not a percentage
                            if (!/^[+-]?[0-9]+\\.?[0-9]*%$/.test(stripped)) {
                                wt = stripped;
                                debugInfo.push('nuclear-wt=' + wt);
                                break;
                            }
                        }
                        // Strategy B: walk siblings of the label span
                        var labelSib = sp.nextElementSibling;
                        var sibParts = [];
                        while (labelSib) {
                            var sibT = (labelSib.textContent || '').trim();
                            if (sibT && /[0-9/]/.test(sibT)) sibParts.push(sibT);
                            labelSib = labelSib.nextElementSibling;
                        }
                        if (sibParts.length > 0) {
                            var sibJoined = sibParts.join(' ').replace(/\\s+/g, ' ').trim();
                            if (/[0-9]/.test(sibJoined) && !/^[+-]?[0-9]+\\.?[0-9]*%$/.test(sibJoined)) {
                                wt = sibJoined;
                                debugInfo.push('nuclear-sib-wt=' + wt);
                                break;
                            }
                        }
                    }
                }
            }

            // ── Final sanitization in JS — reject wt if it's a chapter avg value ──
            if (wt) {
                if (wt.toLowerCase().indexOf('chapter avg') >= 0) wt = null;
                if (wt && /^[+-]?[0-9]+\\.?[0-9]*%$/.test(wt.trim())) wt = null;
            }

            return {
                avg: avg,
                wt:  wt,
                debug: debugInfo.join(' | ')
            };
        """, card_row_el)

        if result:
            dbg = result.get("debug", "")
            if result.get("avg"):  metrics["chapter_avg"]   = result["avg"]
            if result.get("wt"):   metrics["avg_weightage"] = result["wt"]
            metrics["avg_weightage"] = _sanitize_weightage(metrics["avg_weightage"])
            print(f"      metrics: avg={metrics['chapter_avg']}  wt={metrics['avg_weightage']}  [{dbg[:120]}]")
            if metrics["chapter_avg"] != "N/A" and metrics["avg_weightage"] != "N/A":
                return metrics

    except Exception as ex:
        print(f"      JS metrics error: {ex}")

    # ── Fallback: Card innerText line parsing ─────────────────────────────────
    if metrics["chapter_avg"] == "N/A" or metrics["avg_weightage"] == "N/A":
        try:
            card_text = driver.execute_script("""
                var el = arguments[0];
                for (var i = 0; i < 12; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    var it = el.innerText || '';
                    if (it.indexOf('Chapter Avg') >= 0 || it.indexOf('Avg Weightage') >= 0) {
                        return it;
                    }
                }
                return '';
            """, card_row_el)

            if card_text:
                lines = [l.strip() for l in card_text.split("\n") if l.strip()]
                i = 0
                while i < len(lines):
                    ll = lines[i].lower()
                    if ll in ("chapter avg", "chapter avg %"):
                        for j in range(i+1, min(i+4, len(lines))):
                            v = lines[j].strip()
                            if re.search(r"[0-9]", v) and len(v) < 20:
                                if "avg" not in v.lower() and "weightage" not in v.lower():
                                    if metrics["chapter_avg"] == "N/A":
                                        metrics["chapter_avg"] = v
                                    break
                    elif "avg weightage" in ll or ll == "weightage":
                        # Collect value parts: "10" then "/ 80"
                        parts = []
                        for j in range(i+1, min(i+6, len(lines))):
                            v = lines[j].strip()
                            if not v: continue
                            if v.lower() in ("chapter avg","chapter avg %","avg weightage",
                                             "weightage","view chapter details"): break
                            if re.match(r'^[A-Z][a-z]', v) and not re.search(r'[0-9]', v): break
                            if re.match(r'^[+-]?\d+\.?\d*%$', v.strip()): break
                            if re.search(r"[0-9]", v) and len(v) < 20:
                                parts.append(v)
                            elif v.startswith("/") and re.search(r"[0-9]", v):
                                parts.append(v)
                            else:
                                break
                        if parts:
                            joined = " ".join(parts).replace("  ", " ").strip()
                            if metrics["avg_weightage"] == "N/A":
                                metrics["avg_weightage"] = joined
                    i += 1
        except Exception as e:
            print(f"      Card text metrics error: {e}")

    metrics["avg_weightage"] = _sanitize_weightage(metrics["avg_weightage"])

    # ── Python-side last resort: if weightage starts with "/" (missing number) ──
    # or is still N/A, do one more targeted JS extraction using sibling walk
    wt_val = metrics["avg_weightage"]
    if wt_val == "N/A" or (isinstance(wt_val, str) and wt_val.strip().startswith("/")):
        print(f"      ⚠ Weightage incomplete ('{wt_val}'), running targeted re-extraction...")
        try:
            wt_fix = driver.execute_script("""
                var cardEl = arguments[0];
                var node = cardEl;
                for (var i = 0; i < 15; i++) {
                    node = node.parentElement;
                    if (!node) break;
                    if ((node.innerText || '').indexOf('Avg Weightage') >= 0) break;
                }
                if (!node) return null;
                var allEls = Array.from(node.querySelectorAll('span,div,p'));
                for (var i = 0; i < allEls.length; i++) {
                    var el = allEls[i];
                    var t = (el.textContent || '').trim();
                    if (t.toLowerCase() === 'avg weightage' && el.children.length === 0) {
                        // Collect ALL nextElementSibling text
                        var parts = [];
                        var sib = el.nextElementSibling;
                        while (sib) {
                            var st = (sib.textContent || '').trim();
                            if (st) parts.push(st);
                            sib = sib.nextElementSibling;
                        }
                        if (parts.length > 0) return parts.join(' ');
                        // Try parent innerText minus label
                        var par = el.parentElement;
                        if (par) {
                            var pt = (par.innerText || '').replace('Avg Weightage', '').trim();
                            pt = pt.replace(/\\s+/g, ' ').trim();
                            if (pt && /[0-9]/.test(pt)) return pt;
                        }
                    }
                }
                return null;
            """, card_row_el)
            if wt_fix and re.search(r"[0-9]", wt_fix):
                wt_fix = wt_fix.strip()
                if not re.match(r'^[+-]?\d+\.?\d*%$', wt_fix):
                    metrics["avg_weightage"] = wt_fix
                    print(f"      ✅ Re-extracted weightage: {wt_fix}")
        except Exception as ex:
            print(f"      Re-extraction error: {ex}")

    print(f"      Final: avg={metrics['chapter_avg']}  wt={metrics['avg_weightage']}")
    return metrics
def test_login(driver, wait):
    sep("SECTION 1 – Login & Page Load")
    b = store["login_tests"]
    try:
        driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME,"body")))
        rec(b,"TC-L-001","Login page loads","PASS",driver.current_url)
    except Exception as e:
        rec(b,"TC-L-001","Login page loads","FAIL",str(e)); return False
    try:
        logo = driver.find_element(By.TAG_NAME,"img")
        assert logo.is_displayed()
        rec(b,"TC-L-002","Logo visible","PASS")
    except Exception as e:
        rec(b,"TC-L-002","Logo visible","WARN",str(e))
    try:
        usr=wait.until(EC.visibility_of_element_located((By.XPATH,"//input[@type='text' or @type='email']")))
        pwd=driver.find_element(By.XPATH,"//input[@type='password']")
        btn=driver.find_element(By.XPATH,"//button[@type='submit']")
        rec(b,"TC-L-003","Username/Password/Submit visible","PASS")
    except Exception as e:
        rec(b,"TC-L-003","Fields visible","FAIL",str(e)); return False
    try:
        assert pwd.get_attribute("type")=="password"
        rec(b,"TC-L-004","Password field masked","PASS")
    except Exception as e:
        rec(b,"TC-L-004","Password masked","WARN",str(e))
    try:
        usr.clear(); usr.send_keys(USERNAME)
        pwd.clear(); pwd.send_keys(PASSWORD)
        btn.click()
        wait.until(EC.presence_of_element_located(
            (By.XPATH,"//*[contains(.,'Class') or contains(.,'Overview')]")))
        rec(b,"TC-L-005","Login succeeds","PASS",driver.current_url)
        return True
    except Exception as e:
        rec(b,"TC-L-005","Login fails","FAIL",str(e)); return False


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def test_navigation(driver, wait):
    sep("SECTION 2 – Form Selection & Navigation")
    b = store["nav_tests"]
    plan = [(0,"Class",VALUES["Class"]),(1,"Section",VALUES["Section"]),
            (2,"Subject",VALUES["Subject"]),(3,"Exam",VALUES["Exam"]),
            (4,"CompareLeft",VALUES["CompareLeft"]),
            (5,"CompareRight",VALUES["CompareRight"])]
    for idx,key,val in plan:
        tc=f"TC-N-{idx+1:03d}"
        if not wait_opt(driver,idx,val,TIMEOUT):
            rec(b,tc,f"Dropdown '{key}'='{val}'","FAIL","Timed out"); return False
        ok=js_pick(driver,get_selects(driver)[idx],val)
        rec(b,tc,f"Dropdown '{key}'='{val}'","PASS" if ok else "FAIL")
        if not ok: return False
        time.sleep(0.4)

    try:
        old=driver.current_url
        driver.find_element(By.XPATH,"//button[normalize-space()='Enter']").click()
        wait.until(lambda d: d.current_url!=old)
        rec(b,"TC-N-007","Enter → Dashboard","PASS",driver.current_url)
    except Exception as e:
        rec(b,"TC-N-007","Enter","FAIL",str(e)); return False

    time.sleep(2.0)

    ov = None
    for xp in ["//button[normalize-space()='Overview']","//a[normalize-space()='Overview']",
               "//*[contains(@class,'cursor-pointer') and normalize-space(text())='Overview']",
               "//*[normalize-space(text())='Overview']"]:
        els = driver.find_elements(By.XPATH, xp)
        for el in els:
            if el.is_displayed():
                ov=el; break
        if ov: break

    if ov:
        safe_click(driver, ov)
        rec(b,"TC-N-008","Overview tab clicked","PASS")
    else:
        rec(b,"TC-N-008","Overview tab","WARN","Not found — may already be active")

    time.sleep(1.5)

    try:
        hdr=driver.find_element(By.XPATH,"//*[contains(text(),'Overview of Section')]")
        rec(b,"TC-N-009","Page header visible","PASS",el_text(hdr))
    except Exception as e:
        rec(b,"TC-N-009","Page header","WARN",str(e))

    for tab in ["Overview","Chapters","Questions","Students"]:
        n = 10+["Overview","Chapters","Questions","Students"].index(tab)
        try:
            el=driver.find_element(By.XPATH,
               f"//button[normalize-space()='{tab}']|//a[normalize-space()='{tab}']"
               f"|//*[normalize-space(text())='{tab}' and contains(@class,'cursor')]")
            assert el.is_displayed()
            rec(b,f"TC-N-{n:03d}",f"Tab '{tab}' visible","PASS")
        except Exception as e:
            rec(b,f"TC-N-{n:03d}",f"Tab '{tab}'","WARN",str(e))

    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — EXAM COMPARISON
# ══════════════════════════════════════════════════════════════════════════════

def test_exam_comparison(driver):
    sep("SECTION 3 – Exam Comparison Banner")
    b  = store["exam_tests"]
    pt = page_text(driver)

    try:
        h=driver.find_element(By.XPATH,"//*[contains(text(),'Exam Comparison')]")
        rec(b,"TC-EC-001","Exam Comparison heading visible","PASS",el_text(h))
    except Exception as e:
        rec(b,"TC-EC-001","Exam Comparison heading","WARN",str(e))
    try:
        s=driver.find_element(By.XPATH,"//*[contains(text(),'Change in') or contains(text(),'class average')]")
        rec(b,"TC-EC-002","Sub-label 'Change in class average'","PASS",el_text(s)[:60])
    except Exception as e:
        rec(b,"TC-EC-002","Sub-label","WARN",str(e))
    try:
        banner=driver.find_element(By.XPATH,
            "//*[contains(@class,'bg-[#D46B08]') or contains(@class,'D46B08')"
            " or contains(@class,'amber') or contains(@class,'orange')]")
        rec(b,"TC-EC-003","Orange banner rendered","PASS")
    except Exception as e:
        rec(b,"TC-EC-003","Orange banner","WARN",str(e))

    rec(b,"TC-EC-004","Midterm label visible","PASS" if "Midterm" in pt else "WARN")
    rec(b,"TC-EC-005","Preboard label visible","PASS" if "Preboard" in pt else "WARN")

    pcts = re.findall(r'\d+\.?\d*\s*%', pt)[:6]
    if len(pcts)>=2:
        store["exam"]["left_pct"]  = pcts[0]
        store["exam"]["right_pct"] = pcts[1]
        rec(b,"TC-EC-006",f"Left avg ({VALUES['CompareLeft']}) = {pcts[0]}","PASS",pcts[0])
        rec(b,"TC-EC-007",f"Right avg ({VALUES['CompareRight']}) = {pcts[1]}","PASS",pcts[1])
    else:
        rec(b,"TC-EC-006","Percentages","WARN",f"Found: {pcts}")
        rec(b,"TC-EC-007","Second percentage","WARN")

    trend = re.search(r'[-+]?\d+\.?\d*\s*points?\s*(decline|drop|improve)', pt, re.I)
    if not trend: trend = re.search(r'-\d+\.?\d*\s*points', pt, re.I)
    if trend:
        store["exam"]["trend"] = trend.group(0)
        rec(b,"TC-EC-008",f"Trend badge: '{trend.group(0)}'","PASS")
    else:
        rec(b,"TC-EC-008","Trend badge","WARN","Not found as text")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTIONS 4/5/6 — CHAPTER CARDS
# ══════════════════════════════════════════════════════════════════════════════

def test_chapter_section(driver, label):
    conf   = {"Reteach":"TC-RT","Brushup":"TC-BU","On Track":"TC-OT"}
    prefix = conf[label]
    b      = store["chapters"][label]["tests"]
    cd     = store["chapters"][label]

    sep(f"SECTION – {label}")
    print(f"\n  ▶ {label}")

    panel = find_chapter_section_panel(driver, label)
    if panel is None:
        rec(b,f"{prefix}-001",f"'{label}' panel found","WARN","Fallback to body")
        panel = driver.find_element(By.TAG_NAME,"body")
    else:
        rec(b,f"{prefix}-001",f"'{label}' section panel found","PASS")

    # Badge: "2 chapters" or "5 chapters" next to the section label
    # Use JS to find it inside the panel to avoid picking up modal text
    try:
        badge = driver.execute_script("""
            var label = arguments[0];
            // Find the label badge element (colored pill with label text)
            var all = Array.from(document.querySelectorAll('*'));
            for (var i = 0; i < all.length; i++) {
                var e = all[i];
                if (e.textContent.trim() === label && e.children.length === 0) {
                    // Walk up to find the section header row
                    var node = e;
                    for (var s = 0; s < 6; s++) {
                        node = node.parentElement;
                        if (!node) break;
                        // Look for sibling text containing "chapters"
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
            rec(b,f"{prefix}-002","Chapter count badge","PASS",badge)
        else:
            raise Exception("badge not found by JS")
    except Exception as e:
        # Fallback XPath
        try:
            badge_el = driver.find_element(By.XPATH,
                f"//*[normalize-space(text())='{label}']/following-sibling::*[contains(text(),'chapter')][1]"
                f"|//*[normalize-space(text())='{label}']/parent::*//*[contains(text(),'chapter') and contains(text(),' ')]")
            badge = el_text(badge_el)
            # Make sure it's a count badge, not instruction text
            if re.match(r'^\d+\s+chapters?$', badge.strip(), re.I):
                cd["badge"] = badge
                rec(b,f"{prefix}-002","Chapter count badge","PASS",badge)
            else:
                rec(b,f"{prefix}-002","Badge","WARN",f"Non-standard: {badge[:40]}")
        except Exception as e2:
            rec(b,f"{prefix}-002","Badge","WARN",str(e2))

    instr_map = {
        "Reteach":"Revise Thoroughly","Brushup":"Review Specific Concepts","On Track":"Significant Improvement"
    }
    try:
        instr=driver.find_element(By.XPATH,f"//*[contains(text(),'{instr_map[label]}')]")
        rec(b,f"{prefix}-003",f"Instruction '{instr_map[label]}' visible","PASS",el_text(instr)[:60])
    except Exception as e:
        rec(b,f"{prefix}-003","Instruction text","WARN",str(e))

    panel_text = el_text(panel).lower()
    if "no chapters" in panel_text:
        cd["empty"] = True
        rec(b,f"{prefix}-004","Empty state","INFO","0 chapters confirmed"); return

    # ── Find and click the overflow button, then READ the chapter modal ────────
    # The overflow opens a modal listing ALL chapters in this section
    ovf_btn, ovf_txt = _find_chapter_overflow_btn(driver, panel, label)

    if ovf_btn:
        # Click + read modal to get all chapter names
        chapters_from_modal, modal_ok = open_read_close_chapter_modal(
            driver, label, ovf_btn, ovf_txt)

        cd["overflow_clicked"] = [ovf_txt]
        cd["modal_chapters"]   = chapters_from_modal

        rec(b, f"{prefix}-OVF",
            f"Overflow '{ovf_txt}' clicked — modal read",
            "PASS" if modal_ok else "WARN",
            f"'{ovf_txt}' → {len(chapters_from_modal)} chapters from modal")

        for i, ch in enumerate(chapters_from_modal, 1):
            rec(b, f"{prefix}-MCH{i:02d}",
                f"Modal chapter #{i}: {ch}", "PASS")

        time.sleep(0.5)
        panel = find_chapter_section_panel(driver, label) or panel
    else:
        rec(b, f"{prefix}-OVF", "No chapter overflow found", "INFO",
            "All chapters already visible inline")

    cards = find_chapter_cards(panel)
    rec(b,f"{prefix}-004",f"Chapter cards found",
        "PASS" if cards else "WARN", f"{len(cards)} cards: {[c['name'] for c in cards]}")
    print(f"\n    📚 {label} — {len(cards)} chapters:")
    for idx, card in enumerate(cards, 1):
        print(f"      #{idx}: {card['name']}")

    for idx, card in enumerate(cards, 1):
        tc = f"{prefix}-C{idx:02d}"
        print(f"\n    ── Expanding: '{card['name']}'")
        card_data = {"idx":idx,"name":card["name"],"chapter_avg":"N/A","avg_weightage":"N/A"}
        try:
            scroll_to(driver, card["el"])
            # Click to expand
            try: card["el"].click()
            except: driver.execute_script("arguments[0].click()", card["el"])
            time.sleep(2.0)   # wait for expansion animation to fully complete
            # Scroll the card into view center so its metrics are in the viewport
            driver.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", card["el"])
            time.sleep(0.5)
            rec(b,tc,f"Card '{card['name']}' expanded","PASS")
        except Exception as e:
            rec(b,tc,f"Card '{card['name']}' click","WARN",str(e))
            cd["cards"].append(card_data); continue

        # Read metrics STRICTLY from this card — not from any other card
        m = extract_chapter_metrics(driver, card["el"])
        card_data.update(m)
        rec(b,f"{tc}-AVG",f"  Chapter Avg % = '{m['chapter_avg']}'",
            "PASS" if m["chapter_avg"] not in ("N/A","") else "WARN",
            m["chapter_avg"])
        rec(b,f"{tc}-WT",f"  Avg Weightage = '{m['avg_weightage']}'",
            "PASS" if m["avg_weightage"] not in ("N/A","") else "WARN",
            m["avg_weightage"])
        try:
            driver.find_element(By.XPATH,"//*[contains(text(),'View Chapter')]")
            rec(b,f"{tc}-BTN","'View Chapter Details' button present","PASS")
        except:
            rec(b,f"{tc}-BTN","'View Chapter Details' button","WARN","Not found")

        cd["cards"].append(card_data)
        # Collapse card before moving to next
        try:
            card["el"].click()
            time.sleep(0.5)
        except: pass

    print(f"\n  {'─'*62}")
    print(f"  📊  {label.upper()} — {len(cd['cards'])} CHAPTERS")
    print(f"  {'─'*62}")
    for c in cd["cards"]:
        print(f"    #{c['idx']:<3} {c['name']:<36} Avg:{c['chapter_avg']:>9}  Wt:{c['avg_weightage']:>12}")
    print(f"  {'─'*62}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 — HIGHLIGHTED STUDENTS
# ══════════════════════════════════════════════════════════════════════════════

def test_student_category(driver, category):
    prefix = {"Weak":"TC-HS-W","Lagging":"TC-HS-L","Performing Well":"TC-HS-P"}[category]
    sd     = store["students"][category]
    b      = sd["tests"]

    sep(f"  {category}")
    print(f"\n  ▶ {category}")

    # Heading
    try:
        hd=driver.find_element(By.XPATH,
           f"//*[contains(@class,'text-slate-600') and normalize-space(text())='{category}']"
           f"|//*[normalize-space(text())='{category}' and contains(@class,'semibold')]"
           f"|//*[normalize-space(text())='{category}']")
        rec(b,f"{prefix}-001",f"'{category}' heading visible","PASS",el_text(hd))
    except Exception as e:
        rec(b,f"{prefix}-001","Heading","WARN",str(e))

    # Badge
    badge_found = False
    for xp in [
        f"//*[normalize-space(text())='{category}']/following-sibling::*[contains(text(),'student')][1]",
        f"//*[normalize-space(text())='{category}']/following::*[contains(text(),'student')][1]",
        f"//*[normalize-space(text())='{category}']/parent::*//*[contains(text(),'student')]",
    ]:
        try:
            el=driver.find_element(By.XPATH, xp)
            badge=el_text(el)
            if badge and "student" in badge.lower():
                sd["badge"]=badge
                m=re.search(r'(\d+)',badge)
                if m: sd["total"]=int(m.group(1))
                rec(b,f"{prefix}-002","Student count badge","PASS",
                    f"'{badge}' → {sd['total']} declared")
                badge_found=True; break
        except: pass
    if not badge_found:
        rec(b,f"{prefix}-002","Student count badge","WARN","Not found")

    # Find panel
    panel = find_student_panel(driver, category)
    if panel is None:
        rec(b,f"{prefix}-PANEL","Section panel","WARN","Fallback to body")
        panel = driver.find_element(By.TAG_NAME,"body")
    else:
        rec(b,f"{prefix}-PANEL","Section panel found","PASS")

    # Scrape visible students — try JS first, then Selenium
    print(f"\n    📋 Scraping visible students…")
    visible = scrape_student_rows_js(driver, category)
    if not visible:
        visible = scrape_student_rows(panel)
    sd["visible"] = visible

    if visible:
        print(f"    ✅  {len(visible)} visible students:")
        for i,s in enumerate(visible,1):
            ci=f"  ({s.get('class_info','')})" if s.get("class_info") else ""
            print(f"      #{i}: {s['name']} — {s['pct']}{ci}")
            rec(b,f"{prefix}-S{i:02d}",f"Visible #{i}: {s['name']}","PASS",
                f"Score: {s['pct']}" + (f"  Class: {s['class_info']}" if s.get("class_info") else ""))
    else:
        rec(b,f"{prefix}-VISIBLE","Visible student rows","WARN","0 found")

    # Find overflow button
    print(f"\n    🔍 Looking for '+N more students' button…")
    ovf_el, ovf_txt = find_student_overflow(driver, category, panel)

    if ovf_el is None:
        rec(b,f"{prefix}-OVF-001","Overflow button",
            "INFO" if visible else "WARN","Not found — all students visible")
        sd["all"] = visible
        _print_student_summary(category, sd["all"]); return

    sd["overflow_txt"] = ovf_txt
    rec(b,f"{prefix}-OVF-001","Overflow button found","PASS",f"'{ovf_txt}'")
    print(f"    ✅  Found: '{ovf_txt}'")

    # Click overflow
    print(f"\n    🔽  Clicking: '{ovf_txt}'")
    clicked = False
    for attempt in range(3):
        try:
            scroll_to(driver, ovf_el)
            if attempt == 0: ovf_el.click()
            else: driver.execute_script("arguments[0].click();", ovf_el)
            time.sleep(1.5)
            clicked = True
            rec(b,f"{prefix}-OVF-002",f"Clicked '{ovf_txt}'","PASS",f"attempt {attempt+1}")
            break
        except Exception as e:
            if attempt == 2:
                rec(b,f"{prefix}-OVF-002","Click failed","FAIL",str(e))

    if not clicked:
        sd["all"]=visible; _print_student_summary(category,sd["all"]); return

    # Detect and scrape modal
    print(f"\n    🔍  Detecting modal popup…")
    modal_students, modal_found = find_and_scrape_modal(driver, category)
    sd["modal_opened"] = modal_found

    if modal_found:
        rec(b,f"{prefix}-MODAL-001","Modal opened and read",
            "PASS" if modal_students else "WARN",
            f"{len(modal_students)} students from modal")
        sd["modal"] = modal_students

        for j,s in enumerate(modal_students,1):
            rec(b,f"{prefix}-M{j:02d}",f"Modal #{j}: {s['name']}","PASS",
                f"Score: {s['pct']}" + (f"  Class: {s['class_info']}" if s.get("class_info") else ""))

        if sd["total"]>0:
            got=len(modal_students)
            rec(b,f"{prefix}-MODAL-CNT",f"Count: declared {sd['total']}, captured {got}",
                "PASS" if got>=sd["total"] else "WARN",f"{got}/{sd['total']}")

        # Modal already has ALL students (modal includes visible ones too)
        if modal_students:
            sd["all"] = modal_students
        else:
            # Modal opened but empty — keep visible + re-scrape page
            after   = scrape_student_rows_js(driver, category) or scrape_student_rows(panel)
            vis_set = {s["name"] for s in visible}
            new_s   = [s for s in after if s["name"] not in vis_set]
            sd["all"] = visible + new_s

        closed=close_modal(driver)
        rec(b,f"{prefix}-MODAL-CLOSE","Modal closed","PASS" if closed else "WARN")
    else:
        rec(b,f"{prefix}-MODAL-001","Modal","WARN","No modal detected after click")
        time.sleep(1.0)
        # Re-scrape page — maybe inline rows appeared after click
        after   = scrape_student_rows_js(driver, category) or scrape_student_rows(panel)
        vis_set = {s["name"] for s in visible}
        new_s   = [s for s in after if s["name"] not in vis_set]
        sd["all"] = visible + new_s

    # Final safety net — JS DOM scrape if we're short
    declared = sd.get("total", 0)
    captured = len(sd.get("all", []))
    if declared > 0 and captured < declared:
        print(f"\n    ⚠️  Only {captured}/{declared} captured — JS DOM safety net…")
        BORDER_MAP = {
            "Weak":"border-red-400","Lagging":"border-orange-400","Performing Well":"border-green-400"
        }
        bclass = BORDER_MAP.get(category,"")
        try:
            js_students = driver.execute_script("""
                var bclass=arguments[0];
                var panels=Array.from(document.querySelectorAll('*')).filter(function(e){
                    return bclass&&(e.className||'').indexOf(bclass)>=0
                        &&e.getBoundingClientRect().width>200;
                });
                var panel=panels.length>0?panels[0]:document.body;
                var rows=Array.from(panel.querySelectorAll('*')).filter(function(e){
                    var cls=(e.className||'').toString();
                    return cls.indexOf('px-8')>=0&&cls.indexOf('justify-between')>=0
                        &&cls.indexOf('cursor-pointer')>=0;
                });
                var students=[];var seen={};
                rows.forEach(function(row){
                    var bolds=Array.from(row.querySelectorAll('*')).filter(function(e){
                        var cls=(e.className||'').toString();
                        return cls.indexOf('font-bold')>=0&&cls.indexOf('slate-500')>=0
                            &&e.children.length===0;
                    });
                    if(bolds.length>=2){
                        var name=bolds[0].textContent.trim();
                        var pct=bolds[bolds.length-1].textContent.trim();
                        if(name&&/^[A-Z]/.test(name)&&/[0-9]/.test(pct)&&!seen[name]){
                            seen[name]=true;
                            students.push({name:name,pct:pct});
                        }
                    }
                });
                return students;
            """, bclass)
            if js_students and len(js_students) > captured:
                seen_names = {s["name"] for s in sd.get("all",[])}
                for item in js_students:
                    if item["name"] not in seen_names:
                        seen_names.add(item["name"])
                        sd["all"].append({"name":item["name"],"pct":item["pct"],"class_info":"","src":"js-dom-scrape"})
                print(f"    JS safety net added students → total: {len(sd['all'])}")
        except Exception as ex:
            print(f"    JS safety net error: {ex}")

    _print_student_summary(category, sd["all"])


def _print_student_summary(category, students):
    print(f"\n  {'─'*68}")
    print(f"  📊  {category.upper()} — {len(students)} STUDENTS TOTAL")
    print(f"  {'─'*68}")
    if not students:
        print("  ⚠️  No students captured")
    else:
        print(f"  {'#':<4} {'Name':<40} {'Score':>8}  {'Class':<12}  Src")
        print(f"  {'-'*4} {'-'*40} {'-'*8}  {'-'*12}  ---")
        for i,s in enumerate(students,1):
            print(f"  {i:<4} {s['name']:<40} {s.get('pct',''):>8}  "
                  f"{s.get('class_info',''):<12}  {s.get('src','')}")
    print(f"  {'─'*68}")


def test_all_students(driver, wait):
    sep("SECTION 7 – Highlighted Students (Full Verification)")
    b = store["students"]["Weak"]["tests"]
    try:
        hd=driver.find_element(By.XPATH,"//*[contains(text(),'Highlighted Students')]")
        rec(b,"TC-HS-000","Highlighted Students heading","PASS",el_text(hd))
    except Exception as e:
        rec(b,"TC-HS-000","Heading","WARN",str(e))
    try:
        sub=driver.find_element(By.XPATH,
            "//*[contains(text(),'preboard') or contains(text(),'classified')]")
        rec(b,"TC-HS-SUB","Sub-text visible","PASS",el_text(sub)[:80])
    except Exception as e:
        rec(b,"TC-HS-SUB","Sub-text","WARN",str(e))

    for cat in ["Weak","Lagging","Performing Well"]:
        test_student_category(driver, cat)
        time.sleep(0.5)


# ══════════════════════════════════════════════════════════════════════════════
#  PROFESSIONAL HTML REPORT CSS
# ══════════════════════════════════════════════════════════════════════════════

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{
  --bg:#070e1a;--s0:#0b1524;--s1:#0f1d30;--s2:#13253c;--s3:#1a3050;--s4:#213d63;
  --bd:#1e3a5f;--bd2:#264d7a;
  --ac:#3b82f6;--a2:#60a5fa;--a3:#93c5fd;
  --pass:#10b981;--pbg:rgba(16,185,129,.12);--pbd:rgba(16,185,129,.28);
  --fail:#f43f5e;--fbg:rgba(244,63,94,.12);--fbd:rgba(244,63,94,.28);
  --warn:#f59e0b;--wbg:rgba(245,158,11,.12);--wbd:rgba(245,158,11,.28);
  --info:#38bdf8;--ibg:rgba(56,189,248,.1);--ibd:rgba(56,189,248,.28);
  --txt:#ddeeff;--txt2:#a8c8e8;--mut:#6a92b4;--dim:#3a5a7a;
  --weak:#f43f5e;--lag:#f59e0b;--perf:#10b981;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);font-family:'Inter',system-ui,sans-serif;font-size:14px;line-height:1.6;min-height:100vh}

/* TOPBAR */
.topbar{background:linear-gradient(135deg,#04090f 0%,#0a1624 100%);border-bottom:2px solid var(--ac);
  padding:0 40px;display:flex;align-items:center;justify-content:space-between;
  height:68px;position:sticky;top:0;z-index:1000;box-shadow:0 4px 40px rgba(0,0,0,.8)}
.tb-brand{display:flex;align-items:center;gap:16px}
.tb-logo{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,var(--ac),#1d4ed8);
  display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;color:#fff;
  box-shadow:0 0 24px rgba(59,130,246,.5)}
.tb-title{font-size:17px;font-weight:800;color:#fff;letter-spacing:-.3px}
.tb-sub{font-size:11px;color:var(--mut);margin-top:1px}
.tb-meta{font-size:11px;color:var(--dim);text-align:right;line-height:1.9}
.tb-meta span{color:var(--a2);font-weight:700}

/* LAYOUT */
.wrap{max-width:1440px;margin:0 auto;padding:36px 28px}

/* HERO */
.hero{background:linear-gradient(135deg,#0d1f34 0%,#112741 50%,#0d1f34 100%);
  border:1px solid var(--bd);border-radius:20px;padding:48px 52px;margin-bottom:28px;
  position:relative;overflow:hidden;box-shadow:0 8px 48px rgba(0,0,0,.6)}
.hero::before{content:'';position:absolute;top:-80px;right:-80px;width:300px;height:300px;
  border-radius:50%;background:radial-gradient(circle,rgba(59,130,246,.1),transparent 70%)}
.hero::after{content:'';position:absolute;bottom:-60px;left:-40px;width:220px;height:220px;
  border-radius:50%;background:radial-gradient(circle,rgba(16,185,129,.07),transparent 70%)}
.hero-grid{display:grid;grid-template-columns:1fr auto;gap:44px;align-items:center;position:relative;z-index:1}
.hero-eyebrow{font-size:11px;font-weight:700;color:var(--ac);text-transform:uppercase;letter-spacing:2px;margin-bottom:8px}
.hero-title{font-size:32px;font-weight:900;color:#fff;margin-bottom:10px;letter-spacing:-.5px;line-height:1.2}
.hero-title em{font-style:normal;background:linear-gradient(90deg,var(--a2) 0%,var(--pass) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-desc{color:var(--mut);font-size:13.5px;margin-bottom:24px;line-height:1.75;max-width:680px}
.tags{display:flex;flex-wrap:wrap;gap:8px}
.tag{background:var(--s3);border:1px solid var(--bd2);border-radius:20px;padding:5px 16px;font-size:12px;color:var(--mut)}
.tag strong{color:var(--a3)}
.big-r{font-size:80px;font-weight:900;line-height:1;letter-spacing:-4px;text-align:center;
  background:linear-gradient(135deg,var(--pass) 0%,#34d399 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 24px rgba(16,185,129,.35))}
.big-r-label{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:1.2px;margin-top:8px;text-align:center}
.big-r-sub{font-size:13px;color:var(--dim);margin-top:8px;font-family:'JetBrains Mono',monospace;text-align:center}

/* SCORECARD */
.scorecard{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:32px}
.sc{background:var(--s1);border:1px solid var(--bd);border-radius:16px;padding:24px 16px;
  text-align:center;transition:all .25s ease;position:relative;overflow:hidden}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.sc.total::before{background:linear-gradient(90deg,var(--a2),var(--ac))}
.sc.pass::before{background:linear-gradient(90deg,var(--pass),#34d399)}
.sc.fail::before{background:linear-gradient(90deg,var(--fail),#fb7185)}
.sc.warn::before{background:linear-gradient(90deg,var(--warn),#fbbf24)}
.sc.rate::before{background:linear-gradient(90deg,#a855f7,#c084fc)}
.sc:hover{transform:translateY(-4px);box-shadow:0 8px 32px rgba(0,0,0,.5);border-color:var(--bd2)}
.sc-icon{font-size:24px;margin-bottom:10px;opacity:.75}
.sc-n{font-size:40px;font-weight:900;line-height:1;margin-bottom:6px;letter-spacing:-1px}
.sc.total .sc-n{color:var(--a2)}.sc.pass .sc-n{color:var(--pass)}.sc.fail .sc-n{color:var(--fail)}
.sc.warn .sc-n{color:var(--warn)}.sc.rate .sc-n{color:#c084fc}
.sc-l{font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.8px;font-weight:700}

/* SECTION */
.section{margin-bottom:24px;border-radius:16px;overflow:hidden;
  box-shadow:0 4px 24px rgba(0,0,0,.4);animation:fadeup .4s ease both;border:1px solid var(--bd)}
.section:nth-child(1){animation-delay:.02s}.section:nth-child(2){animation-delay:.06s}
.section:nth-child(3){animation-delay:.1s}.section:nth-child(4){animation-delay:.14s}
.section:nth-child(5){animation-delay:.18s}.section:nth-child(6){animation-delay:.22s}
.sec-hdr{display:flex;align-items:center;justify-content:space-between;
  background:linear-gradient(135deg,var(--s2),var(--s3));padding:18px 24px;
  cursor:pointer;user-select:none;transition:all .2s;border-bottom:1px solid var(--bd)}
.sec-hdr:hover{background:linear-gradient(135deg,var(--s3),var(--s4));border-color:var(--bd2)}
.sec-hl{display:flex;align-items:center;gap:14px}
.sec-ico{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 2px 8px rgba(0,0,0,.4)}
.sec-ttl{font-size:14.5px;font-weight:700;color:#fff;letter-spacing:-.2px}
.sec-sub{font-size:11px;color:var(--dim);margin-top:2px}
.sec-stats{display:flex;gap:10px;align-items:center}
.badge{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.3px}
.badge-pass{background:var(--pbg);color:var(--pass);border:1px solid var(--pbd)}
.badge-blue{background:var(--ibg);color:var(--a2);border:1px solid var(--ibd)}
.chev{color:var(--dim);font-size:20px;transition:transform .3s;margin-left:4px}
.chev.open{transform:rotate(180deg)}
.sec-body{background:var(--s1);border-top:none}
.sec-body.hidden{display:none}

/* TABLE */
table{width:100%;border-collapse:collapse}
thead th{background:var(--s2);color:var(--mut);font-size:10.5px;font-weight:700;
  text-transform:uppercase;letter-spacing:1px;padding:13px 18px;text-align:left;
  border-bottom:2px solid var(--bd2)}
tbody tr{border-bottom:1px solid rgba(30,58,95,.4);transition:background .15s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(59,130,246,.05)}
tbody td{padding:12px 18px;font-size:13px;vertical-align:middle}
.tid{font-family:'JetBrains Mono',monospace;color:var(--a2);font-size:11.5px;white-space:nowrap;font-weight:600}
.det{color:var(--mut);font-size:11.5px;font-family:'JetBrains Mono',monospace}
.ts{color:var(--dim);font-size:11px;white-space:nowrap;font-family:'JetBrains Mono',monospace}

/* STATUS BADGES */
.sb{display:inline-flex;align-items:center;gap:4px;padding:4px 11px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap}
.pbg{background:var(--pbg)}.cpass{color:var(--pass);border:1px solid var(--pbd)}
.fbg{background:var(--fbg)}.cfail{color:var(--fail);border:1px solid var(--fbd)}
.wbg{background:var(--wbg)}.cwarn{color:var(--warn);border:1px solid var(--wbd)}
.ibg{background:var(--ibg)}.cinfo{color:var(--info);border:1px solid var(--ibd)}

/* SUB-HEADER */
.sub-hdr{padding:14px 20px 8px;font-size:10.5px;font-weight:800;color:var(--mut);
  text-transform:uppercase;letter-spacing:1.2px;border-top:1px solid var(--bd)}
.sub-hdr:first-child{border-top:none}

/* EXAM BANNER */
.exam-banner{background:linear-gradient(135deg,#6b2208 0%,#854b09 50%,#6b2208 100%);
  border-radius:16px;padding:32px 40px;display:flex;align-items:center;gap:36px;
  margin:20px;position:relative;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.6)}
.exam-banner::before{content:'';position:absolute;right:-30px;top:-30px;width:160px;height:160px;
  border:3px solid rgba(255,255,255,.07);border-radius:50%}
.exam-lbl{font-size:10px;color:rgba(255,255,255,.55);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:5px;font-weight:600}
.exam-pct{font-size:52px;font-weight:900;color:#fff;line-height:1;letter-spacing:-2px}
.exam-arr{font-size:28px;color:rgba(255,255,255,.5);padding:0 8px}
.exam-div{width:1px;height:70px;background:rgba(255,255,255,.12)}
.exam-dec{background:rgba(0,0,0,.3);border-radius:20px;padding:6px 18px;font-size:13px;
  color:#fed7aa;font-weight:700;margin-top:12px;display:inline-flex;align-items:center;
  gap:6px;border:1px solid rgba(255,200,100,.2)}

/* CHAPTER TABLE */
.ch-wrap{margin:16px 20px;border-radius:12px;overflow:hidden;border:1px solid var(--bd);background:var(--s0)}
.ch-hdr{padding:14px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--bd)}
.ch-lbl{height:30px;padding:0 14px;border-radius:8px;font-size:11px;font-weight:800;
  display:flex;align-items:center;text-transform:uppercase;letter-spacing:.5px}
.rt-lbl{background:linear-gradient(135deg,#1d4ed8,#2563eb);color:#fff}
.bu-lbl{background:linear-gradient(135deg,#b45309,#d97706);color:#fff}
.ot-lbl{background:linear-gradient(135deg,#166534,#16a34a);color:#fff}
.ch-badge{padding:3px 12px;border-radius:20px;font-size:11px;font-weight:600;background:var(--s3);color:var(--mut);border:1px solid var(--bd2)}
.ch-table{width:100%;border-collapse:collapse}
.ch-table th{background:var(--s2);color:var(--dim);font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:.8px;padding:11px 18px;text-align:left;border-bottom:1px solid var(--bd)}
.ch-table td{padding:12px 18px;font-size:13px;border-bottom:1px solid rgba(30,58,95,.3);vertical-align:middle}
.ch-table tbody tr:last-child td{border-bottom:none}
.ch-table tbody tr:hover{background:rgba(59,130,246,.04)}
.ch-num{font-size:11px;font-weight:700;color:var(--dim);font-family:'JetBrains Mono',monospace;width:30px}
.ch-name{font-weight:600;color:var(--txt2)}
.ch-avg-pos{color:var(--pass);font-weight:700;font-family:'JetBrains Mono',monospace}
.ch-avg-neg{color:var(--fail);font-weight:700;font-family:'JetBrains Mono',monospace}
.ch-avg-na{color:var(--dim);font-style:italic;font-size:12px}
.ch-wt{color:var(--a2);font-weight:600;font-family:'JetBrains Mono',monospace}
.src-modal{background:rgba(59,130,246,.15);color:var(--a2);border:1px solid rgba(59,130,246,.3);border-radius:20px;padding:2px 9px;font-size:10px;font-weight:700}
.src-inline{background:rgba(16,185,129,.12);color:var(--pass);border:1px solid rgba(16,185,129,.3);border-radius:20px;padding:2px 9px;font-size:10px;font-weight:700}

/* STUDENT GRID */
.cat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:20px}
.ccat{border-radius:16px;overflow:hidden;transition:box-shadow .25s;box-shadow:0 4px 24px rgba(0,0,0,.4)}
.ccat:hover{box-shadow:0 8px 40px rgba(0,0,0,.6)}
.weak-col{background:linear-gradient(180deg,rgba(244,63,94,.13),rgba(244,63,94,.06) 100%);border:1px solid rgba(244,63,94,.28)}
.lag-col{background:linear-gradient(180deg,rgba(245,158,11,.13),rgba(245,158,11,.06) 100%);border:1px solid rgba(245,158,11,.28)}
.perf-col{background:linear-gradient(180deg,rgba(16,185,129,.13),rgba(16,185,129,.06) 100%);border:1px solid rgba(16,185,129,.28)}
.chdr{padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.06);display:flex;align-items:flex-start;gap:12px}
.weak-hdr{background:rgba(244,63,94,.22)}.lag-hdr{background:rgba(245,158,11,.22)}.perf-hdr{background:rgba(16,185,129,.22)}
.cico{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:#fff;flex-shrink:0;box-shadow:0 2px 12px rgba(0,0,0,.5)}
.weak-ico{background:linear-gradient(135deg,#f43f5e,#be123c)}.lag-ico{background:linear-gradient(135deg,#f59e0b,#b45309)}.perf-ico{background:linear-gradient(135deg,#10b981,#065f46)}
.cmeta{flex:1;min-width:0}
.ctit{font-size:17px;font-weight:800;color:#fff;letter-spacing:-.2px}
.cbadge{font-size:11px;color:rgba(255,255,255,.55);margin-top:2px}
.cpills{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.pill{padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700}
.pp{background:rgba(16,185,129,.2);color:var(--pass);border:1px solid rgba(16,185,129,.3)}
.pi{background:rgba(56,189,248,.12);color:var(--info);border:1px solid rgba(56,189,248,.25)}

/* STUDENT TABLE */
.stu-table-wrap{max-height:500px;overflow-y:auto}
.stu-table-wrap::-webkit-scrollbar{width:4px}
.stu-table-wrap::-webkit-scrollbar-track{background:transparent}
.stu-table-wrap::-webkit-scrollbar-thumb{background:var(--bd2);border-radius:4px}
.stu-tbl{width:100%;border-collapse:collapse}
.stu-tbl th{background:var(--s2);color:var(--dim);font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:.8px;padding:10px 14px;text-align:left;
  position:sticky;top:0;z-index:5;border-bottom:1px solid var(--bd2)}
.stu-tbl td{padding:10px 14px;font-size:12.5px;border-bottom:1px solid rgba(30,58,95,.3);vertical-align:middle}
.stu-tbl tbody tr:last-child td{border-bottom:none}
.stu-tbl tbody tr:hover{background:rgba(255,255,255,.03)}
.s-rank{font-size:10px;font-weight:700;color:var(--dim);font-family:'JetBrains Mono',monospace;width:26px;text-align:center}
.s-name{font-weight:600;color:var(--txt2)}
.s-ci{font-size:10px;color:var(--dim);display:block;margin-top:1px}
.s-bar-bg{background:var(--s3);border-radius:3px;height:4px;overflow:hidden;width:70px}
.s-bar{height:100%;border-radius:3px}
.s-pct{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:12.5px;white-space:nowrap;width:55px;text-align:right}
.tag-vis{background:rgba(16,185,129,.15);color:var(--pass);border:1px solid rgba(16,185,129,.25);border-radius:20px;padding:2px 8px;font-size:9px;font-weight:700}
.tag-modal{background:rgba(59,130,246,.15);color:var(--a2);border:1px solid rgba(59,130,246,.25);border-radius:20px;padding:2px 8px;font-size:9px;font-weight:700}
.s-empty{padding:36px;text-align:center;color:var(--dim);font-size:13px;font-style:italic}
.ccat-footer{padding:10px 14px;font-size:11px;color:var(--dim);text-align:center;
  border-top:1px solid rgba(255,255,255,.05);background:rgba(0,0,0,.18)}

/* FOOTER */
.footer{border-top:1px solid var(--bd);margin-top:48px;padding:28px;text-align:center;color:var(--dim);font-size:12px}
.footer-brand{font-size:18px;font-weight:900;color:var(--ac);margin-bottom:8px}

/* MISC */
.nil{padding:16px 20px;color:var(--dim);font-size:12px;text-align:center;font-style:italic}
.ovf-tag{background:rgba(16,185,129,.15);color:var(--pass);border:1px solid rgba(16,185,129,.3);
  border-radius:10px;padding:2px 8px;font-size:10px;font-weight:700;margin-left:8px}

/* ANIMATIONS */
@keyframes fadeup{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}

/* RESPONSIVE */
@media(max-width:1100px){.cat-grid{grid-template-columns:1fr}.scorecard{grid-template-columns:repeat(3,1fr)}}
@media(max-width:768px){.hero-grid{grid-template-columns:1fr}.scorecard{grid-template-columns:repeat(2,1fr)}.exam-banner{flex-direction:column}}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  REPORT HTML BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def _sb(s):
    m={"PASS":("pbg","cpass","✔"),"FAIL":("fbg","cfail","✘"),
       "WARN":("wbg","cwarn","⚠"),"INFO":("ibg","cinfo","ℹ")}
    bg,c,ic=m.get(s,("ibg","cinfo","ℹ"))
    return f'<span class="sb {bg} {c}">{ic} {s}</span>'

def _tbl(entries):
    if not entries: return '<p class="nil">No test entries recorded.</p>'
    rows="".join(
        f'<tr>'
        f'<td><span class="tid">{e["tc_id"]}</span></td>'
        f'<td style="color:var(--txt2);font-weight:500">{e["desc"]}</td>'
        f'<td style="text-align:center">{_sb(e["status"])}</td>'
        f'<td><span class="det">{e.get("detail","")}</span></td>'
        f'<td><span class="ts">{e.get("ts","")}</span></td>'
        f'</tr>'
        for e in entries)
    return (
        '<table><thead><tr>'
        '<th style="width:130px">Test ID</th>'
        '<th>Description</th>'
        '<th style="width:96px;text-align:center">Status</th>'
        '<th>Detail</th>'
        '<th style="width:68px">Time</th>'
        '</tr></thead><tbody>' + rows + '</tbody></table>')

def _chapter_html():
    """
    Build chapter data HTML for the report.
    Shows:
      1. Chapters from Modal (if overflow was clicked) — with PASS badge per chapter
      2. Inline Cards — expanded with Chapter Avg % and Avg Weightage
    """
    html = ""
    LABEL_CSS   = {"Reteach":"rt-lbl","Brushup":"bu-lbl","On Track":"ot-lbl"}
    LABEL_COLOR = {"Reteach":"#60a5fa","Brushup":"#fbbf24","On Track":"#34d399"}
    SECTION_BG  = {"Reteach":"rgba(96,165,250,.08)",
                   "Brushup":"rgba(251,191,36,.08)",
                   "On Track":"rgba(52,211,153,.08)"}
    SECTION_BD  = {"Reteach":"rgba(96,165,250,.3)",
                   "Brushup":"rgba(251,191,36,.3)",
                   "On Track":"rgba(52,211,153,.3)"}

    for label in ["Reteach","Brushup","On Track"]:
        cd      = store["chapters"][label]
        lcss    = LABEL_CSS[label]
        color   = LABEL_COLOR[label]
        cards   = cd["cards"]
        modal_chs = cd.get("modal_chapters", [])
        ovf     = cd.get("overflow_clicked", [])

        ovf_tag = ""
        if ovf:
            ovf_tag = f' <span class="ovf-tag">✅ {", ".join(ovf)} clicked</span>'

        bg  = SECTION_BG[label]
        bd  = SECTION_BD[label]

        # Section header
        section_header = (
            f'<div class="ch-wrap" style="border:1px solid {bd};background:{bg}">'
            f'<div class="ch-hdr" style="border-bottom:1px solid {bd}">'
            f'<span class="ch-lbl {lcss}">{label}</span>'
            f'<span class="ch-badge">{cd.get("badge","")}</span>'
            f'{ovf_tag}'
            f'</div>')

        # ── Part A: Chapters from Modal ────────────────────────────────────────
        modal_html = ""
        if modal_chs:
            modal_rows = ""
            for i, ch in enumerate(modal_chs, 1):
                modal_rows += (
                    f'<tr>'
                    f'<td><span class="ch-num">{i}</span></td>'
                    f'<td><span class="ch-name">{ch}</span></td>'
                    f'<td style="text-align:center">'
                    f'<span class="sb pbg cpass">✔ PASS</span>'
                    f'</td>'
                    f'</tr>')

            modal_html = (
                f'<div style="padding:12px 16px 4px;font-size:10px;font-weight:800;'
                f'color:{color};text-transform:uppercase;letter-spacing:1px;'
                f'display:flex;align-items:center;gap:8px">'
                f'📂 CHAPTERS FROM MODAL (+overflow clicked) — {len(modal_chs)} TOTAL'
                f'</div>'
                f'<table class="ch-table">'
                f'<thead><tr>'
                f'<th width="40">#</th>'
                f'<th>Chapter Name</th>'
                f'<th width="100" style="text-align:center">Status</th>'
                f'</tr></thead>'
                f'<tbody>{modal_rows}</tbody>'
                f'</table>')

        # ── Part B: Inline Cards (expanded with metrics) ───────────────────────
        inline_html = ""
        if cards:
            inline_rows = ""
            for c in cards:
                avg = c.get("chapter_avg","N/A")
                wt  = c.get("avg_weightage","N/A")
                if avg == "N/A":
                    avg_html = '<span class="ch-avg-na">N/A</span>'
                elif str(avg).startswith("-"):
                    avg_html = f'<span class="ch-avg-neg">{avg}</span>'
                else:
                    avg_html = f'<span class="ch-avg-pos">{avg}</span>'
                wt_html = (f'<span class="ch-wt">{wt}</span>'
                           if wt != "N/A" else '<span class="ch-avg-na">N/A</span>')

                inline_rows += (
                    f'<tr>'
                    f'<td><span class="ch-num">{c["idx"]}</span></td>'
                    f'<td><span class="ch-name">{c["name"]}</span></td>'
                    f'<td style="text-align:center">{avg_html}</td>'
                    f'<td style="text-align:center">{wt_html}</td>'
                    f'<td style="text-align:center"><span class="src-inline">inline</span></td>'
                    f'</tr>')

            inline_html = (
                f'<div style="padding:12px 16px 4px;font-size:10px;font-weight:800;'
                f'color:{color};text-transform:uppercase;letter-spacing:1px;'
                f'display:flex;align-items:center;gap:8px;'
                f'border-top:1px solid {bd}">'
                f'📊 INLINE CARDS (EXPANDED) — {len(cards)} CARDS'
                f'</div>'
                f'<table class="ch-table">'
                f'<thead><tr>'
                f'<th width="40">#</th>'
                f'<th>Chapter Name</th>'
                f'<th width="140" style="text-align:center">Chapter Avg %</th>'
                f'<th width="140" style="text-align:center">Avg Weightage</th>'
                f'<th width="80" style="text-align:center">Source</th>'
                f'</tr></thead>'
                f'<tbody>{inline_rows}</tbody>'
                f'</table>')

        # If nothing captured at all
        if not modal_chs and not cards:
            body = '<p class="nil">No chapter data captured for this section.</p>'
        else:
            body = modal_html + inline_html

        html += section_header + body + '</div>'

    return html


def _student_html():
    html = ""
    CAT_CSS   = {"Weak":"weak","Lagging":"lag","Performing Well":"perf"}
    CAT_COLOR = {"Weak":"#f43f5e","Lagging":"#f59e0b","Performing Well":"#10b981"}
    CAT_ICO   = {"Weak":"W","Lagging":"L","Performing Well":"P"}

    for cat in ["Weak","Lagging","Performing Well"]:
        sd    = store["students"][cat]
        css   = CAT_CSS[cat]
        color = CAT_COLOR[cat]
        icon  = CAT_ICO[cat]
        stus  = sd["all"]
        vc    = len(sd["visible"])
        mc    = len(sd["modal"])
        ovf   = sd["overflow_txt"]
        mopn  = sd["modal_opened"]

        pills = ""
        if ovf:  pills += f'<span class="pill pp">✅ {ovf} clicked</span>'
        if mopn: pills += f'<span class="pill pp">🪟 Modal opened · {mc} from modal</span>'
        pills += f'<span class="pill pi">👁 {vc} visible · ✅ {len(stus)} total</span>'

        if not stus:
            body = '<div class="s-empty">⚠ No students captured for this category</div>'
        else:
            stu_rows = ""
            for i, s in enumerate(stus, 1):
                pv   = float(re.sub(r'[^0-9.]','',s.get('pct','0') or '0') or 0)
                bw   = min(int(pv), 100)
                src  = s.get("src","")
                is_vis   = i <= vc
                is_modal = (i > vc and mopn) or "modal" in src

                tag = ('<span class="tag-vis">👁 visible</span>' if is_vis
                       else '<span class="tag-modal">📂 modal</span>' if is_modal
                       else "")
                ci_html = (f'<span class="s-ci">{s.get("class_info","")}</span>'
                           if s.get("class_info") else "")

                stu_rows += (
                    f'<tr>'
                    f'<td><span class="s-rank">{i}</span></td>'
                    f'<td><span class="s-name">{s["name"]}</span>{ci_html}</td>'
                    f'<td><div class="s-bar-bg"><div class="s-bar" style="width:{bw}%;background:{color}"></div></div></td>'
                    f'<td><span class="s-pct" style="color:{color}">{s.get("pct","")}</span></td>'
                    f'<td>{tag}</td>'
                    f'</tr>')

            body = (
                '<div class="stu-table-wrap">'
                '<table class="stu-tbl"><thead><tr>'
                '<th width="26">#</th><th>Student Name</th>'
                '<th width="80">Score Bar</th>'
                '<th width="65">Score</th>'
                '<th width="80">Source</th>'
                '</tr></thead><tbody>' + stu_rows + '</tbody></table></div>')

        footer = (f'<div class="ccat-footer">'
                  f'Total: <strong style="color:{color}">{len(stus)}</strong> students captured'
                  + (f' · Declared: <strong>{sd["total"]}</strong>' if sd["total"] > 0 else "")
                  + f'</div>')

        html += (
            f'<div class="ccat {css}-col">'
            f'<div class="chdr {css}-hdr">'
            f'<div class="cico {css}-ico">{icon}</div>'
            f'<div class="cmeta">'
            f'<div class="ctit">{cat}</div>'
            f'<div class="cbadge">{sd["badge"]}</div>'
            f'<div class="cpills">{pills}</div>'
            f'</div></div>'
            f'{body}'
            f'{footer}'
            f'</div>')

    return f'<div class="cat-grid">{html}</div>'


def _section_block(icon, title, subtitle, icon_bg, passed, total_tests, extra, tests):
    return (
        f"<div class='section'>"
        f"<div class='sec-hdr' onclick='tog(this)'>"
        f"<div class='sec-hl'>"
        f"<div class='sec-ico' style='background:{icon_bg}'>{icon}</div>"
        f"<div><div class='sec-ttl'>{title}</div>"
        f"<div class='sec-sub'>{subtitle}</div></div></div>"
        f"<div class='sec-stats'>"
        f"<span class='badge badge-pass'>{passed} PASSED</span>"
        f"<span class='badge badge-blue'>{total_tests} TESTS</span>"
        f"<span class='chev open'>▾</span></div></div>"
        f"<div class='sec-body'>{extra}{_tbl(tests)}</div></div>")


def build_report():
    total = _P+_F+_W
    rate  = round(_P/max(total,1)*100,1)

    all_ch_tests  = []
    for label in ["Reteach","Brushup","On Track"]:
        all_ch_tests.extend(store["chapters"][label]["tests"])
    all_stu_tests = []
    for cat in ["Weak","Lagging","Performing Well"]:
        all_stu_tests.extend(store["students"][cat]["tests"])

    lp  = sum(1 for e in store["login_tests"]  if e["status"]=="PASS")
    np  = sum(1 for e in store["nav_tests"]     if e["status"]=="PASS")
    ep  = sum(1 for e in store["exam_tests"]    if e["status"]=="PASS")
    chp = sum(1 for e in all_ch_tests           if e["status"]=="PASS")
    sp  = sum(1 for e in all_stu_tests          if e["status"]=="PASS")

    lp2 = store["exam"].get("left_pct","—")
    rp2 = store["exam"].get("right_pct","—")
    tr  = store["exam"].get("trend","—")

    exam_visual = (
        "<div class='exam-banner'>"
        "<div><div class='exam-lbl'>Class Average Comparison</div>"
        f"<div style='font-size:13px;font-weight:600;color:rgba(255,255,255,.8);margin-top:4px'>"
        f"☷ {VALUES['CompareLeft']} &rarr; {VALUES['CompareRight']}</div></div>"
        "<div class='exam-div'></div>"
        f"<div><div class='exam-lbl'>{VALUES['CompareLeft']}</div>"
        f"<div class='exam-pct'>{lp2}</div></div>"
        "<div class='exam-arr'>&rarr;</div>"
        f"<div><div class='exam-lbl'>{VALUES['CompareRight']}</div>"
        f"<div class='exam-pct' style='color:#fed7aa'>{rp2}</div>"
        f"<div class='exam-dec'>&#x2B07; {tr}</div></div>"
        "</div>")

    ch_extra = (
        "<div class='sub-hdr'>&#128203; Chapter Data — Inline Cards + Overflow Clicked</div>"
        + _chapter_html()
        + "<div class='sub-hdr' style='margin-top:4px'>&#129514; Detailed Test Results</div>")

    stu_extra = (
        "<div class='sub-hdr'>&#128203; Student Lists — Visible + Modal (All Students)</div>"
        + _student_html()
        + "<div class='sub-hdr' style='margin-top:4px'>&#129514; Detailed Test Results</div>")

    html = (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>ClassLens — Complete UI Test Report v12</title>"
        "<style>" + CSS + "</style></head><body>"

        "<div class='topbar'>"
        "<div class='tb-brand'><div class='tb-logo'>CL</div>"
        "<div><div class='tb-title'>ClassLens QA — Complete UI Test Report v12</div>"
        "<div class='tb-sub'>Login &nbsp;&middot;&nbsp; Navigation &nbsp;&middot;&nbsp; Exam &nbsp;&middot;&nbsp; Chapter Cards &nbsp;&middot;&nbsp; Highlighted Students (All Modal Data)</div>"
        "</div></div>"
        "<div class='tb-meta'>Generated: <span id='gt'></span><br>"
        f"Class {VALUES['Class']}-{VALUES['Section']} &nbsp;&nbsp;|&nbsp;&nbsp; {VALUES['Subject']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{VALUES['CompareLeft']} &rarr; {VALUES['CompareRight']}"
        "</div></div>"

        "<div class='wrap'>"

        "<div class='hero'><div class='hero-grid'><div>"
        "<div class='hero-eyebrow'>Automation QA Report</div>"
        "<div class='hero-title'>ClassLens Overview Tab <em>Complete UI Test Suite v12</em></div>"
        "<div class='hero-desc'>"
        "Every element on the Overview tab is tested and verified. "
        "Highlighted Students: all +N overflow buttons clicked &rarr; modal popup opened &rarr; "
        "<strong>ALL students captured</strong> (not just visible rows). "
        "Chapter Cards: +N overflow clicked &rarr; modal chapters listed &rarr; "
        "all inline cards expanded &rarr; Chapter Avg % and Avg Weightage extracted."
        "</div>"
        "<div class='tags'>"
        f"<span class='tag'><strong>URL</strong> classlens.inferentics.com</span>"
        f"<span class='tag'><strong>User</strong> {USERNAME}</span>"
        f"<span class='tag'><strong>Class</strong> {VALUES['Class']}-{VALUES['Section']}</span>"
        f"<span class='tag'><strong>Subject</strong> {VALUES['Subject']}</span>"
        f"<span class='tag'><strong>Comparison</strong> {VALUES['CompareLeft']} &rarr; {VALUES['CompareRight']}</span>"
        f"<span class='tag'><strong>Run</strong> {run_ts}</span>"
        "</div></div>"

        f"<div><div class='big-r'>{rate}%</div>"
        f"<div class='big-r-label'>Pass Rate</div>"
        f"<div class='big-r-sub'>{_P}&nbsp;/&nbsp;{total}&nbsp;tests</div>"
        "</div></div></div>"

        "<div class='scorecard'>"
        f"<div class='sc total'><div class='sc-icon'>&#128203;</div><div class='sc-n'>{total}</div><div class='sc-l'>Total Tests</div></div>"
        f"<div class='sc pass'><div class='sc-icon'>&#10004;</div><div class='sc-n'>{_P}</div><div class='sc-l'>Passed</div></div>"
        f"<div class='sc fail'><div class='sc-icon'>&#10008;</div><div class='sc-n'>{_F}</div><div class='sc-l'>Failed</div></div>"
        f"<div class='sc warn'><div class='sc-icon'>&#9888;</div><div class='sc-n'>{_W}</div><div class='sc-l'>Warnings</div></div>"
        f"<div class='sc rate'><div class='sc-icon'>&#128200;</div><div class='sc-n' style='color:#c084fc'>{rate}%</div><div class='sc-l'>Pass Rate</div></div>"
        "</div>"

        + _section_block("&#128274;","Section 1 &ndash; Login &amp; Page Load",
            "Authentication &middot; Fields &middot; Logo &middot; Masking",
            "rgba(59,130,246,.2)",lp,len(store["login_tests"]),"",store["login_tests"])

        + _section_block("&#129517;","Section 2 &ndash; Form Selection &amp; Navigation",
            "6 Cascading Dropdowns &middot; Enter Button &middot; Tab Bar",
            "rgba(168,85,247,.2)",np,len(store["nav_tests"]),"",store["nav_tests"])

        + _section_block("&#128202;","Section 3 &ndash; Exam Comparison Banner",
            "Orange Banner &middot; Class Averages &middot; Trend Badge",
            "rgba(245,158,11,.2)",ep,len(store["exam_tests"]),exam_visual,store["exam_tests"])

        + _section_block("&#128218;","Sections 4/5/6 &ndash; Chapter Cards (Reteach &middot; Brushup &middot; On Track)",
            "All Cards Expanded &middot; +N Overflow Clicked &middot; Chapter Avg % &middot; Avg Weightage",
            "rgba(34,197,94,.2)",chp,len(all_ch_tests),ch_extra,all_ch_tests)

        + _section_block("&#128101;","Section 7 &ndash; Highlighted Students (Full Verification)",
            "Weak &middot; Lagging &middot; Performing Well &middot; +N Overflow Clicked &rarr; Modal &rarr; ALL Students",
            "rgba(168,85,247,.2)",sp,len(all_stu_tests),stu_extra,all_stu_tests)

        + "<div class='footer'>"
        "<div class='footer-brand'>ClassLens QA</div>"
        f"<div>Generated: <span id='ft'></span> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Python &middot; Selenium 4 &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{total} Tests &middot; {rate}% Pass Rate &middot; v12</div>"
        "</div></div>"

        "<script>"
        "var f=new Date().toLocaleString('en-IN',{timeZone:'Asia/Kolkata',"
        "year:'numeric',month:'short',day:'2-digit',"
        "hour:'2-digit',minute:'2-digit',second:'2-digit'});"
        "document.getElementById('gt').textContent=f;"
        "document.getElementById('ft').textContent=f;"
        "function tog(h){"
        "  var b=h.nextElementSibling,c=h.querySelector('.chev');"
        "  var hidden=b.classList.toggle('hidden');"
        "  c.classList.toggle('open',!hidden);"
        "}"
        "</script></body></html>")
    return html


# ══════════════════════════════════════════════════════════════════════════════
#  SAVE & OPEN
# ══════════════════════════════════════════════════════════════════════════════

def open_browser(path):
    abs_p = os.path.abspath(path)
    url   = "file:///" + abs_p.replace(os.sep, "/")
    print(f"\n  🌐 {url}")
    try:
        if webbrowser.open(url, new=2): print("  ✅  Browser launched."); return
    except: pass
    try:
        if sys.platform.startswith("win"): os.startfile(abs_p)
        elif sys.platform=="darwin": subprocess.Popen(["open",abs_p])
        else:
            for cmd in ["xdg-open","sensible-browser","google-chrome","firefox"]:
                try: subprocess.Popen([cmd,abs_p]); return
                except FileNotFoundError: continue
    except Exception as e:
        print(f"  ⚠️  {e}")


def save_outputs():
    total = _P+_F+_W
    store["summary"] = {
        "total":total,"passed":_P,"failed":_F,"warnings":_W,
        "pass_rate": f"{round(_P/max(total,1)*100,1)}%"
    }
    for label in ["Reteach","Brushup","On Track"]:
        for c in store["chapters"][label]["cards"]:
            c.pop("el", None)

    with open(JSON_FILE,"w",encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
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
    print("\n╔" + "═"*72 + "╗")
    print("║   ClassLens — Complete UI Test Suite v12.0  (Professional Edition)      ║")
    print("║   Login · Navigation · Exam · Chapter Cards · ALL Students               ║")
    print(f"║   Started: {run_ts}                                       ║")
    print("╚" + "═"*72 + "╝")

    driver = make_driver()
    wait   = WebDriverWait(driver, TIMEOUT)

    try:
        if not test_login(driver, wait):
            print("❌  Login failed — stopping."); return

        if not test_navigation(driver, wait):
            print("❌  Navigation failed — stopping."); return

        test_exam_comparison(driver)
        test_chapter_section(driver, "Reteach")
        test_chapter_section(driver, "Brushup")
        test_chapter_section(driver, "On Track")
        test_all_students(driver, wait)

    except Exception as exc:
        print(f"\n💥  Unhandled exception: {exc}")
        traceback.print_exc()

    finally:
        sep("FINAL SUMMARY")
        total = _P+_F+_W
        rate  = round(_P/max(total,1)*100,1)
        print(f"  ✅  Passed   : {_P}")
        print(f"  ❌  Failed   : {_F}")
        print(f"  ⚠️   Warnings : {_W}")
        print(f"  📊  Pass Rate: {rate}%  ({_P}/{total})")

        print("\n  ━━━━  CHAPTER CARDS SUMMARY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for label in ["Reteach","Brushup","On Track"]:
            cd=store["chapters"][label]
            print(f"\n  {label.upper()} — {cd.get('badge','')}")
            for c in cd["cards"]:
                print(f"    #{c['idx']:<3} {c['name']:<36} Avg:{c.get('chapter_avg','?'):>9}  Wt:{c.get('avg_weightage','?'):>12}")

        print("\n  ━━━━  STUDENT SUMMARY  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for cat in ["Weak","Lagging","Performing Well"]:
            sd=store["students"][cat]
            stus=sd["all"]
            print(f"\n  {cat.upper()} — {sd.get('badge','')} — {len(stus)} captured")
            if not stus:
                print("    ⚠️  No students captured")
            else:
                print(f"  {'#':<4} {'Name':<40} {'Score':>8}  {'Class':<12}")
                print(f"  {'-'*4} {'-'*40} {'-'*8}  {'-'*12}")
                for i,s in enumerate(stus,1):
                    print(f"  {i:<4} {s['name']:<40} {s.get('pct',''):>8}  {s.get('class_info',''):<12}")

        save_outputs()

        if KEEP_BROWSER_OPEN:
            input("\n👉  Press ENTER to close browser…")
        driver.quit()
        print("\n🏁  Done.")


if __name__ == "__main__":
    main()