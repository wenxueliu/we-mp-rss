<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { getSources, createSource, deleteSource, fetchSource } from '@/api/recommend'
import type { RecommendSource } from '@/api/recommend'

const loading = ref(false)
const sources = ref<RecommendSource[]>([])
const showAddDialog = ref(false)
const form = ref({
  name: '',
  source_type: 'rss',
  url: '',
  enabled: true,
  fetch_interval: 24.0
})

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
  } catch (error) {
    Message.error('添加失败')
  }
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
    <a-page-header title="内容源管理" subtitle="管理推荐内容来源">
      <template #extra>
        <a-space>
          <a-button type="primary" @click="showAddDialog = true">
            <template #icon>
              <icon-plus />
            </template>
            添加内容源
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

    <a-card>
      <a-table :loading="loading" :data="sources">
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

      <div v-if="!loading && sources.length === 0" class="empty-container">
        <a-empty description="暂无内容源" />
      </div>
    </a-card>

    <a-modal v-model:visible="showAddDialog" title="添加内容源" @ok="handleAdd" @cancel="showAddDialog = false">
      <a-form :model="form" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model="form.name" placeholder="输入内容源名称" />
        </a-form-item>
        <a-form-item label="类型" required>
          <a-select v-model="form.source_type">
            <a-option value="rss">RSS</a-option>
            <a-option value="opencli">OpenCLI</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="URL/配置" required>
          <a-input v-model="form.url" :placeholder="form.source_type === 'rss' ? 'RSS URL' : '如 hackernews:top:10'" />
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
  padding: 16px;
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
</style>