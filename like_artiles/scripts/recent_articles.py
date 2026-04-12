#!/usr/bin/env python3
"""
查询最近内容
用法: python recent_articles.py [--db DB_PATH] [limit]
"""
import sys
import argparse
from sqlalchemy import text
from query_db import get_session, format_datetime, format_tags, print_json, set_db_path


def parse_args():
    parser = argparse.ArgumentParser(description="查询最近内容")
    parser.add_argument('--db', '-d', dest='db_path', default=None, help='数据库路径')
    parser.add_argument('limit', nargs='?', type=int, default=20, help='返回数量 (默认: 20)')
    return parser.parse_args()


def query_recent_articles(limit: int = 20):
    """查询最近的内容"""
    session = get_session()
    try:
        query = text("""
            SELECT
                c.id,
                c.title,
                c.url,
                c.description,
                c.author,
                c.source_name,
                c.source_type,
                c.published_at,
                c.thumbnail,
                c.tags,
                c.recommendation_score,
                c.status,
                c.created_at,
                s.name as source_name_full
            FROM recommend_contents c
            LEFT JOIN recommend_sources s ON c.source_id = s.id
            ORDER BY c.created_at DESC
            LIMIT :limit
        """)
        result = session.execute(query, {"limit": limit})
        columns = result.keys()
        rows = result.fetchall()

        articles = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            articles.append({
                "id": row_dict["id"],
                "title": row_dict["title"],
                "url": row_dict["url"],
                "description": row_dict["description"],
                "author": row_dict["author"],
                "source_name": row_dict["source_name"] or row_dict["source_name_full"],
                "source_type": row_dict["source_type"],
                "published_at": format_datetime(row_dict["published_at"]),
                "thumbnail": row_dict["thumbnail"],
                "tags": format_tags(row_dict["tags"]),
                "recommendation_score": row_dict["recommendation_score"],
                "status": row_dict["status"],
                "created_at": format_datetime(row_dict["created_at"]),
            })
        return articles
    finally:
        session.close()


def main():
    args = parse_args()
    if args.db_path:
        set_db_path(args.db_path)
    articles = query_recent_articles(args.limit)
    print_json({
        "code": 0,
        "data": {
            "items": articles,
            "total": len(articles),
            "limit": args.limit
        }
    })


if __name__ == "__main__":
    main()
