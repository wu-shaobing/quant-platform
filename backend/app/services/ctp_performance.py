"""
CTP性能优化服务
提供高性能的数据查询和缓存策略
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import db_manager
from app.core.cache import cache_manager, CTPCacheKeys, cache_result
from app.models.ctp_models import CTPOrder, CTPTrade, CTPPosition, CTPAccount

logger = logging.getLogger(__name__)


class CTPPerformanceService:
    """CTP性能优化服务"""
    
    def __init__(self):
        self.cache_expire_short = 30  # 30秒 - 实时数据
        self.cache_expire_medium = 300  # 5分钟 - 准实时数据
        self.cache_expire_long = 3600  # 1小时 - 静态数据
    
    async def get_user_orders_optimized(
        self, 
        user_id: int, 
        limit: int = 100,
        status_filter: Optional[str] = None,
        instrument_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """优化的用户订单查询"""
        
        # 生成缓存键
        cache_key = f"{CTPCacheKeys.user_orders(user_id)}:{limit}:{status_filter}:{instrument_filter}"
        
        # 尝试从缓存获取
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        async with db_manager.get_session() as session:
            # 构建优化查询
            query = select(CTPOrder).where(CTPOrder.user_id == user_id)
            
            # 添加过滤条件
            if status_filter:
                query = query.where(CTPOrder.order_status == status_filter)
            if instrument_filter:
                query = query.where(CTPOrder.instrument_id == instrument_filter)
            
            # 优化排序和限制
            query = query.order_by(CTPOrder.created_at.desc()).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            orders = result.scalars().all()
            
            # 转换为字典格式
            orders_data = [
                {
                    "id": str(order.id),
                    "order_ref": order.order_ref,
                    "order_sys_id": order.order_sys_id,
                    "instrument_id": order.instrument_id,
                    "direction": order.direction,
                    "offset_flag": order.offset_flag,
                    "limit_price": float(order.limit_price),
                    "volume_total_original": order.volume_total_original,
                    "volume_traded": order.volume_traded,
                    "order_status": order.order_status,
                    "created_at": order.created_at.isoformat(),
                }
                for order in orders
            ]
            
            # 缓存结果
            await cache_manager.set(cache_key, orders_data, self.cache_expire_short)
            
            return orders_data
    
    async def get_user_trades_optimized(
        self, 
        user_id: int, 
        limit: int = 100,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """优化的用户成交查询"""
        
        # 生成缓存键
        cache_key = f"ctp:trades:user:{user_id}:{limit}:{date_from}:{date_to}"
        
        # 尝试从缓存获取
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        async with db_manager.get_session() as session:
            # 构建查询
            query = select(CTPTrade).where(CTPTrade.user_id == user_id)
            
            # 添加日期过滤
            if date_from:
                query = query.where(CTPTrade.created_at >= date_from)
            if date_to:
                query = query.where(CTPTrade.created_at <= date_to)
            
            # 优化排序和限制
            query = query.order_by(CTPTrade.created_at.desc()).limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            trades = result.scalars().all()
            
            # 转换为字典格式
            trades_data = [
                {
                    "id": str(trade.id),
                    "trade_id": trade.trade_id,
                    "order_ref": trade.order_ref,
                    "instrument_id": trade.instrument_id,
                    "direction": trade.direction,
                    "offset_flag": trade.offset_flag,
                    "price": float(trade.price),
                    "volume": trade.volume,
                    "trade_time": trade.trade_time,
                    "created_at": trade.created_at.isoformat(),
                }
                for trade in trades
            ]
            
            # 缓存结果
            await cache_manager.set(cache_key, trades_data, self.cache_expire_medium)
            
            return trades_data
    
    async def get_user_positions_optimized(self, user_id: int) -> List[Dict[str, Any]]:
        """优化的用户持仓查询"""
        
        cache_key = CTPCacheKeys.user_positions(user_id)
        
        # 尝试从缓存获取
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        async with db_manager.get_session() as session:
            # 使用原生SQL查询以获得最佳性能
            query = text("""
                SELECT 
                    instrument_id,
                    direction,
                    SUM(CASE WHEN offset_flag = '0' THEN volume ELSE -volume END) as position,
                    AVG(price) as avg_price,
                    COUNT(*) as trade_count
                FROM ctp_trades 
                WHERE user_id = :user_id 
                GROUP BY instrument_id, direction
                HAVING position != 0
                ORDER BY instrument_id, direction
            """)
            
            result = await session.execute(query, {"user_id": user_id})
            positions = result.fetchall()
            
            # 转换为字典格式
            positions_data = [
                {
                    "instrument_id": row.instrument_id,
                    "direction": row.direction,
                    "position": row.position,
                    "avg_price": float(row.avg_price) if row.avg_price else 0.0,
                    "trade_count": row.trade_count,
                }
                for row in positions
            ]
            
            # 缓存结果
            await cache_manager.set(cache_key, positions_data, self.cache_expire_short)
            
            return positions_data
    
    async def get_trading_statistics(
        self, 
        user_id: int, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取交易统计信息"""
        
        cache_key = f"ctp:stats:user:{user_id}:{date_from}:{date_to}"
        
        # 尝试从缓存获取
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        async with db_manager.get_session() as session:
            # 使用聚合查询获取统计信息
            base_query = select(CTPTrade).where(CTPTrade.user_id == user_id)
            
            if date_from:
                base_query = base_query.where(CTPTrade.created_at >= date_from)
            if date_to:
                base_query = base_query.where(CTPTrade.created_at <= date_to)
            
            # 总成交量和成交金额
            volume_query = select(
                func.sum(CTPTrade.volume).label('total_volume'),
                func.sum(CTPTrade.price * CTPTrade.volume).label('total_amount'),
                func.count(CTPTrade.id).label('trade_count')
            ).where(CTPTrade.user_id == user_id)
            
            if date_from:
                volume_query = volume_query.where(CTPTrade.created_at >= date_from)
            if date_to:
                volume_query = volume_query.where(CTPTrade.created_at <= date_to)
            
            volume_result = await session.execute(volume_query)
            volume_data = volume_result.first()
            
            # 按合约统计
            instrument_query = select(
                CTPTrade.instrument_id,
                func.sum(CTPTrade.volume).label('volume'),
                func.count(CTPTrade.id).label('count')
            ).where(CTPTrade.user_id == user_id)
            
            if date_from:
                instrument_query = instrument_query.where(CTPTrade.created_at >= date_from)
            if date_to:
                instrument_query = instrument_query.where(CTPTrade.created_at <= date_to)
            
            instrument_query = instrument_query.group_by(CTPTrade.instrument_id).order_by(func.sum(CTPTrade.volume).desc())
            
            instrument_result = await session.execute(instrument_query)
            instrument_data = instrument_result.fetchall()
            
            # 构建统计结果
            stats = {
                "total_volume": int(volume_data.total_volume or 0),
                "total_amount": float(volume_data.total_amount or 0),
                "trade_count": int(volume_data.trade_count or 0),
                "instruments": [
                    {
                        "instrument_id": row.instrument_id,
                        "volume": int(row.volume),
                        "count": int(row.count)
                    }
                    for row in instrument_data
                ]
            }
            
            # 缓存结果
            await cache_manager.set(cache_key, stats, self.cache_expire_medium)
            
            return stats
    
    async def batch_cache_user_data(self, user_id: int) -> bool:
        """批量缓存用户数据"""
        try:
            # 并发获取多种数据并缓存
            tasks = [
                self.get_user_orders_optimized(user_id),
                self.get_user_trades_optimized(user_id),
                self.get_user_positions_optimized(user_id),
                self.get_trading_statistics(user_id)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            return True
            
        except Exception as e:
            logger.error(f"Batch cache user data error for user {user_id}: {e}")
            return False
    
    async def clear_user_cache(self, user_id: int) -> bool:
        """清除用户相关缓存"""
        try:
            patterns = [
                f"ctp:orders:user:{user_id}*",
                f"ctp:trades:user:{user_id}*",
                f"ctp:positions:user:{user_id}*",
                f"ctp:stats:user:{user_id}*",
                f"ctp:session:user:{user_id}*"
            ]
            
            for pattern in patterns:
                await cache_manager.clear_pattern(pattern)
            
            return True
            
        except Exception as e:
            logger.error(f"Clear user cache error for user {user_id}: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        try:
            # 数据库连接信息
            db_info = await db_manager.get_connection_info()
            
            # 缓存统计信息
            cache_stats = await cache_manager.get_stats()
            
            return {
                "database": db_info,
                "cache": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get performance metrics error: {e}")
            return {"error": str(e)}


# 全局性能服务实例
ctp_performance_service = CTPPerformanceService()


# 导出主要组件
__all__ = [
    "CTPPerformanceService",
    "ctp_performance_service",
]
