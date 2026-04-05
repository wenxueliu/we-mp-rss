# Recommend 模块集成实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 recommend 项目的推荐功能集成到 we-mp-rss，包括内容源配置、推荐算法、用户交互、偏好学习和知识库管理。

**Architecture:** 作为 `core/recommend/` 独立模块集成，数据通过外键关联到现有 Article 表，API 通过 `/api/v1/wx/recommend/` 前缀暴露，前端新增 Vue 页面。

**Tech Stack:** Python/SQLAlchemy (后端), Vue 3/Element Plus (前端), SQLite (数据库)

---

## 阶段一：数据模型

### Task 1: 创建 core/recommend 目录结构

**Files:**
- Create: `core/recommend/__init__.py`
- Create: `core/recommend/models.py`

- [ ] **Step 1: Create directory and __init__.py**

```bash
mkdir -p core/recommend
touch core/recommend/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add core/recommend/__init__.py
git commit -m "feat: create core/recommend module"
```

### Task 2: 实现推荐数据模型

**Files:**
- Create: `core/recommend/models.py`

- [ ] **Step 1: 创建 base.py 引用和模型基类**

```python
# core/recommend/models.py
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, create_engine, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()
```

- [ ] **Step 2: 创建 RecommendSource 模型**

```python
class RecommendSource(Base):
    """内容源配置表"""
    __tablename__ = "recommend_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="源名称")
    source_type = Column(String(50), nullable=False, comment="源类型：rss, opencli, wechat")
    url = Column(String(500), nullable=False, comment="源 URL 或配置")
    enabled = Column(Boolean, default=True, comment="是否启用")
    config = Column(Text, nullable=True, comment="JSON 配置")
    fetch_interval = Column(Float, default=24.0, comment="抓取间隔（小时）")
    last_fetched_at = Column(DateTime, nullable=True, comment="最后抓取时间")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contents = relationship("RecommendContent", back_populates="source", cascade="all, delete-orphan")
```

- [ ] **Step 3: 创建 RecommendContent 模型**

```python
class RecommendContent(Base):
    """推荐内容映射表"""
    __tablename__ = "recommend_contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(255), nullable=True, comment="关联 Article 表的外键")
    source_id = Column(Integer, ForeignKey("recommend_sources.id"), nullable=False)
    source_type = Column(String(50), nullable=False, comment="来源类型")
    source_name = Column(String(100), nullable=True, comment="来源名称")
    title = Column(String(500), nullable=False, comment="标题")
    url = Column(String(1000), nullable=False, unique=True, comment="原文链接")
    description = Column(Text, nullable=True, comment="描述/摘要")
    author = Column(String(200), nullable=True, comment="作者")
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    thumbnail = Column(String(500), nullable=True, comment="缩略图")
    tags = Column(Text, nullable=True, comment="标签，JSON 数组")
    freshness_score = Column(Float, default=0.0, comment="新鲜度分数 0-100")
    recommendation_score = Column(Float, default=0.0, comment="推荐分数 0-100")
    status = Column(String(50), default="pending", comment="状态：pending, recommended, accepted, rejected")
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source = relationship("RecommendSource", back_populates="contents")
    interactions = relationship("RecommendInteraction", back_populates="content", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_content_status", "status"),
        Index("idx_content_url", "url"),
        Index("idx_content_source", "source_id"),
    )
```

- [ ] **Step 4: 创建 RecommendInteraction 模型**

```python
class RecommendInteraction(Base):
    """用户交互表"""
    __tablename__ = "recommend_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True, comment="用户 ID")
    content_id = Column(Integer, ForeignKey("recommend_contents.id"), nullable=False)
    action = Column(String(50), nullable=False, comment="操作类型：like, dislike, skip, view")
    weight = Column(Float, default=1.0, comment="操作权重")
    extra_data = Column(Text, nullable=True, comment="额外数据，JSON 格式")
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("RecommendContent", back_populates="interactions")

    __table_args__ = (
        Index("idx_interaction_user_content", "user_id", "content_id", unique=True),
        Index("idx_interaction_action", "action"),
    )
```

- [ ] **Step 5: 创建 RecommendPreference 模型**

```python
class RecommendPreference(Base):
    """用户偏好表"""
    __tablename__ = "recommend_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    topic_weights = Column(Text, default="{}", comment="主题权重 JSON")
    source_trust = Column(Text, default="{}", comment="来源信任度 JSON")
    preferred_length_min = Column(Integer, default=0, comment="偏好长度最小值")
    preferred_length_max = Column(Integer, default=10000, comment="偏好长度最大值")
    novelty_preference = Column(Float, default=0.5, comment="新鲜度偏好 0-1")
    quality_threshold = Column(Float, default=50.0, comment="质量阈值")
    blocked_topics = Column(Text, default="[]", comment="屏蔽主题 JSON 数组")
    blocked_sources = Column(Text, default="[]", comment="屏蔽来源 JSON 数组")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 6: 创建 RecommendKnowledge 模型**

```python
class RecommendKnowledge(Base):
    """知识库条目表"""
    __tablename__ = "recommend_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("recommend_contents.id"), nullable=False, unique=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    user_notes = Column(Text, nullable=True, comment="用户笔记")
    ai_summary = Column(Text, nullable=True, comment="AI 摘要")
    key_insights = Column(Text, nullable=True, comment="关键见解 JSON 数组")
    tags = Column(Text, nullable=True, comment="标签 JSON 数组")
    category = Column(String(100), nullable=True, comment="分类")
    access_count = Column(Integer, default=0, comment="访问次数")
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = relationship("RecommendContent")

    __table_args__ = (
        Index("idx_knowledge_user", "user_id"),
    )
```

- [ ] **Step 7: 创建 RecommendSourcePreset 模型**

```python
class RecommendSourcePreset(Base):
    """内容源预设表"""
    __tablename__ = "recommend_source_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="预设名称")
    platform = Column(String(50), nullable=False, comment="平台名称")
    command = Column(String(50), nullable=False, comment="命令")
    limit = Column(Integer, default=10, comment="数量")
    fetch_interval = Column(Float, default=24.0, comment="抓取间隔（小时）")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 8: 创建数据库初始化函数**

```python
def init_recommend_db(database_url: str):
    """初始化推荐模块数据库"""
    engine = create_engine(database_url, echo=False)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal
```

- [ ] **Step 9: Commit**

```bash
git add core/recommend/models.py
git commit -m "feat: add recommend data models

Add 6 tables:
- RecommendSource: content source configuration
- RecommendContent: content mapping with scores
- RecommendInteraction: user interactions
- RecommendPreference: user preferences
- RecommendKnowledge: knowledge base entries
- RecommendSourcePreset: platform presets

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段二：推荐引擎

### Task 3: 移植推荐引擎

**Files:**
- Create: `core/recommend/engine.py`

- [ ] **Step 1: 创建 engine.py 文件结构**

```python
# core/recommend/engine.py
"""推荐引擎模块"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class RecommendationResult:
    """推荐结果"""
    content_id: int
    title: str
    url: str
    score: float
    freshness: float
    preference_match: float
    quality: float
    timeliness: float
    reason: str
```

- [ ] **Step 2: 实现 RecommenderEngine 类**

```python
class RecommenderEngine:
    """推荐引擎"""

    def __init__(
        self,
        freshness_weight: float = 0.4,
        preference_weight: float = 0.3,
        quality_weight: float = 0.2,
        timeliness_weight: float = 0.1,
    ):
        self.freshness_weight = freshness_weight
        self.preference_weight = preference_weight
        self.quality_weight = quality_weight
        self.timeliness_weight = timeliness_weight

    def calculate_score(
        self,
        content: Any,
        user_preferences: Dict[str, Any],
        similarity_scores: List[float] = None,
    ) -> RecommendationResult:
        # 计算新鲜度
        freshness = self._calculate_freshness(content, similarity_scores or [])
        # 计算偏好匹配
        preference_match = self._calculate_preference_match(content, user_preferences)
        # 计算质量
        quality = self._calculate_quality(content)
        # 计算时效性
        timeliness = self._calculate_timeliness(content)
        # 综合分数
        score = (
            freshness * self.freshness_weight
            + preference_match * self.preference_weight
            + quality * self.quality_weight
            + timeliness * self.timeliness_weight
        )
        # 生成推荐理由
        reason = self._generate_reason(freshness, preference_match, quality, timeliness, content)

        return RecommendationResult(
            content_id=content.id if hasattr(content, "id") else 0,
            title=content.title if hasattr(content, "title") else "",
            url=content.url if hasattr(content, "url") else "",
            score=round(score, 2),
            freshness=round(freshness, 2),
            preference_match=round(preference_match, 2),
            quality=round(quality, 2),
            timeliness=round(timeliness, 2),
            reason=reason,
        )
```

- [ ] **Step 3: 实现 _calculate_freshness 方法**

```python
def _calculate_freshness(self, content: Any, similarity_scores: List[float] = None) -> float:
    """计算新鲜度分数"""
    freshness = 50.0
    if similarity_scores:
        max_similarity = max(similarity_scores) if similarity_scores else 0
        freshness = freshness - (max_similarity * 30)
    created_at = getattr(content, "published_at", None) or getattr(content, "created_at", None)
    if created_at:
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = None
        if created_at:
            now = datetime.utcnow()
            if created_at.tzinfo:
                now = now.replace(tzinfo=created_at.tzinfo)
            days_old = (now - created_at).days
            if days_old <= 7:
                freshness += 40
            elif days_old <= 30:
                freshness += 20
            elif days_old <= 90:
                freshness -= 10
            else:
                freshness -= 30
    return max(0.0, min(100.0, freshness))
```

- [ ] **Step 4: 实现 _calculate_preference_match 方法**

```python
def _calculate_preference_match(self, content: Any, user_preferences: Dict[str, Any]) -> float:
    """计算偏好匹配分数"""
    score = 50.0
    topic_weights = user_preferences.get("topic_weights", {})
    if topic_weights and hasattr(content, "tags"):
        tags = content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        for tag in tags:
            if tag in topic_weights:
                score += topic_weights[tag] * 0.5
    blocked_topics = user_preferences.get("blocked_topics", [])
    if blocked_topics and hasattr(content, "tags"):
        tags = content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        for tag in tags:
            if tag in blocked_topics:
                return 0.0
    return max(0.0, min(100.0, score))
```

- [ ] **Step 5: 实现 _calculate_quality 方法**

```python
def _calculate_quality(self, content: Any) -> float:
    """计算内容质量分数"""
    score = 50.0
    title = getattr(content, "title", "")
    if title:
        title_len = len(title)
        if 20 <= title_len <= 100:
            score += 15
        elif 10 <= title_len <= 150:
            score += 10
    description = getattr(content, "description", "")
    if description and len(description) > 50:
        score += 15
    author = getattr(content, "author", "")
    if author:
        score += 10
    thumbnail = getattr(content, "thumbnail", "")
    if thumbnail:
        score += 10
    return max(0.0, min(100.0, score))
```

- [ ] **Step 6: 实现 _calculate_timeliness 方法**

```python
def _calculate_timeliness(self, content: Any) -> float:
    """计算时效性分数"""
    published_at = getattr(content, "published_at", None)
    if not published_at:
        return 50.0
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at)
        except:
            return 50.0
    now = datetime.utcnow()
    if published_at.tzinfo:
        now = now.replace(tzinfo=published_at.tzinfo)
    days_old = (now - published_at).days
    if days_old <= 0:
        return 100.0
    elif days_old <= 7:
        return 100.0 - (days_old * 5)
    elif days_old <= 30:
        return 65.0 - ((days_old - 7) * 1.5)
    else:
        return max(0.0, 30.0 - ((days_old - 30) * 0.5))
```

- [ ] **Step 7: 实现 _generate_reason 方法**

```python
def _generate_reason(self, freshness: float, preference_match: float, quality: float, timeliness: float, content: Any) -> str:
    """生成推荐理由"""
    reasons = []
    if freshness >= 80:
        reasons.append("高度新鲜的内容")
    elif freshness >= 60:
        reasons.append("较为新颖")
    if preference_match >= 70:
        reasons.append("符合您的兴趣")
    elif preference_match >= 50:
        reasons.append("可能感兴趣")
    if quality >= 70:
        reasons.append("内容质量高")
    if timeliness >= 80:
        reasons.append("最新发布")
    elif timeliness >= 60:
        reasons.append("时效性好")
    if not reasons:
        reasons.append("推荐给您")
    return " | ".join(reasons)
```

- [ ] **Step 8: 实现 update_user_preferences 方法**

```python
def update_user_preferences(
    self,
    current_preferences: Dict[str, Any],
    content: Any,
    action: str,
    learning_rate: float = 0.1,
) -> Dict[str, Any]:
    """根据用户行为更新偏好"""
    preferences = current_preferences.copy()
    tags = []
    if hasattr(content, "tags") and content.tags:
        tags = content.tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        if not isinstance(tags, list):
            tags = []
    if "topic_weights" not in preferences:
        preferences["topic_weights"] = {}
    topic_weights = preferences["topic_weights"]
    if action == "like":
        for tag in tags:
            current = topic_weights.get(tag, 50.0)
            topic_weights[tag] = current * (1 - learning_rate) + 100 * learning_rate
    elif action == "dislike":
        for tag in tags:
            current = topic_weights.get(tag, 50.0)
            topic_weights[tag] = current * (1 - learning_rate) + 0 * learning_rate
    elif action == "skip":
        for tag in tags:
            current = topic_weights.get(tag, 50.0)
            topic_weights[tag] = current * (1 - learning_rate * 0.5) + 25 * learning_rate * 0.5
    preferences["topic_weights"] = topic_weights
    return preferences
```

- [ ] **Step 9: Commit**

```bash
git add core/recommend/engine.py
git commit -m "feat: add recommend engine with scoring algorithm

Implements recommendation scoring based on:
- Freshness (40%): content age and uniqueness
- Preference match (30%): topic weights and blacklist
- Quality (20%): title length, description, author, thumbnail
- Timeliness (10%): publication date decay

Includes preference learning (like/dislike/skip).

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段三：内容采集器

### Task 4: 实现采集器基类和 RSS 采集器

**Files:**
- Create: `core/recommend/collectors.py`

- [ ] **Step 1: 创建采集器基类**

```python
# core/recommend/collectors.py
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
        formats = [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
```

- [ ] **Step 2: 实现 RSSCollector**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add core/recommend/collectors.py
git commit -m "feat: add RSS collector for content fetching

Implement BaseCollector abstract class and RSSCollector.
RSSCollector can parse RSS/Atom feeds and extract:
- Title, URL, description
- Author, publication date
- Thumbnail images
- Tags/categories

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

### Task 5: 实现 OpenCLI 采集器

**Files:**
- Modify: `core/recommend/collectors.py`

- [ ] **Step 1: 添加 OpenCLI 采集器**

```python
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
        # 简单实现：调用 opencli-rs CLI
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
```

- [ ] **Step 2: Commit**

```bash
git add core/recommend/collectors.py
git commit -m "feat: add OpenCLI collector for social platforms

Support platforms: hackernews, reddit, bilibili, zhihu, youtube,
twitter, devto, lobsters, stackoverflow

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段四：API 路由

### Task 6: 实现推荐 API 路由

**Files:**
- Create: `apis/recommend.py`

- [ ] **Step 1: 创建 API 路由文件基础结构**

```python
# apis/recommend.py
"""推荐模块 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

router = APIRouter(prefix="/recommend", tags=["推荐"])

# Pydantic 模型
class InteractRequest(BaseModel):
    action: str = Field(..., description="操作类型：like, dislike, skip, view")

class PreferencesUpdateRequest(BaseModel):
    topic_weights: Optional[Dict[str, float]] = None
    blocked_topics: Optional[List[str]] = None
    preferred_length_min: Optional[int] = None
    preferred_length_max: Optional[int] = None
    novelty_preference: Optional[float] = None
    quality_threshold: Optional[float] = None

class SourceCreateRequest(BaseModel):
    name: str
    source_type: str
    url: str
    enabled: bool = True
    config: Optional[str] = None
    fetch_interval: float = 24.0

class SourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[str] = None
    fetch_interval: Optional[float] = None
```

- [ ] **Step 2: 实现 contents 列表接口**

```python
class ContentResponse(BaseModel):
    id: int
    article_id: Optional[str]
    title: str
    url: str
    description: Optional[str]
    thumbnail: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    tags: List[str]
    recommendation_score: float
    freshness: float
    preference_match: float
    quality: float
    timeliness: float
    reason: str
    source_type: str
    source_name: Optional[str]

@router.get("/contents")
async def get_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    source_type: Optional[str] = None,
):
    """获取推荐内容列表"""
    # TODO: 实现数据库查询
    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        },
    }
```

- [ ] **Step 3: 实现 interact 接口**

```python
@router.post("/contents/{content_id}/interact")
async def interact(content_id: int, request: InteractRequest):
    """用户交互"""
    # TODO: 实现交互记录和偏好更新
    return {
        "code": 0,
        "message": "success",
        "data": {
            "preferences_updated": True,
        },
    }
```

- [ ] **Step 4: 实现 preferences 接口**

```python
@router.get("/preferences")
async def get_preferences():
    """获取用户偏好"""
    # TODO: 实现偏好查询
    return {
        "code": 0,
        "message": "success",
        "data": {
            "topic_weights": {},
            "source_trust": {},
            "blocked_topics": [],
            "blocked_sources": [],
            "preferred_length_min": 0,
            "preferred_length_max": 10000,
            "novelty_preference": 0.5,
            "quality_threshold": 50.0,
        },
    }

@router.put("/preferences")
async def update_preferences(request: PreferencesUpdateRequest):
    """更新用户偏好"""
    # TODO: 实现偏好更新
    return {"code": 0, "message": "success", "data": {}}
```

- [ ] **Step 5: 实现 knowledge 接口**

```python
@router.get("/knowledge")
async def get_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
):
    """获取知识库列表"""
    # TODO: 实现知识库查询
    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": [],
            "total": 0,
        },
    }

@router.post("/knowledge")
async def save_to_knowledge(content_id: int):
    """保存到知识库"""
    # TODO: 实现保存
    return {"code": 0, "message": "success", "data": {}}

@router.delete("/knowledge/{knowledge_id}")
async def delete_from_knowledge(knowledge_id: int):
    """从知识库删除"""
    # TODO: 实现删除
    return {"code": 0, "message": "success", "data": {}}
```

- [ ] **Step 6: 实现 sources 接口**

```python
@router.get("/sources")
async def get_sources():
    """获取内容源列表"""
    # TODO: 实现源列表查询
    return {"code": 0, "message": "success", "data": {"items": []}}

@router.post("/sources")
async def create_source(request: SourceCreateRequest):
    """创建内容源"""
    # TODO: 实现创建
    return {"code": 0, "message": "success", "data": {}}

@router.get("/sources/{source_id}")
async def get_source(source_id: int):
    """获取内容源详情"""
    # TODO: 实现详情查询
    return {"code": 0, "message": "success", "data": {}}

@router.put("/sources/{source_id}")
async def update_source(source_id: int, request: SourceUpdateRequest):
    """更新内容源"""
    # TODO: 实现更新
    return {"code": 0, "message": "success", "data": {}}

@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    """删除内容源"""
    # TODO: 实现删除
    return {"code": 0, "message": "success", "data": {}}

@router.post("/sources/{source_id}/fetch")
async def fetch_source(source_id: int):
    """手动抓取内容"""
    # TODO: 实现抓取
    return {"code": 0, "message": "success", "data": {}}

@router.post("/sources/fetch-all")
async def fetch_all_sources():
    """抓取所有启用的源"""
    # TODO: 实现批量抓取
    return {"code": 0, "message": "success", "data": {}}
```

- [ ] **Step 7: 实现 presets 接口**

```python
@router.get("/presets")
async def get_presets():
    """获取平台预设列表"""
    # TODO: 实现预设查询
    return {"code": 0, "message": "success", "data": {"items": []}}

@router.post("/presets")
async def create_preset(request: SourceCreateRequest):
    """创建预设"""
    # TODO: 实现预设创建
    return {"code": 0, "message": "success", "data": {}}
```

- [ ] **Step 8: 在 main.py 中注册路由**

```python
# 在 web.py 的 api_router 注册处添加
from apis.recommend import router as recommend_router

# 在 api_router 注册后添加
api_router.include_router(recommend_router)
```

- [ ] **Step 9: Commit**

```bash
git add apis/recommend.py
git commit -m "feat: add recommend API routes

Endpoints:
- GET/POST /recommend/contents
- POST /recommend/contents/{id}/interact
- GET/PUT /recommend/preferences
- GET/POST/DELETE /recommend/knowledge
- GET/POST/PUT/DELETE /recommend/sources
- POST /recommend/sources/{id}/fetch
- POST /recommend/sources/fetch-all
- GET/POST /recommend/presets

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段五：前端页面

### Task 7: 创建前端 API 调用模块

**Files:**
- Create: `web_ui/src/api/recommend.ts`

- [ ] **Step 1: 创建 API 模块**

```typescript
// web_ui/src/api/recommend.ts
import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1/wx",
});

export const recommendApi = {
  // 内容列表
  getContents(params: {
    page?: number;
    page_size?: number;
    status?: string;
    source_type?: string;
  }) {
    return api.get("/recommend/contents", { params });
  },

  // 用户交互
  interact(contentId: number, action: "like" | "dislike" | "skip" | "view") {
    return api.post(`/recommend/contents/${contentId}/interact`, { action });
  },

  // 偏好
  getPreferences() {
    return api.get("/recommend/preferences");
  },

  updatePreferences(data: any) {
    return api.put("/recommend/preferences", data);
  },

  // 知识库
  getKnowledge(params?: { page?: number; page_size?: number; category?: string }) {
    return api.get("/recommend/knowledge", { params });
  },

  saveToKnowledge(contentId: number) {
    return api.post("/recommend/knowledge", { content_id: contentId });
  },

  deleteFromKnowledge(knowledgeId: number) {
    return api.delete(`/recommend/knowledge/${knowledgeId}`);
  },

  // 内容源
  getSources() {
    return api.get("/recommend/sources");
  },

  createSource(data: any) {
    return api.post("/recommend/sources", data);
  },

  updateSource(sourceId: number, data: any) {
    return api.put(`/recommend/sources/${sourceId}`, data);
  },

  deleteSource(sourceId: number) {
    return api.delete(`/recommend/sources/${sourceId}`);
  },

  fetchSource(sourceId: number) {
    return api.post(`/recommend/sources/${sourceId}/fetch`);
  },

  fetchAllSources() {
    return api.post("/recommend/sources/fetch-all");
  },

  // 预设
  getPresets() {
    return api.get("/recommend/presets");
  },

  createPreset(data: any) {
    return api.post("/recommend/presets", data);
  },
};
```

- [ ] **Step 2: Commit**

```bash
git add web_ui/src/api/recommend.ts
git commit -m "feat: add recommend API client for frontend

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

### Task 8: 创建推荐卡片组件

**Files:**
- Create: `web_ui/src/components/RecommendationCard.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <el-card class="recommendation-card" :body-style="{ padding: '0px' }">
    <div class="card-content">
      <div class="thumbnail" v-if="item.thumbnail">
        <img :src="item.thumbnail" :alt="item.title" />
      </div>
      <div class="info">
        <h3 class="title">{{ item.title }}</h3>
        <p class="description" v-if="item.description">{{ item.description }}</p>
        <div class="meta">
          <span class="author" v-if="item.author">{{ item.author }}</span>
          <span class="source" v-if="item.source_name">{{ item.source_name }}</span>
          <span class="date" v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
        </div>
        <div class="scores">
          <el-tag type="primary">推荐 {{ item.recommendation_score }}</el-tag>
          <el-tag type="info">新鲜 {{ item.freshness }}</el-tag>
          <el-tag type="success">偏好 {{ item.preference_match }}</el-tag>
        </div>
        <p class="reason" v-if="item.reason">{{ item.reason }}</p>
        <div class="actions">
          <el-button type="primary" size="small" @click="handleInteract('like')">
            👍 喜欢
          </el-button>
          <el-button type="danger" size="small" @click="handleInteract('dislike')">
            👎 不感兴趣
          </el-button>
          <el-button size="small" @click="handleInteract('skip')">⏭️ 跳过</el-button>
          <el-button size="small" @click="openUrl(item.url)">🔗 阅读原文</el-button>
          <el-button type="success" size="small" @click="handleSave">📚 收藏</el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { recommendApi } from "../api/recommend";

const props = defineProps<{
  item: {
    id: number;
    title: string;
    url: string;
    description?: string;
    thumbnail?: string;
    author?: string;
    source_name?: string;
    published_at?: string;
    recommendation_score: number;
    freshness: number;
    preference_match: number;
    quality: number;
    timeliness: number;
    reason?: string;
  };
}>();

const handleInteract = async (action: string) => {
  await recommendApi.interact(props.item.id, action);
};

const handleSave = async () => {
  await recommendApi.saveToKnowledge(props.item.id);
};

const openUrl = (url: string) => {
  window.open(url, "_blank");
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString("zh-CN");
};
</script>

<style scoped>
.recommendation-card {
  margin-bottom: 16px;
}
.card-content {
  display: flex;
}
.thumbnail img {
  width: 200px;
  height: 150px;
  object-fit: cover;
}
.info {
  padding: 16px;
  flex: 1;
}
.title {
  margin: 0 0 8px 0;
}
.description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
}
.meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}
.meta span {
  margin-right: 12px;
}
.scores {
  margin-bottom: 8px;
}
.scores .el-tag {
  margin-right: 8px;
}
.reason {
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}
.actions .el-button {
  margin-right: 8px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add web_ui/src/components/RecommendationCard.vue
git commit -m "feat: add RecommendationCard component

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

### Task 9: 创建推荐列表页

**Files:**
- Create: `web_ui/src/views/RecommendView.vue`

- [ ] **Step 1: 创建推荐列表页**

```vue
<template>
  <div class="recommend-view">
    <el-header>
      <h2>推荐内容</h2>
      <div class="filters">
        <el-select v-model="filterStatus" placeholder="状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="推荐" value="recommended" />
          <el-option label="已接受" value="accepted" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button @click="loadContents">刷新</el-button>
      </div>
    </el-header>
    <el-main>
      <div v-loading="loading">
        <RecommendationCard
          v-for="item in contents"
          :key="item.id"
          :item="item"
        />
        <el-empty v-if="!loading && contents.length === 0" description="暂无推荐内容" />
      </div>
      <el-pagination
        v-if="total > 0"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadContents"
      />
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { recommendApi } from "../api/recommend";
import RecommendationCard from "../components/RecommendationCard.vue";

const loading = ref(false);
const contents = ref<any[]>([]);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const filterStatus = ref("");

const loadContents = async () => {
  loading.value = true;
  try {
    const res = await recommendApi.getContents({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
    });
    contents.value = res.data.data.items;
    total.value = res.data.data.total;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadContents();
});
</script>

<style scoped>
.recommend-view {
  padding: 20px;
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add web_ui/src/views/RecommendView.vue
git commit -m "feat: add RecommendView page

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

### Task 10: 创建知识库页

**Files:**
- Create: `web_ui/src/views/KnowledgeView.vue`

- [ ] **Step 1: 创建知识库页**

```vue
<template>
  <div class="knowledge-view">
    <el-header>
      <h2>知识库</h2>
    </el-header>
    <el-main>
      <el-table :data="items" v-loading="loading">
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="category" label="分类" />
        <el-table-column prop="tags" label="标签">
          <template #default="{ row }">
            <el-tag v-for="tag in JSON.parse(row.tags || '[]')" :key="tag" size="small">
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="access_count" label="访问次数" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="openUrl(row.url)">查看</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="total > 0"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadKnowledge"
      />
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { recommendApi } from "../api/recommend";
import { ElMessage } from "element-plus";

const loading = ref(false);
const items = ref<any[]>([]);
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

const loadKnowledge = async () => {
  loading.value = true;
  try {
    const res = await recommendApi.getKnowledge({ page: page.value, page_size: pageSize.value });
    items.value = res.data.data.items;
    total.value = res.data.data.total;
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (id: number) => {
  await recommendApi.deleteFromKnowledge(id);
  ElMessage.success("已删除");
  loadKnowledge();
};

const openUrl = (url: string) => {
  window.open(url, "_blank");
};

onMounted(() => {
  loadKnowledge();
});
</script>
```

- [ ] **Step 2: Commit**

```bash
git add web_ui/src/views/KnowledgeView.vue
git commit -m "feat: add KnowledgeView page

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

### Task 11: 创建内容源管理页

**Files:**
- Create: `web_ui/src/views/SourcesView.vue`

- [ ] **Step 1: 创建内容源管理页**

```vue
<template>
  <div class="sources-view">
    <el-header>
      <h2>内容源管理</h2>
      <el-button type="primary" @click="showAddDialog = true">添加内容源</el-button>
    </el-header>
    <el-main>
      <el-table :data="sources" v-loading="loading">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="source_type" label="类型">
          <template #default="{ row }">
            <el-tag>{{ row.source_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column prop="enabled" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_fetched_at" label="最后抓取">
          <template #default="{ row }">
            {{ row.last_fetched_at ? formatDate(row.last_fetched_at) : "从未" }}
          </template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="handleFetch(row.id)">抓取</el-button>
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-main>

    <el-dialog v-model="showAddDialog" title="添加内容源">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.source_type">
            <el-option label="RSS" value="rss" />
            <el-option label="OpenCLI" value="opencli" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL/配置">
          <el-input v-model="form.url" placeholder="RSS URL 或 opencli 配置如 hackernews:top:10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { recommendApi } from "../api/recommend";
import { ElMessage } from "element-plus";

const loading = ref(false);
const sources = ref<any[]>([]);
const showAddDialog = ref(false);
const form = ref({ name: "", source_type: "rss", url: "" });

const loadSources = async () => {
  loading.value = true;
  try {
    const res = await recommendApi.getSources();
    sources.value = res.data.data.items;
  } finally {
    loading.value = false;
  }
};

const handleAdd = async () => {
  await recommendApi.createSource(form.value);
  ElMessage.success("添加成功");
  showAddDialog.value = false;
  loadSources();
};

const handleFetch = async (id: number) => {
  await recommendApi.fetchSource(id);
  ElMessage.success("抓取任务已启动");
};

const handleEdit = (row: any) => {
  // TODO: 实现编辑
};

const handleDelete = async (id: number) => {
  await recommendApi.deleteSource(id);
  ElMessage.success("已删除");
  loadSources();
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

onMounted(() => {
  loadSources();
});
</script>
```

- [ ] **Step 2: Commit**

```bash
git add web_ui/src/views/SourcesView.vue
git commit -m "feat: add SourcesView page

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段六：配置集成

### Task 12: 添加配置项

**Files:**
- Modify: `config.example.yaml`

- [ ] **Step 1: 添加推荐模块配置**

```yaml
# 推荐模块配置
recommend:
  enabled: true
  # 评分权重
  freshness_weight: 0.4
  preference_weight: 0.3
  quality_weight: 0.2
  timeliness_weight: 0.1
  # 定时任务
  auto_fetch: true
  fetch_interval_hours: 6
  # 偏好学习
  learning_rate: 0.1
```

- [ ] **Step 2: Commit**

```bash
git add config.example.yaml
git commit -m "feat: add recommend module config

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 阶段七：数据迁移

### Task 13: 数据库初始化

**Files:**
- Modify: `core/config.py`

- [ ] **Step 1: 在 core/config.py 中添加 recommend 配置项**

```python
# 在配置类中添加
recommend_freshness_weight: float = 0.4
recommend_preference_weight: float = 0.3
recommend_quality_weight: float = 0.2
recommend_timeliness_weight: float = 0.1
recommend_auto_fetch: bool = True
recommend_fetch_interval_hours: float = 6.0
recommend_learning_rate: float = 0.1
```

- [ ] **Step 2: 创建数据库迁移脚本**

```bash
# 创建 migrations 目录下的迁移文件
touch migrations/xxxx_recommend_init.py
```

- [ ] **Step 3: Commit**

```bash
git add core/config.py
git commit -m "feat: add recommend config options

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## 实现顺序

1. **Task 1**: 创建 core/recommend 目录结构
2. **Task 2**: 实现推荐数据模型
3. **Task 3**: 移植推荐引擎
4. **Task 4**: 实现 RSS 采集器
5. **Task 5**: 实现 OpenCLI 采集器
6. **Task 6**: 实现推荐 API 路由
7. **Task 7**: 创建前端 API 调用模块
8. **Task 8**: 创建推荐卡片组件
9. **Task 9**: 创建推荐列表页
10. **Task 10**: 创建知识库页
11. **Task 11**: 创建内容源管理页
12. **Task 12**: 添加配置项
13. **Task 13**: 数据库初始化

---

## 依赖项

新增 Python 依赖（添加到 requirements.txt）：
- feedparser>=5.2.1

前端依赖（检查是否已存在）：
- axios (检查 web_ui/package.json)
