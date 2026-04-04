import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TG_TOKEN = os.environ.get("8625508269:AAH4UGSL1Vwqk3yt-25ChiHgfvmQj_GN7TI", "")
YA_TOKEN = os.environ.get("y0__xCbo-iTCBiP4j8gwvjc-BYoAmhEsfZqlpkL1b-GcLeEXm6D06-F", "")
CTR_ID = os.environ.get("106106416", "")


def main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 1 күн", callback_data="s1"),
         InlineKeyboardButton("📈 7 күн", callback_data="s7")],
        [InlineKeyboardButton("📅 30 күн", callback_data="s30")],
        [InlineKeyboardButton("🔗 Трафик көздері", callback_data="src")],
        [InlineKeyboardButton("📄 Топ беттер", callback_data="pgs")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Артқа", callback_data="back")]])


def ya_get(params):
    params["id"] = CTR_ID
    r = requests.get(
        "https://api-metrika.yandex.net/stat/v1/data",
        params=params,
        headers={"Authorization": "OAuth " + YA_TOKEN},
        timeout=15
    )
    return r.json()


def make_stats(days, title):
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        d = ya_get({
            "metrics": "ym:s:visits,ym:s:pageviews,ym:s:users,ym:s:newUsers,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
        })
        t = d.get("totals", [0, 0, 0, 0, 0, 0])
        m, s = divmod(int(float(str(t[5]))), 60)
        return (
            "*" + title + "*\n"
            "📆 " + start.strftime('%d.%m.%Y') + " — " + end.strftime('%d.%m.%Y') + "\n\n"
            "━━━━━━━━━━━━━━━\n"
            "👤 Посетитель: *" + str(int(t[0])) + "*\n"
            "📄 Просмотр: *" + str(int(t[1])) + "*\n"
            "🆕 Жаңа: *" + str(int(t[3])) + "*\n"
            "⏱ Орт. уақыт: *" + str(m) + "м " + str(s) + "с*\n"
            "📉 Bounce: *" + str(round(float(str(t[4])), 1)) + "%*\n"
            "━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return "❌ Қате: " + str(e)


def make_sources():
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        d = ya_get({
            "dimensions": "ym:s:trafficSourceName",
            "metrics": "ym:s:visits",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
            "sort": "-ym:s:visits",
            "limit": 7,
        })
        em = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣"]
        txt = "*🔗 Трафик көздері (7 күн)*\n━━━━━━━━━━━━━━━\n"
        for i, row in enumerate(d.get("data", [])):
            name = row["dimensions"][0].get("name") or "Белгісіз"
            txt += em[i] + " " + name + ": *" + str(int(row["metrics"][0])) + "*\n"
        return txt + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return "❌ Қате: " + str(e)


def make_pages():
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        d = ya_get({
            "dimensions": "ym:pv:URLPath",
            "metrics": "ym:pv:pageviews",
            "date1": start.strftime("%Y-%m-%d"),
            "date2": end.strftime("%Y-%m-%d"),
            "sort": "-ym:pv:pageviews",
            "limit": 7,
        })
        txt = "*📄 Топ беттер (7 күн)*\n━━━━━━━━━━━━━━━\n"
        for i, row in enumerate(d.get("data", []), 1):
            page = row["dimensions"][0].get("name") or "/"
            if len(page) > 25:
                page = page[:25] + "..."
            txt += str(i) + ". " + page + ": *" + str(int(row["metrics"][0])) + "*\n"
        return txt + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return "❌ Қате: " + str(e)


def cmd_start(update: Update, context: CallbackContext):
    txt = "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?"
    update.message.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")


def btn_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "back":
        query.edit_message_text(
            "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
        return

    query.edit_message_text("⏳ Жүктелуде...", parse_mode="Markdown")

    if query.data == "s1":
        txt = make_stats(1, "📊 1 күн статистикасы")
    elif query.data == "s7":
        txt = make_stats(7, "📈 7 күн статистикасы")
    elif query.data == "s30":
        txt = make_stats(30, "📅 30 күн статистикасы")
    elif query.data == "src":
        txt = make_sources()
    elif query.data == "pgs":
        txt = make_pages()
    else:
        txt = "❌ Белгісіз команда"

    query.edit_message_text(txt, reply_markup=back_menu(), parse_mode="Markdown")


def main():
    updater = Updater(TG_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", cmd_start))
    dp.add_handler(CallbackQueryHandler(btn_handler))
    logger.info("Bot started!")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
