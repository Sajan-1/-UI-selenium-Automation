import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ================= CONFIG =================

LOGIN_URL = "https://classlens.inferentics.com/login"
USERNAME = "sajan"
PASSWORD = "Operations123"
DROPDOWN_VALUES = ["12", "M", "MATHS", "Midterm", "Midterm", "Preboard 1"]


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='text']"))).send_keys(USERNAME)
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Enter your Class')]")))
    print("✅ Login successful")


# ================= FORM =================

def fill_form(driver, wait):
    wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 6)

    for i in range(6):
        wait.until(lambda d: DROPDOWN_VALUES[i] in [
            opt.text.strip()
            for opt in d.find_elements(By.TAG_NAME, "select")[i]
            .find_elements(By.TAG_NAME, "option")
        ])

        selects = driver.find_elements(By.TAG_NAME, "select")

        for option in selects[i].find_elements(By.TAG_NAME, "option"):
            if option.text.strip() == DROPDOWN_VALUES[i]:
                option.click()
                break

        time.sleep(1)

    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Chapters']")))
    print("✅ Dashboard loaded")


# ================= OPEN CHAPTER TAB =================

def open_chapters_tab(driver, wait):
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Chapters']"))
    ).click()

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Select a chapter')]")
        )
    )

    print("✅ Chapters page opened")


# ================= VALIDATE RIGHT PANEL =================

def validate_right_panel(driver, wait, chapter_name):

    print(f"🔍 Validating right panel for: {chapter_name}")

    # Wait for title to update
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, f"//*[contains(text(),'{chapter_name}')]")
        )
    )

    # Validate change percentage badge
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'%')]")
        )
    )

    # Validate improvement/decline section
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Why this chapter')]")
        )
    )

    # Validate Midterm card
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Midterm')]")
        )
    )

    # Validate Preboard card
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Preboard')]")
        )
    )

    # Validate Struggling students
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Struggling students')]")
        )
    )

    # Validate Weakest Concepts
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Weakest Concepts')]")
        )
    )

    # Validate Strongest Concepts
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Strongest Concepts')]")
        )
    )

    # Validate Remediation Plan
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Remediation Plan')]")
        )
    )

    print(f"✅ {chapter_name} RIGHT PANEL PASSED")


# ================= RUN CHAPTER TESTS =================

def run_all_chapter_tests(driver, wait):

    print("\n🔎 Running chapter validations...\n")

    chapter_locator = "//*[contains(text(),'%')]/ancestor::div[1]"

    chapters = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, chapter_locator))
    )

    total = len(chapters)
    print(f"📌 Found {total} chapters")

    for i in range(total):

        chapters = driver.find_elements(By.XPATH, chapter_locator)
        chapter = chapters[i]

        chapter_name = chapter.text.split("\n")[0]
        print(f"\n➡ Testing: {chapter_name}")

        driver.execute_script("arguments[0].scrollIntoView(true);", chapter)
        driver.execute_script("arguments[0].click();", chapter)

        validate_right_panel(driver, wait, chapter_name)

        time.sleep(1)

    print("\n🟢 ALL CHAPTER TEST CASES PASSED SUCCESSFULLY")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 30)

    try:
        login(driver, wait)
        fill_form(driver, wait)
        open_chapters_tab(driver, wait)
        run_all_chapter_tests(driver, wait)

        input("\nPress ENTER to close browser...")

    except Exception as e:
        print("\n❌ ERROR:", str(e))

    finally:
        driver.quit()


if __name__ == "__main__":
    main()