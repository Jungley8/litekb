/**
 * SSE 流式对话 Hook
 */
import { ref, onUnmounted } from 'vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

interface UseStreamChatOptions {
  onMessage?: (data: any) => void
  onSources?: (sources: any[]) => void
  onDone?: () => void
  onError?: (error: string) => void
}

export function useStreamChat() {
  const isStreaming = ref(false)
  const eventSource = ref<EventSource | null>(null)

  function connect(
    kbId: string,
    message: string,
    options: UseStreamChatOptions = {}
  ): EventSource | null {
    disconnect()
    isStreaming.value = true

    const token = localStorage.getItem('token')
    const url = new URL(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/kb/${kbId}/chat/stream`)
    url.searchParams.set('message', message)
    url.searchParams.set('mode', 'naive')

    const es = new EventSource(url.toString(), {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        options.onMessage?.(data)
      } catch (e) {
        console.error('Parse SSE message error:', e)
      }
    }

    es.addEventListener('sources', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        options.onSources?.(data.sources || [])
      } catch (e) {
        console.error('Parse sources error:', e)
      }
    })

    es.addEventListener('message', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data)
        if (data.content) {
          options.onMessage?.({ type: 'content', data: data.content })
        }
      } catch (e) {
        console.error('Parse message error:', e)
      }
    })

    es.addEventListener('done', () => {
      isStreaming.value = false
      es.close()
      options.onDone?.()
    })

    es.addEventListener('error', (event) => {
      isStreaming.value = false
      try {
        const data = JSON.parse((event as MessageEvent).data)
        options.onError?.(data.detail || 'Unknown error')
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
    isStreaming.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isStreaming,
    connect,
    disconnect
  }
}
