"""
Оркестратор агента — координирует весь pipeline
YouTube Shorts → транскрипция → адаптация → Telegram
"""
import asyncio
import os
import json
import hashlib
import tempfile
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from core.youtube_parser import search_youtube_shorts, download_audio, find_downloaded_file
from core.transcriber import transcribe_audio
from core.adapter import adapt_content
from bot.sender import send_card, send_summary, send_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("agent")

VIDEOS_PER_RUN = int(os.getenv("VIDEOS_PER_RUN", 30))
KEYWORDS = [k.strip() for k in os.getenv(
    "SEARCH_KEYWORDS",
    "нейросети,ChatGPT,ИИ,AI,midjourney,llm"
).split(",") if k.strip()]

SEEN_FILE = "seen_videos.json"


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return set(json.load(f)[-3000:])
        except Exception:
            pass
    return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen)[-3000:], f)


def video_key(v: dict) -> str:
    return hashlib.md5(f"yt:{v['video_id']}".encode()).hexdigest()


async def process_video(video: dict, tmp_dir: str) -> dict:
    vid_id = video["video_id"]

    # Скачиваем аудио
    base_path = os.path.join(tmp_dir, f"yt_{vid_id}")
    ok = await download_audio(vid_id, base_path)
    if not ok:
        return {"success": False, "error": "download failed"}

    audio_path = find_downloaded_file(base_path)
    if not audio_path:
        return {"success": False, "error": "file not found after download"}

    # Транскрибируем
    tr = await transcribe_audio(audio_path)
    if not tr["success"] or not tr["text"]:
        return {"success": False, "error": f"transcription: {tr.get('error')}"}

    # Адаптируем
    ad = await adapt_content(tr["text"], video)
    if not ad["success"]:
        return {"success": False, "error": f"adaptation: {ad.get('error')}"}

    try:
        os.remove(audio_path)
    except Exception:
        pass

    return {"success": True, "transcription": tr["text"], "adaptation": ad}


async def run_agent() -> None:
    logger.info(f"🚀 Запуск | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    seen = load_seen()
    stats = {"found": 0, "sent": 0, "skipped": 0, "errors": 0}

    # Собираем видео по всем ключевым словам
    per_keyword = max(5, VIDEOS_PER_RUN // len(KEYWORDS))
    tasks = [search_youtube_shorts(kw, max_results=per_keyword) for kw in KEYWORDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_videos = []
    for r in results:
        if isinstance(r, list):
            all_videos.extend(r)

    # Дедупликация
    seen_ids = set()
    unique = []
    for v in all_videos:
        key = video_key(v)
        if key not in seen_ids and key not in seen:
            seen_ids.add(key)
            unique.append(v)
        else:
            stats["skipped"] += 1

    # Сортируем по просмотрам
    unique.sort(key=lambda x: x.get("views", 0), reverse=True)
    to_process = unique[:VIDEOS_PER_RUN]

    stats["found"] = len(all_videos)
    logger.info(f"Найдено: {len(all_videos)}, обрабатываем топ {len(to_process)}")

    # Обрабатываем — по 2 параллельно (RAM лимит на Railway)
    sem = asyncio.Semaphore(2)

    async def process_with_sem(video):
        async with sem:
            return video, await process_video(video, tmp_dir)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tasks = [process_with_sem(v) for v in to_process]

        for coro in asyncio.as_completed(tasks):
            try:
                video, result = await coro
                if result["success"]:
                    sent = await send_card(video, result["transcription"], result["adaptation"])
                    if sent:
                        stats["sent"] += 1
                        seen.add(video_key(video))
                    await asyncio.sleep(2)
                else:
                    stats["errors"] += 1
                    logger.warning(f"Пропуск {video['video_id']}: {result['error']}")
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Error: {e}")

    save_seen(seen)
    await send_summary(stats)
    logger.info(f"✅ Готово. Отправлено: {stats['sent']}, ошибок: {stats['errors']}")


if __name__ == "__main__":
    asyncio.run(run_agent())
