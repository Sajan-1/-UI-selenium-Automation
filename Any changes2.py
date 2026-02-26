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
TEST_RESULTS = []


# ================= UTIL FUNCTIONS =================

def check(condition, message, driver=None):
    status = "PASS" if condition else "FAIL"
    icon = "✅" if condition else "❌"
    print(f"{icon} {status}: {message}")

    TEST_RESULTS.append({
        "status": status,
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    if not condition and driver:
        driver.save_screenshot(
            f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )


def verify_visible_text(driver, text):
    try:
        elements = driver.find_elements(
            By.XPATH,
            f"//*[contains(translate(normalize-space(.),"
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
            f"'{text.lower()}')]"
        )
        return any(el.is_displayed() for el in elements)
    except:
        return False


def has_percentage(text):
    return re.search(r"[+-]?\d+\.?\d*%", text) is not None


def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    driver.execute_script("arguments[0].click();", element)


def select_dropdown(driver, index, value):
    selects = driver.find_elements(By.TAG_NAME, "select")
    Select(selects[index]).select_by_visible_text(value)


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ================= LOGIN =================

def login(driver, wait):
    try:
        driver.get(LOGIN_URL)

        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//input[@type='text']")
        )).send_keys(USERNAME)

        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Enter your Class')]")
        ))

        check(True, "Login Successful", driver)

    except Exception as e:
        check(False, f"Login Failed: {e}", driver)


# ================= FILTERS =================

def apply_filters(driver, wait):
    try:
        wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

        for i, key in enumerate(VALUES.values()):
            select_dropdown(driver, i, key)

        driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[normalize-space()='Overview']")
        ))

        check(True, "Filters Applied Successfully", driver)

    except Exception as e:
        check(False, f"Filters Failed: {e}", driver)


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
            check(True, f"Tab '{tab}' clickable", driver)
        except Exception as e:
            check(False, f"Tab '{tab}' failed: {e}", driver)


# ================= OVERVIEW =================

def test_overview(driver, wait):
    print("\n📊 Testing Overview")

    try:
        safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Overview']"))

        try:
            wait.until(EC.visibility_of_element_located((
                By.XPATH,
                "//*[contains(translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), "
                "'exam comparison')]"
            )))
            check(True, "Exam Comparison visible", driver)
        except TimeoutException:
            check(False, "Exam Comparison visible", driver)

        check(verify_visible_text(driver, "Class Average"),
              "Class Average visible", driver)

        check(verify_visible_text(driver, "Target"),
              "Target section visible", driver)

        check(verify_visible_text(driver, "Highlighted"),
              "Highlighted Students visible", driver)

    except Exception as e:
        check(False, f"Overview failed: {e}", driver)


# ================= CHAPTERS =================

def test_chapters(driver, wait):
    print("\n📘 Testing Chapters")

    try:
        safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Chapters']"))

        chapter_locator = "//div[contains(@class,'cursor-pointer') and .//*[contains(text(),'%')]]"
        wait.until(EC.presence_of_all_elements_located((By.XPATH, chapter_locator)))

        chapters = driver.find_elements(By.XPATH, chapter_locator)
        check(len(chapters) > 0, "Chapter list loaded", driver)

        for chapter in chapters:
            name = chapter.text.split("\n")[0]
            check(has_percentage(chapter.text),
                  f"Valid % format in '{name}'", driver)
            safe_click(driver, chapter)

    except Exception as e:
        check(False, f"Chapters section failed: {e}", driver)


# ================= QUESTIONS =================

def test_questions(driver, wait):
    print("\n📗 Testing Questions")

    try:
        safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Questions']"))

        question_locator = (
            By.XPATH,
            "//div[contains(@class,'cursor-pointer') and .//span[starts-with(text(),'Q')]]"
        )

        wait.until(EC.presence_of_all_elements_located(question_locator))
        questions = driver.find_elements(*question_locator)

        check(len(questions) > 0, "Questions loaded", driver)

        for question in questions:
            q_text = question.find_element(
                By.XPATH, ".//span[starts-with(text(),'Q')]"
            ).text

            check(re.search(r"\b\d+\b", question.text) is not None,
                  f"Marks value present in {q_text}", driver)

            safe_click(driver, question)

            fields = ["Chapter", "Concepts", "Type", "Full", "Partial", "Wrong"]

            for field in fields:
                check(verify_visible_text(driver, field),
                      f"{field} visible in {q_text}", driver)

    except Exception as e:
        check(False, f"Questions section failed: {e}", driver)


# ================= STUDENTS =================

def test_students(driver, wait):
    print("\n👩‍🎓 Testing Students")

    try:
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

                # ✅ FIXED STATUS DETECTION FROM STUDENT CARD
                card_text = card.text
                percent_match = re.search(r"([+-]\d+\.?\d*)%", card_text)

                status = None

                if percent_match:
                    percent_value = percent_match.group(1)

                    if percent_value.startswith("+"):
                        status = "IMPROVED"
                    elif percent_value.startswith("-"):
                        status = "DECLINED"
                elif "No Change" in card_text:
                    status = "NO CHANGE"

                if status:
                    print(f"📈 {name} Status: {status}")
                    check(True, f"{status} badge detected for {name}", driver)
                else:
                    check(False, f"Status badge NOT detected for {name}", driver)

                check(has_percentage(card_text),
                      f"Valid % format for {name}", driver)

                safe_click(driver, card)

                wait.until(EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(),'{name}')]")
                ))

            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", left_panel)
            time.sleep(1)

        check(len(processed) > 0, "All Students Tested", driver)

    except Exception as e:
        check(False, f"Students section failed: {e}", driver)


# ================= SUMMARY =================

def print_summary():
    print("\n================ TEST SUMMARY ================")

    passed = [t for t in TEST_RESULTS if t["status"] == "PASS"]
    failed = [t for t in TEST_RESULTS if t["status"] == "FAIL"]

    print(f"\nTotal Tests: {len(TEST_RESULTS)}")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\n❌ FAILED TEST CASES:")
        for t in failed:
            print(" -", t["message"])
    else:
        print("\n🎉 ALL TESTS PASSED")

    report_name = f"Test_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_name, "w") as f:
        json.dump(TEST_RESULTS, f, indent=4)

    print(f"\n📄 Report Saved As: {report_name}")
    print("=============================================")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    print("\n🚀 MASTER TEST SUITE STARTED\n")

    login(driver, wait)

    if any(t["status"] == "FAIL" for t in TEST_RESULTS):
        print_summary()
        driver.quit()
        return

    apply_filters(driver, wait)
    test_tabs(driver, wait)
    test_overview(driver, wait)
    test_chapters(driver, wait)
    test_questions(driver, wait)
    test_students(driver, wait)

    print_summary()

    input("\nPress ENTER to close browser...")
    driver.quit()


if __name__ == "__main__":
    main()