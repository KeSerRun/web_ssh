"""
用户管理数据模型
=================
基于 Django AbstractUser 扩展的自定义用户模型。

扩展字段:
    - mobile:      手机号（中国大陆 11 位，唯一，用于登录）
    - name:        真实姓名
    - sex:         性别（男/女/未知）
    - hosts:       关联主机（多对多，用于资源分配）
    - is_active:   激活状态
    - is_staff:    员工权限
    - is_superuser: 超级管理员权限

登录方式:
    支持手机号或用户名 + 密码登录（见 authentication.py）
"""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re


def mobile_validate(value: str):
    """
    手机号格式验证器。

    规则: 1 开头 + 3-9 第二位 + 9 位数字，共 11 位
    例: 13800138000 ✓ | 12345678901 ✗
    """
    if not re.fullmatch(r'^1[3-9]\d{9}$', value):
        raise ValidationError('手机号格式不正确')


class SexChoices(models.IntegerChoices):
    """性别枚举"""
    MALE = 1, '男'
    FEMALE = 2, '女'
    UNKNOWN = 0, '未知'


class User(AbstractUser):
    """
    自定义用户模型。

    继承 Django 的 AbstractUser 获得基础字段（密码哈希、权限组等），
    在此基础上扩展手机号、真实姓名、关联主机等业务字段。

    权限三件套（继承自 AbstractUser，此处显式声明以便序列化器可见）:
        is_active    — 账号是否激活
        is_staff     — 是否可登录 Admin 后台
        is_superuser — 是否拥有所有权限
    """
    # AbstractUser 自带字段（覆盖以添加中文 verbose_name）
    email = models.EmailField('邮箱', blank=True, null=True)
    first_name = models.CharField('first name', max_length=30, blank=True, null=True)
    last_name = models.CharField('last name', max_length=30, blank=True, null=True)
    date_joined = models.DateTimeField('date joined', auto_now_add=True)
    last_login = models.DateTimeField('last login', blank=True, null=True)

    # ========== 业务扩展字段 ==========
    username = models.CharField(
        '用户名', max_length=30, unique=True,
        error_messages={'unique': '该用户名已存在'}
    )
    mobile = models.CharField(
        '手机号', max_length=11, unique=True,
        validators=[mobile_validate],
        error_messages={'unique': '该手机号已注册'}
    )
    name = models.CharField('真实姓名', max_length=20, blank=True)
    sex = models.IntegerField(
        '性别',
        choices=SexChoices.choices,
        default=SexChoices.UNKNOWN
    )

    # ========== 权限字段（显式声明以在 Serializer 中可见） ==========
    is_active = models.BooleanField('有效', default=True)
    is_staff = models.BooleanField('管理员', default=False)
    is_superuser = models.BooleanField('超级管理员', default=False)

    # ========== 关联主机（多对多） ==========
    hosts = models.ManyToManyField(
        'host.Host',
        verbose_name='关联主机',
        blank=True
    )

    class Meta:
        db_table = 'users'
        verbose_name = '用户'

    def __str__(self):
        """返回格式: 用户名:(手机号)"""
        return f'{self.username}:({self.mobile})'
