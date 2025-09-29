# main.py
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
import os
from io import BytesIO
from PIL import Image

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render сам даёт этот URL

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

app = Flask(__name__)
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

def query_hf(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"HF error {response.status_code}")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    prompt = update.message.text
    await update.message.reply_text("🎨 Генерирую... (20–60 сек)")
    try:
        image_bytes = query_hf({"inputs": prompt})
        image = Image.open(BytesIO(image_bytes))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:150]}")

bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

# Устанавливаем webhook при старте
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, bot_app.bot)
    bot_app.update_queue.put(update)
    return jsonify({"ok": True})

@app.route("/setwebhook")
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/webhook"
    result = bot_app.bot.set_webhook(url=webhook_url)
    return f"Webhook set: {result}, URL: {webhook_url}"

@app.route("/")
def home():
    return "✅ Telegram Image Bot (webhook mode) is running!"

# Запускаем бота в фоне
if __name__ == "__main__":
    # Запускаем без polling — только webhook
    bot_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL', '')}/webhook"
    )
