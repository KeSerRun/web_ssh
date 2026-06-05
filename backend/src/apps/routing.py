"""
WebSocket 路由配置
===================
定义 WebSocket 连接的 URL 映射。

路由格式:
    ws/ssh/<host_id>/

host_id 对应 Host 表的主键，SSHConsumer 会根据此 ID 加载主机信息并建立 SSH 连接。
"""
from django.urls import re_path
from utils.ssh import SSHConsumer

websocket_urlpatterns = [
    re_path(r'ws/ssh/(?P<host_id>\d+)/$', SSHConsumer.as_asgi()),
]