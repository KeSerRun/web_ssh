<template>
  <a-button type="primary" @click="showDrawer" :disabled="!props.dev_id">
    <FolderOpenOutlined /> 文件管理器
  </a-button>

  <a-drawer
    v-model:open="open"
    title="文件管理器"
    placement="right"
    :width="600"
    :z-index="1001"
    getContainer="body"
  >
    <!-- 工具栏 -->
    <div class="fm-toolbar">
      <a-space :size="8" wrap>
        <a-button @click="go_back" size="small">
          <ArrowLeftOutlined /> 上级目录
        </a-button>
        <a-button @click="new_folder" size="small">
          <FolderAddOutlined /> 新建文件夹
        </a-button>
        <a-button @click="upload_file" size="small">
          <UploadOutlined /> 上传文件
        </a-button>
      </a-space>
    </div>

    <a-divider style="margin: 12px 0;" />

    <!-- 路径栏 -->
    <div class="fm-pathbar">
      <span class="fm-path">
        <HomeOutlined /> {{ path }}
      </span>
      <span class="fm-toggle">
        <a-tooltip title="显示/隐藏隐藏文件">
          <a-switch v-model:checked="hide" size="small" @change="dir(path)" />
        </a-tooltip>
      </span>
    </div>

    <!-- 文件列表 -->
    <a-table
      :columns="dictColumns"
      :data-source="dict"
      :custom-row="customRow"
      size="small"
      :pagination="false"
      :loading="loading"
      class="fm-table"
    >
      <template #bodyCell="{ column, text }">
        <template v-if="column.key === 'perm'">
          <component :is="iconMap[text[0]] || FileOutlined" class="fm-icon" />
        </template>
        <template v-else>
          {{ text }}
        </template>
      </template>
    </a-table>

    <!-- 右键菜单 -->
    <a-dropdown
      v-model:open="menuVisible"
      :trigger="['contextmenu']"
      :getPopupContainer="trigger => trigger.parentNode"
    >
      <div ref="menuDom" class="fm-context-trigger"></div>
      <template #overlay>
        <a-menu mode="vertical" @click="onMenuClick" class="fm-context-menu">
          <a-menu-item key="open">
            <FolderOpenOutlined /> 打开
          </a-menu-item>
          <a-menu-item key="download">
            <DownloadOutlined /> 下载
          </a-menu-item>
          <a-menu-divider />
          <a-menu-item key="delete" danger>
            <DeleteOutlined /> 删除
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>

    <!-- 新建文件夹弹窗 -->
    <a-modal
      v-model:open="setNameVisible"
      title="新建文件夹"
      @ok="setNameOk(path)"
      ok-text="创建"
      cancel-text="取消"
    >
      <a-input v-model:value="setName" placeholder="请输入文件夹名称">
        <template #prefix><FolderOutlined /></template>
      </a-input>
    </a-modal>

    <!-- 上传文件弹窗 -->
    <a-modal
      v-model:open="UploadOpen"
      title="上传文件"
      @ok="UploadOk"
      ok-text="上传"
      cancel-text="取消"
    >
      <FileUpload v-model:fileList="fileList" />
    </a-modal>
  </a-drawer>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { httpPOST, httpFileDownload } from '@/http'
import { parseLs, decodePerm } from '@/utils/list'
import { dictColumns } from '@/utils/table'
import {
  FolderOutlined, FileOutlined, LinkOutlined, HomeOutlined,
  FolderOpenOutlined, ArrowLeftOutlined, FolderAddOutlined,
  UploadOutlined, DownloadOutlined, DeleteOutlined,
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import FileUpload from '@/components/FileUpload.vue'

const props = defineProps({ dev_id: Number })

const open = ref(false)
const setNameVisible = ref(false)

const showDrawer = () => {
  if (props.dev_id) {
    open.value = true
    refresh(path.value)
  } else {
    message.warning('请先选择主机')
  }
}

// 监听 drawer 打开，确保刷新
watch(open, (val) => {
  if (val && props.dev_id) refresh(path.value)
})

const customRow = (record) => {
  return {
    onDblclick: () => go_on(record),
    onContextmenu: (e) => {
      e.preventDefault()
      if (!menuVisible.value) {
        currentRow = record
        showContextmenu(e)
      }
    },
    style: {
      userSelect: 'none',
      cursor: 'pointer',
    },
  }
}

const iconMap = {
  'd': FolderOutlined,
  '-': FileOutlined,
  'l': LinkOutlined,
}

const path = ref('./')
const hide = ref(true)
const dict = ref([])
const loading = ref(false)

const get_back_path = () => {
  let currentPath = path.value
  let back = currentPath.split('/').slice(0, -1).join('/')
  return back || '/'
}

const get_on_path = (folder_name) => {
  let on = path.value + '/' + folder_name
  return on.replace(/\/+/g, '/')
}

const go_back = () => dir(get_back_path())

const go_on = (folder) => {
  const { perm } = folder
  let folderType = decodePerm(perm).type
  if (folderType == 'dir' || folderType == 'link') {
    dir(get_on_path(folder.name))
    menuVisible.value = false
  }
}

const pwd = async (current_path) => {
  let formData = { cmd: 'pwd', args: [] }
  return httpPOST(`/host/${props.dev_id}/file/?path=${current_path}`, formData, false).then(response => {
    if (response.data.code === 200) path.value = response.data.data.output.replace(/\n/g, '')
    return response
  }).catch(error => { throw error })
}

const dir = async (current_path) => {
  loading.value = true
  let formData = { cmd: 'ls', args: hide.value ? ['-l'] : ['-la'] }
  return httpPOST(`/host/${props.dev_id}/file/?path=${current_path}`, formData, false).then(response => {
    if (response.data.code === 200) {
      let raw = response.data.data.output
      path.value = current_path
      dict.value = parseLs(raw)
    } else {
      message.error(response.data.message || '读取目录失败')
    }
    return response
  }).catch(() => {
    message.error('文件列表加载失败，请确认主机已连接')
  }).finally(() => {
    loading.value = false
  })
}

const setName = ref('')

const new_folder = () => { setNameVisible.value = true }

const setNameOk = async (current_path) => {
  let formData = { cmd: 'mkdir', args: [`${setName.value}`] }
  return httpPOST(`/host/${props.dev_id}/file/?path=${current_path}`, formData, false).then(response => {
    dir(path.value)
    setNameVisible.value = false
    return response
  }).catch(error => { throw error })
}

const del_it = async (folder) => {
  const { name } = folder
  return new Promise((resolve, reject) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 "${name}" 吗？此操作不可恢复！`,
      okText: '确定删除',
      okType: 'danger',
      cancelText: '取消',
      centered: true,
      onOk: async () => {
        const formData = { cmd: 'rm', args: ['-rf', `"${name}"`] }
        try {
          const res = await httpPOST(`/host/${props.dev_id}/file/?path=${path.value}`, formData, false)
          message.success(`已删除 ${name}`)
          resolve(res)
          await dir(path.value)
        } catch (e) {
          message.error(`删除失败：${e.message}`)
          reject(e)
        }
      },
      onCancel: () => {
        message.info('已取消删除')
        resolve(false)
      },
    })
  })
}

const fileList = ref([])
const UploadOpen = ref(false)

const upload_file = () => { UploadOpen.value = true }

async function UploadOk() {
  if (fileList.value.length) {
    fileList.value.forEach(file => {
      let formData = new FormData()
      // Ant Design 的 file 对象是封装过的，真正的文件在 originFileObj 里
      formData.append('file', file.originFileObj || file)
      formData.append('path', path.value)
      formData.append('filename', file.name)
      httpPOST(`/host/${props.dev_id}/upload/?path=${path.value}`, formData, false).then(async () => {
        await dir(path.value)
        message.success(`${file.name} 上传成功`)
      }).catch(() => { message.error(`${file.name} 上传失败`) })
    })
    fileList.value = []
  }
}

const refresh = (current_path) => {
  pwd(current_path).then(response => {
    if (response.data.code === 200) dir(path.value)
  })
}

// 右键菜单
const menuVisible = ref(false)
const menuDom = ref()
let currentRow = null
let highlightTr = null

const showContextmenu = (e) => {
  if (highlightTr) highlightTr.classList.remove('row-selected')
  highlightTr = e.currentTarget
  highlightTr.classList.add('row-selected')
  nextTick(() => {
    menuDom.value.style.position = 'fixed'
    menuDom.value.style.left = `${e.clientX + 1}px`
    menuDom.value.style.top = `${e.clientY + 1}px`
    menuVisible.value = true
  })
}

function onMenuClick({ key }) {
  menuVisible.value = false
  if (key === 'open') go_on(currentRow)
  else if (key === 'delete') del_it(currentRow)
  else if (key === 'download') {
    let formData = { path: path.value, filename: currentRow.name }
    httpFileDownload(`/host/${props.dev_id}/download/?path=${path.value}`, formData, false)
      .then(() => message.success('下载成功'))
      .catch(() => message.error('下载失败'))
  }
}

watch(menuVisible, (val) => {
  if (!val && highlightTr) {
    highlightTr.classList.remove('row-selected')
    highlightTr = null
  }
})
</script>

<style scoped>
/* 工具栏 */
.fm-toolbar {
  margin-bottom: 4px;
}

/* 路径栏 */
.fm-pathbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.fm-path {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* 文件表格 */
.fm-table :deep(.ant-table-row) {
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.fm-table :deep(.ant-table-row:hover) td {
  background-color: #fff1b8 !important;
}

.fm-table :deep(tr.row-selected) td {
  background-color: #ffd591 !important;
}

/* 文件类型图标 */
.fm-icon {
  font-size: 16px;
  color: var(--color-primary);
}

/* 右键菜单触发器（隐藏，仅用于定位） */
.fm-context-trigger {
  position: fixed;
  width: 1px;
  height: 1px;
  pointer-events: none;
}

/* 右键菜单项 hover */
:deep(.fm-context-menu .ant-menu-item:hover) {
  background-color: #fff1b8;
}

:deep(.fm-context-menu .ant-menu-item-danger:hover) {
  background-color: #fff2f0;
}
</style>
