<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getContents } from '@/api/recommend'
import type { RecommendContent } from '@/api/recommend'
import RecommendationCard from '@/components/RecommendationCard.vue'

const loading = ref(false)
const contents = ref<RecommendContent[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStatus = ref('')

const loadContents = async () => {
  loading.value = true
  try {
    const res = await getContents({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
    })
    contents.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    Message.error('获取推荐内容失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (pageNum: number) => {
  page.value = pageNum
  loadContents()
}

const handleRefresh = () => {
  loadContents()
}

onMounted(() => {
  loadContents()
})
</script>

<template>
  <div class="recommend-view">
    <a-page-header title="推荐内容" subtitle="个性化内容推荐" class="page-header">
      <template #extra>
        <a-space direction="vertical" align="end" class="header-actions">
          <a-select v-model="filterStatus" placeholder="状态筛选" allow-clear style="width: 140px">
            <a-option value="">全部</a-option>
            <a-option value="pending">待处理</a-option>
            <a-option value="recommended">推荐</a-option>
            <a-option value="accepted">已接受</a-option>
            <a-option value="rejected">已拒绝</a-option>
          </a-select>
          <a-button type="primary" @click="handleRefresh">
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

      <div v-else-if="contents.length === 0" class="empty-container">
        <a-empty description="暂无推荐内容" />
      </div>

      <div v-else>
        <RecommendationCard
          v-for="item in contents"
          :key="item.id"
          :item="item"
        />

        <div class="pagination-container">
          <a-pagination
            :current="page"
            :page-size="pageSize"
            :total="total"
            @change="handlePageChange"
            show-total
            :page-size-options="[10, 20, 50]"
            :show-page-size="true"
          />
        </div>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.recommend-view {
  padding: 12px;
  max-width: 100%;
  overflow-x: hidden;
}

.page-header {
  padding: 12px 16px;
  margin-bottom: 12px;
}

.page-header :deep(.arco-page-header-title) {
  font-size: 18px;
}

.page-header :deep(.arco-page-header-subtitle) {
  font-size: 13px;
}

.header-actions {
  width: 100%;
}

.content-card {
  border-radius: 8px;
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

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .recommend-view {
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

  .header-actions .arco-space {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
