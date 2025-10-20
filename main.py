# main.py
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# === Настройки ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 8443))

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или GEMINI_API_KEY")

# === Настройка Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Хранилище чатов (в памяти)
user_chats = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    try:
        await update.message.reply_text("💬 Думаю...")
        
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
        
        response = user_chats[user_id].send_message(text)
        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:150]}")

# === Запуск ===
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
