<<<<<<< HEAD
import re
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ================= CONFIG =================

LOGIN_URL = "https://classlens.inferentics.com/login"
USERNAME  = "sajan"
PASSWORD  = "Operations123"

# These stay fixed — only Section and Exam are entered by you at runtime
BASE_VALUES = {
    "Class":        "12",
    "Subject":      "MATHS",
    "CompareLeft":  "Midterm",
    "CompareRight": "Preboard 1",
}

KEEP_BROWSER_OPEN = True
TEST_RESULTS     = []
CHANGES_DETECTED = []


# ================= HELPERS =================

CURRENT_EXAM    = ""
CURRENT_SECTION = ""

def check(condition, message, driver=None, category="General"):
    status = "PASS" if condition else "FAIL"
    icon   = "✅" if condition else "❌"
    tag    = f"Section {CURRENT_SECTION} | Exam: {CURRENT_EXAM}"
    print(f"  {icon} [{category}] {message}")
    TEST_RESULTS.append({
        "section":  CURRENT_SECTION,
        "exam":     CURRENT_EXAM,
        "category": category,
        "status":   status,
        "message":  message,
        "time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    if not condition and driver:
        driver.save_screenshot(f"FAIL_{CURRENT_SECTION}_{CURRENT_EXAM.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")


def flag_change(field, expected, actual):
    print(f"  ⚠️  CHANGE — {field} | expected: '{expected}' | actual: '{actual}'")
    CHANGES_DETECTED.append({
        "field":    field,
        "expected": expected,
        "actual":   actual,
    })


def find_text(driver, text):
    try:
        els = driver.find_elements(
            By.XPATH,
            f"//*[contains(translate(normalize-space(text()),"
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
            f"'{text.lower()}')]"
        )
        return any(e.is_displayed() for e in els)
    except:
        return False


def body_text(driver):
    return driver.find_element(By.TAG_NAME, "body").text


def type_safely(element, text):
    element.click()
    time.sleep(0.2)
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.DELETE)
    element.send_keys(text)


def get_selects(driver):
    return driver.find_elements(By.TAG_NAME, "select")


def js_select(driver, select_el, value):
    driver.execute_script("""
        const sel = arguments[0], text = arguments[1].trim();
        for (let opt of sel.options) {
            if (opt.text.trim() === text) {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change', {bubbles: true}));
                return;
            }
        }
    """, select_el, value)


def wait_for_option(driver, index, value, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        selects = get_selects(driver)
        if len(selects) > index:
            opts = driver.execute_script(
                "return Array.from(arguments[0].options).map(o => o.text.trim());",
                selects[index]
            )
            if value in opts:
                return
        time.sleep(0.5)
    # Print available options to help debug
    selects = get_selects(driver)
    if len(selects) > index:
        available = driver.execute_script(
            "return Array.from(arguments[0].options).map(o => o.text.trim());",
            selects[index]
        )
        print(f"  ⚠️  Dropdown {index} available options: {available}")
    raise Exception(f"Option '{value}' not found in dropdown {index}")


# ================= LOGIN =================

def login(driver, wait):
    print("\n🔐 Logging in...")
    driver.get(LOGIN_URL)
    username = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email']")
    ))
    password = wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='password']")
    ))
    type_safely(username, USERNAME)
    type_safely(password, PASSWORD)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']")
    )).click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(.,'Enter your Class')]")
    ))
    print("  ✅ Login successful")


# ================= SELECT SECTION & LOAD OVERVIEW =================

def load_overview(driver, wait, section, exam, compare_left, compare_right):
    print(f"\n📂 Loading Overview for Section {section}, Exam: {exam}...")

    wait.until(lambda d: len(get_selects(d)) >= 6)

    # Dropdowns 0-3 first (Class, Section, Subject, Exam)
    first_four = [
        (0, BASE_VALUES["Class"]),
        (1, section),
        (2, BASE_VALUES["Subject"]),
        (3, exam),
    ]

    for index, value in first_four:
        wait_for_option(driver, index, value)
        js_select(driver, get_selects(driver)[index], value)
        time.sleep(0.8)   # give compare dropdowns time to populate after exam selection

    # Dropdowns 4 & 5 populate AFTER exam is chosen — wait longer
    time.sleep(1.5)

    compare = [
        (4, compare_left),
        (5, compare_right),
    ]

    for index, value in compare:
        wait_for_option(driver, index, value, timeout=30)
        js_select(driver, get_selects(driver)[index], value)
        time.sleep(0.5)

    old_url = driver.current_url
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Enter']")
    )).click()
    wait.until(lambda d: d.current_url != old_url)

    # Click Overview tab explicitly
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//*[normalize-space()='Overview']")
    )).click()
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(),'Overview of Section')]")
    ))
    print(f"  ✅ Overview tab loaded — Section {section}, Exam {exam}\n")

# ================= TEST: PAGE HEADER =================

def test_page_header(driver, section):
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  [1] PAGE HEADER")
    cat = "Page Header"

    # Title — match only the element whose direct text is the heading
    els = driver.find_elements(
        By.XPATH,
        "//*[contains(normalize-space(text()),'Overview of Section')]"
    )
    title = next((e.text.strip() for e in els if e.is_displayed() and "\n" not in e.text.strip()), "")
    check(bool(title), f"Page title visible: '{title}'", driver, cat)

    expected_title = f"Overview of Section 12 {section}"
    if title and title != expected_title:
        flag_change("Page Title", expected_title, title)

    # Subtitle
    check(find_text(driver, "students"), "Student count visible in subtitle", driver, cat)
    check(find_text(driver, "MATHS"),    "Subject 'MATHS' visible in subtitle", driver, cat)

    # Tabs
    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        check(find_text(driver, tab), f"Tab '{tab}' present", driver, cat)


# ================= TEST: EXAM COMPARISON =================

def test_exam_comparison(driver, exam, compare_left, compare_right):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  [2] EXAM COMPARISON")
    cat = "Exam Comparison"

    check(find_text(driver, "Exam Comparison"),         "Heading 'Exam Comparison' visible",          driver, cat)
    check(find_text(driver, "Change in class average"), "Subtext 'Change in class average' visible",  driver, cat)
    check(find_text(driver, "Class Average"),           "Label 'Class Average' visible",              driver, cat)
    check(find_text(driver, compare_left),              f"Compare Left '{compare_left}' visible",     driver, cat)
    check(find_text(driver, compare_right),             f"Compare Right '{compare_right}' visible",   driver, cat)

    pt = body_text(driver)

    scores = re.findall(r"\d+\.?\d*%", pt)
    check(len(scores) >= 2, f"At least 2 score percentages visible: {scores[:4]}", driver, cat)

    trend = re.search(r"\d+\.?\d* points? (decline|increase)", pt, re.IGNORECASE)
    check(bool(trend), f"Trend badge visible: '{trend.group(0) if trend else 'NOT FOUND'}'", driver, cat)

    try:
        card = driver.find_element(
            By.XPATH,
            "//div[.//*[contains(text(),'Class Average')] and .//*[contains(text(),'Midterm')]]"
        )
        check(card.is_displayed(), "Exam comparison card box rendered", driver, cat)
    except:
        check(False, "Exam comparison card box rendered", driver, cat)


# ================= TEST: TARGET CHAPTERS =================

def test_target_chapters(driver):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  [3] TARGET THESE CHAPTERS  (Exam: {CURRENT_EXAM})")
    cat = f"Target Chapters [{CURRENT_EXAM}]"

    # ── Section heading ──────────────────────────────────────────
    # From HTML: <div class="text-zinc-800 text-2xl font-semibold">Target these chapters</div>
    try:
        heading_el = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'text-zinc-800') and contains(@class,'font-semibold') "
            "and normalize-space(text())='Target these chapters']"
        )
        check(heading_el.is_displayed(),
              "Heading 'Target these chapters' visible", driver, cat)
    except:
        check(False, "Heading 'Target these chapters' visible", driver, cat)
        print(f"  ℹ️  'Target these chapters' NOT present for Exam: {CURRENT_EXAM}")
        return

    # From HTML: <div class="text-[#5C616D] text-base font-medium">Chapters recommended...</div>
    try:
        subtext_el = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'text-base') and contains(@class,'font-medium') "
            "and contains(text(),'Chapters recommended')]"
        )
        check(subtext_el.is_displayed(),
              "Subtext 'Chapters recommended based on their board weightage...' visible",
              driver, cat)
    except:
        check(False,
              "Subtext 'Chapters recommended based on their board weightage...' visible",
              driver, cat)

    # ── Category configs from DOM ────────────────────────────────
    # Each category box: div.rounded-4xl containing:
    #   - Badge: div.rounded-lg.font-bold.flex.items-center with text e.g. "Reteach"
    #   - Count: div.text-zinc-700.text-sm.font-semibold e.g. "4 chapters"
    #   - Tip heading: div.flex.items-center.gap-2.text-base.font-bold
    #   - Tip body: span with colored text
    #   - Chapter rows: div.rounded-2xl.bg-white.border.border-gray-200 containing
    #                   div.font-bold.text-gray-700.normal-case

    CATEGORIES = {
        "Reteach": {
            "tip_heading": "Revise Thoroughly",
            "tip_words":   ["struggling", "core concepts", "high-weightage", "Reteach", "improvements"],
            "bg_class":    "bg-blue-50",
        },
        "Brushup": {
            "tip_heading": "Review Specific Concepts",
            "tip_words":   ["declined", "remain weak", "decent grasp", "core concepts"],
            "bg_class":    "bg-[#FFF7E6]",
        },
        "On Track": {
            "tip_heading": "Significant Improvement",
            "tip_words":   ["remained high", "improved", "at least 5%"],
            "bg_class":    "bg-green-50",
        },
    }

    # Find all category box containers
    # Each is a div.rounded-4xl containing the badge
    category_boxes = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'rounded-4xl') and "
        ".//div[contains(@class,'rounded-lg') and contains(@class,'font-bold') "
        "and contains(@class,'flex') and contains(@class,'items-center')]]"
    )

    found_labels = []
    for box in category_boxes:
        # Get label from badge div
        try:
            badge = box.find_element(
                By.XPATH,
                ".//div[contains(@class,'rounded-lg') and contains(@class,'font-bold') "
                "and contains(@class,'flex') and contains(@class,'items-center')]"
            )
            label = badge.text.strip()
        except:
            continue

        if label not in CATEGORIES:
            continue

        found_labels.append(label)
        meta = CATEGORIES[label]
        print(f"\n     ── {label} ──")

        check(bool(label), f"Category badge '{label}' visible", driver, cat)

        # Chapter count badge
        # From HTML: <div class="text-zinc-700 text-sm font-semibold">4 chapters</div>
        try:
            count_el = box.find_element(
                By.XPATH,
                ".//div[contains(@class,'text-zinc-700') and contains(@class,'text-sm') "
                "and contains(@class,'font-semibold') and contains(text(),'chapter')]"
            )
            count_txt = count_el.text.strip()
            check(bool(re.match(r"\d+ chapters?", count_txt)),
                  f"'{label}' — Chapter count badge: '{count_txt}'", driver, cat)
            print(f"       Count: {count_txt}")
        except:
            check(False, f"'{label}' — Chapter count badge visible", driver, cat)

        # Tip heading
        # From HTML: div.flex.items-center.gap-2.text-base.font-bold containing tip text
        try:
            tip_h_el = box.find_element(
                By.XPATH,
                f".//div[contains(@class,'text-base') and contains(@class,'font-bold') "
                f"and contains(normalize-space(),'{meta['tip_heading']}')]"
            )
            check(tip_h_el.is_displayed(),
                  f"'{label}' — Tip heading '{meta['tip_heading']}' visible", driver, cat)
        except:
            check(False,
                  f"'{label}' — Tip heading '{meta['tip_heading']}' visible", driver, cat)

        # Tip body words
        # From HTML: <span class="text-sky-700">...</span> inside tip container
        box_text = box.text
        for phrase in meta["tip_words"]:
            check(phrase.lower() in box_text.lower(),
                  f"'{label}' — Tip text contains '{phrase}'", driver, cat)

        # Chapter rows
        # From HTML: div.rounded-2xl.bg-white.border.border-gray-200
        #              > div.px-6.py-4.flex.items-center.justify-between.cursor-pointer
        #                > div.font-bold.text-gray-700.normal-case  ← chapter name
        #                > img[alt='Arrow Icon']                    ← chevron
        chapter_rows = box.find_elements(
            By.XPATH,
            ".//div[contains(@class,'font-bold') and contains(@class,'text-gray-700') "
            "and contains(@class,'normal-case')]"
        )

        chapters_found = []
        for row in chapter_rows:
            ch_name = row.text.strip()
            if ch_name and len(ch_name) > 2:
                chapters_found.append(ch_name)

        check(len(chapters_found) > 0,
              f"'{label}' — At least 1 chapter row found", driver, cat)

        print(f"       Chapters ({len(chapters_found)}):")
        for ch in chapters_found:
            print(f"         • {ch}")
            check(bool(ch),
                  f"'{label}' — Chapter '{ch}' listed and spelled", driver, cat)
            # Spelling: check each significant word
            for word in ch.split():
                if len(word) > 3:
                    check(word.lower() in box_text.lower(),
                          f"'{label}' — Word '{word}' spelled correctly in '{ch}'",
                          driver, cat)

        # Chevron arrow icon next to each chapter
        # From HTML: <img alt="Arrow Icon" ...>
        chevrons = box.find_elements(By.XPATH, ".//img[@alt='Arrow Icon']")
        check(len(chevrons) == len(chapters_found),
              f"'{label}' — Arrow icon present for each chapter "
              f"({len(chevrons)} icons, {len(chapters_found)} chapters)",
              driver, cat)

        # Lightbulb icon in tip
        bulbs = box.find_elements(By.XPATH, ".//svg[.//*[contains(@d,'M15 14')]]")
        check(len(bulbs) > 0,
              f"'{label}' — Lightbulb icon visible in tip", driver, cat)

    # Check all 3 categories were found
    for expected_label in CATEGORIES:
        if expected_label not in found_labels:
            print(f"  ℹ️  Category '{expected_label}' not present for Exam '{CURRENT_EXAM}'")

    check(len(found_labels) > 0,
          f"At least 1 category (Reteach/Brushup/On Track) found for Exam '{CURRENT_EXAM}'",
          driver, cat)


def test_highlighted_students(driver):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  [4] HIGHLIGHTED STUDENTS  (Exam: {CURRENT_EXAM})")
    cat = f"Highlighted Students [{CURRENT_EXAM}]"

    # ── Section heading ──────────────────────────────────────────
    # From HTML: <div class="justify-start text-zinc-800 text-2xl font-semibold font-['Inter']">
    #              Highlighted Students
    #            </div>
    try:
        hs_heading = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'text-zinc-800') and contains(@class,'font-semibold') "
            "and normalize-space(text())='Highlighted Students']"
        )
        check(hs_heading.is_displayed(),
              "Heading 'Highlighted Students' visible", driver, cat)
    except:
        check(False, "Heading 'Highlighted Students' visible", driver, cat)

    # ── Subtext ──────────────────────────────────────────────────
    # From HTML: <div class="...text-slate-500...font-medium...">
    #              Students classified based on their <span class="font-bold">preboard</span> scores.
    #            </div>
    try:
        subtext_el = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'text-slate-500') and contains(@class,'font-medium') "
            "and contains(.,'classified based on their')]"
        )
        subtext_txt = subtext_el.text.strip()
        check("classified based on their" in subtext_txt.lower(),
              f"Subtext visible: '{subtext_txt}'", driver, cat)
        # Check bold 'preboard' span
        bold_pre = subtext_el.find_elements(
            By.XPATH, ".//span[contains(@class,'font-bold')]"
        )
        check(any("preboard" in s.text.lower() for s in bold_pre),
              "Word 'preboard' is bold in subtext", driver, cat)
    except:
        check(False, "Subtext 'Students classified based on their preboard scores' visible",
              driver, cat)

    # ── 3 Box containers ─────────────────────────────────────────
    # From HTML: each box is div.rounded-4xl.border-l-2.bg-[#F1F5FA]
    #   Performing Well → border-amber-300
    #   Lagging         → border-neutral-400
    #   Weak            → border-neutral-400
    #
    # Inside each box:
    #   Title:  div.text-2xl.font-semibold.text-slate-600
    #   Count:  div.text-base.font-medium.text-black/50  e.g. "2 students"
    #   Rows:   div.px-8.py-4.flex.justify-between.rounded-2xl.bg-white.border.border-[#E6E8EC]
    #             div.font-bold.text-slate-500 → name
    #             div.font-bold.text-slate-500 → score
    #   Empty:  div.border-dashed (no cursor-pointer) → "No students in this category yet"
    #   More:   div.border-dashed.cursor-pointer → "+5 more students"

    # Get all 3 boxes ordered as they appear on page
    box_containers = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'rounded-4xl') and contains(@class,'border-l-2') "
        "and contains(@class,'bg-[#F1F5FA]')]"
    )

    check(len(box_containers) == 3,
          f"3 student boxes present on page (found: {len(box_containers)})", driver, cat)

    print(f"\n  {'─'*72}")
    print(f"  {'BOX':<20} {'STUDENT NAME':<36} {'MIDTERM':>10}  {'PREBOARD 1':>12}")
    print(f"  {'─'*72}")

    for box_el in box_containers:
        # ── Get title ────────────────────────────────────────────
        try:
            title_el = box_el.find_element(
                By.XPATH,
                ".//div[contains(@class,'text-2xl') and contains(@class,'font-semibold') "
                "and contains(@class,'text-slate-600')]"
            )
            label = title_el.text.strip()
        except:
            label = "Unknown"

        check(bool(label) and label in ["Performing Well", "Lagging", "Weak"],
              f"Box title valid: '{label}'", driver, cat)

        # ── Get student count ─────────────────────────────────────
        try:
            count_el  = box_el.find_element(
                By.XPATH,
                ".//div[contains(@class,'text-base') and contains(@class,'font-medium') "
                "and contains(@class,'text-black') and contains(text(),'students')]"
            )
            count_txt = count_el.text.strip()
            check(bool(re.match(r"\d+ students?", count_txt)),
                  f"'{label}' — Count badge: '{count_txt}'", driver, cat)
            is_empty  = count_txt.startswith("0")
        except:
            count_txt = "?"
            is_empty  = False

        # ── Empty state ──────────────────────────────────────────
        if is_empty:
            try:
                # div.border-dashed WITHOUT cursor-pointer = static empty box
                empty_el = box_el.find_element(
                    By.XPATH,
                    ".//div[contains(@class,'border-dashed') "
                    "and not(contains(@class,'cursor-pointer'))]"
                )
                check(empty_el.is_displayed(),
                      f"'{label}' — Dashed border empty box visible", driver, cat)
                empty_msg = empty_el.text.strip()
                check(empty_msg == "No students in this category yet",
                      f"'{label}' — Empty message: '{empty_msg}'", driver, cat)
            except:
                check(False,
                      f"'{label}' — Dashed border with empty message visible", driver, cat)
            print(f"  {label:<20} {'— 0 students (empty, dashed border)'}")
            continue

        # ── Student rows ─────────────────────────────────────────
        # div.px-8.py-4.flex.justify-between.rounded-2xl.bg-white.border.border-[#E6E8EC]
        student_row_els = box_el.find_elements(
            By.XPATH,
            ".//div[contains(@class,'px-8') and contains(@class,'py-4') "
            "and contains(@class,'justify-between') and contains(@class,'rounded-2xl') "
            "and contains(@class,'bg-white')]"
        )

        students = []
        for row in student_row_els:
            try:
                # Two div.font-bold.text-slate-500 → [name, score]
                cells = row.find_elements(
                    By.XPATH,
                    ".//div[contains(@class,'font-bold') and contains(@class,'text-slate-500')]"
                )
                if len(cells) >= 2:
                    name  = cells[0].text.strip()
                    score = cells[1].text.strip()
                    if name and len(name) > 2 and re.search(r"\d+\.?\d*%", score):
                        students.append({"name": name, "score": score})
            except:
                continue

        check(len(students) > 0,
              f"'{label}' — Student rows found ({count_txt})", driver, cat)

        # ── Overflow badge ────────────────────────────────────────
        # div.border-dashed.cursor-pointer → "+N more students"
        overflow_txt = ""
        try:
            overflow_el = box_el.find_element(
                By.XPATH,
                ".//div[contains(@class,'border-dashed') "
                "and contains(@class,'cursor-pointer')]"
            )
            overflow_txt = overflow_el.text.strip()
            check(bool(re.match(r"\+\d+ more students?", overflow_txt)),
                  f"'{label}' — Overflow badge: '{overflow_txt}'", driver, cat)
        except:
            pass  # overflow is optional

        # ── Print & test each student ─────────────────────────────
        for i, s in enumerate(students):
            name  = s["name"]
            score = s["score"]

            midterm_score  = score if CURRENT_EXAM.lower() == "midterm"  else "NA"
            preboard_score = score if "preboard" in CURRENT_EXAM.lower() else "NA"

            mid_flag  = " ⚠️" if midterm_score  == "NA" else ""
            pre_flag  = " ⚠️" if preboard_score == "NA" else ""

            box_col = label if i == 0 else ""
            print(f"  {box_col:<20} {name:<36} {midterm_score:>10}{mid_flag}  {preboard_score:>12}{pre_flag}")

            check(bool(name),
                  f"'{label}' — Name present: '{name}'", driver, cat)
            check(bool(re.search(r"\d+\.?\d*%", score)),
                  f"'{label}' | '{name}' — Score format valid: '{score}'", driver, cat)
            check(midterm_score  != "NA",
                  f"'{label}' | '{name}' — Midterm score: {midterm_score}", driver, cat)
            check(preboard_score != "NA",
                  f"'{label}' | '{name}' — Preboard 1 score: {preboard_score}", driver, cat)

        if overflow_txt:
            print(f"  {'':20} {overflow_txt} (hidden — click to expand)")

    print(f"  {'─'*72}")

    # Overall score check
    pt = body_text(driver)
    all_scores = re.findall(r"\d+\.?\d*%", pt)
    check(len(all_scores) >= 1,
          f"Score percentages present on page: {all_scores[:8]}", driver, cat)


def test_layout(driver):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  [5] LAYOUT & SCROLL")
    cat = "Layout"

    sw = driver.execute_script("return document.body.scrollWidth")
    cw = driver.execute_script("return document.body.clientWidth")
    check(sw <= cw, f"No horizontal scroll (scrollW={sw}, clientW={cw})", driver, cat)

    for box in ["Performing Well", "Lagging", "Weak"]:
        check(find_text(driver, box), f"Student box '{box}' visible", driver, cat)


# ================= TEST: SPELLING SWEEP =================

def test_spelling_sweep(driver, section):
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  [6] SPELLING SWEEP  (Exam: {CURRENT_EXAM})")
    cat = f"Spelling [{CURRENT_EXAM}]"
    pt  = body_text(driver)

    # Static phrases always expected regardless of exam
    static_phrases = [
        f"Overview of Section 12 {section}",
        "Exam Comparison",
        "Change in class average",
        "Class Average",
        "Highlighted Students",
        "preboard scores",
        "Performing Well",
        "Lagging",
        "Weak",
    ]

    # Dynamic phrases — only check if they are actually visible on the page
    dynamic_phrases = [
        "Target these chapters",
        "Chapters recommended based on their board weightage",
        "Reteach",
        "Brushup",
        "On Track",
        "Revise Thoroughly",
        "struggling with core concepts",
        "high-weightage units",
        "Review Specific Concepts",
        "declined or remain weak",
        "Significant Improvement",
        "remained high or improved by at least",
    ]

    print("  -- Static phrases (always required) --")
    for phrase in static_phrases:
        present = phrase.lower() in pt.lower()
        check(present, f'"{phrase}"', driver, cat)
        if not present:
            missing = [w for w in phrase.split() if len(w) > 3 and w.lower() not in pt.lower()]
            if missing:
                flag_change(f"Missing text [{CURRENT_EXAM}]", phrase, f"Missing words: {missing}")

    print("  -- Dynamic phrases (present only for certain exams) --")
    for phrase in dynamic_phrases:
        present = phrase.lower() in pt.lower()
        if present:
            check(True, f'"{phrase}" present and spelled correctly', driver, cat)
        else:
            print(f"  ℹ️  Not on page for Exam '{CURRENT_EXAM}': \"{phrase}\"")


# ================= SUMMARY =================

def print_summary(section, exam):
    passed = [t for t in TEST_RESULTS if t["status"] == "PASS"]
    failed = [t for t in TEST_RESULTS if t["status"] == "FAIL"]

    print(f"\n{'='*52}")
    print(f"  OVERVIEW TEST REPORT")
    print(f"  Section : {section}")
    print(f"  Exam    : {exam}")
    print(f"{'='*52}")
    print(f"  Total   : {len(TEST_RESULTS)}")
    print(f"  Passed  : {len(passed)}")
    print(f"  Failed  : {len(failed)}")

    if failed:
        print(f"\n  FAILED TESTS:")
        for t in failed:
            print(f"    [Section {t['section']} | Exam: {t['exam']}]")
            print(f"    [{t['category']}] {t['message']}")

    if CHANGES_DETECTED:
        print(f"\n  CHANGES DETECTED:")
        for c in CHANGES_DETECTED:
            print(f"    {c['field']}")
            print(f"      Expected : {c['expected']}")
            print(f"      Actual   : {c['actual']}")

    report = {
        "section":  section,
        "exam":     exam,
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary":  {"total": len(TEST_RESULTS), "passed": len(passed), "failed": len(failed)},
        "results":  TEST_RESULTS,
        "changes":  CHANGES_DETECTED,
    }
    fname = f"Overview_Report_Section{section}_{exam.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, "w") as f:
        json.dump(report, f, indent=4)

    print(f"\n  Report saved: {fname}")
    print(f"{'='*52}\n")


def main():
    global CURRENT_SECTION, CURRENT_EXAM

    print("\n== OVERVIEW TAB TEST ==")
    print("-" * 40)

    section = input("Enter Section (e.g. M, N, P, Q) : ").strip().upper()
    exam    = input("Enter Exam    (e.g. Midterm)     : ").strip()

    if not section or not exam:
        print("Section and Exam are required. Exiting.")
        return

    CURRENT_SECTION = section
    CURRENT_EXAM    = exam

    print(f"\n  Class         : {BASE_VALUES['Class']}")
    print(f"  Section       : {section}")
    print(f"  Subject       : {BASE_VALUES['Subject']}")
    print(f"  Exam          : {exam}")
    print(f"  Compare Left  : {BASE_VALUES['CompareLeft']}  (default)")
    print(f"  Compare Right : {BASE_VALUES['CompareRight']} (default)")
    print("-" * 40)

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait   = WebDriverWait(driver, 30)

    try:
        login(driver, wait)
        load_overview(driver, wait, section, exam,
                      BASE_VALUES["CompareLeft"], BASE_VALUES["CompareRight"])

        test_page_header(driver, section)
        test_exam_comparison(driver, exam, BASE_VALUES["CompareLeft"], BASE_VALUES["CompareRight"])
        test_target_chapters(driver)
        test_highlighted_students(driver)
        test_layout(driver)
        test_spelling_sweep(driver, section)

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        driver.save_screenshot("error.png")

    finally:
        print_summary(section, exam)
        if KEEP_BROWSER_OPEN:
            input("\nPress ENTER to close browser...")
        driver.quit()


if __name__ == "__main__":
    main()
=======
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.maximize_window()

# 👉 PUT YOUR REAL STUDENT PAGE URL HERE
driver.get("https://example.com")

wait = WebDriverWait(driver, 20)

wait.until(EC.presence_of_element_located((By.XPATH, "//table")))

rows = driver.find_elements(By.XPATH, "//table//tr")

for row in rows:
    try:
        text = row.text.lower()

        if "improved" in text:
            print("Clicking Improve")
            row.find_element(By.XPATH, ".//button[contains(text(),'Improve')]").click()
            time.sleep(2)

        elif "declined" in text:
            print("Clicking Decline")
            row.find_element(By.XPATH, ".//button[contains(text(),'Decline')]").click()
            time.sleep(2)

    except:
        pass

print("DONE")
time.sleep(5)
driver.quit()
>>>>>>> b459d12 (saving local changes before pull)
