"""内容采集器模块"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import re


@dataclass
class ContentItem:
    """内容项"""
    title: str
    url: str
    description: str = ""
    author: str = ""
    published_at: Optional[datetime] = None
    thumbnail: str = ""
    tags: List[str] = None
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.raw_data is None:
            self.raw_data = {}


class BaseCollector(ABC):
    """采集器基类"""

    def __init__(self, max_items: int = 20, config: Dict[str, Any] = None):
        self.max_items = max_items
        self.config = config or {}

    @abstractmethod
    def get_source_type(self) -> str:
        """获取源类型"""
        pass

    @abstractmethod
    async def fetch(self, source_url: str) -> List[ContentItem]:
        """抓取内容"""
        pass

    def validate_item(self, item: ContentItem) -> bool:
        """验证内容项是否有效"""
        return bool(item.title and item.url)

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None


class RSSCollector(BaseCollector):
    """RSS 源采集器"""

    def get_source_type(self) -> str:
        return "rss"

    async def fetch(self, source_url: str) -> List[ContentItem]:
        import feedparser
        try:
            feed = feedparser.parse(source_url)
            items = []
            for entry in feed.entries[: self.max_items]:
                item = self._parse_entry(entry)
                if self.validate_item(item):
                    items.append(item)
            return items
        except Exception as e:
            print(f"RSS 采集错误：{e}")
            return []

    def _parse_entry(self, entry) -> ContentItem:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        description = getattr(entry, "summary", "") or getattr(entry, "description", "")
        author = getattr(entry, "author", "") or entry.get("dc_creator", "")
        date_str = getattr(entry, "published", "") or getattr(entry, "updated", "") or getattr(entry, "created", "")
        published_at = self.parse_date(date_str) if date_str else None
        thumbnail = self._extract_thumbnail(entry)
        tags = self._extract_tags(entry)
        return ContentItem(
            title=title,
            url=link,
            description=self._clean_html(description),
            author=author,
            published_at=published_at,
            thumbnail=thumbnail,
            tags=tags,
            raw_data=dict(entry),
        )

    def _extract_thumbnail(self, entry) -> Optional[str]:
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url", "")
        if hasattr(entry, "media_content"):
            for content in entry.media_content:
                if content.get("url"):
                    return content["url"]
        if hasattr(entry, "enclosures"):
            for enclosure in entry.enclosures:
                if enclosure.type.startswith("image/"):
                    return enclosure.href
        content_html = entry.get("content", [{}])[0].get("value", "") or entry.get("description", "")
        if content_html:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
            if img_match:
                return img_match.group(1)
        return None

    def _extract_tags(self, entry) -> List[str]:
        tags = []
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if hasattr(tag, "term"):
                    tags.append(tag.term)
        dc_subject = entry.get("dc_subject", "")
        if dc_subject:
            tags.append(dc_subject)
        category = entry.get("category", "")
        if category and category not in tags:
            tags.append(category)
        return [tag.strip() for tag in tags if tag and tag.strip()]

    def _clean_html(self, text: str) -> str:
        if not text:
            return ""
        clean_text = re.sub(r"<[^>]+>", "", text)
        clean_text = clean_text.replace("&nbsp;", " ").replace("&amp;", "&")
        clean_text = clean_text.replace("&lt;", "<").replace("&gt;", ">")
        clean_text = clean_text.replace("&quot;", '"').replace("&#39;", "'")
        return " ".join(clean_text.split())


class OpenCLICollector(BaseCollector):
    """opencli-rs 采集器"""

    SUPPORTED_PLATFORMS = {
        "hackernews": ["top", "new", "best", "ask", "show", "job"],
        "reddit": ["hot", "new", "top", "rising"],
        "bilibili": ["hot", "new", "week", "month"],
        "zhihu": ["hot", "new"],
        "youtube": ["trending", "hot"],
        "twitter": ["home", "user", "search", "trending"],
        "devto": ["top", "recent"],
        "lobsters": ["hot", "new", "top"],
        "stackoverflow": ["questions", "questions tagged"],
    }

    def get_source_type(self) -> str:
        return "opencli"

    def _parse_source_url(self, source_url: str) -> Dict[str, Any]:
        if source_url.startswith("{"):
            return json.loads(source_url)
        parts = source_url.split(":")
        if len(parts) < 2:
            raise ValueError(f"无效的 opencli 源配置: {source_url}")
        platform = parts[0]
        command = parts[1]
        limit = int(parts[2]) if len(parts) > 2 else 10
        return {"platform": platform, "command": command, "limit": limit}

    async def fetch(self, source_url: str) -> List[ContentItem]:
        config = self._parse_source_url(source_url)
        platform = config["platform"]
        command = config["command"]
        limit = config["limit"]
        try:
            import subprocess
            result = subprocess.run(
                ["opencli-rs", platform, command, "--limit", str(limit)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            return self._parse_items(data)
        except Exception as e:
            print(f"OpenCLI 采集错误：{e}")
            return []

    def _parse_items(self, data: List[Dict]) -> List[ContentItem]:
        items = []
        for item in data[: self.max_items]:
            items.append(ContentItem(
                title=item.get("title", ""),
                url=item.get("url", ""),
                description=item.get("description", "") or item.get("summary", ""),
                author=item.get("author", "") or item.get("user", ""),
                published_at=self.parse_date(item.get("published_at", "")),
                thumbnail=item.get("thumbnail", "") or item.get("image", ""),
                tags=item.get("tags", []) or [],
                raw_data=item,
            ))
        return items