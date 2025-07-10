"""
监控系统启动脚本
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .ctp_metrics import metrics_collector
from .ctp_alerts import alert_manager
from .prometheus_exporter import prometheus_exporter, setup_prometheus_metrics, start_background_collection
from .alert_rules_sync import setup_alert_rules
from ..core.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def start_monitoring_services():
    """启动监控服务"""
    try:
        logger.info("Starting monitoring services...")

        # 设置日志系统
        setup_logging()
        logger.info("Logging system configured")

        # 设置告警规则
        await setup_alert_rules()
        logger.info("Alert rules configured")

        # 启动指标收集
        await metrics_collector.start_collection()
        logger.info("Metrics collection started")

        # 启动告警监控
        await alert_manager.start_monitoring()
        logger.info("Alert monitoring started")

        # 启动后台指标收集
        asyncio.create_task(start_background_collection())
        logger.info("Background metrics collection started")

        logger.info("All monitoring services started successfully")

    except Exception as e:
        logger.error(f"Failed to start monitoring services: {e}")
        raise


async def stop_monitoring_services():
    """停止监控服务"""
    try:
        logger.info("Stopping monitoring services...")
        
        # 停止告警监控
        await alert_manager.stop_monitoring()
        logger.info("Alert monitoring stopped")
        
        # 停止指标收集
        await metrics_collector.stop_collection()
        logger.info("Metrics collection stopped")
        
        logger.info("All monitoring services stopped successfully")
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring services: {e}")


@asynccontextmanager
async def monitoring_lifespan(app: FastAPI):
    """监控系统生命周期管理"""
    # 启动时
    await start_monitoring_services()
    
    try:
        yield
    finally:
        # 关闭时
        await stop_monitoring_services()


def setup_monitoring_startup(app: FastAPI):
    """设置监控系统启动事件"""

    # 设置Prometheus指标端点
    setup_prometheus_metrics(app)

    @app.on_event("startup")
    async def startup_monitoring():
        """应用启动时启动监控"""
        await start_monitoring_services()

    @app.on_event("shutdown")
    async def shutdown_monitoring():
        """应用关闭时停止监控"""
        await stop_monitoring_services()


# 健康检查端点（独立于认证）
async def health_check():
    """健康检查"""
    try:
        health = await metrics_collector.get_health_status()
        return {
            "status": health["status"],
            "timestamp": health["last_update"],
            "monitoring": {
                "metrics_running": metrics_collector.running,
                "alerts_running": alert_manager.running
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "monitoring": {
                "metrics_running": False,
                "alerts_running": False
            }
        }


# 就绪检查端点
async def readiness_check():
    """就绪检查"""
    try:
        # 检查监控服务是否运行
        if not metrics_collector.running or not alert_manager.running:
            return {"status": "not_ready", "reason": "Monitoring services not running"}
        
        # 检查系统健康状态
        health = await metrics_collector.get_health_status()
        if health["status"] in ["healthy", "degraded"]:
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": health["reason"]}
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


# 存活检查端点
async def liveness_check():
    """存活检查"""
    try:
        # 简单的存活检查
        return {
            "status": "alive",
            "services": {
                "metrics_collector": metrics_collector is not None,
                "alert_manager": alert_manager is not None
            }
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return {"status": "error", "error": str(e)}
