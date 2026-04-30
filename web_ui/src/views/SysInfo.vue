<template>
  <div class="sys-info-page">
    <!-- Expo-style Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="headline-section">系统信息</h1>
        <p class="text-body-large">版本 {{ sysInfo.version }}</p>
      </div>
      <div class="header-badge">
        <span class="badge-pill">
          <span class="badge-dot" :class="{ warning: !sysInfo.queue?.is_running }"></span>
          {{ sysInfo.queue?.is_running ? '队列运行中' : '队列已停止' }}
        </span>
      </div>
    </div>

    <!-- System Resources Card -->
    <div class="card-expo page-section">
      <div class="card-header">
        <h2 class="headline-card">系统资源</h2>
      </div>
      <div class="card-body">
        <SystemResources :resources="sysInfo.resources" />
      </div>
    </div>

    <!-- Article Statistics Card -->
    <div class="card-expo page-section">
      <div class="card-header">
        <h2 class="headline-card">文章统计</h2>
      </div>
      <div class="card-body">
        <a-descriptions :column="{ xs: 1, sm: 2, md: 2, lg: 3 }" :bordered="false" class="expo-descriptions">
          <a-descriptions-item class="desc-item">
            <span class="desc-label">公众号总数</span>
            <span class="desc-value">{{ sysInfo.article?.mp_all_count || 0 }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">文章总数</span>
            <span class="desc-value">{{ sysInfo.article?.all_count || 0 }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">无正文数量</span>
            <span class="desc-value">{{ sysInfo.article?.no_content_count || 0 }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">有正文数量</span>
            <span class="desc-value">{{ sysInfo.article?.has_content_count || 0 }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">已删除</span>
            <span class="desc-value">{{ sysInfo.article?.wrong_count || 0 }}</span>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </div>

    <!-- System Info Card -->
    <div class="card-expo page-section">
      <div class="card-header">
        <h2 class="headline-card">系统详情</h2>
      </div>
      <div class="card-body">
        <a-descriptions :column="{ xs: 1, sm: 1, md: 2, lg: 2 }" :bordered="false" class="expo-descriptions">
          <a-descriptions-item class="desc-item">
            <span class="desc-label">操作系统</span>
            <span class="desc-value">{{ sysInfo.os.name }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">Docker版本</span>
            <span class="desc-value">{{ sysInfo.os.docker_version }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">系统版本</span>
            <span class="desc-value">{{ sysInfo.os.version }} ({{ sysInfo.os.release }})</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">Python版本</span>
            <span class="desc-value">{{ sysInfo.python_version }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">运行时间</span>
            <span class="desc-value">{{ formatUptime(sysInfo.uptime) }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">系统架构</span>
            <span class="desc-value">{{ sysInfo.system.node }} / {{ sysInfo.system.machine }} ({{ sysInfo.system.processor }})</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">TOKEN</span>
            <span class="desc-value mono">{{ sysInfo.wx.token }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">过期时间</span>
            <span class="desc-value">{{ !sysInfo.wx.login ? '未登录' : sysInfo.wx.expiry_time }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">API版本</span>
            <span class="desc-value">{{ sysInfo.api_version }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">队列状态</span>
            <span class="desc-value">{{ sysInfo.queue.is_running || false ? '运行中' : '已停止' }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">挂起队列数量</span>
            <span class="desc-value">{{ sysInfo.queue.pending_tasks || 0 }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">核心版本</span>
            <span class="desc-value">{{ sysInfo.core_version }}</span>
          </a-descriptions-item>
          <a-descriptions-item class="desc-item">
            <span class="desc-label">最新版本</span>
            <span class="desc-value">{{ sysInfo.latest_version }}</span>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { getSysInfo } from "@/api/sysInfo";
import type { SysInfo } from "@/api/sysInfo";
import SystemResources from "@/components/SystemResources.vue";

const sysInfo = ref<SysInfo>({
  os: { name: "", version: "", release: "" },
  python_version: "",
  uptime: 0,
  system: { node: "", machine: "", processor: "" },
  api_version: "/api/v1/wx",
  core_version: "",
  latest_version: "",
  need_update: true,
  wx: { token: "", expiry_time: "" },
  queue: { is_running: false, pending_tasks: 0 },
});

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}天 ${hours}小时 ${minutes}分钟`;
};

onMounted(async () => {
  sysInfo.value = await getSysInfo()
});
</script>

<style scoped>
.sys-info-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
}

/* Page Header - Expo Style */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--border-lavender);
}

.header-content .headline-section {
  margin-bottom: 8px;
}

.header-badge {
  margin-top: 8px;
}

/* Card Expo Override for this page */
.card-expo {
  margin-bottom: 0;
}

.page-section {
  margin-bottom: 48px;
}

.card-header {
  margin-bottom: 24px;
}

.card-header .headline-card {
  color: var(--near-black);
}

.card-body {
  color: var(--slate-gray);
}

/* Expo Descriptions */
.expo-descriptions {
  display: grid;
  gap: 24px;
}

:deep(.arco-descriptions-item) {
  padding-bottom: 0 !important;
}

.desc-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.desc-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--silver);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.desc-value {
  font-size: 16px;
  font-weight: 500;
  color: var(--near-black);
}

.desc-value.mono {
  font-family: var(--font-mono);
  font-size: 14px;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .sys-info-page {
    padding: 24px 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .page-section {
    margin-bottom: 32px;
  }

  .headline-section {
    font-size: 32px !important;
    letter-spacing: -1.5px !important;
  }
}
</style>
