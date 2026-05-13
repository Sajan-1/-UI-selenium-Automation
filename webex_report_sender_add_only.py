# ================== WEBEX REPORT SENDER - ADD ONLY ==================
# Paste this block at the BOTTOM of testes.py. Do not remove any existing line.
# Set these environment variables in Windows before scheduled/manual run:
#   WEBEX_BOT_TOKEN = your bot token
#   WEBEX_ROOM_ID   = your Webex room ID

import os
import json
import requests
from datetime import datetime

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "").strip()
WEBEX_ROOM_ID = os.getenv("WEBEX_ROOM_ID", "").strip()


def _webex_send_message(markdown_text):
    if not WEBEX_BOT_TOKEN or not WEBEX_ROOM_ID:
        print("[WEBEX] Skipped: WEBEX_BOT_TOKEN or WEBEX_ROOM_ID is not set.")
        return False

    try:
        response = requests.post(
            "https://webexapis.com/v1/messages",
            headers={
                "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "roomId": WEBEX_ROOM_ID,
                "markdown": markdown_text,
            },
            timeout=30,
        )
        print("[WEBEX] Status:", response.status_code)
        print("[WEBEX] Response:", response.text[:500])
        return 200 <= response.status_code < 300
    except Exception as exc:
        print("[WEBEX] Send failed:", exc)
        return False


def _classlens_find_master_report():
    candidates = [
        os.path.join("combined_preserved_sources", "classlens_MASTER_ALL_TABS_REPORT.html"),
        os.path.join("combined_preserved_sources", "classlens_all_sections_master_report_v13.html"),
        os.path.join("combined_preserved_sources", "classlens_full_report_v13.html"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return ""


def _classlens_find_failed_summary():
    candidates = [
        os.path.join("combined_preserved_sources", "classlens_FAILED_CASES_CHAT_SUMMARY.txt"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read().strip()
            except Exception:
                pass
    return ""


def send_classlens_final_report_to_webex():
    report_path = _classlens_find_master_report()
    failed_summary = _classlens_find_failed_summary()

    if failed_summary:
        status_line = "❌ **ClassLens Daily Selenium Test Completed — Failed cases detected**"
        details = failed_summary[:2500]
    else:
        status_line = "✅ **ClassLens Daily Selenium Test Completed**"
        details = "No failed-cases summary file was found. Check the master HTML report for complete results."

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_line = f"`{report_path}`" if report_path else "Master report file not found."

    message = (
        f"{status_line}\n\n"
        f"**Run time:** `{now}`\n\n"
        f"**Master report:**\n{report_line}\n\n"
        f"**Summary:**\n{details}"
    )
    _webex_send_message(message)


send_classlens_final_report_to_webex()
# ================== END WEBEX REPORT SENDER - ADD ONLY ==================
