"""搜索模块 API 路由"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import or_

from core.db import DB
from core.recommend.models import RecommendContent
from apis.base import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["搜索"])

MAX_KEYWORD_LENGTH = 200
MAX_RESULTS = 500


def get_session():
    return DB.get_session()


@router.get("")
async def search(
    q: str = Query(..., description="搜索关键词"),
    session=Depends(get_session),
):
    """搜索推荐内容，按标题和摘要匹配"""
    try:
        keyword = q.strip()

        if not keyword:
            logger.warning("搜索关键词为空")
            return error_response(400, "关键词不能为空")

        if len(keyword) > MAX_KEYWORD_LENGTH:
            keyword = keyword[:MAX_KEYWORD_LENGTH]

        query = session.query(RecommendContent).filter(
            or_(
                RecommendContent.title.like(f"%{keyword}%"),
                RecommendContent.description.like(f"%{keyword}%"),
            )
        ).order_by(RecommendContent.id.desc()).limit(MAX_RESULTS)

        total = query.count()
        items = query.all()

        return success_response({
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "summary": item.description,
                    "url": item.url,
                    "author": item.author,
                    "source_type": item.source_type,
                    "source_name": item.source_name,
                    "published_at": item.published_at.isoformat() if item.published_at else None,
                }
                for item in items
            ],
            "total": total,
        })
    except Exception as e:
        logger.error(f"搜索异常: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "internal_error", "message": "搜索服务暂不可用"})
