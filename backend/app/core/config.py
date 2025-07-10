"""
应用配置管理
使用Pydantic Settings进行配置验证和管理
"""
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    PROJECT_NAME: str = "量化投资后端平台"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # 安全配置
    ENCRYPTION_MASTER_KEY: str = os.getenv("ENCRYPTION_MASTER_KEY", "")
    ENABLE_IP_WHITELIST: bool = os.getenv("ENABLE_IP_WHITELIST", "False").lower() == "true"
    ALLOWED_HOSTS: List[str] = ["*"]  # 生产环境应该设置具体的主机名
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:5173",  # Vue开发服务器
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://quant_user:quant_password@localhost:5432/quant_db"
    )
    
    # 测试数据库
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://quant_user:quant_password@localhost:5432/quant_test_db"
    )
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 300  # 缓存过期时间（秒）
    
    # JWT配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30天
    ALGORITHM: str = "HS256"
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".xlsx", ".csv"]
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # CTP交易接口配置
    CTP_BROKER_ID: str = os.getenv("CTP_BROKER_ID", "")
    CTP_USER_ID: str = os.getenv("CTP_USER_ID", "")
    CTP_PASSWORD: str = os.getenv("CTP_PASSWORD", "")
    CTP_TRADE_FRONT: str = os.getenv("CTP_TRADE_FRONT", "")
    CTP_MD_FRONT: str = os.getenv("CTP_MD_FRONT", "")
    CTP_APP_ID: str = os.getenv("CTP_APP_ID", "")
    CTP_AUTH_CODE: str = os.getenv("CTP_AUTH_CODE", "")
    
    # 市场数据配置
    MARKET_DATA_PROVIDER: str = os.getenv("MARKET_DATA_PROVIDER", "mock")  # mock, tushare, wind
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")
    WIND_USERNAME: str = os.getenv("WIND_USERNAME", "")
    WIND_PASSWORD: str = os.getenv("WIND_PASSWORD", "")
    
    # 回测配置
    BACKTEST_DATA_DIR: str = os.getenv("BACKTEST_DATA_DIR", "data/backtest")
    BACKTEST_RESULT_DIR: str = os.getenv("BACKTEST_RESULT_DIR", "results/backtest")
    MAX_BACKTEST_DURATION_DAYS: int = 365 * 5  # 最大回测5年
    
    # Celery配置
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    
    # 监控配置
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "8001"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30  # 心跳间隔（秒）
    WS_MAX_CONNECTIONS: int = 1000   # 最大连接数
    
    # 风险控制配置
    MAX_POSITION_RATIO: float = 0.3      # 单一品种最大持仓比例
    MAX_DAILY_LOSS_RATIO: float = 0.05   # 单日最大亏损比例
    MAX_DRAWDOWN_RATIO: float = 0.15     # 最大回撤比例
    
    # 数据存储配置
    DATA_RETENTION_DAYS: int = 365 * 2   # 数据保留2年
    TICK_DATA_RETENTION_DAYS: int = 30   # Tick数据保留30天
    
    # 数据库配置
    SQLITE_DB_NAME: str = "quant_dev.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600  # 连接池回收时间
    DB_ECHO_LOG: bool = False
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # 强制使用SQLite进行开发和测试
        return f"sqlite+aiosqlite:///./{self.SQLITE_DB_NAME}"

        # if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_SERVER:
        #     # 使用 PostgreSQL (生产/Staging环境)
        #     return (
        #         f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
        #         f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        #     )
        
        # # 默认使用 SQLite (开发环境)
        # return f"sqlite+aiosqlite:///./{self.SQLITE_DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的字段


class DevelopmentSettings(Settings):
    """开发环境配置"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # 开发环境使用SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./quant_dev.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./quant_test.db"


class ProductionSettings(Settings):
    """生产环境配置"""
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 生产环境必须设置的配置
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    
    # 生产环境安全配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]


class TestSettings(Settings):
    """测试环境配置"""
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # 测试环境使用内存数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/15"  # 使用不同的Redis数据库


@lru_cache()
def get_settings() -> Settings:
    """根据环境变量获取对应的配置"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 全局配置实例
settings = get_settings()