<template>
  <a-card class="recommendation-card" :body-style="{ padding: '0px' }">
    <div class="card-content">
      <div class="thumbnail" v-if="item.thumbnail">
        <img :src="item.thumbnail" :alt="item.title" />
      </div>
      <div class="info">
        <h3 class="title">{{ item.title }}</h3>
        <p class="description" v-if="item.description">{{ item.description }}</p>
        <div class="meta">
          <span class="author" v-if="item.author">{{ item.author }}</span>
          <span class="source" v-if="item.source_name">{{ item.source_name }}</span>
          <span class="date" v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
        </div>
        <div class="scores">
          <a-tag color="arcoblue">推荐 {{ item.recommendation_score }}</a-tag>
          <a-tag>新鲜 {{ item.freshness }}</a-tag>
          <a-tag color="green">偏好 {{ item.preference_match }}</a-tag>
        </div>
        <p class="reason" v-if="item.reason">{{ item.reason }}</p>
        <div class="actions">
          <a-button type="primary" size="small" @click="handleInteract('like')">
            👍 喜欢
          </a-button>
          <a-button type="danger" size="small" @click="handleInteract('dislike')">
            👎 不感兴趣
          </a-button>
          <a-button size="small" @click="handleInteract('skip')">⏭️ 跳过</a-button>
          <a-button size="small" @click="openUrl(item.url)">🔗 阅读原文</a-button>
          <a-button type="success" size="small" @click="handleSave">📚 收藏</a-button>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { Message } from '@arco-design/web-vue'
import { interact, saveToKnowledge } from '@/api/recommend'
import type { RecommendContent } from '@/api/recommend'

const props = defineProps<{
  item: RecommendContent
}>()

const handleInteract = async (action: string) => {
  try {
    await interact(props.item.id, action as 'like' | 'dislike' | 'skip' | 'view')
    Message.success('已记录')
  } catch (error) {
    Message.error('操作失败')
  }
}

const handleSave = async () => {
  try {
    await saveToKnowledge(props.item.id)
    Message.success('已收藏到知识库')
  } catch (error) {
    Message.error('收藏失败')
  }
}

const openUrl = (url: string) => {
  window.open(url, '_blank')
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.recommendation-card {
  margin-bottom: 12px;
}
.card-content {
  display: flex;
  flex-direction: column;
}
.thumbnail {
  width: 100%;
  max-height: 200px;
  overflow: hidden;
}
.thumbnail img {
  width: 100%;
  height: auto;
  max-height: 200px;
  object-fit: cover;
}
.info {
  padding: 12px;
  flex: 1;
}
.title {
  margin: 0 0 8px 0;
  font-size: 16px;
  line-height: 1.4;
  word-break: break-all;
}
.description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.meta span {
  margin-right: 12px;
  margin-bottom: 4px;
  display: inline-block;
}
.scores {
  margin-bottom: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.scores .arco-tag {
  margin-right: 0;
}
.reason {
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.actions .arco-btn {
  margin-right: 0;
  flex: 1;
  min-width: 80px;
}

/* 桌面端：横排布局 */
@media (min-width: 768px) {
  .card-content {
    flex-direction: row;
  }
  .thumbnail {
    width: 200px;
    flex-shrink: 0;
    max-height: none;
  }
  .thumbnail img {
    width: 200px;
    height: 150px;
    max-height: none;
  }
}
</style>
