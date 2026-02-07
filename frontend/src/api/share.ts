/**
 * 分享 API 对接
 */
import api from './index'

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

export interface ShareStats {
  share_id: string
  view_count: number
  unique_visitors: number
  created_at: string
}

export const shareApi = {
  // 创建分享链接
  create: (data: CreateShareRequest): Promise<ShareLink> =>
    api.post('/api/v1/share', data),
  
  // 获取分享链接详情
  get: (shareId: string, token: string, password?: string): Promise<ShareLink> =>
    api.get(`/api/v1/share/${shareId}`, {
      params: { token, password }
    }),
  
  // 获取资源的分享列表
  list: (type: string, resourceId: string): Promise<ShareLink[]> =>
    api.get('/api/v1/share', {
      params: { type, resource_id: resourceId }
    }),
  
  // 撤销分享
  revoke: (shareId: string): Promise<void> =>
    api.delete(`/api/v1/share/${shareId}`),
  
  // 获取分享统计
  stats: (shareId: string): Promise<ShareStats> =>
    api.get(`/api/v1/share/${shareId}/stats`),
  
  // 公开访问 (不需要认证)
  access: (shareId: string, token: string, password?: string): Promise<any> =>
    api.get(`/s/${shareId}`, {
      baseURL: '',  // 使用基础 URL
      params: { token, password }
    }),
  
  // 获取嵌入代码
  getEmbedCode: (shareId: string, token: string): Promise<string> =>
    api.get(`/api/v1/share/${shareId}/embed`, {
      params: { token }
    }),
}
