<template>
  <!-- 页面头部 -->
  <div class="page-header">
    <div class="page-header-left">
      <div class="page-icon page-icon--blue"><BankOutlined /></div>
      <div>
        <h2 class="page-title">资产管理</h2>
        <p class="page-subtitle">管理 SSH 远程主机，支持新增、编辑、删除和连接修复</p>
      </div>
    </div>
    <div class="page-header-right">
      <a-space :size="8">
        <a-button @click="createItem" type="primary"><PlusOutlined /> 新建主机</a-button>
        <a-button @click="updateAll"><CloudUploadOutlined /> 批量同步</a-button>
        <a-button @click="repairAll" danger><ToolOutlined /> 修复连接</a-button>
        <a-button @click="openCategoryModal" type="dashed"><PartitionOutlined /> 管理分类</a-button>
      </a-space>
    </div>
  </div>

  <!-- 数据区 -->
  <div class="table-card">
    <a-spin :spinning="loading" tip="正在加载数据...">
      <a-empty
        v-if="!loading && listData.value.length === 0"
        description="暂无主机数据"
      />
      <a-table
        v-else
        :columns="detailsColumns"
        :data-source="pageData.value"
        :pagination="pagination"
        :row-key="record => record.id"
        :row-class-name="rowClassName"
        size="middle"
        @change="handlePageChange"
      >
      <template #bodyCell="{ column, index }">
        <!-- 操作列 -->
        <template v-if="column.key === 'action'">
          <a-space :size="8">
            <a-button type="link" size="small" @click="updateItem(index)"><SaveOutlined /> 保存</a-button>
            <a-button type="link" size="small" @click="insertItem(index)"><PlusOutlined /> 插入</a-button>
            <a-popconfirm
              v-if="pageData.value.length"
              title="确定删除？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="deleteItem(index)"
            >
              <a-button type="link" danger size="small"><DeleteOutlined /> 删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>

        <!-- 状态指示列 -->
        <template v-else-if="column.key === 'update_status'">
          <span
            class="status-dot"
            :class="{
              'status-synced': pageData.value[index].update_status == 1,
              'status-new': pageData.value[index].update_status == 2,
              'status-modified': pageData.value[index].update_status == 3,
            }"
          ></span>
        </template>

        <!-- 分类选择列 -->
        <template v-else-if="column.key === 'category_name'">
          <a-dropdown :trigger="['click']">
            <a-button size="small" class="category-select-btn">
              {{ pageData.value[index].category_name || '选择分类' }}
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item
                  @click="onClickSelect(value.name, index)"
                  v-for="value in categoryList"
                  :key="value.id"
                >
                  {{ value.name }}
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </template>

        <!-- 密码列 -->
        <template v-else-if="column.key === 'connect_pwd'">
          <a-input-password
            size="small"
            @change="onChange(index)"
            v-model:value="pageData.value[index][column.key]"
          />
        </template>

        <!-- 其他文本列 -->
        <template v-else>
          <a-input
            size="small"
            @change="onChange(index)"
            v-model:value="pageData.value[index][column.key]"
          />
        </template>
      </template>
    </a-table>
  </a-spin>
  </div>

  <!-- 管理分类弹窗 -->
  <a-modal
    v-model:open="cateModalOpen"
    title="管理分类"
    :footer="null"
    width="600px"
    :destroy-on-close="true"
  >
    <div style="margin-bottom: var(--space-md);">
      <a-button @click="cateCreate" type="primary" size="small"><PlusOutlined /> 新建分类</a-button>
    </div>
    <a-spin :spinning="cateLoading" tip="加载中...">
      <a-empty v-if="!cateLoading && cateListData.value.length === 0" description="暂无分类" />
      <a-table
        v-else
        :columns="categoryColumns"
        :data-source="catePageData.value"
        :pagination="catePagination"
        :row-key="record => record.id"
        size="small"
        @change="cateHandlePageChange"
      >
        <template #bodyCell="{ column, index }">
          <template v-if="column.key === 'action'">
            <a-space :size="4">
              <a-popconfirm title="确定删除？" ok-text="确定" cancel-text="取消" @confirm="cateDelete(index)">
                <a-button type="link" danger size="small"><DeleteOutlined /></a-button>
              </a-popconfirm>
              <a-button type="link" size="small" @click="cateModify(index)"><EditOutlined /></a-button>
            </a-space>
          </template>
          <template v-else>
            <span class="cell-text">{{ catePageData.value[index][column.key] }}</span>
          </template>
        </template>
      </a-table>
    </a-spin>

    <!-- 分类编辑小弹窗 -->
    <a-modal
      v-model:open="cateFormOpen"
      :title="cateOp === 'create' ? '新建分类' : '编辑分类'"
      @ok="cateSubmit"
      ok-text="确认" cancel-text="取消"
      width="360px"
      :confirm-loading="cateSubmitting"
    >
      <a-input v-model:value="categoryForm.name" placeholder="请输入分类名称" />
    </a-modal>
  </a-modal>
</template>

<script setup>
import { ref, computed, onMounted, toRaw } from 'vue'
import { httpGET, httpPOST, httpPUT, httpDELETE } from '@/http'
import { usePagination } from '@/utils/paginatior'
import { detailsColumns, categoryColumns } from '@/utils/table'
import { detailsForm, categoryForm } from '@/utils/form'
import { api } from '@/settings'
import { assignSame, clearItem } from '@/utils/copy'
import { message } from 'ant-design-vue'
import { PlusOutlined, CloudUploadOutlined, DownOutlined, ToolOutlined, DeleteOutlined, SaveOutlined, BankOutlined, EditOutlined, PartitionOutlined } from '@ant-design/icons-vue'

const { listData, pageData, pagination, handlePageChange, getindex, loading } = usePagination()
const categoryList = ref([])

const getDetails = async () => {
  loading.value = true
  try {
    const response = await httpGET(api.hosts)
    let data = response.data
    data.forEach((item) => { item.update_status = 1 })
    listData.value = data
  } catch {
    message.error('主机数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const getCategory = async () => {
  try {
    const response = await httpGET(api.category)
    categoryList.value = response.data
  } catch {
    message.error('分类数据加载失败')
  }
}

const onClickSelect = (key, index) => {
  index = getindex(index)
  listData.value[index].category = categoryList.value.find(item => item.name === key).id
  listData.value[index].category_name = key
  if (listData.value[index].update_status == 1) {
    listData.value[index].update_status = 3
  }
}

const updateItem = (index, showMsg = true) => {
  index = getindex(index)
  let payload = assignSame(listData.value[index], detailsForm)
  delete payload['update_status']
  delete payload['id']

  // 校验必填字段（批量同步时不弹单项警告）
  if (!payload.ip_addr) {
    if (showMsg) message.warning('IP 地址不能为空')
    return
  }
  if (!payload.connect_pwd) {
    if (showMsg) message.warning('连接密码不能为空')
    return
  }
  if (!payload.category || payload.category === 0) {
    if (showMsg) message.warning('请选择主机分类')
    return
  }

  const onErr = (err) => {
    // http 拦截器已显示 400 错误，此处仅处理其他状态码或网络错误
    if (!err?.response) {
      message.error('网络连接失败，请检查后端服务')
    }
  }

  if (listData.value[index].update_status == 2) {
    return httpPOST(api.hosts, payload, showMsg).then(() => { listData.value[index].update_status = 1 }).catch(onErr)
  } else if (listData.value[index].update_status == 3) {
    return httpPUT(api.hosts, listData.value[index].id, payload, showMsg).then(() => { listData.value[index].update_status = 1 }).catch(onErr)
  }
}

const updateAll = () => {
  const promises = []
  for (let index = 0; index < listData.value.length; index++) {
    const item = listData.value[index]
    // 只同步新增或修改的记录
    if (item.update_status !== 2 && item.update_status !== 3) continue
    const p = updateItem(index, false)
    if (p) promises.push(p)
  }

  if (promises.length === 0) {
    message.info('没有需要同步的更改')
    return
  }

  Promise.allSettled(promises).then((results) => {
    const successCount = results.filter(r => r.status === 'fulfilled').length
    const failCount = results.filter(r => r.status === 'rejected').length
    if (failCount === 0) {
      message.success(`批量同步完成，共处理 ${successCount} 条记录`)
    } else {
      message.warning(`批量同步完成：${successCount} 条成功，${failCount} 条失败`)
    }
  })
}

// 批量修复连接：重新推送公钥（容器重建后 authorized_keys 丢失时使用）
const repairAll = () => {
  listData.value.forEach(item => {
    if (item.id && item.update_status === 1) {
      httpPOST(`${api.hosts}${item.id}/repair/`, {}, true).catch(() => {})
    }
  })
}

const deleteItem = index => {
  index = getindex(index)
  if (listData.value[index].update_status == 2) {
    listData.value.splice(index, 1)
  } else {
    httpDELETE(api.hosts, listData.value[index].id).then(() => { listData.value.splice(index, 1) })
  }
}

const onChange = (index) => {
  index = getindex(index)
  if (listData.value[index].update_status == 1) {
    listData.value[index].update_status = 3
  }
}

const count = computed(() =>
  listData.value?.length
    ? Math.max(...listData.value.map((item) => parseInt(item.id)))
    : 0
)

const createItem = () => {
  clearItem(detailsForm)
  detailsForm.id = `${count.value + 1}`
  detailsForm.update_status = 2
  detailsForm.ip_addr = '127.0.0.1'
  detailsForm.port = 22
  detailsForm.username = 'root'
  detailsForm.connect_pwd = ''
  detailsForm.name = 'host-' + Math.random().toString(36).slice(2, 8)
  if (categoryList.value.length) {
    detailsForm.category = categoryList.value[0].id
    detailsForm.category_name = categoryList.value[0].name
  }
  listData.value.splice(0, 0, structuredClone(toRaw(detailsForm)))
}

const insertItem = index => {
  clearItem(detailsForm)
  index = getindex(index)
  detailsForm.id = `${count.value + 1}`
  detailsForm.update_status = 2
  detailsForm.ip_addr = '127.0.0.1'
  detailsForm.port = 22
  detailsForm.username = 'root'
  detailsForm.connect_pwd = ''
  detailsForm.name = 'host-' + Math.random().toString(36).slice(2, 8)
  if (categoryList.value.length) {
    detailsForm.category = categoryList.value[0].id
    detailsForm.category_name = categoryList.value[0].name
  }
  listData.value.splice(index + 1, 0, structuredClone(toRaw(detailsForm)))
}

const rowClassName = (record) => {
  if (record.update_status == 2) return 'row-new'
  if (record.update_status == 3) return 'row-modified'
  return ''
}

// ==================== 分类管理（内嵌弹窗） ====================
const {
  listData: cateListData, pageData: catePageData,
  pagination: catePagination, handlePageChange: cateHandlePageChange,
  getindex: cateGetIndex, loading: cateLoading,
} = usePagination()
const cateModalOpen = ref(false)
const cateFormOpen = ref(false)
const cateOp = ref('create')
const cateModId = ref(null)
const cateSubmitting = ref(false)

const openCategoryModal = () => {
  cateModalOpen.value = true
  getCategoryList()
}

const getCategoryList = async () => {
  cateLoading.value = true
  try {
    const res = await httpGET(api.category)
    cateListData.value = res.data
  } catch {
    message.error('分类数据加载失败')
  } finally {
    cateLoading.value = false
  }
}

const cateCreate = () => {
  clearItem(categoryForm)
  cateOp.value = 'create'
  cateFormOpen.value = true
}

const cateModify = (index) => {
  clearItem(categoryForm)
  assignSame(cateListData.value[cateGetIndex(index)], categoryForm)
  cateOp.value = 'modify'
  cateModId.value = cateGetIndex(index)
  cateFormOpen.value = true
}

const cateSubmit = () => {
  cateSubmitting.value = true
  const done = () => {
    getCategoryList()
    getCategory()  // 同步更新主机表格中的分类下拉选项
    cateFormOpen.value = false
    cateSubmitting.value = false
  }
  if (cateOp.value === 'create') {
    httpPOST(api.category, categoryForm).then(done).catch(() => { cateSubmitting.value = false })
  } else {
    httpPUT(api.category, cateListData.value[cateModId.value].id, categoryForm).then(done).catch(() => { cateSubmitting.value = false })
  }
}

const cateDelete = (index) => {
  httpDELETE(api.category, cateListData.value[cateGetIndex(index)].id).then(() => {
    getCategoryList()
    getCategory()  // 同步更新主机表格中的分类下拉选项
  })
}

onMounted(() => {
  getDetails()
  getCategory()
})
</script>

<style scoped>
.category-select-btn {
  width: 120px;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  overflow: hidden;
}
.category-select-btn :deep(span) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.category-select-btn :deep(.anticon) {
  flex-shrink: 0;
  margin-left: auto;
  font-size: 10px;
  color: var(--color-text-quaternary);
}

/* 状态圆点指示器 */
.status-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-synced { background-color: #52c41a; }
.status-new { background-color: #ff4d4f; }
.status-modified { background-color: #faad14; }

/* 行状态高亮 */
:deep(.row-new) td {
  background: var(--color-row-new) !important;
}

:deep(.row-modified) td {
  background: var(--color-row-modified) !important;
}
</style>
