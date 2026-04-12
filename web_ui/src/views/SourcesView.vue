<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getSources, createSource, deleteSource, fetchSource, updateSource } from '@/api/recommend'
import { searchBiz } from '@/api/subscription'
import type { RecommendSource } from '@/api/recommend'

const loading = ref(false)
const sources = ref<RecommendSource[]>([])
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const editingId = ref<number>(0)
const form = ref({
  name: '',
  source_type: 'rss',
  url: '',
  enabled: true,
  fetch_interval: 24.0
})

// OpenCLI 配置选项
const opencliPlatforms = [
  { value: 'hackernews', label: 'HackerNews', commands: ['top', 'new', 'best', 'ask', 'show', 'job'] },
  { value: 'reddit', label: 'Reddit', commands: ['hot', 'new', 'top', 'rising'] },
  { value: 'bilibili', label: 'Bilibili', commands: ['hot', 'new', 'week', 'month'] },
  { value: 'zhihu', label: '知乎', commands: ['hot', 'new'] },
  { value: 'youtube', label: 'YouTube', commands: ['trending', 'hot'] },
  { value: 'twitter', label: 'Twitter', commands: ['home', 'user', 'search', 'trending'] },
  { value: 'devto', label: 'Dev.to', commands: ['top', 'recent'] },
  { value: 'lobsters', label: 'Lobsters', commands: ['hot', 'new', 'top'] },
  { value: 'stackoverflow', label: 'StackOverflow', commands: ['questions', 'questions tagged'] },
]

const opencliForm = ref({
  platform: 'hackernews',
  command: 'top',
  limit: 10,
})

const isOpenCLI = () => form.value.source_type === 'opencli'
const isWechat = () => form.value.source_type === 'wechat'

const updateOpenCLIUrl = () => {
  if (isOpenCLI()) {
    form.value.url = `${opencliForm.value.platform}:${opencliForm.value.command}:${opencliForm.value.limit}`
  }
}

// 公众号搜索
const wechatSearchResults = ref<any[]>([])
const wechatSearchKeyword = ref('')

const searchWechatAccounts = async (keyword: string) => {
  if (!keyword) {
    wechatSearchResults.value = []
    return
  }
  try {
    const res = await searchBiz(keyword, { kw: keyword, offset: 0, limit: 10 })
    wechatSearchResults.value = res.list || []
  } catch (error) {
    console.error('搜索公众号失败:', error)
    wechatSearchResults.value = []
  }
}

const selectWechatAccount = (account: any) => {
  form.value.name = account.nickname
  form.value.url = account.fakeid
  wechatSearchResults.value = []
  wechatSearchKeyword.value = ''
}

const loadSources = async () => {
  loading.value = true
  try {
    const res = await getSources()
    sources.value = res.items || []
  } catch (error) {
    Message.error('获取内容源失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  try {
    await createSource(form.value)
    Message.success('添加成功')
    showAddDialog.value = false
    loadSources()
    form.value = { name: '', source_type: 'rss', url: '', enabled: true, fetch_interval: 24.0 }
    opencliForm.value = { platform: 'hackernews', command: 'top', limit: 10 }
    wechatSearchKeyword.value = ''
    wechatSearchResults.value = []
  } catch (error) {
    Message.error('添加失败')
  }
}

const handleEdit = async () => {
  try {
    await updateSource(editingId.value, form.value)
    Message.success('更新成功')
    showEditDialog.value = false
    loadSources()
    form.value = { name: '', source_type: 'rss', url: '', enabled: true, fetch_interval: 24.0 }
    opencliForm.value = { platform: 'hackernews', command: 'top', limit: 10 }
  } catch (error) {
    Message.error('更新失败')
  }
}

const openEditDialog = (source: RecommendSource) => {
  editingId.value = source.id
  form.value = {
    name: source.name,
    source_type: source.source_type,
    url: source.url,
    enabled: source.enabled,
    fetch_interval: source.fetch_interval,
  }
  // 解析 OpenCLI URL
  if (source.source_type === 'opencli') {
    const parts = source.url.split(':')
    if (parts.length >= 3) {
      opencliForm.value = {
        platform: parts[0],
        command: parts[1],
        limit: parseInt(parts[2]) || 10,
      }
    }
  }
  showEditDialog.value = true
}

const handleFetch = async (id: number) => {
  try {
    await fetchSource(id)
    Message.success('抓取任务已启动')
  } catch (error) {
    Message.error('抓取失败')
  }
}

const handleDelete = async (id: number) => {
  try {
    await deleteSource(id)
    Message.success('已删除')
    loadSources()
  } catch (error) {
    Message.error('删除失败')
  }
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '从未'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadSources()
})
</script>

<template>
  <div class="sources-view">
    <a-page-header title="内容源管理" subtitle="管理推荐内容来源" class="page-header">
      <template #extra>
        <a-space direction="vertical" align="end" class="header-actions">
          <a-button type="primary" @click="showAddDialog = true">
            <template #icon>
              <icon-plus />
            </template>
            添加
          </a-button>
          <a-button @click="loadSources">
            <template #icon>
              <icon-refresh />
            </template>
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card class="content-card">
      <!-- 移动端卡片列表 -->
      <div class="mobile-list">
        <div v-if="loading" class="loading-container">
          <a-spin tip="加载中..." size="large" />
        </div>
        <div v-else-if="sources.length === 0" class="empty-container">
          <a-empty description="暂无内容源" />
        </div>
        <div v-else v-for="item in sources" :key="item.id" class="source-item">
          <div class="source-header">
            <span class="source-name">{{ item.name }}</span>
            <a-tag :color="item.enabled ? 'green' : 'gray'" size="small">
              {{ item.enabled ? '启用' : '禁用' }}
            </a-tag>
          </div>
          <div class="source-info">
            <div class="info-row">
              <span class="label">类型：</span>
              <a-tag size="small">{{ item.source_type.toUpperCase() }}</a-tag>
            </div>
            <div class="info-row">
              <span class="label">间隔：</span>
              <span>{{ item.fetch_interval }}小时</span>
            </div>
            <div class="info-row">
              <span class="label">最后抓取：</span>
              <span>{{ formatDate(item.last_fetched_at) }}</span>
            </div>
          </div>
          <div class="source-url">
            <span class="label">URL：</span>
            <span class="url-text">{{ item.url }}</span>
          </div>
          <div class="source-actions">
            <a-button type="primary" size="small" @click="handleFetch(item.id)">抓取</a-button>
            <a-button size="small" @click="openEditDialog(item)">编辑</a-button>
            <a-popconfirm content="确认删除？" @ok="handleDelete(item.id)">
              <a-button type="danger" size="small">删除</a-button>
            </a-popconfirm>
          </div>
        </div>
      </div>

      <!-- 桌面端表格 -->
      <a-table :loading="loading" :data="sources" :pagination="false" class="desktop-table">
        <template #columns>
          <a-table-column title="名称" data-index="name" />
          <a-table-column title="类型" data-index="source_type">
            <template #cell="{ record }">
              <a-tag>{{ record.source_type.toUpperCase() }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="URL/配置" data-index="url">
            <template #cell="{ record }">
              <a-tooltip :content="record.url">
                <span class="url-text">{{ record.url }}</span>
              </a-tooltip>
            </template>
          </a-table-column>
          <a-table-column title="状态" data-index="enabled">
            <template #cell="{ record }">
              <a-tag :color="record.enabled ? 'green' : 'gray'">
                {{ record.enabled ? '启用' : '禁用' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="抓取间隔" data-index="fetch_interval">
            <template #cell="{ record }">
              {{ record.fetch_interval }}小时
            </template>
          </a-table-column>
          <a-table-column title="最后抓取" data-index="last_fetched_at">
            <template #cell="{ record }">
              {{ formatDate(record.last_fetched_at) }}
            </template>
          </a-table-column>
          <a-table-column title="操作">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="handleFetch(record.id)">
                  抓取
                </a-button>
                <a-button type="text" size="small" @click="openEditDialog(record)">
                  编辑
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
    </a-card>

    <a-modal v-model:visible="showAddDialog" title="添加内容源" @ok="handleAdd" @cancel="showAddDialog = false" :width="320">
      <a-form :model="form" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model="form.name" placeholder="输入内容源名称" />
        </a-form-item>
        <a-form-item label="类型" required>
          <a-select v-model="form.source_type">
            <a-option value="rss">RSS</a-option>
            <a-option value="opencli">OpenCLI</a-option>
            <a-option value="wechat">公众号</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="isWechat()" label="公众号" required>
          <div class="wechat-search-wrapper">
            <a-input-search
              v-model="wechatSearchKeyword"
              placeholder="输入公众号名称搜索"
              search-button
              @search="searchWechatAccounts"
            />
            <div v-if="wechatSearchResults.length > 0" class="wechat-search-dropdown">
              <div
                v-for="account in wechatSearchResults"
                :key="account.fakeid"
                class="wechat-result-item"
                @click="selectWechatAccount(account)"
              >
                <img :src="account.round_head_img" class="wechat-avatar" />
                <div class="wechat-info">
                  <div class="wechat-name">{{ account.nickname }}</div>
                  <div class="wechat-signature">{{ account.signature || '暂无简介' }}</div>
                </div>
              </div>
            </div>
          </div>
        </a-form-item>
        <a-form-item v-else-if="!isOpenCLI()" label="URL/配置" required>
          <a-input v-model="form.url" placeholder="RSS URL" />
        </a-form-item>
        <template v-else>
          <a-form-item label="平台" required>
            <a-select v-model="opencliForm.platform" @change="updateOpenCLIUrl">
              <a-option v-for="p in opencliPlatforms" :key="p.value" :value="p.value">{{ p.label }}</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="内容类型" required>
            <a-select v-model="opencliForm.command" @change="updateOpenCLIUrl">
              <a-option v-for="cmd in opencliPlatforms.find(p => p.value === opencliForm.platform)?.commands" :key="cmd" :value="cmd">{{ cmd }}</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="抓取数量">
            <a-input-number v-model="opencliForm.limit" :min="1" :max="100" @change="updateOpenCLIUrl" />
          </a-form-item>
        </template>
        <a-form-item label="抓取间隔（小时）">
          <a-input-number v-model="form.fetch_interval" :min="1" :max="168" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:visible="showEditDialog" title="编辑内容源" @ok="handleEdit" @cancel="showEditDialog = false" :width="320">
      <a-form :model="form" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model="form.name" placeholder="输入内容源名称" />
        </a-form-item>
        <a-form-item label="类型" required>
          <a-select v-model="form.source_type" disabled>
            <a-option value="rss">RSS</a-option>
            <a-option value="opencli">OpenCLI</a-option>
            <a-option value="wechat">公众号</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="isWechat()" label="公众号">
          <span>{{ form.name }}</span>
        </a-form-item>
        <a-form-item v-else-if="!isOpenCLI()" label="URL/配置" required>
          <a-input v-model="form.url" placeholder="RSS URL" />
        </a-form-item>
        <template v-else>
          <a-form-item label="平台" required>
            <a-select v-model="opencliForm.platform" @change="updateOpenCLIUrl">
              <a-option v-for="p in opencliPlatforms" :key="p.value" :value="p.value">{{ p.label }}</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="内容类型" required>
            <a-select v-model="opencliForm.command" @change="updateOpenCLIUrl">
              <a-option v-for="cmd in opencliPlatforms.find(p => p.value === opencliForm.platform)?.commands" :key="cmd" :value="cmd">{{ cmd }}</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="抓取数量">
            <a-input-number v-model="opencliForm.limit" :min="1" :max="100" @change="updateOpenCLIUrl" />
          </a-form-item>
        </template>
        <a-form-item label="启用状态">
          <a-switch v-model="form.enabled" />
        </a-form-item>
        <a-form-item label="抓取间隔（小时）">
          <a-input-number v-model="form.fetch_interval" :min="1" :max="168" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.sources-view {
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

.url-text {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 移动端卡片列表 */
.mobile-list {
  display: none;
}

.source-item {
  padding: 12px;
  border-bottom: 1px solid var(--color-fill-2, #f2f3f5);
}

.source-item:last-child {
  border-bottom: none;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.source-name {
  font-weight: 600;
  font-size: 15px;
}

.source-info {
  margin-bottom: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  font-size: 13px;
  margin-bottom: 4px;
  color: #666;
}

.info-row .label {
  color: #999;
  min-width: 60px;
}

.source-url {
  font-size: 12px;
  margin-bottom: 8px;
  word-break: break-all;
}

.source-url .label {
  color: #999;
}

.source-actions {
  display: flex;
  gap: 8px;
}

.desktop-table {
  display: block;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .sources-view {
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
    align-items: center;
  }

  .mobile-list {
    display: block;
  }

  .desktop-table {
    display: none;
  }

  .arco-modal {
    max-width: calc(100vw - 32px);
  }
}

.wechat-search-wrapper {
  position: relative;
  width: 100%;
}

.wechat-search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--color-bg-1, #fff);
  border: 1px solid var(--color-border, #e5e6e8);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  max-height: 280px;
  overflow-y: auto;
  z-index: 100;
}

.wechat-result-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-fill-2, #f2f3f5);
  transition: background-color 0.2s;
}

.wechat-result-item:last-child {
  border-bottom: none;
}

.wechat-result-item:hover {
  background-color: var(--color-fill-1, #f7f8fa);
}

.wechat-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  margin-right: 12px;
  flex-shrink: 0;
  object-fit: cover;
}

.wechat-info {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wechat-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--color-text-1, #1a1a1a);
}

.wechat-signature {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
