<template>
  <div class="export-dialog">
    <n-button @click="showModal = true">
      <template #icon><n-icon><DownloadOutline /></n-icon></template>
      导出
    </n-button>

    <n-modal v-model:show="showModal" preset="dialog" title="导出知识库" style="width: 500px">
      <!-- 导出格式 -->
      <n-form-item label="导出格式">
        <n-radio-group v-model:value="selectedFormat">
          <n-space>
            <n-radio v-for="fmt in formats" :key="fmt.id" :value="fmt.id">
              {{ fmt.icon }} {{ fmt.name }}
            </n-radio>
          </n-space>
        </n-radio-group>
      </n-form-item>

      <!-- 导出选项 -->
      <n-form-item label="选项">
        <n-checkbox v-model:checked="includeDocuments">包含文档内容</n-checkbox>
      </n-form-item>

      <n-form-item label="选项">
        <n-checkbox v-model:checked="includeConversations">包含对话历史</n-checkbox>
      </n-form-item>

      <!-- 预览 -->
      <n-divider v-if="preview">预览</n-divider>
      <n-input
        v-if="preview"
        type="textarea"
        :value="preview"
        :rows="6"
        readonly
        placeholder="点击「生成预览」查看..."
      />

      <template #action>
        <n-button @click="generatePreview" :loading="previewing">
          生成预览
        </n-button>
        <n-space>
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleExport" :loading="exporting">
            <template #icon><n-icon><DownloadOutline /></n-icon></template>
            下载文件
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { DownloadOutline } from '@vicons/ionicons5'
import { kbApi } from '../api'

const props = defineProps<{
  kbId: string
  kbName: string
}>()

const emit = defineEmits<{
  (e: 'exported', filename: string): void
}>()

const message = useMessage()

const showModal = ref(false)
const selectedFormat = ref('markdown')
const includeDocuments = ref(true)
const includeConversations = ref(false)
const preview = ref('')
const previewing = ref(false)
const exporting = ref(false)

const formats = [
  { id: 'markdown', name: 'Markdown', icon: '📝' },
  { id: 'json', name: 'JSON', icon: '📋' },
  { id: 'html', name: 'HTML', icon: '🌐' },
  { id: 'csv', name: 'CSV', icon: '📊' }
]

async function generatePreview() {
  previewing.value = true
  try {
    const response = await kbApi.export(props.kbId, {
      format: selectedFormat.value,
      include_documents: includeDocuments.value,
      include_conversations: includeConversations.value,
      preview: true
    })
    preview.value = response.content.substring(0, 1000)
  } catch (error) {
    message.error('生成预览失败')
  } finally {
    previewing.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await kbApi.export(props.kbId, {
      format: selectedFormat.value,
      include_documents: includeDocuments.value,
      include_conversations: includeConversations.value
    })
    
    // 下载文件
    const blob = new Blob([response.content], { type: response.content_type })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = response.filename
    link.click()
    URL.revokeObjectURL(url)
    
    message.success(`已导出: ${response.filename}`)
    showModal.value = false
    emit('exported', response.filename)
  } catch (error) {
    message.error('导出失败')
  } finally {
    exporting.value = false
  }
}

watch(showModal, (val) => {
  if (!val) {
    preview.value = ''
  }
})
</script>

<style scoped>
.export-dialog {
  display: inline-block;
}
</style>
