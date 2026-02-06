<template>
  <div class="stats-dashboard">
    <n-spin :show="loading">
      <!-- 统计卡片 -->
      <n-grid :cols="xs ? 2 : 6" :x-gap="16" :y-gap="16">
        <n-gi v-for="stat in stats" :key="stat.label">
          <n-card class="stat-card" hoverable>
            <n-statistic :label="stat.label">
              <template #prefix>
                <n-icon :color="stat.color">
                  <component :is="stat.icon" />
                </n-icon>
              </template>
              {{ stat.value }}
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 趋势图表 -->
      <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
        <n-gi>
          <n-card title="📈 使用趋势 (近7天)">
            <div class="chart-container">
              <div class="bar-chart">
                <div
                  v-for="(item, i) in trends"
                  :key="i"
                  class="bar-item"
                >
                  <div
                    class="bar"
                    :style="{ height: `${item.percent}%` }"
                    :title="`${item.date}: ${item.count} 次`"
                  />
                  <div class="bar-label">{{ item.day }}</div>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="📊 资源类型分布">
            <div class="pie-container">
              <svg viewBox="0 0 100 100" class="pie-chart">
                <circle
                  v-for="(item, i) in resources"
                  :key="item.type"
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  :stroke="item.color"
                  :stroke-width="20"
                  :stroke-dasharray="getDashArray(item.count, totalResources)"
                  :stroke-dashoffset="getDashOffset(i)"
                  class="pie-segment"
                />
              </svg>
              <div class="pie-legend">
                <div v-for="item in resources" :key="item.type" class="legend-item">
                  <span class="dot" :style="{ background: item.color }"></span>
                  <span>{{ item.type }}</span>
                  <span class="count">{{ item.count }}</span>
                </div>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 列表 -->
      <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
        <n-gi>
          <n-card title="🔥 热门文档 (Top 5)">
            <n-list>
              <n-list-item v-for="(doc, i) in hotDocs" :key="doc.id">
                <template #prefix>
                  <n-avatar round :size="small" :color="colors[i]">{{ i + 1 }}</n-avatar>
                </template>
                <n-thing :title="doc.title">
                  <template #header-extra>
                    <n-tag size="small" type="info">
                      <template #icon><n-icon><EyeOutline /></template>
                      {{ doc.views }}
                    </n-tag>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card title="📈 活跃操作">
            <n-list>
              <n-list-item v-for="op in operations" :key="op.type">
                <n-thing :title="op.label">
                  <template #header-extra>
                    <n-tag size="small">{{ op.count }} 次</n-tag>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  FolderOutline,
  DocumentTextOutline,
  ChatbubblesOutline,
  CloudOutline,
  EyeOutline
} from '@vicons/ionicons5'
import { statsApi } from '../api/stats'

const xs = ref(window.innerWidth < 768)
const loading = ref(false)
const colors = ['#18a058', '#2080f0', '#f0a020', '#d03050', '#722ed1']

// 统计数据
const stats = ref([
  { label: '知识库', value: 0, color: '#18a058', icon: FolderOutline },
  { label: '文档', value: 0, color: '#2080f0', icon: DocumentTextOutline },
  { label: '对话', value: 0, color: '#f0a020', icon: ChatbubblesOutline },
  { label: '存储', value: '0 MB', color: '#d03050', icon: CloudOutline },
  { label: '活跃用户', value: 0, color: '#722ed1', icon: FolderOutline },
  { label: 'API 调用', value: 0, color: '#18a058', icon: FolderOutline },
])

// 趋势数据
const trends = ref<any[]>([])
const hotDocs = ref<any[]>([])
const operations = ref([
  { type: 'search', label: '搜索查询', count: 0 },
  { type: 'chat', label: 'RAG 对话', count: 0 },
  { type: 'upload', label: '文档上传', count: 0 },
  { type: 'export', label: '导出次数', count: 0 },
])

const resources = ref([
  { type: 'PDF', count: 0, color: '#d03050' },
  { type: 'DOCX', count: 0, color: '#2080f0' },
  { type: 'TXT', count: 0, color: '#f0a020' },
  { type: 'MD', count: 0, color: '#18a058' },
])

const totalResources = computed(() =>
  resources.value.reduce((sum, r) => sum + r.count, 0)
)

function getDashArray(count: number, total: number): string {
  const circumference = 2 * Math.PI * 40
  const percent = count / total
  return `${circumference * percent} ${circumference * (1 - percent)}`
}

function getDashOffset(index: number): number {
  const circumference = 2 * Math.PI * 40
  let offset = -circumference / 4
  for (let i = 0; i < index; i++) {
    offset -= (resources.value[i].count / totalResources.value) * circumference
  }
  return offset
}

async function loadStats() {
  loading.value = true
  try {
    // 加载统计数据
    const summary = await statsApi.getSummary()
    stats.value[0].value = summary.kb_count
    stats.value[1].value = summary.doc_count
    stats.value[2].value = summary.chat_count
    stats.value[3].value = `${summary.storage_mb} MB`
    stats.value[4].value = summary.active_users
    stats.value[5].value = summary.api_calls

    // 加载趋势
    const trendData = await statsApi.getTrends(7)
    const maxCount = Math.max(...trendData.map((t: any) => t.count), 1)
    trends.value = trendData.map((t: any) => ({
      ...t,
      percent: (t.count / maxCount) * 100,
      day: new Date(t.date).getDate() + '日'
    }))

    // 加载热门文档
    hotDocs.value = await statsApi.getHotDocs(5)

    // 加载资源分布
    const resData = await statsApi.getResourcesByType()
    resData.forEach((r: any, i: number) => {
      if (resources.value[i]) {
        resources.value[i].count = r.count
      }
    })

    // 加载操作统计
    const opData = await statsApi.getOperations()
    opData.forEach((op: any) => {
      const found = operations.value.find(o => o.type === op.type)
      if (found) {
        found.count = op.count
      }
    })
  } catch (error) {
    console.error('加载统计数据失败:', error)
    // 使用模拟数据
    useMockData()
  } finally {
    loading.value = false
  }
}

function useMockData() {
  stats.value = [
    { label: '知识库', value: 5, color: '#18a058', icon: FolderOutline },
    { label: '文档', value: 128, color: '#2080f0', icon: DocumentTextOutline },
    { label: '对话', value: 342, color: '#f0a020', icon: ChatbubblesOutline },
    { label: '存储', value: '156 MB', color: '#d03050', icon: CloudOutline },
    { label: '活跃用户', value: 12, color: '#722ed1', icon: FolderOutline },
    { label: 'API 调用', value: 2560, color: '#18a058', icon: FolderOutline },
  ]

  trends.value = Array.from({ length: 7 }, (_, i) => ({
    date: new Date(Date.now() - (6 - i) * 86400000).toISOString().split('T')[0],
    count: Math.floor(Math.random() * 50) + 10,
    percent: Math.floor(Math.random() * 80) + 20,
    day: new Date(Date.now() - (6 - i) * 86400000).getDate() + '日'
  }))

  hotDocs.value = [
    { id: '1', title: 'AI 入门指南', views: 1250 },
    { id: '2', title: 'Transformer 详解', views: 980 },
    { id: '3', title: 'RAG 最佳实践', views: 756 },
  ]

  resources.value = [
    { type: 'PDF', count: 45, color: '#d03050' },
    { type: 'DOCX', count: 32, color: '#2080f0' },
    { type: 'TXT', count: 28, color: '#f0a020' },
    { type: 'MD', count: 23, color: '#18a058' },
  ]

  operations.value = [
    { type: 'search', label: '搜索查询', count: 456 },
    { type: 'chat', label: 'RAG 对话', count: 342 },
    { type: 'upload', label: '文档上传', count: 128 },
    { type: 'export', label: '导出次数', count: 67 },
  ]
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', () => {
    xs.value = window.innerWidth < 768
  })
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.chart-container {
  padding: 16px 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  height: 100px;
  gap: 8px;
  padding: 0 8px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #18a058, #36ad6a);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  margin-top: auto;
}

.bar-label {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
}

.pie-container {
  display: flex;
  align-items: center;
  gap: 24px;
}

.pie-chart {
  width: 120px;
  height: 120px;
  transform: rotate(-90deg);
}

.pie-segment {
  transition: opacity 0.2s;
  cursor: pointer;
}

.pie-legend {
  flex: 1;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.count {
  margin-left: auto;
  color: #666;
}
</style>
