# main.py
from flask import Flask, request, jsonify
import os
from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
from PIL import Image
import threading

# === Настройки ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TELEGRAM_TOKEN or not HF_API_TOKEN or not RENDER_EXTERNAL_URL:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN, HF_API_TOKEN или RENDER_EXTERNAL_URL")

# === Инициализация Application ===
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === Обработчик генерации изображений ===
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    prompt = update.message.text
    try:
        await update.message.reply_text("🎨 Генерирую изображение... (20–60 сек)")
        
        # Запрос к Hugging Face
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt},
            timeout=60
        )
        
        # Логируем для отладки
        print(f"[HF] Status: {response.status_code}")
        if response.status_code != 200:
            error_detail = response.text[:300]
            print(f"[HF] Error: {error_detail}")
            raise Exception(f"HF error {response.status_code}")

        # Обработка изображения
        image = Image.open(BytesIO(response.content))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio)

    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)[:150]}"
        print(f"[BOT ERROR] {error_msg}")
        try:
            await update.message.reply_text(error_msg)
        except:
            pass

# Добавляем обработчик
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

# === Flask-приложение ===
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Image Bot is running!"

@app.route("/setwebhook")
def set_webhook():
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot = Bot(token=TELEGRAM_TOKEN)
    import asyncio
    success = asyncio.run(bot.set_webhook(url=webhook_url))
    return f"✅ Webhook установлен: {success}<br>URL: {webhook_url}"

# Запуск обработки обновлений в фоне
def start_app():
    application.run_polling()

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_
        update = Update.de_json(json_data, application.bot)
        application.update_queue.put(update)
    return jsonify({"ok": True})

# Запускаем фоновый поток
thread = threading.Thread(target=start_app)
thread.daemon = True
thread.start()

# === Запуск Flask ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
