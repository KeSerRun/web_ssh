"""
自定义权限模块
=================
定义四级 RBAC 权限类，用于 DRF 视图的权限控制。

权限层级（从高到低）:
    IsSuperUser       — 超级管理员，拥有所有权限
    IsStaff           — 员工，可管理普通用户但不能操作 staff/superuser
    IsActive          — 已激活用户，可进行读写操作
    IsActiveReadOnly  — 已激活用户，仅可读（SAFE_METHODS: GET/HEAD/OPTIONS）

使用方式:
    在 ViewSet/APIView 的 permission_classes 中组合使用，
    如: permission_classes = [IsSuperUser | IsStaff | IsActiveReadOnly]
    表示 超级管理员/员工/激活只读用户 均可访问。

注意:
    Django 中间件保证 request.user 始终存在（匿名用户为 AnonymousUser），
    因此 has_permission 中无需重复检查 request.user。
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class IsSuperUser(BasePermission):
    """超级管理员权限 —— 拥有所有数据的完全访问权限。"""

    message = '权限不足：仅超级管理员可执行此操作'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_superuser
            and request.user.is_active
        )


class IsStaff(BasePermission):
    """
    管理员权限 —— 可管理普通用户，但不能操作 staff/superuser 用户。

    对象级权限 (has_object_permission):
        - 非 User 模型       → 放行（管理员可操作主机等其他资源）
        - User 且 staff/admin → 拒绝（无权修改同级或上级）
        - User 且普通用户     → 允许
    """

    message = '权限不足：仅管理员及以上可执行此操作'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
            and request.user.is_active
        )

    def has_object_permission(self, request, view, obj):
        # 非用户模型 → 放行
        if view.queryset.model is not User:
            return True
        # 目标用户是 staff 或 superuser → 拒绝
        if obj.is_superuser or obj.is_staff:
            return False
        return True


class IsActive(BasePermission):
    """已激活用户权限 —— 所有已激活用户均可进行读写操作。"""

    message = '权限不足：账号未激活，请联系管理员'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active


class IsActiveReadOnly(BasePermission):
    """已激活用户只读权限 —— 只能执行安全的 HTTP 方法（GET/HEAD/OPTIONS）。"""

    message = '权限不足：当前用户仅有只读权限'

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return request.user.is_authenticated and request.user.is_active


# ==================== 向后兼容别名 ====================
# 保留旧命名（拼写错误）的别名，避免大规模改动历史引用
IsActie = IsActive
IsActieReadOnly = IsActiveReadOnly
