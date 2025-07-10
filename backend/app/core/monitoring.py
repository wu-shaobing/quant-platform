"""
监控和指标收集模块
提供应用性能监控、健康检查、指标收集等功能
"""
import time
import psutil
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from functools import wraps

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """指标数据"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    unit: str = ""
    description: str = ""


@dataclass
class HealthStatus:
    """健康状态"""
    component: str
    status: str  # healthy, unhealthy, degraded
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
    def counter_inc(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """增加计数器"""
        key = self._make_key(name, labels)
        self.counters[key] += value
        self._record_metric(name, self.counters[key], labels, "counter")
    
    def gauge_set(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        self._record_metric(name, value, labels, "gauge")
    
    def histogram_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图观测值"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        # 保持最近1000个值
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        self._record_metric(name, value, labels, "histogram")
    
    def timer_record(self, name: str, duration: float, labels: Dict[str, str] = None):
        """记录计时器"""
        key = self._make_key(name, labels)
        self.timers[key].append(duration)
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]
        self._record_metric(name, duration, labels, "timer")
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指标键"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{label_str}}"
        return name
    
    def _record_metric(self, name: str, value: float, labels: Dict[str, str] = None, metric_type: str = ""):
        """记录指标"""
        metric = MetricData(
            name=name,
            value=value,
            labels=labels or {},
            timestamp=datetime.utcnow(),
            unit=self._get_unit(name),
            description=self._get_description(name)
        )
        self.metrics[name].append(metric)
    
    def _get_unit(self, name: str) -> str:
        """获取指标单位"""
        unit_mapping = {
            "duration": "seconds",
            "time": "seconds",
            "latency": "seconds",
            "memory": "bytes",
            "cpu": "percent",
            "disk": "bytes",
            "network": "bytes",
            "count": "count",
            "rate": "per_second",
        }
        
        for key, unit in unit_mapping.items():
            if key in name.lower():
                return unit
        return ""
    
    def _get_description(self, name: str) -> str:
        """获取指标描述"""
        descriptions = {
            "http_requests_total": "HTTP请求总数",
            "http_request_duration": "HTTP请求耗时",
            "http_request_size": "HTTP请求大小",
            "http_response_size": "HTTP响应大小",
            "database_connections": "数据库连接数",
            "database_query_duration": "数据库查询耗时",
            "memory_usage": "内存使用量",
            "cpu_usage": "CPU使用率",
            "disk_usage": "磁盘使用量",
            "websocket_connections": "WebSocket连接数",
            "trading_orders": "交易订单数",
            "market_data_updates": "行情数据更新数",
        }
        return descriptions.get(name, "")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        result = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {},
            "timers": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 计算直方图统计
        for name, values in self.histograms.items():
            if values:
                result["histograms"][name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                }
        
        # 计算计时器统计
        for name, values in self.timers.items():
            if values:
                result["timers"][name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "p50": self._percentile(values, 50),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                }
        
        return result
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()

    # 新增: 生命周期钩子
    async def initialize(self):
        """初始化指标收集器（占位，可扩展）"""
        # 这里可以启动后台任务，例如定期推送指标到Prometheus
        logger.debug("MetricsCollector initialized")

    async def cleanup(self):
        """清理资源"""
        # 关闭后台任务并清理资源
        logger.debug("MetricsCollector cleaned up")


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.status_history: deque = deque(maxlen=100)
    
    def register_check(self, name: str, check_func: Callable):
        """注册健康检查"""
        self.checks[name] = check_func
    
    async def check_health(self) -> Dict[str, HealthStatus]:
        """执行所有健康检查"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    status = await check_func()
                else:
                    status = check_func()
                
                if isinstance(status, bool):
                    status = HealthStatus(
                        component=name,
                        status="healthy" if status else "unhealthy",
                        message="OK" if status else "Check failed",
                        timestamp=datetime.utcnow()
                    )
                
                results[name] = status
                
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = HealthStatus(
                    component=name,
                    status="unhealthy",
                    message=str(e),
                    timestamp=datetime.utcnow(),
                    details={"error": str(e)}
                )
        
        # 记录状态历史
        overall_status = "healthy" if all(
            status.status == "healthy" for status in results.values()
        ) else "unhealthy"
        
        self.status_history.append({
            "timestamp": datetime.utcnow(),
            "status": overall_status,
            "details": {name: status.status for name, status in results.items()}
        })
        
        return results
    
    def get_status_history(self) -> List[Dict[str, Any]]:
        """获取状态历史"""
        return list(self.status_history)


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self._monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval: int = 60):
        """开始系统监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        """停止系统监控"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.gauge_set("system_cpu_usage_percent", cpu_percent)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        self.metrics.gauge_set("system_memory_usage_bytes", memory.used)
        self.metrics.gauge_set("system_memory_total_bytes", memory.total)
        self.metrics.gauge_set("system_memory_usage_percent", memory.percent)
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        self.metrics.gauge_set("system_disk_usage_bytes", disk.used)
        self.metrics.gauge_set("system_disk_total_bytes", disk.total)
        self.metrics.gauge_set("system_disk_usage_percent", disk.used / disk.total * 100)
        
        # 网络IO
        network = psutil.net_io_counters()
        self.metrics.gauge_set("system_network_bytes_sent", network.bytes_sent)
        self.metrics.gauge_set("system_network_bytes_recv", network.bytes_recv)
        
        # 进程信息
        process = psutil.Process()
        self.metrics.gauge_set("process_cpu_percent", process.cpu_percent())
        self.metrics.gauge_set("process_memory_bytes", process.memory_info().rss)
        self.metrics.gauge_set("process_threads", process.num_threads())


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics = metrics_collector
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并收集指标"""
        start_time = time.time()
        
        # 记录请求开始
        self.metrics.counter_inc("http_requests_total", labels={
            "method": request.method,
            "endpoint": str(request.url.path)
        })
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        duration = time.time() - start_time
        
        # 记录响应指标
        labels = {
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": str(response.status_code)
        }
        
        self.metrics.timer_record("http_request_duration_seconds", duration, labels)
        self.metrics.histogram_observe("http_request_duration_histogram", duration, labels)
        
        # 记录请求大小
        if hasattr(request, "content_length") and request.content_length:
            self.metrics.histogram_observe("http_request_size_bytes", request.content_length, labels)
        
        # 记录响应大小
        if hasattr(response, "content_length") and response.content_length:
            self.metrics.histogram_observe("http_response_size_bytes", response.content_length, labels)
        
        # 添加性能头
        response.headers["X-Process-Time"] = str(duration)
        
        return response


# 装饰器：性能计时
def monitor_performance(metric_name: str = None, labels: Dict[str, str] = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                final_labels = (labels or {}).copy()
                final_labels["status"] = status
                
                metrics_collector.timer_record(f"{name}_duration", duration, final_labels)
                metrics_collector.counter_inc(f"{name}_calls", labels=final_labels)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                final_labels = (labels or {}).copy()
                final_labels["status"] = status
                
                metrics_collector.timer_record(f"{name}_duration", duration, final_labels)
                metrics_collector.counter_inc(f"{name}_calls", labels=final_labels)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 上下文管理器：性能计时
@asynccontextmanager
async def monitor_duration(name: str, labels: Dict[str, str] = None):
    """监控代码块执行时间"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics_collector.timer_record(name, duration, labels)


# 全局实例
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
system_monitor = SystemMonitor(metrics_collector)


# 注册基础健康检查
def check_memory_usage():
    """检查内存使用"""
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        return HealthStatus(
            component="memory",
            status="unhealthy",
            message=f"Memory usage too high: {memory.percent}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": memory.percent}
        )
    elif memory.percent > 80:
        return HealthStatus(
            component="memory",
            status="degraded",
            message=f"Memory usage high: {memory.percent}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": memory.percent}
        )
    else:
        return HealthStatus(
            component="memory",
            status="healthy",
            message=f"Memory usage normal: {memory.percent}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": memory.percent}
        )


def check_disk_usage():
    """检查磁盘使用"""
    disk = psutil.disk_usage('/')
    usage_percent = disk.used / disk.total * 100
    
    if usage_percent > 95:
        return HealthStatus(
            component="disk",
            status="unhealthy",
            message=f"Disk usage critical: {usage_percent:.1f}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": usage_percent}
        )
    elif usage_percent > 85:
        return HealthStatus(
            component="disk",
            status="degraded",
            message=f"Disk usage high: {usage_percent:.1f}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": usage_percent}
        )
    else:
        return HealthStatus(
            component="disk",
            status="healthy",
            message=f"Disk usage normal: {usage_percent:.1f}%",
            timestamp=datetime.utcnow(),
            details={"usage_percent": usage_percent}
        )


# 注册健康检查
health_checker.register_check("memory", check_memory_usage)
health_checker.register_check("disk", check_disk_usage) 