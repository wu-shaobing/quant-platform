"""
监控API路由
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from app.monitoring import metrics_collector, alert_manager, AlertLevel
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ctp_service import ctp_service

router = APIRouter()


class MetricsResponse(BaseModel):
    """指标响应模型"""
    connection_status: Dict[str, bool]
    connection_uptime: Dict[str, float]
    order_stats: Dict[str, Any]
    trade_count: int
    market_data: Dict[str, Any]
    system: Dict[str, Any]
    errors: Dict[str, int]
    last_update: str


class HealthResponse(BaseModel):
    """健康状态响应模型"""
    status: str
    reason: str
    connections: Dict[str, bool]
    error_rate: float
    last_update: str
    uptime: Dict[str, float]


class AlertResponse(BaseModel):
    """告警响应模型"""
    id: str
    title: str
    description: str
    level: str
    status: str
    source: str
    category: str
    tags: Dict[str, str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    count: int


class AlertCreateRequest(BaseModel):
    """创建告警请求模型"""
    title: str
    description: str
    level: str
    category: str = "manual"
    tags: Dict[str, str] = {}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(current_user: User = Depends(get_current_user)):
    """获取系统指标"""
    try:
        metrics = await metrics_collector.get_metrics_summary()
        return MetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def get_health_status():
    """获取健康状态（无需认证）"""
    try:
        # 获取CTP服务状态
        ctp_status = await ctp_service.get_monitoring_status()

        # 获取监控系统健康状态
        health = await metrics_collector.get_health_status()

        # 合并CTP服务状态
        health["connections"].update({
            "ctp_trade": ctp_status["service_status"]["trade_connected"],
            "ctp_md": ctp_status["service_status"]["md_connected"]
        })

        # 更新整体状态
        if not ctp_status["service_status"]["is_ready"]:
            health["status"] = "degraded"
            health["reason"] += "; CTP service not ready"

        return HealthResponse(**health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """就绪检查（Kubernetes使用）"""
    try:
        health = await metrics_collector.get_health_status()
        if health["status"] in ["healthy", "degraded"]:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")


@router.get("/live")
async def liveness_check():
    """存活检查（Kubernetes使用）"""
    try:
        # 简单的存活检查，只要服务能响应就认为存活
        return {"status": "alive", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Liveness check failed: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(current_user: User = Depends(get_current_user)):
    """获取活跃告警"""
    try:
        alerts = await alert_manager.get_active_alerts()
        return [AlertResponse(**alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history(
    hours: int = Query(24, ge=1, le=168),  # 1小时到7天
    current_user: User = Depends(get_current_user)
):
    """获取告警历史"""
    try:
        alerts = await alert_manager.get_alert_history(hours=hours)
        return [AlertResponse(**alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")


@router.post("/alerts", response_model=AlertResponse)
async def create_manual_alert(
    alert_request: AlertCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """创建手动告警"""
    try:
        from app.monitoring.ctp_alerts import Alert, AlertStatus
        import uuid
        
        # 验证告警级别
        try:
            level = AlertLevel(alert_request.level.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid alert level")
        
        # 创建告警
        alert = Alert(
            id=str(uuid.uuid4()),
            title=alert_request.title,
            description=alert_request.description,
            level=level,
            status=AlertStatus.ACTIVE,
            source="manual",
            category=alert_request.category,
            tags={
                **alert_request.tags,
                "created_by": current_user.username,
                "user_id": str(current_user.id)
            }
        )
        
        # 添加到告警管理器
        alert_manager.alerts[alert.id] = alert
        
        # 发送通知
        await alert_manager._send_notifications(alert)
        
        return AlertResponse(**alert.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """解决告警"""
    try:
        if alert_id not in alert_manager.alerts:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        await alert_manager.resolve_alert(alert_id)
        
        # 添加解决者信息
        alert = alert_manager.alerts[alert_id]
        alert.tags.update({
            "resolved_by": current_user.username,
            "resolver_id": str(current_user.id)
        })
        
        return {"message": "Alert resolved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get("/metrics/connection")
async def get_connection_metrics(current_user: User = Depends(get_current_user)):
    """获取连接指标详情"""
    try:
        metrics = await metrics_collector.get_metrics_summary()
        return {
            "connection_status": metrics["connection_status"],
            "connection_uptime": metrics["connection_uptime"],
            "last_update": metrics["last_update"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection metrics: {str(e)}")


@router.get("/metrics/trading")
async def get_trading_metrics(current_user: User = Depends(get_current_user)):
    """获取交易指标详情"""
    try:
        metrics = await metrics_collector.get_metrics_summary()
        return {
            "order_stats": metrics["order_stats"],
            "trade_count": metrics["trade_count"],
            "last_update": metrics["last_update"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading metrics: {str(e)}")


@router.get("/metrics/market-data")
async def get_market_data_metrics(current_user: User = Depends(get_current_user)):
    """获取行情数据指标详情"""
    try:
        metrics = await metrics_collector.get_metrics_summary()
        return {
            "market_data": metrics["market_data"],
            "last_update": metrics["last_update"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market data metrics: {str(e)}")


@router.get("/metrics/system")
async def get_system_metrics(current_user: User = Depends(get_current_user)):
    """获取系统指标详情"""
    try:
        metrics = await metrics_collector.get_metrics_summary()
        return {
            "system": metrics["system"],
            "errors": metrics["errors"],
            "last_update": metrics["last_update"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system metrics: {str(e)}")


@router.post("/metrics/start")
async def start_metrics_collection(current_user: User = Depends(get_current_user)):
    """启动指标收集"""
    try:
        await metrics_collector.start_collection()
        return {"message": "Metrics collection started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start metrics collection: {str(e)}")


@router.post("/metrics/stop")
async def stop_metrics_collection(current_user: User = Depends(get_current_user)):
    """停止指标收集"""
    try:
        await metrics_collector.stop_collection()
        return {"message": "Metrics collection stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop metrics collection: {str(e)}")


@router.post("/alerts/start")
async def start_alert_monitoring(current_user: User = Depends(get_current_user)):
    """启动告警监控"""
    try:
        await alert_manager.start_monitoring()
        return {"message": "Alert monitoring started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start alert monitoring: {str(e)}")


@router.post("/alerts/stop")
async def stop_alert_monitoring(current_user: User = Depends(get_current_user)):
    """停止告警监控"""
    try:
        await alert_manager.stop_monitoring()
        return {"message": "Alert monitoring stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop alert monitoring: {str(e)}")


@router.get("/status")
async def get_monitoring_status(current_user: User = Depends(get_current_user)):
    """获取监控系统状态"""
    try:
        return {
            "metrics_collection_running": metrics_collector.running,
            "alert_monitoring_running": alert_manager.running,
            "metrics_port": metrics_collector.metrics_port,
            "collection_interval": metrics_collector.collection_interval,
            "alert_check_interval": alert_manager.check_interval,
            "active_alert_count": len(await alert_manager.get_active_alerts()),
            "notification_channels": len(alert_manager.channels),
            "alert_rules": len(alert_manager.rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")
