import requests
import json
import time
from datetime import datetime

# ==============================
# CONFIG
# ==============================
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"

# Store conversation history
chat_history = []

# ==============================
# HELPER: TIMESTAMP
# ==============================
def timestamp():
    return datetime.now().strftime("%H:%M:%S")


# ==============================
# CALL LOCAL AI
# ==============================
def call_ai():
    global chat_history

    payload = {
        "model": MODEL,
        "messages": chat_history,
        "stream": False
    }

    retry_count = 0

    while True:
        try:
            response = requests.post(OLLAMA_URL, json=payload)

            if response.status_code == 200:
                return response.json()

            else:
                print(f"[{timestamp()}] ❌ Error {response.status_code}: {response.text}")
                time.sleep(2)

        except Exception as e:
            print(f"[{timestamp()}] ⚠️ Exception: {e}")
            retry_count += 1
            time.sleep(2 + retry_count)


# ==============================
# MAIN CHAT LOOP
# ==============================
def run_chat():
    print("🚀 Local AI Chat Started (Unlimited / No API Key)\n")

    while True:
        try:
            user_input = input("💬 You: ")

            if user_input.lower() == "exit":
                print("👋 Exiting...")
                break

            # Add user message
            chat_history.append({
                "role": "user",
                "content": user_input
            })

            print(f"[{timestamp()}] ⏳ Thinking...\n")

            result = call_ai()

            if result:
                try:
                    ai_reply = result["message"]["content"]
                except:
                    ai_reply = json.dumps(result, indent=2)

                # Save AI response
                chat_history.append({
                    "role": "assistant",
                    "content": ai_reply
                })

                print(f"🤖 AI:\n{ai_reply}")
                print("-" * 60)

        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    run_chat()