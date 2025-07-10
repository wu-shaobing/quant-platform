"""
CTP安全加固配置
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EncryptionAlgorithm(Enum):
    """加密算法"""
    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    FERNET = "Fernet"
    XOR = "XOR"


@dataclass
class JWTSecurityConfig:
    """JWT安全配置"""
    access_token_lifetime: int = 3600  # 1小时
    refresh_token_lifetime: int = 7 * 24 * 3600  # 7天
    enable_device_fingerprint: bool = True
    enable_token_blacklist: bool = True
    max_refresh_tokens_per_user: int = 5
    token_rotation_enabled: bool = True
    
    # JWT算法配置
    algorithm: str = "HS256"
    issuer: str = "quant-platform"
    audience: str = "trading-api"
    
    # 安全增强
    require_secure_transport: bool = True
    enable_jti: bool = True  # JWT ID
    enable_nbf: bool = True  # Not Before
    clock_skew_tolerance: int = 30  # 时钟偏差容忍度（秒）


@dataclass
class EncryptionConfig:
    """数据加密配置"""
    default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_derivation_iterations: int = 100000
    salt_length: int = 32
    nonce_length: int = 12
    
    # 字段级加密配置
    encrypted_fields: List[str] = field(default_factory=lambda: [
        "password", "api_key", "private_key", "bank_account",
        "id_number", "phone", "email", "trading_account",
        "secret_key", "access_token", "refresh_token"
    ])
    
    # 加密强度配置
    enable_field_level_encryption: bool = True
    enable_database_encryption: bool = True
    enable_transmission_encryption: bool = True
    
    # 密钥管理
    key_rotation_interval: int = 30 * 24 * 3600  # 30天
    backup_key_count: int = 3


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    # 全局限制
    global_requests_per_minute: int = 1000
    global_requests_per_hour: int = 10000
    
    # 端点特定限制
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "login": {"per_minute": 5, "per_hour": 20},
        "trading": {"per_minute": 100, "per_hour": 1000},
        "query": {"per_minute": 200, "per_hour": 2000},
        "market_data": {"per_minute": 500, "per_hour": 5000},
        "order_submit": {"per_minute": 50, "per_hour": 500},
        "order_cancel": {"per_minute": 100, "per_hour": 1000}
    })
    
    # 用户级别限制
    user_level_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "basic": {"per_minute": 50, "per_hour": 500},
        "premium": {"per_minute": 200, "per_hour": 2000},
        "vip": {"per_minute": 500, "per_hour": 5000},
        "admin": {"per_minute": 1000, "per_hour": 10000}
    })
    
    # 限制策略
    enable_sliding_window: bool = True
    enable_burst_protection: bool = True
    burst_multiplier: float = 1.5


@dataclass
class AccessControlConfig:
    """访问控制配置"""
    # IP访问控制
    enable_ip_whitelist: bool = False
    enable_ip_blacklist: bool = True
    default_whitelist: List[str] = field(default_factory=lambda: [
        "127.0.0.1", "::1", "localhost"
    ])
    
    # 地理位置限制
    enable_geo_blocking: bool = False
    allowed_countries: List[str] = field(default_factory=lambda: ["CN", "US", "HK"])
    blocked_countries: List[str] = field(default_factory=list)
    
    # 用户访问控制
    max_concurrent_sessions: int = 3
    session_timeout: int = 8 * 3600  # 8小时
    enable_session_binding: bool = True
    
    # API访问控制
    require_api_key: bool = True
    api_key_rotation_interval: int = 90 * 24 * 3600  # 90天
    enable_api_versioning: bool = True


@dataclass
class AuditConfig:
    """审计配置"""
    # 审计日志
    enable_audit_logging: bool = True
    log_all_requests: bool = False
    log_sensitive_operations: bool = True
    log_failed_attempts: bool = True
    
    # 审计事件类型
    tracked_events: List[str] = field(default_factory=lambda: [
        "LOGIN", "LOGOUT", "ORDER_SUBMIT", "ORDER_CANCEL",
        "DATA_EXPORT", "CONFIG_CHANGE", "SECURITY_VIOLATION"
    ])
    
    # 日志保留
    log_retention_days: int = 365
    enable_log_encryption: bool = True
    enable_log_integrity_check: bool = True
    
    # 实时监控
    enable_real_time_alerts: bool = True
    alert_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "failed_login_attempts": 5,
        "suspicious_ip_requests": 100,
        "high_frequency_trading": 1000,
        "data_export_volume": 10000
    })


@dataclass
class ThreatDetectionConfig:
    """威胁检测配置"""
    # 异常检测
    enable_anomaly_detection: bool = True
    baseline_learning_period: int = 7 * 24 * 3600  # 7天
    anomaly_threshold: float = 0.8
    
    # 攻击检测
    enable_sql_injection_detection: bool = True
    enable_xss_detection: bool = True
    enable_csrf_protection: bool = True
    enable_ddos_protection: bool = True
    
    # 行为分析
    enable_user_behavior_analysis: bool = True
    suspicious_patterns: List[str] = field(default_factory=lambda: [
        "rapid_login_attempts",
        "unusual_trading_patterns",
        "large_data_exports",
        "off_hours_access",
        "multiple_ip_usage"
    ])
    
    # 响应策略
    auto_block_suspicious_ips: bool = True
    auto_lock_suspicious_accounts: bool = False
    alert_security_team: bool = True
    quarantine_suspicious_requests: bool = True


@dataclass
class SecurityHardeningConfig:
    """安全加固总配置"""
    # 子配置
    jwt_config: JWTSecurityConfig = field(default_factory=JWTSecurityConfig)
    encryption_config: EncryptionConfig = field(default_factory=EncryptionConfig)
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    access_control_config: AccessControlConfig = field(default_factory=AccessControlConfig)
    audit_config: AuditConfig = field(default_factory=AuditConfig)
    threat_detection_config: ThreatDetectionConfig = field(default_factory=ThreatDetectionConfig)
    
    # 全局安全设置
    security_level: SecurityLevel = SecurityLevel.HIGH
    enable_security_headers: bool = True
    enable_cors_protection: bool = True
    enable_content_security_policy: bool = True
    
    # 合规性设置
    enable_gdpr_compliance: bool = True
    enable_data_anonymization: bool = True
    enable_right_to_be_forgotten: bool = True
    
    # 性能与安全平衡
    security_performance_mode: str = "balanced"  # strict, balanced, performance
    cache_security_decisions: bool = True
    security_cache_ttl: int = 300  # 5分钟
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "jwt_config": self.jwt_config.__dict__,
            "encryption_config": {
                **self.encryption_config.__dict__,
                "default_algorithm": self.encryption_config.default_algorithm.value
            },
            "rate_limit_config": self.rate_limit_config.__dict__,
            "access_control_config": self.access_control_config.__dict__,
            "audit_config": self.audit_config.__dict__,
            "threat_detection_config": self.threat_detection_config.__dict__,
            "security_level": self.security_level.value,
            "enable_security_headers": self.enable_security_headers,
            "enable_cors_protection": self.enable_cors_protection,
            "enable_content_security_policy": self.enable_content_security_policy,
            "enable_gdpr_compliance": self.enable_gdpr_compliance,
            "enable_data_anonymization": self.enable_data_anonymization,
            "enable_right_to_be_forgotten": self.enable_right_to_be_forgotten,
            "security_performance_mode": self.security_performance_mode,
            "cache_security_decisions": self.cache_security_decisions,
            "security_cache_ttl": self.security_cache_ttl
        }
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityHardeningConfig':
        """从字典创建配置"""
        config = cls()
        
        # 更新JWT配置
        if "jwt_config" in data:
            for key, value in data["jwt_config"].items():
                if hasattr(config.jwt_config, key):
                    setattr(config.jwt_config, key, value)
        
        # 更新加密配置
        if "encryption_config" in data:
            enc_data = data["encryption_config"]
            for key, value in enc_data.items():
                if key == "default_algorithm":
                    config.encryption_config.default_algorithm = EncryptionAlgorithm(value)
                elif hasattr(config.encryption_config, key):
                    setattr(config.encryption_config, key, value)
        
        # 更新其他配置...
        for config_name in ["rate_limit_config", "access_control_config", 
                           "audit_config", "threat_detection_config"]:
            if config_name in data:
                config_obj = getattr(config, config_name)
                for key, value in data[config_name].items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
        
        # 更新全局设置
        if "security_level" in data:
            config.security_level = SecurityLevel(data["security_level"])
        
        for key in ["enable_security_headers", "enable_cors_protection", 
                   "enable_content_security_policy", "enable_gdpr_compliance",
                   "enable_data_anonymization", "enable_right_to_be_forgotten",
                   "security_performance_mode", "cache_security_decisions",
                   "security_cache_ttl"]:
            if key in data:
                setattr(config, key, data[key])
        
        return config


# 默认安全配置实例
default_security_config = SecurityHardeningConfig()

# 生产环境安全配置
production_security_config = SecurityHardeningConfig(
    security_level=SecurityLevel.CRITICAL,
    jwt_config=JWTSecurityConfig(
        access_token_lifetime=1800,  # 30分钟
        refresh_token_lifetime=24 * 3600,  # 1天
        require_secure_transport=True
    ),
    encryption_config=EncryptionConfig(
        default_algorithm=EncryptionAlgorithm.AES_256_GCM,
        key_derivation_iterations=200000,
        enable_field_level_encryption=True,
        enable_database_encryption=True
    ),
    rate_limit_config=RateLimitConfig(
        global_requests_per_minute=500,
        global_requests_per_hour=5000
    ),
    access_control_config=AccessControlConfig(
        enable_ip_whitelist=True,
        enable_geo_blocking=True,
        max_concurrent_sessions=2
    ),
    threat_detection_config=ThreatDetectionConfig(
        enable_anomaly_detection=True,
        auto_block_suspicious_ips=True,
        alert_security_team=True
    )
)

# 开发环境安全配置
development_security_config = SecurityHardeningConfig(
    security_level=SecurityLevel.MEDIUM,
    jwt_config=JWTSecurityConfig(
        access_token_lifetime=7200,  # 2小时
        refresh_token_lifetime=7 * 24 * 3600,  # 7天
        require_secure_transport=False
    ),
    rate_limit_config=RateLimitConfig(
        global_requests_per_minute=2000,
        global_requests_per_hour=20000
    ),
    access_control_config=AccessControlConfig(
        enable_ip_whitelist=False,
        enable_geo_blocking=False,
        max_concurrent_sessions=5
    ),
    threat_detection_config=ThreatDetectionConfig(
        enable_anomaly_detection=False,
        auto_block_suspicious_ips=False,
        alert_security_team=False
    )
)
