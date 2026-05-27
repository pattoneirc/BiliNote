from datetime import datetime
from typing import List, Optional

import requests

from app.downloaders.favorites.base import BaseFavoritesFetcher, FavoriteVideoItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class BilibiliFavoritesFetcher(BaseFavoritesFetcher):

    def get_platform(self) -> str:
        return "bilibili"

    def _headers(self, cookie: str) -> dict:
        h = {
            "User-Agent": UA,
            "Referer": "https://www.bilibili.com",
        }
        if cookie:
            h["Cookie"] = cookie
        return h

    def _get_favorite_folders(self, cookie: str) -> List[dict]:
        url = "https://api.bilibili.com/x/v3/fav/folder/created/list-all"
        try:
            resp = requests.get(
                url,
                params={"up_mid": self._get_mid(cookie)},
                headers=self._headers(cookie),
                timeout=10,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.warning(f"获取收藏夹列表失败: {data.get('message')}")
                return []
            return data.get("data", {}).get("list") or []
        except Exception as e:
            logger.warning(f"获取收藏夹列表异常: {e}")
            return []

    def _get_mid(self, cookie: str) -> Optional[str]:
        url = "https://api.bilibili.com/x/web-interface/nav"
        try:
            resp = requests.get(url, headers=self._headers(cookie), timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                return str(data["data"]["mid"])
        except Exception as e:
            logger.warning(f"获取 mid 失败: {e}")
        return None

    def fetch_favorites(
        self,
        cookie: str,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        folder_id: Optional[int] = None,
    ) -> List[FavoriteVideoItem]:
        results: List[FavoriteVideoItem] = []

        if not cookie:
            logger.warning("Bilibili cookie 为空，无法获取收藏夹")
            return results

        if folder_id:
            folder_ids = [folder_id]
        else:
            folders = self._get_favorite_folders(cookie)
            if not folders:
                logger.info("未找到任何收藏夹")
                return results
            folder_ids = [f["id"] for f in folders]

        for fid in folder_ids:
            items = self._fetch_folder_items(cookie, fid, since, page, page_size)
            results.extend(items)

        return results

    def _fetch_folder_items(
        self,
        cookie: str,
        folder_id: int,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FavoriteVideoItem]:
        url = "https://api.bilibili.com/x/v3/fav/resource/list"
        items: List[FavoriteVideoItem] = []
        current_page = page

        while True:
            try:
                resp = requests.get(
                    url,
                    params={
                        "media_id": folder_id,
                        "pn": current_page,
                        "ps": page_size,
                        "platform": "web",
                    },
                    headers=self._headers(cookie),
                    timeout=15,
                )
                data = resp.json()
            except Exception as e:
                logger.warning(f"获取收藏夹 {folder_id} 第 {current_page} 页失败: {e}")
                break

            if data.get("code") != 0:
                logger.warning(f"收藏夹 API 返回错误: {data.get('message')}")
                break

            medias = data.get("data", {}).get("medias") or []
            if not medias:
                break

            for m in medias:
                fav_time = None
                if m.get("fav_time"):
                    try:
                        fav_time = datetime.fromtimestamp(m["fav_time"])
                    except Exception:
                        pass

                if since and fav_time and fav_time < since:
                    return items

                bvid = m.get("bvid", "")
                video_url = f"https://www.bilibili.com/video/{bvid}" if bvid else ""

                items.append(
                    FavoriteVideoItem(
                        video_id=bvid,
                        platform="bilibili",
                        title=m.get("title", ""),
                        url=video_url,
                        cover_url=m.get("cover", ""),
                        author=m.get("upper", {}).get("name", ""),
                        duration=m.get("duration", 0),
                        favorited_at=fav_time,
                        description=m.get("intro", ""),
                    )
                )

            has_more = data.get("data", {}).get("has_more", False)
            if not has_more:
                break
            current_page += 1

        return items
