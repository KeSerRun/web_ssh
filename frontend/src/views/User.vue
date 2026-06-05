<template>
  <!-- 工具栏 -->
  <div class="page-toolbar">
    <a-button @click="createItem" type="primary">
      <PlusOutlined /> 新建用户
    </a-button>
  </div>

  <!-- 加载状态 -->
  <a-spin :spinning="loading" tip="正在加载数据...">
    <!-- 空数据提示 -->
    <a-empty
      v-if="!loading && listData.value.length === 0"
      description="暂无用户数据"
    />

    <!-- 数据表格 -->
    <a-table
      v-else
      :columns="userColumns"
      :data-source="pageData.value"
      :pagination="pagination"
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
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="modifyItem(index)">编辑</a-button>
          </a-space>
        </template>

        <!-- 文字列 -->
        <template v-else-if="column.key === 'username' || column.key === 'mobile'">
          <a-input readonly size="small" v-model:value="pageData.value[index][column.key]" />
        </template>

        <!-- 布尔开关列 -->
        <template v-else>
          <a-switch
            disabled
            size="small"
            v-model:checked="pageData.value[index][column.key]"
          />
        </template>
      </template>
    </a-table>
  </a-spin>

  <!-- 编辑/新建弹窗 -->
  <a-modal
    v-model:open="open"
    :title="operation === 'create' ? '新建用户' : '编辑用户'"
    @ok="submitOk"
    ok-text="确认"
    cancel-text="取消"
    :destroy-on-close="true"
  >
    <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
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
import { api } from '@/settings'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const { listData, pageData, pagination, handlePageChange, getindex, loading } = usePagination()
const open = ref(false)
const operation = ref(null)
const modifyid = ref(null)

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
  operation.value = 'create'
  open.value = true
}

const modifyItem = (index) => {
  clearItem(userForm)
  assignSame(listData.value[getindex(index)], userForm)
  operation.value = 'modify'
  open.value = true
  modifyid.value = getindex(index)
}

const submitOk = () => {
  if (operation.value == 'create') {
    httpPOST(api.users, userForm).then(() => {
      getUser()
      open.value = false
    })
  } else if (operation.value == 'modify') {
    httpPUT(api.users, listData.value[modifyid.value].id, userForm).then(() => {
      getUser()
      open.value = false
    })
  }
}

onMounted(() => {
  getUser()
})
</script>

<style scoped>
.page-toolbar {
  margin-bottom: var(--space-md);
}
</style>
