<template>
  <div class="organization-selector">
    <n-dropdown
      :options="orgOptions"
      @select="handleSelect"
      trigger="click"
    >
      <n-button quaternary class="org-trigger">
        <template #icon>
          <n-icon><BusinessOutline /></n-icon>
        </template>
        {{ currentOrg?.name || '选择组织' }}
        <n-icon size="14"><ChevronDownOutline /></n-icon>
      </n-button>
    </n-dropdown>

    <n-button
      v-if="canCreateOrg"
      quaternary
      circle
      @click="showCreateModal = true"
    >
      <template #icon>
        <n-icon><AddOutline /></n-icon>
      </template>
    </n-button>

    <!-- 创建组织弹窗 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="创建组织">
      <n-form ref="formRef" :model="newOrg" :rules="rules">
        <n-form-item label="组织名称" path="name">
          <n-input v-model:value="newOrg.name" placeholder="输入组织名称" />
        </n-form-item>
        <n-form-item label="Slug" path="slug">
          <n-input
            v-model:value="newOrg.slug"
            placeholder="用于 URL，如: mycompany"
          >
            <template #prefix>litekb.com/</template>
          </n-input>
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" @click="createOrganization">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  BusinessOutline,
  ChevronDownOutline,
  AddOutline
} from '@vicons/ionicons5'
import { orgApi } from '../api/organization'

interface Organization {
  id: string
  name: string
  slug: string
  role: string
}

const router = useRouter()
const route = useRoute()
const message = useMessage()

const organizations = ref<Organization[]>([])
const currentOrg = ref<Organization | null>(null)
const showCreateModal = ref(false)

const newOrg = ref({
  name: '',
  slug: ''
})

const rules = {
  name: { required: true, message: '请输入组织名称', trigger: 'blur' },
  slug: { required: true, message: '请输入 slug', trigger: 'blur' }
}

const orgOptions = computed(() => [
  ...organizations.value.map(org => ({
    label: org.name,
    key: org.id,
    disabled: org.id === currentOrg.value?.id
  })),
  { type: 'divider' },
  { label: '管理组织', key: 'manage' },
  { label: '创建新组织', key: 'create' }
])

const canCreateOrg = computed(() => true)

async function loadOrganizations() {
  try {
    organizations.value = await orgApi.list()
    if (organizations.value.length > 0 && !currentOrg.value) {
      // 优先使用 URL 中的 org_id
      const urlOrgId = route.query.org_id as string
      const org = organizations.value.find(o => o.id === urlOrgId) || organizations.value[0]
      switchOrganization(org)
    }
  } catch (error) {
    message.error('加载组织列表失败')
  }
}

function handleSelect(orgId: string) {
  if (orgId === 'manage') {
    router.push({ name: 'OrganizationSettings' })
  } else if (orgId === 'create') {
    showCreateModal.value = true
  } else {
    const org = organizations.value.find(o => o.id === orgId)
    if (org) {
      switchOrganization(org)
    }
  }
}

function switchOrganization(org: Organization) {
  currentOrg.value = org
  // 更新本地存储
  localStorage.setItem('last_org_id', org.id)
  // 刷新页面数据
  window.location.reload()
}

async function createOrganization() {
  if (!newOrg.value.name.trim() || !newOrg.value.slug.trim()) {
    message.error('请填写完整信息')
    return
  }

  try {
    const org = await orgApi.create({
      name: newOrg.value.name,
      slug: newOrg.value.slug
    })
    
    message.success('创建成功')
    showCreateModal.value = false
    organizations.value.push({
      id: org.id,
      name: org.name,
      slug: org.slug,
      role: 'owner'
    })
    switchOrganization(org)
    
    newOrg.value = { name: '', slug: '' }
  } catch (error) {
    message.error('创建失败')
  }
}

onMounted(() => {
  const lastOrgId = localStorage.getItem('last_org_id')
  if (lastOrgId) {
    // 先加载列表再设置
    loadOrganizations()
  } else {
    loadOrganizations()
  }
})
</script>

<style scoped>
.organization-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.org-trigger {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
