"""
主机管理序列化器
=================
负责主机数据的验证、序列化/反序列化，以及 SSH 密钥对的自动管理。

核心逻辑 (HostSerializer.validate):
    添加新主机时自动生成 RSA 密钥对并将公钥推送到远程主机，
    实现 SSH 免密登录的自动化配置。
"""
from rest_framework import serializers
from .models import Host, HostCategory
from utils.ssh import generate_key_pair, push_public_key, probe_ssh_connect


class HostCategorySerializer(serializers.ModelSerializer):
    """主机分类序列化器 —— 简单的 id/name 映射"""
    class Meta:
        model = HostCategory
        fields = ['id', 'name']


class HostSerializer(serializers.ModelSerializer):
    """
    主机序列化器

    特殊字段:
        category_name: 只读字段，前端展示分类名称时使用（避免只显示 category id）
        connect_pwd:   仅用于初次连接验证和推送公钥，不在列表/详情中返回

    自动密钥管理 (validate):
        1. 先探测 SSH 连接是否可达
        2. 如果该连接（IP+端口+用户名）未曾注册 → 生成新密钥对 + 推送公钥
        3. 如果已注册 → 直接复用已有密钥对
    """
    # 只读字段：让前端表格可以直接显示分类名称
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Host
        fields = [
            'id', 'status', 'category', 'category_name',
            'name', 'username', 'ip_addr', 'port',
            'connect_pwd', 'remark',
        ]
        extra_kwargs = {
            'category': {'write_only': False},  # 写时用 id，读时也返回
        }

    def validate(self, attrs):
        """
        创建/更新时的全局验证逻辑。

        核心流程:
        1. 收集连接参数（新值优先，若无则取已有实例的值）
        2. 探测 SSH 连接可用性
        3. 判断是否已注册：已注册复用密钥，否则生成新密钥并推送公钥
        """
        # --- 收集连接参数 ---
        # getattr 三元：优先用新提交的值，没有则保留实例原值（更新场景）
        host = attrs.get('ip_addr', getattr(self.instance, 'ip_addr', None))
        port = attrs.get('port', getattr(self.instance, 'port', None))
        user = attrs.get('username', getattr(self.instance, 'username', None))
        pwd = attrs.get('connect_pwd')  # 仅临时使用，不存库

        if not host or not port or not user:
            raise serializers.ValidationError({
                'ip_addr': 'IP 地址、端口、登录账户为必填项，请检查后重试'
            })

        # --- 探测 SSH 连接 ---
        err = probe_ssh_connect(host, port, user, password=pwd)
        if err:
            # 区分常见失败原因，给出更明确的提示
            if 'Authentication' in err or 'auth' in err.lower():
                hint = '认证失败，请检查用户名和密码是否正确'
            elif 'timeout' in err.lower() or 'timed out' in err.lower():
                hint = '连接超时，请检查 IP 地址和端口是否正确，以及防火墙是否开放'
            elif 'refused' in err.lower():
                hint = '连接被拒绝，请检查目标主机 SSH 服务是否已启动'
            elif 'Name or service not known' in err or 'getaddrinfo' in err.lower():
                hint = '无法解析主机名，请检查 IP 地址是否正确'
            else:
                hint = f'SSH 连接失败: {err}'
            raise serializers.ValidationError({'connect_pwd': hint})

        # --- 判断是否已注册密钥 ---
        # 唯一键: (IP地址, 端口, 用户名)
        instance = Host.objects.filter(
            ip_addr=host,
            port=int(port),
            username=user
        ).first()

        if not instance:
            # 新连接：生成密钥对并推送公钥
            print("生成密钥中...")
            private, public = generate_key_pair()
            attrs['private_key'] = private
            attrs['public_key'] = public
            # 将公钥推送到远程主机的 authorized_keys
            push_public_key(attrs)
        else:
            # 已有连接注册：直接复用密钥对
            print("该连接链接已经注册")
            attrs['private_key'] = instance.private_key
            attrs['public_key'] = instance.public_key

        return attrs
