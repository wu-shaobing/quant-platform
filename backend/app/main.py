"""
量化投资后端主应用
基于FastAPI的高性能异步API服务
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import uvicorn

from app.core.config import get_settings
from app.core.database import DatabaseManager, init_db, cleanup_db
from app.core.monitoring import MetricsCollector, HealthChecker, PerformanceMiddleware
from app.core.websocket import ConnectionManager
from app.api import api_router
from app.utils.exceptions import QuantPlatformException
from app.monitoring.startup import setup_monitoring_startup, health_check, readiness_check, liveness_check
from app.monitoring.middleware import setup_monitoring_middleware
from app.middleware.security_middleware import SecurityMiddleware, LoginSecurityMiddleware, CORSSecurityMiddleware

# 获取配置
settings = get_settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化全局组件
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
websocket_manager = ConnectionManager()


async def check_database_health() -> bool:
    """数据库健康检查"""
    try:
        db_manager = DatabaseManager()
        return await db_manager.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_websocket_health() -> bool:
    """WebSocket健康检查"""
    try:
        return websocket_manager.is_healthy()
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: development")
    
    # 初始化监控系统
    await metrics_collector.initialize()
    logger.info("Metrics collector initialized")
    
    # 注册健康检查
    health_checker.register_check("database", check_database_health)
    health_checker.register_check("websocket", check_websocket_health)
    logger.info("Health checks registered")
    
    # 初始化数据库
    await init_db()
    logger.info("Database initialized successfully")
    
    # 调试：打印所有路由路径，帮助确认实际注册路径
    routes = [route.path for route in app.routes]
    logger.info(f"Registered routes: {routes}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down application")
    
    # 关闭WebSocket连接
    await websocket_manager.shutdown()
    logger.info("WebSocket manager shutdown")
    
    # 关闭监控系统
    await metrics_collector.cleanup()
    logger.info("Metrics collector cleaned up")
    
    # 关闭数据库连接
    await cleanup_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
        ## 专业的量化投资后端服务
        
        提供以下核心功能：
        - 🔐 **用户认证**: JWT令牌认证、权限管理、API密钥
        - 📊 **实时行情**: 多市场行情数据、WebSocket推送
        - 💹 **交易执行**: 订单管理、持仓查询、风险控制
        - 🎯 **策略管理**: 策略开发、回测分析、实时监控
        - 📈 **数据分析**: 技术指标、绩效分析、风险评估
        
        ### 技术特点
        - ⚡ 异步高性能架构
        - 🔒 金融级安全保障
        - 📱 RESTful API设计
        - 🔄 实时WebSocket通信
        - 📊 完整的API文档
        """,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url=None,  # 自定义文档路径
        redoc_url=None,  # 自定义ReDoc路径
        openapi_url="/api/v1/openapi.json",
        contact={
            "name": "量化投资平台",
            "email": "support@quantplatform.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )
    
    # 安全中间件配置（按顺序添加）

    # 1. 安全CORS中间件（替代原有CORS）
    app.add_middleware(
        CORSSecurityMiddleware,
        allowed_origins=[str(origin).rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS]
    )

    # 2. 主安全中间件（速率限制、IP白名单等）
    app.add_middleware(
        SecurityMiddleware,
        enable_rate_limiting=True,
        enable_ip_whitelist=getattr(settings, 'ENABLE_IP_WHITELIST', False)
    )

    # 3. 登录安全中间件
    app.add_middleware(LoginSecurityMiddleware)

    # 4. 受信任主机中间件（生产环境）
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=getattr(settings, 'ALLOWED_HOSTS', ["*"])
        )

    # 5. 性能监控中间件
    app.add_middleware(PerformanceMiddleware, metrics_collector=metrics_collector)

    # 6. 监控指标中间件
    setup_monitoring_middleware(app)
    
    # 注册API路由
    app.include_router(api_router)
    
    # 注册WebSocket路由
    from app.core.websocket import simple_websocket_endpoint
    app.add_websocket_route("/ws", simple_websocket_endpoint)
    
    # 全局异常处理
    @app.exception_handler(QuantPlatformException)
    async def quant_platform_exception_handler(request: Request, exc: QuantPlatformException):
        """处理自定义业务异常"""
        logger.warning(f"Business exception: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        logger.warning(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "内部服务器错误" if not settings.DEBUG else str(exc),
                "type": "unexpected_error"
            }
        )
    
    # 自定义OpenAPI文档
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # 添加安全定义
        openapi_schema["components"]["securitySchemes"] = {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT令牌认证"
            },
            "ApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API密钥认证"
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # 自定义文档页面
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        if not settings.DEBUG:
            raise HTTPException(status_code=404, detail="Not found")
        
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        if not settings.DEBUG:
            raise HTTPException(status_code=404, detail="Not found")
        
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        )
    
    # 基础路由
    @app.get("/", tags=["系统"])
    async def root():
        """根路径 - 系统信息"""
        return {
            "message": f"欢迎使用{settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "environment": "development",
            "status": "running",
            "docs_url": "/docs" if settings.DEBUG else "文档在生产环境中已禁用",
            "api_prefix": "/api/v1",
            "features": [
                "用户认证与权限管理",
                "实时行情数据服务",
                "交易执行与风控",
                "策略开发与回测",
                "数据分析与可视化"
            ]
        }
    
    @app.get("/health", tags=["系统"])
    async def health_check_endpoint():
        """系统健康检查"""
        return await health_check()

    @app.get("/ready", tags=["系统"])
    async def readiness_check_endpoint():
        """就绪检查"""
        return await readiness_check()

    @app.get("/live", tags=["系统"])
    async def liveness_check_endpoint():
        """存活检查"""
        return await liveness_check()

    @app.get("/health/legacy", tags=["系统"])
    async def legacy_health_check():
        """原有健康检查（保持兼容性）"""
        from datetime import datetime

        # 检查所有注册的健康检查项
        health_results = await health_checker.check_health()

        # 判断整体健康状态
        is_healthy = all(status.status == "healthy" for status in health_results.values())

        # 设置响应状态码
        status_code = 200 if is_healthy else 503

        # 构建响应数据
        checks_data = {name: status.model_dump() for name, status in health_results.items()}

        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "environment": "development",
            "checks": checks_data,
        }
        
        return JSONResponse(status_code=status_code, content=response_data)
    
    @app.get("/metrics", tags=["监控"])
    async def get_metrics():
        """Prometheus格式的指标端点"""
        metrics_data = await metrics_collector.get_prometheus_metrics()
        
        return JSONResponse(
            content=metrics_data,
            media_type="text/plain"
        )

    @app.get("/info", tags=["系统"])
    async def app_info():
        """应用详细信息"""
        return {
            "application": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": "development",
                "debug": settings.DEBUG,
                "timezone": "Asia/Shanghai"
            },
            "api": {
                "version": "v1",
                "base_url": "/api/v1",
                "documentation": "/docs" if settings.DEBUG else None,
                "openapi_spec": "/api/v1/openapi.json"
            },
            "features": {
                "authentication": True,
                "market_data": True,
                "trading": True,
                "strategy": True,
                "backtest": True,
                "risk_management": True,
                "websocket": True
            },
            "database": {
                "type": "PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite",
                "async_support": True
            }
        }
    
    # 设置监控系统启动事件
    setup_monitoring_startup(app)

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        workers=1 if settings.DEBUG else 4
    )