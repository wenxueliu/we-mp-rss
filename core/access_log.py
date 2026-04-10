"""
访问日志中间件
记录所有 HTTP 请求的访问信息
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.log import logger
from core.config import cfg


class AccessLogMiddleware(BaseHTTPMiddleware):
    """访问日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 记录开始时间
        start_time = time.time()

        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 获取用户代理
        user_agent = request.headers.get("user-agent", "-")

        # 获取认证用户名
        username = "-"
        if hasattr(request.state, "ak_auth"):
            username = "AK_USER"
        # 尝试从已认证的用户获取用户名
        if hasattr(request.state, "user"):
            username = getattr(request.state.user, "username", "AK_USER")

        # 获取请求路径和方法
        method = request.method
        path = request.url.path
        query = request.url.query

        # 记录请求
        logger.info(f" --> {method} {path}" +
                   (f"?{query}" if query else "") +
                   f" | from: {client_ip} | ua: {user_agent[:50]}")

        # 执行请求
        response = await call_next(request)

        # 计算响应时间
        process_time = (time.time() - start_time) * 1000  # 毫秒

        # 获取状态码
        status_code = response.status_code

        # 记录响应
        log_level = "info" if status_code < 400 else ("warning" if status_code < 500 else "error")
        log_func = getattr(logger, log_level)

        log_func(f" <-- {method} {path}" +
                (f"?{query}" if query else "") +
                f" | status: {status_code} | time: {process_time:.2f}ms | user: {username}")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 优先从 X-Forwarded-For 获取（反向代理场景）
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 最后使用客户端地址
        if request.client:
            return request.client.host

        return "-"
