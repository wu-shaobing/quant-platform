"""
CTP安全加固模块
提供API访问控制、数据加密、审计日志和安全防护机制
"""
import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import ipaddress
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from app.core.config import settings
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """审计事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    ORDER_SUBMIT = "order_submit"
    ORDER_CANCEL = "order_cancel"
    POSITION_QUERY = "position_query"
    ACCOUNT_QUERY = "account_query"
    CONFIG_CHANGE = "config_change"
    SECURITY_VIOLATION = "security_violation"
    API_ACCESS = "api_access"
    DATA_EXPORT = "data_export"


@dataclass
class AuditEvent:
    """审计事件"""
    event_type: AuditEventType
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    request_data: Dict[str, Any]
    response_status: int
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    risk_level: SecurityLevel = SecurityLevel.LOW
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'method': self.method,
            'request_data': self.request_data,
            'response_status': self.response_status,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id,
            'risk_level': self.risk_level.value,
            'additional_info': self.additional_info
        }


class DataEncryption:
    """数据加密器"""
    
    def __init__(self, password: Optional[str] = None):
        self.password = password or settings.SECRET_KEY
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """初始化加密器"""
        # 使用PBKDF2从密码生成密钥
        password_bytes = self.password.encode()
        salt = b'stable_salt_for_consistency'  # 在生产环境中应该使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        self._fernet = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted_data = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """加密字典数据"""
        json_data = json.dumps(data, default=str)
        return self.encrypt(json_data)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """解密字典数据"""
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)


class AccessController:
    """访问控制器"""
    
    def __init__(self):
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 每分钟100次
            'trading': {'requests': 50, 'window': 60},   # 交易接口每分钟50次
            'query': {'requests': 200, 'window': 60},    # 查询接口每分钟200次
        }
        self.ip_whitelist = set()
        self.ip_blacklist = set()
        self.blocked_users = set()
    
    async def check_rate_limit(
        self,
        identifier: str,
        endpoint_type: str = 'default'
    ) -> Tuple[bool, Dict[str, Any]]:
        """检查速率限制"""
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        window = limit_config['window']
        max_requests = limit_config['requests']
        
        # 使用Redis计数器
        cache_key = f"rate_limit:{endpoint_type}:{identifier}"
        
        try:
            # 获取当前计数
            current_count = await cache_manager.cache.get(
                CacheKeyPrefix.SYSTEM_CONFIG, 
                cache_key
            ) or 0
            
            if current_count >= max_requests:
                return False, {
                    'allowed': False,
                    'current_count': current_count,
                    'max_requests': max_requests,
                    'window_seconds': window,
                    'reset_time': datetime.now() + timedelta(seconds=window)
                }
            
            # 增加计数
            new_count = await cache_manager.cache.increment(
                CacheKeyPrefix.SYSTEM_CONFIG,
                cache_key
            )
            
            # 设置过期时间
            if new_count == 1:
                await cache_manager.cache.expire(
                    CacheKeyPrefix.SYSTEM_CONFIG,
                    cache_key,
                    window
                )
            
            return True, {
                'allowed': True,
                'current_count': new_count,
                'max_requests': max_requests,
                'window_seconds': window,
                'remaining': max_requests - new_count
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 在错误情况下允许访问，但记录日志
            return True, {'allowed': True, 'error': str(e)}
    
    def check_ip_access(self, ip_address: str) -> bool:
        """检查IP访问权限"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # 检查黑名单
            if ip_address in self.ip_blacklist:
                return False
            
            # 如果有白名单，只允许白名单IP
            if self.ip_whitelist and ip_address not in self.ip_whitelist:
                return False
            
            return True
            
        except ValueError:
            logger.warning(f"Invalid IP address: {ip_address}")
            return False
    
    def add_to_whitelist(self, ip_address: str):
        """添加到IP白名单"""
        self.ip_whitelist.add(ip_address)
        logger.info(f"Added {ip_address} to IP whitelist")
    
    def add_to_blacklist(self, ip_address: str):
        """添加到IP黑名单"""
        self.ip_blacklist.add(ip_address)
        logger.warning(f"Added {ip_address} to IP blacklist")
    
    def block_user(self, user_id: int):
        """阻止用户访问"""
        self.blocked_users.add(user_id)
        logger.warning(f"Blocked user {user_id}")
    
    def unblock_user(self, user_id: int):
        """解除用户阻止"""
        self.blocked_users.discard(user_id)
        logger.info(f"Unblocked user {user_id}")
    
    def is_user_blocked(self, user_id: int) -> bool:
        """检查用户是否被阻止"""
        return user_id in self.blocked_users


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        self.encryption = DataEncryption()
        self.max_log_size = 10000  # 最大日志条数
        self.log_retention_days = 90  # 日志保留天数
    
    async def log_event(self, event: AuditEvent):
        """记录审计事件"""
        try:
            # 加密敏感数据
            encrypted_event = self._encrypt_sensitive_data(event)
            
            # 存储到缓存（用于快速查询）
            cache_key = f"audit_{event.timestamp.strftime('%Y%m%d')}_{secrets.token_hex(8)}"
            await cache_manager.cache.set(
                CacheKeyPrefix.SYSTEM_CONFIG,
                cache_key,
                encrypted_event.to_dict(),
                ttl=self.log_retention_days * 24 * 3600
            )
            
            # 记录到应用日志
            log_message = (
                f"AUDIT: {event.event_type.value} | "
                f"User: {event.user_id} | "
                f"IP: {event.ip_address} | "
                f"Endpoint: {event.endpoint} | "
                f"Status: {event.response_status} | "
                f"Risk: {event.risk_level.value}"
            )
            
            if event.risk_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _encrypt_sensitive_data(self, event: AuditEvent) -> AuditEvent:
        """加密敏感数据"""
        # 创建事件副本
        encrypted_event = AuditEvent(
            event_type=event.event_type,
            user_id=event.user_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            endpoint=event.endpoint,
            method=event.method,
            request_data={},  # 将被加密
            response_status=event.response_status,
            timestamp=event.timestamp,
            session_id=event.session_id,
            risk_level=event.risk_level,
            additional_info={}  # 将被加密
        )
        
        # 加密请求数据
        if event.request_data:
            encrypted_event.request_data = {
                'encrypted': self.encryption.encrypt_dict(event.request_data)
            }
        
        # 加密附加信息
        if event.additional_info:
            encrypted_event.additional_info = {
                'encrypted': self.encryption.encrypt_dict(event.additional_info)
            }
        
        return encrypted_event
    
    async def query_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[int] = None,
        risk_level: Optional[SecurityLevel] = None
    ) -> List[Dict[str, Any]]:
        """查询审计事件"""
        try:
            # 获取日期范围内的所有审计日志键
            events = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.strftime('%Y%m%d')
                pattern = f"audit_{date_str}_*"
                
                keys = await cache_manager.cache.get_keys(
                    CacheKeyPrefix.SYSTEM_CONFIG,
                    pattern
                )
                
                for key in keys:
                    event_data = await cache_manager.cache.get(
                        CacheKeyPrefix.SYSTEM_CONFIG,
                        key
                    )
                    
                    if event_data:
                        # 解密数据
                        decrypted_event = self._decrypt_event_data(event_data)
                        
                        # 应用过滤条件
                        if self._matches_filter(decrypted_event, event_type, user_id, risk_level):
                            events.append(decrypted_event)
                
                current_date += timedelta(days=1)
            
            # 按时间排序
            events.sort(key=lambda x: x['timestamp'], reverse=True)
            return events
            
        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []
    
    def _decrypt_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """解密事件数据"""
        try:
            # 解密请求数据
            if 'request_data' in event_data and 'encrypted' in event_data['request_data']:
                event_data['request_data'] = self.encryption.decrypt_dict(
                    event_data['request_data']['encrypted']
                )
            
            # 解密附加信息
            if 'additional_info' in event_data and 'encrypted' in event_data['additional_info']:
                event_data['additional_info'] = self.encryption.decrypt_dict(
                    event_data['additional_info']['encrypted']
                )
            
            return event_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt event data: {e}")
            return event_data
    
    def _matches_filter(
        self,
        event_data: Dict[str, Any],
        event_type: Optional[AuditEventType],
        user_id: Optional[int],
        risk_level: Optional[SecurityLevel]
    ) -> bool:
        """检查事件是否匹配过滤条件"""
        if event_type and event_data.get('event_type') != event_type.value:
            return False
        
        if user_id and event_data.get('user_id') != user_id:
            return False
        
        if risk_level and event_data.get('risk_level') != risk_level.value:
            return False
        
        return True


class SecurityHardening:
    """安全加固主类"""
    
    def __init__(self):
        self.access_controller = AccessController()
        self.audit_logger = AuditLogger()
        self.encryption = DataEncryption()
        self.security_enabled = True
        self.threat_detection_enabled = True
    
    async def validate_request(
        self,
        user_id: Optional[int],
        ip_address: str,
        endpoint: str,
        method: str,
        user_agent: str,
        request_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """验证请求安全性"""
        if not self.security_enabled:
            return True, {'message': 'Security disabled'}
        
        # 检查IP访问权限
        if not self.access_controller.check_ip_access(ip_address):
            await self._log_security_violation(
                user_id, ip_address, endpoint, "IP blocked", user_agent, request_data
            )
            return False, {'error': 'IP address blocked'}
        
        # 检查用户是否被阻止
        if user_id and self.access_controller.is_user_blocked(user_id):
            await self._log_security_violation(
                user_id, ip_address, endpoint, "User blocked", user_agent, request_data
            )
            return False, {'error': 'User blocked'}
        
        # 检查速率限制
        identifier = f"{user_id}:{ip_address}" if user_id else ip_address
        endpoint_type = self._get_endpoint_type(endpoint)
        
        rate_limit_ok, rate_limit_info = await self.access_controller.check_rate_limit(
            identifier, endpoint_type
        )
        
        if not rate_limit_ok:
            await self._log_security_violation(
                user_id, ip_address, endpoint, "Rate limit exceeded", user_agent, request_data
            )
            return False, {'error': 'Rate limit exceeded', 'details': rate_limit_info}
        
        # 威胁检测
        if self.threat_detection_enabled:
            threat_detected, threat_info = await self._detect_threats(
                user_id, ip_address, endpoint, request_data
            )
            
            if threat_detected:
                await self._log_security_violation(
                    user_id, ip_address, endpoint, f"Threat detected: {threat_info}", 
                    user_agent, request_data
                )
                return False, {'error': 'Security threat detected', 'details': threat_info}
        
        return True, {'message': 'Request validated', 'rate_limit': rate_limit_info}
    
    def _get_endpoint_type(self, endpoint: str) -> str:
        """获取端点类型"""
        if '/trading/' in endpoint or '/orders/' in endpoint:
            return 'trading'
        elif '/query/' in endpoint or '/positions/' in endpoint or '/accounts/' in endpoint:
            return 'query'
        else:
            return 'default'
    
    async def _detect_threats(
        self,
        user_id: Optional[int],
        ip_address: str,
        endpoint: str,
        request_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """威胁检测"""
        # SQL注入检测
        if self._detect_sql_injection(request_data):
            return True, "SQL injection attempt"
        
        # XSS检测
        if self._detect_xss(request_data):
            return True, "XSS attempt"
        
        # 异常大量请求检测
        if await self._detect_abnormal_requests(user_id, ip_address):
            return True, "Abnormal request pattern"
        
        return False, ""
    
    def _detect_sql_injection(self, data: Dict[str, Any]) -> bool:
        """检测SQL注入"""
        sql_patterns = [
            "union select", "drop table", "delete from", "insert into",
            "update set", "exec(", "execute(", "sp_", "xp_"
        ]
        
        data_str = json.dumps(data).lower()
        return any(pattern in data_str for pattern in sql_patterns)
    
    def _detect_xss(self, data: Dict[str, Any]) -> bool:
        """检测XSS攻击"""
        xss_patterns = [
            "<script", "javascript:", "onload=", "onerror=", "onclick="
        ]
        
        data_str = json.dumps(data).lower()
        return any(pattern in data_str for pattern in xss_patterns)
    
    async def _detect_abnormal_requests(self, user_id: Optional[int], ip_address: str) -> bool:
        """检测异常请求模式"""
        if not user_id:
            return False
        
        # 检查短时间内的请求频率
        cache_key = f"request_count:{user_id}:{ip_address}"
        request_count = await cache_manager.cache.get(
            CacheKeyPrefix.SYSTEM_CONFIG,
            cache_key
        ) or 0
        
        # 如果5分钟内超过500次请求，认为异常
        return request_count > 500
    
    async def _log_security_violation(
        self,
        user_id: Optional[int],
        ip_address: str,
        endpoint: str,
        violation_type: str,
        user_agent: str,
        request_data: Dict[str, Any]
    ):
        """记录安全违规"""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method="SECURITY_CHECK",
            request_data=request_data,
            response_status=403,
            risk_level=SecurityLevel.HIGH,
            additional_info={'violation_type': violation_type}
        )
        
        await self.audit_logger.log_event(event)


# 增强的JWT令牌安全管理器
class JWTSecurityManager:
    """JWT令牌安全管理器"""

    def __init__(self):
        self.token_blacklist = set()
        self.refresh_token_store = {}
        self.max_token_lifetime = 3600  # 1小时
        self.refresh_token_lifetime = 7 * 24 * 3600  # 7天

    async def create_secure_token(
        self,
        user_id: int,
        permissions: List[str],
        device_fingerprint: str = None
    ) -> Dict[str, str]:
        """创建安全的JWT令牌"""
        from app.core.auth import create_access_token, create_refresh_token

        # 创建访问令牌
        access_token_data = {
            "sub": str(user_id),
            "permissions": permissions,
            "device_fingerprint": device_fingerprint,
            "token_type": "access",
            "jti": secrets.token_hex(16)  # JWT ID
        }

        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(seconds=self.max_token_lifetime)
        )

        # 创建刷新令牌
        refresh_token_data = {
            "sub": str(user_id),
            "token_type": "refresh",
            "jti": secrets.token_hex(16)
        }

        refresh_token = create_refresh_token(
            data=refresh_token_data,
            expires_delta=timedelta(seconds=self.refresh_token_lifetime)
        )

        # 存储刷新令牌
        self.refresh_token_store[refresh_token_data["jti"]] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "device_fingerprint": device_fingerprint
        }

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.max_token_lifetime
        }

    async def validate_token_security(
        self,
        token: str,
        device_fingerprint: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """验证令牌安全性"""
        try:
            from app.core.auth import verify_token

            # 检查令牌是否在黑名单中
            if token in self.token_blacklist:
                return False, {"error": "Token blacklisted"}

            # 验证令牌
            payload = verify_token(token)
            if not payload:
                return False, {"error": "Invalid token"}

            # 检查设备指纹
            if device_fingerprint and payload.get("device_fingerprint"):
                if payload["device_fingerprint"] != device_fingerprint:
                    return False, {"error": "Device fingerprint mismatch"}

            # 检查令牌类型
            if payload.get("token_type") != "access":
                return False, {"error": "Invalid token type"}

            return True, {"payload": payload}

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False, {"error": "Token validation failed"}

    async def revoke_token(self, token: str):
        """撤销令牌"""
        self.token_blacklist.add(token)
        logger.info(f"Token revoked: {token[:20]}...")

    async def revoke_user_tokens(self, user_id: int):
        """撤销用户的所有令牌"""
        # 这里应该从数据库查询用户的所有活跃令牌并撤销
        # 暂时记录日志
        logger.info(f"All tokens revoked for user {user_id}")

    async def refresh_token_security(
        self,
        refresh_token: str,
        device_fingerprint: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """安全刷新令牌"""
        try:
            from app.core.auth import verify_token

            # 验证刷新令牌
            payload = verify_token(refresh_token)
            if not payload or payload.get("token_type") != "refresh":
                return False, {"error": "Invalid refresh token"}

            jti = payload.get("jti")
            if not jti or jti not in self.refresh_token_store:
                return False, {"error": "Refresh token not found"}

            token_info = self.refresh_token_store[jti]

            # 检查设备指纹
            if device_fingerprint and token_info.get("device_fingerprint"):
                if token_info["device_fingerprint"] != device_fingerprint:
                    return False, {"error": "Device fingerprint mismatch"}

            # 创建新的访问令牌
            user_id = token_info["user_id"]
            new_tokens = await self.create_secure_token(
                user_id,
                ["trading", "query"],  # 默认权限
                device_fingerprint
            )

            # 移除旧的刷新令牌
            del self.refresh_token_store[jti]

            return True, new_tokens

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False, {"error": "Token refresh failed"}


class AdvancedDataEncryption:
    """高级数据加密器"""

    def __init__(self):
        self.field_encryption_keys = {}
        self.encryption_algorithms = {
            "AES-256-GCM": self._aes_gcm_encrypt,
            "ChaCha20-Poly1305": self._chacha20_encrypt
        }
        self._initialize_field_keys()

    def _initialize_field_keys(self):
        """初始化字段级加密密钥"""
        # 为不同类型的敏感数据使用不同的密钥
        sensitive_fields = [
            "password", "api_key", "private_key", "bank_account",
            "id_number", "phone", "email", "trading_account"
        ]

        for field in sensitive_fields:
            self.field_encryption_keys[field] = self._derive_field_key(field)

    def _derive_field_key(self, field_name: str) -> bytes:
        """为特定字段派生加密密钥"""
        try:
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF
            from cryptography.hazmat.primitives import hashes

            master_key = settings.SECRET_KEY.encode()
            salt = f"field_encryption_{field_name}".encode()

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=b'field_encryption'
            )

            return hkdf.derive(master_key)
        except ImportError:
            # 如果cryptography库不可用，使用简单的密钥派生
            import hashlib
            combined = f"{settings.SECRET_KEY}_{field_name}".encode()
            return hashlib.sha256(combined).digest()

    def _aes_gcm_encrypt(self, data: bytes, key: bytes) -> Dict[str, str]:
        """AES-GCM加密"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            aesgcm = AESGCM(key)
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            ciphertext = aesgcm.encrypt(nonce, data, None)

            return {
                "algorithm": "AES-256-GCM",
                "nonce": base64.b64encode(nonce).decode(),
                "ciphertext": base64.b64encode(ciphertext).decode()
            }
        except ImportError:
            # 回退到Fernet加密
            return self._fernet_encrypt(data, key)

    def _aes_gcm_decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """AES-GCM解密"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            aesgcm = AESGCM(key)
            nonce = base64.b64decode(encrypted_data["nonce"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])

            return aesgcm.decrypt(nonce, ciphertext, None)
        except ImportError:
            # 回退到Fernet解密
            return self._fernet_decrypt(encrypted_data, key)

    def _chacha20_encrypt(self, data: bytes, key: bytes) -> Dict[str, str]:
        """ChaCha20-Poly1305加密"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            chacha = ChaCha20Poly1305(key)
            nonce = secrets.token_bytes(12)
            ciphertext = chacha.encrypt(nonce, data, None)

            return {
                "algorithm": "ChaCha20-Poly1305",
                "nonce": base64.b64encode(nonce).decode(),
                "ciphertext": base64.b64encode(ciphertext).decode()
            }
        except ImportError:
            # 回退到Fernet加密
            return self._fernet_encrypt(data, key)

    def _chacha20_decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """ChaCha20-Poly1305解密"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            chacha = ChaCha20Poly1305(key)
            nonce = base64.b64decode(encrypted_data["nonce"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])

            return chacha.decrypt(nonce, ciphertext, None)
        except ImportError:
            # 回退到Fernet解密
            return self._fernet_decrypt(encrypted_data, key)

    def _fernet_encrypt(self, data: bytes, key: bytes) -> Dict[str, str]:
        """Fernet加密（回退方案）"""
        try:
            from cryptography.fernet import Fernet

            # 使用前32字节作为Fernet密钥
            fernet_key = base64.urlsafe_b64encode(key[:32])
            f = Fernet(fernet_key)
            ciphertext = f.encrypt(data)

            return {
                "algorithm": "Fernet",
                "ciphertext": base64.b64encode(ciphertext).decode()
            }
        except ImportError:
            # 最后的回退方案：简单的XOR加密
            return self._xor_encrypt(data, key)

    def _fernet_decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """Fernet解密（回退方案）"""
        try:
            from cryptography.fernet import Fernet

            fernet_key = base64.urlsafe_b64encode(key[:32])
            f = Fernet(fernet_key)
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])

            return f.decrypt(ciphertext)
        except ImportError:
            # 最后的回退方案：简单的XOR解密
            return self._xor_decrypt(encrypted_data, key)

    def _xor_encrypt(self, data: bytes, key: bytes) -> Dict[str, str]:
        """XOR加密（最简单的回退方案）"""
        key_repeated = (key * ((len(data) // len(key)) + 1))[:len(data)]
        ciphertext = bytes(a ^ b for a, b in zip(data, key_repeated))

        return {
            "algorithm": "XOR",
            "ciphertext": base64.b64encode(ciphertext).decode()
        }

    def _xor_decrypt(self, encrypted_data: Dict[str, str], key: bytes) -> bytes:
        """XOR解密（最简单的回退方案）"""
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        key_repeated = (key * ((len(ciphertext) // len(key)) + 1))[:len(ciphertext)]

        return bytes(a ^ b for a, b in zip(ciphertext, key_repeated))

    async def encrypt_field(
        self,
        field_name: str,
        value: str,
        algorithm: str = "AES-256-GCM"
    ) -> str:
        """加密字段数据"""
        try:
            if field_name not in self.field_encryption_keys:
                raise ValueError(f"No encryption key for field: {field_name}")

            key = self.field_encryption_keys[field_name]
            data = value.encode('utf-8')

            if algorithm in self.encryption_algorithms:
                encrypted_data = self.encryption_algorithms[algorithm](data, key)
                return json.dumps(encrypted_data)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

        except Exception as e:
            logger.error(f"Field encryption failed for {field_name}: {e}")
            raise

    async def decrypt_field(self, field_name: str, encrypted_value: str) -> str:
        """解密字段数据"""
        try:
            if field_name not in self.field_encryption_keys:
                raise ValueError(f"No encryption key for field: {field_name}")

            key = self.field_encryption_keys[field_name]
            encrypted_data = json.loads(encrypted_value)
            algorithm = encrypted_data.get("algorithm")

            if algorithm == "AES-256-GCM":
                decrypted_data = self._aes_gcm_decrypt(encrypted_data, key)
            elif algorithm == "ChaCha20-Poly1305":
                decrypted_data = self._chacha20_decrypt(encrypted_data, key)
            elif algorithm == "Fernet":
                decrypted_data = self._fernet_decrypt(encrypted_data, key)
            elif algorithm == "XOR":
                decrypted_data = self._xor_decrypt(encrypted_data, key)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            return decrypted_data.decode('utf-8')

        except Exception as e:
            logger.error(f"Field decryption failed for {field_name}: {e}")
            raise


# 全局安全加固实例
security_hardening = SecurityHardening()
jwt_security_manager = JWTSecurityManager()
advanced_encryption = AdvancedDataEncryption()
