"""
CTP监控指标收集
"""
import time
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
import psutil
import threading

logger = logging.getLogger(__name__)


@dataclass
class CTPMetrics:
    """CTP指标数据类"""
    
    # 连接指标
    connection_status: Dict[str, bool] = field(default_factory=dict)
    connection_uptime: Dict[str, float] = field(default_factory=dict)
    connection_errors: Dict[str, int] = field(default_factory=dict)
    reconnection_count: Dict[str, int] = field(default_factory=dict)
    
    # 交易指标
    order_count: int = 0
    order_success_count: int = 0
    order_error_count: int = 0
    trade_count: int = 0
    cancel_count: int = 0
    cancel_success_count: int = 0
    
    # 行情指标
    tick_count: int = 0
    subscribe_count: int = 0
    market_data_delay: float = 0.0
    
    # 性能指标
    response_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    # 错误指标
    error_counts: Dict[str, int] = field(default_factory=dict)
    last_errors: Dict[str, str] = field(default_factory=dict)
    
    # 时间戳
    last_update: datetime = field(default_factory=datetime.now)


class PrometheusMetrics:
    """Prometheus指标定义"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if PrometheusMetrics._initialized:
            return

        # 连接指标
        self.connection_status = Gauge(
            'ctp_connection_status',
            'CTP connection status (1=connected, 0=disconnected)',
            ['connection_type', 'broker_id']
        )
        
        self.connection_uptime = Gauge(
            'ctp_connection_uptime_seconds',
            'CTP connection uptime in seconds',
            ['connection_type', 'broker_id']
        )
        
        self.reconnection_total = Counter(
            'ctp_reconnection_total',
            'Total number of CTP reconnections',
            ['connection_type', 'broker_id']
        )
        
        # 交易指标
        self.orders_total = Counter(
            'ctp_orders_total',
            'Total number of orders submitted',
            ['broker_id', 'status']
        )
        
        self.trades_total = Counter(
            'ctp_trades_total',
            'Total number of trades executed',
            ['broker_id', 'instrument']
        )
        
        self.order_response_time = Histogram(
            'ctp_order_response_time_seconds',
            'Order response time in seconds',
            ['broker_id', 'order_type']
        )
        
        # 行情指标
        self.market_data_total = Counter(
            'ctp_market_data_total',
            'Total number of market data ticks received',
            ['broker_id', 'instrument']
        )
        
        self.market_data_delay = Histogram(
            'ctp_market_data_delay_seconds',
            'Market data delay in seconds',
            ['broker_id', 'instrument']
        )
        
        self.subscriptions_active = Gauge(
            'ctp_subscriptions_active',
            'Number of active market data subscriptions',
            ['broker_id']
        )
        
        # 错误指标
        self.errors_total = Counter(
            'ctp_errors_total',
            'Total number of CTP errors',
            ['broker_id', 'error_type', 'error_code']
        )
        
        # 性能指标
        self.memory_usage = Gauge(
            'ctp_memory_usage_bytes',
            'CTP service memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'ctp_cpu_usage_percent',
            'CTP service CPU usage percentage'
        )
        
        # 系统信息
        self.info = Info(
            'ctp_service_info',
            'CTP service information'
        )

        # 标记为已初始化
        PrometheusMetrics._initialized = True


class CTPMetricsCollector:
    """CTP指标收集器"""
    
    def __init__(self, metrics_port: int = 9090):
        self.metrics = CTPMetrics()
        self.prometheus_metrics = PrometheusMetrics()
        self.metrics_port = metrics_port
        self.collection_interval = 30  # 30秒收集一次
        self.running = False
        self._lock = asyncio.Lock()
        self._collection_task = None
        
        # 响应时间窗口（保留最近100个样本）
        self.response_time_window = 100
        
        # 启动Prometheus HTTP服务器
        self._start_prometheus_server()
    
    def _start_prometheus_server(self):
        """启动Prometheus HTTP服务器"""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Prometheus metrics server started on port {self.metrics_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    async def start_collection(self):
        """开始指标收集"""
        if self.running:
            return
        
        self.running = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("CTP metrics collection started")
    
    async def stop_collection(self):
        """停止指标收集"""
        self.running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("CTP metrics collection stopped")
    
    async def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await self._update_prometheus_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            process = psutil.Process()
            memory_info = process.memory_info()
            
            async with self._lock:
                self.metrics.cpu_usage = cpu_percent
                self.metrics.memory_usage = memory_info.rss
                self.metrics.last_update = datetime.now()
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _update_prometheus_metrics(self):
        """更新Prometheus指标"""
        try:
            async with self._lock:
                # 更新系统指标
                self.prometheus_metrics.cpu_usage.set(self.metrics.cpu_usage)
                self.prometheus_metrics.memory_usage.set(self.metrics.memory_usage)
                
                # 更新连接状态
                for conn_type, status in self.metrics.connection_status.items():
                    broker_id = "default"  # 可以从配置中获取
                    self.prometheus_metrics.connection_status.labels(
                        connection_type=conn_type,
                        broker_id=broker_id
                    ).set(1 if status else 0)
                
                # 更新连接运行时间
                for conn_type, uptime in self.metrics.connection_uptime.items():
                    broker_id = "default"
                    self.prometheus_metrics.connection_uptime.labels(
                        connection_type=conn_type,
                        broker_id=broker_id
                    ).set(uptime)
                
        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")
    
    # 连接指标记录方法
    async def record_connection_status(self, connection_type: str, status: bool, broker_id: str = "default"):
        """记录连接状态"""
        async with self._lock:
            self.metrics.connection_status[connection_type] = status
            
            # 更新Prometheus指标
            self.prometheus_metrics.connection_status.labels(
                connection_type=connection_type,
                broker_id=broker_id
            ).set(1 if status else 0)
    
    async def record_connection_uptime(self, connection_type: str, uptime: float, broker_id: str = "default"):
        """记录连接运行时间"""
        async with self._lock:
            self.metrics.connection_uptime[connection_type] = uptime
            
            # 更新Prometheus指标
            self.prometheus_metrics.connection_uptime.labels(
                connection_type=connection_type,
                broker_id=broker_id
            ).set(uptime)
    
    async def record_reconnection(self, connection_type: str, broker_id: str = "default"):
        """记录重连事件"""
        async with self._lock:
            self.metrics.reconnection_count[connection_type] = \
                self.metrics.reconnection_count.get(connection_type, 0) + 1
            
            # 更新Prometheus指标
            self.prometheus_metrics.reconnection_total.labels(
                connection_type=connection_type,
                broker_id=broker_id
            ).inc()
    
    # 交易指标记录方法
    async def record_order(self, status: str, response_time: float = None, 
                          broker_id: str = "default", order_type: str = "limit"):
        """记录订单"""
        async with self._lock:
            self.metrics.order_count += 1
            
            if status == "success":
                self.metrics.order_success_count += 1
            else:
                self.metrics.order_error_count += 1
            
            # 记录响应时间
            if response_time is not None:
                response_times = self.metrics.response_times["order"]
                response_times.append(response_time)
                if len(response_times) > self.response_time_window:
                    response_times.pop(0)
                
                # 更新Prometheus指标
                self.prometheus_metrics.order_response_time.labels(
                    broker_id=broker_id,
                    order_type=order_type
                ).observe(response_time)
            
            # 更新Prometheus指标
            self.prometheus_metrics.orders_total.labels(
                broker_id=broker_id,
                status=status
            ).inc()
    
    async def record_trade(self, instrument: str, broker_id: str = "default"):
        """记录成交"""
        async with self._lock:
            self.metrics.trade_count += 1
            
            # 更新Prometheus指标
            self.prometheus_metrics.trades_total.labels(
                broker_id=broker_id,
                instrument=instrument
            ).inc()
    
    async def record_cancel(self, success: bool, broker_id: str = "default"):
        """记录撤单"""
        async with self._lock:
            self.metrics.cancel_count += 1
            if success:
                self.metrics.cancel_success_count += 1
    
    # 行情指标记录方法
    async def record_market_data(self, instrument: str, delay: float = None, 
                                broker_id: str = "default"):
        """记录行情数据"""
        async with self._lock:
            self.metrics.tick_count += 1
            
            if delay is not None:
                self.metrics.market_data_delay = delay
                
                # 更新Prometheus指标
                self.prometheus_metrics.market_data_delay.labels(
                    broker_id=broker_id,
                    instrument=instrument
                ).observe(delay)
            
            # 更新Prometheus指标
            self.prometheus_metrics.market_data_total.labels(
                broker_id=broker_id,
                instrument=instrument
            ).inc()
    
    async def record_subscription_count(self, count: int, broker_id: str = "default"):
        """记录订阅数量"""
        async with self._lock:
            self.metrics.subscribe_count = count
            
            # 更新Prometheus指标
            self.prometheus_metrics.subscriptions_active.labels(
                broker_id=broker_id
            ).set(count)
    
    # 错误指标记录方法
    async def record_error(self, error_type: str, error_code: str, error_msg: str, 
                          broker_id: str = "default"):
        """记录错误"""
        async with self._lock:
            self.metrics.error_counts[error_type] = \
                self.metrics.error_counts.get(error_type, 0) + 1
            self.metrics.last_errors[error_type] = error_msg
            
            # 更新Prometheus指标
            self.prometheus_metrics.errors_total.labels(
                broker_id=broker_id,
                error_type=error_type,
                error_code=error_code
            ).inc()
    
    # 查询方法
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        async with self._lock:
            return {
                "connection_status": dict(self.metrics.connection_status),
                "connection_uptime": dict(self.metrics.connection_uptime),
                "order_stats": {
                    "total": self.metrics.order_count,
                    "success": self.metrics.order_success_count,
                    "error": self.metrics.order_error_count,
                    "success_rate": (
                        self.metrics.order_success_count / self.metrics.order_count
                        if self.metrics.order_count > 0 else 0
                    )
                },
                "trade_count": self.metrics.trade_count,
                "market_data": {
                    "tick_count": self.metrics.tick_count,
                    "subscribe_count": self.metrics.subscribe_count,
                    "delay": self.metrics.market_data_delay
                },
                "system": {
                    "cpu_usage": self.metrics.cpu_usage,
                    "memory_usage": self.metrics.memory_usage
                },
                "errors": dict(self.metrics.error_counts),
                "last_update": self.metrics.last_update.isoformat()
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        async with self._lock:
            # 检查连接状态
            all_connected = all(self.metrics.connection_status.values())
            
            # 检查错误率
            total_orders = self.metrics.order_count
            error_rate = (
                self.metrics.order_error_count / total_orders
                if total_orders > 0 else 0
            )
            
            # 检查最近更新时间
            time_since_update = (datetime.now() - self.metrics.last_update).total_seconds()
            
            # 确定健康状态
            if not all_connected:
                status = "unhealthy"
                reason = "Connection issues detected"
            elif error_rate > 0.1:  # 错误率超过10%
                status = "degraded"
                reason = f"High error rate: {error_rate:.2%}"
            elif time_since_update > 300:  # 5分钟没有更新
                status = "stale"
                reason = "Metrics not updated recently"
            else:
                status = "healthy"
                reason = "All systems operational"
            
            return {
                "status": status,
                "reason": reason,
                "connections": dict(self.metrics.connection_status),
                "error_rate": error_rate,
                "last_update": self.metrics.last_update.isoformat(),
                "uptime": dict(self.metrics.connection_uptime)
            }


# 全局指标收集器实例
metrics_collector = CTPMetricsCollector()
