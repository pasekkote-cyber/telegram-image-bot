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

# Список рабочих моделей для перебора
WORKING_MODELS = [
    "runwayml/stable-diffusion-v1-5",  # Более стабильная модель
    "prompthero/openjourney-v4",       # Альтернативная модель
    "wavymulder/Analog-Diffusion",     # Еще одна альтернатива
]

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    prompt = update.message.text
    user_id = update.effective_user.id
    
    try:
        logger.info(f"User {user_id} requested: {prompt}")
        await update.message.reply_text("🎨 Генерирую изображение... (это займет 20-60 секунд)")
        
        # Пробуем разные модели
        for model_index, model in enumerate(WORKING_MODELS):
            try:
                logger.info(f"Trying model: {model}")
                
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                    json={
                        "inputs": prompt,
                        "options": {
                            "wait_for_model": True,
                            "use_cache": False
                        }
                    },
                    timeout=120
                )
                
                logger.info(f"Model {model} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Проверяем, что ответ действительно содержит изображение
                    if len(response.content) < 1000:  # Слишком маленький ответ - вероятно ошибка
                        error_text = response.text[:200] if response.text else "Empty response"
                        logger.warning(f"Model {model} returned small response: {error_text}")
                        continue
                    
                    try:
                        image = Image.open(BytesIO(response.content))
                        # Проверяем, что изображение валидное
                        image.verify()
                        
                        # Переоткрываем для использования
                        image = Image.open(BytesIO(response.content))
                        
                        bio = BytesIO()
                        bio.name = 'image.png'
                        image.save(bio, 'PNG')
                        bio.seek(0)
                        
                        await update.message.reply_photo(
                            photo=bio, 
                            caption=f"🎨 Сгенерировано по запросу: '{prompt}'\nМодель: {model.split('/')[-1]}"
                        )
                        logger.info(f"✅ Image sent to user {user_id} using {model}")
                        return
                        
                    except Exception as img_error:
                        logger.warning(f"Invalid image from {model}: {img_error}")
                        continue
                
                elif response.status_code == 503:
                    # Модель загружается
                    if model_index < len(WORKING_MODELS) - 1:
                        logger.info(f"Model {model} is loading, trying next model...")
                        continue
                    else:
                        raise Exception("Все модели временно загружаются. Попробуйте через 1-2 минуты.")
                
                elif response.status_code == 404:
                    logger.warning(f"Model {model} not found (404), trying next...")
                    continue
                    
                else:
                    # Другие ошибки API
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Unknown error')
                    except:
                        error_msg = response.text[:500] if response.text else f'Status {response.status_code}'
                    
                    logger.warning(f"Model {model} error: {error_msg}")
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Model {model} timeout, trying next...")
                continue
            except Exception as model_error:
                logger.warning(f"Model {model} failed: {model_error}")
                continue
        
        # Если все модели не сработали
        raise Exception(
            "😔 Все модели временно недоступны.\n\n"
            "Возможные причины:\n"
            "• Модели загружаются (попробуйте через 1-2 минуты)\n"  
            "• Слишком сложный запрос\n"
            "• Временные проблемы с API\n\n"
            "Попробуйте простой запрос на английском, например: 'a cat', 'sunset', 'flower'"
        )
        
    except Exception as e:
        error_msg = f"❌ {str(e)}"
        await update.message.reply_text(error_msg[:1000])
        logger.error(f"Error for user {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для генерации изображений.\n"
        "Просто отправь мне текстовое описание того, что хочешь увидеть!\n\n"
        "Примеры:\n"
        "• 'a cute cat'\n" 
        "• 'beautiful sunset'\n"
        "• 'colorful flowers'\n\n"
        "Лучше использовать английский язык для лучших результатов!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ Помощь:\n\n"
        "Просто напишите описание изображения на английском языке.\n"
        "Бот использует несколько моделей AI для генерации.\n\n"
        "Если возникает ошибка - попробуйте через минуту или упростите запрос."
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
        app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("help"), help_command))
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
