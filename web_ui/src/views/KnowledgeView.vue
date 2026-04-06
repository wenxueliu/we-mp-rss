<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getKnowledge, deleteFromKnowledge } from '@/api/recommend'
import type { KnowledgeItem } from '@/api/recommend'

const loading = ref(false)
const items = ref<KnowledgeItem[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const loadKnowledge = async () => {
  loading.value = true
  try {
    const res = await getKnowledge({ page: page.value, page_size: pageSize.value })
    items.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    Message.error('获取知识库失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteFromKnowledge(id)
    Message.success('已删除')
    loadKnowledge()
  } catch (error) {
    Message.error('删除失败')
  }
}

const openUrl = (url: string) => {
  window.open(url, '_blank')
}

const handlePageChange = (pageNum: number) => {
  page.value = pageNum
  loadKnowledge()
}

onMounted(() => {
  loadKnowledge()
})
</script>

<template>
  <div class="knowledge-view">
    <a-page-header title="知识库" subtitle="管理收藏的内容">
      <template #extra>
        <a-button type="primary" @click="loadKnowledge">
          <template #icon>
            <icon-refresh />
          </template>
          刷新
        </a-button>
      </template>
    </a-page-header>

    <a-card>
      <a-table
        v-if="!loading && items.length > 0"
        :loading="loading"
        :data="items"
        :pagination="{ current: page, pageSize: pageSize, total: total, showTotal: true }"
        @page-change="handlePageChange"
      >
        <template #columns>
          <a-table-column title="标题" data-index="title">
            <template #cell="{ record }">
              <a-link @click="openUrl(record.url)">{{ record.title }}</a-link>
            </template>
          </a-table-column>
          <a-table-column title="分类" data-index="category">
            <template #cell="{ record }">
              <a-tag v-if="record.category">{{ record.category }}</a-tag>
              <span v-else class="no-category">无</span>
            </template>
          </a-table-column>
          <a-table-column title="标签" data-index="tags">
            <template #cell="{ record }">
              <a-tag v-for="tag in (record.tags || [])" :key="tag" size="small">{{ tag }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="访问次数" data-index="access_count" />
          <a-table-column title="创建时间" data-index="created_at" />
          <a-table-column title="操作">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="openUrl(record.url)">
                  查看
                </a-button>
                <a-popconfirm content="确认删除？" @ok="handleDelete(record.id)">
                  <a-button type="text" status="danger" size="small">
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>

      <div v-else-if="loading" class="loading-container">
        <a-spin tip="加载中..." size="large" />
      </div>

      <div v-else class="empty-container">
        <a-empty description="暂无收藏内容" />
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.knowledge-view {
  padding: 12px;
  max-width: 100%;
  overflow-x: hidden;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.no-category {
  color: #999;
}

@media (max-width: 768px) {
  .knowledge-view {
    padding: 8px;
  }
}
</style>