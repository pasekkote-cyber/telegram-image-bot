# main.py
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
import os
import asyncio
import base64
from io import BytesIO
from PIL import Image

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

# URL модели Stable Diffusion на Hugging Face
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

app = Flask(__name__)
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

def query_hf(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"HF error {response.status_code}: {response.text}")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🎨 Генерирую изображение... (может занять 20–40 сек)")

    try:
        image_bytes = query_hf({"inputs": prompt})
        image = Image.open(BytesIO(image_bytes))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")

bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

# Запуск бота при первом запросе (или сразу)
import threading

bot_started = False

def start_bot():
    def run_bot():
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot_app.run_polling()
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

@app.before_request
def ensure_bot_started():
    global bot_started
    if not bot_started:
        start_bot()
        bot_started = True

@app.route("/")
def home():
    return "Telegram + Stable Diffusion (Hugging Face) Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 500
