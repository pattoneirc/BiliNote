from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.engine import SessionLocal
from app.db.models.monitor import MonitorSource, DailyDigest, FavoriteVideo, NotifyChannel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MonitorSourceDAO:

    @staticmethod
    def create(source: dict) -> MonitorSource:
        with SessionLocal() as db:
            obj = MonitorSource(**source)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def get_by_id(source_id: int) -> Optional[MonitorSource]:
        with SessionLocal() as db:
            return db.query(MonitorSource).filter(MonitorSource.id == source_id).first()

    @staticmethod
    def get_all() -> List[MonitorSource]:
        with SessionLocal() as db:
            return db.query(MonitorSource).order_by(MonitorSource.id.desc()).all()

    @staticmethod
    def get_enabled() -> List[MonitorSource]:
        with SessionLocal() as db:
            return db.query(MonitorSource).filter(MonitorSource.enabled == 1).all()

    @staticmethod
    def update(source_id: int, updates: dict) -> Optional[MonitorSource]:
        with SessionLocal() as db:
            obj = db.query(MonitorSource).filter(MonitorSource.id == source_id).first()
            if not obj:
                return None
            for k, v in updates.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            obj.updated_at = datetime.now()
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def delete(source_id: int) -> bool:
        with SessionLocal() as db:
            obj = db.query(MonitorSource).filter(MonitorSource.id == source_id).first()
            if not obj:
                return False
            db.delete(obj)
            db.commit()
            return True

    @staticmethod
    def update_last_check(source_id: int, last_video_id: str):
        with SessionLocal() as db:
            obj = db.query(MonitorSource).filter(MonitorSource.id == source_id).first()
            if obj:
                obj.last_check_at = datetime.now()
                obj.last_video_id = last_video_id
                db.commit()


class FavoriteVideoDAO:

    @staticmethod
    def create(video: dict) -> FavoriteVideo:
        with SessionLocal() as db:
            obj = FavoriteVideo(**video)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def batch_create(videos: List[dict]) -> List[FavoriteVideo]:
        with SessionLocal() as db:
            objs = [FavoriteVideo(**v) for v in videos]
            db.add_all(objs)
            db.commit()
            for o in objs:
                db.refresh(o)
            return objs

    @staticmethod
    def exists(video_id: str, platform: str) -> bool:
        with SessionLocal() as db:
            return db.query(FavoriteVideo).filter(
                FavoriteVideo.video_id == video_id,
                FavoriteVideo.platform == platform,
            ).first() is not None

    @staticmethod
    def get_unprocessed(platform: Optional[str] = None) -> List[FavoriteVideo]:
        with SessionLocal() as db:
            q = db.query(FavoriteVideo).filter(FavoriteVideo.processed == 0)
            if platform:
                q = q.filter(FavoriteVideo.platform == platform)
            return q.order_by(FavoriteVideo.favorited_at.desc()).all()

    @staticmethod
    def mark_processed(video_id: str, platform: str, task_id: str):
        with SessionLocal() as db:
            obj = db.query(FavoriteVideo).filter(
                FavoriteVideo.video_id == video_id,
                FavoriteVideo.platform == platform,
            ).first()
            if obj:
                obj.processed = 1
                obj.task_id = task_id
                db.commit()

    @staticmethod
    def get_by_date_range(start: datetime, end: datetime, platform: Optional[str] = None) -> List[FavoriteVideo]:
        with SessionLocal() as db:
            q = db.query(FavoriteVideo).filter(
                FavoriteVideo.favorited_at >= start,
                FavoriteVideo.favorited_at < end,
            )
            if platform:
                q = q.filter(FavoriteVideo.platform == platform)
            return q.order_by(FavoriteVideo.favorited_at.desc()).all()


class DailyDigestDAO:

    @staticmethod
    def create(digest: dict) -> DailyDigest:
        with SessionLocal() as db:
            obj = DailyDigest(**digest)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def get_by_id(digest_id: int) -> Optional[DailyDigest]:
        with SessionLocal() as db:
            return db.query(DailyDigest).filter(DailyDigest.id == digest_id).first()

    @staticmethod
    def get_by_date(digest_date: str) -> List[DailyDigest]:
        with SessionLocal() as db:
            return db.query(DailyDigest).filter(DailyDigest.digest_date == digest_date).all()

    @staticmethod
    def get_all(limit: int = 30) -> List[DailyDigest]:
        with SessionLocal() as db:
            return db.query(DailyDigest).order_by(DailyDigest.id.desc()).limit(limit).all()

    @staticmethod
    def update_content(digest_id: int, markdown_content: str, video_count: int, file_path: Optional[str] = None):
        with SessionLocal() as db:
            obj = db.query(DailyDigest).filter(DailyDigest.id == digest_id).first()
            if obj:
                obj.markdown_content = markdown_content
                obj.video_count = video_count
                if file_path:
                    obj.file_path = file_path
                db.commit()


class NotifyChannelDAO:

    @staticmethod
    def create(data: dict) -> NotifyChannel:
        with SessionLocal() as db:
            obj = NotifyChannel(**data)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def get_by_id(channel_id: int) -> Optional[NotifyChannel]:
        with SessionLocal() as db:
            return db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()

    @staticmethod
    def get_all() -> List[NotifyChannel]:
        with SessionLocal() as db:
            return db.query(NotifyChannel).order_by(NotifyChannel.id.desc()).all()

    @staticmethod
    def get_enabled() -> List[NotifyChannel]:
        with SessionLocal() as db:
            return db.query(NotifyChannel).filter(NotifyChannel.enabled == 1).all()

    @staticmethod
    def update(channel_id: int, updates: dict) -> Optional[NotifyChannel]:
        with SessionLocal() as db:
            obj = db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()
            if not obj:
                return None
            for k, v in updates.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            obj.updated_at = datetime.now()
            db.commit()
            db.refresh(obj)
            return obj

    @staticmethod
    def delete(channel_id: int) -> bool:
        with SessionLocal() as db:
            obj = db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()
            if not obj:
                return False
            db.delete(obj)
            db.commit()
            return True
