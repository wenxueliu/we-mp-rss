#!/usr/bin/env python3
"""
查询内容源列表
用法: python sources.py [--db DB_PATH]
"""
import json
import argparse
from sqlalchemy import text
from query_db import get_session, print_json, set_db_path


def parse_args():
    parser = argparse.ArgumentParser(description="查询内容源列表")
    parser.add_argument('--db', '-d', dest='db_path', default=None, help='数据库路径')
    return parser.parse_args()


def query_sources():
    """查询所有内容源"""
    session = get_session()
    try:
        query = text("""
            SELECT
                id,
                name,
                source_type,
                url,
                enabled,
                config,
                fetch_interval,
                last_fetched_at,
                created_at
            FROM recommend_sources
            ORDER BY created_at DESC
        """)
        result = session.execute(query)
        columns = result.keys()
        rows = result.fetchall()

        sources = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            sources.append({
                "id": row_dict["id"],
                "name": row_dict["name"],
                "source_type": row_dict["source_type"],
                "url": row_dict["url"],
                "enabled": bool(row_dict["enabled"]),
                "config": json.loads(row_dict["config"]) if row_dict["config"] else None,
                "fetch_interval": row_dict["fetch_interval"],
                "last_fetched_at": str(row_dict["last_fetched_at"]) if row_dict["last_fetched_at"] else None,
                "created_at": str(row_dict["created_at"]) if row_dict["created_at"] else None,
            })
        return sources
    finally:
        session.close()


def main():
    args = parse_args()
    if args.db_path:
        set_db_path(args.db_path)
    sources = query_sources()
    print_json({
        "code": 0,
        "data": {
            "items": sources,
            "total": len(sources)
        }
    })


if __name__ == "__main__":
    main()
