import http from './http'

/**
 * 推荐内容接口
 */
export interface RecommendContent {
  id: number
  article_id?: string
  title: string
  url: string
  description?: string
  thumbnail?: string
  author?: string
  source_name?: string
  published_at?: string
  tags: string[]
  recommendation_score: number
  freshness: number
  preference_match: number
  quality: number
  timeliness: number
  reason?: string
  source_type: string
}

/**
 * 内容源接口
 */
export interface RecommendSource {
  id: number
  name: string
  source_type: string
  url: string
  enabled: boolean
  config?: string
  fetch_interval: number
  last_fetched_at?: string
}

/**
 * 知识库条目接口
 */
export interface KnowledgeItem {
  id: number
  title: string
  url: string
  category?: string
  tags: string[]
  access_count: number
  created_at: string
}

/**
 * 用户偏好接口
 */
export interface UserPreferences {
  topic_weights: Record<string, number>
  source_trust: Record<string, number>
  blocked_topics: string[]
  blocked_sources: string[]
  preferred_length_min: number
  preferred_length_max: number
  novelty_preference: number
  quality_threshold: number
}

/**
 * 平台预设接口
 */
export interface SourcePreset {
  id: number
  name: string
  platform: string
  command: string
  limit: number
  fetch_interval: number
  enabled: boolean
}

/**
 * 获取推荐内容列表
 */
export const getContents = (params: {
  page?: number
  page_size?: number
  status?: string
  source_type?: string
}) => {
  return http.get<{ code: number; data: { items: RecommendContent[]; total: number } }>('/wx/recommend/contents', { params })
}

/**
 * 用户交互
 */
export const interact = (contentId: number, action: 'like' | 'dislike' | 'skip' | 'view') => {
  return http.post<{ code: number; data: { preferences_updated: boolean } }>(`/wx/recommend/contents/${contentId}/interact`, { action })
}

/**
 * 获取交互历史
 */
export const getInteractions = (params?: { page?: number; page_size?: number; action?: string }) => {
  return http.get<{ code: number; data: { items: InteractionItem[]; total: number } }>('/wx/recommend/interactions', { params })
}

export interface InteractionItem {
  id: number
  action: string
  created_at: string
  content: {
    id: number
    title: string
    url: string
    description?: string
    source_name?: string
  }
}

/**
 * 获取用户偏好
 */
export const getPreferences = () => {
  return http.get<{ code: number; data: UserPreferences }>('/wx/recommend/preferences')
}

/**
 * 更新用户偏好
 */
export const updatePreferences = (data: Partial<UserPreferences>) => {
  return http.put<{ code: number }>('/wx/recommend/preferences', data)
}

/**
 * 获取知识库列表
 */
export const getKnowledge = (params?: { page?: number; page_size?: number; category?: string }) => {
  return http.get<{ code: number; data: { items: KnowledgeItem[]; total: number } }>('/wx/recommend/knowledge', { params })
}

/**
 * 保存到知识库
 */
export const saveToKnowledge = (contentId: number) => {
  return http.post<{ code: number; data: { id: number } }>('/wx/recommend/knowledge', { content_id: contentId })
}

/**
 * 从知识库删除
 */
export const deleteFromKnowledge = (knowledgeId: number) => {
  return http.delete<{ code: number }>(`/wx/recommend/knowledge/${knowledgeId}`)
}

/**
 * 获取内容源列表
 */
export const getSources = () => {
  return http.get<{ code: number; data: { items: RecommendSource[] } }>('/wx/recommend/sources')
}

/**
 * 创建内容源
 */
export const createSource = (data: {
  name: string
  source_type: string
  url: string
  enabled?: boolean
  config?: string
  fetch_interval?: number
}) => {
  return http.post<{ code: number; data: { id: number } }>('/wx/recommend/sources', data)
}

/**
 * 更新内容源
 */
export const updateSource = (sourceId: number, data: Partial<{
  name: string
  enabled: boolean
  config: string
  fetch_interval: number
}>) => {
  return http.put<{ code: number }>(`/wx/recommend/sources/${sourceId}`, data)
}

/**
 * 删除内容源
 */
export const deleteSource = (sourceId: number) => {
  return http.delete<{ code: number }>(`/wx/recommend/sources/${sourceId}`)
}

/**
 * 手动抓取内容源
 */
export const fetchSource = (sourceId: number) => {
  return http.post<{ code: number; data: { fetched: number } }>(`/wx/recommend/sources/${sourceId}/fetch`)
}

/**
 * 抓取所有启用的内容源
 */
export const fetchAllSources = () => {
  return http.post<{ code: number; data: { fetched: number } }>('/wx/recommend/sources/fetch-all')
}

/**
 * 获取平台预设列表
 */
export const getPresets = () => {
  return http.get<{ code: number; data: { items: SourcePreset[] } }>('/wx/recommend/presets')
}

/**
 * 创建预设
 */
export const createPreset = (data: {
  name: string
  source_type: string
  url: string
  enabled?: boolean
  fetch_interval?: number
}) => {
  return http.post<{ code: number; data: { id: number } }>('/wx/recommend/presets', data)
}

/**
 * 搜索结果项接口
 */
export interface SearchResult {
  id: number
  title: string
  summary?: string
  url: string
  author?: string
  source_type: string
  source_name?: string
  published_at?: string
}

/**
 * 搜索推荐内容
 */
export const searchContents = (q: string, signal?: AbortSignal) => {
  return http.get<{ code: number; data: { items: SearchResult[]; total: number } }>(
    '/wx/search',
    { params: { q }, signal }
  )
}