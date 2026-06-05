"""
HTTP 访问日志中间件
=====================
记录每个 HTTP 请求的关键信息：客户端 IP、请求方法、路径、状态码、响应体大小、耗时。

日志格式示例:
    192.168.1.100 | "GET /host/hosts/ HTTP/1.1" 200 1234 45ms

配置方式:
    在 settings.py 的 MIDDLEWARE 中添加:
    'utils.middleware.AccessLogMiddleware'
"""
from django.http import FileResponse, StreamingHttpResponse
import logging
import time

# 自定义 logger，专门用于记录 HTTP 访问信息
http_logger = logging.getLogger("http.access")


class AccessLogMiddleware:
    """
    HTTP 访问日志中间件。

    在每个请求-响应周期中记录:
    - 客户端真实 IP（优先 X-Forwarded-For，回退到 REMOTE_ADDR）
    - HTTP 方法和完整路径
    - 响应状态码
    - 响应体大小（字节）
    - 请求耗时（毫秒）
    """

    def __init__(self, get_response):
        """
        Django 中间件标准构造方法。
        get_response: 下一个中间件或视图的可调用对象。
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        中间件入口 —— 在每个请求到来时被调用。

        流程:
        1. 记录请求开始时间
        2. 执行后续中间件/视图
        3. 计算耗时
        4. 提取客户端 IP（支持反向代理）
        5. 获取响应体大小（区分文件流和普通响应）
        6. 写入日志
        """
        t0 = time.time()
        response = self.get_response(request)
        cost = int((time.time() - t0) * 1000)  # 转换为毫秒

        # 获取真实客户端 IP（支持 Nginx 等反向代理）
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (
            x_forwarded.split(",")[0].strip()
            if x_forwarded
            else request.META.get("REMOTE_ADDR", "-")
        )

        # 获取响应体大小
        if isinstance(response, (FileResponse, StreamingHttpResponse)):
            # 文件/流式响应：从 Content-Length 头获取
            length = response.get('Content-Length') or 0
        else:
            # 普通响应：直接取 content 长度
            length = len(response.content)

        # 拼接日志: IP | "METHOD /path HTTP/1.1" 状态码 大小 耗时ms
        msg = (
            f'{ip} | '
            f'"{request.method} {request.get_full_path()} HTTP/1.1" '
            f'{response.status_code} {length} {cost}ms'
        )
        http_logger.info(msg)

        return response
