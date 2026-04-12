#!/usr/bin/env python3
"""
查询用户喜欢的文章
用法: python liked_articles.py [--db DB_PATH] [user_id] [limit]
"""
import sys
import json
import argparse
from sqlalchemy import text
from query_db import get_session, format_datetime, format_tags, print_json, set_db_path


def parse_args():
    parser = argparse.ArgumentParser(description="查询用户喜欢的文章")
    parser.add_argument('--db', '-d', dest='db_path', default=None, help='数据库路径')
    parser.add_argument('user_id', nargs='?', default='default', help='用户ID (默认: default)')
    parser.add_argument('limit', nargs='?', type=int, default=50, help='返回数量 (默认: 50)')
    return parser.parse_args()


def query_liked_articles(user_id: str = "default", limit: int = 50):
    """查询用户喜欢的文章"""
    session = get_session()
    try:
        query = text("""
            SELECT
                i.id as interaction_id,
                i.user_id,
                i.action,
                i.created_at as liked_at,
                c.id as content_id,
                c.title,
                c.url,
                c.description,
                c.author,
                c.source_name,
                c.published_at,
                c.thumbnail,
                c.tags,
                c.recommendation_score
            FROM recommend_interactions i
            JOIN recommend_contents c ON i.content_id = c.id
            WHERE i.user_id = :user_id AND i.action = 'like'
            ORDER BY i.created_at DESC
            LIMIT :limit
        """)
        result = session.execute(query, {"user_id": user_id, "limit": limit})
        columns = result.keys()
        rows = result.fetchall()

        articles = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            articles.append(row_dict["url"])
        return articles
    finally:
        session.close()


def main():
    args = parse_args()
    if args.db_path:
        set_db_path(args.db_path)
    articles = query_liked_articles(args.user_id, args.limit)
    print_json({
        "code": 0,
        "data": {
            "items": articles,
            "total": len(articles),
            "user_id": args.user_id
        }
    })


if __name__ == "__main__":
    main()
