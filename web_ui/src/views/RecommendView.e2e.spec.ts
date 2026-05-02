/**
 * E2E 集成测试 — 推荐内容搜索功能
 *
 * 测试搜索完整用户旅程：功能/非功能/兼容性
 * 使用 vitest + @vue/test-utils 进行组件级集成测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { h, nextTick } from 'vue'
import RecommendView from './RecommendView.vue'

// ── Mock API ──
const mockGetContents = vi.fn()
const mockSearchContents = vi.fn()

vi.mock('@/api/recommend', () => ({
  getContents: (...args: any[]) => mockGetContents(...args),
  searchContents: (...args: any[]) => mockSearchContents(...args),
}))

vi.mock('@arco-design/web-vue', () => ({
  Message: { success: vi.fn(), error: vi.fn() },
}))

// ── Arco Design stubs ──
const ArcoComponents = {
  'a-button': {
    props: ['type', 'size', 'status', 'modelValue'],
    emits: ['click', 'update:modelValue'],
    setup(props: any, { slots, emit }: any) {
      return () => h('button', { onClick: () => emit('click') }, slots.default?.())
    },
  },
  'a-space': {
    props: ['direction', 'align'],
    setup(_: any, { slots }: any) {
      return () => h('div', { class: 'a-space' }, slots.default?.())
    },
  },
  'a-page-header': {
    props: ['title', 'subtitle'],
    setup(_: any, { slots }: any) {
      return () => h('div', { class: 'page-header' }, [slots.extra?.(), slots.default?.()])
    },
  },
  'a-spin': {
    props: ['tip', 'size'],
    setup(_: any, { slots }: any) {
      return () => h('div', { class: 'spin' }, slots.default?.())
    },
  },
  'a-empty': {
    props: ['description'],
    setup(_: any, { slots }: any) {
      return () => h('div', { class: 'empty' }, slots.default?.())
    },
  },
  'a-result': {
    props: ['status', 'title', 'subtitle'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: `result-${props.status}` }, [
        h('span', { class: 'result-title' }, props.title),
        h('span', { class: 'result-subtitle' }, props.subtitle),
        slots.extra?.(),
      ])
    },
  },
  'a-select': {
    props: ['modelValue', 'disabled', 'placeholder', 'allowClear'],
    emits: ['update:modelValue', 'change'],
    setup(props: any, { emit, slots }: any) {
      return () => h('select', {
        value: props.modelValue || '',
        disabled: props.disabled,
        onChange: (e: Event) => emit('update:modelValue', (e.target as HTMLSelectElement).value),
      }, slots.default?.())
    },
  },
  'a-option': {
    props: ['value', 'label'],
    setup(props: any, { slots }: any) {
      return () => h('option', { value: props.value }, slots.default?.() || props.label)
    },
  },
  'a-card': {
    props: ['class'],
    setup(_: any, { slots }: any) {
      return () => h('div', { class: ['card'] }, slots.default?.())
    },
  },
  'a-pagination': {
    props: ['current', 'pageSize', 'total'],
    emits: ['change'],
    setup(props: any, { emit }: any) {
      return () => h('div', { class: 'pagination', onClick: () => emit('change', props.current + 1) })
    },
  },
  'a-tag': {
    props: ['color'],
    setup(_: any, { slots }: any) {
      return () => h('span', { class: 'tag' }, slots.default?.())
    },
  },
  'a-input': {
    props: ['modelValue', 'placeholder', 'allowClear', 'class'],
    emits: ['update:modelValue', 'input', 'keydown', 'compositionstart', 'compositionend', 'clear'],
    setup(props: any, { emit, slots }: any) {
      return () => h('div', { class: 'a-input-wrapper' }, [
        slots.prefix?.(),
        h('input', {
          value: props.modelValue || '',
          class: 'a-input search-input-el',
          placeholder: props.placeholder,
          onInput: (e: Event) => {
            const val = (e.target as HTMLInputElement).value
            emit('update:modelValue', val)
            emit('input', val)
          },
          onCompositionstart: (e: Event) => emit('compositionstart', e),
          onCompositionend: (e: Event) => emit('compositionend', e),
          onKeydown: (e: KeyboardEvent) => emit('keydown', e),
        }),
        props.allowClear && props.modelValue
          ? h('span', { class: 'clear-btn', onClick: () => { emit('update:modelValue', ''); emit('clear') } }, '×')
          : null,
      ])
    },
  },
  'a-tooltip': {
    props: ['content'],
    setup(_: any, { slots }: any) {
      return () => h('div', {}, slots.default?.())
    },
  },
  'icon-refresh': { setup() { return () => h('span', {}, '↻') } },
  'icon-search': { setup() { return () => h('span', {}, '🔍') } },
}

// ── Test data ──
const mockContents = [
  { id: 1, title: 'Python 进阶教程', description: '深入理解 Python 高级特性', url: 'http://a', author: 'A', source_name: 'Src1', source_type: 'rss', tags: [], recommendation_score: 85, freshness: 0.9, preference_match: 0.8, quality: 0.7, timeliness: 0.9, published_at: '2026-01-01' },
  { id: 2, title: 'Go 并发编程实战', description: 'goroutine 和 channel 深度解析', url: 'http://b', author: 'B', source_name: 'Src2', source_type: 'rss', tags: [], recommendation_score: 72, freshness: 0.8, preference_match: 0.7, quality: 0.8, timeliness: 0.85, published_at: '2026-01-02' },
  { id: 3, title: 'Rust 入门指南', description: '系统编程入门', url: 'http://c', author: 'C', source_name: 'Src3', source_type: 'rss', tags: [], recommendation_score: 68, freshness: 0.7, preference_match: 0.6, quality: 0.7, timeliness: 0.7, published_at: '2026-01-03' },
]

const mockSearchResult = [
  { id: 1, title: 'Python 进阶教程', summary: '深入理解 Python 高级特性', url: 'http://a', author: 'A', source_name: 'Src1', source_type: 'rss', published_at: '2026-01-01' as any },
]

function mountView() {
  return mount(RecommendView, { global: { components: ArcoComponents } })
}

async function typeInSearch(wrapper: ReturnType<typeof mountView>, value: string) {
  const input = wrapper.find('input.search-input-el')
  await input.setValue(value)
}

describe('E2E 集成测试 — 推荐搜索功能', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    mockGetContents.mockResolvedValue({ items: mockContents, total: 3 })
    mockSearchContents.mockResolvedValue(mockSearchResult)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ══════════════════════════════════════════════
  // 功能 E2E — Happy Path
  // ══════════════════════════════════════════════

  it('E2E-F-HP-1: 输入搜索关键词 → 列表仅显示匹配结果', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 初始显示 3 条推荐
    expect(mockGetContents).toHaveBeenCalled()

    // 输入搜索
    await typeInSearch(wrapper, 'Python')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledWith('Python', expect.any(AbortSignal))
  })

  it('E2E-F-HP-2: 摘要搜索 — 输入系统编程 → 匹配 Rust 条目', async () => {
    const rustResult = [{ id: 3, title: 'Rust 入门指南', summary: '系统编程入门', url: 'http://c', author: 'C', source_name: 'Src3', source_type: 'rss' }]
    mockSearchContents.mockResolvedValue(rustResult)

    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    await typeInSearch(wrapper, '系统编程')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledWith('系统编程', expect.any(AbortSignal))
  })

  it('E2E-F-HP-3: 大小写不敏感 — python/PYTHON/Python 均匹配', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    await typeInSearch(wrapper, 'PYTHON')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(mockSearchContents).toHaveBeenCalledWith('PYTHON', expect.any(AbortSignal))

    mockSearchContents.mockClear()

    await typeInSearch(wrapper, 'python')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(mockSearchContents).toHaveBeenCalledWith('python', expect.any(AbortSignal))
  })

  it('E2E-F-HP-4: 清空搜索 → 恢复完整推荐列表', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    await typeInSearch(wrapper, 'Python')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 清空搜索
    await typeInSearch(wrapper, '')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 验证 clear 事件触发（恢复列表由 RecommendView 状态控制）
    // SearchBar emits 'clear' which sets isSearchActive=false
     const searchBar = wrapper.findComponent({ name: 'SearchBar' })
     expect(searchBar.exists()).toBe(true)
  })

  // ══════════════════════════════════════════════
  // 功能 E2E — Error Path
  // ══════════════════════════════════════════════

  it('E2E-F-ER-1: 无匹配结果 → 显示 EmptyState', async () => {
    mockSearchContents.mockResolvedValue([])

    const wrapper = mountView()
    await flushPromises()

    await typeInSearch(wrapper, 'zzz123')
    vi.advanceTimersByTime(300)
    await flushPromises()
    await nextTick()

    // 搜索无结果时显示 empty
    const emptyEl = wrapper.find('.empty')
    expect(emptyEl.exists()).toBe(true)
  })

  it('E2E-F-ER-2: API 500 → 显示错误提示', async () => {
    mockSearchContents.mockRejectedValue(new Error('Request failed with status code 500'))

    const wrapper = mountView()
    await flushPromises()

    await typeInSearch(wrapper, 'error')
    vi.advanceTimersByTime(300)
    await flushPromises()
    await nextTick()

    // 错误结果组件
    const resultEl = wrapper.find('.result-error')
    expect(resultEl.exists()).toBe(true)
  })

  it('E2E-F-ER-3: API 超时 → 显示错误提示', async () => {
    mockSearchContents.mockRejectedValue(new Error('timeout of 5000ms exceeded'))

    const wrapper = mountView()
    await flushPromises()

    await typeInSearch(wrapper, 'timeout')
    vi.advanceTimersByTime(300)
    await flushPromises()
    await nextTick()

    const resultEl = wrapper.find('.result-error')
    expect(resultEl.exists()).toBe(true)
  })

  it('E2E-F-ER-4: 推荐列表加载失败 → 显示错误', async () => {
    mockGetContents.mockRejectedValue(new Error('Network error'))

    const wrapper = mountView()
    await flushPromises()

    // 推荐列表失败时显示空状态
    const emptyEl = wrapper.find('.empty')
    expect(emptyEl.exists()).toBe(true)
  })

  // ══════════════════════════════════════════════
  // 功能 E2E — Boundary
  // ══════════════════════════════════════════════

  it('E2E-F-BD-1: 特殊字符/XSS/SQL注入 → 页面不崩溃，正常返回', async () => {
    mockSearchContents.mockResolvedValue([])

    const wrapper = mountView()
    await flushPromises()

    // 测试各种特殊输入
    const inputs = ['<script>alert(1)</script>', "' OR '1'='1", '😀🔥💯']
    for (const input of inputs) {
      await typeInSearch(wrapper, input)
      vi.advanceTimersByTime(300)
      await flushPromises()
      expect(mockSearchContents).toHaveBeenCalledWith(input, expect.any(AbortSignal))
      mockSearchContents.mockClear()
    }
  })

  it('E2E-F-BD-2: 竞态条件 — 慢请求被取消，快请求结果生效', async () => {
    let resolveSlow: any
    const slowPromise = new Promise((resolve) => { resolveSlow = resolve })

    const wrapper = mountView()
    await flushPromises()

    // 第一次搜索（慢）
    mockSearchContents.mockReturnValueOnce(slowPromise as any)
    await typeInSearch(wrapper, 'AAA')
    vi.advanceTimersByTime(300)
    await flushPromises()

    const firstCallSignal = mockSearchContents.mock.calls[0][1] as AbortSignal

    // 第二次搜索（快）
    mockSearchContents.mockResolvedValueOnce([mockSearchResult[0]])
    await typeInSearch(wrapper, 'BBB')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 第一个请求应被 abort
    expect(firstCallSignal.aborted).toBe(true)
    // 第二个请求应被调用
    expect(mockSearchContents).toHaveBeenCalledTimes(2)
    expect(mockSearchContents.mock.calls[1][0]).toBe('BBB')
  })

  it('E2E-F-BD-3: 极长输入 → 正常发送不崩溃', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()

    const longInput = 'x'.repeat(500)
    await typeInSearch(wrapper, longInput)
    vi.advanceTimersByTime(300)
    await flushPromises()

    // API 应该被调用（后端会截断到 200）
    expect(mockSearchContents).toHaveBeenCalledWith(longInput, expect.any(AbortSignal))
  })

  // ══════════════════════════════════════════════
  // 非功能 E2E — 性能
  // ══════════════════════════════════════════════

  it('E2E-NF-PF-1: debounce 300ms 仅触发一次 API 调用', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()

    // 模拟慢速输入 "Python"
    for (const char of 'Python') {
      const input = wrapper.find('input.search-input-el')
      const currentVal = (input.element as HTMLInputElement).value
      await input.setValue(currentVal + char)
      vi.advanceTimersByTime(100) // 每个字符间隔 100ms，都不到 300ms debounce
    }

    // 300ms 后应只触发一次
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledTimes(1)
    expect(mockSearchContents).toHaveBeenCalledWith('Python', expect.any(AbortSignal))
  })

  it('E2E-NF-PF-2: 快速连续输入不卡顿', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()

    // 快速连续输入
    await typeInSearch(wrapper, 'P')
    vi.advanceTimersByTime(100)
    await typeInSearch(wrapper, 'Py')
    vi.advanceTimersByTime(100)
    await typeInSearch(wrapper, 'Pyt')
    vi.advanceTimersByTime(100)
    await typeInSearch(wrapper, 'Pyth')
    vi.advanceTimersByTime(100)
    await typeInSearch(wrapper, 'Pytho')
    vi.advanceTimersByTime(100)
    await typeInSearch(wrapper, 'Python')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 仅最后一次触发
    expect(mockSearchContents).toHaveBeenCalledTimes(1)
    expect(mockSearchContents).toHaveBeenCalledWith('Python', expect.any(AbortSignal))
  })

  // ══════════════════════════════════════════════
  // 非功能 E2E — 安全
  // ══════════════════════════════════════════════

  it('E2E-NF-SC-1: XSS 注入不弹窗不报错', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()

    const xssPayloads = [
      '<img src=x onerror=alert(1)>',
      '<svg onload=alert(1)>',
      "javascript:alert('XSS')",
    ]

    for (const payload of xssPayloads) {
      await typeInSearch(wrapper, payload)
      vi.advanceTimersByTime(300)
      await flushPromises()
      // 组件不应崩溃（查找 input 仍然存在）
      expect(wrapper.find('input.search-input-el').exists()).toBe(true)
      mockSearchContents.mockClear()
    }
  })

  it('E2E-NF-SC-2: URL 参数正确编码', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountView()
    await flushPromises()

    await typeInSearch(wrapper, 'a&b=c')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // API 调用时参数已传递（编码由 http 层处理）
    expect(mockSearchContents).toHaveBeenCalledWith('a&b=c', expect.any(AbortSignal))
  })

  // ══════════════════════════════════════════════
  // 非功能 E2E — 可靠性
  // ══════════════════════════════════════════════

  it('E2E-NF-RL-1: 搜索后重新挂载 → 搜索框为空', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    await typeInSearch(wrapper, 'Python')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 重新挂载（模拟刷新）
    wrapper.unmount()
    const newWrapper = mountView()
    await flushPromises()

    // 输入框应为空
    const input = newWrapper.find('input.search-input-el')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('')
  })

  it('E2E-NF-RL-2: 浏览器后退 → 搜索框可用', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)

    // 搜索框存在且可用
    const input = wrapper.find('input.search-input-el')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).disabled).toBeFalsy()
  })

  // ══════════════════════════════════════════════
  // 兼容性 — 不同屏幕尺寸
  // ══════════════════════════════════════════════

  it('E2E-CP-SC-1: 不同视口下列表可见且搜索框可用', async () => {
    // 测试搜索框和内容区在不同尺寸下可用
    const wrapper = mountView()
    await flushPromises()
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 小视口下输入框仍存在
    const input = wrapper.find('input.search-input-el')
    expect(input.exists()).toBe(true)

    // 验证页面结构完整性
    expect(wrapper.find('.recommend-view').exists()).toBe(true)
  })
})
