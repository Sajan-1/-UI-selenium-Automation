import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


LOGIN_URL = "https://classlens.inferentics.com/login"

USERNAME = "sajan"
PASSWORD = "Operations123"

VALUES = {
    "Class": "12",
    "Section": "Q",
    "Subject": "MATHS",
    "Exam": "Preboard 1"
}


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_experimental_option("detach", True)  # Optional extra safety
    return webdriver.Chrome(options=options)


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='text' or @type='email']")
    )).send_keys(USERNAME)

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//input[@type='password']")
    )).send_keys(PASSWORD)

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@type='submit']")
    )).click()

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "select")))
    print("✅ Login successful")


# ================= FILL FORM (React Safe) =================

def fill_form(driver, wait):

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//label[text()='Class']/following::select[1]")
    ))

    Select(driver.find_element(
        By.XPATH, "//label[text()='Class']/following::select[1]"
    )).select_by_visible_text(VALUES["Class"])

    time.sleep(1)

    Select(driver.find_element(
        By.XPATH, "//label[text()='Section']/following::select[1]"
    )).select_by_visible_text(VALUES["Section"])

    time.sleep(1)

    Select(driver.find_element(
        By.XPATH, "//label[text()='Subject']/following::select[1]"
    )).select_by_visible_text(VALUES["Subject"])

    time.sleep(1)

    Select(driver.find_element(
        By.XPATH, "//label[text()='Exam']/following::select[1]"
    )).select_by_visible_text(VALUES["Exam"])

    time.sleep(1)

    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[normalize-space()='Enter']")
    )).click()

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//div[text()='Questions']")
    ))

    print("✅ Form submitted successfully")


# ================= OPEN QUESTIONS TAB =================

def open_questions_tab(driver, wait):

    tab = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[normalize-space()='Questions']")
    ))
    tab.click()

    time.sleep(2)
    print("✅ Questions tab opened")


# ================= VALIDATE RIGHT PANEL =================

def validate_right_panel(wait):

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//span[text()='Chapter']")
    ))

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//span[text()='Concepts']")
    ))

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//span[text()='Marks']")
    ))

    wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//*[contains(text(),'Average')]")
    ))


# ================= TEST ALL QUESTIONS =================

def test_all_questions(driver, wait):

    question_locator = (
        By.XPATH,
        "//div[contains(@class,'cursor-pointer') and .//span[starts-with(text(),'Q')]]"
    )

    wait.until(EC.presence_of_all_elements_located(question_locator))

    total = len(driver.find_elements(*question_locator))
    print(f"\n🔹 Found {total} questions")

    for i in range(total):

        questions = driver.find_elements(*question_locator)
        question_card = questions[i]

        q_text = question_card.find_element(
            By.XPATH, ".//span[starts-with(text(),'Q')]"
        ).text

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            question_card
        )

        time.sleep(1)

        driver.execute_script("arguments[0].click();", question_card)

        print(f"\n➡ Testing {q_text}")

        validate_right_panel(wait)

        print(f"   ✅ {q_text} Passed")

    print("\n🟢 ALL QUESTIONS VALIDATED SUCCESSFULLY")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 30)

    try:
        login(driver, wait)
        fill_form(driver, wait)
        open_questions_tab(driver, wait)
        test_all_questions(driver, wait)

        print("\n🎉 COMPLETE AUTOMATION PASSED")
        print("Browser will remain open. Close it manually when done.")

        # Keep script alive forever
        while True:
            time.sleep(60)

    except TimeoutException as e:
        print("❌ Timeout Error:", e)
        print("Browser kept open for debugging.")

        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()