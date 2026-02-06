<template>
  <div class="import-dialog">
    <n-button @click="showModal = true">
      <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
      批量导入
    </n-button>

    <n-modal v-model:show="showModal" preset="dialog" title="批量导入文档" style="width: 600px">
      <!-- 步骤指示器 -->
      <n-steps :current="currentStep" style="margin-bottom: 24px">
        <n-step title="选择来源" />
        <n-step title="配置选项" />
        <n-step title="导入预览" />
        <n-step title="完成" />
      </n-steps>

      <!-- 步骤 1: 选择来源 -->
      <div v-if="currentStep === 1">
        <n-radio-group v-model:value="source" class="source-options">
          <n-space vertical>
            <n-radio value="upload">
              <div class="source-item">
                <n-icon size="32"><DocumentOutline /></n-icon>
                <div>
                  <div class="source-title">上传文件</div>
                  <div class="source-desc">支持 TXT, MD, DOCX, PDF</div>
                </div>
              </div>
            </n-radio>
            
            <n-radio value="url">
              <div class="source-item">
                <n-icon size="32"><LinkOutline /></n-icon>
                <div>
                  <div class="source-title">从 URL 导入</div>
                  <div class="source-desc">输入网页 URL 自动抓取</div>
                </div>
              </div>
            </n-radio>
            
            <n-radio value="notion">
              <div class="source-item">
                <n-icon size="32"><LogoNotion /></n-icon>
                <div>
                  <div class="source-title">Notion 页面</div>
                  <div class="source-desc">连接 Notion 同步页面</div>
                </div>
              </div>
            </n-radio>
            
            <n-radio value="webhook">
              <div class="source-item">
                <n-icon size="32"><WebhookOutline /></n-icon>
                <div>
                  <div class="source-title">Webhook</div>
                  <div class="source-desc">通过 Webhook 推送内容</div>
                </div>
              </div>
            </n-radio>
          </n-space>
        </n-radio-group>
      </div>

      <!-- 步骤 2: 配置选项 -->
      <div v-if="currentStep === 2">
        <!-- 上传模式 -->
        <template v-if="source === 'upload'">
          <n-upload
            multiple
            draggable
            accept=".txt,.md,.docx,.pdf"
            :custom-request="handleUpload"
            @change="handleFileChange"
            @remove="handleFileRemove"
          >
            <n-upload-dragger>
              <n-icon size="48" :depth="3"><CloudUploadOutline /></n-icon>
              <n-text style="font-size: 16px">拖拽文件到此处</n-text>
              <n-p depth="3">或点击选择文件 (最多 20 个)</n-p>
            </n-upload-dragger>
          </n-upload>
          
          <div class="file-list" v-if="files.length > 0">
            <n-list>
              <n-list-item v-for="file in files" :key="file.id">
                <n-thing :title="file.name">
                  <template #header-extra>
                    <n-tag size="small">{{ formatSize(file.size) }}</n-tag>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </div>
        </template>
        
        <!-- URL 模式 -->
        <template v-if="source === 'url'">
          <n-form-item label="URL 列表">
            <n-dynamic-input
              v-model:value="urls"
              :min="1"
              placeholder="https://example.com/article"
            >
              <template #create-button-default>
                添加 URL
              </template>
            </n-dynamic-input>
          </n-form-item>
          
          <n-checkbox v-model:checked="extractImages">提取图片为附件</n-checkbox>
          <n-checkbox v-model:checked="cleanHtml">清理 HTML 标签</n-checkbox>
        </template>
        
        <!-- Notion 模式 -->
        <template v-if="source === 'notion'">
          <n-alert type="info" style="margin-bottom: 16px">
            请在设置页面连接 Notion 账号
          </n-alert>
          <n-button @click="$router.push('/settings/integrations')">
            前往设置
          </n-button>
        </template>
      </div>

      <!-- 步骤 3: 导入预览 -->
      <div v-if="currentStep === 3">
        <n-spin :show="importing">
          <n-progress
            type="line"
            :percentage="importProgress"
            :indicator-placement="'inside'"
          >
            正在导入 {{ importedCount }}/{{ totalCount }} 个文件
          </n-progress>
          
          <n-list style="margin-top: 16px; max-height: 200px; overflow-y: auto">
            <n-list-item v-for="item in importResults" :key="item.id">
              <n-thing :title="item.title">
                <template #prefix>
                  <n-icon :color="item.success ? '#18a058' : '#d03050'">
                    <CheckmarkCircleOutline v-if="item.success" />
                    <CloseCircleOutline v-else />
                  </n-icon>
                </template>
                <template #header-extra>
                  <n-tag :type="item.success ? 'success' : 'error'" size="small">
                    {{ item.status }}
                  </n-tag>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-spin>
      </div>

      <!-- 步骤 4: 完成 -->
      <div v-if="currentStep === 4">
        <n-result
          status="success"
          title="导入完成"
          :description="`成功导入 ${successCount} 个文档`"
        >
          <template #footer>
            <n-space justify="center">
              <n-button @click="reset">继续导入</n-button>
              <n-button type="primary" @click="$router.push(`/kb/${kbId}`)">
                查看知识库
              </n-button>
            </n-space>
          </template>
        </n-result>
      </div>

      <!-- 导航按钮 -->
      <template #action v-if="currentStep < 4">
        <n-space justify="space-between">
          <n-button v-if="currentStep > 1" @click="currentStep--">
            上一步
          </n-button>
          <n-space flex :justify="'end'">
            <n-button @click="showModal = false">取消</n-button>
            <n-button
              v-if="currentStep < 3"
              type="primary"
              @click="nextStep"
              :disabled="!canProceed"
            >
              下一步
            </n-button>
            <n-button
              v-if="currentStep === 3"
              type="primary"
              @click="startImport"
              :loading="importing"
            >
              开始导入
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  CloudUploadOutline,
  DocumentOutline,
  LinkOutline,
  LogoNoticon,
  WebhookOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import { docApi } from '../api'

const props = defineProps<{
  kbId: string
}>()

const emit = defineEmits<{
  (e: 'imported', count: number): void
}>()

const message = useMessage()

const showModal = ref(false)
const currentStep = ref(1)
const source = ref('upload')

// 上传相关
const files = ref<any[]>([])
const fileContents = ref<Map<string, File>>(new Map())

// URL 相关
const urls = ref([''])
const extractImages = ref(true)
const cleanHtml = ref(true)

// 导入相关
const importing = ref(false)
const importProgress = ref(0)
const importedCount = ref(0)
const totalCount = ref(0)
const importResults = ref<any[]>([])
const successCount = ref(0)

const formats = [
  { id: 'markdown', name: 'Markdown', icon: '📝' },
  { id: 'json', name: 'JSON', icon: '📋' },
  { id: 'html', name: 'HTML', icon: '🌐' },
  { id: 'csv', name: 'CSV', icon: '📊' }
]

const canProceed = computed(() => {
  if (currentStep.value === 1) return true
  if (currentStep.value === 2) {
    if (source.value === 'upload') return files.value.length > 0
    if (source.value === 'url') return urls.value.some(u => u.trim())
  }
  return true
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleFileChange(options: { fileList: any[] }) {
  files.value = options.fileList
}

function handleFileRemove(options: { file: any }) {
  const index = files.value.findIndex(f => f.id === options.file.id)
  if (index > -1) {
    files.value.splice(index, 1)
    fileContents.value.delete(options.file.name)
  }
}

function handleUpload(options: { file: any }) {
  fileContents.value.set(options.file.name, options.file.file)
}

async function nextStep() {
  currentStep.value++
}

async function startImport() {
  importing.value = true
  importResults.value = []
  successCount.value = 0
  
  if (source.value === 'upload') {
    totalCount.value = files.value.length
    importedCount.value = 0
    
    for (const file of files.value) {
      try {
        const content = fileContents.value.get(file.name)
        const result = await docApi.upload(props.kbId, content || file.file)
        
        importResults.value.push({
          id: result.id,
          title: file.name,
          success: true,
          status: '成功'
        })
        successCount.value++
      } catch (error) {
        importResults.value.push({
          id: file.id,
          title: file.name,
          success: false,
          status: '失败'
        })
      }
      
      importedCount.value++
      importProgress.value = Math.round((importedCount.value / totalCount.value) * 100)
    }
  }
  
  importing.value = false
  currentStep.value = 4
  emit('imported', successCount.value)
}

function reset() {
  currentStep.value = 1
  files.value = []
  fileContents.value.clear()
  urls.value = ['']
  importResults.value = []
  importProgress.value = 0
}

watch(showModal, (val) => {
  if (!val) {
    reset()
  }
})
</script>

<style scoped>
.source-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.source-item:hover {
  background: #f5f5f5;
}

.source-title {
  font-weight: 600;
}

.source-desc {
  font-size: 12px;
  color: #666;
}

.file-list {
  margin-top: 16px;
}

.import-dialog :deep(.n-upload-dragger) {
  padding: 32px;
}
</style>
