/**
 * 项目全局配置
 * ==============
 * 集中管理后端 API 地址和所有接口端点。
 *
 * 切换环境:
 *   - 本机开发: host = 'http://127.0.0.1:8000'
 *   - 局域网测试: host = 'http://10.6.94.252:8000'
 */

// ==================== HTTP 服务端地址 ====================
const host = 'http://127.0.0.1:8000';           // 本机开发
// const host = 'http://10.6.94.252:8000';      // 局域网测试

export default { host }

// ==================== API 端点配置 ====================
export const api = {
    // JWT 认证相关
    'token_obtain': host + '/token/obtain/',     // 登录 → 获取 access + refresh token
    'token_refresh': host + '/token/refresh/',   // 刷新 access token
    'token_verify': host + '/token/verify/',     // 验证 token 是否有效

    // 用户管理
    'users': host + '/user/users/',              // 用户 CRUD
    'register': host + '/user/register/',         // 用户自主注册（独立接口，不走 ViewSet router）

    // 主机管理
    'hosts': host + '/host/hosts/',              // 主机 CRUD
    'category': host + '/host/category/',        // 主机分类 CRUD

    // 主机在线探测（需拼接 ID，如 hostProbe(5) → /host/hosts/5/probe/）
    hostProbe: (id) => host + `/host/hosts/${id}/probe/`,
}
