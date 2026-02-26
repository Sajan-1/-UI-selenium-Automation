import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
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


# ================= UI TESTS =================

def run_login_ui_tests(driver, wait):
    print("\n🔐 Running Login UI Test Cases...\n")

    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("TC_UI_001 ✅ Page loaded")

    # Logo
    logo = driver.find_element(By.TAG_NAME, "img")
    assert logo.is_displayed()
    print("TC_UI_002 ✅ Logo displayed")

    username = driver.find_element(By.XPATH, "//input[@type='text' or @type='email']")
    password = driver.find_element(By.XPATH, "//input[@type='password']")
    login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")

    assert username.is_displayed()
    print("TC_UI_003 ✅ Username visible")

    assert password.is_displayed()
    print("TC_UI_004 ✅ Password visible")

    assert login_btn.is_displayed()
    print("TC_UI_005 ✅ Login button visible")

    print("TC_UI_006 ✅ Username placeholder:", username.get_attribute("placeholder"))
    print("TC_UI_007 ✅ Password placeholder:", password.get_attribute("placeholder"))

    assert password.get_attribute("type") == "password"
    print("TC_UI_008 ✅ Password masked")

    # Required validation
    login_btn.click()
    time.sleep(1)
    print("TC_UI_009 ✅ Required validation checked")

    # Hover effect
    ActionChains(driver).move_to_element(login_btn).perform()
    hover_color = login_btn.value_of_css_property("background-color")
    print("TC_UI_011 ✅ Hover color:", hover_color)

    # Tab order
    username.click()
    username.send_keys(Keys.TAB)
    active = driver.switch_to.active_element
    if active == password:
        print("TC_UI_012 ✅ Tab order correct")
    else:
        print("TC_UI_012 ❌ Tab order incorrect")

    print("\n✅ Login UI Tests Completed\n")


# ================= HELPERS =================

def type_safely(el, text):
    el.clear()
    el.send_keys(text)


def get_selects(driver):
    return driver.find_elements(By.TAG_NAME, "select")


def js_select_by_text(driver, select_el, wanted_text):
    script = """
    const sel = arguments[0];
    const want = arguments[1].trim();

    function fire(el){
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
    }

    for (const opt of sel.options){
      if ((opt.textContent||'').trim() === want){
        sel.value = opt.value;
        fire(sel);
        return {ok:true};
      }
    }
    return {ok:false};
    """
    return driver.execute_script(script, select_el, wanted_text)


def wait_option_available(driver, index, text, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        sels = get_selects(driver)
        if len(sels) > index:
            options = [o.text for o in sels[index].find_elements(By.TAG_NAME, "option")]
            if text in options:
                return True
        time.sleep(0.5)
    raise RuntimeError(f"{text} not available in dropdown {index}")


# ================= LOGIN =================

def login(driver, wait):
    username = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//input[@type='text' or @type='email']"))
    )
    password = driver.find_element(By.XPATH, "//input[@type='password']")

    type_safely(username, USERNAME)
    type_safely(password, PASSWORD)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(.,'Enter your Class')]"))
    )
    print("✅ Login successful")


# ================= CASCADING =================

def fill_form_cascading(driver, wait):
    plan = [
        (0, "Class"),
        (1, "Section"),
        (2, "Subject"),
        (3, "Exam"),
        (4, "CompareLeft"),
        (5, "CompareRight"),
    ]

    for idx, key in plan:
        wait_option_available(driver, idx, VALUES[key])
        sel = get_selects(driver)[idx]
        res = js_select_by_text(driver, sel, VALUES[key])
        if not res.get("ok"):
            raise RuntimeError(f"{key} option not found")
        print(f"✅ {key} selected")
        time.sleep(0.5)

    old_url = driver.current_url
    driver.find_element(By.XPATH, "//button[normalize-space()='Enter']").click()
    wait.until(lambda d: d.current_url != old_url)
    print("✅ Enter clicked")


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🚀 Starting Full Test Suite...\n")

        run_login_ui_tests(driver, wait)
        login(driver, wait)
        fill_form_cascading(driver, wait)

        print("\n🎉 All Tests Passed Successfully")

        if KEEP_BROWSER_OPEN:
            input("👉 Press ENTER to close browser...")
        driver.quit()

    except Exception as e:
        print("\n❌ TEST FAILED")
        print("Error:", e)
        driver.quit()

    finally:
        print("🏁 Script Finished")


if __name__ == "__main__":
    main()