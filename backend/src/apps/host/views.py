"""
主机管理 API 视图
=================
提供主机的 CRUD 操作以及远程文件管理功能。

API 端点:
    - ModelViewSet (RESTful CRUD): /host/hosts/、/host/category/
    - 文件操作: /host/<dev_id>/file/、upload/、download/

所有接口统一返回格式: {"code": <http_status>, "message": "<描述>", "data": <数据|null>}
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Host, HostCategory
from .serializers import HostSerializer, HostCategorySerializer
from django.http import FileResponse
from rest_framework.views import APIView
from utils.ssh import exec_cmd, upload_file, download_file, push_public_key, generate_key_pair, probe_ssh_connect
from utils.permissions import IsSuperUser, IsStaff, IsActie, IsActieReadOnly
from utils.exceptions import APIResponse

logger = logging.getLogger(__name__)


# ==================== 共享工具 ====================

def _get_host_or_404(dev_id):
    """
    根据主机 ID 获取主机信息字典，不存在则返回 404 错误响应。

    此函数消除了 HostFileAPIView / UploadFileAPIView / DownloadFileAPIView
    中重复的主机查询模式。

    Returns:
        tuple: (host_info_dict, None)  成功
        tuple: (None, APIResponse)     主机不存在
    """
    host_info = Host.objects.filter(pk=dev_id).values().first()
    if not host_info:
        return None, APIResponse(
            message='主机不存在或已被删除',
            code=status.HTTP_404_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )
    return host_info, None


# ==================== 视图集 ====================


class HostViewSet(viewsets.ModelViewSet):
    """
    主机 CRUD 视图集

    自动提供: list / create / retrieve / update / partial_update / destroy
    使用 select_related 预加载 category 外键，避免 N+1 查询问题。

    权限: 超级管理员、员工、或已激活只读用户
    """
    queryset = Host.objects.all().select_related('category')
    serializer_class = HostSerializer
    permission_classes = [IsSuperUser | IsStaff | IsActieReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[IsSuperUser | IsStaff])
    def repair(self, request, pk=None):
        """
        修复主机连接 — 重新推送公钥到远端。

        POST /host/hosts/{id}/repair/

        适用场景: Docker 容器重建后 authorized_keys 丢失。
        """
        host = self.get_object()
        if not host.connect_pwd:
            return APIResponse(
                message='该主机缺少连接密码，无法修复，请删除后重新添加',
                code=400, status=400,
            )
        try:
            # 重新生成密钥对并用密码推送公钥
            logger.info("生成密钥中...")
            private, public = generate_key_pair()
            logger.info("密钥生成成功，推送公钥中...")
            push_public_key({
                'ip_addr': host.ip_addr,
                'port': host.port,
                'username': host.username,
                'connect_pwd': host.connect_pwd,
                'public_key': public,
            })
            host.private_key = private
            host.public_key = public
            host.status = 1
            host.save(update_fields=['private_key', 'public_key', 'status'])
            return APIResponse(message='密钥已重新生成并推送，连接已恢复')
        except Exception as e:
            return APIResponse(
                message=f'修复失败：{e}',
                code=500, status=500,
            )

    @action(detail=True, methods=['post'], permission_classes=[IsActie])
    def probe(self, request, pk=None):
        """
        探测主机在线状态 — 通过真实 SSH 连接测试主机是否可达。

        POST /host/hosts/{id}/probe/

        使用存储的私钥尝试连接远程主机，连接成功则更新 status=1（在线），
        失败则更新 status=0（离线）。返回探测结果和错误详情。
        """
        host = self.get_object()

        # 优先使用私钥认证，私钥为空则传 None（paramiko 会跳过密钥认证）
        error = probe_ssh_connect(
            ip_addr=host.ip_addr,
            port=host.port,
            username=host.username,
            pkey_pem=host.private_key or None,
            timeout=5,
        )

        if error is None:
            host.status = 1
            host.save(update_fields=['status'])
            logger.info("主机 %s 探测成功: 在线", host.name)
            return APIResponse(
                data={'status': 1, 'status_text': '在线'},
                message=f'主机 [{host.name}] 连接正常',
            )
        else:
            host.status = 0
            host.save(update_fields=['status'])
            logger.warning("主机 %s 探测失败: %s", host.name, error)
            return APIResponse(
                data={'status': 0, 'status_text': '离线', 'error': error},
                message=f'主机 [{host.name}] 无法连接: {error}',
                code=503,
                status=503,
            )


class HostCategoryViewSet(viewsets.ModelViewSet):
    """
    主机分类 CRUD 视图集

    权限: 与 HostViewSet 一致
    """
    queryset = HostCategory.objects.all()
    serializer_class = HostCategorySerializer
    permission_classes = [IsSuperUser | IsStaff | IsActieReadOnly]


class HostFileAPIView(APIView):
    """
    远程文件管理 API —— 在远程主机上执行受限的 shell 命令。

    POST /host/<dev_id>/file/?path=<base_path>
    Body: {"cmd": "pwd", "args": []}

    安全策略:
        ALLOW_CMD 白名单限制可执行命令，防止任意命令注入。
        所有命令在 cd 到指定 base_path 后执行。
    """
    ALLOW_CMD = {'pwd', 'ls', 'rm', 'mkdir'}
    permission_classes = [IsActie]

    def post(self, request, dev_id):
        # 1. 获取查询参数中的基础路径
        base_path = request.query_params.get('path', '')

        # 2. 获取请求体中的命令和参数
        cmd = request.data.get('cmd', 'pwd')
        args = request.data.get('args', [])

        # 3. 安全校验：命令必须在白名单内
        if cmd not in self.ALLOW_CMD:
            return APIResponse(
                message=f'禁止执行的命令: {cmd}，仅允许: {", ".join(sorted(self.ALLOW_CMD))}',
                code=status.HTTP_403_FORBIDDEN,
                status=status.HTTP_403_FORBIDDEN,
            )

        # 拼接完整命令: cd <base_path> && <cmd> <arg1> <arg2> ...
        full_cmd = f'cd {base_path} && {cmd} ' + ' '.join(args)

        # 4. 通过 SSH 执行命令
        host_info, err = _get_host_or_404(dev_id)
        if err:
            return err

        try:
            logger.debug('cmd: %s', full_cmd)
            out = exec_cmd(host_info=host_info, cmd=full_cmd)
            logger.debug('out: %s', out)
            return APIResponse(data={'output': out})
        except RuntimeError as e:
            return APIResponse(
                message=str(e),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UploadFileAPIView(APIView):
    """
    文件上传 API —— 通过 SFTP 上传文件到远程主机。

    POST /host/<dev_id>/upload/?path=<remote_path>
    Body: multipart/form-data, 字段 filename + file
    """
    permission_classes = [IsActie]

    def post(self, request, dev_id):
        base_path = request.query_params.get('path', '')
        file_name = request.data.get('filename', 'nonename')
        file_obj = request.FILES.get('file')

        if not file_obj:
            return APIResponse(
                message='缺少上传文件，请在请求中附带 file 字段',
                code=status.HTTP_400_BAD_REQUEST,
                status=status.HTTP_400_BAD_REQUEST,
            )

        host_info, err = _get_host_or_404(dev_id)
        if err:
            return err

        try:
            upload_file(host_info, file_obj, base_path, file_name)
            return APIResponse(
                data={'path': base_path, 'name': file_name},
                message='文件上传成功',
            )
        except RuntimeError as e:
            return APIResponse(
                message=f'文件上传失败: {e}',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DownloadFileAPIView(APIView):
    """
    文件下载 API —— 通过 SFTP 从远程主机下载文件。

    POST /host/<dev_id>/download/?path=<remote_path>
    Body: {"filename": "example.txt"}

    返回: FileResponse（浏览器会触发下载）；失败时返回统一 JSON 格式
    """
    permission_classes = [IsActie]

    def post(self, request, dev_id):
        base_path = request.query_params.get('path', '')
        file_name = request.data.get('filename', 'nonename')

        host_info, err = _get_host_or_404(dev_id)
        if err:
            return err

        try:
            file, file_size = download_file(host_info, base_path, file_name)
            response = FileResponse(
                file, as_attachment=True, filename=str(file_name),
            )
            response['Content-Length'] = file_size
            return response
        except FileNotFoundError:
            return APIResponse(
                message=f'文件不存在: {base_path}/{file_name}',
                code=status.HTTP_404_NOT_FOUND,
                status=status.HTTP_404_NOT_FOUND,
            )
        except RuntimeError as e:
            return APIResponse(
                message=str(e),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
