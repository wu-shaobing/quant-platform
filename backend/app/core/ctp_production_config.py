"""
CTP生产环境配置管理
"""
import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field, validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CTPEnvironment(str, Enum):
    """CTP环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    SIMULATION = "simulation"  # 仿真环境


class CTPBrokerConfig(BaseSettings):
    """CTP券商配置"""
    
    # 基础配置
    broker_id: str = Field(..., description="经纪公司代码")
    broker_name: str = Field(..., description="经纪公司名称")
    
    # 交易前置地址
    trade_front_primary: str = Field(..., description="主交易前置地址")
    trade_front_backup: List[str] = Field(default_factory=list, description="备用交易前置地址")
    
    # 行情前置地址
    md_front_primary: str = Field(..., description="主行情前置地址")
    md_front_backup: List[str] = Field(default_factory=list, description="备用行情前置地址")
    
    # 认证配置
    auth_code: Optional[str] = Field(None, description="认证码")
    app_id: Optional[str] = Field(None, description="应用标识")
    user_product_info: str = Field("QuantPlatform", description="用户端产品信息")
    
    # 连接配置
    heartbeat_interval: int = Field(30, description="心跳间隔(秒)")
    timeout: int = Field(10, description="连接超时(秒)")
    max_retry_count: int = Field(3, description="最大重试次数")
    retry_interval: int = Field(5, description="重试间隔(秒)")
    
    # 交易配置
    max_order_ref: int = Field(999999999, description="最大报单引用")
    order_ref_prefix: str = Field("QP", description="报单引用前缀")
    max_subscribe_count: int = Field(500, description="最大订阅数量")
    
    class Config:
        env_prefix = "CTP_BROKER_"


class CTPProductionSettings(BaseSettings):
    """CTP生产环境设置"""
    
    # 环境配置
    environment: CTPEnvironment = Field(CTPEnvironment.PRODUCTION, description="环境类型")
    debug: bool = Field(False, description="调试模式")
    
    # 数据库配置
    database_url: str = Field(..., description="数据库连接URL")
    database_pool_size: int = Field(20, description="数据库连接池大小")
    database_max_overflow: int = Field(30, description="数据库连接池最大溢出")
    
    # Redis配置
    redis_url: str = Field(..., description="Redis连接URL")
    redis_db: int = Field(0, description="Redis数据库编号")
    redis_password: Optional[str] = Field(None, description="Redis密码")
    redis_pool_size: int = Field(10, description="Redis连接池大小")
    
    # 日志配置
    log_level: str = Field("INFO", description="日志级别")
    log_file: str = Field("/var/log/quant-platform/ctp.log", description="日志文件路径")
    log_max_size: str = Field("100MB", description="日志文件最大大小")
    log_backup_count: int = Field(10, description="日志备份数量")
    
    # 监控配置
    metrics_enabled: bool = Field(True, description="启用指标收集")
    metrics_port: int = Field(9090, description="指标服务端口")
    health_check_interval: int = Field(30, description="健康检查间隔(秒)")
    
    # 安全配置
    encryption_key: str = Field(..., description="数据加密密钥")
    jwt_secret_key: str = Field(..., description="JWT密钥")
    api_rate_limit: int = Field(1000, description="API速率限制(每分钟)")
    max_concurrent_connections: int = Field(100, description="最大并发连接数")
    
    # 告警配置
    alert_enabled: bool = Field(True, description="启用告警")
    alert_webhook_url: Optional[str] = Field(None, description="告警Webhook URL")
    alert_email_smtp_host: Optional[str] = Field(None, description="邮件SMTP主机")
    alert_email_smtp_port: int = Field(587, description="邮件SMTP端口")
    alert_email_username: Optional[str] = Field(None, description="邮件用户名")
    alert_email_password: Optional[str] = Field(None, description="邮件密码")
    alert_email_recipients: List[str] = Field(default_factory=list, description="告警邮件接收者")
    
    # 性能配置
    cache_ttl: int = Field(300, description="缓存TTL(秒)")
    batch_size: int = Field(1000, description="批处理大小")
    worker_threads: int = Field(4, description="工作线程数")
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in CTPEnvironment:
            raise ValueError(f"Invalid environment: {v}")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    class Config:
        env_prefix = "CTP_"
        env_file = ".env"


class CTPBrokerRegistry:
    """CTP券商注册表"""
    
    # 主要期货公司配置
    BROKERS = {
        # 中信期货
        "CITIC": CTPBrokerConfig(
            broker_id="66666",
            broker_name="中信期货",
            trade_front_primary="tcp://180.168.146.187:10130",
            trade_front_backup=[
                "tcp://180.168.146.187:10131",
                "tcp://218.202.237.33:10130"
            ],
            md_front_primary="tcp://180.168.146.187:10131",
            md_front_backup=[
                "tcp://180.168.146.187:10132",
                "tcp://218.202.237.33:10131"
            ]
        ),
        
        # 华泰期货
        "HTFC": CTPBrokerConfig(
            broker_id="1080",
            broker_name="华泰期货",
            trade_front_primary="tcp://180.169.112.52:41205",
            trade_front_backup=[
                "tcp://180.169.112.52:41206"
            ],
            md_front_primary="tcp://180.169.112.52:41213",
            md_front_backup=[
                "tcp://180.169.112.52:41214"
            ]
        ),
        
        # 国泰君安期货
        "GTJA": CTPBrokerConfig(
            broker_id="2011",
            broker_name="国泰君安期货",
            trade_front_primary="tcp://180.169.75.18:41205",
            trade_front_backup=[
                "tcp://180.169.75.19:41205"
            ],
            md_front_primary="tcp://180.169.75.18:41213",
            md_front_backup=[
                "tcp://180.169.75.19:41213"
            ]
        ),
        
        # 申银万国期货
        "SYWG": CTPBrokerConfig(
            broker_id="9999",
            broker_name="申银万国期货",
            trade_front_primary="tcp://180.168.146.187:10130",
            trade_front_backup=[
                "tcp://180.168.146.187:10131"
            ],
            md_front_primary="tcp://180.168.146.187:10131",
            md_front_backup=[
                "tcp://180.168.146.187:10132"
            ]
        ),
        
        # 仿真环境
        "SIMNOW": CTPBrokerConfig(
            broker_id="9999",
            broker_name="SimNow仿真",
            trade_front_primary="tcp://180.168.146.187:10130",
            trade_front_backup=[
                "tcp://180.168.146.187:10131"
            ],
            md_front_primary="tcp://180.168.146.187:10131",
            md_front_backup=[
                "tcp://180.168.146.187:10132"
            ]
        )
    }
    
    @classmethod
    def get_broker_config(cls, broker_code: str) -> Optional[CTPBrokerConfig]:
        """获取券商配置"""
        return cls.BROKERS.get(broker_code.upper())
    
    @classmethod
    def list_brokers(cls) -> List[str]:
        """列出所有券商代码"""
        return list(cls.BROKERS.keys())
    
    @classmethod
    def add_broker(cls, broker_code: str, config: CTPBrokerConfig):
        """添加券商配置"""
        cls.BROKERS[broker_code.upper()] = config
        logger.info(f"Added broker config: {broker_code}")


class CTPConfigManager:
    """CTP配置管理器"""
    
    def __init__(self):
        self.settings = CTPProductionSettings()
        self.broker_registry = CTPBrokerRegistry()
    
    def get_broker_config(self, broker_code: str) -> CTPBrokerConfig:
        """获取券商配置"""
        config = self.broker_registry.get_broker_config(broker_code)
        if not config:
            raise ValueError(f"Unknown broker: {broker_code}")
        return config
    
    def get_environment_config(self) -> Dict:
        """获取环境配置"""
        return {
            "environment": self.settings.environment,
            "debug": self.settings.debug,
            "database_url": self.settings.database_url,
            "redis_url": self.settings.redis_url,
            "log_level": self.settings.log_level,
            "metrics_enabled": self.settings.metrics_enabled,
            "alert_enabled": self.settings.alert_enabled
        }
    
    def validate_production_config(self) -> bool:
        """验证生产环境配置"""
        try:
            # 检查必要的环境变量
            required_vars = [
                "CTP_DATABASE_URL",
                "CTP_REDIS_URL", 
                "CTP_ENCRYPTION_KEY",
                "CTP_JWT_SECRET_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            # 验证配置格式
            self.settings = CTPProductionSettings()
            
            # 检查生产环境特定配置
            if self.settings.environment == CTPEnvironment.PRODUCTION:
                if self.settings.debug:
                    logger.warning("Debug mode is enabled in production")
                
                if not self.settings.alert_enabled:
                    logger.warning("Alerts are disabled in production")
                
                if not self.settings.metrics_enabled:
                    logger.warning("Metrics are disabled in production")
            
            logger.info("Production configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_connection_string(self, broker_code: str, connection_type: str = "trade") -> str:
        """获取连接字符串"""
        broker_config = self.get_broker_config(broker_code)
        
        if connection_type == "trade":
            return broker_config.trade_front_primary
        elif connection_type == "md":
            return broker_config.md_front_primary
        else:
            raise ValueError(f"Invalid connection type: {connection_type}")
    
    def get_backup_connections(self, broker_code: str, connection_type: str = "trade") -> List[str]:
        """获取备用连接列表"""
        broker_config = self.get_broker_config(broker_code)
        
        if connection_type == "trade":
            return broker_config.trade_front_backup
        elif connection_type == "md":
            return broker_config.md_front_backup
        else:
            raise ValueError(f"Invalid connection type: {connection_type}")


# 全局配置管理器实例
config_manager = CTPConfigManager()
