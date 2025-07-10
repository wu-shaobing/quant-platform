"""
安全监控仪表板API
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.core.security_hardening import (
    security_hardening, 
    jwt_security_manager, 
    advanced_encryption,
    AuditEvent,
    AuditEventType,
    SecurityLevel
)
from app.core.ctp_security_config import (
    default_security_config,
    production_security_config,
    development_security_config
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security-dashboard", tags=["安全监控仪表板"])


@router.get("/overview", summary="安全概览")
async def get_security_overview(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取安全监控概览"""
    try:
        # 获取最近24小时的统计数据
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # 查询审计事件
        recent_events = await security_hardening.audit_logger.query_events(
            start_date=start_time,
            end_date=end_time
        )
        
        # 统计事件类型
        event_type_stats = {}
        risk_level_stats = {}
        hourly_stats = {}
        
        for event in recent_events:
            # 事件类型统计
            event_type = event.get("event_type", "UNKNOWN")
            event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1
            
            # 风险级别统计
            risk_level = event.get("risk_level", "LOW")
            risk_level_stats[risk_level] = risk_level_stats.get(risk_level, 0) + 1
            
            # 按小时统计
            event_time = event.get("timestamp", datetime.now())
            if isinstance(event_time, str):
                event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            hour_key = event_time.strftime("%Y-%m-%d %H:00")
            hourly_stats[hour_key] = hourly_stats.get(hour_key, 0) + 1
        
        # 获取系统安全状态
        security_status = {
            "security_enabled": security_hardening.security_enabled,
            "threat_detection_enabled": security_hardening.threat_detection_enabled,
            "active_sessions": len(jwt_security_manager.refresh_token_store),
            "blacklisted_tokens": len(jwt_security_manager.token_blacklist),
            "whitelisted_ips": len(security_hardening.access_controller.ip_whitelist),
            "blacklisted_ips": len(security_hardening.access_controller.ip_blacklist),
            "blocked_users": len(security_hardening.access_controller.blocked_users)
        }
        
        # 计算安全评分
        security_score = calculate_security_score(
            event_type_stats, risk_level_stats, security_status
        )
        
        return {
            "status": "success",
            "overview": {
                "security_score": security_score,
                "total_events_24h": len(recent_events),
                "high_risk_events": risk_level_stats.get("HIGH", 0) + risk_level_stats.get("CRITICAL", 0),
                "security_status": security_status,
                "event_type_stats": event_type_stats,
                "risk_level_stats": risk_level_stats,
                "hourly_stats": hourly_stats,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取安全概览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全概览失败: {str(e)}"
        )


@router.get("/threats", summary="威胁检测")
async def get_threat_detection(
    hours: int = 24,
    risk_level: str = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取威胁检测信息"""
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 解析风险级别
        risk_level_enum = None
        if risk_level:
            try:
                risk_level_enum = SecurityLevel(risk_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的风险级别: {risk_level}"
                )
        
        # 查询威胁事件
        threat_events = await security_hardening.audit_logger.query_events(
            start_date=start_time,
            end_date=end_time,
            risk_level=risk_level_enum
        )
        
        # 分析威胁模式
        threat_patterns = analyze_threat_patterns(threat_events)
        
        # 获取被阻止的IP和用户
        blocked_entities = {
            "blocked_ips": list(security_hardening.access_controller.ip_blacklist),
            "blocked_users": list(security_hardening.access_controller.blocked_users),
            "suspicious_ips": get_suspicious_ips(threat_events)
        }
        
        # 威胁趋势分析
        threat_trends = analyze_threat_trends(threat_events, hours)
        
        return {
            "status": "success",
            "threats": {
                "total_threats": len(threat_events),
                "threat_events": threat_events[:50],  # 限制返回数量
                "threat_patterns": threat_patterns,
                "blocked_entities": blocked_entities,
                "threat_trends": threat_trends,
                "query_period": f"{hours} hours",
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取威胁检测信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取威胁检测信息失败: {str(e)}"
        )


@router.get("/performance", summary="安全性能指标")
async def get_security_performance(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取安全性能指标"""
    try:
        # 获取速率限制统计
        rate_limit_stats = {
            "default_limit": security_hardening.access_controller.rate_limits["default"],
            "trading_limit": security_hardening.access_controller.rate_limits["trading"],
            "query_limit": security_hardening.access_controller.rate_limits["query"],
            "current_usage": get_current_rate_limit_usage()
        }
        
        # 获取加密性能指标
        encryption_stats = {
            "total_encrypted_fields": len(advanced_encryption.field_encryption_keys),
            "supported_algorithms": list(advanced_encryption.encryption_algorithms.keys()),
            "encryption_performance": await measure_encryption_performance()
        }
        
        # 获取JWT性能指标
        jwt_stats = {
            "active_tokens": len(jwt_security_manager.refresh_token_store),
            "blacklisted_tokens": len(jwt_security_manager.token_blacklist),
            "token_lifetime": jwt_security_manager.max_token_lifetime,
            "refresh_token_lifetime": jwt_security_manager.refresh_token_lifetime
        }
        
        # 系统资源使用情况
        system_resources = get_security_system_resources()
        
        return {
            "status": "success",
            "performance": {
                "rate_limiting": rate_limit_stats,
                "encryption": encryption_stats,
                "jwt_management": jwt_stats,
                "system_resources": system_resources,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取安全性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全性能指标失败: {str(e)}"
        )


@router.get("/config", summary="安全配置")
async def get_security_config(
    config_type: str = "current",
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取安全配置"""
    try:
        if config_type == "default":
            config = default_security_config
        elif config_type == "production":
            config = production_security_config
        elif config_type == "development":
            config = development_security_config
        else:
            # 返回当前配置（基于默认配置）
            config = default_security_config
        
        return {
            "status": "success",
            "config": config.to_dict(),
            "config_type": config_type,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取安全配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全配置失败: {str(e)}"
        )


@router.post("/config/update", summary="更新安全配置")
async def update_security_config(
    config_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """更新安全配置"""
    try:
        # 验证用户权限（这里简化处理，实际应该检查管理员权限）
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 更新配置
        from app.core.ctp_security_config import SecurityHardeningConfig
        new_config = SecurityHardeningConfig.from_dict(config_data)
        
        # 记录配置变更审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id=current_user.id,
            ip_address="unknown",
            user_agent="API",
            endpoint="/api/v1/security-dashboard/config/update",
            method="POST",
            request_data={"config_keys": list(config_data.keys())},
            response_status=200,
            risk_level=SecurityLevel.HIGH
        ))
        
        return {
            "status": "success",
            "message": "安全配置更新成功",
            "updated_config": new_config.to_dict(),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"更新安全配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新安全配置失败: {str(e)}"
        )


# 辅助函数

def calculate_security_score(
    event_type_stats: Dict[str, int],
    risk_level_stats: Dict[str, int],
    security_status: Dict[str, Any]
) -> int:
    """计算安全评分（0-100）"""
    base_score = 100
    
    # 根据高风险事件扣分
    high_risk_events = risk_level_stats.get("HIGH", 0) + risk_level_stats.get("CRITICAL", 0)
    base_score -= min(high_risk_events * 2, 30)
    
    # 根据安全功能启用情况加分
    if security_status.get("security_enabled"):
        base_score += 5
    if security_status.get("threat_detection_enabled"):
        base_score += 5
    
    # 根据被阻止的恶意实体数量调整
    blocked_entities = security_status.get("blacklisted_ips", 0) + security_status.get("blocked_users", 0)
    if blocked_entities > 0:
        base_score -= min(blocked_entities, 10)
    
    return max(0, min(100, base_score))


def analyze_threat_patterns(threat_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析威胁模式"""
    patterns = {
        "top_threat_types": {},
        "top_source_ips": {},
        "attack_frequency": {},
        "target_endpoints": {}
    }
    
    for event in threat_events:
        # 威胁类型统计
        event_type = event.get("event_type", "UNKNOWN")
        patterns["top_threat_types"][event_type] = patterns["top_threat_types"].get(event_type, 0) + 1
        
        # 源IP统计
        ip_address = event.get("ip_address", "unknown")
        patterns["top_source_ips"][ip_address] = patterns["top_source_ips"].get(ip_address, 0) + 1
        
        # 目标端点统计
        endpoint = event.get("endpoint", "unknown")
        patterns["target_endpoints"][endpoint] = patterns["target_endpoints"].get(endpoint, 0) + 1
    
    # 排序并取前10
    for key in patterns:
        if isinstance(patterns[key], dict):
            patterns[key] = dict(sorted(patterns[key].items(), key=lambda x: x[1], reverse=True)[:10])
    
    return patterns


def get_suspicious_ips(threat_events: List[Dict[str, Any]]) -> List[str]:
    """获取可疑IP列表"""
    ip_counts = {}
    for event in threat_events:
        ip = event.get("ip_address", "unknown")
        if ip != "unknown":
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    
    # 返回请求次数超过阈值的IP
    suspicious_threshold = 10
    return [ip for ip, count in ip_counts.items() if count > suspicious_threshold]


def analyze_threat_trends(threat_events: List[Dict[str, Any]], hours: int) -> Dict[str, Any]:
    """分析威胁趋势"""
    trends = {
        "hourly_distribution": {},
        "threat_escalation": [],
        "peak_hours": []
    }
    
    # 按小时分布
    for event in threat_events:
        timestamp = event.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        hour_key = timestamp.strftime("%H:00")
        trends["hourly_distribution"][hour_key] = trends["hourly_distribution"].get(hour_key, 0) + 1
    
    # 找出峰值时间
    if trends["hourly_distribution"]:
        sorted_hours = sorted(trends["hourly_distribution"].items(), key=lambda x: x[1], reverse=True)
        trends["peak_hours"] = [hour for hour, count in sorted_hours[:3]]
    
    return trends


def get_current_rate_limit_usage() -> Dict[str, Any]:
    """获取当前速率限制使用情况"""
    # 这里应该从Redis或内存中获取实际的使用情况
    # 暂时返回模拟数据
    return {
        "default": {"used": 45, "limit": 100, "percentage": 45},
        "trading": {"used": 23, "limit": 50, "percentage": 46},
        "query": {"used": 78, "limit": 200, "percentage": 39}
    }


async def measure_encryption_performance() -> Dict[str, Any]:
    """测量加密性能"""
    import time
    
    test_data = "test_encryption_performance_data" * 10
    performance_results = {}
    
    for algorithm in ["AES-256-GCM", "ChaCha20-Poly1305", "Fernet"]:
        try:
            start_time = time.time()
            encrypted = await advanced_encryption.encrypt_field("test_field", test_data, algorithm)
            encrypt_time = time.time() - start_time
            
            start_time = time.time()
            await advanced_encryption.decrypt_field("test_field", encrypted)
            decrypt_time = time.time() - start_time
            
            performance_results[algorithm] = {
                "encrypt_time_ms": round(encrypt_time * 1000, 2),
                "decrypt_time_ms": round(decrypt_time * 1000, 2),
                "total_time_ms": round((encrypt_time + decrypt_time) * 1000, 2)
            }
        except Exception as e:
            performance_results[algorithm] = {"error": str(e)}
    
    return performance_results


def get_security_system_resources() -> Dict[str, Any]:
    """获取安全系统资源使用情况"""
    import psutil
    
    try:
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_connections": len(psutil.net_connections()),
            "process_count": len(psutil.pids())
        }
    except Exception:
        return {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "network_connections": 0,
            "process_count": 0,
            "error": "Unable to get system resources"
        }
