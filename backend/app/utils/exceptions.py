"""
自定义异常类
提供业务逻辑相关的异常处理
"""
from typing import Any, Dict, Optional


class QuantPlatformException(Exception):
    """项目基础异常类"""
    
    def __init__(self, message: str, code: int = 500, error_type: str = "internal_error"):
        self.message = message
        self.code = code
        self.error_type = error_type
        super().__init__(self.message)


class AuthenticationError(QuantPlatformException):
    """认证失败异常"""
    
    def __init__(self, message: str = "认证失败", error_type: str = "authentication_error"):
        super().__init__(message, code=401, error_type=error_type)


class PermissionDeniedError(QuantPlatformException):
    """权限不足异常"""
    
    def __init__(self, message: str = "权限不足", error_type: str = "permission_denied"):
        super().__init__(message, code=403, error_type=error_type)


class ValidationError(QuantPlatformException):
    """数据验证失败异常"""
    
    def __init__(self, message: str = "输入数据验证失败", error_type: str = "validation_error"):
        super().__init__(message, code=422, error_type=error_type)


class DataNotFoundError(QuantPlatformException):
    """数据未找到异常"""
    
    def __init__(self, message: str = "请求的数据不存在", error_type: str = "not_found"):
        super().__init__(message, code=404, error_type=error_type)


class ConflictError(QuantPlatformException):
    """资源冲突错误"""
    
    def __init__(self, message: str = "资源冲突", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=409,
            error_type="conflict_error"
        )


class RateLimitError(QuantPlatformException):
    """频率限制错误"""
    
    def __init__(self, message: str = "请求频率过高", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=429,
            error_type="rate_limit_error"
        )


class TradingError(QuantPlatformException):
    """交易相关错误"""
    
    def __init__(self, message: str = "交易操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=400,
            error_type="trading_error"
        )


class RiskControlError(QuantPlatformException):
    """风控错误"""
    
    def __init__(self, message: str = "风控检查失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=400,
            error_type="risk_control_error"
        )


class MarketDataError(QuantPlatformException):
    """行情数据错误"""
    
    def __init__(self, message: str = "行情数据获取失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=500,
            error_type="market_data_error"
        )


class StrategyError(QuantPlatformException):
    """策略相关错误"""
    
    def __init__(self, message: str = "策略操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=400,
            error_type="strategy_error"
        )


class BacktestError(QuantPlatformException):
    """回测相关错误"""
    
    def __init__(self, message: str = "回测操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=400,
            error_type="backtest_error"
        )


class DatabaseError(QuantPlatformException):
    """数据库错误"""
    
    def __init__(self, message: str = "数据库操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=500,
            error_type="database_error"
        )


class ExternalServiceError(QuantPlatformException):
    """外部服务错误"""
    
    def __init__(self, message: str = "外部服务调用失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=502,
            error_type="external_service_error"
        )


class ConfigurationError(QuantPlatformException):
    """配置错误"""
    
    def __init__(self, message: str = "配置错误", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=500,
            error_type="configuration_error"
        )