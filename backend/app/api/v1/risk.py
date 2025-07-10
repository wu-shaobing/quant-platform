"""
风控相关API路由
提供风险监控、预警、限制管理等功能
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.schemas.trading import (
    RiskLimitData,
    RiskCheckResult,
    OrderRequest
)
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["风控"])


@router.get("/limits", response_model=RiskLimitData, summary="获取风控限制")
async def get_risk_limits(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户风控限制设置
    """
    risk_service = RiskService(db)
    
    risk_limits = await risk_service.get_user_risk_limits(current_user.id)
    if not risk_limits:
        # 如果用户没有风控设置，返回默认设置
        risk_limits = await risk_service.get_default_risk_limits()
    
    return RiskLimitData.model_validate(risk_limits)


@router.put("/limits", response_model=RiskLimitData, summary="更新风控限制")
async def update_risk_limits(
    risk_limits: RiskLimitData,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户风控限制设置
    """
    risk_service = RiskService(db)
    
    updated_limits = await risk_service.update_user_risk_limits(
        current_user.id, 
        risk_limits
    )
    
    return RiskLimitData.model_validate(updated_limits)


@router.post("/check", response_model=RiskCheckResult, summary="风险检查")
async def check_risk(
    order_request: OrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对订单进行风险检查
    
    - **order_request**: 订单请求信息
    """
    risk_service = RiskService(db)
    
    risk_check = await risk_service.check_order_risk(
        user_id=current_user.id,
        order_request=order_request
    )
    
    return risk_check


@router.get("/alerts", summary="获取风险预警")
async def get_risk_alerts(
    level: Optional[str] = Query(None, description="预警级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取风险预警记录
    
    - **level**: 预警级别筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    """
    risk_service = RiskService(db)
    
    # 如果没有指定时间范围，默认查询最近7天
    if not start_time:
        start_time = datetime.now() - timedelta(days=7)
    if not end_time:
        end_time = datetime.now()
    
    alerts = await risk_service.get_user_risk_alerts(
        user_id=current_user.id,
        level=level,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "skip": skip,
        "limit": limit
    }


@router.get("/monitoring", summary="风险监控状态")
async def get_risk_monitoring(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前风险监控状态
    """
    risk_service = RiskService(db)
    
    monitoring_data = await risk_service.get_risk_monitoring_data(current_user.id)
    
    return monitoring_data


@router.get("/report", summary="风险报告")
async def get_risk_report(
    report_type: str = Query("daily", description="报告类型(daily/weekly/monthly)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取风险报告
    
    - **report_type**: 报告类型
    """
    risk_service = RiskService(db)
    
    report = await risk_service.generate_risk_report(
        user_id=current_user.id,
        report_type=report_type
    )
    
    return report


# 管理员功能
@router.get("/admin/limits", summary="获取所有用户风控限制")
async def get_all_risk_limits(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户的风控限制设置（管理员权限）
    """
    risk_service = RiskService(db)
    
    all_limits = await risk_service.get_all_user_risk_limits(skip=skip, limit=limit)
    
    return {
        "limits": all_limits,
        "total": len(all_limits),
        "skip": skip,
        "limit": limit
    }


@router.put("/admin/limits/{user_id}", summary="管理员更新用户风控限制")
async def admin_update_risk_limits(
    user_id: int,
    risk_limits: RiskLimitData,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    管理员更新指定用户的风控限制（管理员权限）
    
    - **user_id**: 用户ID
    - **risk_limits**: 风控限制配置
    """
    risk_service = RiskService(db)
    
    updated_limits = await risk_service.update_user_risk_limits(
        user_id, 
        risk_limits
    )
    
    return {
        "user_id": user_id,
        "limits": RiskLimitData.model_validate(updated_limits),
        "message": "风控限制更新成功"
    }


@router.get("/admin/alerts", summary="获取所有风险预警")
async def get_all_risk_alerts(
    level: Optional[str] = Query(None, description="预警级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户的风险预警记录（管理员权限）
    """
    risk_service = RiskService(db)
    
    # 如果没有指定时间范围，默认查询最近7天
    if not start_time:
        start_time = datetime.now() - timedelta(days=7)
    if not end_time:
        end_time = datetime.now()
    
    alerts = await risk_service.get_all_risk_alerts(
        level=level,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "skip": skip,
        "limit": limit
    }


@router.get("/admin/statistics", summary="风控统计信息")
async def get_risk_statistics(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取风控统计信息（管理员权限）
    """
    risk_service = RiskService(db)
    
    stats = await risk_service.get_risk_statistics()
    
    return stats


@router.get("/health", summary="健康检查")
async def health_check():
    """
    风控服务健康检查
    """
    return {
        "status": "healthy",
        "service": "risk",
        "timestamp": datetime.now().isoformat()
    }