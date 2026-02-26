import time
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from openpyxl import Workbook


# ================= CONFIG =================

LOGIN_URL = "https://classlens.inferentics.com/login"
USERNAME = "sajan"
PASSWORD = "Operations123"

VALUES = {
    "Class": "12",
    "Section": "N",
    "Subject": "MATHS",
    "Exam": "Midterm",
    "CompareLeft": "Midterm",
    "CompareRight": "Preboard 1",
}

WAIT_TIME = 30
STUDENT_RESULTS = []


# ================= UTIL =================

def check(condition, message):
    status = "PASS" if condition else "FAIL"
    icon = "✅" if condition else "❌"
    print(f"{icon} {status}: {message}")


def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)


def select_dropdown(driver, index, value):
    selects = driver.find_elements(By.TAG_NAME, "select")
    Select(selects[index]).select_by_visible_text(value)


def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text']")
    )).send_keys(USERNAME)

    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(),'Enter your Class')]")
    ))

    check(True, "Login Successful")


# ================= FILTERS =================

def apply_filters(driver, wait):
    wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

    for i, key in enumerate(VALUES.values()):
        select_dropdown(driver, i, key)

    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[normalize-space()='Overview']")
    ))

    check(True, "Filters Applied")


# ================= TABS =================

def test_tabs(driver, wait):
    print("\n📊 Testing Tabs")

    tabs = ["Overview", "Chapters", "Questions", "Students"]

    for tab in tabs:
        try:
            tab_element = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//*[normalize-space()='{tab}']")
                )
            )
            safe_click(driver, tab_element)
            check(True, f"{tab} Tab Clickable")
        except:
            check(False, f"{tab} Tab Failed")


# ================= OVERVIEW =================

def test_overview(driver, wait):
    print("\n📊 Testing Overview")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Overview']"))

    check("Class Average" in driver.page_source, "Class Average Visible")
    check("Target" in driver.page_source, "Target Section Visible")
    check("Highlighted" in driver.page_source, "Highlighted Students Visible")


# ================= CHAPTERS =================

def test_chapters(driver, wait):
    print("\n📘 Testing Chapters")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Chapters']"))

    chapter_locator = "//div[contains(@class,'cursor-pointer') and .//*[contains(text(),'%')]]"
    wait.until(EC.presence_of_all_elements_located((By.XPATH, chapter_locator)))

    chapters = driver.find_elements(By.XPATH, chapter_locator)

    check(len(chapters) > 0, "Chapters Loaded")

    for chapter in chapters:
        check("%" in chapter.text, "Valid % in Chapter")


# ================= QUESTIONS =================

def test_questions(driver, wait):
    print("\n📗 Testing Questions")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Questions']"))

    question_locator = (
        By.XPATH,
        "//div[contains(@class,'cursor-pointer') and .//span[starts-with(text(),'Q')]]"
    )

    wait.until(EC.presence_of_all_elements_located(question_locator))
    questions = driver.find_elements(*question_locator)

    check(len(questions) > 0, "Questions Loaded")

    for question in questions:
        safe_click(driver, question)
        check("Chapter" in driver.page_source, "Chapter Visible")
        check("Concepts" in driver.page_source, "Concepts Visible")
        check("Type" in driver.page_source, "Type Visible")


# ================= STUDENTS =================

def test_students(driver, wait):
    print("\n👩‍🎓 Testing Students")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Students']"))

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(),'Your Students')]")
    ))

    left_panel = driver.find_element(By.XPATH, "//div[contains(@class,'col-span-4')]")

    processed = set()
    previous_count = 0

    while True:
        cards = left_panel.find_elements(
            By.XPATH,
            ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded')]"
        )

        if len(cards) == previous_count:
            break

        previous_count = len(cards)

        for card in cards:
            name = card.find_element(By.TAG_NAME, "p").text.strip()

            if name in processed:
                continue

            processed.add(name)

            safe_click(driver, card)
            time.sleep(1)

            body_text = driver.find_element(By.TAG_NAME, "body").text
            marks_matches = re.findall(r"(\d+\.?\d*)/(\d+\.?\d*)", body_text)

            if len(marks_matches) >= 2:
                left_marks = float(marks_matches[0][0])
                left_total = float(marks_matches[0][1])
                right_marks = float(marks_matches[1][0])
                right_total = float(marks_matches[1][1])

                left_percent = (left_marks / left_total) * 100
                right_percent = (right_marks / right_total) * 100

                diff = round(left_percent - right_percent, 2)

                if diff > 0:
                    status = "IMPROVED"
                elif diff < 0:
                    status = "DECLINED"
                else:
                    status = "NO CHANGE"

                print(f"{name}: {status} ({diff}%)")

                STUDENT_RESULTS.append({
                    "Student": name,
                    "Left Marks": f"{left_marks}/{left_total}",
                    "Right Marks": f"{right_marks}/{right_total}",
                    "Difference %": diff,
                    "Status": status
                })

        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", left_panel)
        time.sleep(1)

    check(len(processed) > 0, "All Students Processed")


# ================= EXCEL =================

def generate_excel_report():
    wb = Workbook()
    ws = wb.active
    ws.title = "Student Comparison Report"

    ws.append(["Student", "Left Marks", "Right Marks", "Difference %", "Status"])

    for r in STUDENT_RESULTS:
        ws.append([
            r["Student"],
            r["Left Marks"],
            r["Right Marks"],
            r["Difference %"],
            r["Status"],
        ])

    file_name = f"Student_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(file_name)

    print(f"\n📊 Excel Saved: {file_name}")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    login(driver, wait)
    apply_filters(driver, wait)

    test_tabs(driver, wait)
    test_overview(driver, wait)
    test_chapters(driver, wait)
    test_questions(driver, wait)
    test_students(driver, wait)

    generate_excel_report()

    input("\nPress ENTER to close browser...")
    driver.quit()


if __name__ == "__main__":
    main()