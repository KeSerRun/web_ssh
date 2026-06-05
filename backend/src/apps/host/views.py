"""
主机管理 API 视图
=================
提供主机的 CRUD 操作以及远程文件管理功能。

API 端点:
    - ModelViewSet (RESTful CRUD): /host/hosts/、/host/category/
    - 文件操作: /host/<dev_id>/file/、upload/、download/

所有接口统一返回格式: {"code": <http_status>, "message": "<描述>", "data": <数据|null>}
"""
from rest_framework import viewsets, status
from .models import Host, HostCategory
from .serializers import HostSerializer, HostCategorySerializer
from django.http import FileResponse
from rest_framework.views import APIView
from utils.ssh import exec_cmd, upload_file, download_file
from utils.permissions import IsSuperUser, IsStaff, IsActie, IsActieReadOnly
from utils.exceptions import APIResponse


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
        try:
            host_info = Host.objects.filter(pk=dev_id).values().first()
            if not host_info:
                return APIResponse(
                    message='主机不存在或已被删除',
                    code=status.HTTP_404_NOT_FOUND,
                    status=status.HTTP_404_NOT_FOUND,
                )
            print(f'cmd: {full_cmd}')
            out = exec_cmd(host_info=host_info, cmd=full_cmd)
            print(f'out: {out}')
            return APIResponse(data={'output': out})
        except RuntimeError as e:
            return APIResponse(
                message=str(e),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return APIResponse(
                message=f'命令执行失败: {e}',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UploadFileAPIView(APIView):
    """
    文件上传 API —— 通过 SFTP 上传文件到远程主机。

    POST /host/<dev_id>/upload/?path=<remote_path>
    Body: multipart/form-data, 字段 filename + file

    流程:
        1. 从请求中读取目标路径、文件名和文件对象
        2. 查询主机信息
        3. 通过 SFTP 分块上传文件
    """
    permission_classes = [IsActie]

    def post(self, request, dev_id):
        # 1. 获取查询参数中的远程目标路径
        base_path = request.query_params.get('path', '')

        # 2. 获取请求中的文件名和文件对象
        file_name = request.data.get('filename', 'nonename')
        file_obj = request.FILES.get('file')
        if not file_obj:
            return APIResponse(
                message='缺少上传文件，请在请求中附带 file 字段',
                code=status.HTTP_400_BAD_REQUEST,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. 建立 SSH 连接，通过 SFTP 上传文件
        try:
            host_info = Host.objects.filter(pk=dev_id).values().first()
            if not host_info:
                return APIResponse(
                    message='主机不存在或已被删除',
                    code=status.HTTP_404_NOT_FOUND,
                    status=status.HTTP_404_NOT_FOUND,
                )
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
        except Exception as e:
            return APIResponse(
                message=f'文件上传异常: {e}',
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
        # 1. 获取查询参数中的远程路径
        base_path = request.query_params.get('path', '')

        # 2. 获取要下载的文件名
        file_name = request.data.get('filename', 'nonename')

        # 3. 通过 SFTP 下载文件并返回 FileResponse
        try:
            host_info = Host.objects.filter(pk=dev_id).values().first()
            if not host_info:
                return APIResponse(
                    message='主机不存在或已被删除',
                    code=status.HTTP_404_NOT_FOUND,
                    status=status.HTTP_404_NOT_FOUND,
                )
            file, file_size = download_file(host_info, base_path, file_name)
            response = FileResponse(
                file,
                as_attachment=True,
                filename=str(file_name)
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
        except Exception as e:
            return APIResponse(
                message=f'文件下载异常: {e}',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
