from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, create_engine, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


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


class RecommendKnowledge(Base):
    """知识库条目表"""
    __tablename__ = "recommend_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("recommend_contents.id"), nullable=False, unique=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
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


def init_recommend_db(database_url: str):
    """初始化推荐模块数据库"""
    engine = create_engine(database_url, echo=False)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return SessionLocal