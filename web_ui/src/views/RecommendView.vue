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
    <a-page-header title="推荐内容" subtitle="个性化内容推荐">
      <template #extra>
        <a-space>
          <a-select v-model="filterStatus" placeholder="状态筛选" allow-clear style="width: 150px">
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

    <a-card>
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
          />
        </div>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.recommend-view {
  padding: 16px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>