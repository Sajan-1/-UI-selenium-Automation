import json
import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
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

FAILED_REPORT = "failed_cases.json"
FAILED_CASES = []


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ================= UTILITIES =================

def log_failure(test_name, error, driver):
    print(f"❌ {test_name} FAILED → {error}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot = f"{test_name}_{timestamp}.png".replace(" ", "_")
    driver.save_screenshot(screenshot)

    FAILED_CASES.append({
        "test": test_name,
        "error": str(error),
        "screenshot": screenshot
    })


def safe_wait(wait, condition, name, driver):
    try:
        return wait.until(condition)
    except TimeoutException:
        log_failure(name, "Timeout waiting for element", driver)
        return None


def select_dropdown(driver, index, value):
    selects = driver.find_elements(By.TAG_NAME, "select")
    Select(selects[index]).select_by_visible_text(value)


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    safe_wait(wait,
              EC.visibility_of_element_located((By.XPATH, "//input[@type='text']")),
              "Login Page Load", driver).send_keys(USERNAME)

    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Enter your Class')]")),
              "Login Verification", driver)

    print("✅ Login Successful")


# ================= FILTERS =================

def apply_filters(driver, wait):
    safe_wait(wait,
              lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6,
              "Filter Load", driver)

    select_dropdown(driver, 0, VALUES["Class"])
    select_dropdown(driver, 1, VALUES["Section"])
    select_dropdown(driver, 2, VALUES["Subject"])
    select_dropdown(driver, 3, VALUES["Exam"])
    select_dropdown(driver, 4, VALUES["CompareLeft"])
    select_dropdown(driver, 5, VALUES["CompareRight"])

    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Overview']")),
              "Overview Load", driver)

    print("✅ Filters Applied")


# ================= OVERVIEW =================

def validate_overview(driver, wait):
    print("\n🔎 Testing Overview")

    driver.find_element(By.XPATH, "//*[normalize-space()='Overview']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Reteach')]")),
              "Overview Sections", driver)

    sections = ["Reteach", "Brushup", "On Track"]

    for section in sections:
        try:
            el = driver.find_element(By.XPATH, f"//*[contains(text(),'{section}')]")
            if not el.is_displayed():
                raise Exception("Not visible")
        except Exception as e:
            log_failure(f"Overview Section - {section}", e, driver)

    print("✅ Overview Validated")


# ================= CHAPTERS =================

def validate_chapters(driver, wait):
    print("\n🔎 Testing Chapters")

    driver.find_element(By.XPATH, "//*[normalize-space()='Chapters']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select a chapter')]")),
              "Chapters Load", driver)

    chapter_locator = "//div[contains(@class,'cursor-pointer')]"

    chapter_count = len(driver.find_elements(By.XPATH, chapter_locator))

    if chapter_count == 0:
        log_failure("Chapters", "No chapters found", driver)
        return

    print(f"Found {chapter_count} chapters")

    for i in range(chapter_count):
        try:
            chapters = driver.find_elements(By.XPATH, chapter_locator)
            chapter = chapters[i]
            name = chapter.text.split("\n")[0]

            driver.execute_script("arguments[0].click();", chapter)

            safe_wait(wait,
                      EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{name}')]")),
                      f"Chapter Detail - {name}", driver)

            print(f"✅ Chapter OK → {name}")

            # Return to list
            driver.find_element(By.XPATH, "//*[normalize-space()='Chapters']").click()
            safe_wait(wait,
                      EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Select a chapter')]")),
                      "Back to Chapters", driver)

        except StaleElementReferenceException:
            print("🔁 Retrying stale chapter...")
            continue
        except Exception as e:
            log_failure(f"Chapter - index {i}", e, driver)


# ================= QUESTIONS =================

def validate_questions(driver, wait):
    print("\n🔎 Testing Questions")

    driver.find_element(By.XPATH, "//*[normalize-space()='Questions']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Sort By')]")),
              "Questions Load", driver)

    question_locator = "//*[starts-with(normalize-space(),'Q')]"
    question_count = len(driver.find_elements(By.XPATH, question_locator))

    if question_count == 0:
        log_failure("Questions", "No questions found", driver)
        return

    for i in range(question_count):
        try:
            questions = driver.find_elements(By.XPATH, question_locator)
            q = questions[i]

            driver.execute_script("arguments[0].click();", q)

            for field in ["Chapter", "Marks", "Full Marks", "Average"]:
                safe_wait(wait,
                          EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{field}')]")),
                          f"Question Field - {field}", driver)

            print(f"✅ Question {i+1} OK")

        except StaleElementReferenceException:
            continue
        except Exception as e:
            log_failure(f"Question - index {i}", e, driver)


# ================= STUDENTS =================

def validate_students(driver, wait):
    print("\n🔎 Testing Students")

    driver.find_element(By.XPATH, "//*[normalize-space()='Students']").click()

    safe_wait(wait,
              EC.presence_of_element_located((By.XPATH, "//*[text()='Your Students']")),
              "Students Load", driver)

    left_panel = driver.find_element(By.XPATH, "//div[contains(@class,'col-span-4')]")
    processed = set()

    while True:
        cards = left_panel.find_elements(
            By.XPATH,
            ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')]"
        )

        for i in range(len(cards)):
            try:
                cards = left_panel.find_elements(
                    By.XPATH,
                    ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')]"
                )

                card = cards[i]
                name = card.find_element(By.TAG_NAME, "p").text.strip()

                if name in processed:
                    continue

                processed.add(name)

                driver.execute_script("arguments[0].click();", card)

                safe_wait(wait,
                          EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{name}')]")),
                          f"Student Detail - {name}", driver)

                safe_wait(wait,
                          EC.presence_of_element_located((By.XPATH, "//p[contains(@class,'text-5xl')]")),
                          f"Student Marks - {name}", driver)

                marks = driver.find_elements(By.XPATH, "//p[contains(@class,'text-5xl')]")

                if len(marks) < 2:
                    raise Exception("Less than 2 marks")

                mid = marks[0].text.strip()
                pre = marks[1].text.strip()

                if not re.search(r"\d", mid):
                    raise Exception("Invalid Midterm")

                if not re.search(r"\d", pre):
                    raise Exception("Invalid Preboard")

                print(f"✅ Student OK → {name}")

            except StaleElementReferenceException:
                continue
            except Exception as e:
                log_failure(f"Student - {name}", e, driver)

        last_scroll = driver.execute_script("return arguments[0].scrollTop;", left_panel)
        driver.execute_script("arguments[0].scrollTop += 400;", left_panel)
        time.sleep(1)
        new_scroll = driver.execute_script("return arguments[0].scrollTop;", left_panel)

        if new_scroll == last_scroll:
            break


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 20)

    print("\n🚀 MASTER SUITE STARTED\n")

    try:
        login(driver, wait)
        apply_filters(driver, wait)

        validate_overview(driver, wait)
        validate_chapters(driver, wait)
        validate_questions(driver, wait)
        validate_students(driver, wait)

    except Exception as e:
        log_failure("Critical Error", e, driver)

    with open(FAILED_REPORT, "w", encoding="utf-8") as f:
        json.dump(FAILED_CASES, f, indent=2)

    print("\n============================")
    print("📋 FINAL TEST REPORT")
    print("============================")

    if FAILED_CASES:
        print(f"\n❌ Total Failed Cases: {len(FAILED_CASES)}")
        for fail in FAILED_CASES:
            print(f"• {fail['test']}")
    else:
        print("🎉 ALL TESTS PASSED")

    print("\n🟢 Browser remains open for inspection.")
    input("\nPress ENTER to close browser manually...")
    driver.quit()


if __name__ == "__main__":
    main()