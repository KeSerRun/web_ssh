/**
 * HTTP 通信模块
 * ==============
 * 基于 Axios 封装的 HTTP 客户端，提供统一的请求/响应拦截、错误处理
 * 以及 RESTful 操作（GET/POST/PUT/DELETE）的便捷方法。
 *
 * 关键功能:
 *   - JWT Bearer 令牌自动附加
 *   - 统一的成功/失败消息提示（Ant Design Vue message）
 *   - 文件下载支持（blob 响应类型）
 *
 * Token 存储策略:
 *   登录时用户选择"记住我" → localStorage (持久化)
 *   否则 → sessionStorage (关闭浏览器即失效)
 */
import axios from "axios";
import settings from "@/settings";
import { message } from 'ant-design-vue';

// 创建 Axios 实例，配置基础 URL
const http = axios.create({
    baseURL: settings.host,
    withCredentials: false,         // 不发送跨域 cookie
})

// ==================== 请求拦截器 ====================
http.interceptors.request.use((config) => {
    return config;
}, (error) => {
    console.log("http请求失败");
    throw error;
});

// ==================== 响应拦截器 ====================
http.interceptors.response.use((response) => {
    return response;
}, (error) => {
    // 已没有 token（已登出），不发错误提示
    const hasToken = !!(sessionStorage.token || localStorage.token);

    const isAuthEndpoint = error.config?.url?.includes('/token/obtain/')
                        || error.config?.url?.includes('/user/register/');
    const isTokenVerify = error.config?.url?.includes('/token/verify/');

    // 登录/注册页自行处理错误弹窗，拦截器不重复提示
    if (!isTokenVerify && !isAuthEndpoint && hasToken) {
        switch (error.response?.status) {
            case 400:
                message.error(error.response?.data?.message || '提交信息有误，请检查后重试');
                break;
            case 401:
                message.error('登录已过期，请重新登录');
                break;
            case 403:
                message.error(error.response?.data?.message || '没有权限执行此操作');
                break;
            case 500:
                message.error('服务器内部错误，请稍后重试');
                break;
            default:
                if (!error.response) {
                    message.error('网络连接失败，请检查网络后重试');
                } else {
                    console.log("http响应失败:", error.response?.status);
                }
        }
    }
    return Promise.reject(error);
});

// ==================== 工具函数 ====================

/**
 * 从错误对象中提取后端返回的错误信息
 */
const getErrorMessage = (error) => {
    return error.response?.data?.message || error.message;
}

/**
 * 构造带 JWT Bearer 令牌的请求配置
 *
 * 优先从 sessionStorage 读取 token（会话级别），
 * 若无则从 localStorage 读取（持久化）。
 */
const getConfig = () => {
    const token = sessionStorage.token || localStorage.token;
    return { headers: { Authorization: `Bearer ${token}` } };
};

// ==================== RESTful 请求方法 ====================

/**
 * 通用请求包装 —— 自动注入 JWT 令牌、统一成功/错误提示。
 *
 * Axios 方法签名差异:
 *   get / delete  → (url, config)        只有 2 个参数
 *   post / put    → (url, data, config)   有 3 个参数
 * 因此需要区分处理。
 */
const _request = (method, url, data, showMsg, successText) => {
    const config = { ...getConfig() };
    const args = data !== undefined
        ? [url, data, config]       // POST / PUT: 三个参数
        : [url, config];            // GET / DELETE: 两个参数
    return method(...args)
        .then(res => {
            if (showMsg) message.success(successText || '操作成功');
            return res;
        })
        .catch(error => {
            console.log(getErrorMessage(error));
            throw error;
        });
};

/** GET 请求 */
const httpGET = (url, showMsg = false) =>
    _request(http.get, url, undefined, showMsg, '数据获取成功');

/** POST 请求 */
const httpPOST = (url, form, showMsg = true) =>
    _request(http.post, url, form, showMsg, '数据上传成功');

/** PUT 请求（自动拼接 ID 到 URL 末尾） */
const httpPUT = (url, id, form, showMsg = true) =>
    _request(http.put, url + id + '/', form, showMsg, '数据更新成功');

/** DELETE 请求（自动拼接 ID 到 URL 末尾） */
const httpDELETE = (url, id, showMsg = true) =>
    _request(http.delete, url + id + '/', undefined, showMsg, '数据删除成功');

/**
 * 文件下载 —— POST 请求获取 blob，触发浏览器下载
 *
 * @param {string}  url      - 请求地址
 * @param {object}  [form]   - 请求体（需包含 filename 字段）
 * @param {boolean} [showMsg] - 是否显示成功提示
 */
const httpFileDownload = async (url, form = {}, showMsg = true) => {
    return http
        .post(url, form, {
            ...getConfig(),
            responseType: 'blob',
        })
        .then((response) => {
            const blob = new Blob([response.data])
            const link = document.createElement('a')
            link.href = URL.createObjectURL(blob)
            link.download = form.filename || 'download'
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(link.href)

            if (showMsg) message.success('文件下载成功')
            return response
        })
        .catch((error) => {
            console.log(getErrorMessage(error))
            throw error
        })
}

export default http;
export { httpGET, httpPOST, httpPUT, httpDELETE, httpFileDownload };
