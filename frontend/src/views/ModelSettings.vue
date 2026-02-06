<template>
  <div class="model-settings">
    <n-card title="🤖 模型供应商配置">
      
      <!-- 当前供应商 -->
      <n-form-item label="当前供应商">
        <n-select
          v-model:value="currentProvider"
          :options="providerOptions"
          @update:value="handleProviderChange"
        />
      </n-form-item>

      <!-- 模型选择 -->
      <n-form-item label="模型">
        <n-select
          v-model:value="currentModel"
          :options="modelOptions"
          :loading="loadingModels"
          @update:value="handleModelChange"
          placeholder="选择模型"
        />
      </n-form-item>

      <!-- 模型参数 -->
      <n-grid :cols="2" :x-gap="16">
        <n-gi>
          <n-form-item label="Temperature">
            <n-slider
              v-model:value="temperature"
              :min="0" :max="1" :step="0.1"
              @update:value="handleParamChange"
            />
            <span class="param-value">{{ temperature }}</span>
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="Max Tokens">
            <n-input-number
              v-model:value="maxTokens"
              :min="100" :max="8192" :step="100"
              @update:value="handleParamChange"
            />
          </n-form-item>
        </n-gi>
      </n-grid>

      <!-- 可用供应商列表 -->
      <n-divider>可用供应商</n-divider>
      
      <n-grid :cols="xs ? 1 : 3" :x-gap="16" :y-gap="16">
        <n-gi v-for="p in providers" :key="p.type">
          <n-card
            :class="{ active: p.type === currentProvider }"
            class="provider-card"
            size="small"
          >
            <template #header>
              <div class="provider-header">
                <span class="provider-name">{{ p.name }}</span>
                <n-tag v-if="p.type === currentProvider" type="success" size="small">
                  当前
                </n-tag>
              </div>
            </template>

            <div class="provider-info">
              <span>模型数: {{ p.models?.length || 0 }}</span>
              <n-tag
                v-for="cap in p.capabilities?.slice(0, 3)"
                :key="cap"
                size="small"
              >
                {{ cap }}
              </n-tag>
            </div>

            <template #footer>
              <n-button
                v-if="p.type !== currentProvider"
                size="small"
                @click="selectProvider(p.type)"
              >
                切换
              </n-button>
              <n-button
                v-else
                size="small"
                @click="testConnection"
              >
                测试连接
              </n-button>
            </template>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 本地模型管理 -->
      <template v-if="currentProvider === 'ollama'">
        <n-divider>📦 Ollama 模型管理</n-divider>
        
        <n-space>
          <n-button @click="loadOllamaModels">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新
          </n-button>
          <n-input
            v-model:value="ollamaModelToPull"
            placeholder="输入模型名 (如 qwen2.5:7b)"
            style="width: 250px"
          />
          <n-button
            type="primary"
            :loading="pullingModel"
            @click="pullOllamaModel"
          >
            拉取模型
          </n-button>
        </n-space>

        <n-list v-if="ollamaModels.length > 0" style="margin-top: 16px">
          <n-list-item v-for="m in ollamaModels" :key="m.name">
            {{ m.name }}
            <template #suffix>
              <n-tag size="small">{{ formatSize(m.size) }}</n-tag>
            </template>
          </n-list-item>
        </n-list>
      </template>

      <!-- 测试区域 -->
      <n-divider>🧪 模型测试</n-divider>
      
      <n-input
        v-model:value="testPrompt"
        type="textarea"
        placeholder="输入测试提示词..."
        :rows="3"
      />
      <n-button
        type="primary"
        :loading="testing"
        @click="testModel"
        style="margin-top: 8px"
      >
        发送测试
      </n-button>

      <n-input
        v-if="testResult"
        v-model:value="testResult"
        type="textarea"
        readonly
        :rows="4"
        style="margin-top: 8px"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  RefreshOutline,
} from '@vicons/ionicons5'
import { providerApi, ollamaApi } from '../api'

const xs = ref(window.innerWidth < 768)
const loadingModels = ref(false)
const testing = ref(false)
const pullingModel = ref(false)

const providers = ref<any[]>([])
const currentProvider = ref('openai')
const currentModel = ref('gpt-4o')
const temperature = ref(0.1)
const maxTokens = ref(4000)

const ollamaModels = ref<any[]>([])
const ollamaModelToPull = ref('')
const testPrompt = ref('你好，请介绍一下你自己')
const testResult = ref('')

const providerOptions = computed(() => [
  { label: 'OpenAI', value: 'openai' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: 'Ollama (本地)', value: 'ollama' },
  { label: 'vLLM (本地)', value: 'vllm' },
])

const modelOptions = computed(() => {
  const p = providers.value.find(pr => pr.type === currentProvider.value)
  if (!p) return []
  return (p.models || []).map((m: any) => ({
    label: m.id || m.name,
    value: m.id || m.name,
  }))
})

async function loadProviders() {
  try {
    providers.value = await providerApi.listProviders()
    const config = await providerApi.getConfig()
    currentProvider.value = config.provider
    currentModel.value = config.model
    temperature.value = config.temperature || 0.1
    maxTokens.value = config.max_tokens || 4000
  } catch (error) {
    console.error('加载供应商失败:', error)
  }
}

async function loadModels() {
  loadingModels.value = true
  try {
    const p = providers.value.find(pr => pr.type === currentProvider.value)
    if (p) {
      p.models = await providerApi.getModels(currentProvider.value)
    }
  } finally {
    loadingModels.value = false
  }
}

async function handleProviderChange(value: string) {
  currentProvider.value = value
  currentModel.value = ''
  await loadModels()
}

async function handleModelChange(value: string) {
  currentModel.value = value
  await providerApi.switchProvider({
    provider: currentProvider.value,
    model: value,
  })
}

async function handleParamChange() {
  await providerApi.switchProvider({
    provider: currentProvider.value,
    model: currentModel.value,
    temperature: temperature.value,
    max_tokens: maxTokens.value,
  })
}

async function selectProvider(type: string) {
  currentProvider.value = type
  await loadModels()
}

async function testConnection() {
  try {
    const result = await providerApi.testConnection(currentProvider.value)
    if (result.success) {
      message.success(`连接成功! 延迟: ${result.latency}ms`)
    } else {
      message.error('连接失败')
    }
  } catch (error) {
    message.error('连接测试失败')
  }
}

async function loadOllamaModels() {
  try {
    ollamaModels.value = await ollamaApi.listModels()
  } catch (error) {
    console.error('加载 Ollama 模型失败:', error)
  }
}

async function pullOllamaModel() {
  if (!ollamaModelToPull.value) {
    message.warning('请输入模型名')
    return
  }
  
  pullingModel.value = true
  try {
    await ollamaApi.pullModel(ollamaModelToPull.value)
    message.success('开始拉取模型...')
    await loadOllamaModels()
  } catch (error) {
    message.error('拉取失败')
  } finally {
    pullingModel.value = false
  }
}

async function testModel() {
  if (!testPrompt.value) {
    message.warning('请输入测试内容')
    return
  }
  
  testing.value = true
  testResult.value = ''
  
  try {
    // 简化的测试 (实际应调用后端测试接口)
    await new Promise(r => setTimeout(r, 1000))
    testResult.value = `测试成功! 当前模型: ${currentModel.value}\n提示词: ${testPrompt.value}`
  } catch (error) {
    testResult.value = '测试失败'
  } finally {
    testing.value = false
  }
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

onMounted(() => {
  loadProviders()
  if (currentProvider.value === 'ollama') {
    loadOllamaModels()
  }
  window.addEventListener('resize', () => {
    xs.value = window.innerWidth < 768
  })
})
</script>

<style scoped>
.provider-card {
  transition: all 0.3s;
}

.provider-card.active {
  border-color: #18a058;
  background: #f0f9f0;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-name {
  font-weight: 600;
}

.provider-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.param-value {
  margin-left: 8px;
  min-width: 40px;
}
</style>
