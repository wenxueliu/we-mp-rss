<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getInteractions } from '@/api/recommend'
import type { InteractionItem } from '@/api/recommend'

const loading = ref(false)
const items = ref<InteractionItem[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterAction = ref('')

const actionLabels: Record<string, string> = {
  like: '👍 喜欢',
  dislike: '👎 不感兴趣',
  skip: '⏭️ 跳过',
  view: '👁️ 浏览',
}

const actionColors: Record<string, string> = {
  like: 'green',
  dislike: 'red',
  skip: 'gray',
  view: 'arcoblue',
}

const loadInteractions = async () => {
  loading.value = true
  try {
    const res = await getInteractions({
      page: page.value,
      page_size: pageSize.value,
      action: filterAction.value || undefined,
    })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    Message.error('获取交互历史失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (pageNum: number) => {
  page.value = pageNum
  loadInteractions()
}

const openUrl = (url: string) => {
  window.open(url, '_blank')
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadInteractions()
})
</script>

<template>
  <div class="interaction-view">
    <a-page-header title="交互历史" subtitle="查看您的浏览和反馈记录" class="page-header">
      <template #extra>
        <a-space direction="vertical" align="end" class="header-actions">
          <a-select v-model="filterAction" placeholder="筛选操作" allow-clear style="width: 140px">
            <a-option value="">全部</a-option>
            <a-option value="like">👍 喜欢</a-option>
            <a-option value="dislike">👎 不感兴趣</a-option>
            <a-option value="skip">⏭️ 跳过</a-option>
            <a-option value="view">👁️ 浏览</a-option>
          </a-select>
          <a-button type="primary" @click="loadInteractions">
            <template #icon>
              <icon-refresh />
            </template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card class="content-card">
      <div v-if="loading" class="loading-container">
        <a-spin tip="加载中..." size="large" />
      </div>

      <div v-else-if="items.length === 0" class="empty-container">
        <a-empty description="暂无交互记录" />
      </div>

      <div v-else>
        <div class="interaction-list">
          <div v-for="item in items" :key="item.id" class="interaction-item">
            <div class="item-header">
              <a-tag :color="actionColors[item.action] || 'gray'" size="small">
                {{ actionLabels[item.action] || item.action }}
              </a-tag>
              <span class="date">{{ formatDate(item.created_at) }}</span>
            </div>
            <div class="item-content" v-if="item.content">
              <a-link @click="openUrl(item.content.url)" class="title">
                {{ item.content.title }}
              </a-link>
              <p class="description" v-if="item.content.description">
                {{ item.content.description }}
              </p>
              <span class="source" v-if="item.content.source_name">
                {{ item.content.source_name }}
              </span>
            </div>
          </div>
        </div>

        <div class="pagination-container">
          <a-pagination
            :current="page"
            :page-size="pageSize"
            :total="total"
            @change="handlePageChange"
            show-total
          />
        </div>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.interaction-view {
  padding: 12px;
  max-width: 100%;
  overflow-x: hidden;
}

.page-header {
  padding: 12px 16px;
  margin-bottom: 12px;
}

.header-actions {
  align-items: flex-end;
}

.content-card {
  border-radius: 8px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.interaction-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.interaction-item {
  padding: 12px;
  border-bottom: 1px solid var(--color-fill-2, #f2f3f5);
}

.interaction-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.date {
  font-size: 12px;
  color: #999;
}

.item-content .title {
  display: block;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
}

.item-content .description {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-content .source {
  font-size: 12px;
  color: #999;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .interaction-view {
    padding: 8px;
  }

  .page-header {
    padding: 8px 12px;
    margin-bottom: 8px;
  }

  .page-header :deep(.arco-page-header-wrapper) {
    flex-direction: column;
    gap: 8px;
  }

  .header-actions {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
