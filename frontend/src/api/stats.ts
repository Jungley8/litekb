/**
 * 统计 API
 */
import axios from './index'

export interface StatsSummary {
  kb_count: number
  doc_count: number
  chat_count: number
  storage_mb: number
  active_users: number
  api_calls: number
}

export interface TrendData {
  date: string
  count: number
}

export interface ResourceType {
  type: string
  count: number
}

export interface OperationStat {
  type: string
  count: number
}

export const statsApi = {
  // 获取统计摘要
  getSummary: (): Promise<StatsSummary> =>
    api.get('/api/v1/stats/summary'),
  
  // 获取使用趋势
  getTrends: (days: number = 7): Promise<TrendData[]> =>
    api.get('/api/v1/stats/trends', { params: { days } }),
  
  // 获取热门文档
  getHotDocs: (limit: number = 10): Promise<{ id: string; title: string; views: number }[]> =>
    api.get('/api/v1/stats/hot-docs', { params: { limit } }),
  
  // 获取资源类型分布
  getResourcesByType: (): Promise<ResourceType[]> =>
    api.get('/api/v1/stats/resources'),
  
  // 获取操作统计
  getOperations: (): Promise<OperationStat[]> =>
    api.get('/api/v1/stats/operations'),
  
  // 获取活动热力图
  getHeatmap: (days: number = 28): Promise<Record<string, { docs: number; chats: number }>> =>
    api.get('/api/v1/stats/heatmap', { params: { days } }),
  
  // 获取响应时间统计
  getResponseTimes: (): Promise<{ avg: number; p50: number; p95: number }> =>
    api.get('/api/v1/stats/response-times'),
  
  // 获取满意度
  getSatisfaction: (): Promise<{ rate: number; total: number }> =>
    api.get('/api/v1/stats/satisfaction'),
}
