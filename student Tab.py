import json
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
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

OUTFILE = "students_details.json"
RIGHT_PANEL_WAIT = 2


# ================= DRIVER =================

def make_driver():
    opts = Options()
    opts.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(60)
    return driver


# ================= HELPERS =================

def compute_change(mid, pre):
    try:
        m = float(re.findall(r"-?\d+\.?\d*", mid)[0])
        p = float(re.findall(r"-?\d+\.?\d*", pre)[0])
        diff = round(p - m, 1)
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff}%"
    except:
        return "NA"


# ================= LOGIN =================

def login(driver, wait):
    driver.get(LOGIN_URL)

    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='text']"))).send_keys(USERNAME)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@type='password']"))).send_keys(PASSWORD)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Enter your Class')]")))
    print("✅ Login OK")


# ================= DROPDOWN =================

def select_dropdown(driver, wait, label_text, value):
    label = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//label[contains(text(),'{label_text}')]"))
    )
    select = label.find_element(By.XPATH, "./following::select[1]")

    driver.execute_script("""
        const sel = arguments[0];
        const val = arguments[1];
        for (const opt of sel.options){
            if (opt.text.trim() === val){
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change', {bubbles:true}));
            }
        }
    """, select, value)

    time.sleep(1)


def fill_form(driver, wait):
    select_dropdown(driver, wait, "Class", VALUES["Class"])
    select_dropdown(driver, wait, "Section", VALUES["Section"])
    select_dropdown(driver, wait, "Subject", VALUES["Subject"])
    select_dropdown(driver, wait, "Exam", VALUES["Exam"])

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Enter']"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Overview')]")))
    print("✅ Filters selected")


# ================= NAVIGATION =================

def go_to_students_tab(driver, wait):
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Students']"))).click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Your Students']")))
    time.sleep(2)
    print("✅ Navigated to Students tab")


# ================= EXAM EXTRACTION =================

def extract_exam_data(driver, exam_name):
    try:
        card = driver.find_element(
            By.XPATH,
            f"//p[normalize-space()='{exam_name}']/ancestor::div[contains(@class,'rounded-2xl')]"
        )

        percent = card.find_element(By.XPATH, ".//p[contains(@class,'text-5xl')]").text.strip()
        marks = card.find_element(By.XPATH, ".//p[contains(text(),'/')]").text.strip()

        return {
            "exists": True,
            "percent": percent,
            "marks": marks
        }

    except:
        return {
            "exists": False,
            "percent": "NA",
            "marks": "NA"
        }


# ================= RIGHT PANEL VALIDATION =================

def validate_right_panel(driver, student_name):

    result = {
        "student_name_displayed": None,
        "change_displayed": "NA",
        "midterm": {},
        "preboard": {},
        "test_pass": True
    }

    try:
        name_display = driver.find_element(
            By.XPATH, "//p[contains(@class,'text-[32px]')]"
        ).text.strip()

        result["student_name_displayed"] = name_display

        if name_display != student_name:
            result["test_pass"] = False

    except:
        result["test_pass"] = False

    try:
        change = driver.find_element(
            By.XPATH, "//div[contains(@class,'text-2xl') and contains(text(),'%')]"
        ).text.strip()
        result["change_displayed"] = change
    except:
        result["change_displayed"] = "NA"

    result["midterm"] = extract_exam_data(driver, "Midterm")
    result["preboard"] = extract_exam_data(driver, "Preboard 1")

    return result


# ================= STUDENT PROCESS =================

def process_students(driver):

    results = []
    processed = set()

    left_container = driver.find_element(
        By.XPATH, "//div[contains(@class,'col-span-4')]"
    )

    time.sleep(2)

    while True:

        cards = left_container.find_elements(
            By.XPATH,
            ".//div[contains(@class,'cursor-pointer') and contains(@class,'rounded-2xl')]"
        )

        for card in cards:
            name = card.find_element(By.TAG_NAME, "p").text.strip()

            if name in processed:
                continue

            processed.add(name)

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
            time.sleep(0.5)
            card.click()
            time.sleep(RIGHT_PANEL_WAIT)

            panel = validate_right_panel(driver, name)

            mid_pct = panel["midterm"]["percent"]
            mid_marks = panel["midterm"]["marks"]
            pre_pct = panel["preboard"]["percent"]
            pre_marks = panel["preboard"]["marks"]

            # ✅ Correct NA logic
            if mid_pct == "NA" or pre_pct == "NA":
                change_calc = "NA"
            else:
                change_calc = compute_change(mid_pct, pre_pct)

            print(
                f"{'✅ PASS' if panel['test_pass'] else '❌ FAIL'} | {name} | "
                f"Midterm: {mid_pct} {mid_marks} | "
                f"Preboard1: {pre_pct} {pre_marks} | "
                f"Change UI: {panel['change_displayed']} | "
                f"Change Calc: {change_calc}"
            )

            results.append({
                "name": name,
                "midterm_percent": mid_pct,
                "midterm_marks": mid_marks,
                "preboard_percent": pre_pct,
                "preboard_marks": pre_marks,
                "change_displayed": panel["change_displayed"],
                "change_calculated": change_calc,
                "test_pass": panel["test_pass"]
            })

        last_scroll = driver.execute_script("return arguments[0].scrollTop;", left_container)
        driver.execute_script("arguments[0].scrollTop += 400;", left_container)
        time.sleep(1)
        new_scroll = driver.execute_script("return arguments[0].scrollTop;", left_container)

        if new_scroll == last_scroll:
            break

    return results


# ================= MAIN =================

def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 30)

    try:
        login(driver, wait)
        fill_form(driver, wait)
        go_to_students_tab(driver, wait)

        data = process_students(driver)

        with open(OUTFILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"\n✅ Saved {len(data)} students")
        print("🟢 Script completed successfully.")

    except Exception as e:
        print("\n❌ ERROR OCCURRED:")
        print(e)
        print("🔵 Browser kept open for debugging.")

    input("\nPress ENTER to close browser manually...")
    driver.quit()


if __name__ == "__main__":
    main()