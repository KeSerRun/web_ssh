"""
用户管理序列化器
=================
负责用户数据的验证、密码处理、权限控制等。

关键安全规则:
    1. 员工 (is_staff) 无权提升任何人的权限（不能修改 is_staff/is_superuser）
    2. 普通用户不能关联用户名为 root 的主机（防止越权）
"""
from rest_framework import serializers
from .models import User
from apps.host.models import Host


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器

    特殊字段:
        sex:      只读，返回 "男"/"女"/"未知" 文本（而非数字）
        password: 只写，最小 6 位，创建/更新时可选
        hosts:    主机 ID 列表，自动转换为 Host 实例
    """
    # sex 字段存储的是数字，但前端显示需要文本标签
    sex = serializers.CharField(source='get_sex_display', read_only=True)
    # 密码只写（永远不返回），最小 6 位
    password = serializers.CharField(
        write_only=True, required=False,
        allow_null=True, allow_blank=True,
        min_length=6
    )
    # 主机 ID 列表 → 自动转为 Host ORM 实例
    hosts = serializers.PrimaryKeyRelatedField(
        queryset=Host.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'mobile', 'name', 'sex',
            'is_active', 'is_staff', 'is_superuser',
            'password', 'hosts',
        ]

    def validate(self, attrs):
        """
        全局验证：权限层级控制。

        规则:
        - 员工不能修改自己或他人的 staff/superuser 身份
        - 普通用户不能关联 root 主机（防止获取 root 权限）
        """
        request = self.context['request']
        user = request.user

        # 规则1: 员工无权提升权限
        if user and user.is_staff and not user.is_superuser:
            if attrs.get('is_staff') or attrs.get('is_superuser'):
                raise serializers.ValidationError(
                    {'is_staff': '权限不足：员工无权修改 staff 或 superuser 身份，仅超级管理员可操作'}
                )

        # 规则2: 普通用户不能关联 root 主机
        if not attrs.get('is_staff') and not attrs.get('is_superuser'):
            hosts = attrs.get('hosts')
            if hosts and any(h.username == 'root' for h in hosts):
                raise serializers.ValidationError(
                    {'hosts': '安全限制：普通用户不能关联 root 账户的主机，请选择非 root 账户的主机'}
                )

        return super().validate(attrs)

    def validate_hosts(self, hosts):
        """
        字段级验证：拦截普通用户添加 root 主机。

        与全局 validate 中规则 2 互为补充，此方法在部分更新时也会触发。
        """
        user = self.context['request'].user
        # 只有普通用户才需要拦截
        if user and not user.is_staff and not user.is_superuser:
            # 只要列表里出现任何 name='root' 的主机就拒绝
            if any(h.name == 'root' for h in hosts):
                raise serializers.ValidationError(
                    '安全限制：普通用户不能关联 root 账户的主机，请选择非 root 账户的主机'
                )
        return hosts

    def create(self, validated_data):
        """
        创建用户 —— 单独处理密码（调用 set_password 哈希后存储）。
        """
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)  # Django 的密码哈希
            user.save()
        return user

    def update(self, instance, validated_data):
        """
        更新用户 —— 密码可选更新（不传则不修改密码）。
        """
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
