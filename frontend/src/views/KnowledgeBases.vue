<template>
  <div class="knowledge-bases">
    <div class="header">
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        新建知识库
      </n-button>
    </div>

    <n-spin :show="loading">
      <!-- 知识库列表 -->
      <n-grid :cols="xs ? 1 : 3" :x-gap="16" :y-gap="16" class="kb-grid">
        <n-gi v-for="kb in kbList" :key="kb.id">
          <n-card hoverable class="kb-card" @click="goToKB(kb.id)">
            <template #header>
              <div class="kb-header">
                <n-icon size="24" color="#18a058"><FolderOutline /></n-icon>
                <span class="kb-name">{{ kb.name }}</span>
              </div>
            </template>

            <div class="kb-info">
              <n-space vertical>
                <span class="kb-stat">
                  <n-icon><DocumentTextOutline /></n-icon>
                  {{ kb.doc_count }} 篇文档
                </span>
                <span class="kb-stat">
                  <n-icon><TimeOutline /></n-icon>
                  {{ formatDate(kb.created_at) }}
                </span>
              </n-space>
            </div>

            <template #footer>
              <n-space justify="end">
                <n-button size="small" quaternary @click.stop="editKB(kb)">
                  <template #icon><n-icon><SettingsOutline /></n-icon></template>
                  设置
                </n-button>
                <n-button size="small" type="primary" quaternary @click.stop="goToKB(kb.id)">
                  打开
                </n-button>
              </n-space>
            </template>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 空状态 -->
      <n-empty v-if="kbList.length === 0" description="还没有知识库，点击新建一个吧">
        <template #extra>
          <n-button type="primary" @click="showCreateModal = true">
            创建知识库
          </n-button>
        </template>
      </n-empty>
    </n-spin>

    <!-- 新建弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="新建知识库">
      <n-form ref="formRef" :model="newKB" :rules="rules">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="newKB.name" placeholder="输入知识库名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="newKB.description"
            type="textarea"
            placeholder="简单描述这个知识库的内容"
            :rows="3"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" @click="createKB" :loading="creating">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  AddOutline,
  FolderOutline,
  DocumentTextOutline,
  TimeOutline,
  SettingsOutline
} from '@vicons/ionicons5'
import { kbApi } from '../api'

interface KnowledgeBase {
  id: string
  name: string
  description?: string
  doc_count: number
  created_at: string
}

const router = useRouter()
const message = useMessage()

const xs = ref(window.innerWidth < 768)
const loading = ref(false)
const creating = ref(false)
const showCreateModal = ref(false)

const kbList = ref<KnowledgeBase[]>([])
const newKB = ref({ name: '', description: '' })

const rules = {
  name: { required: true, message: '请输入知识库名称', trigger: 'blur' }
}

const kbApiClient = {
  list: () => kbApi.list?.() || Promise.resolve([]) as Promise<KnowledgeBase[]>,
  create: (data: any) => kbApi.create?.(data) as Promise<KnowledgeBase>,
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function goToKB(id: string) {
  router.push({ name: 'kbDetail', params: { id } })
}

function editKB(kb: KnowledgeBase) {
  message.info('设置功能开发中')
}

async function loadKBs() {
  loading.value = true
  try {
    kbList.value = await kbApiClient.list()
  } catch (error) {
    console.error('加载知识库失败:', error)
    // 使用模拟数据
    kbList.value = [
      {
        id: '1',
        name: 'AI 学习笔记',
        description: '收集的 AI 和机器学习相关笔记',
        doc_count: 12,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        id: '2',
        name: '项目文档',
        description: 'LiteKB 开发文档',
        doc_count: 8,
        created_at: '2024-01-20T14:30:00Z'
      },
      {
        id: '3',
        name: '技术文章收藏',
        description: '各类技术文章和教程',
        doc_count: 25,
        created_at: '2024-02-01T09:00:00Z'
      },
    ]
  } finally {
    loading.value = false
  }
}

async function createKB() {
  if (!newKB.value.name.trim()) {
    message.error('请输入知识库名称')
    return
  }

  creating.value = true
  try {
    const kb = await kbApiClient.create({ name: newKB.value.name })
    kbList.value.unshift(kb)
    message.success('创建成功')
    showCreateModal.value = false
    newKB.value = { name: '', description: '' }
  } catch (error) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadKBs()
  window.addEventListener('resize', () => {
    xs.value = window.innerWidth < 768
  })
})
</script>

<style scoped>
.header {
  margin-bottom: 16px;
}

.kb-card {
  cursor: pointer;
  transition: all 0.3s;
}

.kb-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.kb-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-name {
  font-weight: 600;
  font-size: 16px;
}

.kb-info {
  color: #666;
  font-size: 14px;
}

.kb-stat {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
