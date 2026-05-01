#!/usr/bin/env python3
"""
将 Bilibili 关注的人的动态写入推荐内容系统。

工作流程：
  1. 调用 `autocli bilibili following` 获取关注列表
  2. 遍历每个用户，调用 `autocli bilibili dynamics <uid>` 获取动态
  3. 将每条动态写入 recommend_contents 表（通过 url 去重）

用法：
  python scripts/fetch_bilibili_dynamics.py
  python scripts/fetch_bilibili_dynamics.py --all
  python scripts/fetch_bilibili_dynamics.py --max-dynamics 50
  python scripts/fetch_bilibili_dynamics.py --db /path/to/db.db
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "db.db"
AUTOCLI_PATH = PROJECT_ROOT / "bin" / "autocli"

# 动态类型 → 默认标题映射
TYPE_LABELS = {
    "video": "B站视频动态",
    "article": "B站专栏动态",
    "image": "B站图文动态",
    "text": "B站文字动态",
    "music": "B站音乐动态",
    "audio": "B站音频动态",
    "live": "B站直播动态",
    "share": "B站分享动态",
}


def ensure_source(cursor, name, source_type, url):
    """确保 recommend_sources 中存在 Bilibili 源，返回其 id。"""
    cursor.execute(
        "SELECT id FROM recommend_sources WHERE name = ? AND source_type = ?",
        (name, source_type),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """INSERT INTO recommend_sources
               (name, source_type, url, enabled, fetch_interval, created_at, updated_at)
               VALUES (?, ?, ?, 1, 24.0, ?, ?)""",
        (name, source_type, url, now, now),
    )
    return cursor.lastrowid


def run_autocli(args):
    """执行 autocli 命令并返回解析后的 JSON 输出。"""
    cmd = [str(AUTOCLI_PATH)] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
    except FileNotFoundError:
        print(f"错误: 未找到 autocli 二进制文件: {AUTOCLI_PATH}", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"错误: autocli 命令超时: {' '.join(cmd)}", file=sys.stderr)
        return None

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if stderr:
            print(f"  autocli 错误: {stderr}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"  解析 autocli 输出失败: {e}", file=sys.stderr)
        return None


def parse_publish_time(time_str):
    """解析 ISO 格式时间字符串为 SQLite 可接受的格式。"""
    if not time_str:
        return None
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def make_title(content, dyn_type):
    """根据动态内容和类型生成标题。"""
    if content and content.strip():
        text = content.strip().replace("\n", " ").replace("\r", " ")
        if len(text) > 80:
            return text[:80] + "..."
        return text
    return TYPE_LABELS.get(dyn_type, f"B站动态 ({dyn_type})")


def main():
    parser = argparse.ArgumentParser(
        description="将 Bilibili 关注的人的最新动态写入推荐内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s                     # 每个用户最多拉 20 条\n"
            "  %(prog)s --all               # 拉取全部动态（可能很慢）\n"
            "  %(prog)s --max-dynamics 50   # 每个用户最多拉 50 条\n"
        ),
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite 数据库路径 (默认: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="获取每个用户的全部动态（默认仅获取最近 20 条）",
    )
    parser.add_argument(
        "--max-dynamics",
        type=int,
        default=20,
        help="每个用户最多获取的动态数，仅在未启用 --all 时生效 (默认: 20)",
    )
    args = parser.parse_args()

    # ── Step 1: 获取关注列表 ──
    print("正在获取 Bilibili 关注列表...")
    following = run_autocli(["bilibili", "following", "-f", "json"])
    if following is None:
        print("获取关注列表失败，请检查 autocli 是否已登录 Bilibili", file=sys.stderr)
        sys.exit(1)

    print(f"共关注 {len(following)} 个用户")

    # ── Step 2: 连接数据库 ──
    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    # 确保推荐源存在
    source_id = ensure_source(cursor, "Bilibili Dynamics", "opencli", "bilibili:dynamics")
    conn.commit()

    # ── Step 3: 遍历用户获取动态 ──
    total_new = 0
    total_skipped = 0
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    for i, user in enumerate(following, 1):
        name = user.get("name", "未知用户")
        mid = user.get("mid") or user.get("user_id")

        if not mid:
            print(f"  [{i}/{len(following)}] 跳过 {name}: 缺少 mid")
            continue

        print(f"  [{i}/{len(following)}] 正在处理: {name} (mid={mid})")

        # 构造 autocli 命令
        dyn_args = ["bilibili", "dynamics", str(mid), "-f", "json"]
        if args.all:
            dyn_args.extend(["--all", "true"])
        else:
            dyn_args.extend(["--limit", str(args.max_dynamics)])

        dynamics = run_autocli(dyn_args)
        if dynamics is None:
            print(f"    ↳ 获取动态失败，跳过")
            continue

        new_count = 0
        skip_count = 0
        for dyn in dynamics:
            url = dyn.get("url", "")
            if not url:
                continue

            # 去重检查
            cursor.execute("SELECT 1 FROM recommend_contents WHERE url = ?", (url,))
            if cursor.fetchone():
                skip_count += 1
                continue

            content_text = dyn.get("content", "") or ""
            dyn_type = dyn.get("type", "")
            title = make_title(content_text, dyn_type)
            published_at = parse_publish_time(dyn.get("publish_time", ""))
            tags = json.dumps(["bilibili", dyn_type], ensure_ascii=False)

            cursor.execute(
                """INSERT INTO recommend_contents
                       (source_id, source_type, source_name, title, url,
                        description, author, published_at, thumbnail, tags,
                        status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                               'pending', ?, ?)""",
                (
                    source_id,
                    "opencli",
                    "Bilibili",
                    title,
                    url,
                    content_text,
                    name,
                    published_at,
                    dyn.get("thumbnail", "") or "",
                    tags,
                    now_utc,
                    now_utc,
                ),
            )
            new_count += 1

        conn.commit()
        total_new += new_count
        total_skipped += skip_count
        print(f"    ↳ 新增 {new_count} 条, 跳过 {skip_count} 条")

    conn.close()
    print(f"\n完成! 共新增 {total_new} 条推荐内容, 跳过 {total_skipped} 条重复内容")


if __name__ == "__main__":
    main()
