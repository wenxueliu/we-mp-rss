<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getContents } from '@/api/recommend'
import type { RecommendContent, SearchResult } from '@/api/recommend'
import RecommendationCard from '@/components/RecommendationCard.vue'
import SearchBar from '@/components/SearchBar.vue'

const loading = ref(false)
const contents = ref<RecommendContent[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStatus = ref('')

// 搜索状态
const isSearching = ref(false)
const searchResults = ref<SearchResult[]>([])
const searchError = ref('')
const isSearchActive = ref(false)

watch(filterStatus, () => {
  page.value = 1
  loadContents()
})

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
  isSearchActive.value = false
  searchResults.value = []
  searchError.value = ''
  loadContents()
}

const handleInteract = () => {
  loadContents()
}

// 搜索事件处理
const handleSearch = (results: SearchResult[]) => {
  isSearchActive.value = true
  searchResults.value = results
  searchError.value = ''
}

const handleSearchClear = () => {
  isSearchActive.value = false
  searchResults.value = []
  searchError.value = ''
}

const handleSearching = (value: boolean) => {
  isSearching.value = value
}

const handleSearchError = (message: string) => {
  isSearchActive.value = true
  searchError.value = message
  searchResults.value = []
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
            <a-option value="recommended">推荐</a-option>
            <a-option value="not_recommended">不推荐</a-option>
            <a-option value="pending">待定</a-option>
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

    <!-- 搜索栏 -->
    <SearchBar
      @search="handleSearch"
      @clear="handleSearchClear"
      @searching="handleSearching"
      @error="handleSearchError"
    />

    <a-card class="content-card">
      <!-- 搜索加载中 -->
      <div v-if="isSearching" class="status-container">
        <a-spin tip="搜索中..." size="large" />
      </div>

      <!-- 搜索错误 -->
      <div v-else-if="isSearchActive && searchError" class="status-container">
        <a-result status="error" title="搜索暂不可用" :subtitle="searchError">
          <template #extra>
            <a-button type="primary" @click="handleRefresh">返回推荐列表</a-button>
          </template>
        </a-result>
      </div>

      <!-- 搜索无结果 -->
      <div v-else-if="isSearchActive && searchResults.length === 0 && !isSearching" class="status-container">
        <a-empty description="未找到匹配内容" />
      </div>

      <!-- 搜索有结果 -->
      <div v-else-if="isSearchActive && searchResults.length > 0">
        <RecommendationCard
          v-for="item in searchResults"
          :key="item.id"
          :item="item as RecommendContent"
          @interact="handleInteract"
        />
      </div>

      <!-- 默认推荐列表 -->
      <template v-else>
        <div v-if="loading" class="status-container">
          <a-spin tip="加载中..." size="large" />
        </div>

        <div v-else-if="contents.length === 0" class="status-container">
          <a-empty description="暂无推荐内容" />
        </div>

        <div v-else>
          <RecommendationCard
            v-for="item in contents"
            :key="item.id"
            :item="item"
            @interact="handleInteract"
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
      </template>
    </a-card>
  </div>
</template>

<style scoped>
.recommend-view {
  padding: 48px 24px;
  max-width: 1200px;
  margin: 0 auto;
  overflow-x: hidden;
  background: var(--cloud-gray);
  min-height: 100vh;
}

.page-header {
  padding: 0 0 32px 0;
  margin-bottom: 32px;
  border-bottom: 1px solid var(--border-lavender);
}

.page-header :deep(.arco-page-header-title) {
  font-size: 32px !important;
  font-weight: 700 !important;
  color: var(--expo-black) !important;
  letter-spacing: -1px;
}

.page-header :deep(.arco-page-header-subtitle) {
  font-size: 16px !important;
  color: var(--slate-gray) !important;
}

.page-header :deep(.arco-page-header-wrapper) {
  justify-content: space-between;
  align-items: flex-start;
}

.header-actions {
  width: auto;
}

.header-actions :deep(.arco-select-view),
.header-actions :deep(.arco-btn) {
  border-radius: var(--radius-pill) !important;
}

.content-card {
  border-radius: var(--radius-comfortable) !important;
  border: 1px solid var(--border-lavender) !important;
  box-shadow: var(--shadow-whisper);
  background: var(--pure-white);
  padding: 24px;
}

.status-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  overflow-x: auto;
}

.pagination-container :deep(.arco-pagination) {
  justify-content: center;
}

@media (max-width: 768px) {
  .recommend-view {
    padding: 24px 16px;
  }

  .page-header {
    padding: 0 0 24px 0;
    margin-bottom: 24px;
  }

  .page-header :deep(.arco-page-header-wrapper) {
    flex-direction: column;
    gap: 16px;
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

  .content-card {
    padding: 16px;
  }
}
</style>
