"""
Prometheus指标暴露服务
"""
import asyncio
import time
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    start_http_server, REGISTRY
)
from prometheus_client.core import REGISTRY as DEFAULT_REGISTRY
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
import psutil
from loguru import logger

from ..core.config import settings
from .ctp_metrics import metrics_collector


class PrometheusExporter:
    """Prometheus指标导出器"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY
        self.metrics = {}
        self.info_metrics = {}
        self._setup_metrics()
        self._last_collection_time = 0
        self._collection_interval = 30  # 30秒收集一次
    
    def _setup_metrics(self):
        """设置Prometheus指标"""
        
        # 应用信息指标
        self.info_metrics['app_info'] = Info(
            'quant_platform_app_info',
            'Application information',
            registry=self.registry
        )
        
        # 系统指标
        self.metrics['cpu_usage'] = Gauge(
            'quant_platform_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.metrics['memory_usage'] = Gauge(
            'quant_platform_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.metrics['memory_total'] = Gauge(
            'quant_platform_memory_total_bytes',
            'Total memory in bytes',
            registry=self.registry
        )
        
        # CTP连接指标
        self.metrics['ctp_connection_status'] = Gauge(
            'quant_platform_ctp_connection_status',
            'CTP connection status (1=connected, 0=disconnected)',
            ['connection_type'],
            registry=self.registry
        )
        
        self.metrics['ctp_connection_uptime'] = Gauge(
            'quant_platform_ctp_connection_uptime_seconds',
            'CTP connection uptime in seconds',
            ['connection_type'],
            registry=self.registry
        )
        
        self.metrics['ctp_reconnect_count'] = Counter(
            'quant_platform_ctp_reconnect_total',
            'Total number of CTP reconnections',
            ['connection_type'],
            registry=self.registry
        )
        
        # 交易指标
        self.metrics['orders_total'] = Counter(
            'quant_platform_orders_total',
            'Total number of orders',
            ['status', 'side', 'order_type'],
            registry=self.registry
        )
        
        self.metrics['trades_total'] = Counter(
            'quant_platform_trades_total',
            'Total number of trades',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.metrics['trade_volume'] = Counter(
            'quant_platform_trade_volume_total',
            'Total trade volume',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.metrics['trade_amount'] = Counter(
            'quant_platform_trade_amount_total',
            'Total trade amount',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.metrics['order_response_time'] = Histogram(
            'quant_platform_order_response_time_seconds',
            'Order response time in seconds',
            ['order_type'],
            registry=self.registry
        )
        
        # 持仓指标
        self.metrics['positions_count'] = Gauge(
            'quant_platform_positions_count',
            'Number of open positions',
            ['direction'],
            registry=self.registry
        )
        
        self.metrics['portfolio_value'] = Gauge(
            'quant_platform_portfolio_value',
            'Total portfolio value',
            registry=self.registry
        )
        
        self.metrics['unrealized_pnl'] = Gauge(
            'quant_platform_unrealized_pnl',
            'Unrealized profit and loss',
            registry=self.registry
        )
        
        # 行情数据指标
        self.metrics['market_data_received'] = Counter(
            'quant_platform_market_data_received_total',
            'Total market data messages received',
            ['symbol', 'data_type'],
            registry=self.registry
        )
        
        self.metrics['market_data_latency'] = Histogram(
            'quant_platform_market_data_latency_seconds',
            'Market data latency in seconds',
            ['symbol'],
            registry=self.registry
        )
        
        self.metrics['subscriptions_count'] = Gauge(
            'quant_platform_subscriptions_count',
            'Number of active subscriptions',
            ['data_type'],
            registry=self.registry
        )
        
        # 策略指标
        self.metrics['strategies_count'] = Gauge(
            'quant_platform_strategies_count',
            'Number of active strategies',
            ['status'],
            registry=self.registry
        )
        
        self.metrics['strategy_signals'] = Counter(
            'quant_platform_strategy_signals_total',
            'Total strategy signals generated',
            ['strategy_id', 'signal_type'],
            registry=self.registry
        )
        
        # HTTP请求指标
        self.metrics['http_requests_total'] = Counter(
            'quant_platform_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.metrics['http_request_duration'] = Histogram(
            'quant_platform_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # WebSocket指标
        self.metrics['websocket_connections'] = Gauge(
            'quant_platform_websocket_connections',
            'Number of active WebSocket connections',
            ['connection_type'],
            registry=self.registry
        )
        
        self.metrics['websocket_messages'] = Counter(
            'quant_platform_websocket_messages_total',
            'Total WebSocket messages',
            ['direction', 'message_type'],
            registry=self.registry
        )
        
        # 错误指标
        self.metrics['errors_total'] = Counter(
            'quant_platform_errors_total',
            'Total number of errors',
            ['component', 'error_type'],
            registry=self.registry
        )
        
        # 设置应用信息
        self.info_metrics['app_info'].info({
            'version': getattr(settings, 'VERSION', '1.0.0'),
            'environment': getattr(settings, 'ENVIRONMENT', 'development'),
            'service': 'quant-platform-backend'
        })
    
    async def collect_and_update_metrics(self):
        """收集并更新指标"""
        current_time = time.time()
        
        # 检查是否需要收集
        if current_time - self._last_collection_time < self._collection_interval:
            return
        
        try:
            # 收集系统指标
            await self._collect_system_metrics()
            
            # 收集CTP指标
            await self._collect_ctp_metrics()
            
            # 收集交易指标
            await self._collect_trading_metrics()
            
            self._last_collection_time = current_time
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            self.metrics['errors_total'].labels(
                component='metrics_collector',
                error_type='collection_error'
            ).inc()
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics['cpu_usage'].set(cpu_percent)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        self.metrics['memory_usage'].set(memory.used)
        self.metrics['memory_total'].set(memory.total)
    
    async def _collect_ctp_metrics(self):
        """收集CTP指标"""
        try:
            # 从CTP指标收集器获取数据
            ctp_metrics = await metrics_collector.get_metrics_summary()
            
            # 连接状态
            connection_status = ctp_metrics.get('connection_status', {})
            for conn_type, status in connection_status.items():
                self.metrics['ctp_connection_status'].labels(
                    connection_type=conn_type
                ).set(1 if status else 0)
            
            # 连接运行时间
            connection_uptime = ctp_metrics.get('connection_uptime', {})
            for conn_type, uptime in connection_uptime.items():
                self.metrics['ctp_connection_uptime'].labels(
                    connection_type=conn_type
                ).set(uptime)
            
        except Exception as e:
            logger.error(f"Error collecting CTP metrics: {e}")
    
    async def _collect_trading_metrics(self):
        """收集交易指标"""
        try:
            # 从数据库或缓存获取交易统计数据
            # 这里需要根据实际的数据源进行调整
            pass
            
        except Exception as e:
            logger.error(f"Error collecting trading metrics: {e}")
    
    def record_order(self, status: str, side: str, order_type: str):
        """记录订单指标"""
        self.metrics['orders_total'].labels(
            status=status,
            side=side,
            order_type=order_type
        ).inc()
    
    def record_trade(self, symbol: str, side: str, volume: float, amount: float):
        """记录成交指标"""
        self.metrics['trades_total'].labels(
            symbol=symbol,
            side=side
        ).inc()
        
        self.metrics['trade_volume'].labels(
            symbol=symbol,
            side=side
        ).inc(volume)
        
        self.metrics['trade_amount'].labels(
            symbol=symbol,
            side=side
        ).inc(amount)
    
    def record_order_response_time(self, order_type: str, duration: float):
        """记录订单响应时间"""
        self.metrics['order_response_time'].labels(
            order_type=order_type
        ).observe(duration)
    
    def record_market_data(self, symbol: str, data_type: str, latency: float = None):
        """记录行情数据指标"""
        self.metrics['market_data_received'].labels(
            symbol=symbol,
            data_type=data_type
        ).inc()
        
        if latency is not None:
            self.metrics['market_data_latency'].labels(
                symbol=symbol
            ).observe(latency)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录HTTP请求指标"""
        self.metrics['http_requests_total'].labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        self.metrics['http_request_duration'].labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_websocket_connection(self, connection_type: str, delta: int):
        """记录WebSocket连接变化"""
        current = self.metrics['websocket_connections'].labels(
            connection_type=connection_type
        )._value._value
        self.metrics['websocket_connections'].labels(
            connection_type=connection_type
        ).set(max(0, current + delta))
    
    def record_websocket_message(self, direction: str, message_type: str):
        """记录WebSocket消息"""
        self.metrics['websocket_messages'].labels(
            direction=direction,
            message_type=message_type
        ).inc()
    
    def record_error(self, component: str, error_type: str):
        """记录错误"""
        self.metrics['errors_total'].labels(
            component=component,
            error_type=error_type
        ).inc()
    
    async def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        # 更新指标
        await self.collect_and_update_metrics()
        
        # 生成Prometheus格式
        return generate_latest(self.registry)


# 全局指标导出器实例
prometheus_exporter = PrometheusExporter()


def setup_prometheus_metrics(app: FastAPI):
    """设置Prometheus指标端点"""
    
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Prometheus指标端点"""
        metrics_data = await prometheus_exporter.get_metrics()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    
    logger.info("Prometheus metrics endpoint configured at /metrics")


def start_metrics_server(port: int = 9090):
    """启动独立的指标服务器"""
    try:
        start_http_server(port, registry=prometheus_exporter.registry)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
        raise


async def start_background_collection():
    """启动后台指标收集"""
    while True:
        try:
            await prometheus_exporter.collect_and_update_metrics()
            await asyncio.sleep(30)  # 每30秒收集一次
        except Exception as e:
            logger.error(f"Error in background metrics collection: {e}")
            await asyncio.sleep(60)  # 错误后等待1分钟
