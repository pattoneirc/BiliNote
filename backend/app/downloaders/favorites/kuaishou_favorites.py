from datetime import datetime
from typing import List, Optional

import requests

from app.downloaders.favorites.base import BaseFavoritesFetcher, FavoriteVideoItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class KuaishouFavoritesFetcher(BaseFavoritesFetcher):

    def get_platform(self) -> str:
        return "kuaishou"

    def _headers(self, cookie: str) -> dict:
        return {
            "User-Agent": UA,
            "Referer": "https://www.kuaishou.com/",
            "Cookie": cookie,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def fetch_favorites(
        self,
        cookie: str,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FavoriteVideoItem]:
        results: List[FavoriteVideoItem] = []

        if not cookie:
            logger.warning("Kuaishou cookie 为空，无法获取收藏列表")
            return results

        url = "https://www.kuaishou.com/graphql"
        cursor = ""

        for _ in range(page):
            payload = {
                "operationName": "favoriteVideoQuery",
                "query": """
                    query favoriteVideoQuery($pcursor: String, $count: Int) {
                        favoriteVideoQuery(pcursor: $pcursor, count: $count) {
                            pcursor
                            list {
                                photoId
                                caption
                                coverUrl
                                userName
                                duration
                                photoUrl
                                timestamp
                            }
                        }
                    }
                """,
                "variables": {
                    "pcursor": cursor,
                    "count": page_size,
                },
            }

            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=self._headers(cookie),
                    timeout=15,
                )
                data = resp.json()
            except Exception as e:
                logger.warning(f"获取快手收藏列表失败: {e}")
                break

            fav_data = data.get("data", {}).get("favoriteVideoQuery", {})
            video_list = fav_data.get("list") or []

            if not video_list:
                break

            for item in video_list:
                fav_time = None
                ts = item.get("timestamp")
                if ts:
                    try:
                        fav_time = datetime.fromtimestamp(ts / 1000)
                    except Exception:
                        pass

                if since and fav_time and fav_time < since:
                    return results

                photo_id = item.get("photoId", "")
                video_url = f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else ""

                results.append(
                    FavoriteVideoItem(
                        video_id=photo_id,
                        platform="kuaishou",
                        title=item.get("caption", ""),
                        url=video_url,
                        cover_url=item.get("coverUrl", ""),
                        author=item.get("userName", ""),
                        duration=item.get("duration"),
                        favorited_at=fav_time,
                        description=item.get("caption", ""),
                    )
                )

            next_cursor = fav_data.get("pcursor", "")
            if not next_cursor or next_cursor == "no_more":
                break
            cursor = next_cursor

        return results
