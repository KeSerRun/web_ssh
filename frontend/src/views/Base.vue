<template>
  <a-layout class="app-layout">
    <!-- ==================== 侧边栏 ==================== -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      class="app-sider"
      :trigger="null"
    >
      <!-- Logo 品牌区 -->
      <div class="sider-logo" :class="{ collapsed: collapsed }">
        <img src="@/static/images/logo.svg" class="sider-logo-img" alt="logo" />
        <span v-show="!collapsed" class="sider-logo-text">Web SSH</span>
      </div>

      <!-- 导航菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        class="sider-menu"
      >
        <a-menu-item
          v-for="item in visibleMenu"
          :key="item.key"
          class="sider-menu-item"
        >
          <router-link :to="`/base/${item.link}`" class="menu-link">
            <component :is="$icons[item.icon]" />
            <span>{{ item.name }}</span>
          </router-link>
        </a-menu-item>
      </a-menu>

      <!-- 底部用户信息 -->
      <div v-if="!collapsed" class="sider-user">
        <a-avatar :size="28" :src="userAvatar" :style="{ background: userAvatar ? undefined : avatarBg }" class="sider-user-avatar">
          <template #icon><UserOutlined /></template>
        </a-avatar>
        <div class="sider-user-info">
          <div class="sider-user-name">{{ authStore.username }}</div>
          <div class="sider-user-role">{{ authStore.isSuperuser ? '超级管理员' : authStore.isStaff ? '管理员' : '普通用户' }}</div>
        </div>
      </div>

      <!-- 底部折叠按钮 -->
      <div class="sider-collapse-btn" @click="collapsed = !collapsed">
        <MenuFoldOutlined v-if="!collapsed" />
        <MenuUnfoldOutlined v-else />
      </div>
    </a-layout-sider>

    <!-- ==================== 右侧主体 ==================== -->
    <a-layout class="app-main" :style="{ marginLeft: collapsed ? '80px' : '200px' }">
      <!-- 顶部 Header -->
      <a-layout-header class="app-header">
        <div class="header-left">
          <div class="header-brand">
            <CloudServerOutlined class="header-brand-icon" />
            <span class="header-title">远程终端管理系统</span>
          </div>
        </div>
        <div class="header-right">
          <a-space :size="20">
            <!-- 用户下拉 -->
            <a-dropdown placement="bottomRight">
              <div class="header-user-trigger">
                <a-avatar :size="34" :src="userAvatar" :style="{ background: userAvatar ? undefined : avatarBg }" class="header-avatar">
                  <template #icon><UserOutlined /></template>
                </a-avatar>
                <div class="header-user-meta">
                  <span class="header-username">{{ authStore.username }}</span>
                  <span class="header-user-role">
                    {{ authStore.isSuperuser ? '超级管理员' : authStore.isStaff ? '管理员' : '普通用户' }}
                  </span>
                </div>
                <DownOutlined class="header-user-arrow" />
              </div>
              <template #overlay>
                <a-menu class="header-user-menu">
                  <a-menu-item key="profile" disabled>
                    <div class="user-menu-header">
                      <a-avatar :size="44" :src="userAvatar" :style="{ background: userAvatar ? undefined : avatarBg }" class="user-menu-avatar">
                        <template #icon><UserOutlined /></template>
                      </a-avatar>
                      <div>
                        <div class="user-menu-name">{{ authStore.username }}</div>
                        <div class="user-menu-email">{{ authStore.username }}@web-ssh</div>
                      </div>
                    </div>
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="avatar" @click="openAvatarModal">
                    <CameraOutlined /> 修改头像
                  </a-menu-item>
                  <a-menu-item key="logout" @click="logout">
                    <LogoutOutlined /> 退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="app-content">
        <!-- 面包屑 -->
        <div class="content-breadcrumb">
          <a-breadcrumb>
            <a-breadcrumb-item>
              <a @click="goHome"><HomeOutlined /></a>
            </a-breadcrumb-item>
            <a-breadcrumb-item>
              <a @click="goHome">{{ logoText }}</a>
            </a-breadcrumb-item>
            <a-breadcrumb-item v-if="selectedKeys.length">
              {{ base_list.find(i => i.key === selectedKeys[0])?.name }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <!-- 页面内容 -->
        <div class="content-body">
          <router-view v-slot="{ Component }">
            <keep-alive include="Home">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </div>
      </a-layout-content>

      <!-- 底部 Footer -->
      <a-layout-footer class="app-footer">
        Web SSH Management System &copy; {{ new Date().getFullYear() }}
      </a-layout-footer>
    </a-layout>

    <!-- 修改头像弹窗 -->
    <a-modal
      v-model:open="avatarModalOpen"
      title="修改头像"
      @ok="uploadAvatar"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="avatarUploading"
      width="400px"
    >
      <div style="text-align: center; padding: var(--space-lg) 0;">
        <a-avatar :size="80" :src="avatarPreview" :style="{ marginBottom: 'var(--space-md)', background: avatarPreview ? undefined : avatarBg }">
          <template #icon><UserOutlined /></template>
        </a-avatar>
        <div>
          <a-upload
            :max-count="1"
            :before-upload="beforeAvatarUpload"
            :show-upload-list="false"
            accept="image/*"
          >
            <a-button>
              <UploadOutlined /> 选择图片
            </a-button>
          </a-upload>
          <p style="margin-top: var(--space-sm); font-size: var(--font-size-sm); color: var(--color-text-tertiary);">
            支持 JPG、PNG 格式，建议尺寸 200×200
          </p>
        </div>
      </div>
    </a-modal>
  </a-layout>
</template>


<script setup>
import { ref, watch, computed, onMounted, reactive } from 'vue'
import { createVNode } from 'vue'
import { Modal, message } from 'ant-design-vue'
import {
  ExclamationCircleOutlined, CloudServerOutlined,
  UserOutlined, LogoutOutlined, HomeOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined, DownOutlined,
  CameraOutlined, UploadOutlined,
} from '@ant-design/icons-vue'
import router from '@/router/index.js'
import { base_list } from '@/utils/list'
import { useAuthStore } from '@/stores/auth'
import { httpGET, httpPOST } from '@/http'
import { api } from '@/settings'
import settings from '@/settings'

const authStore = useAuthStore()
const collapsed = ref(window.innerWidth < 1000)
const logoText = ref('Web SSH')
const selectedKeys = ref([1])

// ≤ 1000px 自动折叠侧栏
window.addEventListener('resize', () => {
  collapsed.value = window.innerWidth < 1000
})

// ==================== 头像 ====================
const userAvatar = ref('')
const avatarModalOpen = ref(false)
const avatarUploading = ref(false)
const avatarPreview = ref('')
const avatarFile = ref(null)

/** 根据角色返回默认头像背景色 */
const avatarBg = computed(() => {
  if (authStore.isSuperuser) return 'linear-gradient(135deg, #fa8c16, #ffa940)'
  if (authStore.isStaff) return 'linear-gradient(135deg, #1677ff, #4096ff)'
  return 'linear-gradient(135deg, #8c8c8c, #bfbfbf)'
})

/** 获取当前用户头像 */
const fetchUserAvatar = async () => {
  if (!authStore.userId) return
  try {
    const res = await httpGET(api.users + authStore.userId + '/')
    const avatar = res.data.avatar
    if (avatar) {
      userAvatar.value = avatar.startsWith('http') ? avatar : settings.host + avatar
      avatarPreview.value = userAvatar.value
    }
  } catch { /* ignore */ }
}

/** 打开修改头像弹窗 */
const openAvatarModal = () => {
  avatarFile.value = null
  avatarPreview.value = userAvatar.value
  avatarModalOpen.value = true
}

/** 选择文件后预览 */
const beforeAvatarUpload = (file) => {
  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
  return false
}

/** 上传头像 */
const uploadAvatar = () => {
  if (!avatarFile.value) {
    avatarModalOpen.value = false
    return
  }
  if (!authStore.userId) {
    message.error('无法获取用户信息，请重新登录')
    return
  }

  avatarUploading.value = true
  const fd = new FormData()
  fd.append('avatar', avatarFile.value)

  httpPOST(api.users + authStore.userId + '/avatar/', fd, false).then(() => {
    avatarModalOpen.value = false
    userAvatar.value = avatarPreview.value
    // 清理临时 URL
    if (avatarPreview.value.startsWith('blob:')) {
      URL.revokeObjectURL(avatarPreview.value)
    }
  }).catch(err => {
    const msg = err?.response?.data?.message || err?.response?.data?.detail || '头像上传失败'
    message.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }).finally(() => {
    avatarUploading.value = false
  })
}

// 根据用户权限过滤侧边栏菜单
const visibleMenu = computed(() =>
  base_list.filter(item => !item.adminOnly || authStore.isStaff || authStore.isSuperuser)
)

// 挂载时获取用户权限和头像
onMounted(() => {
  authStore.fetchPermissions()
  fetchUserAvatar()
})

// 持久化当前选中的菜单项
if (sessionStorage.getItem('selectedKeys')) {
  selectedKeys.value = [parseInt(sessionStorage.getItem('selectedKeys'))]
}

watch(selectedKeys, (val) => {
  sessionStorage.setItem('selectedKeys', String(val[0]))
})

// 面包屑点击返回主页
const goHome = () => {
  selectedKeys.value = [1]
  router.push({ name: 'Home' })
}

// 退出登录
const logout = () => {
  Modal.confirm({
    title: '退出确认',
    icon: createVNode(ExclamationCircleOutlined),
    content: '确定要退出登录吗？',
    okText: '确定退出',
    cancelText: '取消',
    centered: true,
    onOk() {
      authStore.logout()
      router.replace('/login')
    }
  })
}
</script>


<style scoped>
/* ========== 整体布局 ========== */
.app-layout {
  min-height: 100vh;
}

/* ========== 侧边栏 ========== */
.app-sider {
  position: fixed !important;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  overflow: hidden;
  box-shadow: 2px 0 16px rgba(0, 0, 0, 0.3);
}

.app-sider :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
}

/* ---- Logo ---- */
.sider-logo {
  display: flex;
  align-items: center;
  height: var(--header-height);
  padding: 0 var(--space-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all var(--transition-base);
  overflow: hidden;
  white-space: nowrap;
}

.sider-logo.collapsed {
  padding: 0;
  justify-content: center;
}

.sider-logo-img {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  transition: all var(--transition-base);
}

.sider-logo.collapsed .sider-logo-img {
  width: 32px;
  height: 32px;
}

.sider-logo-text {
  margin-left: var(--space-sm);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: #fff;
  letter-spacing: 2px;
}

/* ---- 菜单 ---- */
.sider-menu {
  flex: 1;
  border-right: none !important;
  padding: var(--space-sm);
}

/* 覆盖 Ant Design 暗色菜单默认背景 */
.sider-menu :deep(.ant-menu) {
  background: transparent;
}

.sider-menu-item {
  margin-bottom: 2px !important;
  border-radius: var(--radius-md) !important;
  overflow: visible !important;
  transition: all var(--transition-base) !important;
}

.sider-menu-item :deep(.ant-menu-title-content) {
  transition: opacity var(--transition-base);
}

/* 菜单项 hover：轻微背景 + 图标放大 */
.sider-menu-item:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

.sider-menu-item:hover :deep(.anticon) {
  transform: scale(1.1);
}

/* 菜单项选中态：蓝色背景 + 左侧指示点 */
.sider-menu-item.ant-menu-item-selected {
  background: linear-gradient(90deg, rgba(22, 119, 255, 0.25), rgba(22, 119, 255, 0.10)) !important;
  box-shadow: inset 0 0 0 1px rgba(22, 119, 255, 0.2);
}

.sider-menu-item.ant-menu-item-selected::after {
  display: none !important; /* 禁用 Ant Design 默认的右侧边框 */
}

.sider-menu-item.ant-menu-item-selected .menu-link {
  color: #fff;
}

.menu-link {
  display: flex;
  align-items: center;
  color: var(--sidebar-text);
  width: 100%;
  gap: var(--space-sm);
  font-size: var(--font-size-base);
  padding: 2px 0;
  transition: color var(--transition-fast);
}

.menu-link:hover {
  color: #fff;
}

/* 侧栏图标 */
.menu-link :deep(.anticon) {
  font-size: 18px;
  transition: transform var(--transition-fast);
}

/* ---- 侧栏用户信息 ---- */
.sider-user {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sider-user-avatar {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
  flex-shrink: 0;
}

.sider-user-name {
  font-size: var(--font-size-sm);
  color: #fff;
  font-weight: 500;
  line-height: 1.3;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sider-user-role {
  font-size: 11px;
  color: var(--sidebar-text);
  line-height: 1.2;
}

/* ---- 折叠按钮 ---- */
.sider-collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--sidebar-text);
  font-size: var(--font-size-md);
  cursor: pointer;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  transition: all var(--transition-base);
}

.sider-collapse-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

/* 折叠按钮图标旋转动画 */
.sider-collapse-btn :deep(.anticon) {
  transition: transform var(--transition-base);
}

/* ========== 主区域 ========== */
.app-main {
  transition: margin-left var(--transition-base);
}

/* ========== Header ========== */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 var(--space-xl);
  background: #fff !important;
  box-shadow: 0 1px 0 var(--color-border-light), var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 10;
}

/* Header 底部渐变装饰线（极淡） */
.app-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-hover), transparent 70%);
  opacity: 0.15;
}

/* ---- Header 左侧品牌 ---- */
.header-left {
  display: flex;
  align-items: center;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.header-brand-icon {
  font-size: 20px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.header-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 窄屏隐藏标题文字，只留图标；用户区只显示头像 */
@media (max-width: 700px) {
  .header-title {
    display: none;
  }
  .header-user-meta {
    display: none;
  }
  .header-user-arrow {
    display: none;
  }
}

/* ---- Header 右侧用户区 ---- */
.header-right {
  display: flex;
  align-items: center;
}

/* 用户触发区：头像 + 信息 + 箭头 */
.header-user-trigger {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 4px 8px 4px 4px;
  border-radius: 24px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.header-user-trigger:hover {
  background: var(--color-bg-page);
}

.header-avatar {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.2);
  flex-shrink: 0;
}

.header-user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.header-username {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-user-role {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.header-user-arrow {
  font-size: 10px;
  color: var(--color-text-quaternary);
  transition: transform var(--transition-fast);
}

/* ---- 用户下拉菜单 ---- */
.header-user-menu {
  min-width: 220px;
}

.user-menu-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) 0;
  cursor: default;
}

.user-menu-avatar {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
  flex-shrink: 0;
}

.user-menu-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
}

.user-menu-email {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

/* ========== 内容区 ========== */
.app-content {
  padding: 0 var(--space-xl);
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-breadcrumb {
  padding: var(--space-sm) var(--space-md);
  margin-top: var(--space-md);
  margin-bottom: var(--space-md);
  background: var(--color-bg-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

/* 面包屑字体 & 间距 */
.content-breadcrumb :deep(.ant-breadcrumb) {
  font-size: var(--font-size-sm);
  line-height: 28px;
}

.content-breadcrumb :deep(.ant-breadcrumb-link) {
  transition: color var(--transition-fast);
  font-weight: 500;
}

.content-breadcrumb :deep(.ant-breadcrumb-link a) {
  color: var(--color-text-secondary);
}

.content-breadcrumb :deep(.ant-breadcrumb-link a:hover) {
  color: var(--color-primary);
}

/* 当前页（不可点击） */
.content-breadcrumb :deep(.ant-breadcrumb-separator) {
  color: var(--color-text-quaternary);
  margin: 0 var(--space-xs);
}

/* 最后一级灰色表示当前页 */
.content-breadcrumb :deep(.ant-breadcrumb-item:last-child .ant-breadcrumb-link) {
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.content-body {
  background: var(--color-bg-white);
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  min-height: calc(100vh - var(--header-height) - var(--footer-height) - 128px);
  box-shadow: var(--shadow-md);
}

/* ========== Footer ========== */
.app-footer {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-quaternary);
  padding: var(--space-md);
  height: var(--footer-height);
  line-height: 1;
}
</style>
