/**
 * SSE 流式对话 Hook
 */
import { ref, onUnmounted } from 'vue'
import { chatApi } from './index'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

export function useStreamChat() {
  const isStreaming = ref(false)
  const messages = ref<Message[]>([])
  const eventSource = ref<EventSource | null>(null)

  function connect(
    kbId: string,
    message: string,
    onMessage: (data: any) => void,
    onDone: () => void,
    onError: (error: string) => void
  ) {
    isStreaming.value = true

    // 构建 SSE URL
    const token = localStorage.getItem('token')
    const url = new URL(`${import.meta.env.VITE_API_URL}/api/v1/kb/${kbId}/chat/stream`)
    url.searchParams.set('message', message)
    url.searchParams.set('mode', 'naive')

    const eventSource = new EventSource(url.toString())
    eventSource.headers = { Authorization: `Bearer ${token}` }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (e) {
        console.error('Parse SSE data error:', e)
      }
    }

    eventSource.addEventListener('sources', (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage({ type: 'sources', ...data })
      } catch (e) {
        console.error('Parse sources error:', e)
      }
    })

    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage({ type: 'content', ...data })
      } catch (e) {
        console.error('Parse message error:', e)
      }
    })

    eventSource.addEventListener('done', () => {
      isStreaming.value = false
      eventSource.close()
      onDone()
    })

    eventSource.addEventListener('error', (event) => {
      isStreaming.value = false
      eventSource.close()
      const data = JSON.parse((event as MessageEvent).data)
      onError(data.detail || 'Unknown error')
    })

    return eventSource
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
    messages,
    connect,
    disconnect
  }
}
