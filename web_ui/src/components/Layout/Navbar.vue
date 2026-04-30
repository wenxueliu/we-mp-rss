<template>
  <a-layout-header class="navbar">
    <div class="navbar-container">
      <a-menu
        mode="horizontal"
        :selected-keys="selectedKeys"
        @menu-item-click="handleMenuClick"
        class="navbar-menu"
      >
        <a-menu-item key="/" class="nav-item">
          <template #icon>
            <icon-home />
          </template>
          <span class="nav-text">订阅管理</span>
        </a-menu-item>
        <a-menu-item key="/recommend" class="nav-item">
          <template #icon>
            <icon-thumb-up />
          </template>
          <span class="nav-text">推荐内容</span>
        </a-menu-item>
        <a-menu-item key="/interaction-history" class="nav-item">
          <template #icon>
            <icon-history />
          </template>
          <span class="nav-text">交互历史</span>
        </a-menu-item>
        <a-menu-item key="/sources" class="nav-item">
          <template #icon>
            <icon-link />
          </template>
          <span class="nav-text">内容源</span>
        </a-menu-item>
        <a-menu-item key="/wechat-status" class="nav-item">
          <template #icon>
            <icon-wechat />
          </template>
          <span class="nav-text">授权管理</span>
        </a-menu-item>
        <a-menu-item key="/export/records" class="nav-item">
          <template #icon>
            <icon-export />
          </template>
          <span class="nav-text">导出记录</span>
        </a-menu-item>
        <a-menu-item key="/tags" class="nav-item">
          <template #icon>
            <icon-tag />
          </template>
          <span class="nav-text">标签管理</span>
        </a-menu-item>
        <a-menu-item key="/message-tasks" class="nav-item">
          <template #icon>
            <icon-notification />
          </template>
          <span class="nav-text">消息任务</span>
        </a-menu-item>
        <a-menu-item key="/filter-rules" class="nav-item">
          <template #icon>
            <icon-filter />
          </template>
          <span class="nav-text">过滤规则</span>
        </a-menu-item>
        <a-menu-item key="/task-queue" class="nav-item">
          <template #icon>
            <icon-list />
          </template>
          <span class="nav-text">任务队列</span>
        </a-menu-item>
        <a-menu-item key="/cascade/feed-status" class="nav-item">
          <template #icon>
            <icon-storage />
          </template>
          <span class="nav-text">公众号状态</span>
        </a-menu-item>
        <a-menu-item key="/cascade" class="nav-item">
          <template #icon>
            <icon-share-external />
          </template>
          <span class="nav-text">级联管理</span>
        </a-menu-item>
        <a-menu-item key="/access-keys" class="nav-item">
          <template #icon>
            <icon-lock />
          </template>
          <span class="nav-text">Access Key</span>
        </a-menu-item>
        <a-menu-item key="/env-exception" class="nav-item">
          <template #icon>
            <icon-exclamation-circle />
          </template>
          <span class="nav-text">异常统计</span>
        </a-menu-item>
        <a-menu-item key="/configs" class="nav-item">
          <template #icon>
            <icon-settings />
          </template>
          <span class="nav-text">配置信息</span>
        </a-menu-item>
        <a-menu-item key="/sys-info" class="nav-item">
          <template #icon>
            <icon-info-circle />
          </template>
          <span class="nav-text">系统信息</span>
        </a-menu-item>
      </a-menu>
    </div>
  </a-layout-header>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const selectedKeys = ref<string[]>(['/'])

watchEffect(() => {
  selectedKeys.value = [route.path]
})

const handleMenuClick = (key: string) => {
  if (route.path === key) return
  router.push(key).catch((err) => {
    if (!err.message?.includes('Avoided redundant navigation')) {
      console.error('路由导航失败:', err)
    }
  })
}
</script>

<style scoped>
.navbar {
  background: var(--pure-white) !important;
  border-bottom: 1px solid var(--border-lavender);
  padding: 0 !important;
  height: auto !important;
  line-height: normal;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.navbar-menu {
  background: transparent !important;
  border-bottom: none !important;
}

/* Expo-style menu items */
:deep(.arco-menu-item) {
  color: var(--slate-gray) !important;
  font-weight: 500;
  border-radius: var(--radius-pill) !important;
  padding: 8px 16px !important;
  margin: 8px 4px !important;
  transition: all 0.2s ease !important;
}

:deep(.arco-menu-item:hover) {
  color: var(--near-black) !important;
  background: var(--cloud-gray) !important;
}

:deep(.arco-menu-item.arco-menu-selected) {
  color: var(--expo-black) !important;
  background: var(--cloud-gray) !important;
  font-weight: 600;
}

:deep(.arco-menu-item .arco-icon) {
  color: var(--slate-gray) !important;
  transition: color 0.2s ease !important;
}

:deep(.arco-menu-item:hover .arco-icon) {
  color: var(--near-black) !important;
}

:deep(.arco-menu-item.arco-menu-selected .arco-icon) {
  color: var(--expo-black) !important;
}

.nav-text {
  font-size: 14px;
}

/* Responsive: hide text on smaller screens, show icons */
@media (max-width: 1024px) {
  :deep(.arco-menu-item) {
    padding: 8px 12px !important;
  }
  .nav-text {
    display: none;
  }
}

@media (max-width: 768px) {
  .navbar-container {
    padding: 0 12px;
    overflow-x: auto;
  }

  :deep(.arco-menu-item) {
    padding: 8px !important;
    margin: 8px 2px !important;
  }

  .nav-text {
    display: none;
  }
}
</style>
