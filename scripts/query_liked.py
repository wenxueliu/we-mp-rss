#!/usr/bin/env python3
"""Query liked articles from the recommendation database."""

import argparse
import json
import sqlite3
from datetime import datetime


def parse_tags(tags_str):
    """Parse tags column as JSON, handling NULL values."""
    if tags_str is None:
        return None
    try:
        return json.loads(tags_str)
    except (json.JSONDecodeError, TypeError):
        return None


def query_liked_articles(db_path, user_id, limit):
    """Query liked articles from the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT
            rc.id,
            rc.title,
            rc.url,
            rc.description,
            rc.author,
            rc.source_name,
            rc.published_at,
            rc.thumbnail,
            rc.tags,
            rc.recommendation_score,
            ri.created_at
        FROM recommend_interactions ri
        JOIN recommend_contents rc ON ri.content_id = rc.id
        WHERE ri.user_id = ? AND ri.action = 'like'
        ORDER BY ri.created_at DESC
        LIMIT ?
    """

    cursor.execute(query, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()

    articles = []
    for row in rows:
        article = {
            "id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "description": row["description"],
            "author": row["author"],
            "source_name": row["source_name"],
            "published_at": row["published_at"],
            "thumbnail": row["thumbnail"],
            "tags": parse_tags(row["tags"]),
            "recommendation_score": row["recommendation_score"],
            "created_at": row["created_at"],
        }
        articles.append(article)

    return articles


def print_plain(articles):
    """Print articles in plain text format."""
    for article in articles:
        created_at = article["created_at"]
        if created_at:
            if isinstance(created_at, str):
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
        else:
            created_at = "N/A"

        title = article["title"] or "No Title"
        source = article["source_name"] or "Unknown Source"
        url = article["url"] or ""

        print(f"[{created_at}] {title} | {source} | {url}")


def print_json(articles):
    """Print articles as JSON."""
    print(json.dumps(articles, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Query liked articles from the database.")
    parser.add_argument(
        "--db",
        default="/home/chengnanfeng/code/we-mp-rss/data/db.db",
        help="Path to the SQLite database",
    )
    parser.add_argument(
        "--user",
        default="default",
        help="User ID to query (default: default)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of articles to return (default: 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of plain text",
    )

    args = parser.parse_args()

    articles = query_liked_articles(args.db, args.user, args.limit)

    if args.json:
        print_json(articles)
    else:
        print_plain(articles)


if __name__ == "__main__":
    main()
