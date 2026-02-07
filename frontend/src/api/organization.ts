/**
 * 组织管理 API 对接
 */
import api from './index'

export interface Organization {
  id: string
  name: string
  slug: string
  logo?: string
  plan: string
  role: string  // owner, admin, member
  member_count?: number
  created_at: string
}

export interface CreateOrgRequest {
  name: string
  slug: string
  logo?: string
}

export interface Member {
  id: string
  user_id: string
  username: string
  email: string
  avatar?: string
  role: string
  joined_at: string
}

export interface Invitation {
  id: string
  email: string
  role: string
  status: 'pending' | 'accepted' | 'expired'
  created_at: string
}

export const orgApi = {
  // 获取组织列表
  list: (): Promise<Organization[]> =>
    api.get('/api/v1/organizations'),
  
  // 创建组织
  create: (data: CreateOrgRequest): Promise<Organization> =>
    api.post('/api/v1/organizations', data),
  
  // 获取组织详情
  get: (orgId: string): Promise<Organization> =>
    api.get(`/api/v1/organizations/${orgId}`),
  
  // 更新组织
  update: (orgId: string, data: Partial<CreateOrgRequest>): Promise<Organization> =>
    api.put(`/api/v1/organizations/${orgId}`, data),
  
  // 删除组织
  delete: (orgId: string): Promise<void> =>
    api.delete(`/api/v1/organizations/${orgId}`),
  
  // ========== 成员管理 ==========
  
  // 获取成员列表
  members: (orgId: string): Promise<Member[]> =>
    api.get(`/api/v1/organizations/${orgId}/members`),
  
  // 邀请成员
  invite: (orgId: string, email: string, role: string = 'member'): Promise<Invitation> =>
    api.post(`/api/v1/organizations/${orgId}/invite`, { email, role }),
  
  // 移除成员
  removeMember: (orgId: string, userId: string): Promise<void> =>
    api.delete(`/api/v1/organizations/${orgId}/members/${userId}`),
  
  // 更新成员角色
  updateMember: (orgId: string, userId: string, role: string): Promise<Member> =>
    api.put(`/api/v1/organizations/${orgId}/members/${userId}`, { role }),
  
  // ========== 邀请管理 ==========
  
  // 获取待处理邀请
  invitations: (orgId: string): Promise<Invitation[]> =>
    api.get(`/api/v1/organizations/${orgId}/invitations`),
  
  // 取消邀请
  cancelInvitation: (orgId: string, inviteId: string): Promise<void> =>
    api.delete(`/api/v1/organizations/${orgId}/invitations/${inviteId}`),
  
  // ========== 使用统计 ==========
  
  usage: (orgId: string): Promise<{
    kb_count: number
    kb_limit: number
    doc_count: number
    doc_limit: number
    member_count: number
    member_limit: number
    storage_gb: number
    storage_limit_gb: number
  }> => api.get(`/api/v1/organizations/${orgId}/usage`),
  
  // ========== 切换组织 ==========
  
  switch: (orgId: string): Promise<{ token: string }> =>
    api.post(`/api/v1/organizations/${orgId}/switch`),
}

// API Keys 管理
export const apiKeyApi = {
  list: (orgId: string) =>
    api.get(`/api/v1/organizations/${orgId}/api-keys`),
  
  create: (orgId: string, name: string, scopes: string[]) =>
    api.post(`/api/v1/organizations/${orgId}/api-keys`, { name, scopes }),
  
  delete: (orgId: string, keyId: string) =>
    api.delete(`/api/v1/organizations/${orgId}/api-keys/${keyId}`),
}
