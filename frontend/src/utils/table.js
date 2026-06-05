/**
 * 表格列定义模块
 * ==================
 * 集中管理项目中所有 Ant Design Vue Table 的列配置。
 *
 * 每列由一个对象定义，常用属性:
 *   title       — 列头文本
 *   dataIndex   — 对应数据字段名
 *   key         — 唯一标识
 *   width       — 列宽（px）
 *   ellipsis    — 内容超出时省略号显示
 *   scopedSlots — 自定义渲染插槽（如操作列）
 *   sorter      — 排序函数
 *
 * 表格用途:
 *   categoryColumns   — 主机分类列表
 *   detailsColumns    — 主机详情列表
 *   userColumns       — 用户管理列表
 *   userHostColumns   — 资源分配列表（含主机列表列）
 *   hostSimpleColumns — 简洁主机信息（用于选择器）
 *   dictColumns       — 远程文件目录列表（含文件类型/权限/大小/日期）
 */

/**
 * 主机分类表格列
 */
const categoryColumns = [
    { title: '分类名称', dataIndex: 'category_name', key: 'name', width: 240, },
    { title: '操作', key: 'action', width: 200, dataIndex: 'action', scopedSlots: { customRender: 'action' } }
];

/**
 * 主机管理表格列
 */
const detailsColumns = [
    { title: '状态', dataIndex: 'update_status', key: 'update_status', width: 40, },
    { title: '类别', dataIndex: 'category_name', key: 'category_name', width: 160, },
    { title: '主机名称', dataIndex: 'name', key: 'name', width: 220, },
    { title: '账户', dataIndex: 'username', key: 'username', width: 120, },
    { title: '地址', dataIndex: 'ip_addr', key: 'ip_addr', width: 200, },
    { title: '端口', dataIndex: 'port', key: 'port', width: 150, elipsis: true, },
    { title: '连接密码', dataIndex: 'connect_pwd', key: 'connect_pwd', width: 220, },
    { title: '备注信息', dataIndex: 'remark', key: 'remark', elipsis: true, },
    { title: '操作', key: 'action', width: 200, dataIndex: 'action', scopedSlots: { customRender: 'action' } }
];

/**
 * 用户管理表格列
 */
const userColumns = [
    { title: '用户名', dataIndex: 'username', key: 'username', width: 240, },
    { title: '手机号', dataIndex: 'mobile', key: 'mobile', width: 240, },
    { title: '激活状态', dataIndex: 'is_active', key: 'is_active', width: 150, },
    { title: '普通员工', dataIndex: 'is_staff', key: 'is_staff', width: 150, },
    { title: '超级管理员', dataIndex: 'is_superuser', key: 'is_superuser', width: 150, },
    { title: '操作', key: 'action', width: 200, dataIndex: 'action', scopedSlots: { customRender: 'action' } }
];

/**
 * 资源分配表格列 —— 比 userColumns 多了"主机列表"列
 */
const userHostColumns = [
    { title: '用户名', dataIndex: 'username', key: 'username', width: 240, },
    { title: '手机号', dataIndex: 'mobile', key: 'mobile', width: 240, },
    { title: '激活状态', dataIndex: 'is_active', key: 'is_active', width: 150, },
    { title: '普通员工', dataIndex: 'is_staff', key: 'is_staff', width: 150, },
    { title: '超级管理员', dataIndex: 'is_superuser', key: 'is_superuser', width: 150, },
    { title: '主机列表', dataIndex: 'hosts', key: 'hosts', width: 150, },
];

/**
 * 简化主机信息列 —— 用于下拉选择器等场景
 */
const hostSimpleColumns = [
    { title: '主机名称', dataIndex: 'title' },
    { title: '主机分类', dataIndex: 'category' },
    { title: '主机地址', dataIndex: 'ip_addr' },
];

/**
 * 远程文件目录列表列
 *
 * sorter: 文件大小列支持按数值排序
 */
const dictColumns = [
    { title: '类型', dataIndex: 'perm', key: 'perm', width: 60, },
    { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true, width: 140 },
    { title: '大小', dataIndex: 'size', key: 'size', width: 100, sorter: (a, b) => a.size - b.size },
    { title: '修改日期', dataIndex: 'date', key: 'date', width: 140 },
];

export { categoryColumns, detailsColumns, userColumns, userHostColumns, hostSimpleColumns, dictColumns }
