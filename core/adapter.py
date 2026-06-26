"""
Адаптация контента через Groq API — бесплатно
Groq даёт бесплатный tier: ~14,400 запросов/день на llama-3.3-70b
"""
import os
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """Ты — контент-редактор Ольги Пузановой.

Ольга — предприниматель, эксперт по ИИ и e-commerce, ведёт онлайн-школу по нейросетям.
Аудитория: предприниматели и селлеры маркетплейсов, которые хотят зарабатывать больше с помощью ИИ.

ГОЛОС И СТИЛЬ:
- Живой разговорный язык — как рассказывает подруге за кофе
- Конкретные цифры, реальные примеры, никакой воды
- Без пафоса и маркетинговых штампов
- Короткие предложения. Энергичный ритм.
- Фокус на практике: что конкретно делать, как применить в бизнесе
- Говорит от первого лица как практик, не теоретик

ЗАДАЧА: Возьми суть из транскрипции, перепиши в голосе Ольги. Не переводи дословно.

ФОРМАТ (строго, без отступлений):
ИДЕЯ: [одна строка]
ХУК: [первые 3 секунды — цепляющая фраза]
СЦЕНАРИЙ:
[00-05] ...
[05-15] ...
[15-35] ...
[35-50] ...
[50-60] [CTA]
ОПИСАНИЕ: [2-3 строки под рилс]
ХЭШТЕГИ: [10-15 штук]
ОЦЕНКА: [цифра 1-10]/10 — [одно предложение почему]"""


async def adapt_content(transcription: str, video_meta: dict) -> dict:
    """
    Адаптирует транскрипцию под голос Оли через Groq (бесплатно)
    """
    if not transcription or len(transcription.strip()) < 20:
        return {"success": False, "error": "Транскрипция слишком короткая", "adapted": ""}

    user_message = f"""Адаптируй этот YouTube Shorts под Reels от Ольги.

ПРОСМОТРЫ: {video_meta.get('views', 0):,}
КАНАЛ: {video_meta.get('channel', '')}
ЗАГОЛОВОК: {video_meta.get('title', '')[:150]}

ТРАНСКРИПЦИЯ:
{transcription[:2500]}"""

    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # бесплатная мощная модель
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1200,
            temperature=0.7,
        )

        adapted_text = response.choices[0].message.content.strip()

        return {
            "success": True,
            "adapted": adapted_text,
            "idea": _extract(adapted_text, "ИДЕЯ"),
            "hook": _extract(adapted_text, "ХУК"),
            "rating": _parse_rating(_extract(adapted_text, "ОЦЕНКА")),
            "error": None
        }

    except Exception as e:
        logger.error(f"Groq error: {e}")
        return {"success": False, "error": str(e), "adapted": ""}


def _extract(text: str, field: str) -> str:
    for line in text.split("\n"):
        if line.startswith(f"{field}:"):
            return line[len(f"{field}:"):].strip()
    return ""


def _parse_rating(rating_str: str) -> int:
    try:
        digits = "".join(filter(str.isdigit, rating_str.split("/")[0]))
        return max(1, min(10, int(digits[0]))) if digits else 5
    except Exception:
        return 5
