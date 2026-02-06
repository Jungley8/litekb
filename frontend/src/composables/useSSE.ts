/**
 * SSE 流式对话 Hook - 简化版
 */
import { ref, onUnmounted } from 'vue'

interface UseSSEOptions {
  onChunk?: (chunk: string) => void
  onSources?: (sources: any[]) => void
  onComplete?: () => void
  onError?: (error: string) => void
}

export function useSSE() {
  const isConnected = ref(false)
  const eventSource = ref<EventSource | null>(null)

  function connect(
    endpoint: string,
    params: Record<string, string> = {},
    options: UseSSEOptions = {}
  ): EventSource | null {
    disconnect()
    isConnected.value = true

    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    
    const url = new URL(`${baseURL}${endpoint}`)
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value)
    })

    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const es = new EventSource(url.toString(), { headers })

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.chunk || data.content) {
          options.onChunk?.(data.chunk || data.content)
        }
        if (data.sources) {
          options.onSources?.(data.sources)
        }
      } catch (e) {
        // 静默处理解析错误
      }
    }

    es.addEventListener('chunk', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        options.onChunk?.(data.chunk || data.content || '')
      } catch {}
    })

    es.addEventListener('sources', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        options.onSources?.(data.sources || [])
      } catch {}
    })

    es.addEventListener('done', () => {
      isConnected.value = false
      options.onComplete?.()
      es.close()
    })

    es.addEventListener('error', (event) => {
      isConnected.value = false
      try {
        const data = JSON.parse((event as MessageEvent).data)
        options.onError?.(data.detail || 'Connection error')
      } catch {
        options.onError?.('Connection error')
      }
      es.close()
    })

    eventSource.value = es
    return es
  }

  function disconnect() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    connect,
    disconnect
  }
}
