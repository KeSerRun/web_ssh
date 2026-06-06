/**
 * 表单数据模型
 * ==============
 * 定义项目中所有表单的响应式数据模型（reactive 对象）。
 *
 * 使用 Vue 3 的 reactive() 创建响应式对象，直接用于 v-model 双向绑定。
 *
 * 表单用途:
 *   userForm      — 用户管理弹窗（新增/编辑用户）
 *   categoryForm  — 主机分类弹窗
 *   detailsForm   — 主机详情弹窗
 *   loginForm     — 登录页表单
 */
import { reactive } from "vue";

/**
 * 用户表单 —— 用户管理 Model 弹窗
 */
const userForm = reactive({
    username: '',
    password: null,
    name: '',
    mobile: '',
    avatar: null,
    is_staff: false,
    is_active: false,
    is_superuser: false,
    hosts: [],                  // 关联主机 ID 列表
});

/**
 * 主机分类表单 —— 分类管理 Model 弹窗
 */
const categoryForm = reactive({
    name: ''
});

/**
 * 主机详情表单 —— 主机管理 Model 弹窗
 */
const detailsForm = reactive({
    status: 1,
    id: '',
    name: '',
    category: 0,                // 分类 ID
    category_name: '',          // 分类名称（只读展示）
    username: 'root',           // 默认登录账户
    ip_addr: '127.0.0.1',       // 默认 IP 地址
    port: 22,                   // 默认 SSH 端口
    connect_pwd: '',            // 初始连接密码（仅用于首次推送公钥）
    remark: '',
});

/**
 * 登录表单
 */
const loginForm = reactive({
    username: '',
    password: '',
    remember: false,            // "记住我" → 决定 token 存 sessionStorage 还是 localStorage
});

export { userForm, categoryForm, detailsForm, loginForm }
