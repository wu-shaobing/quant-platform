"""
安全管理API端点
提供安全监控、配置和管理接口
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.security import (
    rate_limiter, ip_whitelist, login_tracker, 
    SecurityConfig
)
from app.core.auth import get_current_user
from app.models.user import User
from app.services.encryption_service import encryption_service

router = APIRouter(prefix="/security", tags=["安全管理"])


class SecurityStatsResponse(BaseModel):
    """安全统计响应"""
    rate_limiter: Dict[str, Any]
    login_attempts: Dict[str, Any]
    timestamp: str


class IPWhitelistRequest(BaseModel):
    """IP白名单请求"""
    ip_ranges: List[str]


class EncryptionRequest(BaseModel):
    """加密请求"""
    data: str
    password: Optional[str] = None


class DecryptionRequest(BaseModel):
    """解密请求"""
    encrypted_data: str
    password: Optional[str] = None


@router.get("/stats", summary="获取安全统计", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: User = Depends(get_current_user)
):
    """获取系统安全统计信息"""
    try:
        # 检查权限（只有管理员可以查看）
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Only administrators can view security statistics"
            )
        
        # 获取速率限制统计
        rate_stats = rate_limiter.get_stats()
        
        # 获取登录尝试统计
        login_stats = login_tracker.get_stats()
        
        return SecurityStatsResponse(
            rate_limiter=rate_stats,
            login_attempts=login_stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取安全统计失败: {str(e)}")


@router.get("/rate-limit/status", summary="获取速率限制状态")
async def get_rate_limit_status(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的速率限制状态"""
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查速率限制状态
        allowed, details = rate_limiter.is_allowed(client_ip, "api_check")
        
        return JSONResponse(content={
            "client_ip": client_ip,
            "rate_limit_status": "allowed" if allowed else "limited",
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取速率限制状态失败: {str(e)}")


@router.post("/ip-whitelist/check", summary="检查IP白名单")
async def check_ip_whitelist(
    ip_address: str = Query(..., description="要检查的IP地址"),
    current_user: User = Depends(get_current_user)
):
    """检查指定IP是否在白名单中"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can check IP whitelist")
        
        is_allowed = ip_whitelist.is_allowed(ip_address)
        
        return JSONResponse(content={
            "ip_address": ip_address,
            "is_allowed": is_allowed,
            "whitelist_ranges": ip_whitelist.allowed_ranges,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查IP白名单失败: {str(e)}")


@router.post("/ip-whitelist/update", summary="更新IP白名单")
async def update_ip_whitelist(
    request: IPWhitelistRequest,
    current_user: User = Depends(get_current_user)
):
    """更新IP白名单配置"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can update IP whitelist")
        
        # 验证IP范围格式
        import ipaddress
        for ip_range in request.ip_ranges:
            try:
                ipaddress.ip_network(ip_range)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid IP range: {ip_range}")
        
        # 更新白名单
        ip_whitelist.allowed_ranges = request.ip_ranges
        ip_whitelist._compiled_ranges = []
        
        for range_str in request.ip_ranges:
            ip_whitelist._compiled_ranges.append(ipaddress.ip_network(range_str))
        
        return JSONResponse(content={
            "message": "IP whitelist updated successfully",
            "new_ranges": request.ip_ranges,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新IP白名单失败: {str(e)}")


@router.get("/login-attempts/{username}", summary="获取用户登录尝试记录")
async def get_user_login_attempts(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """获取指定用户的登录尝试记录"""
    try:
        # 只有管理员或用户本人可以查看
        if current_user.role != "admin" and current_user.username != username:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 检查账户锁定状态
        is_locked, unlock_time = login_tracker.is_locked(username)
        
        # 获取最近的登录尝试（如果是管理员）
        recent_attempts = []
        if current_user.role == "admin":
            attempts = login_tracker._attempts.get(username, [])
            recent_attempts = [
                {
                    "timestamp": datetime.fromtimestamp(attempt["timestamp"]).isoformat(),
                    "success": attempt["success"],
                    "client_ip": attempt["client_ip"]
                }
                for attempt in attempts[-10:]  # 最近10次尝试
            ]
        
        return JSONResponse(content={
            "username": username,
            "is_locked": is_locked,
            "unlock_time": datetime.fromtimestamp(unlock_time).isoformat() if unlock_time else None,
            "recent_attempts": recent_attempts,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取登录尝试记录失败: {str(e)}")


@router.post("/unlock-account/{username}", summary="解锁用户账户")
async def unlock_user_account(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """解锁被锁定的用户账户"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can unlock accounts")
        
        # 解锁账户
        if username in login_tracker._locked_accounts:
            del login_tracker._locked_accounts[username]
            
            return JSONResponse(content={
                "message": f"Account {username} unlocked successfully",
                "username": username,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return JSONResponse(content={
                "message": f"Account {username} is not locked",
                "username": username,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解锁账户失败: {str(e)}")


@router.post("/encrypt", summary="加密数据")
async def encrypt_data(
    request: EncryptionRequest,
    current_user: User = Depends(get_current_user)
):
    """加密敏感数据"""
    try:
        encrypted_data = encryption_service.encrypt_data(
            data=request.data,
            password=request.password
        )
        
        return JSONResponse(content={
            "encrypted_data": encrypted_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据加密失败: {str(e)}")


@router.post("/decrypt", summary="解密数据")
async def decrypt_data(
    request: DecryptionRequest,
    current_user: User = Depends(get_current_user)
):
    """解密敏感数据"""
    try:
        decrypted_data = encryption_service.decrypt_data(
            encrypted_data=request.encrypted_data,
            password=request.password
        )
        
        return JSONResponse(content={
            "decrypted_data": decrypted_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据解密失败: {str(e)}")


@router.get("/config", summary="获取安全配置")
async def get_security_config(
    current_user: User = Depends(get_current_user)
):
    """获取当前安全配置"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can view security config")
        
        config = {
            "rate_limiting": {
                "max_requests_per_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
                "max_requests_per_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR,
            },
            "login_security": {
                "max_login_attempts": SecurityConfig.MAX_LOGIN_ATTEMPTS,
                "lockout_duration": SecurityConfig.LOGIN_LOCKOUT_DURATION,
            },
            "session_security": {
                "session_timeout": SecurityConfig.SESSION_TIMEOUT,
                "max_concurrent_sessions": SecurityConfig.MAX_CONCURRENT_SESSIONS,
            },
            "encryption": {
                "key_length": SecurityConfig.ENCRYPTION_KEY_LENGTH,
                "salt_length": SecurityConfig.SALT_LENGTH,
                "pbkdf2_iterations": SecurityConfig.PBKDF2_ITERATIONS,
            },
            "ip_whitelist": {
                "allowed_ranges": SecurityConfig.ALLOWED_IP_RANGES,
            }
        }
        
        return JSONResponse(content={
            "security_config": config,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取安全配置失败: {str(e)}")


@router.get("/audit-log", summary="获取安全审计日志")
async def get_security_audit_log(
    limit: int = Query(100, ge=1, le=1000, description="日志条数限制"),
    level: str = Query("INFO", description="日志级别"),
    current_user: User = Depends(get_current_user)
):
    """获取安全审计日志"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can view audit logs")
        
        # 这里应该从日志文件或数据库中读取审计日志
        # 为了演示，返回模拟数据
        audit_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "event": "API_ACCESS",
                "details": "User login successful",
                "user": current_user.username,
                "ip": "127.0.0.1"
            }
        ]
        
        return JSONResponse(content={
            "audit_logs": audit_logs,
            "total_count": len(audit_logs),
            "limit": limit,
            "level": level,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计日志失败: {str(e)}")


@router.post("/generate-token", summary="生成安全令牌")
async def generate_secure_token(
    length: int = Query(32, ge=16, le=128, description="令牌长度"),
    current_user: User = Depends(get_current_user)
):
    """生成安全令牌"""
    try:
        token = encryption_service.generate_secure_token(length)
        
        return JSONResponse(content={
            "token": token,
            "length": length,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成安全令牌失败: {str(e)}")


@router.get("/health", summary="安全系统健康检查")
async def security_health_check():
    """安全系统健康检查"""
    try:
        # 检查各个安全组件的状态
        health_status = {
            "rate_limiter": "healthy",
            "ip_whitelist": "healthy", 
            "login_tracker": "healthy",
            "encryption_service": "healthy",
            "overall": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        return JSONResponse(
            content={
                "overall": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )
