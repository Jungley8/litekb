/**
 * 组织管理 API
 */
import axios from './index'

export interface Organization {
  id: string
  name: string
  slug: string
  logo?: string
  plan: string
  role: string  // 用户在组织中的角色
  member_count?: number
  created_at: string
}

export interface CreateOrgRequest {
  name: string
  slug: string
  logo?: string
}

export interface UpdateOrgRequest {
  name?: string
  logo?: string
  settings?: Record<string, any>
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
  status: string
  created_at: string
  expires_at?: string
}

export interface APIKeyInfo {
  id: string
  name: string
  key_prefix: string
  scopes: string[]
  last_used_at?: string
  created_at: string
}

export const orgApi = {
  // 组织列表
  list: () => api.get<Organization[]>('/api/v1/organizations'),
  
  // 创建组织
  create: (data: CreateOrgRequest) => 
    api.post<Organization>('/api/v1/organizations', data),
  
  // 获取组织详情
  get: (orgId: string) =>
    api.get<Organization>(`/api/v1/organizations/${orgId}`),
  
  // 更新组织
  update: (orgId: string, data: UpdateOrgRequest) =>
    api.put<Organization>(`/api/v1/organizations/${orgId}`, data),
  
  // 删除组织
  delete: (orgId: string) =>
    api.delete(`/api/v1/organizations/${orgId}`),
  
  // ========== 成员管理 ==========
  
  // 成员列表
  members: (orgId: string) =>
    api.get<Member[]>(`/api/v1/organizations/${orgId}/members`),
  
  // 邀请成员
  invite: (orgId: string, email: string, role: string = 'member') =>
    api.post<Invitation>(`/api/v1/organizations/${orgId}/invite`, { email, role }),
  
  // 移除成员
  removeMember: (orgId: string, userId: string) =>
    api.delete(`/api/v1/organizations/${orgId}/members/${userId}`),
  
  // 更新成员角色
  updateMember: (orgId: string, userId: string, role: string) =>
    api.put(`/api/v1/organizations/${orgId}/members/${userId}`, { role }),
  
  // ========== 邀请管理 ==========
  
  // 待处理邀请列表
  invitations: (orgId: string) =>
    api.get<Invitation[]>(`/api/v1/organizations/${orgId}/invitations`),
  
  // 取消邀请
  cancelInvitation: (orgId: string, inviteId: string) =>
    api.delete(`/api/v1/organizations/${orgId}/invitations/${inviteId}`),
  
  // ========== API Keys ==========
  
  // API Key 列表
  apiKeys: (orgId: string) =>
    api.get<APIKeyInfo[]>(`/api/v1/organizations/${orgId}/api-keys`),
  
  // 创建 API Key
  createApiKey: (orgId: string, name: string, scopes: string[]) =>
    api.post<{ id: string; key: string; key_prefix: string }>(
      `/api/v1/organizations/${orgId}/api-keys`,
      { name, scopes }
    ),
  
  // 删除 API Key
  deleteApiKey: (orgId: string, keyId: string) =>
    api.delete(`/api/v1/organizations/${orgId}/api-keys/${keyId}`),
  
  // ========== 使用统计 ==========
  
  usage: (orgId: string) =>
    api.get<{
      kb_count: number
      kb_limit: number
      doc_count: number
      doc_limit: number
      member_count: number
      member_limit: number
      storage_gb: number
      storage_limit_gb: number
    }>(`/api/v1/organizations/${orgId}/usage`),
}
