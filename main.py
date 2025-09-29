# main.py
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO
from PIL import Image
import json

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
        
        # Добавляем повторные попытки
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
                    headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                    json={"inputs": prompt},
                    timeout=120
                )
                
                logger.info(f"HF API response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Успешный ответ
                    image = Image.open(BytesIO(response.content))
                    bio = BytesIO()
                    bio.name = 'image.png'
                    image.save(bio, 'PNG')
                    bio.seek(0)
                    
                    await update.message.reply_photo(photo=bio, caption=f"🎨 Сгенерировано по запросу: '{prompt}'")
                    logger.info(f"Image sent to user {user_id}")
                    return
                    
                elif response.status_code == 503:
                    # Модель загружается
                    if attempt < max_retries - 1:
                        wait_time = 30 * (attempt + 1)  # Увеличиваем время ожидания
                        logger.info(f"Model is loading, waiting {wait_time} seconds...")
                        await update.message.reply_text(f"⏳ Модель загружается... Жду {wait_time} секунд")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise Exception("Модель все еще загружается. Попробуйте позже.")
                
                else:
                    # Другие ошибки API
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Unknown error')
                    except:
                        error_msg = response.text[:500] if response.text else 'Empty response'
                    
                    raise Exception(f"HuggingFace API error {response.status_code}: {error_msg}")
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    await update.message.reply_text("⏳ Таймаут, пробую снова...")
                    continue
                else:
                    raise Exception("Превышено время ожидания генерации после нескольких попыток")
        
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        # Обрезаем сообщение для Telegram
        if len(error_msg) > 1000:
            error_msg = error_msg[:1000] + "..."
        await update.message.reply_text(error_msg)
        logger.error(f"Error for user {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для генерации изображений.\n"
        "Просто отправь мне текстовое описание того, что хочешь увидеть!\n\n"
        "Пример: 'красивый закат над морем'"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    try:
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
                url_path="/webhook",
                secret_token=None
            )
        else:
            # Polling режим для локальной разработки
            logger.info("Starting polling...")
            app.run_polling()
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
