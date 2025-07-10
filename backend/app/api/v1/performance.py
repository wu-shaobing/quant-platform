"""
CTP性能优化API端点
提供性能监控和优化控制接口
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.core.cache import cache_manager
from app.core.memory_pool import ctp_data_pool
from app.core.connection_pool import ctp_connection_manager
from app.services.ctp_performance import ctp_performance_service
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/performance", tags=["性能优化"])


@router.get("/metrics", summary="获取性能指标")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """获取系统性能指标"""
    try:
        metrics = await ctp_performance_service.get_performance_metrics()
        
        # 添加内存池统计
        memory_pool_stats = ctp_data_pool.get_all_stats()
        metrics["memory_pools"] = [
            {
                "name": stat.pool_name,
                "total_objects": stat.total_objects,
                "available_objects": stat.available_objects,
                "in_use_objects": stat.in_use_objects,
                "hit_rate": stat.hit_rate,
                "created_count": stat.created_count,
                "recycled_count": stat.recycled_count
            }
            for stat in memory_pool_stats
        ]
        
        # 添加连接池统计
        connection_pool_stats = ctp_connection_manager.get_all_stats()
        metrics["connection_pools"] = connection_pool_stats
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/cache/stats", summary="获取缓存统计")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """获取缓存统计信息"""
    try:
        stats = await cache_manager.get_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.post("/cache/clear", summary="清除缓存")
async def clear_cache(
    pattern: str = Query(..., description="缓存键模式"),
    current_user: User = Depends(get_current_user)
):
    """清除指定模式的缓存"""
    try:
        cleared_count = await cache_manager.clear_pattern(pattern)
        return JSONResponse(content={
            "message": f"已清除 {cleared_count} 个缓存项",
            "pattern": pattern,
            "cleared_count": cleared_count
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.post("/cache/user/{user_id}/preload", summary="预加载用户缓存")
async def preload_user_cache(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """预加载指定用户的缓存数据"""
    try:
        success = await ctp_performance_service.batch_cache_user_data(user_id)
        
        if success:
            return JSONResponse(content={
                "message": f"用户 {user_id} 缓存预加载成功",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=500, detail="缓存预加载失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预加载用户缓存失败: {str(e)}")


@router.delete("/cache/user/{user_id}", summary="清除用户缓存")
async def clear_user_cache(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """清除指定用户的所有缓存"""
    try:
        success = await ctp_performance_service.clear_user_cache(user_id)
        
        if success:
            return JSONResponse(content={
                "message": f"用户 {user_id} 缓存清除成功",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=500, detail="缓存清除失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除用户缓存失败: {str(e)}")


@router.get("/orders/optimized", summary="优化的订单查询")
async def get_orders_optimized(
    limit: int = Query(100, ge=1, le=1000, description="查询数量限制"),
    status_filter: Optional[str] = Query(None, description="订单状态过滤"),
    instrument_filter: Optional[str] = Query(None, description="合约代码过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取优化的订单数据"""
    try:
        orders = await ctp_performance_service.get_user_orders_optimized(
            user_id=current_user.id,
            limit=limit,
            status_filter=status_filter,
            instrument_filter=instrument_filter
        )
        
        return JSONResponse(content={
            "orders": orders,
            "count": len(orders),
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单数据失败: {str(e)}")


@router.get("/trades/optimized", summary="优化的成交查询")
async def get_trades_optimized(
    limit: int = Query(100, ge=1, le=1000, description="查询数量限制"),
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    """获取优化的成交数据"""
    try:
        trades = await ctp_performance_service.get_user_trades_optimized(
            user_id=current_user.id,
            limit=limit,
            date_from=date_from,
            date_to=date_to
        )
        
        return JSONResponse(content={
            "trades": trades,
            "count": len(trades),
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取成交数据失败: {str(e)}")


@router.get("/positions/optimized", summary="优化的持仓查询")
async def get_positions_optimized(
    current_user: User = Depends(get_current_user)
):
    """获取优化的持仓数据"""
    try:
        positions = await ctp_performance_service.get_user_positions_optimized(
            user_id=current_user.id
        )
        
        return JSONResponse(content={
            "positions": positions,
            "count": len(positions),
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓数据失败: {str(e)}")


@router.get("/statistics", summary="交易统计信息")
async def get_trading_statistics(
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user)
):
    """获取交易统计信息"""
    try:
        stats = await ctp_performance_service.get_trading_statistics(
            user_id=current_user.id,
            date_from=date_from,
            date_to=date_to
        )
        
        return JSONResponse(content={
            "statistics": stats,
            "user_id": current_user.id,
            "date_range": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易统计失败: {str(e)}")


@router.get("/memory-pools/stats", summary="内存池统计")
async def get_memory_pool_stats(
    current_user: User = Depends(get_current_user)
):
    """获取内存池统计信息"""
    try:
        stats = ctp_data_pool.get_all_stats()
        
        return JSONResponse(content={
            "memory_pools": [
                {
                    "name": stat.pool_name,
                    "total_objects": stat.total_objects,
                    "available_objects": stat.available_objects,
                    "in_use_objects": stat.in_use_objects,
                    "hit_rate": round(stat.hit_rate, 2),
                    "created_count": stat.created_count,
                    "recycled_count": stat.recycled_count,
                    "last_reset": stat.last_reset.isoformat()
                }
                for stat in stats
            ],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存池统计失败: {str(e)}")


@router.post("/memory-pools/clear", summary="清空内存池")
async def clear_memory_pools(
    current_user: User = Depends(get_current_user)
):
    """清空所有内存池"""
    try:
        ctp_data_pool.clear_all_pools()
        
        return JSONResponse(content={
            "message": "所有内存池已清空",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空内存池失败: {str(e)}")


@router.get("/connection-pools/stats", summary="连接池统计")
async def get_connection_pool_stats(
    current_user: User = Depends(get_current_user)
):
    """获取连接池统计信息"""
    try:
        stats = ctp_connection_manager.get_all_stats()
        
        return JSONResponse(content={
            "connection_pools": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接池统计失败: {str(e)}")


@router.get("/health", summary="性能健康检查")
async def performance_health_check():
    """性能系统健康检查"""
    try:
        # 检查缓存连接
        cache_healthy = await cache_manager.exists("health_check")
        await cache_manager.set("health_check", "ok", 60)
        
        # 检查数据库连接
        from app.core.database import db_manager
        db_healthy = await db_manager.health_check()
        
        # 检查内存池状态
        memory_stats = ctp_data_pool.get_all_stats()
        memory_healthy = all(stat.total_objects > 0 for stat in memory_stats)
        
        health_status = {
            "cache": "healthy" if cache_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy", 
            "memory_pools": "healthy" if memory_healthy else "unhealthy",
            "overall": "healthy" if all([cache_healthy, db_healthy, memory_healthy]) else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if health_status["overall"] == "healthy" else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        return JSONResponse(
            content={
                "overall": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )
