from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.db.monitor_dao import MonitorSourceDAO, FavoriteVideoDAO, DailyDigestDAO, NotifyChannelDAO
from app.services.favorites_monitor import FavoritesMonitorService
from app.services.daily_digest import DailyDigestService
from app.services.notify_service import NotifyService
from app.services.monitor_scheduler import (
    start_scheduler,
    stop_scheduler,
    update_monitor_schedule,
    get_scheduler,
)
from app.utils.logger import get_logger
from app.utils.response import ResponseWrapper as R

logger = get_logger(__name__)

router = APIRouter()


class MonitorSourceCreate(BaseModel):
    platform: str
    source_type: str = "favorites"
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    enabled: int = 1
    process_mode: str = "summary"
    cron_expression: str = "0 22 * * *"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None
    note_style: Optional[str] = None
    note_format: Optional[str] = None


class MonitorSourceUpdate(BaseModel):
    source_name: Optional[str] = None
    enabled: Optional[int] = None
    process_mode: Optional[str] = None
    cron_expression: Optional[str] = None
    model_name: Optional[str] = None
    provider_id: Optional[str] = None
    note_style: Optional[str] = None
    note_format: Optional[str] = None
    source_id: Optional[str] = None


class ManualCheckRequest(BaseModel):
    source_id: Optional[int] = None


class ManualDigestRequest(BaseModel):
    target_date: Optional[str] = None
    model_name: Optional[str] = None
    provider_id: Optional[str] = None


class ProcessVideosRequest(BaseModel):
    process_mode: str = "summary"
    model_name: Optional[str] = None
    provider_id: Optional[str] = None
    style: Optional[str] = None
    note_format: Optional[list] = None


@router.post("/monitor_source")
def create_monitor_source(data: MonitorSourceCreate):
    try:
        source_data = data.model_dump()
        obj = MonitorSourceDAO.create(source_data)
        return R.success({
            "id": obj.id,
            "platform": obj.platform,
            "source_type": obj.source_type,
            "source_name": obj.source_name,
            "enabled": obj.enabled,
            "process_mode": obj.process_mode,
            "cron_expression": obj.cron_expression,
        })
    except Exception as e:
        logger.error(f"创建监控源失败: {e}")
        return R.error(msg=str(e))


@router.get("/monitor_sources")
def list_monitor_sources():
    try:
        sources = MonitorSourceDAO.get_all()
        result = []
        for s in sources:
            result.append({
                "id": s.id,
                "platform": s.platform,
                "source_type": s.source_type,
                "source_id": s.source_id,
                "source_name": s.source_name,
                "enabled": s.enabled,
                "process_mode": s.process_mode,
                "cron_expression": s.cron_expression,
                "model_name": s.model_name,
                "provider_id": s.provider_id,
                "note_style": s.note_style,
                "note_format": s.note_format,
                "last_check_at": str(s.last_check_at) if s.last_check_at else None,
                "last_video_id": s.last_video_id,
                "created_at": str(s.created_at) if s.created_at else None,
            })
        return R.success(result)
    except Exception as e:
        logger.error(f"获取监控源列表失败: {e}")
        return R.error(msg=str(e))


@router.get("/monitor_source/{source_id}")
def get_monitor_source(source_id: int):
    obj = MonitorSourceDAO.get_by_id(source_id)
    if not obj:
        return R.error(msg="监控源不存在", code=404)
    return R.success({
        "id": obj.id,
        "platform": obj.platform,
        "source_type": obj.source_type,
        "source_id": obj.source_id,
        "source_name": obj.source_name,
        "enabled": obj.enabled,
        "process_mode": obj.process_mode,
        "cron_expression": obj.cron_expression,
        "model_name": obj.model_name,
        "provider_id": obj.provider_id,
        "note_style": obj.note_style,
        "note_format": obj.note_format,
        "last_check_at": str(obj.last_check_at) if obj.last_check_at else None,
        "last_video_id": obj.last_video_id,
        "created_at": str(obj.created_at) if obj.created_at else None,
    })


@router.put("/monitor_source/{source_id}")
def update_monitor_source(source_id: int, data: MonitorSourceUpdate):
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        obj = MonitorSourceDAO.update(source_id, updates)
        if not obj:
            return R.error(msg="监控源不存在", code=404)
        return R.success({
            "id": obj.id,
            "platform": obj.platform,
            "enabled": obj.enabled,
            "process_mode": obj.process_mode,
        })
    except Exception as e:
        logger.error(f"更新监控源失败: {e}")
        return R.error(msg=str(e))


@router.delete("/monitor_source/{source_id}")
def delete_monitor_source(source_id: int):
    success = MonitorSourceDAO.delete(source_id)
    if not success:
        return R.error(msg="监控源不存在", code=404)
    return R.success(msg="删除成功")


@router.post("/monitor/check")
def manual_check(data: ManualCheckRequest, background_tasks: BackgroundTasks):
    try:
        if data.source_id:
            items = FavoritesMonitorService.check_source(data.source_id)
            saved = FavoritesMonitorService.save_new_favorites(items, data.source_id)
            return R.success({
                "new_count": len(saved),
                "items": saved,
            })
        else:
            background_tasks.add_task(FavoritesMonitorService.run_monitor_cycle)
            return R.success(msg="全量监控检查已在后台启动")
    except Exception as e:
        logger.error(f"手动检查失败: {e}")
        return R.error(msg=str(e))


@router.post("/monitor/process")
def process_unprocessed(data: ProcessVideosRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            FavoritesMonitorService.process_unprocessed_videos,
            process_mode=data.process_mode,
            model_name=data.model_name,
            provider_id=data.provider_id,
            style=data.style,
            note_format=data.note_format,
        )
        return R.success(msg="视频处理任务已在后台启动")
    except Exception as e:
        logger.error(f"启动处理任务失败: {e}")
        return R.error(msg=str(e))


@router.post("/monitor/digest")
def generate_digest(data: ManualDigestRequest, background_tasks: BackgroundTasks):
    try:
        if data.model_name and data.provider_id:
            background_tasks.add_task(
                DailyDigestService.generate_daily_digest,
                target_date=data.target_date,
                model_name=data.model_name,
                provider_id=data.provider_id,
            )
        else:
            background_tasks.add_task(
                DailyDigestService.generate_daily_digest,
                target_date=data.target_date,
            )
        return R.success(msg="每日摘要生成任务已在后台启动")
    except Exception as e:
        logger.error(f"生成摘要失败: {e}")
        return R.error(msg=str(e))


@router.get("/digests")
def list_digests(limit: int = 30):
    try:
        result = DailyDigestService.list_digests(limit)
        return R.success(result)
    except Exception as e:
        logger.error(f"获取摘要列表失败: {e}")
        return R.error(msg=str(e))


@router.get("/digest/{digest_id}")
def get_digest(digest_id: int):
    result = DailyDigestService.get_digest(digest_id)
    if not result:
        return R.error(msg="摘要不存在", code=404)
    return R.success(result)


@router.get("/favorite_videos")
def list_favorite_videos(
    platform: Optional[str] = None,
    processed: Optional[int] = None,
    limit: int = 50,
):
    try:
        if processed is not None and processed == 0:
            videos = FavoriteVideoDAO.get_unprocessed(platform)
        else:
            videos = FavoriteVideoDAO.get_unprocessed(platform) if processed == 0 else []

        result = []
        for v in videos[:limit]:
            result.append({
                "id": v.id,
                "video_id": v.video_id,
                "platform": v.platform,
                "title": v.title,
                "url": v.url,
                "cover_url": v.cover_url,
                "author": v.author,
                "duration": v.duration,
                "favorited_at": str(v.favorited_at) if v.favorited_at else None,
                "processed": v.processed,
                "task_id": v.task_id,
            })
        return R.success(result)
    except Exception as e:
        logger.error(f"获取收藏视频列表失败: {e}")
        return R.error(msg=str(e))


@router.post("/monitor/scheduler/start")
def start_monitor_scheduler():
    try:
        start_scheduler()
        return R.success(msg="调度器已启动")
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        return R.error(msg=str(e))


@router.post("/monitor/scheduler/stop")
def stop_monitor_scheduler():
    try:
        stop_scheduler()
        return R.success(msg="调度器已停止")
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        return R.error(msg=str(e))


@router.get("/monitor/scheduler/status")
def get_scheduler_status():
    try:
        scheduler = get_scheduler()
        running = scheduler.running
        jobs = []
        if running:
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                })
        return R.success({
            "running": running,
            "jobs": jobs,
        })
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        return R.error(msg=str(e))


@router.put("/monitor/scheduler/cron")
def update_scheduler_cron(cron_expression: str):
    try:
        update_monitor_schedule(cron_expression)
        return R.success(msg=f"调度已更新: {cron_expression}")
    except Exception as e:
        logger.error(f"更新调度失败: {e}")
        return R.error(msg=str(e))


class NotifyChannelCreate(BaseModel):
    channel_type: str
    name: Optional[str] = None
    webhook_url: str
    secret: Optional[str] = None
    enabled: int = 1
    notify_on_digest: int = 1
    notify_on_new_favorite: int = 0
    notify_on_error: int = 0
    template: Optional[str] = None


class NotifyChannelUpdate(BaseModel):
    name: Optional[str] = None
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    enabled: Optional[int] = None
    notify_on_digest: Optional[int] = None
    notify_on_new_favorite: Optional[int] = None
    notify_on_error: Optional[int] = None
    template: Optional[str] = None


@router.post("/notify_channel")
def create_notify_channel(data: NotifyChannelCreate):
    try:
        channel_data = data.model_dump()
        obj = NotifyChannelDAO.create(channel_data)
        return R.success({
            "id": obj.id,
            "channel_type": obj.channel_type,
            "name": obj.name,
            "enabled": obj.enabled,
        })
    except Exception as e:
        logger.error(f"创建通知渠道失败: {e}")
        return R.error(msg=str(e))


@router.get("/notify_channels")
def list_notify_channels():
    try:
        channels = NotifyChannelDAO.get_all()
        result = []
        for ch in channels:
            result.append({
                "id": ch.id,
                "channel_type": ch.channel_type,
                "name": ch.name,
                "webhook_url": ch.webhook_url,
                "secret": "***" if ch.secret else None,
                "enabled": ch.enabled,
                "notify_on_digest": ch.notify_on_digest,
                "notify_on_new_favorite": ch.notify_on_new_favorite,
                "notify_on_error": ch.notify_on_error,
                "template": ch.template,
                "created_at": str(ch.created_at) if ch.created_at else None,
            })
        return R.success(result)
    except Exception as e:
        logger.error(f"获取通知渠道列表失败: {e}")
        return R.error(msg=str(e))


@router.put("/notify_channel/{channel_id}")
def update_notify_channel(channel_id: int, data: NotifyChannelUpdate):
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        obj = NotifyChannelDAO.update(channel_id, updates)
        if not obj:
            return R.error(msg="通知渠道不存在", code=404)
        return R.success({
            "id": obj.id,
            "channel_type": obj.channel_type,
            "name": obj.name,
            "enabled": obj.enabled,
        })
    except Exception as e:
        logger.error(f"更新通知渠道失败: {e}")
        return R.error(msg=str(e))


@router.delete("/notify_channel/{channel_id}")
def delete_notify_channel(channel_id: int):
    success = NotifyChannelDAO.delete(channel_id)
    if not success:
        return R.error(msg="通知渠道不存在", code=404)
    return R.success(msg="删除成功")


@router.post("/notify_channel/{channel_id}/test")
def test_notify_channel(channel_id: int):
    try:
        result = NotifyService.test_channel(channel_id)
        if result["success"]:
            return R.success(msg=result["message"])
        else:
            return R.error(msg=result["message"])
    except Exception as e:
        logger.error(f"测试通知渠道失败: {e}")
        return R.error(msg=str(e))
