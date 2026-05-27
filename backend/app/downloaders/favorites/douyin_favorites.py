import json
from datetime import datetime
from typing import List, Optional
from urllib.parse import quote, urlencode

import httpx
import requests

from app.downloaders.douyin_helper.abogus import ABogus
from app.downloaders.favorites.base import BaseFavoritesFetcher, FavoriteVideoItem
from app.utils.logger import get_logger

logger = get_logger(__name__)

DOUYIN_DOMAIN = "https://www.douyin.com"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class DouyinFavoritesFetcher(BaseFavoritesFetcher):

    def get_platform(self) -> str:
        return "douyin"

    def _headers(self, cookie: str) -> dict:
        return {
            "User-Agent": UA,
            "Referer": "https://www.douyin.com/",
            "Cookie": cookie,
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        }

    def _get_sec_uid(self, cookie: str) -> Optional[str]:
        url = f"{DOUYIN_DOMAIN}/aweme/v1/web/user/profile/other/"
        try:
            resp = requests.get(
                url,
                headers=self._headers(cookie),
                timeout=10,
            )
            data = resp.json()
            if data.get("status_code") == 0:
                return data.get("user", {}).get("sec_uid")
        except Exception:
            pass
        return None

    def fetch_favorites(
        self,
        cookie: str,
        since: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FavoriteVideoItem]:
        results: List[FavoriteVideoItem] = []

        if not cookie:
            logger.warning("Douyin cookie 为空，无法获取收藏列表")
            return results

        cursor = (page - 1) * page_size

        while True:
            params = {
                "device_platform": "webapp",
                "aid": "6383",
                "channel": "channel_pc_web",
                "pc_client_type": "1",
                "version_code": "290100",
                "version_name": "29.1.0",
                "cookie_enabled": "true",
                "platform": "PC",
                "downlink": "10",
                "effective_type": "4g",
                "count": str(page_size),
                "cursor": str(cursor),
            }

            try:
                bogus = ABogus()
                ab_value = bogus.get_value(params)
                a_bogus = quote(ab_value, safe="")
                query_str = urlencode(params)
                full_url = f"{DOUYIN_DOMAIN}/aweme/v1/web/aweme/favorite/?{query_str}&a_bogus={a_bogus}"

                resp = requests.get(full_url, headers=self._headers(cookie), timeout=15)
                data = resp.json()
            except Exception as e:
                logger.warning(f"获取抖音收藏列表失败: {e}")
                break

            if data.get("status_code") != 0:
                logger.warning(f"抖音收藏 API 返回错误: status_code={data.get('status_code')}")
                break

            aweme_list = data.get("aweme_list") or []
            if not aweme_list:
                break

            for item in aweme_list:
                fav_time = None
                create_time = item.get("create_time")
                if create_time:
                    try:
                        fav_time = datetime.fromtimestamp(create_time)
                    except Exception:
                        pass

                if since and fav_time and fav_time < since:
                    return results

                aweme_id = item.get("aweme_id", "")
                video_url = f"https://www.douyin.com/video/{aweme_id}" if aweme_id else ""

                results.append(
                    FavoriteVideoItem(
                        video_id=aweme_id,
                        platform="douyin",
                        title=item.get("desc", ""),
                        url=video_url,
                        cover_url=item.get("video", {}).get("cover", {}).get("url_list", [""])[0],
                        author=item.get("author", {}).get("nickname", ""),
                        duration=item.get("video", {}).get("duration", 0) // 1000 if item.get("video", {}).get("duration") else None,
                        favorited_at=fav_time,
                        description=item.get("desc", ""),
                    )
                )

            has_more = data.get("has_more", False)
            if not has_more:
                break
            cursor = data.get("cursor", cursor + page_size)

        return results
