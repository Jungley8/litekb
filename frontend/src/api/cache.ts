/**
 * API 缓存层
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 内存缓存
const memoryCache = new Map<string, { data: any; timestamp: number }>()

// 缓存配置
const CACHE_CONFIG = {
  // 默认 TTL: 5 分钟
  defaultTTL: 5 * 60 * 1000,
  
  // API 特定配置
  api: {
    '/api/v1/kb': { ttl: 5 * 60 * 1000 },
    '/api/v1/kb/*/docs': { ttl: 2 * 60 * 1000 },
    '/api/v1/kb/*/search': { ttl: 10 * 60 * 1000 },
    '/api/v1/kb/*/graph': { ttl: 30 * 60 * 1000 },
    '/api/v1/organizations': { ttl: 5 * 60 * 1000 },
    '/api/v1/me': { ttl: 60 * 60 * 1000 },
  }
}

// 生成缓存 Key
function generateCacheKey(config: { method: string; url: string; params?: any; data?: any }): string {
  const { method, url, params, data } = config
  
  let key = `${method.toUpperCase()}:${url}`
  
  if (params) {
    key += `?${JSON.stringify(params)}`
  }
  
  if (data && method.toUpperCase() !== 'GET') {
    key += `:${JSON.stringify(data)}`
  }
  
  return key
}

// 获取 TTL
function getTTL(url: string): number {
  // 精确匹配
  if (CACHE_CONFIG.api[url]) {
    return CACHE_CONFIG.api[url].ttl
  }
  
  // 模式匹配
  for (const [pattern, config] of Object.entries(CACHE_CONFIG.api)) {
    const regex = new RegExp(pattern.replace('*', '[^/]+'))
    if (regex.test(url)) {
      return config.ttl
    }
  }
  
  return CACHE_CONFIG.defaultTTL
}

// 是否应该缓存
function shouldCache(config: { method: string; url: string }): boolean {
  const cacheableMethods = ['GET', 'HEAD']
  const cacheableUrls = Object.keys(CACHE_CONFIG.api)
  
  return (
    cacheableMethods.includes(config.method.toUpperCase()) &&
    cacheableUrls.some(url => url.includes('*') 
      ? new RegExp(url.replace('*', '[^/]+')).test(config.url)
      : url === config.url
    )
  )
}

// Axios 请求拦截器
axios.interceptors.request.use(
  (config) => {
    if (shouldCache(config)) {
      const key = generateCacheKey(config)
      const cached = memoryCache.get(key)
      
      if (cached && Date.now() - cached.timestamp < getTTL(config.url)) {
        config.adapter = () => Promise.resolve({
          data: cached.data,
          status: 200,
          statusText: 'OK',
          headers: {},
          config
        })
      }
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// Axios 响应拦截器
axios.interceptors.response.use(
  async (response) => {
    const config = response.config
    
    if (shouldCache(config)) {
      const key = generateCacheKey(config)
      memoryCache.set(key, {
        data: response.data,
        timestamp: Date.now()
      })
    }
    
    return response
  },
  (error) => Promise.reject(error)
)

// 缓存管理
export const cache = {
  // 获取缓存
  get<T = any>(key: string): T | null {
    const item = memoryCache.get(key)
    if (item && Date.now() - item.timestamp < getTTL(key)) {
      return item.data as T
    }
    memoryCache.delete(key)
    return null
  },
  
  // 设置缓存
  set(key: string, data: any, ttl?: number): void {
    memoryCache.set(key, {
      data,
      timestamp: Date.now()
    })
  },
  
  // 删除缓存
  delete(key: string): void {
    memoryCache.delete(key)
  },
  
  // 按模式删除
  deletePattern(pattern: string): void {
    const regex = new RegExp(pattern)
    for (const key of memoryCache.keys()) {
      if (regex.test(key)) {
        memoryCache.delete(key)
      }
    }
  },
  
  // 清空所有缓存
  clear(): void {
    memoryCache.clear()
  },
  
  // 获取缓存大小
  size(): number {
    return memoryCache.size
  }
}

// 便捷方法: 缓存特定请求
export async function cachedRequest<T>(
  url: string,
  params?: any,
  ttl?: number
): Promise<T> {
  const key = `GET:${url}?${JSON.stringify(params || {})}`
  
  const cached = cache.get<T>(key)
  if (cached) {
    return cached
  }
  
  const response = await axios.get<T>(url, { params })
  cache.set(key, response.data, ttl)
  
  return response.data
}

// 使缓存失效
export function invalidateCache(pattern: string): void {
  cache.deletePattern(pattern)
}
