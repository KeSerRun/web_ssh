<template>
  <!-- 工具栏区 -->
  <div class="terminal-toolbar">
    <a-space :size="12">
      <!-- 主机选择下拉 -->
      <a-dropdown :trigger="['click']" placement="bottomLeft" @openChange="onDropdownOpen">
        <a-button class="host-select-btn">
          <CloudServerOutlined />
          <span class="host-select-label">{{ selectedHost }}</span>
          <DownOutlined />
        </a-button>
        <template #overlay>
          <a-menu class="host-select-menu">
            <a-menu-item
              v-for="id in host_ids"
              :key="id"
              @click="onClickSelect(id)"
            >
              <a-tag
                :color="getHostStatus(id) === 'online' ? 'green' : getHostStatus(id) === 'probing' ? 'processing' : 'default'"
                class="host-status-tag"
              >
                {{ getHostStatus(id) === 'online' ? '在线' : getHostStatus(id) === 'probing' ? '检测中...' : '离线' }}
              </a-tag>
              {{ getHostName(id) }}
            </a-menu-item>
            <a-menu-divider v-if="host_ids.length" />
            <a-menu-item disabled v-if="!host_ids.length">
              暂无可用的主机
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>

      <!-- 连接按钮 -->
      <a-button @click="linkToHost" type="primary" :disabled="!selectedHostId">
        <LinkOutlined /> 连接主机
      </a-button>

      <!-- 断开按钮（仅连接后可见） -->
      <a-button v-if="connected" @click="disconnectHost" danger>
        <DisconnectOutlined /> 断开连接
      </a-button>

      <!-- 清屏按钮 -->
      <a-button @click="clearTerminal">
        <ClearOutlined /> 清屏
      </a-button>

      <!-- 文件管理器（仅连接后可用） -->
      <FileManager v-if="connected" :dev_id="selectedHostId" />
    </a-space>
  </div>

  <!-- 终端窗口 -->
  <div class="terminal-wrapper">
    <div class="terminal-titlebar">
      <div class="titlebar-dots">
        <span class="dot dot-red"></span>
        <span class="dot dot-yellow"></span>
        <span class="dot dot-green"></span>
      </div>
      <span class="titlebar-text">
        {{ selectedHostId ? `${getHostName(selectedHostId)} — SSH Terminal` : '未连接' }}
      </span>
    </div>
    <div class="terminal-body">
      <div ref="terminalEl" class="terminal"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, onActivated } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import settings from '@/settings'
import { getUserInfo } from '@/utils/token'
import { httpGET, httpPOST } from '@/http'
import { api } from '@/settings'
import FileManager from '@/components/FileManager.vue'
import { message } from 'ant-design-vue'
import {
  CloudServerOutlined, DownOutlined, LinkOutlined, DisconnectOutlined, ClearOutlined,
} from '@ant-design/icons-vue'

// keep-alive 需要组件名来识别缓存目标
defineOptions({ name: 'Home' })

let term
let fitAddon
let socket
let resizeObserver

const terminalEl = ref(null)
const selectedHost = ref('请选择主机')
const selectedHostId = ref()
const host = ref()
const host_ids = ref([])
const connected = ref(false)

const getHostName = (id) => {
  return host.value?.find(item => item.id === id)?.name || ''
}

const getHostStatus = (id) => {
  const item = host.value?.find(h => h.id === id)
  if (item?._probing) return 'probing'
  return item?.status === 1 ? 'online' : 'offline'
}

const getDetails = () => {
  return httpGET(api.hosts).then(res => {
    // 保留本地探测状态，只更新服务端数据
    const oldMap = {}
    host.value?.forEach(h => { oldMap[h.id] = h._probing })
    host.value = (res.data || []).map(h => {
      h._probing = oldMap[h.id] || false
      return h
    })
  })
}

const getHostIds = () => {
  return getUserInfo().then(res => {
    host_ids.value = res.data.hosts
  })
}

const onClickSelect = (key) => {
  selectedHostId.value = key
  selectedHost.value = getHostName(key)
}

// 是否正在批量探测中
let probingAll = false

// 下拉菜单展开时，批量探测所有主机在线状态
const onDropdownOpen = async (open) => {
  if (!open) return          // 关闭时忽略
  if (probingAll) return     // 正在探测中，防重入
  if (!host_ids.value.length) return

  probingAll = true

  // 标记所有主机为探测中
  const targets = host_ids.value
    .map(id => host.value?.find(h => h.id === id))
    .filter(Boolean)

  targets.forEach(h => { h._probing = true })

  // 并行探测所有主机
  const results = await Promise.allSettled(
    targets.map(h =>
      httpPOST(api.hostProbe(h.id), {}, false).then(res => {
        h.status = res.data.data.status   // APIResponse 包裹格式: {code, message, data: {status, status_text}}
      }).catch(() => {
        h.status = 0
      })
    )
  )

  // 清除探测状态
  targets.forEach(h => { h._probing = false })
  probingAll = false
}

const linkToHost = () => {
  if (!selectedHostId.value) {
    message.warning('请先选择一台主机')
    return
  }
  socket?.close()
  initSocket(selectedHostId.value)
}

const disconnectHost = () => {
  socket?.close()
  connected.value = false
  term?.writeln('\r\n\x1b[33m[ 手动断开 ]\x1b[0m\r\n')
}

const clearTerminal = () => {
  term?.clear()
}

/* ========== WebSocket 连接 ========== */
function initSocket(host_id) {
  let token = sessionStorage.token || localStorage.token
  socket = new WebSocket(
    `${settings.host.replace('http', 'ws')}/ws/ssh/${host_id}/`,
    ['jwt', token]
  )
  socket.onopen = () => {
    connected.value = true
    term.writeln('\r\n\x1b[32m[ 已连接 ]\x1b[0m\r\n')
    getDetails()  // 连接成功后刷新主机列表，更新在线状态
  }
  socket.onmessage = ({ data }) => term.write(atob(data))
  socket.onclose = () => {
    connected.value = false
    term.writeln('\r\n\x1b[31m[ 已断开 ]\x1b[0m\r\n')
    getDetails()
  }
  socket.onerror = () => {
    connected.value = false
    term.writeln('\r\n\x1b[31m[ 连接错误 ]\x1b[0m\r\n')
    getDetails()
  }
}

/* ========== xterm 终端 ========== */
function initTerm() {
  term = new Terminal({
    fontSize: 14,
    fontFamily: '"Cascadia Code", "Fira Code", Consolas, monospace',
    cursorBlink: true,
    cursorStyle: 'bar',
    theme: {
      background: '#1a1e2b',
      foreground: '#e0e0e0',
      cursor: '#4096ff',
      selectionBackground: 'rgba(64, 150, 255, 0.3)',
      black: '#1a1e2b',
      red: '#f07178',
      green: '#a6e22e',
      yellow: '#ffd866',
      blue: '#4096ff',
      magenta: '#ab9df2',
      cyan: '#78dce8',
      white: '#e0e0e0',
    },
    allowProposedApi: true,
  })

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalEl.value)
  fitAddon.fit()

  let cmd = ''
  term.onData(raw => {
    const code = raw.charCodeAt(0)
    if (code === 13) {
      // 回车
      term.writeln('')
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(btoa(cmd + '\n'))
      }
      cmd = ''
      return
    } else if (code === 127) {
      // 退格
      if (cmd.length > 0) {
        cmd = cmd.slice(0, -1)
        term.write('\b \b')
      }
      return
    } else {
      term.write(raw)
      cmd += raw
    }
  })

  // 监听窗口大小变化，终端自适应
  resizeObserver = new ResizeObserver(() => {
    fitAddon?.fit()
  })
  resizeObserver.observe(terminalEl.value)
}

onMounted(() => {
  initTerm()
  getHostIds()
  getDetails()
})

// keep-alive 缓存后切回时：刷新主机列表 + 自适应终端（保持连接状态）
onActivated(() => {
  getHostIds()
  getDetails()
  fitAddon?.fit()
})

onBeforeUnmount(() => {
  socket?.close()
  term?.dispose()
  fitAddon?.dispose()
  resizeObserver?.disconnect()
})
</script>

<style scoped>
/* ========== 工具栏 ========== */
.terminal-toolbar {
  margin-bottom: var(--space-md);
}

@media (max-width: 1000px) {
  .terminal-toolbar :deep(.ant-space) {
    flex-wrap: wrap;
    gap: var(--space-sm) !important;
  }
  .terminal-body .terminal {
    height: calc(60vh - 100px) !important;
    min-height: 250px !important;
  }
}

.host-select-btn {
  min-width: 160px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.host-select-label {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.host-select-menu {
  min-width: 200px;
  max-height: 300px;
  overflow-y: auto;
}

.host-status-tag {
  margin-right: var(--space-sm);
  font-size: var(--font-size-sm);
  line-height: 18px;
  transition: all var(--transition-base);
}


/* ========== 终端窗口 ========== */
.terminal-wrapper {
  width: 100%;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  border: 1px solid #2a2e3a;
}

/* 标题栏（模拟 mac 窗口） */
.terminal-titlebar {
  display: flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--space-md);
  background: #1a1e2b;
  user-select: none;
}

.titlebar-dots {
  display: flex;
  gap: 6px;
  margin-right: var(--space-md);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot-red { background: #ff5f57; }
.dot-yellow { background: #febc2e; }
.dot-green { background: #28c840; }

.titlebar-text {
  font-size: var(--font-size-sm);
  color: #999;
  flex: 1;
  text-align: center;
  margin-right: 46px; /* 平衡左侧圆点宽度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 终端主体 */
.terminal-body {
  background: #1a1e2b;
  padding: var(--space-sm);
}

.terminal {
  width: 100%;
  height: calc(80vh - 140px);
  min-height: 400px;
}
</style>
