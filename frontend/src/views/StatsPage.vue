<template>
  <div class="stats-page">
    <n-grid :cols="xs ? 1 : 4" :x-gap="16" :y-gap="16">
      <!-- 统计卡片 -->
      <n-gi v-for="stat in stats" :key="stat.label" @click="$router.push(stat.route)">
        <n-card class="stat-card" hoverable>
          <div class="stat-content">
            <n-icon :size="32" :color="stat.color">
              <component :is="stat.icon" />
            </n-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </div>
          <n-progress
            v-if="stat.max"
            type="line"
            :percentage="Math.round(stat.value / stat.max * 100)"
            :show-indicator="false"
            :height="4"
          />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 趋势图表 -->
    <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
      <!-- 使用趋势 -->
      <n-gi>
        <n-card title="📈 使用趋势">
          <div class="chart-container">
            <div class="bar-chart">
              <div
                v-for="(item, i) in trends"
                :key="i"
                class="bar-item"
              >
                <div
                  class="bar"
                  :style="{ height: `${item.value}%` }"
                />
                <div class="bar-label">{{ item.label }}</div>
              </div>
            </div>
          </div>
        </n-card>
      </n-gi>

      <!-- 资源分布 -->
      <n-gi>
        <n-card title="📊 资源分布">
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
                :stroke-dasharray="getDashArray(item.value, resourcesTotal)"
                :stroke-dashoffset="getDashOffset(resources, i)"
                class="pie-segment"
              />
            </svg>
            <div class="pie-legend">
              <div v-for="item in resources" :key="item.type" class="legend-item">
                <span class="dot" :style="{ background: item.color }"></span>
                <span>{{ item.type }}</span>
                <span class="count">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 列表 -->
    <n-grid :cols="xs ? 1 : 2" :x-gap="16" :y-gap="16" style="margin-top: 16px">
      <!-- 热门文档 -->
      <n-gi>
        <n-card title="🔥 热门文档">
          <n-list>
            <n-list-item v-for="(doc, i) in hotDocs" :key="doc.id">
              <template #prefix>
                <n-avatar :size="small" :color="colors[i]">
                  {{ i + 1 }}
                </n-avatar>
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

      <!-- 活跃用户 -->
      <n-gi>
        <n-card title="👥 活跃用户">
          <n-list>
            <n-list-item v-for="user in activeUsers" :key="user.id">
              <template #prefix>
                <n-avatar round size="small">
                  {{ user.name[0] }}
                </n-avatar>
              </template>
              <n-thing :title="user.name">
                <template #header-extra>
                  <n-tag size="small">{{ user.actions }} 次操作</n-tag>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 快捷操作 -->
    <n-card title="⚡ 快捷操作" style="margin-top: 16px">
      <n-space>
        <n-button @click="$router.push('/kbs')">
          <template #icon><n-icon><FolderOutline /></n-icon></template>
          创建知识库
        </n-button>
        <n-button @click="$router.push('/chat')">
          <template #icon><n-icon><ChatbubblesOutline /></n-icon></template>
          开始对话
        </n-button>
        <n-button @click="$router.push('/settings')">
          <template #icon><n-icon><SettingsOutline /></n-icon></template>
          系统设置
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  FolderOutline,
  DocumentTextOutline,
  ChatbubblesOutline,
  PeopleOutline,
  TimeOutline,
  EyeOutline,
  SettingsOutline
} from '@vicons/ionicons5'

const xs = ref(window.innerWidth < 768)
const colors = ['#18a058', '#2080f0', '#f0a020', '#d03050', '#722ed1']

const stats = ref([
  { label: '知识库', value: 5, max: 10, color: '#18a058', icon: FolderOutline, route: '/kbs' },
  { label: '文档', value: 128, max: 1000, color: '#2080f0', icon: DocumentTextOutline, route: '/search' },
  { label: '对话', value: 342, max: 1000, color: '#f0a020', icon: ChatbubblesOutline, route: '/chat' },
  { label: '用户', value: 12, max: 50, color: '#d03050', icon: PeopleOutline, route: '/settings' },
])

const trends = ref([
  { label: '周一', value: 65 },
  { label: '周二', value: 80 },
  { label: '周三', value: 45 },
  { label: '周四', value: 90 },
  { label: '周五', value: 70 },
  { label: '周六', value: 30 },
  { label: '周日', value: 25 },
])

const resources = ref([
  { type: 'PDF', value: 45, color: '#d03050' },
  { type: 'DOCX', value: 32, color: '#2080f0' },
  { type: 'TXT', value: 28, color: '#f0a020' },
  { type: 'MD', value: 23, color: '#18a058' },
])

const resourcesTotal = computed(() => 
  resources.value.reduce((sum, r) => sum + r.value, 0)
)

const hotDocs = ref([
  { id: '1', title: 'AI 入门指南', views: 1250 },
  { id: '2', title: 'Transformer 详解', views: 980 },
  { id: '3', title: 'RAG 最佳实践', views: 756 },
  { id: '4', title: '知识图谱入门', views: 543 },
])

const activeUsers = ref([
  { id: '1', name: '张三', actions: 156 },
  { id: '2', name: '李四', actions: 98 },
  { id: '3', name: '王五', actions: 67 },
])

function getDashArray(value: number, total: number): string {
  const circumference = 2 * Math.PI * 40
  const percent = value / total
  return `${circumference * percent} ${circumference * (1 - percent)}`
}

function getDashOffset(list: any[], index: number): number {
  const circumference = 2 * Math.PI * 40
  let offset = -circumference / 4
  for (let i = 0; i < index; i++) {
    offset -= (list[i].value / resourcesTotal.value) * circumference
  }
  return offset
}

onMounted(() => {
  window.addEventListener('resize', () => {
    xs.value = window.innerWidth < 768
  })
})
</script>

<style scoped>
.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.chart-container {
  padding: 16px 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  height: 120px;
  gap: 8px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar {
  width: 100%;
  background: linear-gradient(to top, #18a058, #36ad6a);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
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
</style>
