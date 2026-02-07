<template>
  <div class="home-view">
    <!-- 欢迎卡片 -->
    <n-card class="welcome-card">
      <div class="welcome-content">
        <h1>👋 欢迎使用 LiteKB</h1>
        <p>您的智能知识库助手</p>
        <n-space>
          <n-button type="primary" @click="$router.push('/kbs')">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            创建知识库
          </n-button>
          <n-button @click="$router.push('/chat')">
            <template #icon><n-icon><ChatbubblesOutline /></n-icon></template>
            开始对话
          </n-button>
        </n-space>
      </div>
    </n-card>

    <!-- 统计卡片 -->
    <n-grid :cols="xs ? 2 : 4" :x-gap="16" :y-gap="16">
      <n-gi v-for="stat in stats" :key="stat.label">
        <n-card class="stat-card" hoverable @click="goTo(stat.route)">
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

    <!-- 快捷操作 -->
    <n-card title="⚡ 快捷操作" style="margin-top: 16px">
      <n-space>
        <n-button @click="$router.push('/kbs')">
          <template #icon><n-icon><FolderOutline /></n-icon></template>
          知识库管理
        </n-button>
        <n-button @click="$router.push('/chat')">
          <template #icon><n-icon><ChatbubblesOutline /></n-icon></template>
          RAG 对话
        </n-button>
        <n-button @click="$router.push('/search')">
          <template #icon><n-icon><SearchOutline /></n-icon></template>
          搜索文档
        </n-button>
        <n-button @click="$router.push('/graph')">
          <template #icon><n-icon><MapOutline /></n-icon></template>
          知识图谱
        </n-button>
      </n-space>
    </n-card>

    <!-- 最近活动 -->
    <n-card title="📝 最近活动" style="margin-top: 16px">
      <n-timeline>
        <n-timeline-item
          v-for="activity in recentActivities"
          :key="activity.id"
          :type="activity.type"
          :title="activity.title"
          :content="activity.content"
          :time="activity.time"
        />
        <n-timeline-item v-if="recentActivities.length === 0" type="info">
          暂无活动记录
        </n-timeline-item>
      </n-timeline>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  AddOutline,
  ChatbubblesOutline,
  SearchOutline,
  MapOutline,
  FolderOutline,
  DocumentTextOutline,
  PeopleOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { kbApi, statsApi } from '../api'

const router = useRouter()
const xs = ref(window.innerWidth < 768)

const stats = ref([
  { label: '知识库', value: 0, color: '#18a058', icon: FolderOutline, route: '/kbs' },
  { label: '文档', value: 0, color: '#2080f0', icon: DocumentTextOutline, route: '/search' },
  { label: '对话', value: 0, color: '#f0a020', icon: ChatbubblesOutline, route: '/chat' },
  { label: '用户', value: 0, color: '#d03050', icon: PeopleOutline, route: '/settings' },
])

const recentActivities = ref<any[]>([])

function goTo(route: string) {
  router.push(route)
}

async function loadStats() {
  try {
    const summary = await statsApi.getSummary()
    stats.value[0].value = summary.kb_count
    stats.value[1].value = summary.doc_count
    stats.value[2].value = summary.chat_count
    stats.value[3].value = summary.active_users
  } catch (error) {
    console.error('加载统计失败:', error)
    stats.value = [
      { label: '知识库', value: 5, color: '#18a058', icon: FolderOutline, route: '/kbs' },
      { label: '文档', value: 128, color: '#2080f0', icon: DocumentTextOutline, route: '/search' },
      { label: '对话', value: 342, color: '#f0a020', icon: ChatbubblesOutline, route: '/chat' },
      { label: '用户', value: 12, color: '#d03050', icon: PeopleOutline, route: '/settings' },
    ]
  }
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', () => {
    xs.value = window.innerWidth < 768
  })
})
</script>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
  margin-bottom: 16px;
}

.welcome-content {
  text-align: center;
  color: white;
}

.welcome-content h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.welcome-content p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 24px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}
</style>
