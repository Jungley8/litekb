/**
 * 分享 API
 */
import axios from './index'

export interface ShareLink {
  id: string
  short_url: string
  token: string
  type: 'document' | 'kb' | 'conversation'
  resource_id: string
  permission: 'view' | 'comment' | 'edit'
  expires_at?: string
  view_count: number
  created_at: string
}

export interface CreateShareRequest {
  type: 'document' | 'kb' | 'conversation'
  resource_id: string
  permission?: 'view' | 'comment' | 'edit'
  expires_in_days?: number
  max_views?: number
  password?: string
}

export const shareApi = {
  // 创建分享链接
  create: (data: CreateShareRequest) =>
    api.post<ShareLink>('/api/v1/share', data),
  
  // 获取分享链接
  get: (shareId: string, token: string, password?: string) =>
    api.get<ShareLink>(`/api/v1/share/${shareId}`, {
      params: { token, password }
    }),
  
  // 获取资源的分享链接列表
  list: (type: string, resourceId: string) =>
    api.get<ShareLink[]>('/api/v1/share', {
      params: { type, resource_id: resourceId }
    }),
  
  // 撤销分享
  revoke: (shareId: string) =>
    api.delete(`/api/v1/share/${shareId}`),
  
  // 获取分享统计
  stats: (shareId: string) =>
    api.get<{ view_count: number; unique_visitors: number }>(
      `/api/v1/share/${shareId}/stats`
    ),
  
  // 公开访问 (无需认证)
  access: (shareId: string, token: string, password?: string) =>
    api.get(`/s/${shareId}`, {
      baseURL: '',  // 使用基础 URL
      params: { token, password }
    }),
}
