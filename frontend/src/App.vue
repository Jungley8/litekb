<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <div class="app-container" :class="{ 'dark-mode': isDark }">
            <n-layout has-sider>
              <!-- 侧边栏 -->
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed-width="64"
                :width="240"
                :collapsed="collapsed"
                show-trigger
                @collapse="collapsed = true"
                @expand="collapsed = false"
              >
                <div class="logo" @click="$router.push('/')">
                  <n-icon size="24" color="#18a058">
                    <BookOutline />
                  </n-icon>
                  <span v-show="!collapsed" class="logo-text">LiteKB 🦊</span>
                </div>
                
                <n-menu
                  v-model:value="activeKey"
                  :collapsed="collapsed"
                  :collapsed-width="64"
                  :collapsed-icon-size="22"
                  :options="menuOptions"
                  @update:value="handleMenuClick"
                />
                
                <!-- 主题切换 -->
                <div class="theme-toggle">
                  <n-button quaternary block @click="toggleTheme">
                    <template #icon>
                      <n-icon><MoonOutline v-if="isDark" /><SunnyOutline v-else /></n-icon>
                    </template>
                    <span v-show="!collapsed">{{ isDark ? '浅色模式' : '深色模式' }}</span>
                  </n-button>
                </div>
              </n-layout-sider>

              <!-- 主内容区 -->
              <n-layout>
                <n-layout-header bordered class="header">
                  <div class="header-left">
                    <h2>{{ pageTitle }}</h2>
                  </div>
                  <div class="header-right">
                    <n-button quaternary circle @click="showSearch = true">
                      <template #icon>
                        <n-icon><SearchOutline /></n-icon>
                      </template>
                    </n-button>
                    
                    <!-- 组织选择器 -->
                    <OrganizationSelector />
                    
                    <n-avatar round size="small" class="user-avatar" @click="$router.push('/settings')">
                      {{ userInitials }}
                    </n-avatar>
                  </div>
                </n-layout-header>

                <n-layout-content class="content" :class="{ 'dark-content': isDark }">
                  <router-view />
                </n-layout-content>
              </n-layout>
            </n-layout>
          </div>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon, darkTheme } from 'naive-ui'
import {
  BookOutline,
  HomeOutline,
  FolderOutline,
  ChatbubblesOutline,
  SearchOutline,
  MapOutline,
  SettingsOutline,
  BarChartOutline,
  MoonOutline,
  SunnyOutline
} from '@vicons/ionicons5'
import OrganizationSelector from './components/OrganizationSelector.vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const activeKey = ref('home')
const isDark = ref(false)
const showSearch = ref(false)

// 用户信息
const userInitials = computed(() => {
  return 'U'
})

// 页面标题
const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    home: '仪表盘',
    kbs: '知识库',
    kbDetail: '知识库详情',
    chat: 'RAG 对话',
    search: '搜索',
    graph: '知识图谱',
    stats: '统计',
    settings: '设置'
  }
  return titles[route.name as string] || 'LiteKB'
})

// 主题切换
function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// 主题配置
const themeOverrides = computed(() => ({
  common: {
    primaryColor: '#18a058',
    primaryColorHover: '#36ad6a',
    primaryColorPressed: '#0c7a43',
    borderColor: isDark.value ? '#333' : '#e0e0e6',
    tableColor: isDark.value ? '#1a1a1a' : '#fff',
    cardColor: isDark.value ? '#1a1a1a' : '#fff',
    modalColor: isDark.value ? '#1a1a1a' : '#fff',
    popoverColor: isDark.value ? '#1a1a1a' : '#fff',
    bodyColor: isDark.value ? '#0f0f0f' : '#f5f7f9',
    textColorBase: isDark.value ? '#fff' : '#333',
    textColor1: isDark.value ? '#fff' : '#333',
    textColor2: isDark.value ? '#ccc' : '#666',
    textColor3: isDark.value ? '#999' : '#999',
  }
}))

// 菜单配置
function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  {
    label: '仪表盘',
    key: 'home',
    icon: renderIcon(HomeOutline)
  },
  {
    label: '知识库',
    key: 'kbs',
    icon: renderIcon(FolderOutline)
  },
  {
    label: '搜索',
    key: 'search',
    icon: renderIcon(SearchOutline)
  },
  {
    label: 'RAG 对话',
    key: 'chat',
    icon: renderIcon(ChatbubblesOutline)
  },
  {
    label: '知识图谱',
    key: 'graph',
    icon: renderIcon(MapOutline)
  },
  {
    label: '统计',
    key: 'stats',
    icon: renderIcon(BarChartOutline)
  },
  {
    type: 'divider'
  },
  {
    label: '设置',
    key: 'settings',
    icon: renderIcon(SettingsOutline)
  }
]

function handleMenuClick(key: string) {
  activeKey.value = key
  router.push({ name: key })
}

// 初始化主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  isDark.value = savedTheme === 'dark'
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  cursor: pointer;
  transition: background 0.3s;
}

.logo:hover {
  background: rgba(24, 160, 88, 0.1);
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #18a058;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  cursor: pointer;
}

.content {
  padding: 24px;
  height: calc(100vh - 64px);
  overflow: auto;
  background: #f5f7f9;
  transition: background 0.3s;
}

.content.dark-content {
  background: #0f0f0f;
}

.theme-toggle {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  padding: 0 12px;
}

/* 深色模式适配 */
.dark-mode .n-layout-sider {
  background: #1a1a1a !important;
}

.dark-mode .n-layout-header {
  background: #1a1a1a !important;
}

.dark-mode .n-card {
  background: #1a1a1a;
  border-color: #333;
}

.dark-mode .n-button {
  color: #fff;
}
</style>
