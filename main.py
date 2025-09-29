# main.py
from flask import Flask
import os

# Проверка токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

# Попробуем импортировать библиотеки
try:
    from telegram import Bot
    import requests
    from io import BytesIO
    from PIL import Image
    LIBRARIES_OK = True
except Exception as e:
    LIBRARIES_OK = False
    IMPORT_ERROR = str(e)

app = Flask(__name__)

@app.route("/")
def home():
    if LIBRARIES_OK:
        return "✅ Flask + токены + библиотеки OK!"
    else:
        return f"❌ Ошибка импорта: {IMPORT_ERROR}"

@app.route("/setwebhook")
def set_webhook():
    return "🛠 Webhook (библиотеки загружены)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
