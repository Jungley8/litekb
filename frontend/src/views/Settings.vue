<template>
  <div class="settings-view">
    <n-tabs type="line" animated>
      <!-- LLM 配置 -->
      <n-tab-pane name="llm" tab="LLM 设置">
        <n-card>
          <n-form :model="llmConfig" label-placement="left" label-width="120">
            <n-form-item label="提供商">
              <n-select
                v-model:value="llmConfig.provider"
                :options="llmProviders"
                placeholder="选择 LLM 提供商"
              />
            </n-form-item>
            
            <n-form-item v-if="llmConfig.provider === 'openai'" label="API Key">
              <n-input
                v-model:value="llmConfig.api_key"
                type="password"
                placeholder="sk-..."
                show-password-on="click"
              />
            </n-form-item>
            
            <n-form-item label="模型">
              <n-select
                v-model:value="llmConfig.model"
                :options="modelOptions"
                placeholder="选择模型"
              />
            </n-form-item>

            <n-form-item label="温度">
              <n-slider
                v-model:value="llmConfig.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                :tooltip="true"
              />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="saveLLMConfig">
                保存设置
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- Embedding 配置 -->
      <n-tab-pane name="embedding" tab="Embedding 设置">
        <n-card>
          <n-form :model="embeddingConfig" label-placement="left" label-width="120">
            <n-form-item label="提供商">
              <n-select
                v-model:value="embeddingConfig.provider"
                :options="embeddingProviders"
                placeholder="选择 Embedding 提供商"
              />
            </n-form-item>
            
            <n-form-item label="模型">
              <n-select
                v-model:value="embeddingConfig.model"
                :options="embeddingModels"
                placeholder="选择模型"
              />
            </n-form-item>

            <n-form-item label="向量维度">
              <n-input-number
                v-model:value="embeddingConfig.dimensions"
                :min="64"
                :max="4096"
                :step="64"
              />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="saveEmbeddingConfig">
                保存设置
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- 系统设置 -->
      <n-tab-pane name="system" tab="系统设置">
        <n-card>
          <n-form label-placement="left" label-width="120">
            <n-form-item label="默认知识库">
              <n-select
                v-model:value="systemConfig.defaultKB"
                :options="kbOptions"
                placeholder="选择默认知识库"
                clearable
              />
            </n-form-item>

            <n-form-item label="语言">
              <n-select
                v-model:value="systemConfig.language"
                :options="[
                  { label: '中文', value: 'zh' },
                  { label: 'English', value: 'en' }
                ]"
              />
            </n-form-item>

            <n-form-item label="主题">
              <n-select
                v-model:value="systemConfig.theme"
                :options="[
                  { label: '浅色', value: 'light' },
                  { label: '深色', value: 'dark' },
                  { label: '跟随系统', value: 'auto' }
                ]"
              />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="saveSystemConfig">
                保存设置
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- 关于 -->
      <n-tab-pane name="about" tab="关于">
        <n-card>
          <n-descriptions :column="1" label-placement="left">
            <n-descriptions-item label="版本">
              <n-tag>v0.1.0</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="技术栈">
              Vue 3 + FastAPI + Qdrant
            </n-descriptions-item>
            <n-descriptions-item label="License">
              MIT
            </n-descriptions-item>
            <n-descriptions-item label="GitHub">
              <n-button text type="primary">
                https://github.com/yourname/litekb
              </n-button>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { configApi } from '../api'

const message = useMessage()

const llmConfig = ref({
  provider: 'openai',
  api_key: '',
  model: 'gpt-3.5-turbo',
  temperature: 0.7
})

const embeddingConfig = ref({
  provider: 'openai',
  model: 'text-embedding-3-small',
  dimensions: 1536
})

const systemConfig = ref({
  defaultKB: null,
  language: 'zh',
  theme: 'light'
})

const kbList = ref<Array<{ id: string; name: string }>>([])
const kbOptions = computed(() =>
  kbList.value.map(kb => ({ label: kb.name, value: kb.id }))
)

const llmProviders = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Ollama (本地)', value: 'ollama' },
  { label: 'DeepSeek', value: 'deepseek' }
]

const modelOptions = [
  { label: 'GPT-3.5-Turbo', value: 'gpt-3.5-turbo' },
  { label: 'GPT-4', value: 'gpt-4' },
  { label: 'GPT-4-Turbo', value: 'gpt-4-turbo' }
]

const embeddingProviders = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'HuggingFace', value: 'huggingface' },
  { label: 'Ollama (本地)', value: 'ollama' }
]

const embeddingModels = [
  { label: 'text-embedding-3-small', value: 'text-embedding-3-small' },
  { label: 'text-embedding-3-large', value: 'text-embedding-3-large' },
  { label: 'all-MiniLM-L6-v2', value: 'all-MiniLM-L6-v2' }
]

async function saveLLMConfig() {
  try {
    await configApi.updateLLMConfig(llmConfig.value)
    message.success('LLM 设置已保存')
  } catch (error) {
    message.error('保存失败')
  }
}

async function saveEmbeddingConfig() {
  try {
    await configApi.updateEmbeddingConfig(embeddingConfig.value)
    message.success('Embedding 设置已保存')
  } catch (error) {
    message.error('保存失败')
  }
}

async function saveSystemConfig() {
  // 保存到本地存储
  localStorage.setItem('litekb_settings', JSON.stringify(systemConfig.value))
  message.success('系统设置已保存')
}

onMounted(() => {
  // 加载知识库列表
  // TODO: 加载 API 配置
  // 加载本地设置
  const saved = localStorage.getItem('litekb_settings')
  if (saved) {
    systemConfig.value = JSON.parse(saved)
  }
})
</script>

<style scoped>
.settings-view {
  max-width: 800px;
}
</style>
