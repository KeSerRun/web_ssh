/**
 * Vue Router 路由配置
 * ====================
 * 项目使用 Vue Router 实现单页应用（SPA）的页面导航。
 *
 * 路由结构:
 *   /login  → Login.vue (登录页)
 *   /base   → Base.vue  (主布局，包含侧边导航栏)
 *     ├─ /base/home       → Home.vue       (展示大厅)
 *     ├─ /base/host       → Host.vue       (资产管理)
 *     ├─ /base/category   → Category.vue   (资源分类)
 *     ├─ /base/user       → User.vue       (用户管理)
 *     ├─ /base/allocation → Allocation.vue (资源分配)
 *     └─ /base/test       → Test.vue       (测试/终端页面)
 *
 * 路由守卫 (beforeEach):
 *   首次导航 → 网络验证 token
 *   30 秒内再次导航 → 使用缓存结果（无需网络请求）
 *   未登录用户重定向到登录页，已登录用户跳过登录页直接进主页。
 */
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const routes = [
    {
        path: "/login",
        name: "Login",
        alias: "/",                       // 访问根路径 "/" 也会匹配到登录页
        component: () => import("../views/Login.vue"),  // 懒加载
        meta: {
            requiresAuth: false,          // 不需要认证即可访问
        },
    },
    {
        path: "/register",
        name: "Register",
        component: () => import("../views/Register.vue"),
        meta: {
            requiresAuth: false,          // 不需要认证即可访问
        },
    },
    {
        path: "/base",
        name: "Base",
        component: () => import("../views/Base.vue"),
        meta: {
            requiresAuth: true,           // 需要认证
        },
        children: [
            // 所有业务页面都是 Base 的子路由，共享侧边栏布局
            {
                path: "home",
                name: "Home",
                component: () => import("../views/Home.vue"),
                meta: { requiresAuth: true }
            },
            {
                path: "host",
                name: "Host",
                component: () => import("../views/Host.vue"),
                meta: { requiresAuth: true, requiresAdmin: true }
            },
            {
                path: "category",
                name: "Category",
                component: () => import("../views/Category.vue"),
                meta: { requiresAuth: true, requiresAdmin: true }
            },
            {
                path: "user",
                name: "User",
                component: () => import("../views/User.vue"),
                meta: { requiresAuth: true, requiresAdmin: true }
            },
            {
                path: "allocation",
                name: "Allocation",
                component: () => import("../views/Allocation.vue"),
                meta: { requiresAuth: true, requiresAdmin: true }
            },
            {
                path: "test",
                name: "Test",
                component: () => import("../views/Test.vue"),
                meta: { requiresAuth: true }
            },
        ],
    },
]

const router = createRouter({
    history: createWebHistory(),          // HTML5 History 模式（无 # 号）
    routes: routes,
});

/**
 * 全局前置路由守卫
 *
 * 使用 Pinia auth store 进行 token 校验。
 *
 * 认证流程:
 *   1. 目标页需要认证 + 已登录 → 验证 token → 有效放行/无效去登录
 *   2. 目标页需要认证 + 未登录 → 重定向到登录
 *   3. 目标页是登录 + 已登录 → 验证后直接跳主页（避免重复登录）
 *   4. 目标页是登录 + 未登录 → 正常进入登录页
 *
 * 性能优化:
 *   authStore.verifyToken() 首次调用会网络验证，30 秒内后续调用直接返回缓存结果，
 *   避免每次切换模块都发 HTTP 请求（消除 50-200ms 延迟）。
 */
router.beforeEach(async (to, from, next) => {
    document.title = to.name;             // 设置浏览器标签页标题
    const authStore = useAuthStore();

    if (to.meta.requiresAuth) {
        // ===== 需要认证的页面 =====
        if (authStore.isAuthenticated) {
            // 有 token：验证（带缓存，30 秒内不重复请求）
            const valid = await authStore.verifyToken();
            if (valid) {
                // 检查是否需要管理员权限
                if (to.meta.requiresAdmin) {
                    if (!authStore.isStaff && !authStore.isSuperuser) {
                        await authStore.fetchPermissions()
                    }
                    if (!authStore.isStaff && !authStore.isSuperuser) {
                        console.log("权限不足，跳转到展示大厅");
                        next({ name: "Home" });
                        return;
                    }
                }
                next();                     // token 有效，放行
            } else {
                // token 过期且刷新失败 → 清除并跳转登录
                console.log("token已过期或已失效");
                authStore.logout();
                next({ name: "Login" });
            }
        } else {
            // 无 token → 去登录
            next({ name: "Login" });
        }
    } else {
        // ===== 不需要认证的页面（Login）=====
        if (authStore.isAuthenticated && to.name === 'Login') {
            // 已登录用户访问登录页 → 验证后直接跳主页
            const valid = await authStore.verifyToken();
            if (valid) {
                console.log("当前用户已通过token验证，直接跳转主页");
                next({ name: "Home" });
            } else {
                // token 过期 → 清除并留在登录页
                console.log("token已过期或已失效");
                authStore.logout();
                next();
            }
        } else {
            next();                         // 未登录 → 正常进登录页
        }
    }
});

export default router;
