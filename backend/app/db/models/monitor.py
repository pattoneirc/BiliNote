from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func

from app.db.engine import Base


class MonitorSource(Base):
    __tablename__ = "monitor_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default="favorites")
    source_id = Column(String, nullable=True)
    source_name = Column(String, nullable=True)
    enabled = Column(Integer, default=1)
    process_mode = Column(String, default="summary")
    cron_expression = Column(String, default="0 22 * * *")
    last_check_at = Column(DateTime, nullable=True)
    last_video_id = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    provider_id = Column(String, nullable=True)
    note_style = Column(String, nullable=True)
    note_format = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DailyDigest(Base):
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    digest_date = Column(String, nullable=False)
    title = Column(String, nullable=False)
    markdown_content = Column(Text, nullable=True)
    video_count = Column(Integer, default=0)
    platform = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class FavoriteVideo(Base):
    __tablename__ = "favorite_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    title = Column(String, nullable=True)
    url = Column(String, nullable=False)
    cover_url = Column(String, nullable=True)
    author = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    favorited_at = Column(DateTime, nullable=True)
    processed = Column(Integer, default=0)
    task_id = Column(String, nullable=True)
    digest_id = Column(Integer, nullable=True)
    monitor_source_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class NotifyChannel(Base):
    __tablename__ = "notify_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_type = Column(String, nullable=False)
    name = Column(String, nullable=True)
    webhook_url = Column(String, nullable=False)
    secret = Column(String, nullable=True)
    enabled = Column(Integer, default=1)
    notify_on_digest = Column(Integer, default=1)
    notify_on_new_favorite = Column(Integer, default=0)
    notify_on_error = Column(Integer, default=0)
    template = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
