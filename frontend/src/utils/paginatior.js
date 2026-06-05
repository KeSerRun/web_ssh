/**
 * 前端分页 Composable
 * ====================
 * 基于 Vue 3 响应式系统实现的纯前端分页方案。
 *
 * 核心概念:
 *   usePagination() — 工厂函数，每次调用返回独立的响应式状态
 *   listData   — 全量数据的响应式容器
 *   current    — 当前页码（ref，变化时自动触发 pageData 重算）
 *   pageSize   — 每页条数
 *   pagination — 计算属性，Ant Design Table 的 pagination prop 直接使用
 *   pageData   — 计算属性，当前页的数据切片
 *   loading    — 数据加载状态
 *   error      — 错误信息
 *
 * 重要变更:
 *   每个视图调用 usePagination() 获取自己独立的 listData、pagination 等状态，
 *   不再共享模块级全局变量。切换视图时新组件从空白状态开始，避免显示上一视图的旧数据。
 *
 * 使用方式:
 *   const { listData, pageData, pagination, loading, handlePageChange } = usePagination()
 *   // 请求完成后赋值: listData.value = response.data
 *   // 模板中: <a-table :pagination="pagination" :data-source="pageData.value" @change="handlePageChange" />
 */
import { reactive, ref, computed } from "vue";

/**
 * 创建独立的分页状态实例
 *
 * @returns {object} 包含 listData, current, pageSize, pagination, pageData,
 *                   getindex, handlePageChange, loading, error, reset
 */
export function usePagination() {
    /**
     * 全量数据 —— 从后端获取的全部数据存放于此
     */
    const listData = reactive({ value: [] });

    /**
     * 当前页码（从 1 开始）
     */
    const current = ref(1);

    /**
     * 每页显示条数
     */
    const pageSize = ref(5);

    /**
     * 数据加载中标志
     */
    const loading = ref(false);

    /**
     * 错误信息（加载失败时设置）
     */
    const error = ref(null);

    /**
     * 分页配置对象（Ant Design Vue Table 的 :pagination prop）
     */
    const pagination = computed(() => ({
        total: listData.value.length,
        current: current.value,
        pageSize: pageSize.value,
        showSizeChanger: true,
        pageSizeOptions: ["5", "10", "15", "20"],
        showTotal: (total) => `共有${total}条数据`,
    }));

    /**
     * 从分页索引计算在整个数据列表中的全局索引
     */
    const getindex = (index) => {
        return (current.value - 1) * pageSize.value + index;
    };

    /**
     * 当前页的数据切片
     */
    const pageData = computed(() => ({
        value: listData.value.slice(
            (current.value - 1) * pageSize.value,
            current.value * pageSize.value
        ),
    }));

    /**
     * Ant Design Table 分页变化回调
     */
    const handlePageChange = (pag) => {
        current.value = pag.current;
        pageSize.value = pag.pageSize;
    };

    /**
     * 重置所有状态（切换视图时调用）
     */
    const reset = () => {
        listData.value = [];
        current.value = 1;
        pageSize.value = 5;
        loading.value = false;
        error.value = null;
    };

    return {
        listData,
        current,
        pageSize,
        pagination,
        pageData,
        getindex,
        handlePageChange,
        loading,
        error,
        reset,
    };
}
