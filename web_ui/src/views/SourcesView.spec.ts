import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { h, nextTick } from 'vue'
import SourcesView from './SourcesView.vue'

// Mock API modules
const mockGetSources = vi.fn().mockResolvedValue({ items: [] })
const mockCreateSource = vi.fn().mockResolvedValue({})
const mockSearchBiz = vi.fn()

vi.mock('@/api/recommend', () => ({
  getSources: (...args: any[]) => mockGetSources(...args),
  createSource: (...args: any[]) => mockCreateSource(...args),
  deleteSource: vi.fn().mockResolvedValue({}),
  fetchSource: vi.fn().mockResolvedValue({}),
  updateSource: vi.fn().mockResolvedValue({}),
}))

vi.mock('@/api/subscription', () => ({
  searchBiz: (...args: any[]) => mockSearchBiz(...args),
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
  'a-tag': {
    props: ['color', 'size'],
    setup(props: any, { slots }: any) {
      return () => h('span', { class: 'a-tag' }, slots.default?.())
    },
  },
  'a-popconfirm': {
    props: ['content'],
    emits: ['ok', 'cancel'],
    setup(props: any, { slots, emit }: any) {
      return () => h('div', { class: 'popconfirm', onClick: () => emit('ok') }, slots.default?.())
    },
  },
  'a-table': {
    props: ['loading', 'data', 'pagination'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'table' }, slots.default?.())
    },
  },
  'a-table-column': {
    props: ['title', 'dataIndex'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'table-column' }, slots.default?.())
    },
  },
  'a-tooltip': {
    props: ['content'],
    setup(props: any, { slots }: any) {
      return () => h('span', { class: 'tooltip' }, slots.default?.())
    },
  },
  'a-card': {
    props: ['class'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: ['card', props.class] }, slots.default?.())
    },
  },
  'a-input': {
    props: ['modelValue', 'placeholder', 'type', 'disabled'],
    emits: ['update:modelValue', 'input'],
    setup(props: any, { emit }: any) {
      return (ctx: any) => h('input', {
        value: props.modelValue,
        placeholder: props.placeholder,
        type: props.type || 'text',
        disabled: props.disabled,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value),
      })
    },
  },
  'a-input-search': {
    props: ['modelValue', 'placeholder', 'searchButton'],
    emits: ['update:modelValue', 'search'],
    setup(props: any, { emit }: any) {
      return (ctx: any) => h('div', { class: 'input-search' }, [
        h('input', {
          value: props.modelValue,
          placeholder: props.placeholder,
          onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).value),
          onKeydown: (e: KeyboardEvent) => e.key === 'Enter' && emit('search', props.modelValue),
        }),
        h('button', {
          class: 'search-btn',
          onClick: () => emit('search', props.modelValue)
        }, '搜索'),
      ])
    },
  },
  'a-input-number': {
    props: ['modelValue', 'min', 'max'],
    emits: ['update:modelValue'],
    setup(props: any, { emit }: any) {
      return (ctx: any) => h('input', {
        type: 'number',
        value: props.modelValue,
        min: props.min,
        max: props.max,
        onInput: (e: Event) => emit('update:modelValue', Number((e.target as HTMLInputElement).value)),
      })
    },
  },
  'a-form': {
    props: ['model', 'layout'],
    setup(props: any, { slots }: any) {
      return () => h('form', { class: 'a-form' }, slots.default?.())
    },
  },
  'a-form-item': {
    props: ['label', 'required'],
    setup(props: any, { slots }: any) {
      return () => h('div', { class: 'form-item' }, [
        props.label ? h('label', {}, props.label) : null,
        slots.default?.(),
      ])
    },
  },
  'a-select': {
    props: ['modelValue', 'disabled'],
    emits: ['update:modelValue', 'change'],
    setup(props: any, { emit, slots }: any) {
      return (ctx: any) => h('select', {
        value: props.modelValue,
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
  'a-modal': {
    props: ['visible', 'title', 'width'],
    emits: ['ok', 'cancel'],
    setup(props: any, { slots, emit }: any) {
      return () => props.visible
        ? h('div', { class: 'modal' }, [
            h('div', { class: 'modal-content' }, slots.default?.()),
            h('button', { class: 'modal-ok', onClick: () => emit('ok') }, '确定'),
            h('button', { class: 'modal-cancel', onClick: () => emit('cancel') }, '取消'),
          ])
        : null
    },
  },
  'a-switch': {
    props: ['modelValue', 'checked'],
    emits: ['update:modelValue', 'change'],
    setup(props: any, { emit }: any) {
      return (ctx: any) => h('input', {
        type: 'checkbox',
        checked: props.modelValue || props.checked,
        onChange: (e: Event) => emit('update:modelValue', (e.target as HTMLInputElement).checked),
      })
    },
  },
  'icon-plus': {
    setup(_: any, { slots }: any) {
      return () => h('span', {}, '+')
    },
  },
  'icon-refresh': {
    setup(_: any, { slots }: any) {
      return () => h('span', {}, '↻')
    },
  },
}

const mountWithArco = () => {
  return mount(SourcesView, {
    global: {
      components: ArcoComponents,
      provide: {
        Message: { success: vi.fn(), error: vi.fn() },
      },
    },
  })
}

const mockSearchResults = [
  {
    fakeid: 'MjM5MjAxNDE3NA==',
    nickname: '极客杰尼',
    signature: '做一个有趣的人',
    round_head_img: 'https://example.com/avatar1.jpg',
  },
  {
    fakeid: 'MjM5MjAxNDE3NQ==',
    nickname: '极客杰尼2',
    signature: '另一个极客杰尼',
    round_head_img: 'https://example.com/avatar2.jpg',
  },
]

describe('SourcesView 添加公众号 UI集成测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSearchBiz.mockResolvedValue({ list: mockSearchResults })
  })

  describe('添加公众号完整流程', () => {
    it('should open add dialog when clicking 添加 button', async () => {
      const wrapper = mountWithArco()
      await flushPromises()

      const addButton = wrapper.find('button')
      expect(addButton.exists()).toBe(true)
      await addButton.trigger('click')
      await flushPromises()

      expect(wrapper.find('.modal').exists()).toBe(true)
    })

    it('should show wechat search input when source_type is wechat', async () => {
      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal
      await wrapper.find('button').trigger('click')
      await flushPromises()

      // Change select to wechat
      const select = wrapper.find('select')
      await select.setValue('wechat')
      await flushPromises()

      // Should show search input
      const searchInput = wrapper.find('.input-search input')
      expect(searchInput.exists()).toBe(true)
    })

    it('should display search results when searching for wechat account', async () => {
      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Type search keyword and click search button
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('极客杰尼')
      await nextTick()

      // Click search button
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      // Should show results
      const resultItems = wrapper.findAll('.wechat-result-item')
      expect(resultItems.length).toBe(2)
      expect(resultItems[0].find('.wechat-name').text()).toBe('极客杰尼')
    })

    it('should fill form when selecting a wechat account from search results', async () => {
      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Search
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('极客杰尼')
      await nextTick()
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      // Click on result
      await wrapper.find('.wechat-result-item').trigger('click')
      await flushPromises()
      await nextTick()

      // Form should be filled
      const form = (wrapper.vm as any).form
      expect(form.name).toBe('极客杰尼')
      expect(form.url).toBe('MjM5MjAxNDE3NA==')
      expect(form.source_type).toBe('wechat')

      // Search results should be cleared
      expect(wrapper.findAll('.wechat-result-item').length).toBe(0)
    })

    it('should submit form with correct wechat data when clicking ok', async () => {
      const { Message } = await import('@arco-design/web-vue')

      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Search and select
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('极客杰尼')
      await nextTick()
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      await wrapper.find('.wechat-result-item').trigger('click')
      await flushPromises()
      await nextTick()

      // Click OK
      await wrapper.find('.modal-ok').trigger('click')
      await flushPromises()

      // Verify createSource was called with correct data
      expect(mockCreateSource).toHaveBeenCalledWith({
        name: '极客杰尼',
        source_type: 'wechat',
        url: 'MjM5MjAxNDE3NA==',
        enabled: true,
        fetch_interval: 24,
      })

      expect(Message.success).toHaveBeenCalledWith('添加成功')
    })

    it('should clear search results when source_type changes away from wechat', async () => {
      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Search
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('极客杰尼')
      await nextTick()
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      expect(wrapper.findAll('.wechat-result-item').length).toBe(2)

      // Change to RSS
      await wrapper.find('select').setValue('rss')
      await flushPromises()
      await nextTick()

      // Search results should be gone
      expect(wrapper.findAll('.wechat-result-item').length).toBe(0)
    })
  })

  describe('公众号搜索边界情况', () => {
    it('should show empty results when no account matches', async () => {
      mockSearchBiz.mockResolvedValue({ list: [] })

      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Search
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('不存在的公众号')
      await nextTick()
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      expect(wrapper.findAll('.wechat-result-item').length).toBe(0)
    })

    it('should handle search API error gracefully', async () => {
      mockSearchBiz.mockRejectedValue(new Error('Network error'))

      const wrapper = mountWithArco()
      await flushPromises()

      // Open modal and select wechat
      await wrapper.find('button').trigger('click')
      await flushPromises()

      await wrapper.find('select').setValue('wechat')
      await flushPromises()

      // Search
      const searchInput = wrapper.find('.input-search input')
      await searchInput.setValue('test')
      await nextTick()
      await wrapper.find('.search-btn').trigger('click')
      await flushPromises()
      await nextTick()

      // Should show no results
      expect(wrapper.findAll('.wechat-result-item').length).toBe(0)
    })
  })
})
