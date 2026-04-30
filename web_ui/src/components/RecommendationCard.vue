<template>
  <a-card class="recommendation-card" :body-style="{ padding: '0px' }" @click="openUrl(item.url)">
    <div class="card-content">
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
        <div class="actions" @click.stop>
          <a-button type="primary" size="small" @click="handleInteract('like')">
            👍 喜欢
          </a-button>
          <a-button type="danger" size="small" @click="handleInteract('dislike')">
            👎 不感兴趣
          </a-button>
          <a-button size="small" @click="handleInteract('skip')">⏭️ 跳过</a-button>
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

const emit = defineEmits<{
  (e: 'interact', action: string): void
}>()

const handleInteract = async (action: string) => {
  try {
    await interact(props.item.id, action as 'like' | 'dislike' | 'skip' | 'view')
    Message.success('已记录')
    emit('interact', action)
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
  return new Date(dateStr).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.recommendation-card {
  margin-bottom: 16px;
  background: var(--pure-white);
  border: 1px solid var(--border-lavender);
  border-radius: var(--radius-comfortable);
  box-shadow: var(--shadow-whisper);
  transition: all 0.2s ease;
}

.recommendation-card:hover {
  box-shadow: var(--shadow-elevated);
  transform: translateY(-2px);
}

.card-content {
  padding: 20px;
}

.info {
  flex: 1;
}

.title {
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  word-break: break-all;
  color: var(--near-black);
  letter-spacing: -0.25px;
}

.description {
  color: var(--slate-gray);
  font-size: 14px;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

.meta {
  font-size: 12px;
  color: var(--silver);
  margin-bottom: 12px;
  flex-wrap: wrap;
  display: flex;
  gap: 12px;
}

.meta span {
  margin-bottom: 4px;
  display: inline-block;
}

.scores {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scores .arco-tag {
  margin-right: 0;
  border-radius: var(--radius-pill) !important;
  font-weight: 500;
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
  border-radius: var(--radius-pill) !important;
  font-weight: 500;
  transition: all 0.2s ease;
}

.actions .arco-btn:hover {
  transform: translateY(-1px);
}
</style>
