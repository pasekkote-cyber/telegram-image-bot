# main.py
import os
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
from io import BytesIO

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
PORT = int(os.environ.get("PORT", 8443))

if not TELEGRAM_TOKEN:
    raise ValueError("❌ Не задан TELEGRAM_TOKEN")

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерация изображения через Stability AI"""
    if not update.message or not update.message.text:
        return
    
    prompt = update.message.text
    user_id = update.effective_user.id
    
    try:
        logger.info(f"User {user_id} requested: {prompt}")
        
        if not STABILITY_API_KEY:
            await update.message.reply_text(
                "❌ STABILITY_API_KEY не настроен.\n\n"
                "Как получить API ключ:\n"
                "1. Зарегистрируйтесь на platform.stability.ai\n"
                "2. В Dashboard найдите API Keys\n"
                "3. Скопируйте ключ и добавьте в настройки Render как STABILITY_API_KEY"
            )
            return
        
        await update.message.reply_text("🎨 Генерирую изображение... (10-20 секунд)")
        
        # Stability AI API
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "image/*"
            },
            files={"none": ''},  # Обязательный параметр
            data={
                "prompt": prompt,
                "output_format": "png",
            },
            timeout=60
        )
        
        logger.info(f"Stability AI response status: {response.status_code}")
        
        if response.status_code == 200:
            # Успешная генерация
            bio = BytesIO(response.content)
            bio.name = 'image.png'
            
            await update.message.reply_photo(
                photo=bio,
                caption=f"🎨 '{prompt}'\nСгенерировано через Stability AI"
            )
            logger.info(f"✅ Image successfully sent to user {user_id}")
            
        elif response.status_code == 402:
            await update.message.reply_text(
                "❌ Лимит бесплатных изображений исчерпан.\n\n"
                "Решение:\n"
                "• Перейдите на platform.stability.ai\n"
                "• Проверьте баланс в Dashboard\n"
                "• При необходимости пополните счёт"
            )
        elif response.status_code == 401:
            await update.message.reply_text(
                "❌ Неверный Stability AI API ключ.\n\n"
                "Решение:\n"
                "• Проверьте STABILITY_API_KEY в Render\n"
                "• Убедитесь что ключ скопирован полностью\n"
                "• Создайте новый API ключ на platform.stability.ai"
            )
        elif response.status_code == 429:
            await update.message.reply_text(
                "❌ Слишком много запросов.\n\n"
                "Подождите немного и попробуйте снова."
            )
        else:
            error_text = response.text[:500] if response.text else "Unknown error"
            await update.message.reply_text(
                f"❌ Ошибка генерации: {response.status_code}\n"
                f"Детали: {error_text}"
            )
        
    except requests.exceptions.Timeout:
        await update.message.reply_text(
            "❌ Превышено время ожидания генерации.\n"
            "Попробуйте позже или упростите запрос."
        )
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        await update.message.reply_text(error_msg[:1000])
        logger.error(f"Error for user {user_id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    if STABILITY_API_KEY:
        status = "✅ Stability AI настроен"
    else:
        status = "❌ STABILITY_API_KEY не задан"
    
    await update.message.reply_text(
        f"👋 Привет! Я бот для генерации изображений через Stability AI.\n\n"
        f"{status}\n\n"
        f"📝 Просто отправь мне описание на английском языке!\n\n"
        f"📌 Примеры запросов:\n"
        f"• 'a cute cat wearing hat'\n"
        f"• 'beautiful sunset over mountains'\n"
        f"• 'colorful flowers in garden'\n"
        f"• 'cyberpunk city at night'\n\n"
        f"⚡ Генерация занимает 10-20 секунд"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "ℹ️ Помощь по использованию бота:\n\n"
        "📝 Отправьте текстовое описание изображения на английском языке\n"
        "⏱️ Генерация занимает 10-20 секунд\n"
        "🖼️ Бот вернёт сгенерированное изображение\n\n"
        "💡 Советы для лучших результатов:\n"
        "• Используйте конкретные описания\n"
        "• Добавляйте детали (цвета, стиль, фон)\n"
        "• Избегайте слишком сложных запросов\n\n"
        "🛠️ Команды:\n"
        "/start - начать работу\n"
        "/help - эта справка\n"
        "/status - проверить статус API"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - проверка статуса API"""
    if not STABILITY_API_KEY:
        await update.message.reply_text("❌ STABILITY_API_KEY не задан")
        return
    
    try:
        await update.message.reply_text("🔍 Проверяю статус Stability AI API...")
        
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
            files={"none": ''},
            data={"prompt": "test", "output_format": "png"},
            timeout=15
        )
        
        if response.status_code in [200, 400]:  # 400 - нормально для теста без валидного промпта
            await update.message.reply_text(
                "✅ Stability AI API доступен и работает!\n\n"
                "📊 Статус: Активен\n"
                "⚡ Готов к генерации изображений"
            )
        else:
            await update.message.reply_text(
                f"❓ Неожиданный статус API: {response.status_code}\n"
                f"Ответ: {response.text[:200]}"
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки статуса: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Запуск бота"""
    try:
        # Создаём Application
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
        app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("start"), start))
        app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("help"), help_command))
        app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("status"), status_command))
        app.add_error_handler(error_handler)
        
        # Запуск на Render
        RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
        
        if RENDER_EXTERNAL_URL:
            # Webhook режим для Render
            webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
            logger.info(f"🚀 Starting Stability AI Bot on port {PORT}")
            logger.info(f"🌐 Webhook URL: {webhook_url}")
            
            app.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=webhook_url,
                url_path="/webhook",
                secret_token=None
            )
        else:
            # Polling режим для локальной разработки
            logger.info("🔄 Starting polling...")
            app.run_polling()
            
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
