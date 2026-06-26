"""
Telegram sender — отправляет карточки Оле
"""
import asyncio
import os
import logging
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

_bot = None

def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=BOT_TOKEN)
    return _bot

STARS = {1:"⭐",2:"⭐⭐",3:"⭐⭐⭐",4:"⭐⭐⭐⭐",5:"⭐⭐⭐⭐⭐",
         6:"⭐⭐⭐⭐⭐⭐",7:"💫💫💫",8:"🔥🔥🔥",9:"🔥🔥🔥🔥",10:"🔥🔥🔥🔥🔥"}


def esc(text: str) -> str:
    """Экранирует для MarkdownV2"""
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


async def send_card(video: dict, transcription: str, adaptation: dict) -> bool:
    bot = get_bot()
    rating = adaptation.get("rating", 5)
    views = f"{video.get('views', 0):,}".replace(",", " ")

    # Сообщение 1 — карточка
    msg1 = (
        f"▶️ *YouTube Shorts* | {esc(views)} просмотров\n"
        f"👤 {esc(video.get('channel', ''))}\n"
        f"🔗 {esc(video.get('url', ''))}\n\n"
        f"🎯 *{esc(adaptation.get('idea', ''))}*\n\n"
        f"⚡️ ХУК: _{esc(adaptation.get('hook', ''))}_\n\n"
        f"Оценка: {STARS.get(rating, '⭐⭐⭐⭐⭐')} {rating}/10"
    )

    # Сообщение 2 — сценарий
    adapted = adaptation.get("adapted", "")[:3500]
    msg2 = f"📝 *СЦЕНАРИЙ:*\n\n{esc(adapted)}"

    # Сообщение 3 — оригинал
    short_tr = transcription[:600] + ("..." if len(transcription) > 600 else "")
    msg3 = f"🎙 *Оригинал:*\n_{esc(short_tr)}_"

    try:
        for msg in [msg1, msg2, msg3]:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            )
            await asyncio.sleep(0.5)
        return True
    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        # Fallback без форматирования
        try:
            plain = (
                f"▶️ YouTube | {views} просмотров\n"
                f"{video.get('url', '')}\n\n"
                f"ИДЕЯ: {adaptation.get('idea', '')}\n"
                f"ХУК: {adaptation.get('hook', '')}\n"
                f"Оценка: {rating}/10\n\n"
                f"{adaptation.get('adapted', '')[:2000]}"
            )
            await bot.send_message(chat_id=CHAT_ID, text=plain)
            return True
        except Exception:
            return False


async def send_summary(stats: dict) -> None:
    text = (
        f"📊 Сессия завершена\n\n"
        f"Найдено: {stats.get('found', 0)}\n"
        f"Отправлено: {stats.get('sent', 0)}\n"
        f"Уже видели: {stats.get('skipped', 0)}\n"
        f"Ошибок: {stats.get('errors', 0)}"
    )
    try:
        await get_bot().send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"Summary error: {e}")


async def send_alert(text: str) -> None:
    try:
        await get_bot().send_message(chat_id=CHAT_ID, text=f"⚠️ {text[:400]}")
    except Exception:
        pass
