<template>
  <el-card class="recommendation-card" :body-style="{ padding: '0px' }">
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
          <el-tag type="primary">推荐 {{ item.recommendation_score }}</el-tag>
          <el-tag type="info">新鲜 {{ item.freshness }}</el-tag>
          <el-tag type="success">偏好 {{ item.preference_match }}</el-tag>
        </div>
        <p class="reason" v-if="item.reason">{{ item.reason }}</p>
        <div class="actions">
          <el-button type="primary" size="small" @click="handleInteract('like')">
            👍 喜欢
          </el-button>
          <el-button type="danger" size="small" @click="handleInteract('dislike')">
            👎 不感兴趣
          </el-button>
          <el-button size="small" @click="handleInteract('skip')">⏭️ 跳过</el-button>
          <el-button size="small" @click="openUrl(item.url)">🔗 阅读原文</el-button>
          <el-button type="success" size="small" @click="handleSave">📚 收藏</el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { interact, saveToKnowledge } from '@/api/recommend'
import type { RecommendContent } from '@/api/recommend'

const props = defineProps<{
  item: RecommendContent
}>()

const handleInteract = async (action: string) => {
  try {
    await interact(props.item.id, action as 'like' | 'dislike' | 'skip' | 'view')
    ElMessage.success('已记录')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleSave = async () => {
  try {
    await saveToKnowledge(props.item.id)
    ElMessage.success('已收藏到知识库')
  } catch (error) {
    ElMessage.error('收藏失败')
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
  margin-bottom: 16px;
}
.card-content {
  display: flex;
}
.thumbnail img {
  width: 200px;
  height: 150px;
  object-fit: cover;
}
.info {
  padding: 16px;
  flex: 1;
}
.title {
  margin: 0 0 8px 0;
}
.description {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}
.meta span {
  margin-right: 12px;
}
.scores {
  margin-bottom: 8px;
}
.scores .el-tag {
  margin-right: 8px;
}
.reason {
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}
.actions .el-button {
  margin-right: 8px;
}
</style>