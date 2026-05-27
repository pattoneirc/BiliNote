import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from app.db.monitor_dao import DailyDigestDAO, FavoriteVideoDAO
from app.gpt.base import GPT
from app.gpt.gpt_factory import GPTFactory
from app.models.model_config import ModelConfig
from app.services.provider import ProviderService
from app.utils.logger import get_logger

logger = get_logger(__name__)

DIGEST_OUTPUT_DIR = Path(os.getenv("DIGEST_OUTPUT_DIR", "digest_results"))
DIGEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DIGEST_SYSTEM_PROMPT = """你是一个专业的视频内容分析师。你的任务是根据用户当天收藏的多个视频的笔记摘要，生成一份结构清晰的每日视频收藏汇总文档。

要求：
1. 文档标题格式：# 📺 每日视频收藏汇总 - {date}
2. 按主题/领域对视频进行分类（如技术、生活、娱乐、学习等）
3. 每个视频包含：标题、作者、平台、一句话总结、关键要点（2-3条）
4. 在文档末尾添加「今日洞察」部分，总结今天收藏视频的整体趋势和亮点
5. 使用 Markdown 格式，结构清晰
6. 语言简洁专业"""


class DailyDigestService:

    @staticmethod
    def generate_daily_digest(
        target_date: Optional[str] = None,
        model_name: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> Optional[dict]:
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        start = date_obj.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)

        videos = FavoriteVideoDAO.get_by_date_range(start, end)
        if not videos:
            logger.info(f"{target_date} 没有收藏视频，跳过摘要生成")
            return None

        video_summaries = []
        for v in videos:
            summary = f"### {v.title}\n"
            summary += f"- **作者**: {v.author or '未知'}\n"
            summary += f"- **平台**: {v.platform}\n"
            summary += f"- **链接**: {v.url}\n"

            if v.task_id:
                note_path = Path("note_results") / f"{v.task_id}.json"
                if note_path.exists():
                    try:
                        with open(note_path, "r", encoding="utf-8") as f:
                            note_data = json.load(f)
                        markdown = note_data.get("markdown", "")
                        if markdown:
                            lines = markdown.split("\n")
                            key_points = []
                            for line in lines:
                                line = line.strip()
                                if line.startswith("- ") or line.startswith("* "):
                                    key_points.append(line)
                                    if len(key_points) >= 5:
                                        break
                            if key_points:
                                summary += "- **要点**:\n  " + "\n  ".join(key_points) + "\n"
                    except Exception as e:
                        logger.warning(f"读取笔记 {v.task_id} 失败: {e}")

            video_summaries.append(summary)

        combined = f"日期: {target_date}\n\n收藏视频数量: {len(videos)}\n\n"
        combined += "\n---\n\n".join(video_summaries)

        if not provider_id or not model_name:
            digest_markdown = DailyDigestService._build_manual_digest(target_date, videos, video_summaries)
        else:
            digest_markdown = DailyDigestService._build_ai_digest(
                target_date, combined, model_name, provider_id
            )

        file_path = DailyDigestService._save_digest_file(target_date, digest_markdown)

        digest_data = {
            "digest_date": target_date,
            "title": f"每日视频收藏汇总 - {target_date}",
            "markdown_content": digest_markdown,
            "video_count": len(videos),
            "platform": ",".join(set(v.platform for v in videos)),
            "file_path": file_path,
        }

        existing = DailyDigestDAO.get_by_date(target_date)
        if existing:
            DailyDigestDAO.update_content(
                existing[0].id, digest_markdown, len(videos), file_path
            )
            digest_data["id"] = existing[0].id
        else:
            obj = DailyDigestDAO.create(digest_data)
            digest_data["id"] = obj.id

        try:
            from app.services.notify_service import NotifyService
            NotifyService.notify_digest(
                digest_date=target_date,
                title=digest_data["title"],
                content=digest_markdown,
                video_count=len(videos),
            )
        except Exception as e:
            logger.warning(f"发送摘要通知失败（不影响摘要生成）: {e}")

        return digest_data

    @staticmethod
    def _build_manual_digest(
        target_date: str, videos, video_summaries: List[str]
    ) -> str:
        lines = [f"# 📺 每日视频收藏汇总 - {target_date}\n"]
        lines.append(f"> 共收藏 **{len(videos)}** 个视频\n")

        platform_counts = {}
        for v in videos:
            platform_counts[v.platform] = platform_counts.get(v.platform, 0) + 1
        platform_info = "、".join(f"{p} {c}个" for p, c in platform_counts.items())
        lines.append(f"> 平台分布：{platform_info}\n")
        lines.append("---\n")

        for summary in video_summaries:
            lines.append(summary)
            lines.append("\n---\n")

        lines.append("\n## 📝 今日洞察\n")
        lines.append(f"今天共收藏了 {len(videos)} 个视频，"
                      f"涵盖 {len(platform_counts)} 个平台。"
                      f"以上视频已自动完成笔记生成和内容分析。\n")

        return "\n".join(lines)

    @staticmethod
    def _build_ai_digest(
        target_date: str,
        combined_content: str,
        model_name: str,
        provider_id: str,
    ) -> str:
        try:
            provider = ProviderService.get_provider_by_id(provider_id)
            if not provider:
                logger.warning(f"供应商 {provider_id} 未找到，回退手动摘要")
                return f"# 📺 每日视频收藏汇总 - {target_date}\n\n{combined_content}"

            config = ModelConfig(
                api_key=provider["api_key"],
                base_url=provider["base_url"],
                model_name=model_name,
                provider=provider["type"],
                name=provider["name"],
            )
            gpt = GPTFactory().from_config(config)

            prompt = f"请根据以下 {target_date} 收藏的视频信息，生成一份每日视频收藏汇总文档：\n\n{combined_content}"

            from app.models.gpt_model import GPTSource
            source = GPTSource(
                title=f"每日视频收藏汇总 - {target_date}",
                segment=[],
                tags=[],
                style="简洁专业",
                extras=prompt,
            )
            result = gpt.summarize(source)
            return result or DailyDigestService._build_manual_digest.__func__(
                target_date, [], [combined_content]
            )
        except Exception as e:
            logger.error(f"AI 生成每日摘要失败: {e}")
            return f"# 📺 每日视频收藏汇总 - {target_date}\n\n{combined_content}"

    @staticmethod
    def _save_digest_file(target_date: str, content: str) -> str:
        file_name = f"digest_{target_date}.md"
        file_path = DIGEST_OUTPUT_DIR / file_name
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"每日摘要已保存: {file_path}")
        return str(file_path)

    @staticmethod
    def get_digest(digest_id: int) -> Optional[dict]:
        obj = DailyDigestDAO.get_by_id(digest_id)
        if not obj:
            return None
        return {
            "id": obj.id,
            "digest_date": obj.digest_date,
            "title": obj.title,
            "markdown_content": obj.markdown_content,
            "video_count": obj.video_count,
            "platform": obj.platform,
            "file_path": obj.file_path,
            "created_at": str(obj.created_at) if obj.created_at else None,
        }

    @staticmethod
    def list_digests(limit: int = 30) -> List[dict]:
        objs = DailyDigestDAO.get_all(limit)
        return [
            {
                "id": o.id,
                "digest_date": o.digest_date,
                "title": o.title,
                "video_count": o.video_count,
                "platform": o.platform,
                "file_path": o.file_path,
                "created_at": str(o.created_at) if o.created_at else None,
            }
            for o in objs
        ]
