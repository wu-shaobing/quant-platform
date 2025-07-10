"""
数据库查询优化器
提供高性能的数据库查询和连接池管理
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.core.config import settings
from app.core.database import get_db
from app.models.ctp_models import CTPOrder, CTPTrade, CTPPosition, CTPAccount

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """查询类型"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    BULK_INSERT = "bulk_insert"
    BULK_UPDATE = "bulk_update"


@dataclass
class QueryMetrics:
    """查询性能指标"""
    query_type: QueryType
    execution_time: float
    rows_affected: int
    query_hash: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type.value,
            "execution_time": self.execution_time,
            "rows_affected": self.rows_affected,
            "query_hash": self.query_hash,
            "timestamp": self.timestamp.isoformat()
        }


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.query_metrics: List[QueryMetrics] = []
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
        self.connection_pool_size = 20
        self.max_overflow = 30
        self.pool_timeout = 30
        self.pool_recycle = 3600
    
    def create_optimized_engine(self):
        """创建优化的数据库引擎"""
        # 数据库连接URL
        database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        # 连接池配置
        engine = create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.connection_pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # 连接前检查
            echo=False,  # 生产环境关闭SQL日志
            future=True,
            # 连接参数优化
            connect_args={
                "server_settings": {
                    "application_name": "quant_platform",
                    "jit": "off",  # 关闭JIT编译以减少延迟
                },
                "command_timeout": 60,
                "prepared_statement_cache_size": 0,  # 禁用预处理语句缓存
            }
        )
        
        return engine
    
    @asynccontextmanager
    async def get_optimized_session(self):
        """获取优化的数据库会话"""
        async with get_db() as session:
            try:
                # 设置会话级别的优化参数
                await session.execute(text("SET LOCAL work_mem = '256MB'"))
                await session.execute(text("SET LOCAL random_page_cost = 1.1"))
                await session.execute(text("SET LOCAL effective_cache_size = '4GB'"))
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def execute_optimized_query(
        self,
        session: AsyncSession,
        query: Select,
        query_type: QueryType = QueryType.SELECT
    ) -> Any:
        """执行优化查询"""
        import time
        import hashlib
        
        start_time = time.time()
        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        query_hash = hashlib.md5(query_str.encode()).hexdigest()[:8]
        
        try:
            result = await session.execute(query)
            
            if query_type == QueryType.SELECT:
                rows = result.fetchall()
                rows_affected = len(rows)
                return_value = rows
            else:
                rows_affected = result.rowcount
                return_value = result
            
            execution_time = time.time() - start_time
            
            # 记录查询指标
            metrics = QueryMetrics(
                query_type=query_type,
                execution_time=execution_time,
                rows_affected=rows_affected,
                query_hash=query_hash,
                timestamp=datetime.now()
            )
            self.query_metrics.append(metrics)
            
            # 记录慢查询
            if execution_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {execution_time:.3f}s, "
                    f"hash: {query_hash}, rows: {rows_affected}"
                )
            
            return return_value
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}, time: {execution_time:.3f}s")
            raise
    
    def build_optimized_order_query(
        self,
        user_id: Optional[int] = None,
        instrument_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Select:
        """构建优化的订单查询"""
        query = select(CTPOrder)
        
        # 添加过滤条件
        conditions = []
        if user_id:
            conditions.append(CTPOrder.user_id == user_id)
        if instrument_id:
            conditions.append(CTPOrder.instrument_id == instrument_id)
        if status:
            conditions.append(CTPOrder.order_status == status)
        if start_date:
            conditions.append(CTPOrder.created_at >= start_date)
        if end_date:
            conditions.append(CTPOrder.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 添加排序和分页
        query = query.order_by(CTPOrder.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query
    
    def build_optimized_trade_query(
        self,
        user_id: Optional[int] = None,
        instrument_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Select:
        """构建优化的成交查询"""
        query = select(CTPTrade)
        
        conditions = []
        if user_id:
            conditions.append(CTPTrade.user_id == user_id)
        if instrument_id:
            conditions.append(CTPTrade.instrument_id == instrument_id)
        if start_date:
            conditions.append(CTPTrade.created_at >= start_date)
        if end_date:
            conditions.append(CTPTrade.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(CTPTrade.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query
    
    def build_optimized_position_query(
        self,
        user_id: int,
        instrument_id: Optional[str] = None
    ) -> Select:
        """构建优化的持仓查询"""
        query = select(CTPPosition).where(CTPPosition.user_id == user_id)
        
        if instrument_id:
            query = query.where(CTPPosition.instrument_id == instrument_id)
        
        # 只查询有持仓的记录
        query = query.where(CTPPosition.position > 0)
        
        return query
    
    async def bulk_insert_orders(
        self,
        session: AsyncSession,
        orders_data: List[Dict[str, Any]]
    ) -> int:
        """批量插入订单"""
        if not orders_data:
            return 0
        
        try:
            # 使用批量插入
            result = await session.execute(
                CTPOrder.__table__.insert(),
                orders_data
            )
            await session.commit()
            return len(orders_data)
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk insert orders failed: {e}")
            raise
    
    async def bulk_update_orders(
        self,
        session: AsyncSession,
        updates: List[Dict[str, Any]]
    ) -> int:
        """批量更新订单"""
        if not updates:
            return 0
        
        try:
            updated_count = 0
            for update_data in updates:
                order_id = update_data.pop('id')
                result = await session.execute(
                    CTPOrder.__table__.update()
                    .where(CTPOrder.id == order_id)
                    .values(**update_data)
                )
                updated_count += result.rowcount
            
            await session.commit()
            return updated_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk update orders failed: {e}")
            raise
    
    async def get_aggregated_statistics(
        self,
        session: AsyncSession,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取聚合统计数据"""
        try:
            # 订单统计
            order_stats = await session.execute(
                select(
                    func.count(CTPOrder.id).label('total_orders'),
                    func.sum(CTPOrder.volume_total_original).label('total_volume'),
                    func.count(CTPOrder.id).filter(CTPOrder.order_status == '1').label('filled_orders')
                )
                .where(
                    and_(
                        CTPOrder.user_id == user_id,
                        CTPOrder.created_at >= start_date,
                        CTPOrder.created_at <= end_date
                    )
                )
            )
            order_result = order_stats.first()
            
            # 成交统计
            trade_stats = await session.execute(
                select(
                    func.count(CTPTrade.id).label('total_trades'),
                    func.sum(CTPTrade.volume).label('total_trade_volume'),
                    func.sum(CTPTrade.price * CTPTrade.volume).label('total_turnover')
                )
                .where(
                    and_(
                        CTPTrade.user_id == user_id,
                        CTPTrade.created_at >= start_date,
                        CTPTrade.created_at <= end_date
                    )
                )
            )
            trade_result = trade_stats.first()
            
            return {
                'order_statistics': {
                    'total_orders': order_result.total_orders or 0,
                    'total_volume': float(order_result.total_volume or 0),
                    'filled_orders': order_result.filled_orders or 0
                },
                'trade_statistics': {
                    'total_trades': trade_result.total_trades or 0,
                    'total_trade_volume': float(trade_result.total_trade_volume or 0),
                    'total_turnover': float(trade_result.total_turnover or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Get aggregated statistics failed: {e}")
            raise
    
    def get_query_performance_report(self) -> Dict[str, Any]:
        """获取查询性能报告"""
        if not self.query_metrics:
            return {"message": "No query metrics available"}
        
        # 按查询类型分组统计
        type_stats = {}
        for metric in self.query_metrics:
            query_type = metric.query_type.value
            if query_type not in type_stats:
                type_stats[query_type] = {
                    'count': 0,
                    'total_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                    'total_rows': 0
                }
            
            stats = type_stats[query_type]
            stats['count'] += 1
            stats['total_time'] += metric.execution_time
            stats['max_time'] = max(stats['max_time'], metric.execution_time)
            stats['min_time'] = min(stats['min_time'], metric.execution_time)
            stats['total_rows'] += metric.rows_affected
        
        # 计算平均值
        for stats in type_stats.values():
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['avg_rows'] = stats['total_rows'] / stats['count']
            if stats['min_time'] == float('inf'):
                stats['min_time'] = 0
        
        # 慢查询统计
        slow_queries = [
            m for m in self.query_metrics 
            if m.execution_time > self.slow_query_threshold
        ]
        
        return {
            'total_queries': len(self.query_metrics),
            'slow_queries_count': len(slow_queries),
            'slow_query_threshold': self.slow_query_threshold,
            'query_type_statistics': type_stats,
            'recent_slow_queries': [
                {
                    'query_hash': q.query_hash,
                    'execution_time': q.execution_time,
                    'rows_affected': q.rows_affected,
                    'timestamp': q.timestamp.isoformat()
                }
                for q in sorted(slow_queries, key=lambda x: x.execution_time, reverse=True)[:10]
            ]
        }
    
    def clear_metrics(self):
        """清除查询指标"""
        self.query_metrics.clear()
        logger.info("Query metrics cleared")


class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self):
        self.engines = {}
        self.session_makers = {}
    
    def create_read_replica_engine(self, replica_url: str):
        """创建只读副本引擎"""
        engine = create_async_engine(
            replica_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )
        self.engines['read_replica'] = engine
        self.session_makers['read_replica'] = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        return engine
    
    @asynccontextmanager
    async def get_read_session(self):
        """获取只读会话"""
        if 'read_replica' in self.session_makers:
            async with self.session_makers['read_replica']() as session:
                yield session
        else:
            # 如果没有只读副本，使用主库
            async with get_db() as session:
                yield session
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        stats = {}
        
        for name, engine in self.engines.items():
            pool = engine.pool
            stats[name] = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
        
        return stats


# 全局实例
db_optimizer = DatabaseOptimizer()
connection_pool_manager = ConnectionPoolManager()
