<template>
  <div class="allocation-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-icon page-icon--orange"><SwapOutlined /></div>
        <div>
          <h2 class="page-title">资源分配</h2>
          <p class="page-subtitle">将主机资源分配给指定用户，控制访问权限</p>
        </div>
      </div>
      <div class="page-header-right">
        <a-space :size="8">
          <a-button type="primary" @click="selectUser"><UserOutlined /> 选择用户</a-button>
        </a-space>
      </div>
    </div>

    <!-- 用户列表区 -->
    <div class="table-card">
      <a-spin :spinning="loading" tip="正在加载数据...">
        <a-empty
          v-if="!loading && listData.value.length === 0"
          description="请先选择用户"
        />
        <a-table
          v-else
          :columns="userHostColumns"
          :data-source="pageData.value"
          :pagination="pagination"
          :row-key="record => record.id"
          size="middle"
          @change="handlePageChange"
        >
        <template #bodyCell="{ column, index }">
          <template v-if="column.key === 'username' || column.key === 'mobile'">
            <a-input readonly size="small" v-model:value="pageData.value[index][column.key]" />
          </template>
          <template v-else-if="column.key === 'hosts'">
            <a-list
              size="small"
              bordered
              :data-source="getHostNameList(pageData.value[index][column.key])"
              class="host-list"
            >
              <template #renderItem="{ item }">
                <a-list-item class="host-list-item">{{ item }}</a-list-item>
              </template>
            </a-list>
          </template>
          <template v-else>
            <CheckCircleFilled v-if="pageData.value[index][column.key]" style="color: #52c41a; font-size: 16px;" />
            <CloseCircleFilled v-else style="color: #d9d9d9; font-size: 16px;" />
          </template>
        </template>
      </a-table>
    </a-spin>
    </div>

    <!-- 分配操作区 -->
    <div class="transfer-section">
      <div class="table-card" style="padding: var(--space-md) var(--space-lg);">
        <a-space :size="12" style="margin-bottom: var(--space-md);">
          <a-button type="primary" @click="submitUser" :disabled="!listData.value.length" class="ant-btn-color-success">
            <SwapOutlined /> 批量分配
          </a-button>
        </a-space>

        <a-transfer
          v-model:target-keys="targetKeys"
          :data-source="mockData"
          :show-search="true"
          :show-select-all="true"
          :filter-option="(inputValue, item) => item.hostName.includes(inputValue)"
          :titles="['可分配主机', '已分配主机']"
          :operations="['', '']"
          :locale="{ itemUnit: '台', itemsUnit: '台' }"
          @change="onChange"
          :list-style="{ width: '100%', flex: 1, height: '320px' }"
          class="host-transfer"
        >
          <template #children="{
            direction, filteredItems, selectedKeys,
            disabled: listDisabled, onItemSelectAll, onItemSelect,
          }">
            <a-table
              :row-selection="getRowSelection({
                disabled: listDisabled,
                selectedKeys, onItemSelectAll, onItemSelect,
              })"
              :columns="direction === 'left' ? leftColumns : rightColumns"
              :data-source="filteredItems"
              :row-key="record => String(record.key)"
              size="small"
              :style="{ pointerEvents: listDisabled ? 'none' : undefined }"
              :custom-row="({ key, disabled: itemDisabled }) => ({
                onClick: () => {
                  if (itemDisabled || listDisabled) return
                  onItemSelect(key, !selectedKeys.includes(key))
                },
              })"
            />
          </template>
        </a-transfer>
      </div>
    </div>

    <!-- 选择用户弹窗 -->
    <a-modal
      v-model:open="open"
      title="选择用户"
      @ok="selectOk"
      ok-text="确认选择"
      cancel-text="取消"
      width="480px"
      :confirm-loading="false"
    >
      <div class="select-header">
        <a-checkbox
          v-model:checked="state.checkAll"
          :indeterminate="state.indeterminate"
          @change="onCheckAllChange"
        >
          全选
        </a-checkbox>
        <a-input-search
          v-model:value="searchValue"
          placeholder="搜索用户…"
          @search="onSearch"
          allow-clear
          size="small"
          style="width: 180px;"
        />
      </div>
      <a-divider style="margin: var(--space-sm) 0;" />
      <div class="select-list">
        <a-checkbox-group v-model:value="state.checkedList" :options="userOptions" />
        <a-empty v-if="!userOptions.length" description="未找到匹配的用户" :image-style="{ height: '40px' }" />
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { userHostColumns, hostSimpleColumns } from '@/utils/table'
import { usePagination } from '@/utils/paginatior'
import { httpGET, httpPUT } from '@/http'
import { userForm } from '@/utils/form'
import { assignSame, union } from '@/utils/copy'
import { findSimilarStrings } from '@/utils/search'
import { api } from '@/settings'
import { message } from 'ant-design-vue'
import { UserOutlined, SwapOutlined, CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue'

const { listData, pageData, pagination, handlePageChange, loading } = usePagination()
let user = ref([])
let category = ref([])
let hosts = ref([])
const open = ref(false)
const mockData = ref([])
const targetKeys = ref([])
const leftColumns = ref(hostSimpleColumns)
const rightColumns = ref(hostSimpleColumns)
const rightKeys = ref([])

const onChange = nextTargetKeys => {
  rightKeys.value = nextTargetKeys
}

const getRowSelection = ({ disabled, selectedKeys, onItemSelectAll, onItemSelect }) => {
  return {
    getCheckboxProps: item => ({
      disabled: disabled || item.disabled,
    }),
    onSelectAll(selected, selectedRows) {
      const treeSelectedKeys = selectedRows
        .filter(item => !item.disabled)
        .map(({ key }) => key)
      onItemSelectAll(treeSelectedKeys, selected)
    },
    onSelect({ key }, selected) {
      onItemSelect(key, selected)
    },
    selectedRowKeys: selectedKeys,
  }
}

// 选择用户
const selectUser = async () => {
  loading.value = true
  try {
    await getUser()
    state.checkedList = state.checkedAllList = []
    state.checkAll = false
    state.indeterminate = false
    userOptions.value = userTotalOptions.value || []
    searchValue.value = ''
    open.value = true
  } catch {
    message.error('加载用户数据失败')
  } finally {
    loading.value = false
  }
}

const selectOk = () => {
  open.value = false
  user.value = user.value.filter(item => state.checkedList.includes(item['username']))
  listData.value = user.value
  resetMock()
}

// 构建穿梭框数据
const resetMock = () => {
  mockData.value = []
  for (let i = 0; i < hosts.value.length; i++) {
    mockData.value.push({
      key: String(hosts.value[i].id),
      hostName: hosts.value[i].name,
      category: getCategoryName(hosts.value[i].category),
      ip_addr: `${hosts.value[i].username}@${hosts.value[i].ip_addr}:${hosts.value[i].port}`,
    })
  }
}

const getUser = async () => {
  loading.value = true
  try {
    const response = await httpGET(api.users)
    let data = response.data
    user.value = data
    userTotalOptions.value = data.map(item => item['username'])
    userOptions.value = userTotalOptions.value
  } catch {
    message.error('用户数据加载失败')
  } finally {
    loading.value = false
  }
}

const getCategory = () => {
  httpGET(api.category).then(response => { category.value = response.data })
}

const getDetails = () => {
  httpGET(api.hosts).then(response => { hosts.value = response.data })
}

const getHostNameList = (id_list) => {
  return id_list?.map(id => hosts.value.find(item => item.id === id)?.name).filter(Boolean)
}

const getCategoryName = (id) => {
  return category.value.filter(item => item.id === id)[0]?.name
}

const submitUser = () => {
  for (let i = 0; i < listData.value.length; i++) {
    assignSame(user.value[i], userForm)
    let payload = userForm
    payload.hosts = rightKeys.value
    delete payload.password
    httpPUT(api.users, user.value[i].id, payload).then(() => {
      getUser().then(() => {
        user.value = user.value.filter(item => state.checkedList.includes(item['username']))
        listData.value = user.value
      })
    })
  }
}

// 用户搜索选择
const userOptions = ref()
const userTotalOptions = ref()
const searchValue = ref()
const state = reactive({
  checkedList: [],
  checkedAllList: [],
  checkAll: false,
  indeterminate: true,
})

const onCheckAllChange = e => {
  Object.assign(state, {
    checkedList: e.target.checked ? userOptions.value : [],
    indeterminate: false,
  })
}

const onSearch = () => {
  let val = state.checkedList
  state.checkedAllList = union(state.checkedAllList, val)
  state.indeterminate = !!val.length && val.length < userOptions.value.length
  state.checkAll = val.length === userOptions.value.length
  if (!searchValue.value) {
    userOptions.value = userTotalOptions.value
  } else {
    userOptions.value = findSimilarStrings(searchValue.value, userTotalOptions.value)
  }
  state.checkedList = state.checkedAllList
}

watch(
  () => state.checkedList,
  val => {
    state.indeterminate = !!val.length && val.length < userOptions.value.length
    state.checkAll = val.length === userOptions.value.length
  },
)

onMounted(() => {
  listData.value = []
  getCategory()
  getDetails()
})
</script>

<style scoped>
.allocation-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}


/* 主机列表 */
.host-list {
  max-height: 160px;
  min-height: 60px;
  overflow-y: auto;
  border-radius: var(--radius-sm);
}

.host-list-item {
  padding: 2px 8px;
  font-size: var(--font-size-sm);
}

/* 选择用户弹窗 */
.select-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.select-list {
  max-height: 260px;
  overflow-y: auto;
  padding: var(--space-sm) 0;
}
.select-list :deep(.ant-checkbox-wrapper) {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  margin-left: 0 !important;
}
.select-list :deep(.ant-checkbox-wrapper:hover) {
  background: var(--color-primary-bg);
}
.select-list :deep(.ant-checkbox-group) {
  display: flex;
  flex-direction: column;
}
</style>
