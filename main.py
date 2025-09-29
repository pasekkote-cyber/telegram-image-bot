# main.py
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
from PIL import Image

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
PORT = int(os.environ.get("PORT", 8443))  # Render использует PORT

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    prompt = update.message.text
    try:
        await update.message.reply_text("🎨 Генерирую... (20–60 сек)")
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt},
            timeout=60
        )
        print(f"[HF] Status: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"HF error {response.status_code}")
        
        image = Image.open(BytesIO(response.content))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio)
    except Exception as e:
        print(f"[ERROR] {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:150]}")

# Создаём Application
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

# Запуск
if __name__ == "__main__":
    # Получаем URL для webhook из Render
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        print(f"Setting webhook to: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            secret_token=None  # можно добавить для безопасности
        )
    else:
        # Fallback на polling (не для Render)
        app.run_polling()
