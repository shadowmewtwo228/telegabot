# main.py
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging
import os

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv("8199522326:AAEmUp2Y1AeGiP87Bx-lXXqNL3oqiNkgGxU")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не установлен")

# Валюты
CURRENCIES = {
    'USD': 'Доллар США 💵',
    'EUR': 'Евро 🇪🇺',
    'GBP': 'Фунт стерлингов 🇬🇧',
    'CHF': 'Швейцарский франк 🇨🇭',
    'CNY': 'Китайский юань 🇨🇳',
    'JPY': 'Японская иена 🇯🇵',
}

# Подписчики
subscribers = set()

# Получение курса
def get_exchange_rates():
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url)
        data = response.json()
        rates = data['Valute']
        
        message = f"💱 *Курс валют на {datetime.now().strftime('%d.%m.%Y')}*\n\n"
        for code, name in CURRENCIES.items():
            if code in rates:
                value = rates[code]['Value']
                previous = rates[code]['Previous']
                diff = value - previous
                arrow = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                trend = f"{diff:+.2f}"
                message += f"{arrow} *{name}*: `{value:.2f}` ₽ ({trend})\n"
        
        message += f"\n_Данные: ЦБ РФ_\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        return message
    except Exception as e:
        return f"❌ Ошибка: {e}"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)

    await update.message.reply_text(
        "Привет! 👋 Я бот, который присылает курс валют.\n"
        "Команды:\n"
        "• /rate — узнать курс сейчас\n"
        "• Каждый день в 9:00 (МСК) — автоматическое уведомление"
    )

# Команда /rate
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_exchange_rates()
    await update.message.reply_text(message, parse_mode='MarkdownV2')

# Ежедневная отправка
async def send_daily_rates(app):
    message = get_exchange_rates()
    for chat_id in subscribers:
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Ошибка отправки {chat_id}: {e}")

# Запуск
if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rate", rate))

    # Планировщик
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_daily_rates, "cron", hour=9, minute=0, args=[application])
    scheduler.start()

    print("Бот запущен...")
    application.run_polling()
