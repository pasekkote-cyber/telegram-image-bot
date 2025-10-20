# main.py
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
from PIL import Image
import google.generativeai as genai

# === Настройки ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # ← НОВАЯ переменная!
PORT = int(os.environ.get("PORT", 8443))

if not TELEGRAM_TOKEN or not HF_API_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN, HF_API_TOKEN или GEMINI_API_KEY")

# === Настройка Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
# Создаём модель с поддержкой чата
model = genai.GenerativeModel("gemini-1.5-flash")  # или "gemini-1.0-pro"

# Хранилище чатов (в памяти)
user_chats = {}

# === Генерация изображения (Hugging Face) ===
async def generate_image_from_prompt(update: Update, prompt: str):
    try:
        await update.message.reply_text("🎨 Генерирую изображение...")
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt},
            timeout=60
        )
        if response.status_code != 200:
            raise Exception(f"HF error {response.status_code}")
        image = Image.open(BytesIO(response.content))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        await update.message.reply_photo(photo=bio)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка генерации: {str(e)[:150]}")

# === Обработка текстовых сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Команда для генерации изображения
    if text.startswith("/img "):
        return await generate_image_from_prompt(update, text[5:].strip())

    # Диалог с Gemini
    try:
        await update.message.reply_text("💬 Думаю...")
        
        # Создаём чат при первом обращении
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
        
        # Отправляем сообщение
        response = user_chats[user_id].send_message(text)
        reply = response.text
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка Gemini: {str(e)[:150]}")

# === Запуск бота ===
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url
        )
    else:
        app.run_polling()
