# main.py
from flask import Flask
import os

# Проверка токенов (без импорта telegram!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask + токены OK!"

@app.route("/setwebhook")
def set_webhook():
    return "🛠 Webhook setup (токены загружены)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
