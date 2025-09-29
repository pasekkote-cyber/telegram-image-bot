# main.py
import os
import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
PORT = int(os.environ.get("PORT", 8443))

async def full_hf_diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полная диагностика HuggingFace доступа"""
    
    await update.message.reply_text("🔍 Запускаю полную диагностику HF...")
    
    results = []
    
    # 1. Проверка базовой аутентификации
    try:
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            user_info = response.json()
            results.append(f"✅ Аутентификация: Успешно")
            results.append(f"   👤 Пользователь: {user_info.get('name')}")
            results.append(f"   🔑 Роль: {user_info.get('role')}")
            results.append(f"   🚀 Inference API: {user_info.get('canAccessInferenceAPI', False)}")
        else:
            results.append(f"❌ Аутентификация: Неудача (Status: {response.status_code})")
    except Exception as e:
        results.append(f"❌ Аутентификация: Ошибка - {e}")

    # 2. Проверка доступа к Inference API
    try:
        response = requests.get(
            "https://api-inference.huggingface.co/models/gpt2",  # Простая текстовая модель
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            timeout=10
        )
        if response.status_code == 200:
            results.append("✅ Inference API: Доступен")
        elif response.status_code == 403:
            results.append("❌ Inference API: Запрещено (403)")
        elif response.status_code == 404:
            results.append("❌ Inference API: Модель не найдена (404)")
        else:
            results.append(f"❌ Inference API: Ошибка {response.status_code}")
    except Exception as e:
        results.append(f"❌ Inference API: Ошибка - {e}")

    # 3. Проверка конкретных моделей Stable Diffusion
    sd_models = [
        "runwayml/stable-diffusion-v1-5",
        "stabilityai/stable-diffusion-2-1",
        "CompVis/stable-diffusion-v1-4"
    ]
    
    results.append("\n🔍 Проверка моделей Stable Diffusion:")
    
    for model in sd_models:
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": "test"},
                timeout=15
            )
            
            if response.status_code == 200:
                results.append(f"  ✅ {model}: Доступна")
            elif response.status_code == 402:
                results.append(f"  💰 {model}: Требуется оплата (402)")
            elif response.status_code == 403:
                results.append(f"  🚫 {model}: Нет доступа (403)")
            elif response.status_code == 404:
                results.append(f"  ❌ {model}: Не найдена (404)")
            elif response.status_code == 503:
                results.append(f"  ⏳ {model}: Загружается (503)")
            else:
                # Пытаемся получить детальную ошибку
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown')
                    results.append(f"  ❓ {model}: {response.status_code} - {error_msg}")
                except:
                    results.append(f"  ❓ {model}: {response.status_code}")
                    
        except Exception as e:
            results.append(f"  💥 {model}: Ошибка - {e}")

    # 4. Проверка доступности моделей через API
    try:
        response = requests.get(
            f"https://huggingface.co/api/models/runwayml/stable-diffusion-v1-5",
            timeout=10
        )
        if response.status_code == 200:
            model_info = response.json()
            results.append(f"\n📊 Информация о модели:")
            results.append(f"   📥 Загрузки: {model_info.get('downloads', 'N/A')}")
            results.append(f"   🏷️ Лицензия: {model_info.get('license', 'N/A')}")
            results.append(f"   ⚠️ Ограничения: {model_info.get('cardData', {}).get('license', 'N/A')}")
    except Exception as e:
        results.append(f"\n❓ Инфо о модели: Ошибка - {e}")

    # Отправляем результаты
    result_text = "\n".join(results)
    await update.message.reply_text(f"Результаты диагностики:\n{result_text}")

async def check_subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса подписки HF"""
    await update.message.reply_text("🔍 Проверяю статус подписки...")
    
    try:
        # Проверяем доступ к платным функциям
        response = requests.get(
            "https://huggingface.co/api/billing/subscription",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            timeout=10
        )
        
        if response.status_code == 200:
            sub_info = response.json()
            await update.message.reply_text(
                f"📋 Статус подписки:\n"
                f"   💰 Plan: {sub_info.get('plan', 'Free')}\n"
                f"   📊 Usage: {sub_info.get('usage', 'N/A')}\n"
                f"   🚀 Limits: {sub_info.get('limits', 'N/A')}"
            )
        elif response.status_code == 404:
            await update.message.reply_text("❌ Подписка не найдена (бесплатный аккаунт)")
        else:
            await update.message.reply_text(f"❓ Статус подписки: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки подписки: {e}")

async def test_simple_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест с простой моделью (не SD)"""
    await update.message.reply_text("🧪 Тестирую простую текстовую модель...")
    
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/gpt2",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": "Hello, how are you?"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            await update.message.reply_text(f"✅ Текстовая модель работает!\nОтвет: {str(result)[:200]}...")
        else:
            await update.message.reply_text(f"❌ Текстовая модель не работает: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка текстовой модели: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Бот диагностики HuggingFace\n\n"
        "Команды:\n"
        "/diagnose - Полная диагностика\n" 
        "/subscription - Проверка подписки\n"
        "/test_model - Тест простой модели\n"
        "/generate - Попытка генерации изображения"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Попытка генерации с улучшенной диагностикой"""
    prompt = update.message.text
    user_id = update.effective_user.id
    
    try:
        logger.info(f"User {user_id} requested: {prompt}")
        await update.message.reply_text("🎨 Пытаюсь сгенерировать...")
        
        # Сначала проверяем доступ
        response = requests.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            timeout=10
        )
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Ошибка аутентификации HF")
            return
            
        user_info = response.json()
        can_access_inference = user_info.get('canAccessInferenceAPI', False)
        
        if not can_access_inference:
            await update.message.reply_text(
                "❌ Нет доступа к Inference API!\n\n"
                "Решение:\n"
                "1. Перейдите в Settings → Billing на HF\n" 
                "2. Активируйте Inference API\n"
                "3. Возможно, нужна привязка карты"
            )
            return
        
        # Пробуем генерацию
        response = requests.post(
            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5",
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt},
            timeout=120
        )
        
        logger.info(f"Generation status: {response.status_code}")
        
        if response.status_code == 200:
            from io import BytesIO
            from PIL import Image
            
            image = Image.open(BytesIO(response.content))
            bio = BytesIO()
            bio.name = 'image.png'
            image.save(bio, 'PNG')
            bio.seek(0)
            
            await update.message.reply_photo(photo=bio, caption=f"🎨 {prompt}")
            
        elif response.status_code == 402:
            await update.message.reply_text(
                "❌ Требуется оплата для Stable Diffusion!\n\n"
                "Решение:\n" 
                "1. Перейдите на https://huggingface.co/settings/billing\n"
                "2. Добавьте способ оплаты\n"
                "3. Или используйте другой сервис (Stability AI)"
            )
            
        elif response.status_code == 403:
            await update.message.reply_text(
                "❌ Нет прав доступа к этой модели!\n\n"
                "Решение:\n"
                "1. Нужна специальная активация модели\n"
                "2. Или используйте другую модель"
            )
            
        else:
            await update.message.reply_text(f"❌ Ошибка генерации: {response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("start"), start))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("diagnose"), full_hf_diagnosis))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("subscription"), check_subscription_status))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("test_model"), test_simple_model))
    
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        app.run_webhook(
            listen="0.0.0.0", 
            port=PORT,
            webhook_url=f"{RENDER_EXTERNAL_URL}/webhook",
            url_path="/webhook"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
