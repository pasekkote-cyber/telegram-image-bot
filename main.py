# main.py
import os
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
from PIL import Image

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
PORT = int(os.environ.get("PORT", 8443))

if not TELEGRAM_TOKEN or not HF_API_TOKEN:
    raise ValueError("❌ Не заданы TELEGRAM_TOKEN или HF_API_TOKEN")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    prompt = update.message.text
    user_id = update.effective_user.id
    
    try:
        logger.info(f"User {user_id} requested: {prompt}")
        await update.message.reply_text("🎨 Генерирую изображение... (это займет 20-60 секунд)")
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt},
            timeout=120  # Увеличиваем таймаут
        )
        
        logger.info(f"HF API response status: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error')
            raise Exception(f"HuggingFace API error: {error_msg}")
        
        image = Image.open(BytesIO(response.content))
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        
        await update.message.reply_photo(photo=bio, caption=f"🎨 Сгенерировано по запросу: '{prompt}'")
        logger.info(f"Image sent to user {user_id}")
        
    except requests.exceptions.Timeout:
        error_msg = "❌ Превышено время ожидания генерации изображения. Попробуйте позже."
        await update.message.reply_text(error_msg)
        logger.error(f"Timeout for user {user_id}")
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        await update.message.reply_text(error_msg[:1000])  # Ограничиваем длину сообщения
        logger.error(f"Error for user {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для генерации изображений.\n"
        "Просто отправь мне текстовое описание того, что хочешь увидеть!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    # Создаём Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("start"), start))
    app.add_error_handler(error_handler)
    
    # Запуск на Render
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    
    if RENDER_EXTERNAL_URL:
        # Webhook режим для Render
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        logger.info(f"Starting webhook on port {PORT} with URL: {webhook_url}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            url_path="/webhook",  # Добавляем путь
            secret_token=None
        )
    else:
        # Polling режим для локальной разработки
        logger.info("Starting polling...")
        app.run_polling()

if __name__ == "__main__":
    main()
