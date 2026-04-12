---
name: liked-articles
description: 查询用户喜欢的文章内容。当用户想查看自己点赞过、收藏过、或标记为喜欢的内容时触发。也用于个人内容回顾、兴趣分析、或基于点赞历史生成推荐。直接运行 skill/scripts/liked_articles.py 脚本查询数据库。
---

# 喜欢内容查询

查询当前用户在推荐系统中的"喜欢"历史，返回每条喜欢记录对应的文章详情。

## 查询方式

### 直接运行脚本（推荐）

```bash
# 默认查询
python skill/scripts/liked_articles.py

# 指定用户
python skill/scripts/liked_articles.py <user_id>

# 指定数据库路径
python skill/scripts/liked_articles.py --db /path/to/db.db

# 组合参数
python skill/scripts/liked_articles.py --db data/db.db <user_id> <limit>
```

**参数说明：**
| 参数 | 说明 |
|------|------|
| `--db`, `-d` | 数据库路径（可选，默认使用项目 data/db.db） |
| `user_id` | 用户ID（可选，默认: default） |
| `limit` | 返回数量（可选，默认: 50） |

**示例输出：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "interaction_id": 60,
        "liked_at": "2026-04-12T12:17:27.918971",
        "title": "文章标题",
        "url": "https://...",
        "description": "文章描述",
        "author": "作者",
        "source_name": "公众号名",
        "published_at": "发布时间",
        "thumbnail": "缩略图URL",
        "tags": ["标签1", "标签2"],
        "recommendation_score": 0.0
      }
    ],
    "total": 10,
    "user_id": "default"
  }
}
```

## 输出字段说明

| 字段 | 说明 |
|------|------|
| `interaction_id` | 交互记录ID |
| `liked_at` | 点赞时间 |
| `title` | 文章标题 |
| `url` | 文章链接 |
| `description` | 文章描述/摘要 |
| `author` | 作者 |
| `source_name` | 来源（公众号/RSS源名） |
| `published_at` | 发布时间 |
| `thumbnail` | 缩略图 |
| `tags` | 标签列表 |
| `recommendation_score` | 推荐分数 |

## 其他可用脚本

| 脚本 | 说明 |
|------|------|
| `skill/scripts/liked_articles.py` | 查询喜欢的文章 |
| `skill/scripts/recent_articles.py` | 查询最近内容 |
| `skill/scripts/sources.py` | 查询内容源列表 |

## 使用场景

- 用户说"查看我喜欢的文章"
- 用户说"我之前点赞过哪些内容"
- 用户说"导出我喜欢的内容"
- 用户想基于点赞历史分析兴趣偏好
