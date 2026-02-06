<template>
  <div class="mobile-layout" :class="{ 'has-tabbar': showTabBar }">
    <!-- 移动端顶部栏 -->
    <n-layout-header v-if="isMobile" class="mobile-header">
      <div class="header-left">
        <n-button quaternary circle @click="showMenu = true">
          <template #icon><n-icon><MenuOutline /></n-icon></template>
        </n-button>
      </div>
      <div class="header-title">{{ pageTitle }}</div>
      <div class="header-right">
        <slot name="header-right" />
      </div>
    </n-layout-header>

    <!-- 移动端 TabBar -->
    <n-layout-footer v-if="showTabBar && isMobile" class="mobile-tabbar">
      <n-tabbar
        v-model:value="activeTab"
        :bordered="false"
        @update:value="handleTabChange"
      >
        <n-tabbar-item name="home" tab="首页">
          <template #icon>
            <n-icon><HomeOutline /></n-icon>
          </template>
        </n-tabbar-item>
        <n-tabbar-item name="kbs" tab="知识库">
          <template #icon>
            <n-icon><FolderOutline /></n-icon>
          </template>
        </n-tabbar-item>
        <n-tabbar-item name="chat" tab="对话">
          <template #icon>
            <n-icon><ChatbubblesOutline /></n-icon>
          </template>
        </n-tabbar-item>
        <n-tabbar-item name="profile" tab="我的">
          <template #icon>
            <n-icon><PersonOutline /></n-icon>
          </template>
        </n-tabbar-item>
      </n-tabbar>
    </n-layout-footer>

    <!-- 抽屉菜单 -->
    <n-drawer v-model:show="showMenu" :width="280" placement="left">
      <n-drawer-content title="菜单" closable>
        <n-menu
          :options="menuOptions"
          :value="activeRoute"
          @update:value="handleMenuClick"
        />
      </n-drawer-content>
    </n-drawer>

    <!-- 主内容区 -->
    <div class="mobile-content" :class="{ 'with-tabbar': showTabBar }">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeOutline,
  FolderOutline,
  ChatbubblesOutline,
  PersonOutline,
  MenuOutline
} from '@vicons/ionicons5'

const props = withDefaults(defineProps<{
  showTabBar?: boolean
}>(), {
  showTabBar: true
})

const router = useRouter()
const route = useRoute()

const showMenu = ref(false)
const isMobile = ref(false)
const activeTab = ref('home')

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    home: '首页',
    kbs: '知识库',
    chat: '对话',
    profile: '我的'
  }
  return titles[activeTab.value] || route.meta.title || 'LiteKB'
})

const activeRoute = computed(() => route.name as string)

const menuOptions = [
  { label: '首页', key: 'home', icon: () => HomeOutline },
  { label: '知识库', key: 'kbs', icon: () => FolderOutline },
  { label: 'RAG 对话', key: 'chat', icon: () => ChatbubblesOutline },
  { type: 'divider' },
  { label: '搜索', key: 'search', icon: () => SearchOutline },
  { label: '设置', key: 'settings', icon: () => SettingsOutline }
]

function handleTabChange(tab: string) {
  router.push({ name: tab })
}

function handleMenuClick(key: string) {
  showMenu.value = false
  router.push({ name: key })
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

function handleResize() {
  checkMobile()
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', handleResize)
  
  // 初始化 activeTab
  const routeName = route.name as string
  if (['home', 'kbs', 'chat', 'profile'].includes(routeName)) {
    activeTab.value = routeName
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<script lang="ts">
import { SearchOutline, SettingsOutline } from '@vicons/ionicons5'
</script>

<style scoped>
.mobile-layout {
  min-height: 100vh;
  background: #f5f7f9;
}

.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  z-index: 100;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.header-title {
  font-weight: 600;
  font-size: 16px;
}

.mobile-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: white;
  box-shadow: 0 -1px 2px rgba(0, 0, 0, 0.05);
}

.mobile-content {
  padding-top: 56px;
  padding-bottom: env(safe-area-inset-bottom);
  min-height: 100vh;
}

.mobile-content.with-tabbar {
  padding-bottom: 60px;
}

/* 平板和桌面端 */
@media (min-width: 768px) {
  .mobile-layout {
    display: none;
  }
}
</style>
