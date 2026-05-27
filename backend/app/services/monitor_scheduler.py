import os
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.favorites_monitor import FavoritesMonitorService
from app.services.daily_digest import DailyDigestService
from app.utils.logger import get_logger

logger = get_logger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    return _scheduler


def start_scheduler():
    scheduler = get_scheduler()

    default_cron = os.getenv("MONITOR_CRON", "0 22 * * *")
    parts = default_cron.split()
    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone="Asia/Shanghai",
        )
    else:
        trigger = CronTrigger(hour=22, minute=0, timezone="Asia/Shanghai")

    scheduler.add_job(
        _run_monitor_and_digest,
        trigger=trigger,
        id="favorites_monitor",
        name="收藏视频监控",
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
        logger.info("收藏监控调度器已启动")


def stop_scheduler():
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("收藏监控调度器已停止")


def update_monitor_schedule(cron_expression: str):
    scheduler = get_scheduler()
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式: {cron_expression}")

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone="Asia/Shanghai",
    )

    scheduler.reschedule_job(
        "favorites_monitor",
        trigger=trigger,
    )
    logger.info(f"收藏监控调度已更新: {cron_expression}")


def _run_monitor_and_digest():
    try:
        logger.info("开始执行收藏监控任务...")
        new_count = FavoritesMonitorService.run_monitor_cycle()
        logger.info(f"收藏监控完成，发现 {new_count} 条新收藏")

        logger.info("开始生成每日摘要...")
        result = DailyDigestService.generate_daily_digest()
        if result:
            logger.info(f"每日摘要生成完成: {result.get('title')}")
        else:
            logger.info("今日无需生成摘要")
    except Exception as e:
        logger.error(f"收藏监控任务执行失败: {e}", exc_info=True)
