<template>
  <div class="chat-view">
    <n-card class="chat-card" :bordered="false">
      <!-- 头部 -->
      <template #header>
        <div class="chat-header">
          <div class="header-info">
            <n-icon size="24" color="#18a058"><ChatbubblesOutline /></n-icon>
            <span>{{ title }}</span>
          </div>
          <n-space>
            <n-button quaternary circle @click="showSettings = true">
              <template #icon><n-icon><SettingsOutline /></n-icon></template>
            </n-button>
          </n-space>
        </div>
      </template>

      <!-- 消息区域 -->
      <div class="messages-container" ref="containerRef">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <n-empty description="开始与知识库对话吧">
            <template #icon>
              <n-avatar :size="80" round color="#18a058">
                <n-icon size="40"><SparklesOutline /></n-icon>
              </n-avatar>
            </template>
            <template #extra>
              <div class="suggestions">
                <n-button
                  v-for="(q, i) in suggestedQuestions"
                  :key="i"
                  size="small"
                  @click="sendSuggestion(q)"
                >
                  {{ q }}
                </n-button>
              </div>
            </template>
          </n-empty>
        </div>

        <!-- 消息列表 -->
        <template v-else>
          <div
            v-for="(msg, idx) in messages"
            :key="msg.id || idx"
            :class="['message', msg.role]"
          >
            <!-- 用户消息 -->
            <template v-if="msg.role === 'user'">
              <div class="message-avatar">
                <n-avatar round size="small">U</n-avatar>
              </div>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
              </div>
            </template>

            <!-- AI 消息 -->
            <template v-else>
              <div class="message-avatar">
                <n-avatar round size="small" color="#18a058">
                  <n-icon><SparklesOutline /></n-icon>
                </n-avatar>
              </div>
              <div class="message-content">
                <!-- 回答 -->
                <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
                
                <!-- 来源 -->
                <div v-if="msg.sources?.length" class="sources">
                  <n-collapse>
                    <n-collapse-item title="参考来源" name="sources">
                      <n-list>
                        <n-list-item v-for="(s, i) in msg.sources" :key="i">
                          <template #prefix>
                            <n-tag size="small" type="info">{{ i + 1 }}</n-tag>
                          </template>
                          <n-thing :title="s.title">
                            <template #description>
                              <n-progress
                                type="line"
                                :percentage="Math.round(s.score * 100)"
                                :show-indicator="false"
                                :height="4"
                                style="width: 60px"
                              />
                            </template>
                            <n-button
                              text
                              type="primary"
                              size="small"
                              @click="viewSource(s)"
                            >
                              查看原文
                            </n-button>
                          </n-thing>
                        </n-list-item>
                      </n-list>
                    </n-collapse-item>
                  </n-collapse>
                </div>
                
                <!-- 操作 -->
                <div class="message-actions">
                  <n-button-group size="small">
                    <n-button text @click="copyAnswer(msg.content)">
                      <template #icon><n-icon><CopyOutline /></n-icon></template>
                    </n-button>
                    <n-button text @click="regenerate(msg)">
                      <template #icon><n-icon><RefreshOutline /></n-icon></template>
                    </n-button>
                    <n-button text @click="showShare(msg)">
                      <template #icon><n-icon><ShareOutline /></n-icon></template>
                    </n-button>
                  </n-button-group>
                </div>
              </div>
            </template>
          </div>

          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-state">
            <n-spin size="small" />
            <span>正在思考...</span>
          </div>
        </template>
      </div>

      <!-- 输入区域 -->
      <template #footer>
        <div class="input-area">
          <!-- 附件按钮 -->
          <n-popover trigger="click" placement="top-start">
            <template #trigger>
              <n-button quaternary circle>
                <template #icon><n-icon><AttachOutline /></n-icon></template>
              </n-button>
            </template>
            <n-space>
              <n-button @click="selectFile">
                <template #icon><n-icon><DocumentOutline /></n-icon></template>
                文件
              </n-button>
              <n-button @click="selectImage">
                <template #icon><n-icon><ImageOutline /></n-icon></template>
                图片
              </n-button>
            </n-space>
          </n-popover>

          <n-input
            v-model:value="inputMessage"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
            @keydown.enter.exact="sendMessage"
          />

          <n-button
            type="primary"
            :loading="isLoading"
            :disabled="!canSend"
            @click="sendMessage"
          >
            <template #icon><n-icon><SendOutline /></n-icon></template>
          </n-button>
        </div>

        <!-- 快捷提示 -->
        <div class="input-hints">
          <n-tag size="small" :bordered="false">Ctrl+Enter 发送</n-tag>
          <n-tag size="small" :bordered="false">/ 搜索历史</n-tag>
        </div>
      </template>
    </n-card>

    <!-- 设置抽屉 -->
    <n-drawer v-model:show="showSettings" :width="360" placement="right">
      <n-drawer-content title="对话设置">
        <n-form label-placement="left" label-width="80">
          <n-form-item label="模式">
            <n-select
              v-model:value="ragMode"
              :options="[
                { label: '标准 RAG', value: 'naive' },
                { label: '上下文增强', value: 'contextual' },
                { label: '图谱增强', value: 'graph-augmented' }
              ]"
            />
          </n-form-item>
          
          <n-form-item label="温度">
            <n-slider
              v-model:value="temperature"
              :min="0" :max="1" :step="0.1"
              :tooltip="true"
            />
          </n-form-item>
          
          <n-form-item label="上下文">
            <n-switch v-model:value="useHistory" />
            <span style="margin-left: 8px">包含历史</span>
          </n-form-item>
        </n-form>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { marked } from 'marked'
import hljs from 'highlight.js'
import {
  ChatbubblesOutline,
  SparklesOutline,
  SendOutline,
  SettingsOutline,
  CopyOutline,
  RefreshOutline,
  ShareOutline,
  AttachOutline,
  DocumentOutline,
  ImageOutline
} from '@vicons/ionicons5'
import { chatApi } from '../api'

interface Message {
  id?: string
  role: 'user' | 'assistant'
  content: string
  sources?: any[]
}

interface Props {
  kbId: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'RAG 对话'
})

const emit = defineEmits<{
  (e: 'sourceClick', source: any): void
}>()

const message = useMessage()
const containerRef = ref<HTMLElement>()

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const showSettings = ref(false)

// 设置
const ragMode = ref('naive')
const temperature = ref(0.7)
const useHistory = ref(true)

const suggestedQuestions = [
  "这个知识库的主要内容是什么？",
  "有哪些关键概念？",
  "总结核心要点"
]

const canSend = computed(() =>
  !isLoading.value && inputMessage.value.trim()
)

function renderMarkdown(content: string): string {
  return marked(content, {
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value
      }
      return hljs.highlightAuto(code).value
    }
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
}

async function sendMessage() {
  if (!canSend.value) return

  const userMsg: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value.trim()
  }

  messages.value.push(userMsg)
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const history = useHistory.value ? messages.value.slice(-7) : []
    const response = await chatApi.chat(props.kbId, userMsg.content, history)

    const assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.answer,
      sources: response.sources
    }

    messages.value.push(assistantMsg)
  } catch (error) {
    message.error('获取回答失败')
    console.error(error)
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

function sendSuggestion(question: string) {
  inputMessage.value = question
  sendMessage()
}

function copyAnswer(content: string) {
  navigator.clipboard.writeText(content)
  message.success('已复制')
}

function regenerate(msg: Message) {
  message.info('重新生成功能开发中')
}

function showShare(msg: Message) {
  message.info('分享功能开发中')
}

function viewSource(source: any) {
  emit('sourceClick', source)
}

function selectFile() {
  message.info('文件上传功能开发中')
}

function selectImage() {
  message.info('图片上传功能开发中')
}
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 112px);
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.welcome-message {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.suggestions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
}

.message.user {
  background: #f0f0f0;
  flex-direction: row-reverse;
}

.message.assistant {
  background: #e8f5e9;
}

.message-content {
  max-width: 70%;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.sources {
  margin-top: 12px;
}

.message-actions {
  margin-top: 8px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.message:hover .message-actions {
  opacity: 1;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #999;
  padding: 8px;
}

.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area .n-input {
  flex: 1;
}

.input-hints {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style>
