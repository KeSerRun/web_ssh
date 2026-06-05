<template>
  <div class="login-page">
    <!-- 背景层 -->
    <div class="login-bg"></div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 标题区 -->
      <div class="login-header">
        <div class="login-logo">
          <CloudServerOutlined />
        </div>
        <h1 class="login-title">Web SSH</h1>
        <p class="login-subtitle">远程终端管理系统</p>
      </div>

      <!-- 表单 -->
      <a-form
        :model="loginForm"
        name="login"
        autocomplete="off"
        :rules="rules"
        @finish="onFinish"
        class="login-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="loginForm.username"
            placeholder="用户名 / 手机号"
            size="large"
            class="login-input"
          >
            <template #prefix>
              <UserOutlined class="input-icon" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="loginForm.password"
            placeholder="请输入密码"
            size="large"
            class="login-input"
          >
            <template #prefix>
              <LockOutlined class="input-icon" />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-form-item name="remember" no-style>
            <a-checkbox v-model:checked="loginForm.remember" class="remember-check">
              记住登录状态
            </a-checkbox>
          </a-form-item>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            class="login-btn"
            :loading="loading"
          >
            登 录
          </a-button>
        </a-form-item>
      </a-form>

      <!-- 跳转注册 -->
      <div class="login-register-link">
        没有账号？
        <router-link to="/register" class="register-link">立即注册</router-link>
      </div>
    </div>

    <!-- 底部版权 -->
    <div class="login-footer">
      <span>Web SSH Management System</span>
    </div>
  </div>
</template>


<script setup>
import { ref } from 'vue'
import { Modal } from 'ant-design-vue'
import { UserOutlined, LockOutlined, CloudServerOutlined } from '@ant-design/icons-vue'
import { loginForm } from '@/utils/form'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const authStore = useAuthStore()
const loading = ref(false)

// 回填上次登录的用户名，并清空密码（防止残留旧密码导致 401）
loginForm.password = ''
if (localStorage.getItem('username')) {
  loginForm.username = localStorage.getItem('username')
}

const onFinish = () => {
  loading.value = true
  authStore.login({
    username: loginForm.username,
    password: loginForm.password,
    remember: loginForm.remember,
  }).then(() => {
    router.push('/base/home')
    console.log('登录成功')
  }).catch(errorInfo => {
    Modal.error({
      title: '登录失败',
      content: '用户名或密码错误，请检查后重试',
      okText: '知道了',
    })
    console.log('登录失败:', errorInfo)
  }).finally(() => {
    loading.value = false
  })
}

// ---------- 表单校验 ----------
const validateUser = async (_rule, value) => {
  if (!value) return Promise.reject('请输入用户名或手机号')
  return Promise.resolve()
}

const validatePass = async (_rule, value) => {
  if (!value) return Promise.reject('请输入密码')
  return Promise.resolve()
}

const rules = {
  username: [{ required: true, validator: validateUser, trigger: 'blur' }],
  password: [{ required: true, validator: validatePass, trigger: 'blur' }],
}
</script>


<style scoped>
/* ========== 页面容器 ========== */
.login-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 100vw;
  min-height: 100vh;
  overflow: hidden;
}

/* ========== 背景层 ========== */
.login-bg {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(22, 119, 255, 0.15) 0%, rgba(22, 119, 255, 0.02) 50%, rgba(0, 0, 0, 0.03) 100%),
    url('../static/images/login.png') center / cover no-repeat;
  z-index: 0;
}

.login-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(2px);
}

/* ========== 登录卡片 ========== */
.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  padding: var(--space-2xl) var(--space-xl) var(--space-xl);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-xl);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.08),
    0 1px 4px rgba(0, 0, 0, 0.04);
}

/* ========== 标题区 ========== */
.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.login-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  font-size: 32px;
  color: #fff;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border-radius: 50%;
  margin-bottom: var(--space-md);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
}

.login-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: 2px;
}

.login-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* ========== 表单 ========== */
.login-form :deep(.ant-form-item) {
  margin-bottom: var(--space-lg);
}

.login-input :deep(.ant-input-prefix) {
  margin-right: var(--space-sm);
}

.input-icon {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-md);
}

.remember-check {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* ========== 登录按钮 ========== */
.login-btn {
  width: 100%;
  height: 44px;
  font-size: var(--font-size-md);
  font-weight: 500;
  letter-spacing: 4px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border: none;
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.35);
  transition: all var(--transition-base);
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45);
}

.login-btn:active {
  transform: translateY(0);
}

/* ========== 注册链接 ========== */
.login-register-link {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

.register-link {
  color: var(--color-primary);
  font-weight: 500;
  margin-left: 4px;
}

/* ========== 页脚 ========== */
.login-footer {
  position: absolute;
  bottom: var(--space-lg);
  z-index: 1;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  letter-spacing: 1px;
}
</style>
