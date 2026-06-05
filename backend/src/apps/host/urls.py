"""
主机管理路由配置
=================
使用 DRF Router 自动生成 RESTful 路由，并手动添加自定义文件操作端点。

自动生成的路由:
    GET     /host/hosts/         → 主机列表
    POST    /host/hosts/         → 创建主机
    GET     /host/hosts/{id}/    → 主机详情
    PUT     /host/hosts/{id}/    → 更新主机
    PATCH   /host/hosts/{id}/    → 部分更新主机
    DELETE  /host/hosts/{id}/    → 删除主机
    (category 同理)

手动添加的路由:
    POST /host/<dev_id>/file/       → 远程执行文件命令
    POST /host/<dev_id>/upload/     → 上传文件到远程主机
    POST /host/<dev_id>/download/   → 从远程主机下载文件
"""
from rest_framework.routers import DefaultRouter
from .views import (
    HostViewSet, HostCategoryViewSet,
    HostFileAPIView, UploadFileAPIView, DownloadFileAPIView
)
from django.urls import path

# Router 自动生成 CRUD 路由
router = DefaultRouter()
router.register(r'hosts', HostViewSet, basename='host')
router.register(r'category', HostCategoryViewSet, basename='category')

# 合并自动路由和手动自定义路由
urlpatterns = router.urls + [
    path('<int:dev_id>/file/', HostFileAPIView.as_view(), name='file'),
    path('<int:dev_id>/upload/', UploadFileAPIView.as_view(), name='upload'),
    path('<int:dev_id>/download/', DownloadFileAPIView.as_view(), name='download'),
]
