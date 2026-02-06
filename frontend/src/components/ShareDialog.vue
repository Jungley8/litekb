<template>
  <div class="share-dialog">
    <n-button @click="showModal = true">
      <template #icon><n-icon><ShareOutline /></n-icon></template>
      分享
    </n-button>

    <n-modal v-model:show="showModal" preset="dialog" title="分享" style="width: 500px">
      <n-tabs type="line" animated>
        <!-- 链接分享 -->
        <n-tab-pane name="link" tab="链接分享">
          <n-form-item label="权限">
            <n-radio-group v-model:value="permission">
              <n-space>
                <n-radio value="view">只读</n-radio>
                <n-radio value="comment">可评论</n-radio>
                <n-radio value="edit">可编辑</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-form-item label="有效期">
            <n-select
              v-model:value="expiresIn"
              :options="[
                { label: '1 天', value: 1 },
                { label: '7 天', value: 7 },
                { label: '30 天', value: 30 },
                { label: '永不过期', value: 0 }
              ]"
            />
          </n-form-item>

          <n-form-item label="访问密码">
            <n-input
              v-model:value="password"
              type="password"
              placeholder="留空表示无需密码"
              show-password-on="click"
            />
          </n-form-item>

          <n-divider />

          <!-- 生成的链接 -->
          <div v-if="shareLink" class="share-link-result">
            <n-input
              :value="shareLink.short_url"
              readonly
              placeholder="点击「创建链接」生成"
            >
              <template #suffix>
                <n-button text @click="copyLink">
                  <template #icon><n-icon><CopyOutline /></n-icon></template>
                </n-button>
              </template>
            </n-input>
            
            <n-alert type="info" style="margin-top: 12px">
              <template #header>Token (用于访问)</template>
              <code>{{ shareLink.token }}</code>
              <n-button text size="small" @click="copyToken">复制</n-button>
            </n-alert>
          </div>

          <n-button
            v-else
            type="primary"
            block
            @click="createShareLink"
            :loading="creating"
          >
            创建分享链接
          </n-button>
        </n-tab-pane>

        <!-- 嵌入代码 -->
        <n-tab-pane name="embed" tab="嵌入">
          <n-form-item label="嵌入方式">
            <n-radio-group v-model:value="embedType">
              <n-space vertical>
                <n-radio value="iframe">Iframe 嵌入</n-radio>
                <n-radio value="widget">小部件</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-input
            type="textarea"
            :value="embedCode"
            :rows="4"
            readonly
          />
          
          <n-button
            type="primary"
            text
            @click="copyEmbedCode"
            style="margin-top: 8px"
          >
            <template #icon><n-icon><CopyOutline /></n-icon></template>
            复制代码
          </n-button>
        </n-tab-pane>

        <!-- 管理分享 -->
        <n-tab-pane name="manage" tab="管理链接">
          <n-empty v-if="shareLinks.length === 0" description="暂无分享链接" />
          
          <n-list v-else>
            <n-list-item v-for="link in shareLinks" :key="link.id">
              <n-thing>
                <template #header>
                  {{ link.short_url }}
                </template>
                <template #header-extra>
                  <n-button text type="error" size="small" @click="revokeLink(link.id)">
                    撤销
                  </n-button>
                </template>
                <template #description>
                  <n-space>
                    <n-tag size="small">{{ link.permission }}</n-tag>
                    <n-tag size="small" :type="link.expires_at ? 'warning' : 'success'">
                      {{ link.expires_at ? `过期: ${link.expires_at}` : '永不过期' }}
                    </n-tag>
                    <span>访问: {{ link.view_count }}</span>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-tab-pane>
      </n-tabs>

      <template #action>
        <n-button @click="showModal = false">关闭</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { ShareOutline, CopyOutline } from '@vicons/ionicons5'
import { shareApi } from '../api/share'

const props = defineProps<{
  type: 'document' | 'kb' | 'conversation'
  resourceId: string
}>()

const emit = defineEmits<{
  (e: 'shared', link: any): void
}>()

const message = useMessage()

const showModal = ref(false)
const permission = ref('view')
const expiresIn = ref(7)
const password = ref('')
const embedType = ref('iframe')

const creating = ref(false)
const shareLink = ref<any>(null)
const shareLinks = ref<any[]>([])

const embedCode = computed(() => {
  if (!shareLink.value) return ''
  
  if (embedType.value === 'iframe') {
    return `<iframe src="${shareLink.value.short_url}/embed" width="100%" height="600" frameborder="0"></iframe>`
  }
  
  return `<div data-litekb-share="${shareLink.value.id}"></div>
<script src="${window.location.origin}/widget.js"><\/script>`
})

async function createShareLink() {
  creating.value = true
  try {
    shareLink.value = await shareApi.create({
      type: props.type,
      resource_id: props.resourceId,
      permission: permission.value,
      expires_in_days: expiresIn.value === 0 ? undefined : expiresIn.value,
      password: password.value || undefined
    })
    message.success('分享链接已创建')
    loadShareLinks()
  } catch (error) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

async function loadShareLinks() {
  try {
    shareLinks.value = await shareApi.list(props.type, props.resourceId)
  } catch (error) {
    console.error('加载分享列表失败')
  }
}

async function revokeLink(shareId: string) {
  try {
    await shareApi.revoke(shareId)
    message.success('已撤销')
    loadShareLinks()
  } catch (error) {
    message.error('撤销失败')
  }
}

function copyLink() {
  navigator.clipboard.writeText(shareLink.value.short_url)
  message.success('链接已复制')
}

function copyToken() {
  navigator.clipboard.writeText(shareLink.value.token)
  message.success('Token 已复制')
}

function copyEmbedCode() {
  navigator.clipboard.writeText(embedCode.value)
  message.success('代码已复制')
}

watch(showModal, (val) => {
  if (val && shareLink.value) {
    loadShareLinks()
  }
})
</script>

<style scoped>
.share-link-result {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}
</style>
