/**
 * Pinia 认证状态管理
 * ==================
 * 集中管理 JWT token、用户信息、登录/登出操作。
 *
 * verifyToken() 使用缓存策略：
 *   首次调用 → 网络请求验证 token
 *   30 秒内再次调用 → 直接返回缓存结果（无需网络请求）
 *   这消除了切换模块时的 50-200ms 路由守卫延迟。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { jwtDecode } from 'jwt-decode'
import http from '@/http'
import { api } from '@/settings'

export const useAuthStore = defineStore('auth', () => {
  // ==================== State ====================
  const accessToken = ref(
    sessionStorage.getItem('token') || localStorage.getItem('token') || null
  )
  const refreshTokenValue = ref(
    sessionStorage.getItem('refresh') || localStorage.getItem('refresh') || null
  )
  const username = ref(localStorage.getItem('username') || '')
  // 从已存储的 JWT token 解码 user_id，避免刷新后 userId 为 null 导致 fetchPermissions 跳过
  const userId = ref(_decodeUserId())
  const isStaff = ref(false)       // 员工权限
  const isSuperuser = ref(false)   // 超级管理员权限
  const lastVerified = ref(0)      // 上次验证成功的时间戳
  const tokenIsValid = ref(null)   // null=未知, true=有效, false=失效

  /** 从已存储的 token 中解码 user_id（无网络请求） */
  function _decodeUserId() {
    try {
      const token = sessionStorage.getItem('token') || localStorage.getItem('token')
      if (token) return jwtDecode(token).user_id
    } catch {}
    return null
  }

  // ==================== Getters ====================
  const isAuthenticated = computed(() => !!accessToken.value)

  /** 是否需要重新网络验证（距上次验证超过 30 秒） */
  const needsVerification = computed(() => {
    return Date.now() - lastVerified.value > 30_000
  })

  // ==================== Actions ====================

  /** 登录：获取 token 并持久化 */
  async function login(credentials) {
    // 先清除所有旧 token，确保不会残留过期凭证
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('refresh')
    accessToken.value = null
    refreshTokenValue.value = null

    const response = await http.post(api.token_obtain, {
      username: credentials.username,
      password: credentials.password,
    })
    const { access, refresh } = response.data

    accessToken.value = access
    refreshTokenValue.value = refresh
    username.value = credentials.username

    // 持久化存储
    if (credentials.remember) {
      localStorage.setItem('token', access)
    } else {
      sessionStorage.setItem('token', access)
    }
    sessionStorage.setItem('refresh', refresh)
    localStorage.setItem('username', credentials.username)

    // 从 JWT payload 解码 user_id
    try {
      const payload = jwtDecode(access)
      userId.value = payload.user_id
    } catch { /* ignore decode error */ }

    lastVerified.value = Date.now()
    tokenIsValid.value = true

    // 获取用户权限信息
    await fetchPermissions()
  }

  /** 从 API 获取当前用户的 staff/superuser 权限 */
  async function fetchPermissions() {
    if (!userId.value) userId.value = _decodeUserId()
    if (!userId.value) return
    try {
      const res = await http.get(
        `${api.users}${userId.value}/`,
        { headers: { Authorization: `Bearer ${accessToken.value}` } }
      )
      isStaff.value = res.data.is_staff || false
      isSuperuser.value = res.data.is_superuser || false
    } catch {
      isStaff.value = false
      isSuperuser.value = false
    }
  }

  /** 退出登录：清除所有状态和持久化存储 */
  function logout() {
    accessToken.value = null
    refreshTokenValue.value = null
    username.value = ''
    userId.value = null
    isStaff.value = false
    isSuperuser.value = false
    tokenIsValid.value = false
    lastVerified.value = 0

    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('refresh')
    localStorage.removeItem('username')
    sessionStorage.removeItem('selectedKeys')
  }

  /** 验证 token 有效性（带缓存，避免每次路由跳转都发网络请求） */
  async function verifyToken() {
    if (!accessToken.value) {
      tokenIsValid.value = false
      return false
    }
    // 缓存命中：30 秒内已验证通过，直接返回
    if (!needsVerification.value && tokenIsValid.value === true) {
      return true
    }
    try {
      await http.post(api.token_verify, { token: accessToken.value })
      lastVerified.value = Date.now()
      tokenIsValid.value = true
      return true
    } catch {
      tokenIsValid.value = false
      // 尝试刷新 token
      try {
        const refresh = refreshTokenValue.value
        if (refresh) {
          const response = await http.post(api.token_refresh, { refresh })
          accessToken.value = response.data.access
          // 更新存储
          if (localStorage.getItem('token')) {
            localStorage.setItem('token', response.data.access)
          } else {
            sessionStorage.setItem('token', response.data.access)
          }
          lastVerified.value = Date.now()
          tokenIsValid.value = true
          return true
        }
      } catch { /* refresh also failed */ }
      return false
    }
  }

  return {
    accessToken, refreshTokenValue, username, userId,
    isStaff, isSuperuser,
    lastVerified, tokenIsValid,
    isAuthenticated, needsVerification,
    login, logout, verifyToken, fetchPermissions,
  }
})
