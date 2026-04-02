import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ──────────────────────────────────────────────
# БАПТАУЛАР
# ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8625508269:AAH4UGSL1Vwqk3yt-25ChiHgfvmQj_GN7TI")
METRIKA_TOKEN = os.getenv("METRIKA_TOKEN", "ЯНДЕКС_ТОКЕНІН_ҚОЙЫҢЫЗ")
COUNTER_ID = os.getenv("COUNTER_ID", "СЧЁТЧИК_ID_ҚОЙЫҢЫЗ")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# НЕГІЗГІ МЕНЮ
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 1 күн", callback_data="day_1"),
            InlineKeyboardButton("📈 7 күн", callback_data="day_7"),
        ],
        [InlineKeyboardButton("📅 30 күн", callback_data="day_30")],
        [InlineKeyboardButton("🔗 Трафик көздері", callback_data="sources")],
        [InlineKeyboardButton("📄 Топ беттер", callback_data="pages")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?"

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ──────────────────────────────────────────────
# БАТЫРМА БАСЫЛҒАНДА
# ──────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        await start(update, context)
        return

    # Жүктелуде хабарламасы — лезде шығады
    await query.edit_message_text("⏳ Жүктелуде...", parse_mode="Markdown")

    if data.startswith("day_"):
        days = int(data.split("_")[1])
        titles = {1: "📊 1 күн статистикасы", 7: "📈 7 күн статистикасы", 30: "📅 30 күн статистикасы"}
        text = get_stats(days, titles[days])
    elif data == "sources":
        text = get_sources()
    elif data == "pages":
        text = get_pages()
    else:
        text = "❌ Белгісіз команда"

    back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Артқа", callback_data="back")]])
    await query.edit_message_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

# ──────────────────────────────────────────────
# СТАТИСТИКА АЛУ
# ──────────────────────────────────────────────
def get_stats(days: int, title: str) -> str:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_from = start_date.strftime("%Y-%m-%d")
    date_to = end_date.strftime("%Y-%m-%d")
    date_from_display = start_date.strftime("%d.%m.%Y")
    date_to_display = end_date.strftime("%d.%m.%Y")

    url = "https://api-metrika.yandex.net/stat/v1/data"
    params = {
        "id": COUNTER_ID,
        "metrics": "ym:s:visits,ym:s:pageviews,ym:s:users,ym:s:newUsers,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
        "date1": date_from,
        "date2": date_to,
    }
    headers = {"Authorization": f"OAuth {METRIKA_TOKEN}"}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        if "errors" in data:
            return f"❌ Қате: {data['errors'][0]['message']}"

        totals = data.get("totals", [0, 0, 0, 0, 0, 0])
        visitors = int(totals[0])
        pageviews = int(totals[1])
        new_users = int(totals[3])
        bounce = round(totals[4], 1)
        avg_time = int(totals[5])
        m, s = divmod(avg_time, 60)

        text = f"*{title}*\n"
        text += f"📆 {date_from_display} — {date_to_display}\n\n"
        text += "━━━━━━━━━━━━━━━\n"
        text += f"👤 Посетитель: *{visitors:,}*\n"
        text += f"📄 Просмотр: *{pageviews:,}*\n"
        text += f"🆕 Жаңа: *{new_users:,}*\n"
        text += f"⏱ Орт. уақыт: *{m}м {s}с*\n"
        text += f"📉 Bounce: *{bounce}%*\n"
        text += "━━━━━━━━━━━━━━━"
        return text

    except Exception as e:
        return f"❌ Қате: {str(e)}"

# ──────────────────────────────────────────────
# ТРАФИК КӨЗДЕРІ
# ──────────────────────────────────────────────
def get_sources() -> str:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    url = "https://api-metrika.yandex.net/stat/v1/data"
    params = {
        "id": COUNTER_ID,
        "dimensions": "ym:s:trafficSourceName",
        "metrics": "ym:s:visits",
        "date1": start_date.strftime("%Y-%m-%d"),
        "date2": end_date.strftime("%Y-%m-%d"),
        "sort": "-ym:s:visits",
        "limit": 7,
    }
    headers = {"Authorization": f"OAuth {METRIKA_TOKEN}"}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]
        text = "*🔗 Трафик көздері (7 күн)*\n━━━━━━━━━━━━━━━\n"

        for i, row in enumerate(data.get("data", [])):
            name = row["dimensions"][0]["name"] or "Белгісіз"
            visits = int(row["metrics"][0])
            text += f"{emojis[i]} {name}: *{visits}*\n"

        text += "━━━━━━━━━━━━━━━"
        return text

    except Exception as e:
        return f"❌ Қате: {str(e)}"

# ──────────────────────────────────────────────
# ТОП БЕТТЕР
# ──────────────────────────────────────────────
def get_pages() -> str:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    url = "https://api-metrika.yandex.net/stat/v1/data"
    params = {
        "id": COUNTER_ID,
        "dimensions": "ym:pv:URLPath",
        "metrics": "ym:pv:pageviews",
        "date1": start_date.strftime("%Y-%m-%d"),
        "date2": end_date.strftime("%Y-%m-%d"),
        "sort": "-ym:pv:pageviews",
        "limit": 7,
    }
    headers = {"Authorization": f"OAuth {METRIKA_TOKEN}"}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        text = "*📄 Топ беттер (7 күн)*\n━━━━━━━━━━━━━━━\n"

        for i, row in enumerate(data.get("data", []), 1):
            page = row["dimensions"][0]["name"] or "/"
            views = int(row["metrics"][0])
            if len(page) > 25:
                page = page[:25] + "..."
            text += f"{i}. `{page}`: *{views}*\n"

        text += "━━━━━━━━━━━━━━━"
        return text

    except Exception as e:
        return f"❌ Қате: {str(e)}"

# ──────────────────────────────────────────────
# БАСТАУ
# ──────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("Бот іске қосылды!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
