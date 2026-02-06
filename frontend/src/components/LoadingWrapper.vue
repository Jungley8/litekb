<template>
  <div class="loading-container">
    <!-- 全局加载遮罩 -->
    <n-spin v-if="globalLoading" :show="globalLoading" class="global-spin">
      <div class="global-spin-content">
        <n-spin :size="60" :show="true" />
        <p>{{ loadingText }}</p>
      </div>
    </n-spin>
    
    <!-- 页面加载骨架屏 -->
    <template v-else-if="isPageLoading">
      <div class="skeleton-page">
        <n-card v-for="i in 3" :key="i" class="skeleton-card">
          <n-skeleton :height="200" :width="'100%'" />
          <n-skeleton :height="20" :width="'60%'" style="margin-top: 16px" />
          <n-skeleton :height="20" :width="'80%'" style="margin-top: 12px" />
          <n-skeleton :height="20" :width="'40%'" style="margin-top: 12px" />
        </n-card>
      </div>
    </template>
    
    <!-- 实际内容 -->
    <slot v-else />
  </div>
</template>

<script setup lang="ts">
import { ref, provide, onMounted } from 'vue'

const props = defineProps<{
  loading?: boolean
  text?: string
}>()

const emit = defineEmits<{
  (e: 'update:loading', loading: boolean): void
}>()

const globalLoading = ref(false)
const loadingText = ref('加载中...')
const isPageLoading = ref(false)

// 提供给子组件的加载状态
const loadingState = ref({
  isLoading: false,
  text: ''
})

provide('loadingState', loadingState)

function setLoading(loading: boolean, text: string = '加载中...') {
  loadingState.value.isLoading = loading
  loadingState.value.text = text
  emit('update:loading', loading)
  globalLoading.value = loading
  loadingText.value = text
}

// 全局加载
function showLoading(text: string = '加载中...') {
  setLoading(true, text)
}

function hideLoading() {
  setLoading(false)
}

// 骨架屏模式
function showSkeleton() {
  isPageLoading.value = true
}

function hideSkeleton() {
  isPageLoading.value = false
}

// 带加载的内容
async function withLoading<T>(fn: () => Promise<T>, text: string = '处理中...'): Promise<T> {
  showLoading(text)
  try {
    return await fn()
  } finally {
    hideLoading()
  }
}

// 带骨架屏的内容
async function withSkeleton<T>(fn: () => Promise<T>): Promise<T> {
  showSkeleton()
  try {
    return await fn()
  } finally {
    hideSkeleton()
  }
}

// 暴露方法
defineExpose({
  showLoading,
  hideLoading,
  showSkeleton,
  hideSkeleton,
  withLoading,
  withSkeleton
})
</script>

<style scoped>
.loading-container {
  min-height: 100%;
}

.global-spin {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.global-spin-content {
  background: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
}

.global-spin-content p {
  margin-top: 16px;
  color: #666;
}

.skeleton-page {
  padding: 16px;
}

.skeleton-card {
  margin-bottom: 16px;
}
</style>
