import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { h, nextTick } from 'vue'
import RecommendView from './RecommendView.vue'

// Mock API
const mockGetContents = vi.fn()

vi.mock('@/api/recommend', () => ({
  getContents: (...args: any[]) => mockGetContents(...args),
}))

vi.mock('@arco-design/web-vue', () => ({
  Message: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// Arco Design component stubs
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
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'a-space' }, slots.default?.())
    },
  },
  'a-page-header': {
    props: ['title', 'subtitle'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'page-header' }, [slots.extra?.(), slots.default?.()])
    },
  },
  'a-spin': {
    props: ['tip', 'size'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'spin' }, slots.default?.())
    },
  },
  'a-empty': {
    props: ['description'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'empty' }, slots.default?.())
    },
  },
  'a-select': {
    props: ['modelValue', 'disabled', 'placeholder', 'allowClear'],
    emits: ['update:modelValue', 'change'],
    setup(props: any, { emit, slots }: any) {
      return (ctx: any) => h('select', {
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
    setup(props: any, { slots }: any) {
      return () => h('div', { class: ['card', props.class] }, slots.default?.())
    },
  },
  'a-pagination': {
    props: ['current', 'pageSize', 'total'],
    emits: ['change', 'pageChange'],
    setup(props: any, { emit }: any) {
      return () => h('div', { class: 'pagination', onClick: () => emit('change', props.current + 1) })
    },
  },
  'icon-refresh': {
    setup(_: any, { slots }: any) {
      return () => h('span', {}, '↻')
    },
  },
}

const mockContentItems = [
  {
    id: 1,
    title: '测试文章标题1',
    url: 'https://example.com/article1',
    description: '这是文章描述1',
    thumbnail: 'https://example.com/thumb1.jpg',
    author: '极客杰尼',
    published_at: '2026-04-12T10:00:00',
    tags: ['技术', '编程'],
    recommendation_score: 85,
    freshness: 0.9,
    preference_match: 0.8,
    quality: 0.75,
    timeliness: 0.9,
    source_type: 'wechat',
    source_name: '极客杰尼',
  },
  {
    id: 2,
    title: '测试文章标题2',
    url: 'https://example.com/article2',
    description: '这是文章描述2',
    thumbnail: 'https://example.com/thumb2.jpg',
    author: '科技前沿',
    published_at: '2026-04-12T08:00:00',
    tags: ['科技'],
    recommendation_score: 72,
    freshness: 0.85,
    preference_match: 0.7,
    quality: 0.8,
    timeliness: 0.85,
    source_type: 'rss',
    source_name: 'RSS源',
  },
]

const mountWithArco = () => {
  return mount(RecommendView, {
    global: {
      components: ArcoComponents,
    },
  })
}

describe('RecommendView 推荐内容 UI集成测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('初始化和加载', () => {
    it('should load contents on mount', async () => {
      mockGetContents.mockResolvedValue({ items: mockContentItems, total: 2 })

      const wrapper = mountWithArco()
      await flushPromises()

      expect(mockGetContents).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        status: undefined,
      })
    })

    it('should display loading state initially', async () => {
      mockGetContents.mockImplementation(() => new Promise(() => {})) // Never resolves

      const wrapper = mountWithArco()
      await nextTick()

      expect(wrapper.find('.spin').exists()).toBe(true)
    })

    it('should display contents when loaded', async () => {
      mockGetContents.mockResolvedValue({ items: mockContentItems, total: 2 })

      const wrapper = mountWithArco()
      await flushPromises()

      const cards = wrapper.findAll('.recommendation-card')
      expect(cards.length).toBe(2)
    })

    it('should display empty state when no contents', async () => {
      mockGetContents.mockResolvedValue({ items: [], total: 0 })

      const wrapper = mountWithArco()
      await flushPromises()

      expect(wrapper.find('.empty').exists()).toBe(true)
    })
  })

  describe('筛选功能', () => {
    it('should call getContents with filter status when filter changes', async () => {
      mockGetContents.mockResolvedValue({ items: mockContentItems, total: 2 })

      const wrapper = mountWithArco()
      await flushPromises()

      mockGetContents.mockClear()

      const select = wrapper.find('select')
      await select.setValue('recommended')
      await flushPromises()

      expect(mockGetContents).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        status: 'recommended',
      })
    })
  })

  describe('交互功能', () => {
    it('should reload contents when clicking refresh button', async () => {
      mockGetContents.mockResolvedValue({ items: mockContentItems, total: 2 })

      const wrapper = mountWithArco()
      await flushPromises()

      mockGetContents.mockClear()
      mockGetContents.mockResolvedValue({ items: [mockContentItems[0]], total: 1 })

      await wrapper.find('button').trigger('click')
      await flushPromises()

      expect(mockGetContents).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('should show error message when load fails', async () => {
      const { Message } = await import('@arco-design/web-vue')
      mockGetContents.mockRejectedValue(new Error('Network error'))

      const wrapper = mountWithArco()
      await flushPromises()

      expect(Message.error).toHaveBeenCalledWith('获取推荐内容失败')
    })
  })
})
