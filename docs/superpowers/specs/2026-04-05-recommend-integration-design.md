# 推荐功能集成设计文档

## 概述

将 recommend 项目的推荐功能（多平台内容抓取、智能推荐算法、用户交互、偏好学习、知识库管理）作为独立模块集成到 we-mp-rss 项目中。

## 目录结构

```
we-mp-rss/
├── core/
│   └── recommend/
│       ├── __init__.py
│       ├── models.py          # 推荐数据模型
│       ├── engine.py          # 推荐引擎（从 recommend 移植）
│       ├── collectors.py      # 内容采集器（RSS、OpenCLI）
│       └── scheduler.py       # 定时任务调度
├── apis/
│   └── recommend.py           # 推荐 API 路由
├── web_ui/src/
│   ├── api/
│   │   └── recommend.ts       # 前端 API 调用
│   ├── views/
│   │   ├── RecommendView.vue  # 推荐列表页
│   │   ├── KnowledgeView.vue  # 知识库页
│   │   └── PreferencesView.vue # 偏好设置页
│   └── components/
│       ├── RecommendationCard.vue # 推荐内容卡片
│       └── InteractionButtons.vue # 交互按钮组
```

## 数据模型设计

### 新增数据库表

#### 1. recommend_contents（推荐内容映射表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| article_id | String(255) | 关联 Article 表的外键 |
| source_type | String(50) | 来源类型：rss, wechat |
| source_id | String(100) | 来源标识（如公众号ID） |
| title | String(500) | 标题 |
| url | String(1000) | 原文链接 |
| description | Text | 描述/摘要 |
| author | String(200) | 作者 |
| published_at | DateTime | 发布时间 |
| thumbnail | String(500) | 缩略图 |
| tags | Text | 标签（JSON数组） |
| freshness_score | Float | 新鲜度分数 0-100 |
| recommendation_score | Float | 推荐分数 0-100 |
| status | String(50) | 状态：pending, recommended, accepted, rejected |
| is_processed | Boolean | 是否已处理 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 2. recommend_interactions（用户交互表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| user_id | String(100) | 用户ID |
| content_id | Integer | 外键，关联 recommend_contents |
| action | String(50) | 操作：like, dislike, skip, view |
| weight | Float | 操作权重 |
| extra_data | Text | 额外数据（JSON） |
| created_at | DateTime | 创建时间 |

#### 3. recommend_preferences（用户偏好表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| user_id | String(100) | 用户ID，唯一索引 |
| topic_weights | Text | 主题权重（JSON对象） |
| source_trust | Text | 来源信任度（JSON对象） |
| preferred_length_min | Integer | 偏好长度最小值 |
| preferred_length_max | Integer | 偏好长度最大值 |
| novelty_preference | Float | 新鲜度偏好 0-1 |
| quality_threshold | Float | 质量阈值 |
| blocked_topics | Text | 屏蔽主题（JSON数组） |
| blocked_sources | Text | 屏蔽来源（JSON数组） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 4. recommend_sources（内容源配置表）

| 字段 | 类型 | 说明 |
|------|------|
| id | Integer | 主键，自增 |
| name | String(100) | 源名称 |
| source_type | String(50) | 源类型：rss, opencli, wechat |
| url | String(500) | 源 URL 或配置 |
| enabled | Boolean | 是否启用 |
| config | Text | JSON 配置 |
| fetch_interval | Float | 抓取间隔（小时），默认 24 |
| last_fetched_at | DateTime | 最后抓取时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 5. recommend_source_presets（内容源预设表）

| 字段 | 类型 | 说明 |
|------|------|
| id | Integer | 主键，自增 |
| name | String(100) | 预设名称 |
| platform | String(50) | 平台名称 |
| command | String(50) | 命令 |
| limit | Integer | 数量限制，默认 10 |
| fetch_interval | Float | 抓取间隔（小时） |
| enabled | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 6. recommend_knowledge（知识库表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| content_id | Integer | 外键，关联 recommend_contents，唯一 |
| user_id | String(100) | 用户ID |
| title | String(500) | 标题 |
| user_notes | Text | 用户笔记 |
| ai_summary | Text | AI生成的摘要 |
| key_insights | Text | 关键见解（JSON数组） |
| tags | Text | 标签（JSON数组） |
| category | String(100) | 分类 |
| access_count | Integer | 访问次数 |
| last_accessed_at | DateTime | 最后访问时间 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 推荐引擎设计

### 评分算法

推荐分数由以下因素加权计算：

```
score = 新鲜度(40%) + 偏好匹配(30%) + 内容质量(20%) + 时效性(10%)
```

#### 1. 新鲜度分数 (freshness_weight = 0.4)

- 基础分数：50
- 与已有内容相似度越高，分数越低
- 7天内：+40分，30天内：+20分，更久：递减

#### 2. 偏好匹配分数 (preference_weight = 0.3)

- 主题权重匹配
- 来源信任度
- 黑名单检查（命中返回0）

#### 3. 内容质量分数 (quality_weight = 0.2)

- 标题长度适中（20-100字符）：+15
- 描述完整（>50字符）：+15
- 有作者信息：+10
- 有缩略图：+10

#### 4. 时效性分数 (timeliness_weight = 0.1)

- 7天内：100分，每过一天递减
- 7-30天：65分开始递减
- 30天后：30分开始递减

### 偏好学习

基于用户行为更新偏好：

- **like**: 正向强化，topic_weights 向 100 移动
- **dislike**: 负向强化，topic_weights 向 0 移动
- **skip**: 轻微负向，向 25 移动

学习率默认 0.1

## API 设计

### 推荐相关接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/wx/recommend/contents | 获取推荐内容列表 |
| GET | /api/v1/wx/recommend/contents/{id} | 获取推荐内容详情 |
| POST | /api/v1/wx/recommend/contents/{id}/interact | 用户交互（like/dislike/skip） |
| GET | /api/v1/wx/recommend/preferences | 获取用户偏好 |
| PUT | /api/v1/wx/recommend/preferences | 更新用户偏好 |
| GET | /api/v1/wx/recommend/knowledge | 获取知识库列表 |
| POST | /api/v1/wx/recommend/knowledge | 保存到知识库 |
| DELETE | /api/v1/wx/recommend/knowledge/{id} | 从知识库删除 |

### 内容源管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/wx/recommend/sources | 获取内容源列表 |
| POST | /api/v1/wx/recommend/sources | 创建内容源 |
| GET | /api/v1/wx/recommend/sources/{id} | 获取内容源详情 |
| PUT | /api/v1/wx/recommend/sources/{id} | 更新内容源 |
| DELETE | /api/v1/wx/recommend/sources/{id} | 删除内容源 |
| POST | /api/v1/wx/recommend/sources/{id}/fetch | 手动抓取内容 |
| POST | /api/v1/wx/recommend/sources/fetch-all | 抓取所有启用的源 |
| GET | /api/v1/wx/recommend/presets | 获取平台预设列表 |
| POST | /api/v1/wx/recommend/presets | 创建预设 |

### 请求/响应示例

#### POST /api/v1/wx/recommend/contents/{id}/interact

请求：
```json
{
  "action": "like"
}
```

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "preferences_updated": true
  }
}
```

#### GET /api/v1/wx/recommend/contents

响应：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "article_id": "xxx",
        "title": "文章标题",
        "url": "https://...",
        "description": "摘要",
        "thumbnail": "https://...",
        "recommendation_score": 85.5,
        "freshness": 90.0,
        "preference_match": 80.0,
        "quality": 75.0,
        "timeliness": 95.0,
        "reason": "高度新鲜的内容 | 符合您的兴趣 | 最新发布",
        "author": "公众号名称",
        "published_at": "2026-04-05T10:00:00Z",
        "tags": ["科技", "AI"]
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

## 前端页面设计

### 1. 推荐列表页 (RecommendView.vue)

- 顶部：筛选条件（时间范围、分数范围）
- 中间：推荐内容卡片列表
- 每个卡片包含：
  - 标题、摘要、缩略图
  - 推荐分数及各项评分
  - 推荐理由
  - 交互按钮：👍 👎 ⏭️ 🔗

### 2. 知识库页 (KnowledgeView.vue)

- 已保存内容列表
- 支持搜索、分类、标签筛选
- 可添加笔记

### 3. 偏好设置页 (PreferencesView.vue)

- 主题权重配置（可视化滑块）
- 屏蔽主题/来源管理
- 内容长度偏好
- 新鲜度/质量权重调整

### 4. 内容源管理页 (SourcesView.vue)

- 源列表展示（名称、类型、状态、最后抓取时间）
- 支持的源类型：
  - **RSS**: 输入 RSS URL，自动解析标题
  - **OpenCLI**: hackernews, reddit, bilibili, zhihu, youtube, twitter, devto, lobsters, stackoverflow
- 添加/编辑/删除内容源
- 手动触发抓取
- 预设平台快速添加

## 移植文件清单

从 recommend 项目移植以下文件：

| 源文件 | 目标文件 |
|--------|----------|
| backend/models.py | core/recommend/models.py |
| backend/recommender/engine.py | core/recommend/engine.py |
| backend/collectors/base.py | core/recommend/collectors.py |
| backend/collectors/rss.py | core/recommend/collectors.py |
| backend/collectors/opencli.py | core/recommend/collectors.py |
| backend/scheduler.py | core/recommend/scheduler.py |
| frontend/src/views/HomeView.vue | web_ui/src/views/RecommendView.vue |
| frontend/src/views/KnowledgeView.vue | web_ui/src/views/KnowledgeView.vue |
| frontend/src/views/InteractionsView.vue | 合并到 RecommendView.vue |
| frontend/src/views/SourcesView.vue | web_ui/src/views/SourcesView.vue |

## 配置项

在 config.yaml 中新增：

```yaml
recommend:
  enabled: true
  # 评分权重
  freshness_weight: 0.4
  preference_weight: 0.3
  quality_weight: 0.2
  timeliness_weight: 0.1
  # 定时任务
  auto_fetch: true
  fetch_interval_hours: 6
  # 偏好学习
  learning_rate: 0.1
```

## 依赖项

新增 Python 依赖：
- apscheduler（已在现有项目使用）
- feedparser（RSS 解析）
- httpx（HTTP 请求）

前端依赖（已在 we-mp-rss 使用）：
- axios
- element-plus
