<template>
  <n-spin :show="loading">
    <div class="search-view">
      <!-- 搜索框 -->
      <n-card class="search-card" :bordered="false">
        <n-input-group>
          <n-input
            v-model:value="query"
            placeholder="搜索知识库..."
            :loading="loading"
            @keydown.enter="handleSearch"
            size="large"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          <n-button type="primary" size="large" @click="handleSearch">
            搜索
          </n-button>
        </n-input-group>

        <!-- 搜索选项 -->
        <div class="search-options">
          <n-space>
            <span>知识库:</span>
            <n-select
              v-model:value="selectedKBs"
              multiple
              placeholder="全部"
              :options="kbOptions"
              style="width: 300px"
              clearable
            />
            <n-select
              v-model:value="strategy"
              placeholder="检索策略"
              :options="strategyOptions"
              style="width: 150px"
            />
          </n-space>
        </div>
      </n-card>

      <!-- 搜索结果 -->
      <div v-if="hasSearched" class="results-section">
        <div class="results-header">
          <span>找到 {{ results.length }} 个结果</span>
          <n-tag v-if="strategy" type="info">{{ strategy }}</n-tag>
        </div>

        <n-spin :show="loading">
          <n-list v-if="results.length > 0" class="results-list">
            <n-list-item v-for="result in results" :key="result.id">
              <n-thing>
                <template #header>
                  <n-button text type="primary" @click="viewDocument(result)">
                    {{ result.title }}
                  </n-button>
                </template>
                <template #header-extra>
                  <n-tag size="small" type="success">
                    相似度: {{ (result.score * 100).toFixed(1) }}%
                  </n-tag>
                </template>
                <template #description>
                  <n-tag size="small">{{ result.type }}</n-tag>
                </template>
                <div class="result-content" v-html="highlightResult(result.content)"></div>
              </n-thing>
            </n-list-item>
          </n-list>

          <n-empty v-else description="未找到相关结果" />
        </n-spin>
      </div>

      <!-- 初始状态 -->
      <div v-else class="initial-state">
        <n-empty description="输入关键词开始搜索">
          <template #icon>
            <n-icon size="64" color="#999"><SearchOutline /></n-icon>
          </template>
        </n-empty>
      </div>
    </div>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import { searchApi, kbApi } from '../api'

interface SearchResult {
  id: string
  title: string
  content: string
  score: number
  type: string
}

const message = useMessage()

const query = ref('')
const loading = ref(false)
const hasSearched = ref(false)
const results = ref<SearchResult[]>([])
const selectedKBs = ref<string[]>([])
const strategy = ref('hybrid')

const kbList = ref<Array<{ id: string; name: string }>>([])
const kbOptions = computed(() =>
  kbList.value.map(kb => ({ label: kb.name, value: kb.id }))
)

const strategyOptions = [
  { label: '混合检索', value: 'hybrid' },
  { label: '向量检索', value: 'vector' },
  { label: '关键词检索', value: 'keyword' },
  { label: '图谱检索', value: 'graph' }
]

function highlightResult(content: string): string {
  if (!query.value) return content
  
  const regex = new RegExp(`(${query.value})`, 'gi')
  return content.replace(regex, '<span class="search-highlight">$1</span>')
}

async function handleSearch() {
  if (!query.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  hasSearched.value = true

  try {
    // TODO: 调用实际搜索 API
    // 模拟搜索结果
    await new Promise(resolve => setTimeout(resolve, 500))
    
    results.value = [
      {
        id: '1',
        title: 'Transformer 架构详解',
        content: `Transformer 是一种基于注意力机制的神经网络架构，${query.value} 在其中扮演重要角色...`,
        score: 0.95,
        type: 'document'
      },
      {
        id: '2',
        title: '注意力机制原理',
        content: `注意力机制允许模型在处理序列时关注最相关的部分，${query.value} 是其核心概念之一...`,
        score: 0.87,
        type: 'document'
      },
      {
        id: '3',
        title: 'BERT 预训练模型',
        content: `BERT 使用双向 Transformer 编码器，${query.value} 在其训练过程中有重要应用...`,
        score: 0.82,
        type: 'document'
      }
    ].filter(r => r.content.toLowerCase().includes(query.value.toLowerCase()) || true)
  } catch (error) {
    message.error('搜索失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function viewDocument(result: SearchResult) {
  message.info(`查看文档: ${result.title}`)
}

async function loadKBs() {
  try {
    kbList.value = await kbApi.list()
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
}

onMounted(() => {
  loadKBs()
})
</script>

<style scoped>
.search-view {
  max-width: 900px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 16px;
}

.search-options {
  margin-top: 12px;
  font-size: 14px;
  color: #666;
}

.results-section {
  margin-top: 16px;
}

.results-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  color: #666;
}

.results-list {
  background: white;
  border-radius: 8px;
}

.result-content {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.initial-state {
  margin-top: 100px;
  text-align: center;
}
</style>
