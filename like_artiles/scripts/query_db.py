#!/usr/bin/env python3
"""
数据库查询脚本基类
支持通过 --db 参数指定数据库路径
"""
import os
import sys
import json
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# 默认数据库路径: 项目根目录的 data/db.db
def get_default_db_path():
    """获取默认数据库路径"""
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(_project_root, "..", "data", "db.db"))


# 缓存命令行指定的数据库路径
_cmd_db_path = None


def set_db_path(db_path):
    """设置数据库路径（由脚本调用）"""
    global _cmd_db_path, _database_url
    _cmd_db_path = db_path
    _database_url = f"sqlite:///{db_path}" if db_path else None


def get_db_path_from_args():
    """获取数据库路径（供外部调用）"""
    return _cmd_db_path


# 缓存数据库URL
_database_url = None


def get_database_url():
    """获取数据库URL"""
    global _database_url
    if _database_url is None:
        db_path = get_db_path_from_args() or get_default_db_path()
        _database_url = f"sqlite:///{db_path}"
    return _database_url


def get_engine():
    """获取数据库引擎"""
    engine = create_engine(get_database_url(), connect_args={"check_same_thread": False})
    return engine


def get_session():
    """获取数据库会话"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def query_to_dict(result, columns):
    """将查询结果转换为字典列表"""
    return [dict(zip(columns, row)) for row in result]


def format_datetime(dt):
    """格式化日期时间"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)


def format_tags(tags_str):
    """格式化标签JSON字符串"""
    if tags_str is None:
        return []
    if isinstance(tags_str, list):
        return tags_str
    try:
        return json.loads(tags_str)
    except:
        return []


def print_json(data):
    """打印JSON格式输出"""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
