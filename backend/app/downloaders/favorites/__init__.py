from app.downloaders.favorites.base import BaseFavoritesFetcher
from app.downloaders.favorites.bilibili_favorites import BilibiliFavoritesFetcher
from app.downloaders.favorites.douyin_favorites import DouyinFavoritesFetcher
from app.downloaders.favorites.kuaishou_favorites import KuaishouFavoritesFetcher
from app.downloaders.favorites.youtube_favorites import YouTubeFavoritesFetcher

FAVORITES_FETCHER_MAP: dict[str, BaseFavoritesFetcher] = {
    "bilibili": BilibiliFavoritesFetcher(),
    "douyin": DouyinFavoritesFetcher(),
    "kuaishou": KuaishouFavoritesFetcher(),
    "youtube": YouTubeFavoritesFetcher(),
}


def get_favorites_fetcher(platform: str) -> BaseFavoritesFetcher | None:
    return FAVORITES_FETCHER_MAP.get(platform)
