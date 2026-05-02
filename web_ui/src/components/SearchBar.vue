<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { searchContents, type SearchResult } from '@/api/recommend'

const emit = defineEmits<{
  (e: 'search', results: SearchResult[]): void
  (e: 'clear'): void
  (e: 'searching', value: boolean): void
  (e: 'error', message: string): void
}>()

const query = ref('')
const isComposing = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null
let abortController: AbortController | null = null
const DEBOUNCE_MS = 300

const handleInput = () => {
  if (isComposing.value) return

  clearTimeout(debounceTimer!)
  debounceTimer = setTimeout(() => {
    search()
  }, DEBOUNCE_MS)
}

const handleCompositionStart = () => {
  isComposing.value = true
}

const handleCompositionEnd = () => {
  isComposing.value = false
  handleInput()
}

const search = async () => {
  const keyword = query.value.trim()

  // 空输入 → 恢复完整列表
  if (!keyword) {
    abortPrevious()
    emit('clear')
    return
  }

  abortPrevious()
  abortController = new AbortController()

  emit('searching', true)

  try {
    const res = await searchContents(keyword, abortController.signal)
    const results = res as unknown as SearchResult[]
    emit('search', results)
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return
    }
    const message = error instanceof Error ? error.message : '搜索暂不可用，请稍后重试'
    emit('error', message)
  } finally {
    emit('searching', false)
  }
}

const abortPrevious = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

const handleClear = () => {
  query.value = ''
  abortPrevious()
  emit('clear')
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    handleClear()
  }
}

onUnmounted(() => {
  clearTimeout(debounceTimer!)
  abortPrevious()
})
</script>

<template>
  <div class="search-bar">
    <div class="search-wrapper">
      <a-input
        v-model="query"
        placeholder="搜索标题、摘要..."
        allow-clear
        class="search-input"
        @input="handleInput"
        @keydown="handleKeydown"
        @compositionstart="handleCompositionStart"
        @compositionend="handleCompositionEnd"
        @clear="handleClear"
      >
        <template #prefix>
          <icon-search />
        </template>
      </a-input>
    </div>
  </div>
</template>

<style scoped>
.search-bar {
  margin-bottom: 24px;
  width: 100%;
}

.search-wrapper {
  max-width: 100%;
}

.search-input {
  width: 100%;
}

.search-input :deep(.arco-input-wrapper) {
  border-radius: var(--radius-pill);
  height: 48px;
  padding: 0 16px;
  border: 1px solid var(--border-lavender);
  background: var(--pure-white);
  transition: all 0.2s ease;
}

.search-input :deep(.arco-input-wrapper:hover) {
  border-color: var(--accent-blue);
}

.search-input :deep(.arco-input-wrapper:focus-within) {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(var(--accent-blue-rgb), 0.15);
}

.search-input :deep(.arco-input) {
  font-size: 16px;
}
</style>
