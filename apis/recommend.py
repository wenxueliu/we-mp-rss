"""推荐模块 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from core.db import DB
from core.recommend.models import (
    RecommendSource, RecommendContent, RecommendInteraction,
    RecommendPreference, RecommendKnowledge, RecommendSourcePreset
)
from core.recommend.engine import RecommenderEngine, calculate_content_status
from core.recommend.collectors import RSSCollector, OpenCLICollector, WechatCollector, ContentItem
from core.queue import ContentTaskQueue
from apis.base import success_response, error_response
from core.auth import get_current_user

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


def get_session():
    return DB.get_session()


@router.get("/contents")
async def get_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    session=Depends(get_session),
):
    """获取推荐内容列表"""
    query = session.query(RecommendContent).filter(RecommendContent.is_processed == False)
    if status:
        query = query.filter(RecommendContent.status == status)
    if source_type:
        query = query.filter(RecommendContent.source_type == source_type)

    total = query.count()
    contents = query.order_by(RecommendContent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    engine = RecommenderEngine()
    for c in contents:
        # 获取用户偏好
        prefs = session.query(RecommendPreference).first()
        user_prefs = {
            "topic_weights": json.loads(prefs.topic_weights) if prefs and prefs.topic_weights else {},
            "blocked_topics": json.loads(prefs.blocked_topics) if prefs and prefs.blocked_topics else [],
        }
        result = engine.calculate_score(c, user_prefs)
        items.append({
            "id": c.id,
            "article_id": c.article_id,
            "title": c.title,
            "url": c.url,
            "description": c.description,
            "thumbnail": c.thumbnail,
            "author": c.author,
            "published_at": (c.published_at or c.created_at).isoformat() if (c.published_at or c.created_at) else None,
            "tags": json.loads(c.tags) if c.tags else [],
            "recommendation_score": result.score,
            "freshness": result.freshness,
            "preference_match": result.preference_match,
            "quality": result.quality,
            "timeliness": result.timeliness,
            "reason": result.reason,
            "source_type": c.source_type,
            "source_name": c.source_name,
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/contents/{content_id}/interact")
async def interact(content_id: int, request: InteractRequest, session=Depends(get_session)):
    """用户交互"""
    content = session.query(RecommendContent).filter(RecommendContent.id == content_id).first()
    if not content:
        return error_response(404, "内容不存在")

    user_id = "default"  # TODO: 从认证获取

    # 记录交互
    interaction = RecommendInteraction(
        user_id=user_id,
        content_id=content_id,
        action=request.action,
    )
    session.add(interaction)

    # 标记内容为已处理（从推荐列表隐藏）
    content.is_processed = True

    # 更新偏好
    prefs = session.query(RecommendPreference).filter(RecommendPreference.user_id == user_id).first()
    if not prefs:
        prefs = RecommendPreference(user_id=user_id)
        session.add(prefs)

    engine = RecommenderEngine()
    current_prefs = {
        "topic_weights": json.loads(prefs.topic_weights) if prefs.topic_weights else {},
        "blocked_topics": json.loads(prefs.blocked_topics) if prefs.blocked_topics else [],
    }
    updated_prefs = engine.update_user_preferences(current_prefs, content, request.action)
    prefs.topic_weights = json.dumps(updated_prefs.get("topic_weights", {}))

    session.commit()

    return success_response({"preferences_updated": True})


@router.get("/interactions")
async def get_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    session=Depends(get_session),
):
    """获取交互历史"""
    user_id = "default"
    query = session.query(RecommendInteraction).filter(RecommendInteraction.user_id == user_id)
    if action:
        query = query.filter(RecommendInteraction.action == action)

    total = query.count()
    interactions = query.order_by(RecommendInteraction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for i in interactions:
        content = session.query(RecommendContent).filter(RecommendContent.id == i.content_id).first()
        items.append({
            "id": i.id,
            "action": i.action,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "content": {
                "id": content.id,
                "title": content.title,
                "url": content.url,
                "description": content.description,
                "source_name": content.source_name,
            } if content else None,
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/preferences")
async def get_preferences(session=Depends(get_session)):
    """获取用户偏好"""
    user_id = "default"  # TODO: 从认证获取
    prefs = session.query(RecommendPreference).filter(RecommendPreference.user_id == user_id).first()

    if not prefs:
        return success_response({
            "topic_weights": {},
            "source_trust": {},
            "blocked_topics": [],
            "blocked_sources": [],
            "preferred_length_min": 0,
            "preferred_length_max": 10000,
            "novelty_preference": 0.5,
            "quality_threshold": 50.0,
        })

    return success_response({
        "topic_weights": json.loads(prefs.topic_weights) if prefs.topic_weights else {},
        "source_trust": json.loads(prefs.source_trust) if prefs.source_trust else {},
        "blocked_topics": json.loads(prefs.blocked_topics) if prefs.blocked_topics else [],
        "blocked_sources": json.loads(prefs.blocked_sources) if prefs.blocked_sources else [],
        "preferred_length_min": prefs.preferred_length_min,
        "preferred_length_max": prefs.preferred_length_max,
        "novelty_preference": prefs.novelty_preference,
        "quality_threshold": prefs.quality_threshold,
    })


@router.put("/preferences")
async def update_preferences(request: PreferencesUpdateRequest, session=Depends(get_session)):
    """更新用户偏好"""
    user_id = "default"  # TODO: 从认证获取
    prefs = session.query(RecommendPreference).filter(RecommendPreference.user_id == user_id).first()

    if not prefs:
        prefs = RecommendPreference(user_id=user_id)
        session.add(prefs)

    if request.topic_weights is not None:
        prefs.topic_weights = json.dumps(request.topic_weights)
    if request.blocked_topics is not None:
        prefs.blocked_topics = json.dumps(request.blocked_topics)
    if request.preferred_length_min is not None:
        prefs.preferred_length_min = request.preferred_length_min
    if request.preferred_length_max is not None:
        prefs.preferred_length_max = request.preferred_length_max
    if request.novelty_preference is not None:
        prefs.novelty_preference = request.novelty_preference
    if request.quality_threshold is not None:
        prefs.quality_threshold = request.quality_threshold

    session.commit()
    return success_response({})


@router.get("/knowledge")
async def get_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    session=Depends(get_session),
):
    """获取知识库列表"""
    user_id = "default"  # TODO: 从认证获取
    query = session.query(RecommendKnowledge).filter(RecommendKnowledge.user_id == user_id)
    if category:
        query = query.filter(RecommendKnowledge.category == category)

    total = query.count()
    items = query.order_by(RecommendKnowledge.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return success_response({
        "items": [{
            "id": k.id,
            "title": k.title,
            "url": k.url,
            "category": k.category,
            "tags": json.loads(k.tags) if k.tags else [],
            "access_count": k.access_count,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        } for k in items],
        "total": total,
    })


@router.post("/knowledge")
async def save_to_knowledge(content_id: int, session=Depends(get_session)):
    """保存到知识库"""
    user_id = "default"  # TODO: 从认证获取
    content = session.query(RecommendContent).filter(RecommendContent.id == content_id).first()
    if not content:
        return error_response(404, "内容不存在")

    existing = session.query(RecommendKnowledge).filter(
        RecommendKnowledge.content_id == content_id,
        RecommendKnowledge.user_id == user_id
    ).first()
    if existing:
        return success_response({"id": existing.id})

    knowledge = RecommendKnowledge(
        content_id=content_id,
        user_id=user_id,
        title=content.title,
        url=content.url,
        tags=content.tags,
    )
    session.add(knowledge)
    session.commit()

    return success_response({"id": knowledge.id})


@router.delete("/knowledge/{knowledge_id}")
async def delete_from_knowledge(knowledge_id: int, session=Depends(get_session)):
    """从知识库删除"""
    knowledge = session.query(RecommendKnowledge).filter(RecommendKnowledge.id == knowledge_id).first()
    if knowledge:
        session.delete(knowledge)
        session.commit()
    return success_response({})


@router.get("/sources")
async def get_sources(session=Depends(get_session)):
    """获取内容源列表"""
    sources = session.query(RecommendSource).order_by(RecommendSource.created_at.desc()).all()
    return success_response({"items": [{
        "id": s.id,
        "name": s.name,
        "source_type": s.source_type,
        "url": s.url,
        "enabled": s.enabled,
        "config": s.config,
        "fetch_interval": s.fetch_interval,
        "last_fetched_at": s.last_fetched_at.isoformat() if s.last_fetched_at else None,
    } for s in sources]})


@router.post("/sources")
async def create_source(request: SourceCreateRequest, session=Depends(get_session)):
    """创建内容源"""
    source = RecommendSource(
        name=request.name,
        source_type=request.source_type,
        url=request.url,
        enabled=request.enabled,
        config=request.config,
        fetch_interval=request.fetch_interval,
    )
    session.add(source)
    session.commit()
    return success_response({"id": source.id})


@router.get("/sources/{source_id}")
async def get_source(source_id: int, session=Depends(get_session)):
    """获取内容源详情"""
    source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
    if not source:
        return error_response(404, "内容源不存在")
    return success_response({
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "enabled": source.enabled,
        "config": source.config,
        "fetch_interval": source.fetch_interval,
        "last_fetched_at": source.last_fetched_at.isoformat() if source.last_fetched_at else None,
    })


@router.put("/sources/{source_id}")
async def update_source(source_id: int, request: SourceUpdateRequest, session=Depends(get_session)):
    """更新内容源"""
    source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
    if not source:
        return error_response(404, "内容源不存在")

    if request.name is not None:
        source.name = request.name
    if request.enabled is not None:
        source.enabled = request.enabled
    if request.config is not None:
        source.config = request.config
    if request.fetch_interval is not None:
        source.fetch_interval = request.fetch_interval

    session.commit()
    return success_response({})


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, session=Depends(get_session)):
    """删除内容源"""
    source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
    if source:
        session.delete(source)
        session.commit()
    return success_response({})


def _fetch_source_task(source_id: int, task_name: str):
    """内容源抓取任务，运行在 ContentTaskQueue 中"""
    session = DB.get_session()
    try:
        source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
        if not source:
            return

        # 根据类型选择采集器
        if source.source_type == "rss":
            collector = RSSCollector()
        elif source.source_type == "opencli":
            collector = OpenCLICollector()
        elif source.source_type == "wechat":
            collector = WechatCollector()
        else:
            return

        import asyncio
        items = asyncio.get_event_loop().run_until_complete(collector.fetch(source.url))
        engine = RecommenderEngine()

        for item in items:
            existing = session.query(RecommendContent).filter(RecommendContent.url == item.url).first()
            if existing:
                continue
            class TempContent:
                def __init__(self, item):
                    self.id = 0
                    self.title = item.title
                    self.url = item.url
                    self.description = item.description
                    self.author = item.author
                    self.published_at = item.published_at
                    self.thumbnail = item.thumbnail
                    self.tags = json.dumps(item.tags) if item.tags else None
                    self.source_name = source.name
            temp = TempContent(item)
            result = engine.calculate_score(temp, {})
            status = calculate_content_status(result.score)
            content = RecommendContent(
                source_id=source.id,
                source_type=source.source_type,
                source_name=source.name,
                title=item.title,
                url=item.url,
                description=item.description,
                author=item.author,
                published_at=item.published_at,
                thumbnail=item.thumbnail,
                tags=json.dumps(item.tags) if item.tags else None,
                status=status,
            )
            session.add(content)

        source.last_fetched_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


@router.post("/sources/{source_id}/fetch")
async def fetch_source(source_id: int, session=Depends(get_session)):
    """手动抓取内容"""
    source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
    if not source:
        return error_response(404, "内容源不存在")

    task_name = f"抓取 {source.name}"
    ContentTaskQueue.add_task(_fetch_source_task, source_id, task_name, task_name=task_name)
    return success_response({"message": "任务已加入队列", "source": source.name})


@router.post("/sources/fetch-all")
async def fetch_all_sources(session=Depends(get_session)):
    """抓取所有启用的源"""
    sources = session.query(RecommendSource).filter(RecommendSource.enabled == True).all()
    engine = RecommenderEngine()
    total = 0
    for source in sources:
        if source.source_type == "rss":
            collector = RSSCollector()
        elif source.source_type == "opencli":
            collector = OpenCLICollector()
        elif source.source_type == "wechat":
            collector = WechatCollector()
        else:
            continue

        items = await collector.fetch(source.url)
        for item in items:
            existing = session.query(RecommendContent).filter(RecommendContent.url == item.url).first()
            if existing:
                continue
            class TempContent:
                def __init__(self, item):
                    self.id = 0
                    self.title = item.title
                    self.url = item.url
                    self.description = item.description
                    self.author = item.author
                    self.published_at = item.published_at
                    self.thumbnail = item.thumbnail
                    self.tags = json.dumps(item.tags) if item.tags else None
                    self.source_name = source.name
            temp = TempContent(item)
            result = engine.calculate_score(temp, {})
            status = calculate_content_status(result.score)
            content = RecommendContent(
                source_id=source.id,
                source_type=source.source_type,
                source_name=source.name,
                title=item.title,
                url=item.url,
                description=item.description,
                author=item.author,
                published_at=item.published_at,
                thumbnail=item.thumbnail,
                tags=json.dumps(item.tags) if item.tags else None,
                status=status,
            )
            session.add(content)
        source.last_fetched_at = datetime.utcnow()
        total += len(items)

    session.commit()
    return success_response({"fetched": total})


@router.get("/presets")
async def get_presets(session=Depends(get_session)):
    """获取平台预设列表"""
    presets = session.query(RecommendSourcePreset).order_by(RecommendSourcePreset.created_at.desc()).all()
    return success_response({"items": [{
        "id": p.id,
        "name": p.name,
        "platform": p.platform,
        "command": p.command,
        "limit": p.limit,
        "fetch_interval": p.fetch_interval,
        "enabled": p.enabled,
    } for p in presets]})


@router.post("/presets")
async def create_preset(request: SourceCreateRequest, session=Depends(get_session)):
    """创建预设"""
    preset = RecommendSourcePreset(
        name=request.name,
        platform=request.source_type,
        command=request.url,
        enabled=request.enabled,
        fetch_interval=request.fetch_interval,
    )
    session.add(preset)
    session.commit()
    return success_response({"id": preset.id})