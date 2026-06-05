"""
自定义权限模块
=================
定义四级 RBAC 权限类，用于 DRF 视图的权限控制。

权限层级（从高到低）:
    IsSuperUser     — 超级管理员，拥有所有权限
    IsStaff         — 员工，可管理普通用户但不能操作 staff/superuser
    IsActie         — 已激活用户，可进行读写操作
    IsActieReadOnly — 已激活用户，仅可读（SAFE_METHODS: GET/HEAD/OPTIONS）

使用方式:
    在 ViewSet/APIView 的 permission_classes 中组合使用，
    如: permission_classes = [IsSuperUser | IsStaff | IsActieReadOnly]
    表示 超级管理员/员工/激活只读用户 均可访问。
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class IsSuperUser(BasePermission):
    """
    超级管理员权限 —— 拥有所有数据的完全访问权限。

    条件: 已认证 + is_superuser + is_active
    """
    message = '权限不足：仅超级管理员可执行此操作'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser and
            request.user.is_active
        )


class IsStaff(BasePermission):
    """
    员工权限 —— 可管理普通用户，但不能操作 staff/superuser 用户。

    条件: 已认证 + is_staff + is_active

    对象级权限 (has_object_permission):
        - 非 User 模型 → 放行（员工可操作主机等其他资源）
        - User 模型 + 目标用户是 staff/superuser → 拒绝（无权修改同级或上级）
        - User 模型 + 目标用户是普通用户 → 允许
    """
    message = '权限不足：仅管理员及以上可执行此操作'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_staff and
            request.user.is_active
        )

    def has_object_permission(self, request, view, obj):
        """
        对象级权限：阻止员工操作 staff/superuser 用户。

        Args:
            obj: 被操作的模型实例

        Returns:
            True  允许操作
            False 拒绝（目标用户是 staff 或 superuser）
        """
        # 非用户模型 → 放行
        if view.queryset.model is not User:
            return True
        # 目标用户是 staff 或 superuser → 拒绝
        elif obj.is_superuser or obj.is_staff:
            return False
        return True


class IsActie(BasePermission):
    """
    已激活用户权限 —— 所有已激活用户均可进行读写操作。

    条件: 已认证 + is_active
    用途: 终端操作（SSH、文件管理等）需要的是激活状态，而非管理员身份。
    """
    message = '权限不足：账号未激活，请联系管理员'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class IsActieReadOnly(BasePermission):
    """
    已激活用户只读权限 —— 只能执行安全的 HTTP 方法（GET/HEAD/OPTIONS）。

    条件: 已认证 + is_active + SAFE_METHODS

    用途: 普通激活用户可以查看主机列表/用户列表，但不能增删改。
    """
    message = '权限不足：当前用户仅有只读权限'

    def has_permission(self, request, view):
        # 非安全方法直接拒绝
        if request.method in SAFE_METHODS:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.is_active
            )
        return False
