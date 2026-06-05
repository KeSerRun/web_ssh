/**
 * 对象复制与操作工具模块
 * ========================
 * 提供对象属性复制、清空、数组合并去重等功能。
 */
import { toRaw } from "vue";

/**
 * 将对象 A 中与 B 同名属性的值复制到 B 上（输出 B 的原始对象）
 *
 * 使用场景：编辑弹窗打开时，将表格行数据复制到表单对象中。
 *
 * @param {object} A - 源对象（如表格行数据）
 * @param {object} B - 目标对象（如表单数据模型）
 * @returns {object}  - B 的原始对象（toRaw 去除 Proxy 包装）
 */
function assignSame(A, B) {
    Object.keys(B).forEach(k => k in A && (B[k] = A[k]));
    return toRaw(B);
}

/**
 * 清空对象中的所有属性值
 *
 * 根据属性类型自动置为默认空值:
 *   string  → ''
 *   boolean → false
 *   number  → 0
 *
 * 使用场景：新增弹窗打开前清空表单。
 *
 * @param {object} A - 需要清空的对象
 */
function clearItem(A) {
    Object.keys(A).forEach(k => {
        const t = typeof A[k];
        if (t === 'string') A[k] = '';
        else if (t === 'boolean') A[k] = false;
        else if (t === 'number') A[k] = 0;
    });
}

/**
 * 返回两个数组的并集（去重，保持首次出现顺序）
 *
 * 使用 Set 实现 O(n) 去重。
 *
 * @param {Array} A - 第一个数组
 * @param {Array} B - 第二个数组
 * @returns {Array}  - 去重后的并集
 */
function union(A, B) {
    const set = new Set();               // 用于去重的集合
    return [...A, ...B].filter(x => {
        if (set.has(x)) return false;
        set.add(x);
        return true;
    });
}


export { assignSame, clearItem, union }
