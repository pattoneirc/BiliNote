from datetime import datetime
from typing import List, Optional

from app.downloaders.favorites.base import BaseFavoritesFetcher, FavoriteVideoItem
from app.services.proxy_config_manager import ProxyConfigManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeFavoritesFetcher(BaseFavoritesFetcher):

    def get_platform(self) -> str:
        return "youtube"

    def fetch_favorites(
        self,
        cookie: str,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        playlist_id: Optional[str] = None,
    ) -> List[FavoriteVideoItem]:
        results: List[FavoriteVideoItem] = []

        if not playlist_id:
            playlist_id = "LL"

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            import yt_dlp
        except ImportError:
            logger.warning("youtube-transcript-api 或 yt-dlp 未安装")
            return results

        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "playlistend": page * page_size,
        }

        proxy = ProxyConfigManager().get_proxy_url()
        if proxy:
            ydl_opts["proxy"] = proxy

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                info = ydl.extract_info(playlist_url, download=False)

                if not info or "entries" not in info:
                    logger.info(f"YouTube 播放列表 {playlist_id} 为空或无法访问")
                    return results

                entries = list(info.get("entries") or [])
                start_idx = (page - 1) * page_size
                entries = entries[start_idx : start_idx + page_size]

                for entry in entries:
                    if not entry:
                        continue

                    video_id = entry.get("id", entry.get("url", ""))
                    if not video_id:
                        continue

                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    results.append(
                        FavoriteVideoItem(
                            video_id=video_id,
                            platform="youtube",
                            title=entry.get("title", ""),
                            url=video_url,
                            cover_url=entry.get("thumbnail", ""),
                            author=entry.get("channel", entry.get("uploader", "")),
                            duration=entry.get("duration"),
                            favorited_at=None,
                            description=entry.get("description", ""),
                        )
                    )

        except Exception as e:
            logger.warning(f"获取 YouTube 收藏列表失败: {e}")

        return results
