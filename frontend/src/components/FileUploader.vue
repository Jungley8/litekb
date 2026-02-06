<template>
  <div class="upload-area">
    <n-upload
      :custom-request="handleUpload"
      :max="10"
      multiple
      draggable
      accept=".txt,.md,.docx,.pdf"
      @change="handleChange"
      @remove="handleRemove"
    >
      <n-upload-dragger>
        <div class="upload-content">
          <n-icon size="48" :depth="3">
            <CloudUploadOutline />
          </n-icon>
          <n-text style="font-size: 16px">
            点击或拖拽文件到此处上传
          </n-text>
          <n-p depth="3" style="margin: 8px 0 0 0">
            支持 TXT, Markdown, DOCX, PDF 格式
          </n-p>
          <n-p depth="3" style="margin: 4px 0 0 0">
            单文件最大 10MB
          </n-p>
        </div>
      </n-upload-dragger>
    </n-upload>

    <!-- 上传进度 -->
    <div v-if="uploadingFiles.length > 0" class="upload-progress">
      <n-hr />
      <n-text strong>上传中</n-text>
      <n-list>
        <n-list-item v-for="file in uploadingFiles" :key="file.id">
          <n-thing>
            <template #header>
              {{ file.name }}
            </template>
            <template #header-extra>
              <n-progress
                type="line"
                :percentage="file.percentage || 0"
                :status="file.status"
              />
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </div>

    <!-- 上传完成 -->
    <div v-if="completedFiles.length > 0" class="completed-files">
      <n-hr />
      <n-text strong>上传完成</n-text>
      <n-list>
        <n-list-item v-for="file in completedFiles" :key="file.id">
          <n-thing>
            <template #header>
              {{ file.name }}
            </template>
            <template #header-extra>
              <n-tag type="success" size="small">
                {{ file.status }}
              </n-tag>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { CloudUploadOutline } from '@vicons/ionicons5'
import { docApi } from '../api'

interface UploadFile {
  id: string
  name: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  percentage?: number
  error?: string
}

const props = defineProps<{
  kbId: string
}>()

const emit = defineEmits<{
  (e: 'uploaded', files: any[]): void
}>()

const message = useMessage()
const fileList = ref<any[]>([])
const uploadingFiles = computed(() => 
  fileList.value.filter(f => f.status === 'uploading')
)
const completedFiles = computed(() =>
  fileList.value.filter(f => f.status === 'success')
)

function handleChange(options: { fileList: any[] }) {
  fileList.value = options.fileList.map(f => ({
    ...f,
    id: f.id || Date.now().toString(),
    status: f.status === 'pending' ? 'pending' : 'pending',
    name: f.name
  }))
}

function handleRemove(options: { file: any }) {
  const index = fileList.value.findIndex(f => f.id === options.file.id)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

async function handleUpload(options: { file: any }) {
  const file = options.file
  
  const index = fileList.value.findIndex(f => f.id === file.id)
  if (index === -1) return
  
  fileList.value[index].status = 'uploading'
  
  try {
    const result = await docApi.upload(props.kbId, file.file, (progress) => {
      fileList.value[index].percentage = progress
    })
    
    fileList.value[index].status = 'success'
    fileList.value[index].percentage = 100
    
    message.success(`${file.name} 上传成功`)
    
    emit('uploaded', [result])
    
  } catch (error: any) {
    fileList.value[index].status = 'error'
    fileList.value[index].error = error.message || '上传失败'
    message.error(`${file.name} 上传失败: ${error.message}`)
  }
}
</script>

<style scoped>
.upload-area {
  padding: 16px 0;
}

.upload-content {
  padding: 20px;
  text-align: center;
}

.upload-progress,
.completed-files {
  margin-top: 16px;
}
</style>
