<template>
  <!-- 工具栏 -->
  <div class="page-toolbar">
    <a-button @click="createItem" type="primary">
      <PlusOutlined /> 新建分类
    </a-button>
  </div>

  <!-- 加载状态 -->
  <a-spin :spinning="loading" tip="正在加载数据...">
    <!-- 空数据提示 -->
    <a-empty
      v-if="!loading && listData.value.length === 0"
      description="暂无分类数据"
    />

    <!-- 数据表格 -->
    <a-table
      v-else
      :columns="categoryColumns"
      :data-source="pageData.value"
      :pagination="pagination"
      size="middle"
      @change="handlePageChange"
    >
      <template #bodyCell="{ column, index }">
        <template v-if="column.key === 'action'">
          <a-space :size="4">
            <a-popconfirm
              v-if="pageData.value.length"
              title="确定删除此分类？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="deleteItem(index)"
            >
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="modifyItem(index)">编辑</a-button>
          </a-space>
        </template>
        <template v-else>
          <a-input readonly size="small" v-model:value="pageData.value[index][column.key]" />
        </template>
      </template>
    </a-table>
  </a-spin>

  <!-- 编辑/新建弹窗 -->
  <a-modal
    v-model:open="open"
    :title="operation === 'create' ? '新建分类' : '编辑分类'"
    @ok="submitOk"
    ok-text="确认"
    cancel-text="取消"
    :destroy-on-close="true"
  >
    <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
      <a-form-item label="分类名称">
        <a-input v-model:value="categoryForm.name" placeholder="请输入分类名称" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { httpGET, httpPOST, httpPUT, httpDELETE } from '@/http'
import { usePagination } from '@/utils/paginatior'
import { categoryColumns } from '@/utils/table'
import { categoryForm } from '@/utils/form'
import { assignSame, clearItem } from '@/utils/copy'
import { api } from '@/settings'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const { listData, pageData, pagination, handlePageChange, getindex, loading } = usePagination()
const open = ref(false)
const operation = ref(null)
const modifyid = ref(null)

const getCategory = async () => {
  loading.value = true
  try {
    const response = await httpGET(api.category)
    listData.value = response.data
  } catch {
    message.error('分类数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const deleteItem = (index) => {
  httpDELETE(api.category, listData.value[getindex(index)].id).then(() => {
    getCategory()
  })
}

const createItem = () => {
  clearItem(categoryForm)
  operation.value = 'create'
  open.value = true
}

const modifyItem = (index) => {
  clearItem(categoryForm)
  assignSame(listData.value[getindex(index)], categoryForm)
  operation.value = 'modify'
  open.value = true
  modifyid.value = getindex(index)
}

const submitOk = () => {
  if (operation.value == 'create') {
    httpPOST(api.category, categoryForm).then(() => {
      getCategory()
      open.value = false
    })
  } else if (operation.value == 'modify') {
    httpPUT(api.category, listData.value[modifyid.value].id, categoryForm).then(() => {
      getCategory()
      open.value = false
    })
  }
}

onMounted(() => {
  getCategory()
})
</script>

<style scoped>
.page-toolbar {
  margin-bottom: var(--space-md);
}
</style>
