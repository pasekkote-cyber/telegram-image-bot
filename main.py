# main.py
import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai

# === Получаем токены из переменных окружения ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# === Проверка обязательных переменных ===
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не задан")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY не задан")
if not RENDER_EXTERNAL_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL не задан")

# === Настройка Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === Хранилище чатов (в памяти) ===
user_chats = {}

# === Обработчик сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Создаём новый чат при первом сообщении
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    try:
        await update.message.reply_text("💬 Думаю...")
        response = user_chats[user_id].send_message(text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:150]}")

# === Настройка Telegram-бота ===
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Запуск в режиме webhook ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    
    print(f"🚀 Запуск на порту {port}")
    print(f"🔗 Webhook URL: {webhook_url}")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )
