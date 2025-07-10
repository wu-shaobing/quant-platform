"""
API v1 路由模块
集成所有API路由
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .market import router as market_router
from .trading import router as trading_router
from .strategy import router as strategy_router
from .backtest import router as backtest_router
from .risk import router as risk_router
from .ctp import router as ctp_router
from .ctp_websocket import router as ctp_websocket_router
from .monitoring import router as monitoring_router
from .performance import router as performance_router
from .security import router as security_router
from .security_dashboard import router as security_dashboard_router
from app.api.captcha import router as captcha_router

# 创建API v1路由器
api_router = APIRouter(prefix="/v1")

# 注册所有路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(market_router, prefix="/market", tags=["行情"])
api_router.include_router(trading_router, prefix="/trading", tags=["交易"])
api_router.include_router(strategy_router, prefix="/strategy", tags=["策略"])
api_router.include_router(backtest_router, prefix="/backtest", tags=["回测"])
api_router.include_router(risk_router, prefix="/risk", tags=["风控"])
api_router.include_router(ctp_router, tags=["CTP交易接口"])
api_router.include_router(ctp_websocket_router, tags=["CTP WebSocket"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["监控告警"])
api_router.include_router(performance_router, tags=["性能优化"])
api_router.include_router(security_router, tags=["安全管理"])
api_router.include_router(security_dashboard_router, tags=["安全监控仪表板"])
api_router.include_router(captcha_router, prefix="/captcha", tags=["验证码"])

__all__ = ["api_router"]