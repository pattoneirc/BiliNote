import uuid
from datetime import datetime
from typing import List, Optional

from app.db.monitor_dao import MonitorSourceDAO, FavoriteVideoDAO
from app.downloaders.favorites import get_favorites_fetcher
from app.downloaders.favorites.base import FavoriteVideoItem
from app.services.cookie_manager import CookieConfigManager
from app.services.note import NoteGenerator
from app.enmus.note_enums import DownloadQuality
from app.enmus.task_status_enums import TaskStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FavoritesMonitorService:

    @staticmethod
    def check_source(source_id: int) -> List[FavoriteVideoItem]:
        source = MonitorSourceDAO.get_by_id(source_id)
        if not source:
            logger.warning(f"监控源 {source_id} 不存在")
            return []

        if not source.enabled:
            logger.info(f"监控源 {source_id} 已禁用，跳过")
            return []

        platform = source.platform
        fetcher = get_favorites_fetcher(platform)
        if not fetcher:
            logger.warning(f"不支持的平台: {platform}")
            return []

        cookie_mgr = CookieConfigManager()
        cookie = cookie_mgr.get(platform)
        if not cookie:
            logger.warning(f"平台 {platform} 的 Cookie 未配置，跳过")
            return []

        since = source.last_check_at
        extra_kwargs = {}
        if platform == "bilibili" and source.source_id:
            try:
                extra_kwargs["folder_id"] = int(source.source_id)
            except ValueError:
                pass
        if platform == "youtube" and source.source_id:
            extra_kwargs["playlist_id"] = source.source_id

        try:
            items = fetcher.fetch_favorites(
                cookie=cookie,
                since=since,
                page_size=20,
                **extra_kwargs,
            )
        except Exception as e:
            logger.error(f"获取 {platform} 收藏列表失败: {e}")
            return []

        new_items = []
        for item in items:
            if not FavoriteVideoDAO.exists(item.video_id, item.platform):
                new_items.append(item)

        if new_items:
            last_video_id = new_items[0].video_id
            MonitorSourceDAO.update_last_check(source_id, last_video_id)
        else:
            MonitorSourceDAO.update_last_check(source_id, source.last_video_id or "")

        logger.info(f"监控源 {source_id} ({platform}): 发现 {len(new_items)} 条新收藏")
        return new_items

    @staticmethod
    def save_new_favorites(items: List[FavoriteVideoItem], monitor_source_id: int) -> List[dict]:
        saved = []
        for item in items:
            if FavoriteVideoDAO.exists(item.video_id, item.platform):
                continue
            video_data = {
                "video_id": item.video_id,
                "platform": item.platform,
                "title": item.title,
                "url": item.url,
                "cover_url": item.cover_url,
                "author": item.author,
                "duration": item.duration,
                "favorited_at": item.favorited_at,
                "processed": 0,
                "monitor_source_id": monitor_source_id,
            }
            obj = FavoriteVideoDAO.create(video_data)
            saved.append({
                "id": obj.id,
                "video_id": obj.video_id,
                "platform": obj.platform,
                "title": obj.title,
                "url": obj.url,
            })
        return saved

    @staticmethod
    def process_unprocessed_videos(
        process_mode: str = "summary",
        model_name: Optional[str] = None,
        provider_id: Optional[str] = None,
        style: Optional[str] = None,
        note_format: Optional[list] = None,
    ) -> List[dict]:
        unprocessed = FavoriteVideoDAO.get_unprocessed()
        if not unprocessed:
            logger.info("没有待处理的收藏视频")
            return []

        results = []
        generator = NoteGenerator()

        for video in unprocessed:
            task_id = str(uuid.uuid4())
            try:
                logger.info(f"开始处理收藏视频: {video.title} ({video.url})")
                generator._update_status(task_id, TaskStatus.PENDING)

                if process_mode == "full":
                    note = generator.generate(
                        video_url=video.url,
                        platform=video.platform,
                        quality=DownloadQuality.medium,
                        task_id=task_id,
                        model_name=model_name,
                        provider_id=provider_id,
                        style=style,
                        _format=note_format or [],
                    )
                else:
                    note = generator.generate(
                        video_url=video.url,
                        platform=video.platform,
                        quality=DownloadQuality.fast,
                        task_id=task_id,
                        model_name=model_name,
                        provider_id=provider_id,
                        style=style or "简洁",
                        _format=note_format or [],
                    )

                if note:
                    FavoriteVideoDAO.mark_processed(video.video_id, video.platform, task_id)
                    results.append({
                        "video_id": video.video_id,
                        "platform": video.platform,
                        "title": video.title,
                        "task_id": task_id,
                        "status": "success",
                    })
                else:
                    results.append({
                        "video_id": video.video_id,
                        "platform": video.platform,
                        "title": video.title,
                        "task_id": task_id,
                        "status": "failed",
                    })
            except Exception as e:
                logger.error(f"处理收藏视频失败: {video.title}, error: {e}")
                results.append({
                    "video_id": video.video_id,
                    "platform": video.platform,
                    "title": video.title,
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                })

        return results

    @staticmethod
    def run_monitor_cycle():
        enabled_sources = MonitorSourceDAO.get_enabled()
        all_new_items: List[FavoriteVideoItem] = []

        for source in enabled_sources:
            try:
                items = FavoritesMonitorService.check_source(source.id)
                if items:
                    FavoritesMonitorService.save_new_favorites(items, source.id)
                    all_new_items.extend(items)
            except Exception as e:
                logger.error(f"监控源 {source.id} ({source.platform}) 检查失败: {e}")

        if all_new_items:
            process_mode = enabled_sources[0].process_mode if enabled_sources else "summary"
            model_name = enabled_sources[0].model_name if enabled_sources else None
            provider_id = enabled_sources[0].provider_id if enabled_sources else None
            style = enabled_sources[0].note_style if enabled_sources else None
            note_format_str = enabled_sources[0].note_format if enabled_sources else None
            note_format = note_format_str.split(",") if note_format_str else []

            FavoritesMonitorService.process_unprocessed_videos(
                process_mode=process_mode,
                model_name=model_name,
                provider_id=provider_id,
                style=style,
                note_format=note_format,
            )
        else:
            logger.info("本轮监控未发现新收藏视频")

        return len(all_new_items)
