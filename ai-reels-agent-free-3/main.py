"""
Планировщик — запускает агента каждые N часов на Railway
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("scheduler")

INTERVAL = int(os.getenv("PARSE_INTERVAL_HOURS", 6))


async def job():
    try:
        from agent import run_agent
        await run_agent()
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        from bot.sender import send_alert
        await send_alert(f"Агент упал: {e}")


async def main():
    logger.info(f"🤖 AI Reels Agent | интервал: каждые {INTERVAL} часов")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(job, IntervalTrigger(hours=INTERVAL), id="reels_agent")
    scheduler.start()

    # Запуск сразу при старте
    logger.info("Первый запуск...")
    await job()

    # Держим живым
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
