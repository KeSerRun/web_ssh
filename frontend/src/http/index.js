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

    if (!isTokenVerify && hasToken) {
        switch (error.response?.status) {
            case 400:
                message.error(error.response?.data?.message || '提交信息有误，请检查后重试');
                break;
            case 401:
                if (!isAuthEndpoint) {
                    message.error('登录已过期，请重新登录');
                }
                break;
            case 403:
                message.error('没有权限执行此操作');
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
const getConfg = () => {
    let token = sessionStorage.token || localStorage.token;
    return {
        headers: {
            Authorization: `Bearer ${token}`,
        }
    };
}

// ==================== RESTful 请求方法 ====================

/**
 * GET 请求 —— 获取数据
 * @param {string} url           - 请求地址
 * @param {boolean} show_massage - 是否显示成功/失败提示
 */
const httpGET = async (url, show_massage = false) => {
    return http.get(url, getConfg()).then(response => {
        if (show_massage) {
            message.success('数据获取成功');
        }
        return response;
    }).catch(error => {
        console.log(getErrorMessage(error));
        throw error;
    });
};

/**
 * POST 请求 —— 创建数据
 * @param {string} url           - 请求地址
 * @param {object} form          - 请求体数据
 * @param {boolean} show_massage - 是否显示成功/失败提示
 */
const httpPOST = async (url, form, show_massage = true) => {
    return http.post(url, form, getConfg()).then((response) => {
        if (show_massage) {
            message.success('数据上传成功');
        }
        return response;
    }).catch(error => {
        console.log(getErrorMessage(error));
        throw error;
    })
}

/**
 * PUT 请求 —— 更新数据（全量替换）
 * @param {string} url           - 请求地址（不含 ID）
 * @param {number} id            - 资源 ID，自动拼接到 URL 末尾
 * @param {object} form          - 请求体数据
 * @param {boolean} show_massage - 是否显示成功/失败提示
 */
const httpPUT = async (url, id, form, show_massage = true) => {
    return http.put(url + id + '/', form, getConfg()).then((response) => {
        if (show_massage) {
            message.success('数据更新成功');
        }
        return response;
    }).catch(error => {
        console.log(getErrorMessage(error));
        throw error;
    })
}

/**
 * DELETE 请求 —— 删除数据
 * @param {string} url           - 请求地址（不含 ID）
 * @param {number} id            - 资源 ID，自动拼接到 URL 末尾
 * @param {boolean} show_massage - 是否显示成功/失败提示
 */
const httpDELETE = async (url, id, show_massage = true) => {
    return http.delete(url + id + '/', getConfg()).then((response) => {
        if (show_massage) {
            message.success('数据删除成功');
        }
        return response;
    }).catch(error => {
        console.log(getErrorMessage(error));
        throw error;
    })
}

/**
 * 文件下载 —— POST 请求获取 blob，触发浏览器下载
 *
 * 实现原理:
 *   1. 以 blob 类型接收响应（二进制数据）
 *   2. 创建临时 <a> 标签
 *   3. 用 URL.createObjectURL 生成临时下载链接
 *   4. 触发点击 → 浏览器下载
 *   5. 清理临时元素和 URL
 *
 * @param {string} url           - 请求地址
 * @param {object} form          - 请求体（需包含 filename 字段）
 * @param {boolean} show_massage - 是否显示成功/失败提示
 */
const httpFileDownload = async (url, form = {}, show_massage = true) => {
    return http
        .post(url, form, {
            ...getConfg(),
            responseType: 'blob',           // 关键：以二进制方式接收响应
        })
        .then((response) => {
            // 创建临时下载链接并触发点击
            const blob = new Blob([response.data])
            const link = document.createElement('a')
            link.href = URL.createObjectURL(blob)
            link.download = form.filename    // 设置下载文件名
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()                     // 触发下载
            document.body.removeChild(link)
            URL.revokeObjectURL(link.href)   // 释放内存

            if (show_massage) message.success('文件下载成功')
            return response
        })
        .catch((error) => {
            console.log(getErrorMessage(error))
            throw error
        })
}

export default http;
export { httpGET, httpPOST, httpPUT, httpDELETE, httpFileDownload };
