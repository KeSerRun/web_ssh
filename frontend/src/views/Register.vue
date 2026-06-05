<template>
  <div class="register-page">
    <!-- 背景层 -->
    <div class="register-bg"></div>

    <!-- 注册卡片 -->
    <div class="register-card">
      <!-- 标题区 -->
      <div class="register-header">
        <div class="register-logo">
          <UserAddOutlined />
        </div>
        <h1 class="register-title">创建账号</h1>
        <p class="register-subtitle">注册后即可使用终端管理系统</p>
      </div>

      <!-- 表单 -->
      <a-form
        :model="form"
        name="register"
        autocomplete="off"
        :rules="rules"
        @finish="onFinish"
        class="register-form"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="form.username"
            placeholder="请输入用户名"
            size="large"
            class="register-input"
          >
            <template #prefix>
              <UserOutlined class="input-icon" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="mobile">
          <a-input
            v-model:value="form.mobile"
            placeholder="请输入手机号"
            size="large"
            class="register-input"
          >
            <template #prefix>
              <PhoneOutlined class="input-icon" />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item name="password">
          <a-input-password
            v-model:value="form.password"
            placeholder="请设置密码（至少6位）"
            size="large"
            class="register-input"
          >
            <template #prefix>
              <LockOutlined class="input-icon" />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            class="register-btn"
            :loading="loading"
          >
            注 册
          </a-button>
        </a-form-item>
      </a-form>

      <!-- 跳转登录 -->
      <div class="register-footer">
        已有账号？
        <router-link to="/login" class="login-link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  UserOutlined, LockOutlined, PhoneOutlined, UserAddOutlined,
} from '@ant-design/icons-vue'
import { httpPOST } from '@/http'
import { api } from '@/settings'
import router from '@/router'

const loading = ref(false)

const form = reactive({
  username: '',
  mobile: '',
  password: '',
})

const onFinish = () => {
  loading.value = true
  httpPOST(api.register, {
    username: form.username,
    mobile: form.mobile,
    password: form.password,
  }).then(() => {
    message.success('注册成功，请登录')
    router.push('/login')
  }).catch(err => {
    const data = err?.response?.data
    if (data) {
      // 提取后端返回的具体错误信息
      const msgs = []
      for (const [key, val] of Object.entries(data)) {
        msgs.push(Array.isArray(val) ? val.join('；') : val)
      }
      message.error(msgs.join('；') || '注册失败，请稍后重试')
    } else {
      message.error('注册失败，请检查网络连接')
    }
  }).finally(() => {
    loading.value = false
  })
}

// ---------- 表单校验 ----------
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度 2-20 位', trigger: 'blur' },
  ],
  mobile: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}
</script>


<style scoped>
/* ========== 页面容器 ========== */
.register-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 100vw;
  min-height: 100vh;
  overflow: hidden;
}

/* ========== 背景层 ========== */
.register-bg {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(22, 119, 255, 0.12) 0%, rgba(22, 119, 255, 0.02) 50%, rgba(0, 0, 0, 0.03) 100%),
    url('../static/images/login.png') center / cover no-repeat;
  z-index: 0;
}

.register-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(2px);
}

/* ========== 注册卡片 ========== */
.register-card {
  position: relative;
  z-index: 1;
  width: 420px;
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
.register-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.register-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  font-size: 32px;
  color: #fff;
  background: linear-gradient(135deg, #52c41a, #73d13d);
  border-radius: 50%;
  margin-bottom: var(--space-md);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.register-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: 2px;
}

.register-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-xs);
}

/* ========== 表单 ========== */
.register-form :deep(.ant-form-item) {
  margin-bottom: var(--space-lg);
}

.register-input :deep(.ant-input-prefix) {
  margin-right: var(--space-sm);
}

.input-icon {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-md);
}

/* ========== 注册按钮 ========== */
.register-btn {
  width: 100%;
  height: 44px;
  font-size: var(--font-size-md);
  font-weight: 500;
  letter-spacing: 4px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #52c41a, #73d13d);
  border: none;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.35);
  transition: all var(--transition-base);
}

.register-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(82, 196, 26, 0.45);
}

.register-btn:active {
  transform: translateY(0);
}

/* ========== 底部链接 ========== */
.register-footer {
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-sm);
}

.login-link {
  color: var(--color-primary);
  font-weight: 500;
  margin-left: 4px;
}
</style>
