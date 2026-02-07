/**
 * 模型供应商 API
 */
import api from './index'

export interface ProviderInfo {
  type: string  // 'openai' | 'anthropic' | 'google' | 'ollama' | 'vllm'
  name: string
  models: Array<{
    id: string
    object: string
    created: number
    owned_by: string
  }>
  capabilities: string[]
}

export interface ModelConfig {
  provider: string
  model: string
  temperature?: number
  max_tokens?: number
}

export const providerApi = {
  // 获取可用供应商列表
  listProviders: (): Promise<ProviderInfo[]> =>
    api.get('/api/v1/models/providers'),
  
  // 获取当前配置
  getConfig: (): Promise<ModelConfig> =>
    api.get('/api/v1/models/config'),
  
  // 切换供应商
  switchProvider: (data: ModelConfig): Promise<{ success: boolean }> =>
    api.post('/api/v1/models/switch', data),
  
  // 获取供应商模型列表
  getModels: (provider: string): Promise<Array<{ id: string; name: string }>> =>
    api.get(`/api/v1/models/${provider}/list`),
  
  // 测试连接
  testConnection: (provider: string): Promise<{ success: boolean; latency: number }> =>
    api.post(`/api/v1/models/${provider}/test`),
}

// Ollama 专用 API
export const ollamaApi = {
  listModels: (): Promise<Array<{ name: string; size: number }>> =>
    api.get('/api/v1/models/ollama/list'),
  
  pullModel: (model: string, stream?: boolean): Promise<any> =>
    api.post('/api/v1/models/ollama/pull', { model, stream }),
}

// vLLM 专用 API
export const vllmApi = {
  listModels: (): Promise<Array<{ id: string }>> =>
    api.get('/api/v1/models/vllm/list'),
}
