<template>
  <div class="chat-view">
    <n-card class="chat-card" :bordered="false">
      <!-- 聊天头部 -->
      <template #header>
        <div class="chat-header">
          <div class="header-info">
            <n-icon size="24" color="#18a058"><ChatbubblesOutline /></n-icon>
            <span>RAG 对话</span>
          </div>
          <n-select
            v-model:value="selectedKB"
            placeholder="选择知识库"
            :options="kbOptions"
            style="width: 200px"
            clearable
          />
        </div>
      </template>

      <!-- 聊天消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <n-empty description="开始与知识库对话吧">
            <template #extra>
              <p class="hint">选择或创建一个知识库，然后开始提问</p>
            </template>
          </n-empty>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message', msg.role]"
        >
          <div class="message-avatar">
            <n-avatar v-if="msg.role === 'user'" round size="small">
              U
            </n-avatar>
            <n-avatar v-else round size="small" color="#18a058">
              <template #icon>
                <n-icon><SparklesOutline /></n-icon>
              </template>
            </n-avatar>
          </div>
          
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            
            <!-- 来源引用 -->
            <div v-if="msg.sources && msg.sources.length > 0" class="sources">
              <n-collapse>
                <n-collapse-item title="参考来源" name="sources">
                  <n-ol>
                    <li v-for="source in msg.sources" :key="source.doc_id">
                      <n-button text type="primary" @click="viewSource(source)">
                        {{ source.title }}
                      </n-button>
                      <p class="source-chunk">{{ source.chunk }}</p>
                    </li>
                  </n-ol>
                </n-collapse-item>
              </n-collapse>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-state">
          <n-spin size="small" />
          <span>正在思考...</span>
        </div>
      </div>

      <!-- 输入区域 -->
      <template #footer>
        <div class="input-area">
          <n-input
            v-model:value="inputMessage"
            type="textarea"
            placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
            :autosize="{ minRows: 1, maxRows: 4 }"
            @keydown.enter.exact="sendMessage"
          />
          <div class="input-actions">
            <n-button
              type="primary"
              :loading="isLoading"
              :disabled="!canSend"
              @click="sendMessage"
            >
              <template #icon><n-icon><SendOutline /></n-icon></template>
              发送
            </n-button>
          </div>
        </div>
      </template>
    </n-card>
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
  SendOutline
} from '@vicons/ionicons5'
import { chatApi, kbApi } from '../api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    doc_id: string
    title: string
    chunk: string
  }>
}

interface KBOption {
  label: string
  value: string
}

const message = useMessage()
const messagesContainer = ref<HTMLElement>()

const messages = ref<Message[]>([])
const inputMessage = ref('')
const selectedKB = ref<string | null>(null)
const isLoading = ref(false)
const kbList = ref<Array<{ id: string; name: string }>>([])

const kbOptions = computed(() =>
  kbList.value.map(kb => ({
    label: kb.name,
    value: kb.id
  }))
)

const canSend = computed(() =>
  !isLoading.value && inputMessage.value.trim() && selectedKB.value
)

function formatMessage(content: string): string {
  // Markdown 渲染
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
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
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
    const response = await chatApi.chat(
      selectedKB.value!,
      userMsg.content,
      messages.value
        .filter(m => m.role === 'user' || (m.role === 'assistant' && !m.sources))
        .map(m => ({ role: m.role, content: m.content }))
    )

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

function viewSource(source: { doc_id: string; title: string }) {
  message.info(`查看文档: ${source.title}`)
}

// 加载知识库列表
async function loadKBs() {
  try {
    kbList.value = await kbApi.list()
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
}

loadKBs()
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

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hint {
  color: #999;
  font-size: 14px;
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
}

.message.assistant {
  background: #e8f5e9;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  overflow: hidden;
}

.message-text {
  line-height: 1.6;
}

.sources {
  margin-top: 12px;
  font-size: 13px;
}

.source-chunk {
  color: #666;
  margin: 4px 0 0 0;
  padding: 8px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 4px;
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

.input-actions {
  flex-shrink: 0;
}
</style>
