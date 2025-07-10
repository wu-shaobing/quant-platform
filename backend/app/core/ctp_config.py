"""
CTP交易接口配置
"""
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import settings

# 导入生产环境配置
try:
    from .ctp_production_config import (
        CTPProductionSettings,
        CTPBrokerRegistry,
        CTPConfigManager,
        config_manager
    )
    PRODUCTION_CONFIG_AVAILABLE = True
except ImportError:
    PRODUCTION_CONFIG_AVAILABLE = False


class CTPConfig(BaseModel):
    """CTP配置类"""
    
    # 基础连接配置
    broker_id: str = Field(default=settings.CTP_BROKER_ID, description="经纪商代码")
    user_id: str = Field(default=settings.CTP_USER_ID, description="用户代码")
    password: str = Field(default=settings.CTP_PASSWORD, description="密码")
    app_id: str = Field(default=settings.CTP_APP_ID, description="应用标识")
    auth_code: str = Field(default=settings.CTP_AUTH_CODE, description="授权编码")
    
    # 服务器地址
    trade_front: str = Field(default=settings.CTP_TRADE_FRONT, description="交易前置地址")
    md_front: str = Field(default=settings.CTP_MD_FRONT, description="行情前置地址")
    
    # 连接配置
    timeout: int = Field(default=30, description="连接超时时间(秒)")
    heartbeat_interval: int = Field(default=60, description="心跳间隔(秒)")
    max_retry_count: int = Field(default=3, description="最大重试次数")
    retry_interval: int = Field(default=5, description="重试间隔(秒)")
    
    # 交易配置
    max_order_ref: int = Field(default=999999, description="最大报单引用")
    order_ref_prefix: str = Field(default="QP", description="报单引用前缀")
    
    # 行情配置
    subscribe_symbols: list[str] = Field(default_factory=list, description="默认订阅合约")
    max_subscribe_count: int = Field(default=500, description="最大订阅数量")
    
    # 风控配置
    enable_risk_check: bool = Field(default=True, description="启用风控检查")
    max_order_volume: int = Field(default=100, description="单笔最大下单量")
    max_daily_volume: int = Field(default=1000, description="日最大交易量")
    
    class Config:
        env_prefix = "CTP_"


class CTPStatus(BaseModel):
    """CTP连接状态"""
    
    # 连接状态
    trade_connected: bool = Field(default=False, description="交易连接状态")
    md_connected: bool = Field(default=False, description="行情连接状态")
    trade_logged_in: bool = Field(default=False, description="交易登录状态")
    md_logged_in: bool = Field(default=False, description="行情登录状态")
    
    # 连接时间
    trade_connect_time: Optional[str] = Field(default=None, description="交易连接时间")
    md_connect_time: Optional[str] = Field(default=None, description="行情连接时间")
    trade_login_time: Optional[str] = Field(default=None, description="交易登录时间")
    md_login_time: Optional[str] = Field(default=None, description="行情登录时间")
    
    # 错误信息
    last_error: Optional[str] = Field(default=None, description="最后错误信息")
    error_count: int = Field(default=0, description="错误计数")
    
    # 统计信息
    order_count: int = Field(default=0, description="报单数量")
    trade_count: int = Field(default=0, description="成交数量")
    subscribe_count: int = Field(default=0, description="订阅数量")
    
    @property
    def is_ready(self) -> bool:
        """是否就绪（交易和行情都已连接登录）"""
        return (self.trade_connected and self.trade_logged_in and 
                self.md_connected and self.md_logged_in)
    
    @property
    def trade_ready(self) -> bool:
        """交易是否就绪"""
        return self.trade_connected and self.trade_logged_in
    
    @property
    def md_ready(self) -> bool:
        """行情是否就绪"""
        return self.md_connected and self.md_logged_in


class CTPError(Exception):
    """CTP异常类"""
    
    def __init__(self, error_id: int, error_msg: str, request_id: int = 0):
        self.error_id = error_id
        self.error_msg = error_msg
        self.request_id = request_id
        super().__init__(f"CTP Error {error_id}: {error_msg}")


class CTPOrderRef:
    """CTP报单引用管理器"""
    
    def __init__(self, prefix: str = "QP", max_ref: int = 999999):
        self.prefix = prefix
        self.max_ref = max_ref
        self.current_ref = 1
        self._lock = None  # 在异步环境中使用asyncio.Lock
    
    def get_next_ref(self) -> str:
        """获取下一个报单引用"""
        ref = f"{self.prefix}{self.current_ref:06d}"
        self.current_ref += 1
        if self.current_ref > self.max_ref:
            self.current_ref = 1
        return ref
    
    def reset(self):
        """重置报单引用"""
        self.current_ref = 1


# 全局CTP配置实例
ctp_config = CTPConfig()


def get_production_config() -> Optional[Dict[str, Any]]:
    """获取生产环境配置"""
    if not PRODUCTION_CONFIG_AVAILABLE:
        return None

    try:
        # 获取当前环境
        environment = os.getenv('CTP_ENVIRONMENT', 'development')

        if environment == 'production':
            # 验证生产环境配置
            if not config_manager.validate_production_config():
                raise ValueError("Production configuration validation failed")

            # 获取券商配置
            broker_code = os.getenv('CTP_BROKER_CODE', 'SIMNOW')
            broker_config = config_manager.get_broker_config(broker_code)

            # 获取环境配置
            env_config = config_manager.get_environment_config()

            return {
                'broker_config': broker_config.dict(),
                'environment_config': env_config,
                'broker_code': broker_code
            }
    except Exception as e:
        import logging
        logging.error(f"Failed to get production config: {e}")
        return None

    return None


def get_ctp_config_for_environment() -> CTPConfig:
    """根据环境获取CTP配置"""
    prod_config = get_production_config()

    if prod_config:
        # 使用生产环境配置
        broker_config = prod_config['broker_config']

        return CTPConfig(
            broker_id=broker_config['broker_id'],
            user_id=os.getenv('CTP_USER_ID', ''),
            password=os.getenv('CTP_PASSWORD', ''),
            app_id=broker_config.get('app_id', ''),
            auth_code=broker_config.get('auth_code', ''),
            trade_front=broker_config['trade_front_primary'],
            md_front=broker_config['md_front_primary'],
            timeout=broker_config.get('timeout', 30),
            heartbeat_interval=broker_config.get('heartbeat_interval', 60),
            max_retry_count=broker_config.get('max_retry_count', 3),
            retry_interval=broker_config.get('retry_interval', 5),
            max_order_ref=broker_config.get('max_order_ref', 999999),
            order_ref_prefix=broker_config.get('order_ref_prefix', 'QP'),
            max_subscribe_count=broker_config.get('max_subscribe_count', 500)
        )
    else:
        # 使用默认配置
        return ctp_config

# CTP错误码映射
CTP_ERROR_CODES = {
    0: "正确",
    -1: "网络连接失败",
    -2: "未处理请求超过许可数",
    -3: "每秒发送请求数超过许可数",
    1: "用户名不存在",
    2: "用户密码错误",
    3: "经纪商代码错误",
    4: "用户类型错误",
    5: "用户未登录",
    6: "用户登录失败",
    7: "用户已登录",
    8: "用户未确认",
    9: "用户状态不对",
    10: "用户权限不够",
    11: "上次登录信息不对",
    12: "登录信息不一致",
    13: "前置不活跃",
    14: "前置未连接",
    15: "报单字段有误",
    16: "报单价格有误",
    17: "报单数量有误",
    18: "报单价格类型有误",
    19: "报单价格条件有误",
    20: "报单时间条件有误",
    21: "报单成交量类型有误",
    22: "报单触发条件有误",
    23: "报单强平原因有误",
    24: "报单自动挂起标志有误",
    25: "报单用户强平标志有误",
    26: "合约代码错误",
    27: "合约乘数错误",
    28: "交易所代码错误",
    29: "报单引用不能为空",
    30: "报单引用重复",
}


def get_error_message(error_id: int) -> str:
    """获取错误信息"""
    return CTP_ERROR_CODES.get(error_id, f"未知错误: {error_id}")
