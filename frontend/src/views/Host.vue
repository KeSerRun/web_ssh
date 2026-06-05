<template>
  <!-- 工具栏 -->
  <div class="page-toolbar">
    <a-space :size="12">
      <a-button @click="createItem" type="primary">
        <PlusOutlined /> 新建主机
      </a-button>
      <a-button @click="updateAll">
        <CloudUploadOutlined /> 批量同步
      </a-button>
    </a-space>
  </div>

  <!-- 加载状态 -->
  <a-spin :spinning="loading" tip="正在加载数据...">
    <!-- 空数据提示 -->
    <a-empty
      v-if="!loading && listData.value.length === 0"
      description="暂无主机数据"
    />

    <!-- 数据表格 -->
    <a-table
      v-else
      :columns="detailsColumns"
      :data-source="pageData.value"
      :pagination="pagination"
      :row-class-name="rowClassName"
      size="middle"
      @change="handlePageChange"
    >
      <template #bodyCell="{ column, index }">
        <!-- 操作列 -->
        <template v-if="column.key === 'action'">
          <a-space :size="4">
            <a-popconfirm
              v-if="pageData.value.length"
              title="确定删除？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="deleteItem(index)"
            >
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
            <a-button type="link" size="small" @click="insertItem(index)">插入</a-button>
            <a-button type="link" size="small" @click="updateItem(index)">保存</a-button>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { httpGET, httpPOST, httpPUT, httpDELETE } from '@/http'
import { usePagination } from '@/utils/paginatior'
import { detailsColumns } from '@/utils/table'
import { detailsForm } from '@/utils/form'
import { api } from '@/settings'
import { assignSame, clearItem } from '@/utils/copy'
import { message } from 'ant-design-vue'
import { PlusOutlined, CloudUploadOutlined, DownOutlined } from '@ant-design/icons-vue'

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

const updateItem = (index) => {
  index = getindex(index)
  let payload = assignSame(listData.value[index], detailsForm)
  delete payload['update_status']
  delete payload['id']
  if (listData.value[index].update_status == 2) {
    httpPOST(api.hosts, payload).then(() => { listData.value[index].update_status = 1 })
  } else if (listData.value[index].update_status == 3) {
    httpPUT(api.hosts, listData.value[index].id, payload).then(() => { listData.value[index].update_status = 1 })
  }
}

const updateAll = () => {
  for (let index = 0; index < listData.value.length; index++) {
    updateItem(index)
  }
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
  listData.value.splice(0, 0, structuredClone(detailsForm))
}

const insertItem = index => {
  clearItem(detailsForm)
  index = getindex(index)
  detailsForm.id = `${count.value + 1}`
  detailsForm.update_status = 2
  listData.value.splice(index + 1, 0, structuredClone(detailsForm))
}

const rowClassName = (record) => {
  if (record.update_status == 2) return 'row-new'
  if (record.update_status == 3) return 'row-modified'
  return ''
}

onMounted(() => {
  getDetails()
  getCategory()
})
</script>

<style scoped>
.page-toolbar {
  margin-bottom: var(--space-md);
}

.category-select-btn {
  min-width: 100px;
  text-align: left;
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
  background: #fff2f0 !important;
}

:deep(.row-modified) td {
  background: #fffbe6 !important;
}
</style>
