/**
 * 性能优化 Hooks
 */
import { ref, onMounted, onUnmounted } from 'vue'

// ==================== 虚拟滚动 ====================

export function useVirtualScroll(
  containerRef: { value: HTMLElement | null },
  itemHeight: number,
  overscan: number = 5
) {
  const scrollTop = ref(0)
  const containerHeight = ref(0)
  const itemCount = ref(0)
  const startIndex = ref(0)
  const endIndex = ref(0)

  function calculateRange() {
    if (!containerRef.value) return

    containerHeight.value = containerRef.value.clientHeight
    scrollTop.value = containerRef.value.scrollTop

    const start = Math.floor(scrollTop.value / itemHeight)
    const visibleCount = Math.ceil(containerHeight.value / itemHeight)

    startIndex.value = Math.max(0, start - overscan)
    endIndex.value = Math.min(
      itemCount.value - 1,
      start + visibleCount + overscan
    )
  }

  function handleScroll(e: Event) {
    calculateRange()
  }

  onMounted(() => {
    containerRef.value?.addEventListener('scroll', handleScroll)
    calculateRange()
  })

  onUnmounted(() => {
    containerRef.value?.removeEventListener('scroll', handleScroll)
  })

  return {
    startIndex,
    endIndex,
    containerHeight,
    offsetY: computed(() => startIndex.value * itemHeight)
  }
}

// ==================== 图片懒加载 ====================

export function useLazyLoad(
  src: string,
  placeholder: string = ''
) {
  const imageSrc = ref(placeholder)
  const isLoaded = ref(false)
  const error = ref(false)

  const observer = ref<IntersectionObserver | null>(null)

  function observe(element: HTMLElement) {
    if (observer.value) {
      observer.value.observe(element)
    }
  }

  onMounted(() => {
    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // 开始加载
            const img = new Image()
            img.onload = () => {
              imageSrc.value = src
              isLoaded.value = true
            }
            img.onerror = () => {
              error.value = true
            }
            img.src = src
            observer.value?.unobserve(entry.target)
          }
        })
      },
      {
        rootMargin: '100px'
      }
    )

    // 如果元素已存在
    // observe()
  })

  onUnmounted(() => {
    observer.value?.disconnect()
  })

  return {
    imageSrc,
    isLoaded,
    error,
    observe
  }
}

// ==================== 防抖 ====================

export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  function debouncedFn(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      fn(...args)
    }, delay)
  }

  function cancel() {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  return {
    debouncedFn,
    cancel
  }
}

// ==================== 节流 ====================

export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number = 300
) {
  let inThrottle = false

  function throttledFn(...args: Parameters<T>) {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }

  return throttledFn
}

// ==================== 离线状态 ====================

export function useOffline() {
  const isOnline = ref(navigator.onLine)
  const wasOffline = ref(false)

  function handleOnline() {
    wasOffline.value = !isOnline.value
    isOnline.value = true
  }

  function handleOffline() {
    isOnline.value = false
  }

  onMounted(() => {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    isOnline,
    wasOffline
  }
}

// ==================== 本地缓存 ====================

export function useLocalStorage<T>(key: string, defaultValue: T) {
  const storedValue = localStorage.getItem(key)
  const data = ref<T>(
    storedValue ? JSON.parse(storedValue) : defaultValue
  )

  function setValue(value: T) {
    data.value = value
    localStorage.setItem(key, JSON.stringify(value))
  }

  function removeValue() {
    localStorage.removeItem(key)
    data.value = defaultValue
  }

  // 监听其他标签页的更改
  onMounted(() => {
    window.addEventListener('storage', (e) => {
      if (e.key === key && e.newValue) {
        data.value = JSON.parse(e.newValue)
      }
    })
  })

  return {
    data,
    setValue,
    removeValue
  }
}

// ==================== 请求缓存 ====================

import { cache } from '../api/cache'

export function useRequestCache<T>(
  key: string,
  fetchFn: () => Promise<T>,
  ttl: number = 300
) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  async function fetchData() {
    // 先尝试从缓存读取
    const cached = await cache.get(key)
    if (cached) {
      data.value = cached
      return cached
    }

    loading.value = true
    try {
      const result = await fetchFn()
      data.value = result
      await cache.set(key, result, ttl)
      return result
    } catch (e) {
      error.value = e as Error
      throw e
    } finally {
      loading.value = false
    }
  }

  function invalidate() {
    cache.delete(key)
    data.value = null
  }

  return {
    data,
    loading,
    error,
    fetchData,
    invalidate
  }
}
