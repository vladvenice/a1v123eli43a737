"""
🎂 Birthday Warming Bot
Отправляет сообщения-прогревы к дню рождения каждые 3 часа (10:00–22:00 МСК),
а 6 марта в 23:00 МСК — отправляет финальную ссылку.

Установка: pip install python-telegram-bot apscheduler pytz
Запуск:     python birthday_bot.py
"""

import asyncio
import os
import random
import logging
from datetime import datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHAT_ID    = int(os.environ["CHAT_ID"])
FINAL_LINK = "https://aveiliabirthday.netlify.app/"  # ← замени на свою ссылку

# ─── СООБЩЕНИЯ-ПРОГРЕВЫ ───────────────────────────────────────────────────────

WARMING_MESSAGES = [
    "✨ Кстати, скоро будет один особенный день... чувствуешь что-то в воздухе?",
    "🌸 Говорят, что в марте случаются самые лучшие вещи. Просто так, к слову 😏",
    "🎈 Где-то в недалёком будущем тебя ждёт кое-что приятное. Скоро узнаешь!",
    "⏳ Тик-так... Время идёт, и с каждым часом что-то важное всё ближе~",
    "🌟 Знаешь, я тут подумал... ты заслуживаешь праздника. И он будет!",
    "🎁 Уже готовится что-то особенное. Осталось совсем чуть-чуть подождать 😉",
    "🔮 Моя интуиция говорит: скоро тебе будет очень хорошо. Доверяй процессу!",
    "💫 Ты когда-нибудь замечала, как перед чем-то классным всегда чуть-чуть тревожно и радостно одновременно?",
    "🎶 Какая-то мелодия крутится в голове... что-то праздничное, не пойму откуда 🎂",
    "🌙 Вечер хороший, правда? Наслаждайся — дни считаны до чего-то особенного!",
    "🚀 Скоро. Очень скоро. Готовься к чему-то тёплому и приятному 💛",
    "🎉 Psst... я знаю один секрет. Он связан с тобой и 7 марта. Вот и всё, что скажу!",
    "🌈 Представь: ещё немного — и будет повод улыбнуться во весь рот. Жди!",
    "🕯️ Каждый день делает тебя ближе к чему-то особенному. Просто будь собой 💙",
    "🐣 Скоро вылупится что-то хорошее. Уже совсем скоро! 🐥",
    "🍰 Ощущение, что кто-то уже печёт торт... может, не буквально, но почти!",
    "✉️ Одно письмо уже на пути к тебе. Ждать совсем немного осталось~",
    "🌺 Знаешь, что мне нравится в тебе? Многое. И 7 марта — отличный повод это сказать!",
    "⭐ Ты — звезда. И скоро будет повод об этом напомнить официально 😄",
    "🎠 Карусель событий закрутится уже совсем скоро. Держись крепче — будет весело!",
]

FINAL_MESSAGE = (
    "🎂🎉 С ДНЁМ РОЖДЕНИЯ! 🎉🎂\n\n"
    "Вот твой подарок — с любовью и теплом:\n\n"
    "{link}\n\n"
    "Пусть этот день будет самым лучшим! 💛"
)

# ─── ЛОГИРОВАНИЕ ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── СОСТОЯНИЕ ────────────────────────────────────────────────────────────────

sent_indices: set[int] = set()
final_sent: bool = False

# ─── ФУНКЦИИ ──────────────────────────────────────────────────────────────────

async def send_warming(bot: Bot) -> None:
    """Выбирает случайное (ещё не отправленное) сообщение и шлёт его."""
    global sent_indices

    available = [i for i in range(len(WARMING_MESSAGES)) if i not in sent_indices]
    if not available:
        # Все сообщения уже отправлены — сбрасываем и повторяем
        sent_indices.clear()
        available = list(range(len(WARMING_MESSAGES)))

    idx = random.choice(available)
    sent_indices.add(idx)
    text = WARMING_MESSAGES[idx]

    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        log.info(f"Warming sent (#{idx}): {text[:50]}...")
    except Exception as e:
        log.error(f"Ошибка при отправке warming: {e}")


async def send_final(bot: Bot) -> None:
    """Отправляет финальную ссылку."""
    global final_sent
    if final_sent:
        return

    text = FINAL_MESSAGE.format(link=FINAL_LINK)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        final_sent = True
        log.info("Final birthday message sent!")
    except Exception as e:
        log.error(f"Ошибка при отправке финального сообщения: {e}")


# ─── ПЛАНИРОВЩИК ──────────────────────────────────────────────────────────────

async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    tz_moscow = pytz.timezone("Europe/Moscow")
    scheduler = AsyncIOScheduler(timezone=tz_moscow)

    # Каждые 3 часа с 10:00 до 22:00 МСК (10, 13, 16, 19, 22)
    for hour in range(10, 23, 3):
        scheduler.add_job(
            send_warming,
            trigger="cron",
            hour=hour,
            minute=0,
            args=[bot],
            id=f"warming_{hour}",
        )
        log.info(f"Запланирована отправка warming в {hour:02d}:00 МСК")

    # Финальное сообщение 6 марта в 23:00 МСК
    scheduler.add_job(
        send_final,
        trigger="cron",
        month=3,
        day=6,
        hour=23,
        minute=0,
        args=[bot],
        id="final_birthday",
    )
    log.info("Запланирована финальная ссылка: 6 марта в 23:00 МСК")

    scheduler.start()
    log.info("🤖 Бот запущен! Ожидание расписания...")

    # Держим event loop живым
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("Бот остановлен.")


# ─── ТОЧКА ВХОДА ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(main())
