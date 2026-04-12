"""
内容源定时抓取任务
定期检查所有启用的内容源，根据 fetch_interval 决定是否需要抓取
"""
from datetime import datetime
from core.recommend.models import RecommendSource, RecommendContent
from core.recommend.collectors import RSSCollector, OpenCLICollector, WechatCollector
from core.recommend.engine import RecommenderEngine, calculate_content_status
from core.db import DB
from core.log import logger
import json


def fetch_recommend_source(source_id: int):
    """抓取单个内容源"""
    session = DB.get_session()
    try:
        source = session.query(RecommendSource).filter(RecommendSource.id == source_id).first()
        if not source or not source.enabled:
            return 0

        # 根据类型选择采集器
        if source.source_type == "rss":
            collector = RSSCollector()
        elif source.source_type == "opencli":
            collector = OpenCLICollector()
        elif source.source_type == "wechat":
            collector = WechatCollector()
        else:
            logger.warning(f"Unsupported source type: {source.source_type}")
            return 0

        # 同步执行采集（注意：实际项目中可能是异步）
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        items = loop.run_until_complete(collector.fetch(source.url))
        engine = RecommenderEngine()

        new_count = 0
        for item in items:
            existing = session.query(RecommendContent).filter(
                RecommendContent.url == item.url
            ).first()
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
            new_count += 1

        source.last_fetched_at = datetime.utcnow()
        session.commit()
        logger.info(f"Source {source.name} fetched, {new_count} new items")
        return new_count
    except Exception as e:
        logger.error(f"Fetch source {source_id} failed: {e}")
        session.rollback()
        return 0
    finally:
        session.close()


def check_and_fetch_sources():
    """
    检查所有内容源，根据 fetch_interval 决定是否需要抓取
    这个函数会被定时调度器定期调用
    """
    session = DB.get_session()
    try:
        # 获取所有启用的源
        sources = session.query(RecommendSource).filter(RecommendSource.enabled == True).all()
        now = datetime.utcnow()

        for source in sources:
            # 如果从未抓取过，立即抓取
            if source.last_fetched_at is None:
                logger.info(f"Source {source.name} never fetched, fetching now...")
                session.commit()  # 释放当前事务，让抓取在独立事务中执行
                fetch_recommend_source(source.id)
                session = DB.get_session()  # 重新获取会话
                continue

            # 计算距离上次抓取的小时数
            elapsed_hours = (now - source.last_fetched_at).total_seconds() / 3600

            # 如果超过抓取间隔，执行抓取
            if elapsed_hours >= source.fetch_interval:
                logger.info(f"Source {source.name} elapsed {elapsed_hours:.1f}h >= {source.fetch_interval}h, fetching...")
                session.commit()  # 释放当前事务
                fetch_recommend_source(source.id)
                session = DB.get_session()  # 重新获取会话
            else:
                logger.debug(f"Source {source.name} elapsed {elapsed_hours:.1f}h < {source.fetch_interval}h, skip")

    except Exception as e:
        logger.error(f"Check and fetch sources failed: {e}")
    finally:
        session.close()
