"""
安全中间件
提供API安全防护、速率限制、IP白名单等功能
"""
import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import rate_limiter, ip_whitelist, login_tracker
from app.core.security_hardening import security_hardening, AuditEvent, AuditEventType, SecurityLevel
from app.core.auth import get_user_from_token
import json
import ipaddress

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app, enable_rate_limiting: bool = True, enable_ip_whitelist: bool = False):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_ip_whitelist = enable_ip_whitelist
        
        # 不需要安全检查的路径
        self.excluded_paths = {
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/metrics",
            "/favicon.ico"
        }
        
        # 需要特殊处理的敏感端点
        self.sensitive_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/ctp/connect",
            "/api/v1/ctp/order",
            "/api/v1/ctp/trade",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        endpoint = request.url.path
        method = request.method
        
        # 跳过排除的路径
        if endpoint in self.excluded_paths:
            return await call_next(request)
        
        try:
            # 1. IP白名单检查
            if self.enable_ip_whitelist and not self._check_ip_whitelist(client_ip):
                logger.warning(f"IP {client_ip} not in whitelist, blocking request to {endpoint}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Access denied", "message": "IP not in whitelist"}
                )
            
            # 2. 速率限制检查
            if self.enable_rate_limiting:
                rate_check_result = self._check_rate_limit(client_ip, endpoint)
                if not rate_check_result["allowed"]:
                    logger.warning(f"Rate limit exceeded for IP {client_ip} on {endpoint}")
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "message": rate_check_result["message"],
                            "retry_after": rate_check_result.get("retry_after", 60)
                        },
                        headers={"Retry-After": str(rate_check_result.get("retry_after", 60))}
                    )
            
            # 3. 添加安全头
            request.state.security_headers = self._get_security_headers()
            request.state.client_ip = client_ip
            request.state.start_time = start_time
            
            # 4. 处理请求
            response = await call_next(request)
            
            # 5. 添加安全响应头
            for header, value in request.state.security_headers.items():
                response.headers[header] = value
            
            # 6. 记录访问日志
            self._log_request(request, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # 发生错误时也要记录
            self._log_security_event("middleware_error", {
                "client_ip": client_ip,
                "endpoint": endpoint,
                "error": str(e)
            })
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 使用客户端地址
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _check_ip_whitelist(self, client_ip: str) -> bool:
        """检查IP白名单"""
        try:
            return ip_whitelist.is_allowed(client_ip)
        except Exception as e:
            logger.error(f"IP whitelist check error: {e}")
            return False
    
    def _check_rate_limit(self, client_ip: str, endpoint: str) -> Dict[str, Any]:
        """检查速率限制"""
        try:
            allowed, details = rate_limiter.is_allowed(client_ip, endpoint)
            
            if allowed:
                return {
                    "allowed": True,
                    "details": details
                }
            else:
                return {
                    "allowed": False,
                    "message": details.get("error", "Rate limit exceeded"),
                    "retry_after": 60 if "minute" in details.get("error", "") else 300
                }
                
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return {"allowed": True}  # 出错时允许通过
    
    def _get_security_headers(self) -> Dict[str, str]:
        """获取安全响应头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    
    def _log_request(self, request: Request, response: Response, duration: float):
        """记录请求日志"""
        try:
            client_ip = getattr(request.state, "client_ip", "unknown")
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code
            user_agent = request.headers.get("user-agent", "")
            
            # 记录基本访问日志
            logger.info(
                f"API_ACCESS - {method} {endpoint} - {status_code} - "
                f"{client_ip} - {duration:.3f}s - {user_agent}"
            )
            
            # 记录敏感端点访问
            if endpoint in self.sensitive_endpoints:
                self._log_security_event("sensitive_endpoint_access", {
                    "endpoint": endpoint,
                    "method": method,
                    "client_ip": client_ip,
                    "status_code": status_code,
                    "duration": duration
                })
            
        except Exception as e:
            logger.error(f"Request logging error: {e}")
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """记录安全事件"""
        try:
            logger.warning(f"SECURITY_EVENT - {event_type} - {details}")
        except Exception as e:
            logger.error(f"Security event logging error: {e}")


class LoginSecurityMiddleware(BaseHTTPMiddleware):
    """登录安全中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.login_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/token",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理登录请求"""
        endpoint = request.url.path
        
        # 只处理登录端点
        if endpoint not in self.login_endpoints:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        # 处理请求
        response = await call_next(request)
        
        # 记录登录尝试
        if hasattr(request.state, "login_attempt"):
            attempt_info = request.state.login_attempt
            login_tracker.record_attempt(
                username=attempt_info.get("username", "unknown"),
                success=attempt_info.get("success", False),
                client_ip=client_ip
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """CORS安全中间件"""
    
    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000", 
            "http://127.0.0.1:5173",
            "https://localhost:3000",
            "https://localhost:5173",
        ]
        logger.info(f"CORS allowed origins: {self.allowed_origins}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理CORS请求"""
        origin = request.headers.get("origin")
        logger.debug(f"CORS request - Origin: {origin}, Method: {request.method}, Path: {request.url.path}")
        
        # 处理预检请求
        if request.method == "OPTIONS":
            logger.debug("Handling CORS preflight request")
            response = Response()
            
            # 设置CORS头
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
                response.headers["Access-Control-Allow-Headers"] = ", ".join([
                    "Accept",
                    "Accept-Language", 
                    "Content-Language",
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "X-Request-ID",
                    "X-Timestamp",
                    "Cache-Control",
                    "Pragma"
                ])
                response.headers["Access-Control-Max-Age"] = "86400"  # 24小时
                logger.debug(f"CORS preflight approved for origin: {origin}")
            else:
                logger.warning(f"CORS preflight rejected for origin: {origin}")
                response.status_code = 403
            
            return response
        
        # 处理实际请求
        response = await call_next(request)
        
        # 为所有响应添加CORS头
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Range, X-Request-ID"
            logger.debug(f"CORS headers added for origin: {origin}")
        
        return response


# 导出中间件
__all__ = [
    "SecurityMiddleware",
    "LoginSecurityMiddleware", 
    "CORSSecurityMiddleware",
]
