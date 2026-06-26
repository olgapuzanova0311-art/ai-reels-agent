"""
Транскрипция через Groq Whisper API — бесплатно
До 7200 минут аудио в день на бесплатном тире
"""
import asyncio
import os
import subprocess
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))


async def convert_to_mp3(input_path: str) -> str:
    """Конвертирует аудио в mp3 через ffmpeg"""
    output_path = input_path.rsplit(".", 1)[0] + ".mp3"
    if input_path == output_path:
        output_path = input_path + "_converted.mp3"
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vn", "-acodec", "libmp3lame",
        "-ab", "64k", "-ar", "16000",
        "-y", output_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(proc.communicate(), timeout=60)
    return output_path if os.path.exists(output_path) else input_path


async def transcribe_audio(audio_path: str) -> dict:
    """
    Транскрибирует аудио через Groq Whisper — бесплатно
    """
    if not os.path.exists(audio_path):
        return {"success": False, "error": "Файл не найден", "text": ""}

    # Конвертируем в mp3 если нужно
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in (".mp3", ".m4a", ".wav"):
        audio_path = await convert_to_mp3(audio_path)

    # Groq лимит — 25MB
    if os.path.getsize(audio_path) > 24 * 1024 * 1024:
        logger.warning("Файл слишком большой, обрезаем до 3 минут")
        trimmed = audio_path + "_trim.mp3"
        cmd = ["ffmpeg", "-i", audio_path, "-t", "180", "-y", trimmed]
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        if os.path.exists(trimmed):
            audio_path = trimmed

    try:
        with open(audio_path, "rb") as f:
            response = await groq_client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f),
                model="whisper-large-v3-turbo",  # быстрая и точная, бесплатно
                response_format="text",
                language=None,  # автоопределение
            )

        text = response.strip() if isinstance(response, str) else response.text.strip()
        logger.info(f"Транскрипция: {text[:80]}...")

        return {"success": True, "text": text, "language": "auto", "error": None}

    except Exception as e:
        logger.error(f"Groq Whisper error: {e}")
        return {"success": False, "error": str(e), "text": ""}
