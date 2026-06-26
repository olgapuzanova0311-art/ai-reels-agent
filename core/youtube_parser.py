"""
YouTube Shorts парсер — полностью бесплатно через yt-dlp
Никаких API ключей не нужно
"""
import asyncio
import json
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MIN_VIEWS = int(os.getenv("MIN_VIEWS", 10000))
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", 24))


async def search_youtube_shorts(keyword: str, max_results: int = 15) -> list[dict]:
    """Ищет YouTube Shorts через yt-dlp — бесплатно"""
    results = []

    # Ищем через YouTube search
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--flat-playlist",
        "--playlist-end", str(max_results * 3),  # с запасом, потом фильтруем
        f"ytsearch{max_results * 3}:{keyword} shorts нейросети"
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)

        for line in stdout.decode("utf-8", errors="ignore").strip().split("\n"):
            if not line.strip():
                continue
            try:
                video = json.loads(line)

                duration = video.get("duration") or 0
                # Только Shorts (до 3 минут)
                if duration > 180:
                    continue

                view_count = video.get("view_count") or 0
                upload_date_str = video.get("upload_date", "")

                age_ok = True
                if upload_date_str:
                    try:
                        upload_dt = datetime.strptime(upload_date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                        age_hours = (datetime.now(timezone.utc) - upload_dt).total_seconds() / 3600
                        age_ok = age_hours <= MAX_AGE_HOURS
                    except Exception:
                        pass  # если не можем распарсить дату — берём

                if view_count >= MIN_VIEWS and age_ok:
                    video_id = video.get("id", "")
                    results.append({
                        "platform": "youtube",
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/shorts/{video_id}",
                        "title": video.get("title", ""),
                        "views": view_count,
                        "channel": video.get("channel") or video.get("uploader", ""),
                        "upload_date": upload_date_str,
                        "duration": duration,
                        "keyword": keyword,
                    })

                if len(results) >= max_results:
                    break

            except json.JSONDecodeError:
                continue

    except asyncio.TimeoutError:
        logger.warning(f"YouTube search timeout: {keyword}")
    except Exception as e:
        logger.error(f"YouTube search error: {e}")

    logger.info(f"YouTube [{keyword}]: найдено {len(results)} роликов")
    return results


async def download_audio(video_id: str, output_path: str) -> bool:
    """Скачивает аудио из YouTube Shorts — бесплатно через yt-dlp"""
    cmd = [
        "yt-dlp",
        "--format", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",   # среднее качество, меньше размер
        "--output", output_path,
        "--no-playlist",
        "--socket-timeout", "30",
        f"https://www.youtube.com/shorts/{video_id}"
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        # yt-dlp добавляет .mp3 к имени
        mp3_path = output_path + ".mp3" if not output_path.endswith(".mp3") else output_path
        actual_path = mp3_path if os.path.exists(mp3_path) else output_path

        if os.path.exists(actual_path):
            return True

        logger.warning(f"Download failed for {video_id}: {stderr.decode()[:200]}")
        return False
    except asyncio.TimeoutError:
        logger.warning(f"Download timeout: {video_id}")
        return False
    except Exception as e:
        logger.error(f"Download error {video_id}: {e}")
        return False


def find_downloaded_file(base_path: str) -> str | None:
    """Находит скачанный файл (yt-dlp может добавлять расширение)"""
    for ext in [".mp3", ".m4a", ".webm", ".opus", ""]:
        path = base_path + ext if ext else base_path
        if os.path.exists(path):
            return path
    return None
