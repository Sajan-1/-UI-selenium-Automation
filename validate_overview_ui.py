import time
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

USERNAME = "sajan"
PASSWORD = "Operations123"

VALUES = {
    "Class": "12",
    "Section": "M",
    "Subject": "MATHS",
    "Exam": "Midterm",
    "CompareLeft": "Midterm",
    "CompareRight": "Preboard 1",
}

KEEP_BROWSER_OPEN = True


# ================= DRIVER =================

def make_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


# ================= HELPERS =================

def type_safely(element, text):
    element.click()
    time.sleep(0.2)
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.DELETE)
    element.send_keys(text)


def get_selects(driver):
    return driver.find_elements(By.TAG_NAME, "select")


def js_select_by_text(driver, select_el, wanted_text):
    script = """
    const sel = arguments[0];
    const text = arguments[1].trim();
    for (let opt of sel.options){
        if (opt.text.trim() === text){
            sel.value = opt.value;
            sel.dispatchEvent(new Event('change', {bubbles:true}));
            return true;
        }
    }
    return false;
    """
    return driver.execute_script(script, select_el, wanted_text)


def wait_option_available(driver, index, text, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        selects = get_selects(driver)
        if len(selects) > index:
            options = driver.execute_script(
                "return Array.from(arguments[0].options).map(o=>o.text.trim());",
                selects[index]
            )
            if text in options:
                return True
        time.sleep(0.5)
    raise Exception(f"Option '{text}' not available")


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    username = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//input[@type='text' or @type='email']"))
    )
    password = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//input[@type='password']"))
    )

    type_safely(username, USERNAME)
    type_safely(password, PASSWORD)

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    ).click()

    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(.,'Enter your Class')]"))
    )

    print("✅ Login successful")


# ================= FORM FILL =================

def fill_form(driver, wait):
    wait.until(lambda d: len(get_selects(d)) >= 6)

    plan = [
        (0, "Class"),
        (1, "Section"),
        (2, "Subject"),
        (3, "Exam"),
        (4, "CompareLeft"),
        (5, "CompareRight"),
    ]

    for index, key in plan:
        wait_option_available(driver, index, VALUES[key])
        js_select_by_text(driver, get_selects(driver)[index], VALUES[key])
        time.sleep(0.5)
        print(f"✅ {key} selected")

    old_url = driver.current_url

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Enter']"))
    ).click()

    wait.until(lambda d: d.current_url != old_url)

    print("✅ Enter clicked")
    print("🌐 Current URL:", driver.current_url)


# ================= UI VALIDATION =================

def validate_overview_ui(driver, wait):
    print("🔍 Validating Overview Page...")

    # Wait for page load using stable text
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Overview of Section')]")
        )
    )

    # Validate tabs
    for tab in ["Overview", "Chapters", "Questions", "Students"]:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(),'{tab}')]")
            )
        )
    print("✅ Tabs present")

    # Validate comparison card
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Class Average')]")
        )
    )
    print("✅ Comparison card present")

    # Validate chapter categories
    for category in ["Reteach", "Brushup", "On Track"]:
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(text(),'{category}')]")
            )
        )
    print("✅ Chapter categories present")

    # Validate no horizontal scroll
    scroll_width = driver.execute_script("return document.body.scrollWidth")
    client_width = driver.execute_script("return document.body.clientWidth")

    if scroll_width > client_width:
        raise Exception("Horizontal scroll detected")

    print("✅ No horizontal scroll")
    print("🟢 UI Validation Successful")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🚀 Starting Automation...")

        login(driver, wait)
        fill_form(driver, wait)
        validate_overview_ui(driver, wait)

        print("🎉 ALL TESTS PASSED")

        if KEEP_BROWSER_OPEN:
            input("👉 Press ENTER to close browser...")

        driver.quit()

    except Exception as e:
        print("\n❌ TEST FAILED")
        print("Type:", type(e).__name__)
        print("Message:", str(e))
        driver.save_screenshot("error.png")
        print("📸 Screenshot saved as error.png")
        driver.quit()

    finally:
        print("🏁 Script Finished")


if __name__ == "__main__":
    main()
    