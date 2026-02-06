<template>
  <div class="kb-detail">
    <n-spin :show="loading">
      <!-- 头部 -->
      <div class="kb-header">
        <div class="header-info">
          <n-button quaternary circle @click="$router.back()">
            <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
          </n-button>
          <div class="kb-title">
            <h2>{{ kb?.name }}</h2>
            <p>{{ kb?.description }}</p>
          </div>
        </div>
        <n-space>
          <n-button type="primary" @click="showUploadModal = true">
            <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
            上传文档
          </n-button>
          <n-dropdown :options="moreOptions" @select="handleMore">
            <n-button>
              <template #icon><n-icon><MoreOutline /></n-icon></template>
              更多
            </n-button>
          </n-dropdown>
        </n-space>
      </div>

      <!-- Tab 切换 -->
      <n-tabs type="line" animated v-model:value="activeTab">
        <n-tab-pane name="docs" tab="文档">
          <div class="docs-content">
            <!-- 文档列表 -->
            <n-empty v-if="documents.length === 0" description="还没有文档">
              <template #extra>
                <n-button type="primary" @click="showUploadModal = true">
                  上传第一个文档
                </n-button>
              </template>
            </n-empty>

            <n-list v-else hoverable>
              <n-list-item v-for="doc in documents" :key="doc.id">
                <n-thing>
                  <template #header>
                    <n-button text type="primary">{{ doc.title }}</n-button>
                  </template>
                  <template #header-extra>
                    <n-tag :type="doc.status === 'indexed' ? 'success' : 'warning'" size="small">
                      {{ doc.status }}
                    </n-tag>
                  </template>
                  <template #description>
                    {{ formatDate(doc.created_at) }}
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>
        </n-tab-pane>

        <n-tab-pane name="chat" tab="RAG 对话">
          <!-- 复用 Chat 组件 -->
          <Chat :kb-id="kbId" />
        </n-tab-pane>

        <n-tab-pane name="graph" tab="知识图谱">
          <Graph :kb-id="kbId" />
        </n-tab-pane>

        <n-tab-pane name="settings" tab="设置">
          <n-card>
            <n-form label-placement="left" label-width="120">
              <n-form-item label="知识库名称">
                <n-input v-model:value="editForm.name" />
              </n-form-item>
              <n-form-item label="描述">
                <n-input v-model:value="editForm.description" type="textarea" :rows="3" />
              </n-form-item>
              <n-form-item>
                <n-button type="primary" @click="saveSettings">保存</n-button>
              </n-form-item>
            </n-form>
          </n-card>
        </n-tab-pane>
      </n-tabs>
    </n-spin>

    <!-- 上传弹窗 -->
    <n-modal v-model:show="showUploadModal" preset="dialog" title="上传文档" style="width: 500px">
      <n-upload
        :custom-request="handleUpload"
        :max="5"
        multiple
        accept=".txt,.md,.docx,.pdf"
        @change="handleUploadChange"
      >
        <n-upload-dragger>
          <div style="margin-bottom: 12px">
            <n-icon size="48" :depth="3"><CloudUploadOutline /></n-icon>
          </div>
          <n-text style="font-size: 16px">点击或拖拽文件到此处上传</n-text>
          <n-p depth="3" style="margin: 8px 0 0 0">
            支持 TXT, Markdown, DOCX, PDF 格式
          </n-p>
        </n-upload-dragger>
      </n-upload>
      <template #action>
        <n-button @click="showUploadModal = false">关闭</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  ArrowBackOutline,
  CloudUploadOutline,
  MoreOutline
} from '@vicons/ionicons5'
import { kbApi, docApi } from '../api'
import Chat from './Chat.vue'
import Graph from './Graph.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const kbId = route.params.id as string
const loading = ref(false)
const activeTab = ref('docs')

const kb = ref<any>(null)
const documents = ref<any[]>([])
const showUploadModal = ref(false)
const uploadFiles = ref<any[]>([])

const editForm = ref({
  name: '',
  description: ''
})

const moreOptions = [
  { label: '导出知识库', key: 'export' },
  { label: '重建索引', key: 'reindex' },
  { label: '删除知识库', key: 'delete' }
]

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function handleMore(key: string) {
  if (key === 'delete') {
    message.warning('删除功能开发中')
  } else if (key === 'reindex') {
    message.info('重建索引中...')
  } else if (key === 'export') {
    message.info('导出功能开发中')
  }
}

function handleUploadChange(options: any) {
  uploadFiles.value = options.fileList
}

async function handleUpload() {
  if (uploadFiles.value.length === 0) {
    message.warning('请选择文件')
    return
  }

  for (const file of uploadFiles.value) {
    try {
      await docApi.upload(kbId, file.file, (p) => {
        // 进度
      })
      message.success(`${file.name} 上传成功`)
    } catch (error) {
      message.error(`${file.name} 上传失败`)
    }
  }

  showUploadModal.value = false
  uploadFiles.value = []
  loadDocuments()
}

async function saveSettings() {
  try {
    await kbApi.update(kbId, editForm.value)
    message.success('设置已保存')
    kb.value.name = editForm.value.name
    kb.value.description = editForm.value.description
  } catch (error) {
    message.error('保存失败')
  }
}

async function loadKB() {
  loading.value = true
  try {
    kb.value = await kbApi.get(kbId)
    editForm.value = {
      name: kb.value.name,
      description: kb.value.description || ''
    }
  } catch (error) {
    message.error('加载失败')
    router.back()
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  try {
    documents.value = await docApi.list(kbId)
  } catch (error) {
    console.error('加载文档失败:', error)
  }
}

onMounted(() => {
  loadKB()
  loadDocuments()
})
</script>

<style scoped>
.kb-detail {
  height: calc(100vh - 112px);
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.kb-title h2 {
  margin: 0;
  font-size: 20px;
}

.kb-title p {
  margin: 4px 0 0 0;
  color: #666;
  font-size: 14px;
}

.docs-content {
  min-height: 300px;
}
</style>
