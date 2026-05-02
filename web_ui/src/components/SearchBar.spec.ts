import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { h, nextTick } from 'vue'
import SearchBar from './SearchBar.vue'

// Mock search API
const mockSearchContents = vi.fn()

vi.mock('@/api/recommend', () => ({
  searchContents: (...args: any[]) => mockSearchContents(...args),
}))

vi.mock('@arco-design/web-vue', () => ({
  Message: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Arco Design component stubs
const ArcoComponents = {
  'a-input': {
    props: ['modelValue', 'placeholder', 'allowClear', 'class'],
    emits: ['update:modelValue', 'input', 'keydown', 'compositionstart', 'compositionend', 'clear'],
    setup(props: any, { emit, slots }: any) {
      return () => h('div', { class: 'a-input-wrapper' }, [
        slots.prefix?.(),
        h('input', {
          value: props.modelValue || '',
          class: 'a-input',
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
  'icon-search': {
    setup() { return () => h('span', {}, '🔍') },
  },
}

function mountSearchBar() {
  return mount(SearchBar, {
    global: {
      components: ArcoComponents,
    },
  })
}

// Helper to type in search input
async function typeSearch(wrapper: ReturnType<typeof mountSearchBar>, value: string) {
  const input = wrapper.find('input.a-input')
  await input.setValue(value)
}

// Helper to trigger clear
async function clickClear(wrapper: ReturnType<typeof mountSearchBar>) {
  const clearBtn = wrapper.find('.clear-btn')
  if (clearBtn.exists()) {
    await clearBtn.trigger('click')
  }
}

describe('SearchBar 搜索组件单元测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // UT-FE-1: 空输入不搜索
  it('UT-FE-1: 空输入不调用搜索 API', async () => {
    const wrapper = mountSearchBar()

    // 输入空白
    await typeSearch(wrapper, '')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).not.toHaveBeenCalled()
  })

  // UT-FE-2: debounce 后调用 API
  it('UT-FE-2: debounce 300ms 后触发搜索 API', async () => {
    mockSearchContents.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'Python')
    // 还未到 300ms
    expect(mockSearchContents).not.toHaveBeenCalled()

    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledTimes(1)
    expect(mockSearchContents).toHaveBeenCalledWith('Python', expect.any(AbortSignal))
  })

  // UT-FE-3: 搜索结果更新
  it('UT-FE-3: 搜索结果通过 search 事件返回', async () => {
    const searchResults = [{ id: 1, title: 'Test', url: '', source_type: 'rss' }]
    mockSearchContents.mockResolvedValue(searchResults)
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'test')
    vi.advanceTimersByTime(300)
    await flushPromises()
    await nextTick()

    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')![0][0]).toEqual(searchResults)
  })

  // UT-FE-4: 连续输入 debounce（仅最后一次触发）
  it('UT-FE-4: 连续快速输入，仅最后一次触发搜索', async () => {
    mockSearchContents.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'a')
    vi.advanceTimersByTime(100)  // 未到 debounce
    await typeSearch(wrapper, 'ab')
    vi.advanceTimersByTime(100)  // 未到 debounce，重置
    await typeSearch(wrapper, 'abc')
    vi.advanceTimersByTime(300)  // 到达 debounce
    await flushPromises()

    // 只调用了一次，关键词是最后一次输入的
    expect(mockSearchContents).toHaveBeenCalledTimes(1)
    expect(mockSearchContents).toHaveBeenCalledWith('abc', expect.any(AbortSignal))
  })

  // UT-FE-5: 请求取消 (AbortController 竞态)
  it('UT-FE-5: 新搜索取消前一个未完成的请求', async () => {
    const wrapper = mountSearchBar()

    // 第一次搜索 - 不 resolve（pending 状态）
    let resolveFirst: any
    const firstPromise = new Promise((resolve) => { resolveFirst = resolve })
    mockSearchContents.mockReturnValueOnce(firstPromise)

    await typeSearch(wrapper, 'a')
    vi.advanceTimersByTime(300)
    await flushPromises()

    const firstSignal = mockSearchContents.mock.calls[0][1]

    // 第二次搜索 - resolve
    mockSearchContents.mockResolvedValueOnce({ items: [], total: 0 })
    await typeSearch(wrapper, 'ab')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 第一个请求应被 abort
    expect(firstSignal.aborted).toBe(true)

    // 第二个请求正常
    expect(mockSearchContents).toHaveBeenCalledTimes(2)
    expect(mockSearchContents.mock.calls[1][0]).toBe('ab')
  })

  // UT-FE-6: 空结果
  it('UT-FE-6: API 返回空数组时触发 search 事件带空数组', async () => {
    mockSearchContents.mockResolvedValue([])
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'noresults')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')![0][0]).toEqual([])
  })

  // UT-FE-7: API 500 错误
  it('UT-FE-7: API 500 错误触发 error 事件', async () => {
    mockSearchContents.mockRejectedValue(new Error('Request failed with status code 500'))
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'error')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('error')).toBeTruthy()
    expect(wrapper.emitted('error')![0][0]).toBeTruthy()
  })

  // UT-FE-8: API 超时
  it('UT-FE-8: API 超时触发 error 事件', async () => {
    mockSearchContents.mockRejectedValue(new Error('timeout of 5000ms exceeded'))
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'timeout')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('error')).toBeTruthy()
  })

  // UT-FE-9: 网络错误
  it('UT-FE-9: 网络错误触发 error 事件', async () => {
    mockSearchContents.mockRejectedValue(new Error('Network Error'))
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'network')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('error')).toBeTruthy()
  })

  // UT-FE-10: IME 组合输入
  it('UT-FE-10: IME compositionstart 时不搜索，compositionend 后搜索', async () => {
    mockSearchContents.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountSearchBar()

    const input = wrapper.find('input.a-input')

    // 模拟 IME compositionstart
    await input.trigger('compositionstart')

    // 在 IME 组合中修改值
    await input.setValue('中文')

    // 还没触发 compositionend，不应搜索
    vi.advanceTimersByTime(300)
    expect(mockSearchContents).not.toHaveBeenCalled()

    // 触发 compositionend
    await input.trigger('compositionend')

    // compositionend 后触发搜索（需要 debounce）
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledTimes(1)
  })

  // UT-FE-11: 特殊字符编码
  it('UT-FE-11: 特殊字符参数由 API 层 encodeURIComponent 处理', async () => {
    mockSearchContents.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountSearchBar()

    await typeSearch(wrapper, 'a&b=c')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(mockSearchContents).toHaveBeenCalledWith('a&b=c', expect.any(AbortSignal))
  })

  // UT-FE-12: 清空恢复列表
  it('UT-FE-12: 清空输入框触发 clear 事件', async () => {
    mockSearchContents.mockResolvedValue({ items: [{ id: 1, title: 'x', url: '', source_type: 'rss' }] })
    const wrapper = mountSearchBar()

    // 先搜索
    await typeSearch(wrapper, 'test')
    vi.advanceTimersByTime(300)
    await flushPromises()

    // 清空输入
    await typeSearch(wrapper, '')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('clear')).toBeTruthy()
  })

  // 额外: Escape 键清空
  it('Escape 键清空搜索并触发 clear 事件', async () => {
    const wrapper = mountSearchBar()
    const input = wrapper.find('input.a-input')

    await input.setValue('test')
    await input.trigger('keydown', { key: 'Escape' })

    expect(wrapper.emitted('clear')).toBeTruthy()
  })

  // 额外: 清空搜索框后再次触发 clear
  it('连续清空输入框触发 clear 事件', async () => {
    mockSearchContents.mockResolvedValue({ items: [], total: 0 })
    const wrapper = mountSearchBar()

    // 先搜索一次
    await typeSearch(wrapper, 'test')
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(wrapper.emitted('search')).toBeTruthy()

    // 清空 → 触发 clear
    await typeSearch(wrapper, '')
    vi.advanceTimersByTime(300)
    await flushPromises()

    expect(wrapper.emitted('clear')).toBeTruthy()
  })
})
