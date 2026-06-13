import json
import re
import asyncio
import requests
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8655586658:AAHrZiVvVKLrn3KEF5nFbdy2P0-fEf1LGIo"
CHAT_ID = 1258531174

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeWNtubYNVApdkQ-kGTSGF0khFqL4PEFDE7-af5P7DYX1TC_g/viewform"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def extract_shifts(html):
    match = re.search(r"FB_PUBLIC_LOAD_DATA_ = (.*?);</script>", html, re.S)
    if not match:
        return []

    data = json.loads(match.group(1))
    questions = data[1][1]

    for q in questions:
        if "Sloty w Wrocław" in str(q):
            try:
                return [opt[0] for opt in q[4][0][1]]
            except:
                return []
    return []


def get_current_shifts():
    try:
        r = requests.get(FORM_URL, timeout=15)
        if r.status_code != 200:
            return []
        return extract_shifts(r.text)
    except:
        return []


def load_old_shifts():
    try:
        with open("shifts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_shifts(shifts):
    with open("shifts.json", "w", encoding="utf-8") as f:
        json.dump(shifts, f, ensure_ascii=False, indent=2)


async def monitor():
    await asyncio.sleep(3)
    old = load_old_shifts()

    while True:
        try:
            new = get_current_shifts()

            if not new:
                await asyncio.sleep(20)
                continue

            diff = [s for s in new if s not in old]

            if diff:
                for shift in diff:
                    kb = InlineKeyboardMarkup()
                    kb.add(InlineKeyboardButton("Открыть форму", url=FORM_URL))

                    await bot.send_message(
                        CHAT_ID,
                        f"🟢 Новая смена:\n{shift}",
                        reply_markup=kb
                    )

                save_shifts(new)
                old = new

        except Exception as e:
            await bot.send_message(
                CHAT_ID,
                f"⚠️ Ошибка мониторинга: {e}\nПерезапускаю цикл..."
            )

        await asyncio.sleep(20)


@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "Бот запущен.\n"
        "Я буду присылать только новые смены.\n\n"
        "Команды:\n"
        "/status — показать текущие смены\n"
        "/last — последние найденные смены\n"
        "/help — список команд"
    )


@dp.message_handler(commands=["help"])
async def help_cmd(msg: types.Message):
    await msg.answer(
        "📌 Команды бота:\n"
        "/status — показать текущие смены\n"
        "/last — последние сохранённые смены\n"
        "/help — список команд"
    )


@dp.message_handler(commands=["status"])
async def status(msg: types.Message):
    shifts = get_current_shifts()
    if not shifts:
        await msg.answer("❗ Сейчас нет доступных смен.")
        return

    text = "📋 Текущие смены:\n\n" + "\n".join(f"• {s}" for s in shifts)
    await msg.answer(text)


@dp.message_handler(commands=["last"])
async def last(msg: types.Message):
    shifts = load_old_shifts()
    if not shifts:
        await msg.answer("❗ История пустая.")
        return

    text = "📦 Последние сохранённые смены:\n\n" + "\n".join(f"• {s}" for s in shifts)
    await msg.answer(text)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(monitor())
    executor.start_polling(dp, skip_updates=True)
