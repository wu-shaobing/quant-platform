"""
监控中间件
"""
import time
import asyncio
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from loguru import logger

from .prometheus_exporter import prometheus_exporter
from ..core.logging_config import log_system_event


class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 检查是否需要排除
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算响应时间
            duration = time.time() - start_time
            
            # 记录指标
            prometheus_exporter.record_http_request(
                method=request.method,
                endpoint=self._get_endpoint_pattern(request),
                status_code=response.status_code,
                duration=duration
            )
            
            # 记录日志
            log_system_event(
                component="http_api",
                event_type="request_completed",
                data={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "user_agent": request.headers.get("user-agent", ""),
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            return response
            
        except Exception as e:
            # 计算响应时间
            duration = time.time() - start_time
            
            # 记录错误指标
            prometheus_exporter.record_http_request(
                method=request.method,
                endpoint=self._get_endpoint_pattern(request),
                status_code=500,
                duration=duration
            )
            
            prometheus_exporter.record_error(
                component="http_api",
                error_type=type(e).__name__
            )
            
            # 记录错误日志
            log_system_event(
                component="http_api",
                event_type="request_error",
                data={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                    "client_ip": self._get_client_ip(request)
                },
                level="ERROR"
            )
            
            raise
    
    def _get_endpoint_pattern(self, request: Request) -> str:
        """获取端点模式"""
        # 尝试从路由获取模式
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path
        
        # 简化路径模式
        path = request.url.path
        
        # 替换数字ID为占位符
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', path)  # UUID
        
        return path
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 从连接信息获取
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class WebSocketMetricsMiddleware:
    """WebSocket指标收集中间件"""
    
    def __init__(self):
        self.active_connections: Dict[str, int] = {}
    
    async def connect(self, websocket, connection_type: str = "general"):
        """WebSocket连接建立"""
        prometheus_exporter.record_websocket_connection(connection_type, 1)
        
        # 更新活跃连接计数
        if connection_type not in self.active_connections:
            self.active_connections[connection_type] = 0
        self.active_connections[connection_type] += 1
        
        log_system_event(
            component="websocket",
            event_type="connection_established",
            data={
                "connection_type": connection_type,
                "active_connections": self.active_connections[connection_type],
                "client_ip": self._get_websocket_client_ip(websocket)
            }
        )
    
    async def disconnect(self, websocket, connection_type: str = "general"):
        """WebSocket连接断开"""
        prometheus_exporter.record_websocket_connection(connection_type, -1)
        
        # 更新活跃连接计数
        if connection_type in self.active_connections:
            self.active_connections[connection_type] = max(0, self.active_connections[connection_type] - 1)
        
        log_system_event(
            component="websocket",
            event_type="connection_closed",
            data={
                "connection_type": connection_type,
                "active_connections": self.active_connections.get(connection_type, 0),
                "client_ip": self._get_websocket_client_ip(websocket)
            }
        )
    
    async def message_sent(self, message_type: str, data_size: int = 0):
        """记录发送的消息"""
        prometheus_exporter.record_websocket_message("outbound", message_type)
        
        log_system_event(
            component="websocket",
            event_type="message_sent",
            data={
                "message_type": message_type,
                "data_size": data_size
            }
        )
    
    async def message_received(self, message_type: str, data_size: int = 0):
        """记录接收的消息"""
        prometheus_exporter.record_websocket_message("inbound", message_type)
        
        log_system_event(
            component="websocket",
            event_type="message_received",
            data={
                "message_type": message_type,
                "data_size": data_size
            }
        )
    
    def _get_websocket_client_ip(self, websocket) -> str:
        """获取WebSocket客户端IP"""
        try:
            if hasattr(websocket, "client") and websocket.client:
                return websocket.client.host
            return "unknown"
        except:
            return "unknown"


class TradingMetricsCollector:
    """交易指标收集器"""
    
    @staticmethod
    async def record_order_submitted(order_data: Dict[str, Any]):
        """记录订单提交"""
        prometheus_exporter.record_order(
            status="submitted",
            side=order_data.get("side", "unknown"),
            order_type=order_data.get("order_type", "unknown")
        )
        
        from ..core.logging_config import log_trading_event
        log_trading_event(
            event_type="order_submitted",
            data=order_data
        )
    
    @staticmethod
    async def record_order_filled(order_data: Dict[str, Any], trade_data: Dict[str, Any]):
        """记录订单成交"""
        prometheus_exporter.record_order(
            status="filled",
            side=order_data.get("side", "unknown"),
            order_type=order_data.get("order_type", "unknown")
        )
        
        prometheus_exporter.record_trade(
            symbol=trade_data.get("symbol", "unknown"),
            side=trade_data.get("side", "unknown"),
            volume=float(trade_data.get("volume", 0)),
            amount=float(trade_data.get("amount", 0))
        )
        
        from ..core.logging_config import log_trading_event
        log_trading_event(
            event_type="order_filled",
            data={**order_data, **trade_data}
        )
    
    @staticmethod
    async def record_order_rejected(order_data: Dict[str, Any], reason: str):
        """记录订单拒绝"""
        prometheus_exporter.record_order(
            status="rejected",
            side=order_data.get("side", "unknown"),
            order_type=order_data.get("order_type", "unknown")
        )
        
        prometheus_exporter.record_error(
            component="trading",
            error_type="order_rejected"
        )
        
        from ..core.logging_config import log_trading_event
        log_trading_event(
            event_type="order_rejected",
            data={**order_data, "rejection_reason": reason},
            level="WARNING"
        )
    
    @staticmethod
    async def record_order_response_time(order_type: str, start_time: float):
        """记录订单响应时间"""
        duration = time.time() - start_time
        prometheus_exporter.record_order_response_time(order_type, duration)


class MarketDataMetricsCollector:
    """行情数据指标收集器"""
    
    @staticmethod
    async def record_market_data_received(symbol: str, data_type: str, timestamp: float = None):
        """记录行情数据接收"""
        latency = None
        if timestamp:
            latency = time.time() - timestamp
        
        prometheus_exporter.record_market_data(symbol, data_type, latency)
        
        from ..core.logging_config import log_market_data_event
        log_market_data_event(
            symbol=symbol,
            event_type="data_received",
            data={
                "data_type": data_type,
                "latency": latency,
                "timestamp": timestamp
            }
        )
    
    @staticmethod
    async def record_subscription_change(data_type: str, delta: int):
        """记录订阅变化"""
        # 这里需要实现订阅计数逻辑
        pass


# 全局中间件实例
websocket_metrics = WebSocketMetricsMiddleware()
trading_metrics = TradingMetricsCollector()
market_data_metrics = MarketDataMetricsCollector()


def setup_monitoring_middleware(app):
    """设置监控中间件"""
    # 添加HTTP指标中间件
    app.add_middleware(MetricsMiddleware)
    
    logger.info("Monitoring middleware configured")
