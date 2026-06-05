"""
自定义认证后端
=================
扩展 Django 默认的认证机制，支持使用手机号或用户名登录。

Django 默认只支持 username + password 登录，
此后端允许用户在登录表单的"用户名"字段中输入手机号或用户名。
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class MobileOrUsernameBackend(ModelBackend):
    """
    双字段认证后端：支持手机号或用户名 + 密码登录。

    工作流程:
        1. 用户提交 username 字段（可能是手机号或用户名）
        2. 用 Q 对象同时查询 mobile 和 username 字段
        3. 找到用户后验证密码

    配置方式:
        在 settings.py 的 AUTHENTICATION_BACKENDS 中添加此类的路径。
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        认证用户。

        查询策略: mobile=username OR username=username
        即用户输入的内容同时匹配手机号和用户名两个字段。
        """
        # username 参数可能是手机号也可能是用户名
        user = User.objects.filter(
            Q(mobile=username) | Q(username=username)
        ).first()

        if user and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        """
        根据主键获取用户（Django session 认证流程需要）。
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
