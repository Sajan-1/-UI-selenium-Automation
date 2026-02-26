import json
import time
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager

# ================= CONFIG =================

URL = "https://classlens.inferentics.com/login"
USERNAME = "sajan"
PASSWORD = "Operations123"

WAIT = 30
RESULTS = []

# ================= LOGGER =================

def log(condition, msg, driver=None):
    status = "PASS" if condition else "FAIL"
    print(("✅" if condition else "❌"), msg)

    RESULTS.append({
        "status": status,
        "message": msg,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    if not condition and driver:
        driver.save_screenshot(f"failure_{int(time.time())}.png")

# ================= SAFE ACTIONS =================

def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)

def percent(text):
    return re.search(r"[+-]?\d+\.?\d*%", text) is not None

# ================= DRIVER =================

def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# ================= LOGIN =================

def test_login(driver, wait):
    driver.get(URL)

    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='text']"))).send_keys(USERNAME)
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Enter your Class')]")))
    log(True, "Login success")

# ================= FILTERS =================

def test_filters(driver, wait):
    wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

    values = ["12", "N", "MATHS", "Midterm", "Midterm", "Preboard 1"]

    for i, v in enumerate(values):
        selects = driver.find_elements(By.TAG_NAME, "select")
        Select(selects[i]).select_by_visible_text(v)

    driver.find_element(By.XPATH, "//button[.='Enter']").click()
    wait.until(EC.visibility_of_element_located((By.XPATH, "//*[.='Overview']")))

    log(True, "Filters applied")

# ================= OVERVIEW =================

def test_overview(driver, wait):

    safe_click(driver, driver.find_element(By.XPATH, "//*[.='Overview']"))

    elements = [
        "Exam Comparison",
        "Class Average",
        "Target",
        "Highlighted"
    ]

    for text in elements:
        log(wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(.,'{text}')]"))), f"{text} visible")

    cards = driver.find_elements(By.XPATH, "//div[contains(@class,'rounded')]")
    log(len(cards) >= 3, "Overview cards loaded")

# ================= CHAPTERS =================

def test_chapters(driver, wait):

    safe_click(driver, driver.find_element(By.XPATH, "//*[.='Chapters']"))

    locator = "//div[contains(@class,'cursor-pointer')]"
    wait.until(EC.presence_of_all_elements_located((By.XPATH, locator)))

    total = len(driver.find_elements(By.XPATH, locator))
    log(total > 0, "Chapters loaded")

    for i in range(total):
        for _ in range(3):
            try:
                chapters = driver.find_elements(By.XPATH, locator)
                text = chapters[i].text
                log(percent(text), "Chapter % present")
                safe_click(driver, chapters[i])
                break
            except StaleElementReferenceException:
                time.sleep(1)

# ================= QUESTIONS =================

def test_questions(driver, wait):

    safe_click(driver, driver.find_element(By.XPATH, "//*[.='Questions']"))

    locator = "//div[contains(@class,'cursor-pointer')]"
    wait.until(EC.presence_of_all_elements_located((By.XPATH, locator)))

    total = len(driver.find_elements(By.XPATH, locator))
    log(total > 0, "Questions loaded")

    for i in range(min(5, total)):
        for _ in range(3):
            try:
                questions = driver.find_elements(By.XPATH, locator)
                safe_click(driver, questions[i])
                time.sleep(1)
                log(True, "Question opened")
                break
            except StaleElementReferenceException:
                time.sleep(1)

# ================= STUDENTS =================

def test_students(driver, wait):

    safe_click(driver, driver.find_element(By.XPATH, "//*[.='Students']"))

    locator = "//div[contains(@class,'rounded') and contains(@class,'cursor-pointer')]"
    wait.until(EC.presence_of_all_elements_located((By.XPATH, locator)))

    students = driver.find_elements(By.XPATH, locator)
    log(len(students) >= 5, "Students loaded")

    for i in range(min(10, len(students))):
        for _ in range(3):
            try:
                students = driver.find_elements(By.XPATH, locator)
                text = students[i].text
                log(percent(text), "Student % valid")
                safe_click(driver, students[i])
                break
            except StaleElementReferenceException:
                time.sleep(1)

# ================= SUMMARY =================

def summary():
    print("\n=========== TEST SUMMARY ===========")

    passed = len([r for r in RESULTS if r["status"] == "PASS"])
    failed = len([r for r in RESULTS if r["status"] == "FAIL"])

    print("Total Tests:", len(RESULTS))
    print("Passed:", passed)
    print("Failed:", failed)

    with open("report.json", "w") as f:
        json.dump(RESULTS, f, indent=4)

# ================= MAIN =================

def main():
    driver = create_driver()
    wait = WebDriverWait(driver, WAIT)

    test_login(driver, wait)
    test_filters(driver, wait)
    test_overview(driver, wait)
    test_chapters(driver, wait)
    test_questions(driver, wait)
    test_students(driver, wait)

    summary()
    driver.quit()

if __name__ == "__main__":
    main()