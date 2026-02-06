<template>
  <div class="dashboard">
    <n-grid :cols="4" :x-gap="16" :y-gap="16">
      <!-- 统计卡片 -->
      <n-gi :span="1">
        <n-card>
          <n-statistic label="知识库数量">
            <template #prefix>
              <n-icon color="#18a058"><FolderOutline /></n-icon>
            </template>
            {{ stats.kbCount }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi :span="1">
        <n-card>
          <n-statistic label="文档总数">
            <template #prefix>
              <n-icon color="#2080f0"><DocumentTextOutline /></n-icon>
            </template>
            {{ stats.docCount }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi :span="1">
        <n-card>
          <n-statistic label="对话次数">
            <template #prefix>
              <n-icon color="#f0a020"><ChatbubblesOutline /></n-icon>
            </template>
            {{ stats.chatCount }}
          </n-statistic>
        </n-card>
      </n-gi>
      
      <n-gi :span="1">
        <n-card>
          <n-statistic label="实体数量">
            <template #prefix>
              <n-icon color="#d03050"><NodesOutline /></n-icon>
            </template>
            {{ stats.entityCount }}
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 快捷操作 -->
    <n-card title="快捷操作" class="mt-16">
      <n-space>
        <n-button type="primary" @click="$router.push({ name: 'kbs' })">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          创建知识库
        </n-button>
        <n-button @click="$router.push({ name: 'chat' })">
          <template #icon><n-icon><ChatbubblesOutline /></n-icon></template>
          开始对话
        </n-button>
        <n-button @click="$router.push({ name: 'search' })">
          <template #icon><n-icon><SearchOutline /></n-icon></template>
          搜索知识库
        </n-button>
      </n-space>
    </n-card>

    <!-- 最近活动 -->
    <n-card title="最近活动" class="mt-16">
      <n-timeline>
        <n-timeline-item
          v-for="activity in recentActivities"
          :key="activity.id"
          :type="activity.type"
          :title="activity.title"
          :content="activity.content"
          :time="activity.time"
        />
      </n-timeline>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  FolderOutline,
  DocumentTextOutline,
  ChatbubblesOutline,
  NodesOutline,
  AddOutline,
  SearchOutline
} from '@vicons/ionicons5'

const stats = ref({
  kbCount: 0,
  docCount: 0,
  chatCount: 0,
  entityCount: 0
})

const recentActivities = ref([
  {
    id: '1',
    type: 'success' as const,
    title: '创建知识库',
    content: '新建了「AI 学习笔记」知识库',
    time: '10分钟前'
  },
  {
    id: '2',
    type: 'info' as const,
    title: '上传文档',
    content: '上传了「Transformer 架构详解.pdf」',
    time: '30分钟前'
  },
  {
    id: '3',
    type: 'warning' as const,
    title: 'RAG 对话',
    content: '询问「什么是注意力机制？」',
    time: '1小时前'
  }
])

onMounted(() => {
  // TODO: 从 API 获取统计数据
  stats.value = {
    kbCount: 3,
    docCount: 15,
    chatCount: 42,
    entityCount: 128
  }
})
</script>

<style scoped>
.mt-16 {
  margin-top: 16px;
}
</style>
