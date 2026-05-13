from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import webbrowser
import os

URL = "https://classlens.inferentics.com"
USERNAME = "sajan"
PASSWORD = "Operations123"

REPORT_FILE = "login_report.html"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

status = "FAIL"
reason = ""

try:
    print("🚀 Opening Login Page...")
    driver.get(URL)

    username_input = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='text']"))
    )

    password_input = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
    )

    print("✍️ Entering credentials...")
    username_input.clear()
    username_input.send_keys(USERNAME)

    password_input.clear()
    password_input.send_keys(PASSWORD)

    login_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
    )

    print("🔐 Clicking login...")
    login_button.click()

    time.sleep(4)

    # Validation
    if "dashboard" in driver.current_url.lower() or "overview" in driver.page_source.lower():
        status = "PASS"
        reason = "Login successful"
        print("✅ TEST PASSED")
    else:
        status = "FAIL"
        reason = "Dashboard not detected"
        print("❌ TEST FAILED")

except Exception as e:
    status = "FAIL"
    reason = str(e)
    print("❌ ERROR:", reason)

finally:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ===== HTML REPORT =====
    html_content = f"""
    <html>
    <head>
        <title>Login Test Report</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            .pass {{ color: green; font-weight: bold; }}
            .fail {{ color: red; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 50%; }}
            td, th {{ border: 1px solid #ddd; padding: 10px; }}
        </style>
    </head>
    <body>
        <h2>Login Test Report</h2>
        <table>
            <tr><th>Timestamp</th><td>{timestamp}</td></tr>
            <tr><th>URL</th><td>{URL}</td></tr>
            <tr><th>Username</th><td>{USERNAME}</td></tr>
            <tr><th>Status</th>
                <td class="{ 'pass' if status=='PASS' else 'fail' }">{status}</td></tr>
            <tr><th>Reason</th><td>{reason}</td></tr>
        </table>
    </body>
    </html>
    """

    with open(REPORT_FILE, "w") as f:
        f.write(html_content)

    print(f"📄 Report saved: {REPORT_FILE}")

    # ===== AUTO OPEN IN BROWSER =====
    file_path = os.path.abspath(REPORT_FILE)
    webbrowser.open("file://" + file_path)

    time.sleep(2)
    driver.quit()