<template>
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="page-header-left">
      <div class="page-icon page-icon--purple"><UserOutlined /></div>
      <div>
        <h2 class="page-title">用户管理</h2>
        <p class="page-subtitle">管理系统用户，分配权限角色与可访问的主机资源</p>
      </div>
    </div>
    <div class="page-header-right">
      <a-button @click="createItem" type="primary"><PlusOutlined /> 新建用户</a-button>
    </div>
  </div>

  <!-- 数据区 -->
  <div class="table-card">
    <a-spin :spinning="loading" tip="正在加载数据...">
      <a-empty
        v-if="!loading && listData.value.length === 0"
        description="暂无用户数据"
      />
      <a-table
        v-else
        :columns="userColumns"
        :data-source="pageData.value"
        :pagination="pagination"
        :row-key="record => record.id"
        size="middle"
        @change="handlePageChange"
      >
      <template #bodyCell="{ column, index }">
        <!-- 操作列 -->
        <template v-if="column.key === 'action'">
          <a-space :size="4">
            <a-popconfirm
              v-if="pageData.value.length"
              title="确定删除此用户？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="deleteItem(index)"
            >
              <a-button type="link" danger size="small"><DeleteOutlined /> 删除</a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="modifyItem(index)"><EditOutlined /> 编辑</a-button>
          </a-space>
        </template>

        <!-- 头像列 -->
        <template v-else-if="column.key === 'avatar'">
          <a-avatar
            :size="32"
            :src="avatarUrl(pageData.value[index].avatar)"
            :style="{ background: pageData.value[index].avatar ? undefined : avatarBg(pageData.value[index]) }"
          >
            <template #icon><UserOutlined /></template>
          </a-avatar>
        </template>

        <!-- 文字列 -->
        <template v-else-if="column.key === 'username' || column.key === 'mobile'">
          <span class="cell-text">{{ pageData.value[index][column.key] }}</span>
        </template>

        <!-- 布尔列 -->
        <template v-else>
          <CheckCircleFilled v-if="pageData.value[index][column.key]" style="color: #52c41a; font-size: 16px;" />
          <CloseCircleFilled v-else style="color: #d9d9d9; font-size: 16px;" />
        </template>
      </template>
    </a-table>
  </a-spin>
  </div>

  <!-- 编辑/新建弹窗 -->
  <a-modal
    v-model:open="open"
    :title="operation === 'create' ? '新建用户' : '编辑用户'"
    @ok="submitOk"
    ok-text="确认"
    cancel-text="取消"
    :destroy-on-close="true"
    width="520px"
    :confirm-loading="submitting"
  >
    <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item label="头像">
        <a-upload
          :max-count="1"
          list-type="picture-card"
          :before-upload="beforeUpload"
          :file-list="avatarFileList"
          @remove="onRemoveAvatar"
        >
          <PlusOutlined />
        </a-upload>
      </a-form-item>
      <a-form-item label="用户名">
        <a-input v-model:value="userForm.username" placeholder="请输入用户名" />
      </a-form-item>
      <a-form-item label="密码">
        <a-input-password v-model:value="userForm.password" placeholder="留空则不修改" />
      </a-form-item>
      <a-form-item label="手机号">
        <a-input v-model:value="userForm.mobile" placeholder="请输入手机号" />
      </a-form-item>
      <a-form-item label="激活状态">
        <a-switch v-model:checked="userForm.is_active" />
      </a-form-item>
      <a-form-item label="员工权限">
        <a-switch v-model:checked="userForm.is_staff" />
      </a-form-item>
      <a-form-item label="超级管理员">
        <a-switch v-model:checked="userForm.is_superuser" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { httpGET, httpPOST, httpPUT, httpDELETE } from '@/http'
import { usePagination } from '@/utils/paginatior'
import { userColumns } from '@/utils/table'
import { userForm } from '@/utils/form'
import { assignSame, clearItem } from '@/utils/copy'
import settings from '@/settings'
import { api } from '@/settings'
import { message } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined, CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue'

const { listData, pageData, pagination, handlePageChange, getindex, loading } = usePagination()
const open = ref(false)
const operation = ref(null)
const modifyid = ref(null)
const submitting = ref(false)
const avatarFileList = ref([])
const removeAvatar = ref(false)

/** 构造完整头像 URL */
const avatarUrl = (path) => {
  if (!path) return ''
  return path.startsWith('http') ? path : settings.host + path
}

/** 根据角色返回默认头像背景色 */
const avatarBg = (user) => {
  if (user.is_superuser) return 'linear-gradient(135deg, #fa8c16, #ffa940)'
  if (user.is_staff) return 'linear-gradient(135deg, #1677ff, #4096ff)'
  return 'linear-gradient(135deg, #8c8c8c, #bfbfbf)'
}

/** 上传前拦截：只存文件引用，不自动上传 */
const beforeUpload = (file) => {
  avatarFileList.value = [file]
  return false  // 阻止自动上传，手动随表单提交
}

const getUser = async () => {
  loading.value = true
  try {
    const response = await httpGET(api.users)
    listData.value = response.data
  } catch {
    message.error('用户数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const deleteItem = (index) => {
  httpDELETE(api.users, listData.value[getindex(index)].id).then(() => {
    getUser()
  })
}

const createItem = () => {
  clearItem(userForm)
  avatarFileList.value = []
  removeAvatar.value = false
  operation.value = 'create'
  open.value = true
}

const modifyItem = (index) => {
  clearItem(userForm)
  removeAvatar.value = false
  const userData = listData.value[getindex(index)]
  assignSame(userData, userForm)

  // 已有头像时显示预览
  if (userData.avatar) {
    avatarFileList.value = [{
      uid: '-1',
      name: '当前头像',
      status: 'done',
      url: avatarUrl(userData.avatar),
    }]
  } else {
    avatarFileList.value = []
  }

  operation.value = 'modify'
  open.value = true
  modifyid.value = getindex(index)
}

/** 移除头像（预览或已有头像） */
const onRemoveAvatar = () => {
  avatarFileList.value = []
  removeAvatar.value = true
}

const submitOk = () => {
  submitting.value = true
  const hasNewAvatar = avatarFileList.value.length > 0 && avatarFileList.value[0].uid !== '-1'

  const done = () => {
    getUser()
    open.value = false
    avatarFileList.value = []
    removeAvatar.value = false
    submitting.value = false
  }

  if (hasNewAvatar) {
    // 有新头像 → FormData
    const fd = new FormData()
    for (const [key, val] of Object.entries(userForm)) {
      if (key === 'hosts' && Array.isArray(val)) {
        val.forEach(id => fd.append('hosts', id))
      } else if (val != null && key !== 'avatar') {
        fd.append(key, val)
      }
    }
    fd.append('avatar', avatarFileList.value[0])

    if (operation.value == 'create') {
      httpPOST(api.users, fd, false).then(done).catch(() => { submitting.value = false })
    } else {
      httpPUT(api.users, listData.value[modifyid.value].id, fd, false).then(done).catch(() => { submitting.value = false })
    }
  } else if (removeAvatar.value) {
    // 删除头像 → 发送 null
    const payload = { ...userForm }
    payload.avatar = null
    if (operation.value == 'create') {
      httpPOST(api.users, payload).then(done).catch(() => { submitting.value = false })
    } else {
      httpPUT(api.users, listData.value[modifyid.value].id, payload).then(done).catch(() => { submitting.value = false })
    }
  } else {
    // 无新头像 → JSON（不发送 avatar 字段）
    const payload = { ...userForm }
    delete payload.avatar
    if (operation.value == 'create') {
      httpPOST(api.users, payload).then(done).catch(() => { submitting.value = false })
    } else {
      httpPUT(api.users, listData.value[modifyid.value].id, payload).then(done).catch(() => { submitting.value = false })
    }
  }
}

onMounted(() => {
  getUser()
})
</script>

<style scoped>
</style>
