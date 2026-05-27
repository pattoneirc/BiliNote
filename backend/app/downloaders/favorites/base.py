from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FavoriteVideoItem:
    video_id: str
    platform: str
    title: str
    url: str
    cover_url: Optional[str] = None
    author: Optional[str] = None
    duration: Optional[int] = None
    favorited_at: Optional[datetime] = None
    description: Optional[str] = None


class BaseFavoritesFetcher(ABC):
    @abstractmethod
    def fetch_favorites(
        self,
        cookie: str,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FavoriteVideoItem]:
        pass

    @abstractmethod
    def get_platform(self) -> str:
        pass
