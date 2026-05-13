#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ClassLens deep UI audit: login, test every discovered section and all tabs."""
import os, re, sys, time, html, traceback
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_URL = os.environ.get("CLASSLENS_URL", "https://classlens.inferentics.com")
USERNAME = os.environ.get("CLASSLENS_USERNAME", "sajan")
PASSWORD = os.environ.get("CLASSLENS_PASSWORD", "Operations123")
OUT = Path(__file__).resolve().parent
ART = OUT / "deep_ui_audit_artifacts"
ART.mkdir(exist_ok=True)
TARGET_TABS = ["Overview", "Chapters", "Questions", "Students"]
TARGET_FILTERS = {"Class": "12", "Section": "P", "Subject": "Maths", "Exam": "Midterm"}
RESULTS = []

def log(status, section, tab, detail, evidence=""):
    row = {"time": datetime.now().strftime("%H:%M:%S"), "status": status, "section": section, "tab": tab, "detail": detail, "evidence": evidence}
    RESULTS.append(row)
    print(f"[{status}] [SECTION={section}] [TAB={tab}] {detail}" + (f" | {evidence}" if evidence else ""), flush=True)

def safe_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text or "na")).strip("_")[:80] or "na"

def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    if os.environ.get("CLASSLENS_HEADLESS", "0").lower() in ("1", "true", "yes"):
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1600,1100")
    return webdriver.Chrome(options=options)

def wait_ready(driver, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False

def click_text(driver, texts, timeout=10):
    from selenium.webdriver.common.by import By
    texts = [texts] if isinstance(texts, str) else texts
    end = time.time() + timeout
    while time.time() < end:
        for t in texts:
            xp = "//*[self::button or self::a or @role='tab' or @role='button' or contains(@class,'tab')][contains(normalize-space(.), %r)]" % t
            try:
                for el in driver.find_elements(By.XPATH, xp):
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                        time.sleep(0.15)
                        try:
                            el.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", el)
                        return True
            except Exception:
                pass
        time.sleep(0.25)
    return False

def login(driver):
    from selenium.webdriver.common.by import By
    driver.get(BASE_URL)
    wait_ready(driver)
    time.sleep(1)
    inputs = driver.find_elements(By.XPATH, "//input[not(@type='hidden')]")
    user = None
    pwd = None
    for i in inputs:
        meta = " ".join([i.get_attribute("type") or "", i.get_attribute("name") or "", i.get_attribute("id") or "", i.get_attribute("placeholder") or ""]).lower()
        if not user and any(k in meta for k in ["user", "email", "login", "name"]):
            user = i
        if not pwd and ("password" in meta or (i.get_attribute("type") or "").lower() == "password"):
            pwd = i
    if not user and inputs:
        user = inputs[0]
    if not pwd and len(inputs) > 1:
        pwd = inputs[1]
    if not user or not pwd:
        log("FAIL", "Login", "Login", "Could not find username/password fields")
        return False
    user.clear(); user.send_keys(USERNAME)
    pwd.clear(); pwd.send_keys(PASSWORD)
    if not click_text(driver, ["Login", "Sign in", "Submit", "Continue"], timeout=3):
        try:
            pwd.submit()
        except Exception:
            pass
    wait_ready(driver)
    time.sleep(3)
    body = driver.find_element(By.TAG_NAME, "body").text[:1000]
    if any(x in body.lower() for x in ["invalid", "incorrect", "failed"]):
        log("FAIL", "Login", "Login", "Login page reports invalid credentials", body[:180])
        return False
    log("PASS", "Login", "Login", "Login completed", f"url={driver.current_url}")
    return True

def select_by_label(driver, label, desired, allow_partial=True):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select
    label_l = label.lower()
    selects = driver.find_elements(By.TAG_NAME, "select")
    candidates = []
    for sel in selects:
        score = 0
        attrs = " ".join([sel.get_attribute("name") or "", sel.get_attribute("id") or "", sel.get_attribute("aria-label") or "", sel.get_attribute("placeholder") or ""]).lower()
        if label_l in attrs:
            score += 10
        try:
            near = driver.execute_script("""const e=arguments[0]; let p=e.parentElement, txt=''; for(let i=0;i<4 && p;i++,p=p.parentElement){txt += ' ' + (p.innerText || '');} return txt.slice(0,500);""", sel).lower()
            if label_l in near:
                score += 5
        except Exception:
            pass
        candidates.append((score, sel))
    candidates.sort(key=lambda x: x[0], reverse=True)
    for score, sel in candidates:
        if score <= 0 and len(selects) > 1:
            continue
        try:
            s = Select(sel)
            opts = [o.text.strip() for o in s.options if o.text.strip()]
            target = None
            for o in opts:
                if o.lower() == str(desired).lower():
                    target = o; break
            if not target and allow_partial:
                for o in opts:
                    if str(desired).lower() in o.lower():
                        target = o; break
            if target:
                s.select_by_visible_text(target)
                time.sleep(1)
                log("PASS", "Filters", label, f"Selected {label}", target)
                return sel, target, opts
        except Exception:
            continue
    log("WARN", "Filters", label, f"Could not select {label}={desired}")
    return None, None, []

def set_base_filters(driver):
    for label, val in TARGET_FILTERS.items():
        if label != "Section":
            select_by_label(driver, label, val)

def discover_sections(driver):
    sel, chosen, opts = select_by_label(driver, "Section", TARGET_FILTERS["Section"])
    clean = [o for o in opts if o and o.strip().lower() not in ["select", "section", "all", "--"]]
    seen = []
    for o in clean or ([chosen] if chosen else [TARGET_FILTERS["Section"]]):
        if o and o not in seen:
            seen.append(o)
    return seen

def count_visible_data(driver):
    from selenium.webdriver.common.by import By
    rows = [r for r in driver.find_elements(By.CSS_SELECTOR, "table tbody tr") if r.is_displayed()]
    cards = [c for c in driver.find_elements(By.CSS_SELECTOR, "[class*='card'], [class*='panel'], [class*='box']") if c.is_displayed()]
    buttons = [b for b in driver.find_elements(By.CSS_SELECTOR, "button,a,[role='button']") if b.is_displayed()]
    text = driver.find_element(By.TAG_NAME, "body").text
    return rows, cards, buttons, text

def save_snapshot(driver, section, tab):
    html_path = ART / f"{safe_name(section)}__{safe_name(tab)}.html"
    png_path = ART / f"{safe_name(section)}__{safe_name(tab)}.png"
    try:
        html_path.write_text(driver.page_source, encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        driver.save_screenshot(str(png_path))
    except Exception:
        pass
    return html_path.name, png_path.name

def audit_tab(driver, section, tab):
    ok_click = click_text(driver, tab, timeout=8)
    time.sleep(2)
    rows, cards, buttons, text = count_visible_data(driver)
    html_name, png_name = save_snapshot(driver, section, tab)
    evidence = f"rows={len(rows)}, cards={len(cards)}, buttons={len(buttons)}, chars={len(text)}, screenshot={png_name}, html={html_name}"
    lower = text.lower()
    if any(x in lower for x in ["traceback", "exception", "failed to fetch", "server error"]):
        log("FAIL", section, tab, "Application error text detected", text[:220])
    elif not ok_click:
        log("WARN", section, tab, "Tab click not confirmed; audited current view", evidence)
    elif len(text.strip()) < 40:
        log("WARN", section, tab, "Tab opened but visible content is too small", evidence)
    elif any(x in lower for x in ["no data", "no records", "not found", "empty"]):
        log("WARN", section, tab, "Empty-state text detected", evidence)
    else:
        log("PASS", section, tab, "Tab loaded with visible data", evidence)

def build_report():
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r['status'] == 'PASS')
    failed = sum(1 for r in RESULTS if r['status'] == 'FAIL')
    warned = sum(1 for r in RESULTS if r['status'] == 'WARN')
    pct = round((passed / max(total, 1)) * 100, 1)
    rows = ''.join(f"<tr><td><input type='checkbox'></td><td><span class='b {r['status'].lower()}'>{html.escape(r['status'])}</span></td><td>{html.escape(r['section'])}</td><td>{html.escape(r['tab'])}</td><td>{html.escape(r['detail'])}</td><td><code>{html.escape(r['evidence'])}</code></td><td>{html.escape(r['time'])}</td></tr>" for r in RESULTS)
    css = ":root{--bg:#071421;--card:#10233a;--line:#244766;--txt:#e7f4ff;--muted:#88a8c7;--cyan:#22d3ee;--green:#34d399;--red:#fb7185;--amber:#fbbf24}*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#06111e,#0b1c30);color:var(--txt);font-family:Inter,Segoe UI,Arial,sans-serif}.wrap{max-width:1450px;margin:0 auto;padding:22px}.hero{background:linear-gradient(135deg,#113154,#0b1d33);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:0 18px 50px #0008}.kicker{color:var(--cyan);font-weight:900;text-transform:uppercase;letter-spacing:.12em;font-size:12px}h1{font-size:34px;margin:5px 0 8px}.muted{color:var(--muted)}.score{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:18px 0}.metric{background:#0d2036;border:1px solid var(--line);border-radius:14px;padding:17px}.metric b{font-size:30px;display:block}.card{background:var(--card);border:1px solid var(--line);border-radius:16px;margin:18px 0;padding:18px}.b{display:inline-block;border-radius:999px;padding:5px 11px;font-size:12px;font-weight:900}.pass{background:#063d2f;color:#86efac}.fail{background:#4c101d;color:#fecdd3}.warn{background:#4a3008;color:#fde68a}.info{background:#12355f;color:#bfdbfe}table{width:100%;border-collapse:collapse;margin-top:12px}th,td{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}th{color:#9cc5e7;background:#0b1b2e}code{white-space:pre-wrap;color:#d7edff}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.pill{border:1px solid var(--line);border-radius:999px;padding:7px 11px;color:#bdefff;background:#082038}@media(max-width:900px){.score{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.score{grid-template-columns:1fr}.wrap{padding:12px}}"
    pills = ''.join(f"<span class='pill'>{html.escape(t)}</span>" for t in TARGET_TABS)
    doc = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ClassLens Complete Section/Tab UI Test Suite</title><style>{css}</style></head><body><main class='wrap'><section class='hero'><div class='kicker'>Automation QA Report</div><h1>ClassLens Complete Section & Tab UI Test Suite</h1><p class='muted'>Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Tests every discovered Section value and all required tabs.</p><div class='tabs'>{pills}</div><div class='score'><div class='metric'>Pass rate<b>{pct}%</b></div><div class='metric'>Total checks<b>{total}</b></div><div class='metric'>Passed<b>{passed}</b></div><div class='metric'>Warnings<b>{warned}</b></div><div class='metric'>Failed<b>{failed}</b></div></div></section><section class='card'><h2>Complete Evidence Matrix</h2><table><thead><tr><th>Check</th><th>Status</th><th>Section</th><th>Tab</th><th>Description</th><th>Evidence</th><th>Time</th></tr></thead><tbody>{rows}</tbody></table></section><p class='muted'>Screenshots and HTML snapshots are saved in deep_ui_audit_artifacts beside this report.</p></main></body></html>"
    path = OUT / "classlens_complete_section_tab_report.html"
    path.write_text(doc, encoding='utf-8')
    print(f"[PASS] [SECTION=Report] [TAB=Dashboard] Deep UI audit report written | {path.name}")
    return path

def main():
    driver = None
    try:
        driver = get_driver()
        if not login(driver):
            build_report(); return 1
        set_base_filters(driver)
        sections = discover_sections(driver)
        log("INFO", "Discovery", "Sections", "Discovered section options", ", ".join(sections))
        for sec in sections:
            select_by_label(driver, "Section", sec)
            time.sleep(1.5)
            for tab in TARGET_TABS:
                audit_tab(driver, sec, tab)
        failed = sum(1 for r in RESULTS if r['status'] == 'FAIL')
        build_report()
        return 0 if failed == 0 else 1
    except Exception as exc:
        log("FAIL", "Runner", "Exception", str(exc), traceback.format_exc()[-900:])
        build_report()
        return 1
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    raise SystemExit(main())
