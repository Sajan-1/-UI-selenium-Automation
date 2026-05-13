# -*- coding: utf-8 -*-
"""
Get Webex Room ID for the Selenium automation report space.

Usage in PowerShell:
  $env:WEBEX_BOT_TOKEN="PASTE_YOUR_BOT_ACCESS_TOKEN_HERE"
  python get_room_id_webex.py

Then copy the ROOM ID printed for your Webex space.
"""

import os
import sys
import requests

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN", "").strip()

if not WEBEX_BOT_TOKEN:
    print("ERROR: WEBEX_BOT_TOKEN is not set.")
    print('PowerShell example:')
    print('$env:WEBEX_BOT_TOKEN="PASTE_YOUR_BOT_ACCESS_TOKEN_HERE"')
    print('python get_room_id_webex.py')
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
    "Content-Type": "application/json",
}

response = requests.get("https://webexapis.com/v1/rooms", headers=headers, timeout=30)

print("Status:", response.status_code)

try:
    data = response.json()
except Exception:
    print(response.text)
    sys.exit(1)

if response.status_code != 200:
    print(data)
    sys.exit(1)

rooms = data.get("items", [])

if not rooms:
    print("No rooms found. Make sure the bot is added to your Webex space.")
    sys.exit(0)

print("\n===== WEBEX ROOMS FOUND =====\n")
for room in rooms:
    print("NAME   :", room.get("title", ""))
    print("ROOM ID:", room.get("id", ""))
    print("-" * 80)
