import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
    opts = Options()
    opts.add_argument("--start-maximized")
    return webdriver.Chrome(options=opts)


# ================= HELPERS =================

def type_safely(el, text):
    el.click()
    time.sleep(0.2)
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.DELETE)
    el.send_keys(text)


def get_selects(driver):
    return driver.find_elements(By.TAG_NAME, "select")


def js_select_by_text(driver, select_el, wanted_text):
    script = """
    const sel = arguments[0];
    const want = arguments[1];

    function fire(el){
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
    }

    for (const opt of sel.options){
        if (opt.textContent.trim() === want){
            sel.value = opt.value;
            fire(sel);
            return true;
        }
    }
    return false;
    """
    return driver.execute_script(script, select_el, wanted_text)


def wait_selects_count(driver, min_count=6, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: len(get_selects(d)) >= min_count
    )


def wait_option_available(driver, select_index, wanted_text, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: wanted_text in [
            o.text.strip()
            for o in get_selects(d)[select_index].find_elements(By.TAG_NAME, "option")
        ]
    )


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


# ================= FORM FILL =================

def fill_form_cascading(driver, wait):
    wait_selects_count(driver)

    plan = [
        (0, "Class"),
        (1, "Section"),
        (2, "Subject"),
        (3, "Exam"),
        (4, "CompareLeft"),
        (5, "CompareRight"),
    ]

    # Select Class first
    if not js_select_by_text(driver, get_selects(driver)[0], VALUES["Class"]):
        raise RuntimeError("Class option not found")
    print("✅ Class selected")

    for idx, key in plan[1:]:
        wait_option_available(driver, idx, VALUES[key])
        if not js_select_by_text(driver, get_selects(driver)[idx], VALUES[key]):
            raise RuntimeError(f"{key} option not found")
        print(f"✅ {key} selected")
        time.sleep(0.5)

    # Click Enter
    old_url = driver.current_url
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Enter']"))
    ).click()

    wait.until(lambda d: d.current_url != old_url)
    print("✅ Enter clicked")


# ================= OVERVIEW VALIDATION =================

def validate_overview_page(driver, wait):

    print("\n🔎 Running Overview Tab Validations...\n")

    # Wait until Overview loads fully
    wait.until(lambda d: "Overview" in d.page_source)
    print("✅ TC_01 Page Loaded")

    # Wait for percentage to appear anywhere in page
    wait.until(lambda d: "%" in d.page_source)
    print("✅ TC_11 Percentage Found")

    # Validate Reteach section
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Reteach')]"))
    )
    print("✅ TC_21 Reteach section present")

    # Validate Brushup section
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Brushup')]"))
    )
    print("✅ TC_22 Brushup section present")

    # Validate On Track section
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'On Track')]"))
    )
    print("✅ TC_23 On Track section present")

    # Validate Highlighted Students
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Performing Well')]"))
    )
    print("✅ TC_31 Performing Well section present")

    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Weak')]"))
    )
    print("✅ TC_32 Weak section present")

    # Validate Tabs
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Chapters')]"))
    )
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Questions')]"))
    )
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Students')]"))
    )
    print("✅ TC_44 Tabs present")

    print("\n🟢 Overview Basic UI Tests Passed\n")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 40)

    try:
        print("🚀 Starting automation...")

        login(driver, wait)
        print("✅ Login OK")

        fill_form_cascading(driver, wait)
        print("✅ Filters Applied")

        validate_overview_page(driver, wait)

        print("🎉 Automation completed successfully")

        if KEEP_BROWSER_OPEN:
            input("👉 Press ENTER to close browser manually...")

        driver.quit()

    except Exception as e:
        print("\n❌ ERROR OCCURRED")
        print("Type:", type(e).__name__)
        print("Message:", str(e))
        driver.quit()

    finally:
        print("🏁 Script finished.")


if __name__ == "__main__":
    main()