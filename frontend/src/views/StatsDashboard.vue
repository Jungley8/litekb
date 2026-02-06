<template>
  <div class="stats-dashboard">
    <!-- 统计卡片 -->
    <n-grid :cols="xs ? 2 : 6" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="知识库">
            <template #prefix>
              <n-icon color="#18a058"><FolderOutline /></n-icon>
            </template>
            {{ stats.total_kbs }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="文档">
            <template #prefix>
              <n-icon color="#2080f0"><DocumentTextOutline /></n-icon>
            </template>
            {{ stats.total_docs }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="对话">
            <template #prefix>
              <n-icon color="#f0a020"><ChatbubblesOutline /></n-icon>
            </template>
            {{ stats.total_conversations }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="存储">
            <template #prefix>
              <n-icon color="#d03050"><CloudOutline /></n-icon>
            </template>
            {{ stats.storage_used_mb }} MB
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="响应时间">
            <template #prefix>
              <n-icon color="#18a058"><TimerOutline /></n-icon>
            </template>
            {{ responseStats.avg_response_time }}s
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi>
        <n-card class="stat-card">
          <n-statistic label="满意度">
            <template #prefix>
              <n-icon color="#18a058"><HappyOutline /></n-icon>
            </template>
            {{ (responseStats.satisfaction_rate * 100).toFixed(0) }}%
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 图表区域 -->
    <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
      <!-- 使用趋势 -->
      <n-gi>
        <n-card title="使用趋势">
          <div class="chart-container">
            <div class="trend-chart">
              <div
                v-for="(item, i) in trends.slice(-14)"
                :key="i"
                class="trend-bar"
                :style="{ height: `${(item.count / maxTrend) * 100}%` }"
                :title="`${item.date}: ${item.count}`"
              />
            </div>
            <div class="chart-labels">
              <span v-for="(item, i) in trends.slice(-14)" :key="i" class="label">
                {{ formatDate(item.date) }}
              </span>
            </div>
          </div>
        </n-card>
      </n-gi>

      <!-- 资源类型分布 -->
      <n-gi>
        <n-card title="资源类型">
          <div class="pie-chart">
            <svg viewBox="0 0 100 100" class="pie">
              <circle
                v-for="(item, i) in resourceTypes"
                :key="item.type"
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                :stroke="colors[i % colors.length]"
                :stroke-width="20"
                :stroke-dasharray="getDashArray(item.count, totalResources)"
                :stroke-dashoffset="getDashOffset(i, resourceTypes)"
                class="pie-segment"
              />
            </svg>
            <div class="pie-legend">
              <div
                v-for="(item, i) in resourceTypes"
                :key="item.type"
                class="legend-item"
              >
                <span class="dot" :style="{ background: colors[i % colors.length] }"></span>
                <span>{{ item.type }}</span>
                <span class="count">{{ item.count }}</span>
              </div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 列表区域 -->
    <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
      <!-- 热门文档 -->
      <n-gi>
        <n-card title="热门文档">
          <n-list>
            <n-list-item v-for="(doc, i) in popularDocs" :key="doc.id">
              <template #prefix>
                <n-avatar round size="small" :color="colors[i]">
                  {{ i + 1 }}
                </n-avatar>
              </template>
              <n-thing :title="doc.title">
                <template #header-extra>
                  <n-icon><EyeOutline /></n-icon>
                  {{ doc.views }}
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-gi>

      <!-- 热门搜索 -->
      <n-gi>
        <n-card title="热门搜索">
          <n-list>
            <n-list-item v-for="(s, i) in popularSearches" :key="s.query">
              <template #prefix>
                <n-tag size="small" :type="getSearchTagType(i)">
                  {{ i + 1 }}
                </n-tag>
              </template>
              <n-thing :title="s.query">
                <template #header-extra>
                  <n-icon><SearchOutline /></n-icon>
                  {{ s.count }}
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 活动热力图 -->
    <n-card title="28天活动" style="margin-top: 16px">
      <div class="heatmap">
        <div
          v-for="(data, date) in activityHeatmap"
          :key="date"
          class="heat-cell"
          :style="{ opacity: getHeatOpacity(data.documents + data.conversations) }"
          :title="`${date}: ${data.documents} 文档, ${data.conversations} 对话`"
        >
          {{ date.slice(-2) }}
        </div>
      </div>
      <div class="heatmap-legend">
        <span>少</span>
        <div class="gradient"></div>
        <span>多</span>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  FolderOutline,
  DocumentTextOutline,
  ChatbubblesOutline,
  CloudOutline,
  TimerOutline,
  HappyOutline,
  EyeOutline,
  SearchOutline
} from '@vicons/ionicons5'

const props = defineProps<{
  orgId: string
}>()

// 响应式断点
const xs = ref(window.innerWidth < 768)

const colors = ['#18a058', '#2080f0', '#f0a020', '#d03050', '#722ed1', '#eb2f96']

// 统计数据
const stats = ref({
  total_kbs: 5,
  total_docs: 128,
  total_chunks: 1250,
  total_conversations: 342,
  storage_used_mb: 156.5
})

const trends = ref<any[]>([])
const popularDocs = ref<any[]>([])
const popularSearches = ref<any[]>([])
const responseStats = ref({
  avg_response_time: 1.2,
  satisfaction_rate: 0.92,
  total_questions: 1250
})

const resourceTypes = ref([
  { type: 'PDF', count: 45 },
  { type: 'DOCX', count: 32 },
  { type: 'TXT', count: 28 },
  { type: 'MD', count: 23 }
])

const activityHeatmap = ref<any>({})

const totalResources = computed(() =>
  resourceTypes.value.reduce((sum, r) => sum + r.count, 0)
)

const maxTrend = computed(() =>
  Math.max(...trends.value.map(t => t.count), 1)
)

function formatDate(dateStr: string): string {
  return new Date(dateStr).getDate().toString()
}

function getDashArray(count: number, total: number): string {
  const circumference = 2 * Math.PI * 40
  const percent = count / total
  return `${circumference * percent} ${circumference * (1 - percent)}`
}

function getDashOffset(index: number, data: any[]): number {
  const circumference = 2 * Math.PI * 40
  let offset = -circumference / 4
  
  for (let i = 0; i < index; i++) {
    offset -= (data[i].count / totalResources.value) * circumference
  }
  
  return offset
}

function getHeatOpacity(count: number): number {
  const max = 30
  return Math.min(0.2 + (count / max) * 0.8, 1)
}

function getSearchTagType(index: number): string {
  if (index === 0) return 'error'
  if (index === 1) return 'warning'
  return 'default'
}

onMounted(() => {
  // TODO: 加载真实数据
  trends.value = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - i * 86400000).toISOString().split('T')[0],
    count: 10 + Math.floor(Math.random() * 50)
  })).reverse()
  
  popularDocs.value = [
    { id: '1', title: 'AI 入门指南', views: 1250 },
    { id: '2', title: 'Transformer 详解', views: 980 },
    { id: '3', title: 'RAG 最佳实践', views: 756 },
  ]
  
  popularSearches.value = [
    { query: '注意力机制', count: 256 },
    { query: 'BERT', count: 189 },
    { query: 'GPT', count: 156 },
  ]
  
  const heatmap: any = {}
  for (let i = 27; i >= 0; i--) {
    const date = new Date(Date.now() - i * 86400000).toISOString().split('T')[0]
    heatmap[date] = {
      documents: Math.floor(Math.random() * 20),
      conversations: Math.floor(Math.random() * 25)
    }
  }
  activityHeatmap.value = heatmap
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.chart-container {
  padding: 16px 0;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  height: 100px;
  gap: 4px;
  padding: 0 8px;
}

.trend-bar {
  flex: 1;
  background: linear-gradient(to top, #18a058, #36ad6a);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.trend-bar:hover {
  background: #0c7a43;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 10px;
  color: #999;
}

.label {
  flex: 1;
  text-align: center;
}

.pie-chart {
  display: flex;
  align-items: center;
  gap: 24px;
}

.pie {
  width: 120px;
  height: 120px;
  transform: rotate(-90deg);
}

.pie-segment {
  cursor: pointer;
  transition: opacity 0.2s;
}

.pie-segment:hover {
  opacity: 0.8;
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

.heatmap {
  display: grid;
  grid-template-columns: repeat(14, 1fr);
  gap: 4px;
  padding: 16px 0;
}

.heat-cell {
  aspect-ratio: 1;
  background: #18a058;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: white;
  cursor: pointer;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.gradient {
  width: 100px;
  height: 8px;
  background: linear-gradient(to right, rgba(24, 160, 88, 0.2), #18a058);
  border-radius: 4px;
}
</style>
