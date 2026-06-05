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
        <CloudServerOutlined class="sider-logo-icon" />
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
          v-for="item in base_list"
          :key="item.key"
          class="sider-menu-item"
        >
          <router-link :to="`/base/${item.link}`" class="menu-link">
            <component :is="$icons[item.icon]" />
            <span class="menu-label">{{ item.name }}</span>
          </router-link>
        </a-menu-item>
      </a-menu>

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
          <span class="header-title">远程终端管理系统</span>
        </div>
        <div class="header-right">
          <a-space :size="12">
            <a-avatar :size="32" class="header-avatar">
              <template #icon><UserOutlined /></template>
            </a-avatar>
            <span class="header-username">{{ authStore.username }}</span>
            <a-button type="text" class="header-logout-btn" @click="logout">
              <LogoutOutlined />
              <span>退出</span>
            </a-button>
          </a-space>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="app-content">
        <!-- 面包屑 -->
        <div class="content-breadcrumb">
          <a-breadcrumb>
            <a-breadcrumb-item>
              <HomeOutlined />
            </a-breadcrumb-item>
            <a-breadcrumb-item>{{ logoText }}</a-breadcrumb-item>
            <a-breadcrumb-item v-if="selectedKeys.length">
              {{ base_list[selectedKeys[0] - 1]?.name }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <!-- 页面内容 -->
        <div class="content-body">
          <router-view v-slot="{ Component }">
            <transition name="page-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </a-layout-content>

      <!-- 底部 Footer -->
      <a-layout-footer class="app-footer">
        Web SSH Management System &copy; {{ new Date().getFullYear() }}
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>


<script setup>
import { ref, watch } from 'vue'
import { createVNode } from 'vue'
import { Modal } from 'ant-design-vue'
import {
  ExclamationCircleOutlined, CloudServerOutlined,
  UserOutlined, LogoutOutlined, HomeOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined,
} from '@ant-design/icons-vue'
import router from '@/router/index.js'
import { base_list } from '@/utils/list'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const collapsed = ref(false)
const logoText = ref('Web SSH')
const selectedKeys = ref([1])

// 持久化当前选中的菜单项
if (sessionStorage.getItem('selectedKeys')) {
  selectedKeys.value = [parseInt(sessionStorage.getItem('selectedKeys'))]
}

watch(selectedKeys, (val) => {
  sessionStorage.setItem('selectedKeys', String(val[0]))
})

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
  min-width: 1200px;
}

/* ========== 侧边栏 ========== */
.app-sider {
  position: fixed !important;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  transition: padding var(--transition-base);
  overflow: hidden;
  white-space: nowrap;
}

.sider-logo.collapsed {
  padding: 0 var(--space-sm);
  justify-content: center;
}

.sider-logo-icon {
  font-size: 24px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.sider-logo-text {
  margin-left: var(--space-sm);
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  font-style: italic;
  font-family: 'Times New Roman', serif;
}

/* ---- 菜单 ---- */
.sider-menu {
  flex: 1;
  border-right: none !important;
  padding-top: var(--space-sm);
}

.sider-menu-item {
  margin: 2px var(--space-sm);
  border-radius: var(--radius-md) !important;
  overflow: hidden;
}

.menu-link {
  display: flex;
  align-items: center;
  color: inherit;
  width: 100%;
}

.menu-label {
  margin-left: var(--space-sm);
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
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  transition: all var(--transition-fast);
}

.sider-collapse-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.06);
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
  line-height: var(--header-height);
  padding: 0 var(--space-lg);
  background: #fff !important;
  box-shadow: var(--shadow-sm);
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-right {
  display: flex;
  align-items: center;
}

.header-avatar {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
}

.header-username {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-logout-btn {
  color: var(--color-text-tertiary);
}

.header-logout-btn:hover {
  color: var(--color-error);
}

/* ========== 内容区 ========== */
.app-content {
  padding: 0 var(--space-lg);
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.content-breadcrumb {
  padding: var(--space-md) 0;
}

.content-body {
  background: var(--color-bg-white);
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  min-height: 400px;
  box-shadow: var(--shadow-sm);
}

/* ========== Footer ========== */
.app-footer {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  padding: var(--space-md);
  height: var(--footer-height);
  line-height: 1;
}
</style>
