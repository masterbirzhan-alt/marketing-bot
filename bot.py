import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8625508269:AAH4UGSL1Vwqk3yt-25ChiHgfvmQj_GN7TI")
METRIKA_TOKEN = os.environ.get("y0__xCbo-iTCBiP4j8gwvjc-BYoAmhEsfZqlpkL1b-GcLeEXm6D06-F", "")
COUNTER_ID = os.environ.get("106106416", "")


def get_back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Артқа", callback_data="back")]])


def get_main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 1 күн", callback_data="day_1"),
         InlineKeyboardButton("📈 7 күн", callback_data="day_7")],
        [InlineKeyboardButton("📅 30 күн", callback_data="day_30")],
        [InlineKeyboardButton("🔗 Трафик көздері", callback_data="sources")],
        [InlineKeyboardButton("📄 Топ беттер", callback_data="pages")],
    ])


def metrika(params):
    params["id"] = COUNTER_ID
    r = requests.get(
        "https://api-metrika.yandex.net/stat/v1/data",
        params=params,
        headers={"Authorization": f"OAuth {METRIKA_TOKEN}"},
        timeout=15
    )
    return r.json()


def stats_text(days, title):
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        d = metrika({
            "metrics": "ym:s:visits,ym:s:pageviews,ym:s:users,ym:s:newUsers,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
        })
        t = d.get("totals", [0]*6)
        m, s = divmod(int(t[5]), 60)
        return (
            f"*{title}*\n📆 {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Посетитель: *{int(t[0]):,}*\n"
            f"📄 Просмотр: *{int(t[1]):,}*\n"
            f"🆕 Жаңа: *{int(t[3]):,}*\n"
            f"⏱ Орт. уақыт: *{m}м {s}с*\n"
            f"📉 Bounce: *{round(t[4], 1)}%*\n"
            f"━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Қате: {e}"


def sources_text():
    end = datetime.now()
    start = end - timedelta(days=7)
    try:
        d = metrika({
            "dimensions": "ym:s:trafficSourceName",
            "metrics": "ym:s:visits",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
            "sort": "-ym:s:visits",
            "limit": 7,
        })
        emojis = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣"]
        text = "*🔗 Трафик көздері (7 күн)*\n━━━━━━━━━━━━━━━\n"
        for i, row in enumerate(d.get("data", [])):
            name = row["dimensions"][0].get("name") or "Белгісіз"
            text += f"{emojis[i]} {name}: *{int(row['metrics'][0])}*\n"
        return text + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return f"❌ Қате: {e}"


def pages_text():
    end = datetime.now()
    start = end - timedelta(days=7)
    try:
        d = metrika({
            "dimensions": "ym:pv:URLPath",
            "metrics": "ym:pv:pageviews",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
            "sort": "-ym:pv:pageviews",
            "limit": 7,
        })
        text = "*📄 Топ беттер (7 күн)*\n━━━━━━━━━━━━━━━\n"
        for i, row in enumerate(d.get("data", []), 1):
            page = row["dimensions"][0].get("name") or "/"
            if len(page) > 25:
                page = page[:25] + "..."
            text += f"{i}. `{page}`: *{int(row['metrics'][0])}*\n"
        return text + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return f"❌ Қате: {e}"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_kb(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_kb(), parse_mode="Markdown")


async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back":
        await cmd_start(update, context)
        return

    await q.edit_message_text("⏳ Жүктелуде...", parse_mode="Markdown")

    titles = {"day_1": "📊 1 күн", "day_7": "📈 7 күн", "day_30": "📅 30 күн"}
    days_map = {"day_1": 1, "day_7": 7, "day_30": 30}

    if q.data in days_map:
        text = stats_text(days_map[q.data], titles[q.data])
    elif q.data == "sources":
        text = sources_text()
    elif q.data == "pages":
        text = pages_text()
    else:
        text = "❌ Белгісіз команда"

    await q.edit_message_text(text, reply_markup=get_back_kb(), parse_mode="Markdown")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(btn))
    logger.info("Бот іске қосылды!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
