# 安全相关 - CTP安全加固版本

import hashlib
import secrets
import time
import logging
import ipaddress
import json
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union, List, Tuple
from collections import defaultdict, deque
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer()


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_minutes = settings.REFRESH_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(
        self, 
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "access",
            "iat": datetime.utcnow(),
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建刷新令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.refresh_token_expire_minutes
            )
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "refresh",
            "iat": datetime.utcnow(),
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            return None
    
    def get_subject_from_token(self, token: str) -> Optional[str]:
        """从令牌中获取主题（通常是用户ID）"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """检查令牌是否过期"""
        payload = self.verify_token(token)
        if payload:
            exp = payload.get("exp")
            if exp:
                return datetime.utcnow() > datetime.fromtimestamp(exp)
        return True
    
    def get_token_type(self, token: str) -> Optional[str]:
        """获取令牌类型"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("type")
        return None
    
    def hash_password(self, password: str) -> str:
        """加密密码"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_password_reset_token(self, email: str) -> str:
        """生成密码重置令牌"""
        delta = timedelta(hours=1)  # 1小时有效期
        now = datetime.utcnow()
        expires = now + delta
        exp = expires.timestamp()
        encoded_jwt = jwt.encode(
            {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
            self.secret_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """验证密码重置令牌"""
        try:
            decoded_token = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            if decoded_token.get("type") != "password_reset":
                return None
            return decoded_token["sub"]
        except JWTError:
            return None
    
    def generate_api_key(self, user_id: str, name: str = "default") -> str:
        """生成API密钥"""
        timestamp = int(datetime.utcnow().timestamp())
        random_part = secrets.token_hex(16)
        key_data = f"{user_id}:{name}:{timestamp}:{random_part}"
        
        # 使用HMAC生成安全的API密钥
        api_key = hashlib.sha256(
            f"{self.secret_key}:{key_data}".encode()
        ).hexdigest()
        
        return f"qp_{api_key[:32]}"  # qp = quant platform
    
    def verify_api_key(self, api_key: str, user_id: str) -> bool:
        """验证API密钥"""
        # 这里应该从数据库验证API密钥
        # 暂时返回True，实际应用中需要实现数据库查询
        return api_key.startswith("qp_") and len(api_key) == 35
    
    def generate_totp_secret(self) -> str:
        """生成TOTP密钥（用于双因素认证）"""
        return secrets.token_hex(20)
    
    def create_session_token(self, user_id: str, device_info: str = "") -> str:
        """创建会话令牌"""
        timestamp = int(datetime.utcnow().timestamp())
        session_data = f"{user_id}:{device_info}:{timestamp}:{secrets.token_hex(16)}"
        
        session_token = hashlib.sha256(
            f"{self.secret_key}:session:{session_data}".encode()
        ).hexdigest()
        
        return f"sess_{session_token[:32]}"


# 全局安全管理器实例
security_manager = SecurityManager()


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌的便捷函数"""
    return security_manager.create_access_token(subject, expires_delta)


def create_refresh_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌的便捷函数"""
    return security_manager.create_refresh_token(subject, expires_delta)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码的便捷函数"""
    return security_manager.verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希的便捷函数"""
    return security_manager.hash_password(password)


def validate_password(password: str) -> Dict[str, Any]:
    """验证密码强度"""
    errors = []
    
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"密码长度至少{settings.PASSWORD_MIN_LENGTH}位")
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("密码必须包含大写字母")
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("密码必须包含小写字母")
    
    if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        errors.append("密码必须包含数字")
    
    if settings.PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("密码必须包含特殊字符")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": calculate_password_strength(password)
    }


def calculate_password_strength(password: str) -> str:
    """计算密码强度"""
    score = 0
    
    # 长度评分
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    # 字符类型评分
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    
    # 复杂度评分
    if len(set(password)) > len(password) * 0.7:  # 字符多样性
        score += 1
    
    if score <= 3:
        return "弱"
    elif score <= 5:
        return "中等"
    elif score <= 7:
        return "强"
    else:
        return "很强"


class PermissionChecker:
    """权限检查器"""
    
    @staticmethod
    def check_permission(user_permissions: list, required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        return required_permission in user_permissions
    
    @staticmethod
    def check_role(user_roles: list, required_role: str) -> bool:
        """检查用户是否有指定角色"""
        return required_role in user_roles
    
    @staticmethod
    def is_admin(user_roles: list) -> bool:
        """检查是否为管理员"""
        return "admin" in user_roles or "super_admin" in user_roles
    
    @staticmethod
    def is_trader(user_roles: list) -> bool:
        """检查是否为交易员"""
        return "trader" in user_roles or "admin" in user_roles
    
    @staticmethod
    def can_access_trading(user_permissions: list) -> bool:
        """检查是否可以访问交易功能"""
        trading_permissions = [
            "trading:read", "trading:write", "trading:execute"
        ]
        return any(perm in user_permissions for perm in trading_permissions)


# 权限检查器实例
permission_checker = PermissionChecker()


# 常用权限常量
class Permissions:
    """权限常量"""
    
    # 用户权限
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # 交易权限
    TRADING_READ = "trading:read"
    TRADING_WRITE = "trading:write"
    TRADING_EXECUTE = "trading:execute"
    TRADING_CANCEL = "trading:cancel"
    
    # 策略权限
    STRATEGY_READ = "strategy:read"
    STRATEGY_WRITE = "strategy:write"
    STRATEGY_EXECUTE = "strategy:execute"
    STRATEGY_DELETE = "strategy:delete"
    
    # 回测权限
    BACKTEST_READ = "backtest:read"
    BACKTEST_WRITE = "backtest:write"
    BACKTEST_EXECUTE = "backtest:execute"
    
    # 市场数据权限
    MARKET_READ = "market:read"
    MARKET_WRITE = "market:write"
    
    # 风险管理权限
    RISK_READ = "risk:read"
    RISK_WRITE = "risk:write"
    RISK_MANAGE = "risk:manage"
    
    # 系统管理权限
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_SYSTEM = "admin:system"


# 角色常量
class Roles:
    """角色常量"""
    
    SUPER_ADMIN = "super_admin"      # 超级管理员
    ADMIN = "admin"                  # 管理员
    TRADER = "trader"                # 交易员
    ANALYST = "analyst"              # 分析师
    VIEWER = "viewer"                # 查看者
    GUEST = "guest"                  # 访客


# CTP安全加固新增功能

class SecurityConfig:
    """安全配置"""

    # API安全配置
    MAX_REQUESTS_PER_MINUTE = 1000  # 每分钟最大请求数
    MAX_REQUESTS_PER_HOUR = 10000   # 每小时最大请求数
    MAX_LOGIN_ATTEMPTS = 5          # 最大登录尝试次数
    LOGIN_LOCKOUT_DURATION = 300    # 登录锁定时间（秒）

    # 数据加密配置
    ENCRYPTION_KEY_LENGTH = 32      # 加密密钥长度
    SALT_LENGTH = 16               # 盐值长度
    PBKDF2_ITERATIONS = 100000     # PBKDF2迭代次数

    # 会话安全配置
    SESSION_TIMEOUT = 3600         # 会话超时时间（秒）
    MAX_CONCURRENT_SESSIONS = 5    # 最大并发会话数

    # IP白名单配置
    ALLOWED_IP_RANGES = [
        "127.0.0.0/8",    # 本地回环
        "10.0.0.0/8",     # 私有网络A类
        "172.16.0.0/12",  # 私有网络B类
        "192.168.0.0/16", # 私有网络C类
    ]


class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self._requests = defaultdict(lambda: deque())
        self._blocked_ips = {}

    def is_allowed(self, client_ip: str, endpoint: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """检查是否允许请求"""
        current_time = time.time()
        key = f"{client_ip}:{endpoint}"

        # 检查IP是否被阻止
        if client_ip in self._blocked_ips:
            if current_time < self._blocked_ips[client_ip]:
                return False, {
                    "error": "IP blocked due to rate limiting",
                    "blocked_until": self._blocked_ips[client_ip]
                }
            else:
                del self._blocked_ips[client_ip]

        # 获取请求历史
        request_times = self._requests[key]

        # 清理过期的请求记录
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        while request_times and request_times[0] < hour_ago:
            request_times.popleft()

        # 统计最近一分钟和一小时的请求数
        minute_requests = sum(1 for t in request_times if t > minute_ago)
        hour_requests = len(request_times)

        # 检查速率限制
        if minute_requests >= SecurityConfig.MAX_REQUESTS_PER_MINUTE:
            self._blocked_ips[client_ip] = current_time + 60  # 阻止1分钟
            return False, {
                "error": "Rate limit exceeded (per minute)",
                "requests_per_minute": minute_requests,
                "limit": SecurityConfig.MAX_REQUESTS_PER_MINUTE
            }

        if hour_requests >= SecurityConfig.MAX_REQUESTS_PER_HOUR:
            self._blocked_ips[client_ip] = current_time + 300  # 阻止5分钟
            return False, {
                "error": "Rate limit exceeded (per hour)",
                "requests_per_hour": hour_requests,
                "limit": SecurityConfig.MAX_REQUESTS_PER_HOUR
            }

        # 记录当前请求
        request_times.append(current_time)

        return True, {
            "requests_per_minute": minute_requests + 1,
            "requests_per_hour": hour_requests + 1,
            "remaining_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE - minute_requests - 1,
            "remaining_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR - hour_requests - 1
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取速率限制统计"""
        current_time = time.time()
        active_clients = len([
            key for key, times in self._requests.items()
            if times and times[-1] > current_time - 3600
        ])

        return {
            "active_clients": active_clients,
            "blocked_ips": len(self._blocked_ips),
            "total_tracked_endpoints": len(self._requests)
        }


class IPWhitelistValidator:
    """IP白名单验证器"""

    def __init__(self, allowed_ranges: List[str] = None):
        self.allowed_ranges = allowed_ranges or SecurityConfig.ALLOWED_IP_RANGES
        self._compiled_ranges = []

        for range_str in self.allowed_ranges:
            try:
                self._compiled_ranges.append(ipaddress.ip_network(range_str))
            except ValueError as e:
                logger.error(f"Invalid IP range {range_str}: {e}")

    def is_allowed(self, client_ip: str) -> bool:
        """检查IP是否在白名单中"""
        try:
            client_addr = ipaddress.ip_address(client_ip)

            for network in self._compiled_ranges:
                if client_addr in network:
                    return True

            return False

        except ValueError:
            logger.error(f"Invalid IP address: {client_ip}")
            return False


class LoginAttemptTracker:
    """登录尝试跟踪器"""

    def __init__(self):
        self._attempts = defaultdict(list)
        self._locked_accounts = {}

    def record_attempt(self, username: str, success: bool, client_ip: str):
        """记录登录尝试"""
        current_time = time.time()

        # 清理过期记录
        self._cleanup_expired_attempts(username)

        # 记录尝试
        self._attempts[username].append({
            "timestamp": current_time,
            "success": success,
            "client_ip": client_ip
        })

        # 检查是否需要锁定账户
        if not success:
            failed_attempts = [
                attempt for attempt in self._attempts[username]
                if not attempt["success"] and
                current_time - attempt["timestamp"] < 300  # 5分钟内
            ]

            if len(failed_attempts) >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                self._locked_accounts[username] = current_time + SecurityConfig.LOGIN_LOCKOUT_DURATION
                logger.warning(f"Account {username} locked due to multiple failed login attempts")

    def is_locked(self, username: str) -> Tuple[bool, Optional[float]]:
        """检查账户是否被锁定"""
        if username in self._locked_accounts:
            unlock_time = self._locked_accounts[username]
            if time.time() < unlock_time:
                return True, unlock_time
            else:
                del self._locked_accounts[username]

        return False, None

    def _cleanup_expired_attempts(self, username: str):
        """清理过期的登录尝试记录"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 保留1小时内的记录

        if username in self._attempts:
            self._attempts[username] = [
                attempt for attempt in self._attempts[username]
                if attempt["timestamp"] > cutoff_time
            ]


# 全局安全组件实例
security_manager = SecurityManager()
rate_limiter = RateLimiter()
ip_whitelist = IPWhitelistValidator()
login_tracker = LoginAttemptTracker()
permission_checker = PermissionChecker()

# 全局便捷函数
def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证令牌的全局函数"""
    return security_manager.verify_token(token)


# 导出主要组件
__all__ = [
    "security_manager",
    "create_access_token",
    "create_refresh_token",
    "verify_password",
    "get_password_hash",
    "validate_password",
    "calculate_password_strength",
    "permission_checker",
    "Permissions",
    "Roles",
    "security",
    # 新增安全功能
    "SecurityConfig",
    "RateLimiter",
    "IPWhitelistValidator",
    "LoginAttemptTracker",
    "rate_limiter",
    "ip_whitelist",
    "login_tracker",
]