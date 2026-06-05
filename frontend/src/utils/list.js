/**
 * 列表与数据解析工具
 * ====================
 * 提供侧边栏导航列表、SSH 远程 ls -l 输出解析等功能。
 *
 * base_list:   侧边栏导航菜单项，使用 Ant Design 图标（大驼峰命名）
 * parseLs:     解析 ls -l 输出为结构化数据
 * decodePerm:  解析 rwx 权限位为可读对象
 * formatSize:  字节 → 可读大小（KB/MB/GB/TB）
 */
import { reactive } from "vue";

/**
 * 侧边栏导航菜单
 *
 * icon 字段对应 @ant-design/icons-vue 的组件名（大驼峰格式），
 * 如 HomeOutlined、BankOutlined 等。
 */
const base_list = reactive([
    { key: 1, name: "展示大厅", icon: "HomeOutlined", link: "home",         adminOnly: false },
    { key: 2, name: "资产管理", icon: "BankOutlined", link: "host",        adminOnly: true  },
    { key: 3, name: "资源分类", icon: "PartitionOutlined", link: "category", adminOnly: true  },
    { key: 4, name: "用户管理", icon: "UserOutlined", link: "user",        adminOnly: true  },
    { key: 5, name: "资源分配", icon: "SwapOutlined", link: "allocation",  adminOnly: true  },
    { key: 6, name: "测试页面", icon: "ExperimentOutlined", link: "test",  adminOnly: false },
]);

/**
 * 字节数 → 人类可读的大小字符串
 *
 * @param {number} bytes - 字节数
 * @returns {string}      例: "1.45 GB" | "300 KB" | "0 B"
 */
function formatSize(bytes) {
    if (bytes == 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    const val = (bytes / Math.pow(k, i)).toFixed(i > 1 ? 2 : 0)
    return `${val} ${sizes[i]}`
}

/**
 * ls -l 输出的正则表达式
 *
 * 匹配字段:
 *   [1] 权限位 (drwxr-xr-x)
 *   [2] 硬链接数
 *   [3] 所有者
 *   [4] 所属组
 *   [5] 文件大小（字节）
 *   [6] 月份 (Jan-Dec)
 *   [7] 日期 (1-31)
 *   [8] 时间 (HH:MM 或 YYYY)
 *   [9] 文件/目录名
 *   [10] 符号链接目标（可选）
 */
const LS_RE = /^([-\wlrwxstST+]{10})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\w{3})\s+(\d{1,2})\s+([\d:]+)\s+(.+?)(?:\s+->\s+(.*))?$/;

/**
 * 解析 ls -l 命令的输出文本为结构化列表
 *
 * 处理流程:
 *   1. 按行分割
 *   2. 过滤空行和 "total" 汇总行
 *   3. 用正则匹配每行提取字段
 *   4. 过滤掉 . 和 .. 目录
 *   5. 格式化文件大小为可读单位
 *
 * @param {string} text - ls -l 的原始输出
 * @returns {Array<object>}  结构化文件列表
 */
function parseLs(text) {
    return text
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('total'))          // 过滤汇总行
        .reduce((arr, line) => {
            const m = line.match(LS_RE);
            if (!m) return arr;
            const [, perm, nlink, user, group, size, month, day, time, name, target] = m;
            // 过滤 . 和 .. 目录
            if (name !== '.' && name !== '..') {
                arr.push({
                    perm,                                   // 权限字符串
                    nlink: Number(nlink),                   // 硬链接数
                    user,                                   // 所有者
                    group,                                  // 所属组
                    size: formatSize(size),                 // 格式化后的大小
                    date: `${month} ${day} ${time}`,        // 修改日期
                    name,                                   // 文件名
                    target: target || null                  // 符号链接目标
                });
            }
            return arr;
        }, []);
}

/**
 * 解析权限位字符串为结构化对象
 *
 * 输入示例: "drwxr-xr-x"
 * 输出示例: { type: "dir", owner: "rwx", group: "r-x", other: "r-x" }
 *
 * 首位字符含义:
 *   - → 普通文件    d → 目录       l → 符号链接
 *   c → 字符设备    b → 块设备    p → 命名管道
 *   s → Socket     D → Door
 *
 * @param {string} perm - 10 位权限字符串
 * @returns {object}     { type, owner, group, other }
 */
function decodePerm(perm) {
    const typeMap = {
        '-': 'file',
        d: 'dir',
        l: 'link',
        c: 'char',
        b: 'block',
        p: 'pipe',
        s: 'socket',
        D: 'door',
    };
    return {
        type: typeMap[perm[0]] || 'unknown',    // 文件类型
        owner: perm.slice(1, 4),                // 所有者权限 (rwx)
        group: perm.slice(4, 7),                // 所属组权限 (r-x)
        other: perm.slice(7, 10),               // 其他人权限 (r-x)
    };
}

export { base_list, parseLs, decodePerm }
