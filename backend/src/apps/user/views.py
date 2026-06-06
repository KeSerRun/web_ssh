"""
用户管理 API 视图
=================
提供用户的 CRUD 操作以及用户自主注册。

使用 DRF ModelViewSet 自动实现 RESTful API，
权限控制由 permissions 模块处理。
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer, RegisterSerializer
from utils.permissions import IsSuperUser, IsStaff, IsActie, IsActieReadOnly

User = get_user_model()


class RegisterAPIView(APIView):
    """
    用户自主注册接口 — 独立 APIView，不经过 ViewSet router。

    POST /user/register/
    请求体: { "username": "...", "mobile": "...", "password": "..." }

    无需认证，注册后自动激活，默认无管理权限。
    """
    authentication_classes = []       # 关闭所有认证，避免 SessionAuth 触发 CSRF 403
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'id': user.id, 'username': user.username, 'mobile': user.mobile},
            status=status.HTTP_201_CREATED,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    用户 CRUD 视图集

    自动提供:
        list    — GET  /user/users/     用户列表
        create  — POST /user/users/     创建用户
        retrieve — GET  /user/users/{id}/ 用户详情
        update  — PUT  /user/users/{id}/ 全量更新用户
        destroy — DELETE /user/users/{id}/ 删除用户

    权限:
        超级管理员 → 全部操作
        员工       → 可管理普通用户（不能操作 superuser/staff）
        激活用户   → 只读
    """
    queryset = User.objects.all().prefetch_related('hosts')
    serializer_class = UserSerializer
    permission_classes = [IsSuperUser | IsStaff | IsActieReadOnly]

    @action(
        detail=True, methods=['post', 'put'],
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsActie],
    )
    def avatar(self, request, pk=None):
        """上传用户头像 — POST /user/users/{id}/avatar/"""
        user = self.get_object()
        # 只允许修改自己的头像（管理员除外）
        if not (request.user.is_staff or request.user.is_superuser) and request.user.id != user.id:
            return Response(
                {'message': '只能修改自己的头像'},
                status=status.HTTP_403_FORBIDDEN,
            )

        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response(
                {'message': '请选择要上传的图片'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.avatar = avatar_file
        user.save(update_fields=['avatar'])
        return Response({'avatar': user.avatar.url if user.avatar else None})
