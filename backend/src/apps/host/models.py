"""
主机管理数据模型
=================
定义主机（Host）和主机分类（HostCategory）两个核心模型。

Host 是系统最核心的实体，每一台被管理的远程服务器对应一条 Host 记录。
系统通过 SSH 密钥认证实现免密登录，私钥存储在数据库中，公钥推送到远程主机。
"""
from django.db import models


class HostCategory(models.Model):
    """
    主机分类（如：数据库服务器、Web 服务器、测试环境等）。

    用于对主机进行逻辑分组，方便管理和筛选。
    """
    name = models.CharField(
        '类别名称',
        max_length=50,
        unique=True,
        error_messages={'unique': '该主机分类已存在'}
    )

    class Meta:
        db_table = 'host_category'
        verbose_name = '主机分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Host(models.Model):
    """
    远程主机模型 —— 系统核心实体。

    每一条记录代表一台可被管理的远程 Linux/Unix 服务器。

    连接方式:
        1. 初次添加时，用户提供密码 → 系统生成 RSA 密钥对 → 公钥推送到远端 → 私钥存入数据库
        2. 后续操作均使用密钥认证，无需密码

    关键字段:
        - private_key: PEM 格式 RSA 私钥（存储在数据库，用于免密登录）
        - public_key:  OpenSSH 格式公钥（已推送到远端 ~/.ssh/authorized_keys）
        - connect_pwd: 初始连接密码（仅用于首次添加时推送公钥）
    """
    STATUS_CHOICES = [(1, '在线'), (0, '离线')]

    status = models.IntegerField('状态', choices=STATUS_CHOICES, default=0)
    category = models.ForeignKey(
        HostCategory,
        on_delete=models.CASCADE,
        verbose_name='类别'
    )
    name = models.CharField(
        '主机名称',
        unique=True,
        max_length=100,
        error_messages={'unique': '该主机名称已存在'}
    )
    username = models.CharField('登录账户', max_length=50)
    ip_addr = models.GenericIPAddressField('IP地址')
    port = models.IntegerField('端口', default=22)
    connect_pwd = models.CharField('连接密码', max_length=255)
    remark = models.TextField('备注', blank=True)

    # ========== SSH 密钥对 ==========
    # 私钥存储在数据库，公钥已推送到远端 ~/.ssh/authorized_keys
    public_key = models.TextField(blank=True)   # OpenSSH 格式公钥
    private_key = models.TextField(blank=True)  # PEM 格式私钥

    class Meta:
        db_table = 'host'
        verbose_name = '主机'
        verbose_name_plural = verbose_name

    def __str__(self):
        """返回格式: 主机名(IP:端口)"""
        return f"{self.name}({self.ip_addr}:{self.port})"
