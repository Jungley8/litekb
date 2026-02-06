<template>
  <div class="org-settings">
    <n-tabs type="line" animated>
      <!-- 基本信息 -->
      <n-tab-pane name="general" tab="基本信息">
        <n-card>
          <n-form :model="orgForm" label-placement="left" label-width="120">
            <n-form-item label="组织名称">
              <n-input v-model:value="orgForm.name" placeholder="组织名称" />
            </n-form-item>
            
            <n-form-item label="Slug">
              <n-input v-model:value="orgForm.slug" disabled>
                <template #prefix>litekb.com/</template>
              </n-input>
            </n-form-item>
            
            <n-form-item label="Logo">
              <n-upload
                action="/api/v1/upload/logo"
                :custom-request="handleLogoUpload"
                :show-file-list="false"
              >
                <n-avatar
                  round
                  :size="80"
                  :src="orgForm.logo"
                  style="cursor: pointer"
                >
                  <template #fallback>
                    <n-icon size="40"><ImageOutline /></n-icon>
                  </template>
                </n-avatar>
                <n-p depth="3" style="margin-top: 8px">点击更换 Logo</n-p>
              </n-upload>
            </n-form-item>
            
            <n-form-item>
              <n-button type="primary" @click="saveOrg" :loading="saving">
                保存
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <!-- 成员管理 -->
      <n-tab-pane name="members" tab="成员管理">
        <n-card>
          <template #header>
            <div class="card-header">
              <span>成员列表 ({{ members.length }})</span>
              <n-button type="primary" @click="showInviteModal = true">
                <template #icon><n-icon><PersonAddOutline /></n-icon></template>
                邀请成员
              </n-button>
            </div>
          </template>

          <n-data-table
            :columns="memberColumns"
            :data="members"
            :bordered="false"
          />

          <n-divider />

          <n-alert type="info" title="权限说明">
            <template #header>角色权限</template>
            <ul>
              <li><n-tag>Owner</n-tag> 完全控制，包括删除组织</li>
              <li><n-tag>Admin</n-tag> 管理成员，编辑设置</li>
              <li><n-tag>Member</n-tag> 普通操作</li>
            </ul>
          </n-alert>
        </n-card>
      </n-tab-pane>

      <!-- 邀请管理 -->
      <n-tab-pane name="invitations" tab="待处理邀请">
        <n-card>
          <n-empty v-if="invitations.length === 0" description="没有待处理的邀请" />
          
          <n-list v-else>
            <n-list-item v-for="invite in invitations" :key="invite.id">
              <n-thing>
                <template #header>
                  {{ invite.email }}
                  <n-tag size="small" style="margin-left: 8px">
                    {{ invite.role }}
                  </n-tag>
                </template>
                <template #header-extra>
                  <n-button
                    size="small"
                    quaternary
                    @click="cancelInvite(invite.id)"
                  >
                    取消
                  </n-button>
                </template>
                <template #description>
                  发送于 {{ formatDate(invite.created_at) }}
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-tab-pane>

      <!-- API Keys -->
      <n-tab-pane name="apikeys" tab="API Keys">
        <n-card>
          <template #header>
            <div class="card-header">
              <span>API Keys</span>
              <n-button type="primary" @click="showCreateKeyModal = true">
                <template #icon><n-icon><KeyOutline /></n-icon></template>
                创建 Key
              </n-button>
            </div>
          </template>

          <n-alert type="warning" style="margin-bottom: 16px">
            API Key 只会显示一次，请立即复制并妥善保管。
          </n-alert>

          <n-data-table
            :columns="keyColumns"
            :data="apiKeys"
            :bordered="false"
          />
        </n-card>
      </n-tab-pane>

      <!-- 使用统计 -->
      <n-tab-pane name="usage" tab="使用统计">
        <n-card>
          <n-grid :cols="4" :x-gap="16">
            <n-gi>
              <n-statistic label="知识库">
                <template #prefix>{{ usage.kb_count }}</template>
                <template #suffix>/ {{ usage.kb_limit }}</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="文档">
                <template #prefix>{{ usage.doc_count }}</template>
                <template #suffix>/ {{ usage.doc_limit }}</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="成员">
                <template #prefix>{{ usage.member_count }}</template>
                <template #suffix>/ {{ usage.member_limit }}</template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="存储">
                <template #prefix>{{ usage.storage_gb }}</template>
                <template #suffix>GB / {{ usage.storage_limit_gb }}GB</template>
              </n-statistic>
            </n-gi>
          </n-grid>

          <n-divider />

          <n-button
            v-if="usage.kb_count >= usage.kb_limit"
            type="warning"
            block
          >
            升级到 Pro 版，解锁更多功能
          </n-button>
        </n-card>
      </n-tab-pane>

      <!-- 危险操作 -->
      <n-tab-pane name="danger" tab="危险操作">
        <n-card>
          <n-alert type="error" title="危险操作">
            以下操作不可撤销，请谨慎操作。
          </n-alert>

          <n-space vertical style="margin-top: 16px">
            <n-button type="warning" ghost @click="handleTransfer">
              转让组织
            </n-button>
            
            <n-popconfirm @positive-click="deleteOrg">
              <template #trigger>
                <n-button type="error" ghost>
                  删除组织
                </n-button>
              </template>
              确定要删除此组织吗？此操作不可撤销。
            </n-popconfirm>
          </n-space>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- 邀请成员弹窗 -->
    <n-modal v-model:show="showInviteModal" preset="dialog" title="邀请成员">
      <n-form :model="inviteForm">
        <n-form-item label="邮箱">
          <n-input v-model:value="inviteForm.email" placeholder="输入邮箱地址" />
        </n-form-item>
        <n-form-item label="角色">
          <n-select
            v-model:value="inviteForm.role"
            :options="roleOptions"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showInviteModal = false">取消</n-button>
        <n-button type="primary" @click="sendInvite">发送邀请</n-button>
      </template>
    </n-modal>

    <!-- 创建 API Key 弹窗 -->
    <n-modal v-model:show="showCreateKeyModal" preset="dialog" title="创建 API Key">
      <n-form :model="keyForm">
        <n-form-item label="名称">
          <n-input v-model:value="keyForm.name" placeholder="给 Key 起个名字" />
        </n-form-item>
        <n-form-item label="权限">
          <n-checkbox-group v-model:value="keyForm.scopes">
            <n-space>
              <n-checkbox value="read">读取</n-checkbox>
              <n-checkbox value="write">写入</n-checkbox>
              <n-checkbox value="admin">管理</n-checkbox>
            </n-space>
          </n-checkbox-group>
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateKeyModal = false">取消</n-button>
        <n-button type="primary" @click="createApiKey">创建</n-button>
      </template>
    </n-modal>

    <!-- 新建 Key 显示弹窗 -->
    <n-modal v-model:show="showNewKeyModal" preset="dialog" title="API Key 已创建">
      <n-input
        v-model:value="newKeyValue"
        type="textarea"
        readonly
        placeholder="API Key"
      />
      <n-alert type="warning" style="margin-top: 12px">
        请立即复制并妥善保管，此 Key 只会显示一次。
      </n-alert>
      <template #action>
        <n-button type="primary" @click="copyKey">复制</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage, useDialog, NButton, NTag, NSpace } from 'naive-ui'
import {
  ImageOutline,
  PersonAddOutline,
  KeyOutline
} from '@vicons/ionicons5'
import { orgApi, Member, Invitation, APIKeyInfo } from '../api/organization'

const route = useRoute()
const message = useMessage()
const dialog = useDialog()

const orgId = route.params.id as string

const saving = ref(false)
const showInviteModal = ref(false)
const showCreateKeyModal = ref(false)
const showNewKeyModal = ref(false)
const newKeyValue = ref('')

const orgForm = ref({
  name: '',
  slug: '',
  logo: ''
})

const inviteForm = ref({
  email: '',
  role: 'member'
})

const keyForm = ref({
  name: '',
  scopes: ['read']
})

const members = ref<Member[]>([])
const invitations = ref<Invitation[]>([])
const apiKeys = ref<APIKeyInfo[]>([])

const usage = ref({
  kb_count: 0, kb_limit: 3,
  doc_count: 0, doc_limit: 1000,
  member_count: 0, member_limit: 5,
  storage_gb: 0, storage_limit_gb: 1
})

const roleOptions = [
  { label: 'Member', value: 'member' },
  { label: 'Admin', value: 'admin' }
]

// 表格列配置
const memberColumns = [
  { title: '用户', key: 'username' },
  { title: '邮箱', key: 'email' },
  { 
    title: '角色', 
    key: 'role',
    render(row: Member) {
      return h(NTag, { type: row.role === 'owner' ? 'warning' : row.role === 'admin' ? 'info' : 'default' }, {
        default: () => row.role
      })
    }
  },
  { title: '加入时间', key: 'joined_at' },
  {
    title: '操作',
    key: 'actions',
    render(row: Member) {
      return h(NSpace, {}, {
        default: () => [
          row.role !== 'owner' && h(NButton, {
            size: 'small',
            quaternary: true,
            onClick: () => updateMemberRole(row.user_id, row.role === 'admin' ? 'member' : 'admin')
          }, { default: () => row.role === 'admin' ? '降级' : '升级' }),
          row.role !== 'owner' && h(NButton, {
            size: 'small',
            quaternary: true,
            type: 'error',
            onClick: () => removeMember(row.user_id)
          }, { default: () => '移除' })
        ]
      })
    }
  }
]

const keyColumns = [
  { title: '名称', key: 'name' },
  { title: 'Key', key: 'key_prefix', render: (row: APIKeyInfo) => `****${row.key_prefix}` },
  { title: '权限', key: 'scopes', render: (row: APIKeyInfo) => row.scopes.join(', ') },
  { title: '最后使用', key: 'last_used_at' },
  {
    title: '操作',
    key: 'actions',
    render(row: APIKeyInfo) {
      return h(NButton, {
        size: 'small',
        type: 'error',
        quaternary: true,
        onClick: () => deleteApiKey(row.id)
      }, { default: () => '删除' })
    }
  }
]

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function loadOrg() {
  try {
    const org = await orgApi.get(orgId)
    orgForm.value = {
      name: org.name,
      slug: org.slug,
      logo: org.logo || ''
    }
  } catch (error) {
    message.error('加载组织信息失败')
  }
}

async function loadMembers() {
  try {
    members.value = await orgApi.members(orgId)
  } catch (error) {
    message.error('加载成员列表失败')
  }
}

async function loadInvitations() {
  try {
    invitations.value = await orgApi.invitations(orgId)
  } catch (error) {
    console.error('加载邀请列表失败')
  }
}

async function loadApiKeys() {
  try {
    apiKeys.value = await orgApi.apiKeys(orgId)
  } catch (error) {
    console.error('加载 API Keys 失败')
  }
}

async function loadUsage() {
  try {
    usage.value = await orgApi.usage(orgId)
  } catch (error) {
    console.error('加载使用统计失败')
  }
}

async function saveOrg() {
  saving.value = true
  try {
    await orgApi.update(orgId, orgForm.value)
    message.success('保存成功')
  } catch (error) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function sendInvite() {
  if (!inviteForm.value.email) {
    message.error('请输入邮箱')
    return
  }
  
  try {
    await orgApi.invite(orgId, inviteForm.value.email, inviteForm.value.role)
    message.success('邀请已发送')
    showInviteModal.value = false
    inviteForm.value = { email: '', role: 'member' }
    loadInvitations()
  } catch (error) {
    message.error('发送邀请失败')
  }
}

async function cancelInvite(inviteId: string) {
  try {
    await orgApi.cancelInvitation(orgId, inviteId)
    message.success('邀请已取消')
    loadInvitations()
  } catch (error) {
    message.error('取消邀请失败')
  }
}

async function removeMember(userId: string) {
  dialog.warning({
    title: '确认移除',
    content: '确定要将此成员移除吗？',
    positiveText: '移除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await orgApi.removeMember(orgId, userId)
        message.success('成员已移除')
        loadMembers()
      } catch (error) {
        message.error('移除失败')
      }
    }
  })
}

async function updateMemberRole(userId: string, role: string) {
  try {
    await orgApi.updateMember(orgId, userId, role)
    message.success('角色已更新')
    loadMembers()
  } catch (error) {
    message.error('更新失败')
  }
}

async function createApiKey() {
  if (!keyForm.value.name) {
    message.error('请输入名称')
    return
  }
  
  try {
    const result = await orgApi.createApiKey(orgId, keyForm.value.name, keyForm.value.scopes)
    newKeyValue.value = result.key
    showCreateKeyModal.value = false
    showNewKeyModal.value = true
    loadApiKeys()
  } catch (error) {
    message.error('创建失败')
  }
}

async function deleteApiKey(keyId: string) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除此 API Key 吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await orgApi.deleteApiKey(orgId, keyId)
        message.success('已删除')
        loadApiKeys()
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

function copyKey() {
  navigator.clipboard.writeText(newKeyValue.value)
  message.success('已复制到剪贴板')
}

function handleLogoUpload() {
  message.info('Logo 上传功能开发中')
}

function deleteOrg() {
  dialog.error({
    title: '确认删除',
    content: '确定要删除此组织吗？此操作不可撤销，所有数据将被删除。',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await orgApi.delete(orgId)
        message.success('组织已删除')
        // 跳转首页
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

onMounted(() => {
  loadOrg()
  loadMembers()
  loadInvitations()
  loadApiKeys()
  loadUsage()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
