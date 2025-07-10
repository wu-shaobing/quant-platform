"""
CTP性能优化配置
定义性能优化相关的配置参数和策略
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class OptimizationLevel(str, Enum):
    """优化级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class CacheStrategy(str, Enum):
    """缓存策略"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


@dataclass
class DatabaseOptimizationConfig:
    """数据库优化配置"""
    # 连接池配置
    pool_size: int = 50
    max_overflow: int = 100
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # 查询优化
    query_cache_size: int = 1000
    query_timeout: int = 30
    batch_size: int = 1000
    max_concurrent_queries: int = 10
    
    # 索引优化
    enable_concurrent_index: bool = True
    auto_analyze: bool = True
    analyze_threshold: int = 1000
    
    # 分区配置
    enable_partitioning: bool = True
    partition_by_date: bool = True
    partition_retention_days: int = 90


@dataclass
class CacheOptimizationConfig:
    """缓存优化配置"""
    # Redis配置
    redis_pool_size: int = 100
    redis_timeout: int = 5
    redis_retry_attempts: int = 3
    
    # 缓存策略
    cache_strategy: CacheStrategy = CacheStrategy.ADAPTIVE
    default_ttl: int = 300
    max_memory_usage: int = 1024  # MB
    
    # 压缩配置
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    compression_level: int = 6
    
    # 预热配置
    enable_cache_warming: bool = True
    warm_popular_symbols: List[str] = None
    warm_data_limit: int = 100
    
    def __post_init__(self):
        if self.warm_popular_symbols is None:
            self.warm_popular_symbols = [
                'rb2501', 'i2501', 'hc2501', 'j2501', 'ag2412', 'au2412'
            ]


@dataclass
class NetworkOptimizationConfig:
    """网络优化配置"""
    # 连接配置
    max_connections: int = 1000
    keep_alive_timeout: int = 30
    connection_timeout: int = 10
    
    # TCP优化
    tcp_nodelay: bool = True
    tcp_keepalive: bool = True
    socket_buffer_size: int = 65536
    
    # WebSocket配置
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    websocket_max_message_size: int = 1048576  # 1MB


@dataclass
class PerformanceMonitoringConfig:
    """性能监控配置"""
    # 监控间隔
    monitoring_interval: int = 10  # seconds
    metrics_retention: int = 1000  # number of samples
    
    # 阈值配置
    cpu_threshold: float = 80.0  # percent
    memory_threshold: float = 80.0  # percent
    latency_threshold: float = 100.0  # milliseconds
    
    # 告警配置
    enable_alerts: bool = True
    alert_cooldown: int = 300  # seconds
    
    # 日志配置
    enable_performance_logging: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 1.0  # seconds


@dataclass
class CTPPerformanceConfig:
    """CTP性能优化总配置"""
    optimization_level: OptimizationLevel = OptimizationLevel.MEDIUM
    
    # 子配置
    database: DatabaseOptimizationConfig = None
    cache: CacheOptimizationConfig = None
    network: NetworkOptimizationConfig = None
    monitoring: PerformanceMonitoringConfig = None
    
    # 高频交易优化
    enable_hft_mode: bool = False
    hft_latency_target: float = 1.0  # milliseconds
    hft_throughput_target: int = 10000  # orders per second
    
    # 自动优化
    enable_auto_optimization: bool = True
    auto_optimization_interval: int = 3600  # seconds
    
    def __post_init__(self):
        if self.database is None:
            self.database = DatabaseOptimizationConfig()
        if self.cache is None:
            self.cache = CacheOptimizationConfig()
        if self.network is None:
            self.network = NetworkOptimizationConfig()
        if self.monitoring is None:
            self.monitoring = PerformanceMonitoringConfig()
        
        # 根据优化级别调整配置
        self._adjust_config_by_level()
    
    def _adjust_config_by_level(self):
        """根据优化级别调整配置"""
        if self.optimization_level == OptimizationLevel.LOW:
            self.database.pool_size = 20
            self.database.max_concurrent_queries = 5
            self.cache.redis_pool_size = 50
            self.cache.enable_compression = False
            
        elif self.optimization_level == OptimizationLevel.MEDIUM:
            self.database.pool_size = 50
            self.database.max_concurrent_queries = 10
            self.cache.redis_pool_size = 100
            self.cache.enable_compression = True
            
        elif self.optimization_level == OptimizationLevel.HIGH:
            self.database.pool_size = 100
            self.database.max_concurrent_queries = 20
            self.cache.redis_pool_size = 200
            self.cache.enable_compression = True
            self.enable_hft_mode = True
            
        elif self.optimization_level == OptimizationLevel.EXTREME:
            self.database.pool_size = 200
            self.database.max_concurrent_queries = 50
            self.cache.redis_pool_size = 500
            self.cache.enable_compression = True
            self.enable_hft_mode = True
            self.hft_latency_target = 0.5
            self.hft_throughput_target = 50000


# 性能优化策略配置
PERFORMANCE_STRATEGIES = {
    "market_data_optimization": {
        "description": "市场数据处理优化",
        "strategies": [
            "批量插入市场数据",
            "时间序列数据压缩",
            "分区表优化",
            "索引优化"
        ]
    },
    "order_processing_optimization": {
        "description": "订单处理优化", 
        "strategies": [
            "订单批处理",
            "异步处理队列",
            "内存池优化",
            "连接池优化"
        ]
    },
    "cache_optimization": {
        "description": "缓存优化",
        "strategies": [
            "多层缓存架构",
            "智能缓存预热",
            "压缩存储",
            "缓存失效策略"
        ]
    },
    "network_optimization": {
        "description": "网络优化",
        "strategies": [
            "连接复用",
            "数据压缩",
            "批量传输",
            "WebSocket优化"
        ]
    }
}

# 性能基准配置
PERFORMANCE_BENCHMARKS = {
    "latency": {
        "order_submission": {"target": 10, "unit": "ms"},
        "market_data_processing": {"target": 5, "unit": "ms"},
        "database_query": {"target": 50, "unit": "ms"},
        "cache_access": {"target": 1, "unit": "ms"}
    },
    "throughput": {
        "orders_per_second": {"target": 1000, "unit": "ops"},
        "market_data_updates": {"target": 10000, "unit": "ops"},
        "database_inserts": {"target": 5000, "unit": "ops"},
        "cache_operations": {"target": 50000, "unit": "ops"}
    },
    "resource_usage": {
        "cpu_usage": {"target": 70, "unit": "%"},
        "memory_usage": {"target": 80, "unit": "%"},
        "network_bandwidth": {"target": 100, "unit": "Mbps"},
        "disk_io": {"target": 500, "unit": "MB/s"}
    }
}

# 默认配置实例
default_performance_config = CTPPerformanceConfig()

# 高频交易配置实例
hft_performance_config = CTPPerformanceConfig(
    optimization_level=OptimizationLevel.EXTREME,
    enable_hft_mode=True
)

# 开发环境配置实例
dev_performance_config = CTPPerformanceConfig(
    optimization_level=OptimizationLevel.LOW
)
