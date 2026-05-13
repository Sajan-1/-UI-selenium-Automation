import json
import re
import time
import traceback
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

LOGIN_URL = "https://classlens.inferentics.com"
USERNAME = "sajan"
PASSWORD = "Operations123"

VALUES = {
    "Class": "12",
    "Section": "N",
    "Subject": "Maths",
    "Exam": "Midterm",
    "CompareLeft": "Midterm",
    "CompareRight": "Preboard 1",
}

WAIT_TIME = 25


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ================= UTILITIES =================

def safe_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)


def compute_change(mid, pre):
    try:
        m = float(re.findall(r"-?\d+\.?\d*", mid)[0])
        p = float(re.findall(r"-?\d+\.?\d*", pre)[0])
        diff = round(p - m, 1)
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff}%"
    except:
        return "NA"


def select_dropdown(driver, index, value):
    selects = driver.find_elements(By.TAG_NAME, "select")
    Select(selects[index]).select_by_visible_text(value)


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

    print("✅ Login Successful")


# ================= FILTERS =================

def apply_filters(driver, wait):

    wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

    select_dropdown(driver, 0, VALUES["Class"])
    select_dropdown(driver, 1, VALUES["Section"])
    select_dropdown(driver, 2, VALUES["Subject"])
    select_dropdown(driver, 3, VALUES["Exam"])
    select_dropdown(driver, 4, VALUES["CompareLeft"])
    select_dropdown(driver, 5, VALUES["CompareRight"])

    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[normalize-space()='Overview']")
    ))

    print("✅ Filters Applied")


# ================= OVERVIEW =================

def test_overview(driver, wait):

    print("\n📊 Testing Overview")

    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(),'{tab}')]")
        ))

    for bucket in ["Reteach", "Brushup", "On Track"]:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(),'{bucket}')]")
        ))

    print("🟢 Overview Passed")


# ================= CHAPTERS =================

def test_chapters(driver, wait):

    print("\n📘 Testing Chapters")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Chapters']"))
    time.sleep(1)

    chapter_locator = "//div[contains(@class,'cursor-pointer') and .//*[contains(text(),'%')]]"
    wait.until(EC.presence_of_all_elements_located((By.XPATH, chapter_locator)))

    chapters = driver.find_elements(By.XPATH, chapter_locator)

    for i in range(len(chapters)):
        chapters = driver.find_elements(By.XPATH, chapter_locator)
        chapter = chapters[i]

        chapter_name = chapter.text.split("\n")[0]
        safe_click(driver, chapter)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(),'{chapter_name}')]")
        ))

        print(f"✅ {chapter_name}")

    print("🟢 Chapters Passed")


# ================= QUESTIONS =================

def test_questions(driver, wait):

    print("\n📗 Testing Questions")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Questions']"))
    time.sleep(1)

    question_locator = (
        By.XPATH,
        "//div[contains(@class,'cursor-pointer') and .//span[starts-with(text(),'Q')]]"
    )

    wait.until(EC.presence_of_all_elements_located(question_locator))

    questions = driver.find_elements(*question_locator)

    for i in range(len(questions)):
        questions = driver.find_elements(*question_locator)
        question = questions[i]

        q_text = question.find_element(
            By.XPATH, ".//span[starts-with(text(),'Q')]"
        ).text

        safe_click(driver, question)

        for field in ["Chapter", "Concepts", "Marks", "Average"]:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(),'{field}')]")
            ))

        print(f"✅ {q_text}")

    print("🟢 Questions Passed")


# ================= STUDENTS =================

def test_students(driver, wait):

    print("\n👩‍🎓 Testing Students")

    safe_click(driver, driver.find_element(By.XPATH, "//*[normalize-space()='Students']"))
    time.sleep(1)

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[text()='Your Students']")
    ))

    left_panel = driver.find_element(
        By.XPATH, "//div[contains(@class,'col-span-4')]"
    )

    processed = set()

    while True:

        cards = left_panel.find_elements(
            By.XPATH,
            ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')]"
        )

        for card in cards:
            name = card.find_element(By.TAG_NAME, "p").text.strip()

            if name in processed:
                continue

            processed.add(name)

            safe_click(driver, card)
            time.sleep(1)

            wait.until(lambda d: d.find_elements(
                By.XPATH, "//p[contains(@class,'text-[32px]')]"
            ))

            print(f"✅ {name}")

        last_scroll = driver.execute_script("return arguments[0].scrollTop;", left_panel)
        driver.execute_script("arguments[0].scrollTop += 400;", left_panel)
        time.sleep(1)
        new_scroll = driver.execute_script("return arguments[0].scrollTop;", left_panel)

        if new_scroll == last_scroll:
            break

    print("🟢 Students Passed")


# ================= MAIN =================

def main():

    driver = make_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    try:
        print("\n🚀 MASTER TEST SUITE STARTED\n")

        login(driver, wait)
        apply_filters(driver, wait)

        test_overview(driver, wait)
        test_chapters(driver, wait)
        test_questions(driver, wait)
        test_students(driver, wait)

        print("\n🎉 EVERYTHING TESTED SUCCESSFULLY")

    except Exception as e:
        print("\n❌ TEST FAILED")
        print("Type:", type(e).__name__)
        print("Message:", str(e))
        traceback.print_exc()
        driver.save_screenshot("error.png")

    input("\nPress ENTER to close browser...")
    driver.quit()


if __name__ == "__main__":
    main()