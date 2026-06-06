/**
 * JWT Token 工具模块
 * ===================
 * 提供 JWT 令牌的解析、刷新和用户信息获取功能。
 *
 * 令牌存储:
 *   - localStorage.token    → "记住我"后的持久化 access token
 *   - sessionStorage.token  → 会话级别 access token
 *   - localStorage.refresh  → 持久化 refresh token
 *   - sessionStorage.refresh → 会话级别 refresh token
 */
import { jwtDecode } from "jwt-decode";
import { httpGET, httpPOST } from "@/http";
import { api } from "@/settings";

/**
 * JWT Token 的 Base64Url 解码（手动实现，用于不依赖库的场景）
 *
 * JWT 结构: header.payload.signature（以 . 分隔）
 * 取 payload 部分（第二段）进行 Base64Url → Base64 → UTF-8 解码。
 *
 * @param {string} str - JWT token 字符串
 * @returns {string}   - 解码后的 JSON payload 字符串
 */
function base64urlDecode(str) {
    str = str.split('.')[1];                    // 取 payload 段
    str = str.replace(/-/g, '+').replace(/_/g, '/');  // Base64Url → Base64
    while (str.length % 4) str += '=';          // 补齐 padding
    return atob(str);                           // Base64 解码
}

/**
 * 刷新 JWT access token
 *
 * 使用 refresh token 向服务端换取新的 access token。
 * 刷新成功后自动更新本地存储。
 *
 * @returns {Promise} - 刷新后的响应或错误
 */
const refreshToken = () => {
    let refresh = sessionStorage.refresh || localStorage.refresh || '';
    return httpPOST(api.token_refresh, { refresh: refresh }).then((response) => {
        // 根据原有存储位置更新 access token
        if (localStorage.token) {
            localStorage.token = response.data.access;
        } else {
            sessionStorage.token = response.data.access;
        }
        return response;
    }).catch(error => { return error });
}

/**
 * 从 JWT payload 中提取当前用户 ID
 *
 * SimpleJWT 默认在 payload 中包含 user_id 字段。
 *
 * @returns {number|undefined} - 用户 ID，无 token 时返回 undefined
 */
const getUserId = () => {
    let token = sessionStorage.token || localStorage.token;
    if (token) {
        const payload = jwtDecode(token);       // 使用 jwt-decode 库解码
        return payload.user_id;                 // SimpleJWT 默认字段
    }
}

/**
 * 获取当前登录用户的详细信息
 *
 * 先从 token 提取 user_id，再请求用户详情接口。
 *
 * @returns {Promise} - 用户详情响应或错误
 */
const getUserInfo = async () => {
    const uid = getUserId()
    if (!uid) throw new Error('无法获取用户 ID，请重新登录')
    return httpGET(`${api.users}${uid}`)
}

export { base64urlDecode, getUserId, getUserInfo, refreshToken };
