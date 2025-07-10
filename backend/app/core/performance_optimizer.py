"""
高频交易性能优化器
提供低延迟、高吞吐量的交易处理优化
"""
import asyncio
import time
import logging
import pickle
import zlib
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import psutil
import gc

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.cache import cache_manager, CTPCacheKeys
from app.core.database_optimizer import db_optimizer
from app.models.market import MarketData, KLineData
from app.models.trading import Order, Position
from app.models.ctp_models import CTPOrder, CTPTrade, CTPPosition

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_io: Dict[str, int] = field(default_factory=dict)
    disk_io: Dict[str, int] = field(default_factory=dict)
    active_connections: int = 0
    pending_orders: int = 0
    processed_orders_per_second: float = 0.0
    average_latency: float = 0.0
    error_rate: float = 0.0


class LatencyTracker:
    """延迟跟踪器"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.latencies = deque(maxlen=max_samples)
        self.lock = threading.Lock()
    
    def record_latency(self, latency: float):
        """记录延迟"""
        with self.lock:
            self.latencies.append(latency)
    
    def get_statistics(self) -> Dict[str, float]:
        """获取延迟统计"""
        with self.lock:
            if not self.latencies:
                return {
                    'count': 0,
                    'average': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }
            
            sorted_latencies = sorted(self.latencies)
            count = len(sorted_latencies)
            
            return {
                'count': count,
                'average': sum(sorted_latencies) / count,
                'min': sorted_latencies[0],
                'max': sorted_latencies[-1],
                'p50': sorted_latencies[int(count * 0.5)],
                'p95': sorted_latencies[int(count * 0.95)],
                'p99': sorted_latencies[int(count * 0.99)]
            }


class OrderProcessor:
    """高性能订单处理器"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 0.1):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.order_queue = Queue()
        self.batch_buffer = []
        self.last_flush_time = time.time()
        self.processing = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.latency_tracker = LatencyTracker()
    
    async def submit_order(self, order_data: Dict[str, Any]) -> str:
        """提交订单"""
        start_time = time.time()
        order_id = f"order_{int(time.time() * 1000000)}"
        
        # 添加时间戳
        order_data['submit_time'] = start_time
        order_data['order_id'] = order_id
        
        # 放入队列
        self.order_queue.put(order_data)
        
        # 如果队列满了或者超时，立即处理
        if (self.order_queue.qsize() >= self.batch_size or 
            time.time() - self.last_flush_time >= self.flush_interval):
            await self._process_batch()
        
        # 记录延迟
        latency = time.time() - start_time
        self.latency_tracker.record_latency(latency)
        
        return order_id
    
    async def _process_batch(self):
        """处理批次订单"""
        if self.processing:
            return
        
        self.processing = True
        try:
            # 从队列中取出订单
            batch = []
            while len(batch) < self.batch_size:
                try:
                    order = self.order_queue.get_nowait()
                    batch.append(order)
                except Empty:
                    break
            
            if batch:
                # 异步处理批次
                await self._execute_batch(batch)
                self.last_flush_time = time.time()
        
        finally:
            self.processing = False
    
    async def _execute_batch(self, batch: List[Dict[str, Any]]):
        """执行批次订单"""
        try:
            # 这里可以调用实际的CTP接口
            # 模拟处理时间
            await asyncio.sleep(0.001)
            
            # 缓存订单状态
            for order in batch:
                cache_key = CTPCacheKeys.order_status(order['order_id'])
                await cache_manager.set(
                    cache_key,
                    {
                        'status': 'submitted',
                        'submit_time': order['submit_time'],
                        'process_time': time.time()
                    },
                    expire=3600
                )
            
            logger.debug(f"Processed batch of {len(batch)} orders")
            
        except Exception as e:
            logger.error(f"Failed to execute order batch: {e}")
            # 处理失败的订单
            for order in batch:
                await self._handle_failed_order(order, str(e))
    
    async def _handle_failed_order(self, order: Dict[str, Any], error: str):
        """处理失败的订单"""
        cache_key = CTPCacheKeys.order_status(order['order_id'])
        await cache_manager.set(
            cache_key,
            {
                'status': 'failed',
                'error': error,
                'submit_time': order['submit_time'],
                'fail_time': time.time()
            },
            expire=3600
        )


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.gc_threshold = 0.8  # 内存使用率阈值
        self.last_gc_time = time.time()
        self.gc_interval = 60  # GC间隔（秒）
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': memory_percent,
            'available': psutil.virtual_memory().available / 1024 / 1024  # MB
        }
    
    async def optimize_memory(self):
        """优化内存使用"""
        memory_info = self.get_memory_usage()
        
        # 如果内存使用率过高，执行垃圾回收
        if (memory_info['percent'] > self.gc_threshold * 100 or
            time.time() - self.last_gc_time > self.gc_interval):
            
            # 强制垃圾回收
            collected = gc.collect()
            self.last_gc_time = time.time()
            
            logger.info(f"Memory optimization: collected {collected} objects")
            
            # 清理缓存中的过期数据
            await self._cleanup_expired_cache()
    
    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            # 清理过期的订单缓存
            if hasattr(cache_manager, 'redis_client') and cache_manager.redis_client:
                # 使用Redis SCAN命令查找过期键
                cursor = 0
                expired_count = 0

                while True:
                    cursor, keys = await cache_manager.redis_client.scan(
                        cursor, match="ctp:order:*", count=100
                    )

                    for key in keys:
                        ttl = await cache_manager.redis_client.ttl(key)
                        if ttl == -1:  # 没有过期时间设置
                            await cache_manager.redis_client.expire(key, 3600)  # 设置1小时过期
                        elif ttl == -2:  # 键不存在
                            expired_count += 1

                    if cursor == 0:
                        break

                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired cache entries")

        except Exception as e:
            logger.error(f"Failed to cleanup expired cache: {e}")


class NetworkOptimizer:
    """网络优化器"""
    
    def __init__(self):
        self.connection_pool_size = 50
        self.keep_alive_timeout = 30
        self.tcp_nodelay = True
        self.tcp_keepalive = True
    
    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络统计"""
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections()
        
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'active_connections': len([c for c in connections if c.status == 'ESTABLISHED']),
            'total_connections': len(connections)
        }
    
    async def optimize_connections(self):
        """优化网络连接"""
        # 这里可以实现连接池优化逻辑
        stats = self.get_network_stats()
        
        # 如果连接数过多，可以考虑清理空闲连接
        if stats['active_connections'] > self.connection_pool_size * 0.8:
            logger.warning(f"High connection count: {stats['active_connections']}")


class DatabaseQueryOptimizer:
    """数据库查询优化器"""

    def __init__(self):
        self.query_cache = {}
        self.query_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'avg_time': 0})
        self.batch_size = 1000

    async def get_latest_market_data_cached(
        self,
        session,
        symbol: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取最新市场数据（带缓存）"""
        cache_key = CTPCacheKeys.market_data_latest(symbol)

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            return cached_data

        # 从数据库查询
        start_time = time.time()
        try:
            query = select(MarketData).where(
                MarketData.symbol_code == symbol
            ).order_by(MarketData.timestamp.desc()).limit(limit)

            result = await session.execute(query)
            market_data = result.scalars().all()

            # 转换为字典格式
            data_list = [{
                'symbol_code': data.symbol_code,
                'last_price': float(data.last_price),
                'volume': data.volume,
                'turnover': float(data.turnover),
                'timestamp': data.timestamp.isoformat()
            } for data in market_data]

            # 缓存结果（30秒过期）
            await cache_manager.set(cache_key, data_list, expire=30)

            # 记录查询统计
            query_time = time.time() - start_time
            self._update_query_stats('get_latest_market_data', query_time)

            return data_list

        except Exception as e:
            logger.error(f"查询最新市场数据失败: {e}")
            return []

    async def get_user_orders_cached(
        self,
        session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取用户订单（带缓存）"""
        cache_key = CTPCacheKeys.user_orders(user_id)

        # 尝试从缓存获取
        cached_orders = await cache_manager.get(cache_key)
        if cached_orders:
            return cached_orders

        # 从数据库查询
        start_time = time.time()
        try:
            query = select(CTPOrder).where(
                and_(
                    CTPOrder.user_id == user_id,
                    CTPOrder.order_status.in_(['4', '1', '2'])  # 活跃状态
                )
            ).order_by(CTPOrder.insert_time.desc())

            result = await session.execute(query)
            orders = result.scalars().all()

            # 转换为字典格式
            orders_list = [{
                'order_ref': order.order_ref,
                'instrument_id': order.instrument_id,
                'direction': order.direction,
                'limit_price': float(order.limit_price),
                'volume_total_original': order.volume_total_original,
                'order_status': order.order_status,
                'insert_time': order.insert_time.isoformat() if order.insert_time else None
            } for order in orders]

            # 缓存结果（60秒过期）
            await cache_manager.set(cache_key, orders_list, expire=60)

            # 记录查询统计
            query_time = time.time() - start_time
            self._update_query_stats('get_user_orders', query_time)

            return orders_list

        except Exception as e:
            logger.error(f"查询用户订单失败: {e}")
            return []

    async def batch_insert_market_data(
        self,
        session,
        data_list: List[Dict[str, Any]]
    ):
        """批量插入市场数据"""
        if not data_list:
            return

        start_time = time.time()
        try:
            # 分批插入
            for i in range(0, len(data_list), self.batch_size):
                batch = data_list[i:i + self.batch_size]

                # 构建批量插入语句
                values = []
                for data in batch:
                    values.append(
                        f"('{data['symbol_code']}', {data['last_price']}, "
                        f"{data['volume']}, {data['turnover']}, "
                        f"{data['open_interest']}, '{data['timestamp']}', '{data['trading_date']}')"
                    )

                insert_sql = f"""
                    INSERT INTO market_data (
                        symbol_code, last_price, volume, turnover,
                        open_interest, timestamp, trading_date
                    ) VALUES {','.join(values)}
                """

                await session.execute(text(insert_sql))

            await session.commit()

            # 记录统计
            insert_time = time.time() - start_time
            self._update_query_stats('batch_insert_market_data', insert_time)

            logger.info(f"批量插入 {len(data_list)} 条市场数据，耗时 {insert_time:.3f}s")

        except Exception as e:
            await session.rollback()
            logger.error(f"批量插入市场数据失败: {e}")

    def _update_query_stats(self, query_name: str, duration: float):
        """更新查询统计"""
        stats = self.query_stats[query_name]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']

    def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计"""
        return dict(self.query_stats)


class AdvancedCacheManager:
    """高级缓存管理器"""

    def __init__(self):
        self.compression_enabled = True
        self.compression_threshold = 1024  # 1KB

    async def cache_with_compression(
        self,
        key: str,
        data: Any,
        expire: int = 300
    ):
        """带压缩的缓存"""
        try:
            import pickle
            import zlib

            # 序列化数据
            serialized_data = pickle.dumps(data)

            # 如果数据大于阈值，进行压缩
            if self.compression_enabled and len(serialized_data) > self.compression_threshold:
                compressed_data = zlib.compress(serialized_data)
                # 添加压缩标记
                final_data = b'COMPRESSED:' + compressed_data
            else:
                final_data = b'RAW:' + serialized_data

            await cache_manager.set(key, final_data, expire, serialize=False)

        except Exception as e:
            logger.error(f"压缩缓存失败: {e}")

    async def get_with_decompression(self, key: str) -> Any:
        """带解压的获取缓存"""
        try:
            import pickle
            import zlib

            data = await cache_manager.get(key, serialize=False)
            if not data:
                return None

            # 检查是否压缩
            if data.startswith(b'COMPRESSED:'):
                compressed_data = data[11:]  # 去掉标记
                decompressed_data = zlib.decompress(compressed_data)
                return pickle.loads(decompressed_data)
            elif data.startswith(b'RAW:'):
                raw_data = data[4:]  # 去掉标记
                return pickle.loads(raw_data)
            else:
                # 兼容旧格式
                return pickle.loads(data)

        except Exception as e:
            logger.error(f"解压缓存失败: {e}")
            return None


class PerformanceOptimizer:
    """性能优化器主类"""

    def __init__(self):
        self.order_processor = OrderProcessor()
        self.memory_optimizer = MemoryOptimizer()
        self.network_optimizer = NetworkOptimizer()
        self.db_optimizer = DatabaseQueryOptimizer()
        self.cache_optimizer = AdvancedCacheManager()
        self.metrics_history = deque(maxlen=1000)
        self.optimization_enabled = True
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """停止性能监控"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                # 收集性能指标
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 执行优化
                if self.optimization_enabled:
                    await self._perform_optimizations(metrics)
                
                # 等待下一次监控
                await asyncio.sleep(10)  # 每10秒监控一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        # CPU和内存使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = self.memory_optimizer.get_memory_usage()
        
        # 网络IO
        network_stats = self.network_optimizer.get_network_stats()
        
        # 磁盘IO
        disk_io = psutil.disk_io_counters()
        
        # 订单处理指标
        latency_stats = self.order_processor.latency_tracker.get_statistics()
        
        return PerformanceMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory_info['percent'],
            network_io={
                'bytes_sent': network_stats['bytes_sent'],
                'bytes_recv': network_stats['bytes_recv']
            },
            disk_io={
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            },
            active_connections=network_stats['active_connections'],
            pending_orders=self.order_processor.order_queue.qsize(),
            average_latency=latency_stats['average']
        )
    
    async def _perform_optimizations(self, metrics: PerformanceMetrics):
        """执行性能优化"""
        # 内存优化
        if metrics.memory_usage > 80:
            await self.memory_optimizer.optimize_memory()
        
        # 网络优化
        if metrics.active_connections > 100:
            await self.network_optimizer.optimize_connections()
        
        # 订单处理优化
        if metrics.pending_orders > 50:
            await self.order_processor._process_batch()
    
    async def submit_order(self, order_data: Dict[str, Any]) -> str:
        """提交订单（优化版本）"""
        return await self.order_processor.submit_order(order_data)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.metrics_history:
            return {"message": "No performance data available"}
        
        latest_metrics = self.metrics_history[-1]
        
        # 计算平均值
        avg_cpu = sum(m.cpu_usage for m in self.metrics_history) / len(self.metrics_history)
        avg_memory = sum(m.memory_usage for m in self.metrics_history) / len(self.metrics_history)
        avg_latency = sum(m.average_latency for m in self.metrics_history) / len(self.metrics_history)
        
        # 延迟统计
        latency_stats = self.order_processor.latency_tracker.get_statistics()
        
        return {
            'current_metrics': {
                'cpu_usage': latest_metrics.cpu_usage,
                'memory_usage': latest_metrics.memory_usage,
                'active_connections': latest_metrics.active_connections,
                'pending_orders': latest_metrics.pending_orders,
                'average_latency': latest_metrics.average_latency
            },
            'average_metrics': {
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory,
                'average_latency': avg_latency
            },
            'latency_statistics': latency_stats,
            'optimization_status': {
                'enabled': self.optimization_enabled,
                'monitoring_active': self.monitoring_task is not None
            }
        }
    
    async def optimize_database_queries(self, session: AsyncSession):
        """优化数据库查询"""
        try:
            # 创建优化索引
            await self._create_performance_indexes(session)

            # 更新表统计信息
            await self._update_table_statistics(session)

            logger.info("数据库查询优化完成")

        except Exception as e:
            logger.error(f"数据库查询优化失败: {e}")

    async def _create_performance_indexes(self, session: AsyncSession):
        """创建性能优化索引"""
        indexes = [
            # 市场数据复合索引
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_symbol_time_desc "
            "ON market_data(symbol_code, timestamp DESC)",

            # CTP订单状态索引
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ctp_orders_user_status_time "
            "ON ctp_orders(user_id, order_status, insert_time DESC)",

            # CTP持仓索引
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ctp_positions_user_instrument "
            "ON ctp_positions(user_id, instrument_id) WHERE position > 0",

            # K线数据索引
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kline_symbol_type_time "
            "ON kline_data(symbol_code, kline_type, timestamp DESC)",
        ]

        for index_sql in indexes:
            try:
                await session.execute(text(index_sql))
                logger.info(f"索引创建成功: {index_sql.split()[5]}")
            except Exception as e:
                logger.warning(f"索引创建失败: {e}")

        await session.commit()

    async def _update_table_statistics(self, session: AsyncSession):
        """更新表统计信息"""
        tables = ['market_data', 'ctp_orders', 'ctp_positions', 'kline_data']

        for table in tables:
            try:
                await session.execute(text(f"ANALYZE {table}"))
                logger.info(f"表统计信息更新完成: {table}")
            except Exception as e:
                logger.warning(f"表统计信息更新失败 {table}: {e}")

    async def warm_cache(self):
        """预热缓存"""
        try:
            # 预热常用的市场数据
            popular_symbols = ['rb2501', 'i2501', 'hc2501', 'j2501']  # 热门合约

            from app.core.database import get_db
            async for session in get_db():
                for symbol in popular_symbols:
                    await self.db_optimizer.get_latest_market_data_cached(
                        session, symbol, limit=50
                    )
                break  # 只需要一个session

            logger.info(f"缓存预热完成，预热了 {len(popular_symbols)} 个合约的数据")

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")

    async def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        try:
            # 获取查询统计
            query_stats = self.db_optimizer.get_query_statistics()

            # 获取缓存统计
            cache_stats = await cache_manager.get_stats() if hasattr(cache_manager, 'get_stats') else {}

            # 获取性能指标
            performance_report = self.get_performance_report()

            # 获取内存使用情况
            memory_info = self.memory_optimizer.get_memory_usage()

            # 获取网络统计
            network_stats = self.network_optimizer.get_network_stats()

            return {
                'timestamp': datetime.now().isoformat(),
                'database_optimization': {
                    'query_statistics': query_stats,
                    'total_queries': sum(stats['count'] for stats in query_stats.values()),
                    'average_query_time': sum(stats['avg_time'] for stats in query_stats.values()) / len(query_stats) if query_stats else 0
                },
                'cache_optimization': {
                    'cache_statistics': cache_stats,
                    'compression_enabled': self.cache_optimizer.compression_enabled
                },
                'performance_metrics': performance_report,
                'system_resources': {
                    'memory': memory_info,
                    'network': network_stats
                },
                'optimization_status': {
                    'enabled': self.optimization_enabled,
                    'monitoring_active': self.monitoring_task is not None
                }
            }

        except Exception as e:
            logger.error(f"获取优化报告失败: {e}")
            return {'error': str(e)}

    def enable_optimization(self):
        """启用优化"""
        self.optimization_enabled = True
        logger.info("Performance optimization enabled")

    def disable_optimization(self):
        """禁用优化"""
        self.optimization_enabled = False
        logger.info("Performance optimization disabled")


# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()
