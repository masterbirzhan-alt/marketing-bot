import os
import asyncio
import logging
import requests
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TG_TOKEN = os.environ.get("8625508269:AAH4UGSL1Vwqk3yt-25ChiHgfvmQj_GN7TI", "")
YA_TOKEN = os.environ.get("y0__xCbo-iTCBiP4j8gwvjc-BYoAmhEsfZqlpkL1b-GcLeEXm6D06-F", "")
CTR_ID = os.environ.get("106106416", "")

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 1 күн", callback_data="s1"),
         InlineKeyboardButton(text="📈 7 күн", callback_data="s7")],
        [InlineKeyboardButton(text="📅 30 күн", callback_data="s30")],
        [InlineKeyboardButton(text="🔗 Трафик көздері", callback_data="src")],
        [InlineKeyboardButton(text="📄 Топ беттер", callback_data="pgs")],
    ])


def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Артқа", callback_data="back")]
    ])


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
        t = d.get("totals", [0]*6)
        m, s = divmod(int(float(str(t[5]))), 60)
        return (
            f"*{title}*\n"
            f"📆 {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Посетитель: *{int(t[0])}*\n"
            f"📄 Просмотр: *{int(t[1])}*\n"
            f"🆕 Жаңа: *{int(t[3])}*\n"
            f"⏱ Орт. уақыт: *{m}м {s}с*\n"
            f"📉 Bounce: *{round(float(str(t[4])), 1)}%*\n"
            f"━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"❌ Қате: {e}"


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
            txt += f"{em[i]} {name}: *{int(row['metrics'][0])}*\n"
        return txt + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return f"❌ Қате: {e}"


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
            txt += f"{i}. `{page}`: *{int(row['metrics'][0])}*\n"
        return txt + "━━━━━━━━━━━━━━━"
    except Exception as e:
        return f"❌ Қате: {e}"


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "back")
async def back_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 *Сайт аналитика боты*\n\nҚандай статистика керек?",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.callback_query(F.data.in_({"s1", "s7", "s30", "src", "pgs"}))
async def btn_handler(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("⏳ Жүктелуде...", parse_mode="Markdown")

    data = callback.data
    titles = {"s1": "📊 1 күн статистикасы", "s7": "📈 7 күн статистикасы", "s30": "📅 30 күн статистикасы"}
    days_map = {"s1": 1, "s7": 7, "s30": 30}

    if data in days_map:
        txt = make_stats(days_map[data], titles[data])
    elif data == "src":
        txt = make_sources()
    elif data == "pgs":
        txt = make_pages()
    else:
        txt = "❌ Белгісіз команда"

    await callback.message.edit_text(txt, reply_markup=back_menu(), parse_mode="Markdown")


async def main():
    logging.info("Bot started!")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
