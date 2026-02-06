import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

// ==================== Auth ====================

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/api/v1/auth/login', { username, password }),
  
  register: (username: string, password: string, email?: string) =>
    api.post('/api/v1/auth/register', { username, password, email }),
  
  getMe: () => api.get('/api/v1/me')
}

// ==================== Knowledge Base ====================

export const kbApi = {
  list: () => api.get('/api/v1/kb'),
  
  get: (kbId: string) => api.get(`/api/v1/kb/${kbId}`),
  
  create: (data: { name: string; description?: string }) =>
    api.post('/api/v1/kb', data),
  
  update: (kbId: string, data: { name?: string; description?: string }) =>
    api.put(`/api/v1/kb/${kbId}`, data),
  
  delete: (kbId: string) => api.delete(`/api/v1/kb/${kbId}`)
}

// ==================== Documents ====================

export const docApi = {
  list: (kbId: string) => api.get(`/api/v1/kb/${kbId}/docs`),
  
  upload: (kbId: string, file: File, onProgress?: (p: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/v1/kb/${kbId}/docs/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      }
    })
  },
  
  create: (kbId: string, data: { title: string; content?: string; metadata?: Record<string, any> }) =>
    api.post(`/api/v1/kb/${kbId}/docs`, data),
  
  delete: (kbId: string, docId: string) => 
    api.delete(`/api/v1/kb/${kbId}/docs/${docId}`),
  
  get: (kbId: string, docId: string) =>
    api.get(`/api/v1/kb/${kbId}/docs/${docId}`)
}

// ==================== Search ====================

export const searchApi = {
  search: (kbId: string, query: string, options?: { 
    strategy?: string
    top_k?: number
    filters?: Record<string, any>
  }) => 
    api.post(`/api/v1/kb/${kbId}/search`, {
      query,
      ...options
    }),
  
  // 跨知识库搜索
  searchAll: (query: string, kbIds?: string[]) =>
    api.post('/api/v1/search', { query, kb_ids: kbIds })
}

// ==================== Chat / RAG ====================

export const chatApi = {
  chat: (kbId: string, message: string, history?: Array<{ role: string; content: string }>) =>
    api.post(`/api/v1/kb/${kbId}/chat`, {
      message,
      history
    }),
  
  // 流式对话
  streamChat: (kbId: string, message: string) => {
    // TODO: 实现 SSE 流式响应
    return api.post(`/api/v1/kb/${kbId}/chat/stream`, { message })
  }
}

// ==================== Knowledge Graph ====================

export const graphApi = {
  getGraph: (kbId: string) => api.get(`/api/v1/kb/${kbId}/graph`),
  
  buildGraph: (kbId: string, options?: { rebuild?: boolean }) =>
    api.post(`/api/v1/kb/${kbId}/graph/build`, options),
  
  searchEntities: (kbId: string, query: string) =>
    api.get(`/api/v1/kb/${kbId}/graph/search`, { params: { query } }),
  
  getEntity: (kbId: string, entityId: string) =>
    api.get(`/api/v1/kb/${kbId}/graph/entity/${entityId}`)
}

// ==================== Config ====================

export const configApi = {
  getLLMConfig: () => api.get('/api/v1/config/llm'),
  
  updateLLMConfig: (data: { provider: string; api_key?: string; model?: string }) =>
    api.put('/api/v1/config/llm', data),
  
  getEmbeddingConfig: () => api.get('/api/v1/config/embedding'),
  
  updateEmbeddingConfig: (data: { provider: string; model?: string; dimensions?: number }) =>
    api.put('/api/v1/config/embedding', data)
}

export default api
