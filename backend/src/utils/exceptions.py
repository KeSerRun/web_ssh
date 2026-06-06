"""
全局异常处理与统一响应模块
===========================
提供两大功能:
    1. APIResponse — 统一成功/失败响应的快捷构造器
    2. custom_exception_handler — DRF 全局异常处理器

所有 API 返回严格遵循统一格式:
    {"code": <http_status>, "message": "<描述>", "data": <数据|null>}

成功示例:
    {"code": 200, "message": "ok", "data": {...}}
    {"code": 201, "message": "创建成功", "data": {...}}

错误示例:
    {"code": 400, "message": "用户名不能为空", "data": null}
    {"code": 403, "message": "权限不足：仅超级管理员可操作", "data": null}
    {"code": 500, "message": "服务器内部错误", "data": null}
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response

# 字段名 → 中文标签映射（用于错误提示）
FIELD_LABELS = {
    'ip_addr': 'IP地址', 'port': '端口', 'username': '用户名',
    'connect_pwd': '连接密码', 'name': '主机名称', 'category': '分类',
    'remark': '备注', 'password': '密码', 'mobile': '手机号',
    'hosts': '关联主机', 'is_active': '激活状态', 'is_staff': '员工权限',
    'is_superuser': '超级管理员', 'avatar': '头像', 'sex': '性别',
}


def APIResponse(data='__no_data__', message='ok', code=None, status=None):
    """
    统一 API 响应构造器。

    约定:
        - 成功时不传 code 和 status，默认 200
        - 失败时必须传 code 和 status（通常二者相同）
        - data 为 None 表示错误响应；data 为 dict/list 表示成功数据
        - 传入 data='__no_data__'（哨兵值）时，不包含 data 字段（兼容旧接口）

    Args:
        data:    响应数据（dict/list/None/sentinel）
        message: 提示文本
        code:    业务状态码（默认等于 HTTP 状态码）
        status:  HTTP 状态码

    Returns:
        Response 对象

    Examples:
        # 成功，带数据
        APIResponse(data={'id': 1, 'name': 'test'})
        → {"code": 200, "message": "ok", "data": {"id": 1, "name": "test"}}

        # 成功，自定义消息
        APIResponse(data={'id': 1}, message='创建成功', code=201, status=201)

        # 业务错误
        APIResponse(message='缺少文件', code=400, status=400)
        → {"code": 400, "message": "缺少文件", "data": null}

        # 权限拒绝
        APIResponse(message='无权操作', code=403, status=403)

        # 服务器错误
        APIResponse(message='SSH 连接失败', code=500, status=500)
    """
    if code is None:
        code = 200
    if status is None:
        status = code

    # 哨兵值表示不传 data，兼容老接口的纯文本响应
    if data == '__no_data__':
        return Response({'code': code, 'message': message}, status=status)

    # data 显式传入 None → 错误响应
    if data is None:
        return Response({'code': code, 'message': message, 'data': None}, status=status)

    # 正常数据响应
    return Response({'code': code, 'message': message, 'data': data}, status=status)


def custom_exception_handler(exc, context):
    """
    DRF 全局异常处理器。

    处理流程:
        1. 先调用 DRF 默认处理器获取标准错误响应（含验证错误、404、权限拒绝等）
        2. 将响应统一包装为 {code, message, data} 格式
        3. DRF 未处理的异常（如 Django 原生 500）统一返回 500

    错误信息提取策略:
        优先取 response.data 中的 detail，若为字典（字段级错误）则序列化为 JSON 字符串。

    Args:
        exc:     异常对象
        context: DRF 上下文

    Returns:
        Response: 统一格式的错误响应
    """
    # 1. DRF 默认处理
    response = exception_handler(exc, context)

    if response is not None:
        # 2. 提取错误信息
        detail = response.data
        if isinstance(detail, dict):
            # 字段级验证错误 → 格式化为可读字符串
            # 例: {"password": ["密码长度不足"]}  → "password: 密码长度不足"
            messages = []
            for field, errors in detail.items():
                label = FIELD_LABELS.get(field, field)
                if isinstance(errors, list):
                    messages.append(f"{label}: {'; '.join(str(e) for e in errors)}")
                else:
                    messages.append(f"{label}: {errors}")
            message = '; '.join(messages)
        elif isinstance(detail, list):
            message = '; '.join(str(d) for d in detail)
        else:
            message = str(detail) if detail else str(exc)

        return Response({
            'code': response.status_code,
            'message': message,
            'data': None
        }, status=response.status_code)

    # 3. DRF 未处理 → 500
    return Response({
        'code': 500,
        'message': '服务器内部错误，请联系管理员',
        'data': None
    }, status=500)
