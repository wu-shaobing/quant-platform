"""
CTP连接池管理器
管理CTP交易和行情连接的高性能连接池
"""
import asyncio
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """连接状态"""
    IDLE = "idle"
    ACTIVE = "active"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    status: ConnectionStatus
    created_at: datetime
    last_used: datetime
    use_count: int
    error_count: int
    connection_object: Any = None


class CTPConnectionPool:
    """CTP连接池"""
    
    def __init__(
        self,
        name: str,
        factory: Callable,
        max_connections: int = 10,
        min_connections: int = 2,
        max_idle_time: int = 300,  # 5分钟
        health_check_interval: int = 60,  # 1分钟
        max_retries: int = 3
    ):
        self.name = name
        self.factory = factory
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.max_retries = max_retries
        
        self._connections: Dict[str, ConnectionInfo] = {}
        self._idle_connections = deque()
        self._lock = threading.RLock()
        self._connection_counter = 0
        self._health_check_task = None
        self._shutdown = False
        
        # 统计信息
        self._total_created = 0
        self._total_acquired = 0
        self._total_released = 0
        self._total_errors = 0
        
        # 初始化最小连接数
        self._initialize_connections()
        
        # 启动健康检查
        self._start_health_check()
    
    def _initialize_connections(self):
        """初始化最小连接数"""
        for _ in range(self.min_connections):
            try:
                self._create_connection()
            except Exception as e:
                logger.error(f"Failed to initialize connection in pool {self.name}: {e}")
    
    def _create_connection(self) -> Optional[ConnectionInfo]:
        """创建新连接"""
        try:
            with self._lock:
                if len(self._connections) >= self.max_connections:
                    return None
                
                self._connection_counter += 1
                connection_id = f"{self.name}_{self._connection_counter}"
                
                # 创建连接对象
                connection_obj = self.factory()
                
                # 创建连接信息
                conn_info = ConnectionInfo(
                    connection_id=connection_id,
                    status=ConnectionStatus.IDLE,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                    use_count=0,
                    error_count=0,
                    connection_object=connection_obj
                )
                
                self._connections[connection_id] = conn_info
                self._idle_connections.append(connection_id)
                self._total_created += 1
                
                logger.debug(f"Created new connection {connection_id} in pool {self.name}")
                return conn_info
                
        except Exception as e:
            logger.error(f"Failed to create connection in pool {self.name}: {e}")
            self._total_errors += 1
            return None
    
    def acquire_connection(self, timeout: float = 30.0) -> Optional[ConnectionInfo]:
        """获取连接"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self._lock:
                # 尝试从空闲连接中获取
                if self._idle_connections:
                    connection_id = self._idle_connections.popleft()
                    conn_info = self._connections.get(connection_id)
                    
                    if conn_info and self._is_connection_healthy(conn_info):
                        conn_info.status = ConnectionStatus.ACTIVE
                        conn_info.last_used = datetime.now()
                        conn_info.use_count += 1
                        self._total_acquired += 1
                        
                        logger.debug(f"Acquired connection {connection_id} from pool {self.name}")
                        return conn_info
                    else:
                        # 连接不健康，移除并重试
                        if conn_info:
                            self._remove_connection(connection_id)
                
                # 如果没有空闲连接，尝试创建新连接
                if len(self._connections) < self.max_connections:
                    conn_info = self._create_connection()
                    if conn_info:
                        conn_info.status = ConnectionStatus.ACTIVE
                        conn_info.use_count += 1
                        self._total_acquired += 1
                        return conn_info
            
            # 等待一段时间后重试
            time.sleep(0.1)
        
        logger.warning(f"Failed to acquire connection from pool {self.name} within timeout")
        return None
    
    def release_connection(self, conn_info: ConnectionInfo):
        """释放连接"""
        with self._lock:
            if conn_info.connection_id not in self._connections:
                return
            
            # 检查连接是否健康
            if self._is_connection_healthy(conn_info):
                conn_info.status = ConnectionStatus.IDLE
                conn_info.last_used = datetime.now()
                self._idle_connections.append(conn_info.connection_id)
                self._total_released += 1
                
                logger.debug(f"Released connection {conn_info.connection_id} to pool {self.name}")
            else:
                # 连接不健康，移除
                self._remove_connection(conn_info.connection_id)
    
    def _is_connection_healthy(self, conn_info: ConnectionInfo) -> bool:
        """检查连接是否健康"""
        try:
            # 检查连接对象是否存在
            if not conn_info.connection_object:
                return False
            
            # 检查错误次数
            if conn_info.error_count > self.max_retries:
                return False
            
            # 检查连接状态（这里需要根据实际CTP连接对象的API来实现）
            # 示例：假设连接对象有is_connected方法
            if hasattr(conn_info.connection_object, 'is_connected'):
                return conn_info.connection_object.is_connected()
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed for connection {conn_info.connection_id}: {e}")
            conn_info.error_count += 1
            return False
    
    def _remove_connection(self, connection_id: str):
        """移除连接"""
        try:
            conn_info = self._connections.pop(connection_id, None)
            if conn_info:
                # 清理连接对象
                if hasattr(conn_info.connection_object, 'disconnect'):
                    conn_info.connection_object.disconnect()
                
                logger.debug(f"Removed connection {connection_id} from pool {self.name}")
                
        except Exception as e:
            logger.error(f"Error removing connection {connection_id}: {e}")
    
    def _start_health_check(self):
        """启动健康检查任务"""
        def health_check_worker():
            while not self._shutdown:
                try:
                    self._perform_health_check()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health check error in pool {self.name}: {e}")
                    time.sleep(self.health_check_interval)
        
        self._health_check_task = threading.Thread(
            target=health_check_worker,
            daemon=True,
            name=f"HealthCheck-{self.name}"
        )
        self._health_check_task.start()
    
    def _perform_health_check(self):
        """执行健康检查"""
        current_time = datetime.now()
        connections_to_remove = []
        
        with self._lock:
            for connection_id, conn_info in self._connections.items():
                # 检查空闲超时
                if (conn_info.status == ConnectionStatus.IDLE and 
                    (current_time - conn_info.last_used).total_seconds() > self.max_idle_time):
                    connections_to_remove.append(connection_id)
                    continue
                
                # 检查连接健康状态
                if not self._is_connection_healthy(conn_info):
                    connections_to_remove.append(connection_id)
            
            # 移除不健康的连接
            for connection_id in connections_to_remove:
                self._remove_connection(connection_id)
                # 从空闲队列中移除
                if connection_id in self._idle_connections:
                    self._idle_connections.remove(connection_id)
            
            # 确保最小连接数
            while len(self._connections) < self.min_connections:
                if not self._create_connection():
                    break
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._lock:
            idle_count = len(self._idle_connections)
            active_count = sum(
                1 for conn in self._connections.values() 
                if conn.status == ConnectionStatus.ACTIVE
            )
            
            return {
                "pool_name": self.name,
                "total_connections": len(self._connections),
                "idle_connections": idle_count,
                "active_connections": active_count,
                "max_connections": self.max_connections,
                "min_connections": self.min_connections,
                "total_created": self._total_created,
                "total_acquired": self._total_acquired,
                "total_released": self._total_released,
                "total_errors": self._total_errors,
                "utilization_rate": (active_count / max(len(self._connections), 1)) * 100
            }
    
    def shutdown(self):
        """关闭连接池"""
        self._shutdown = True
        
        with self._lock:
            # 关闭所有连接
            for connection_id in list(self._connections.keys()):
                self._remove_connection(connection_id)
            
            self._idle_connections.clear()
        
        logger.info(f"Connection pool {self.name} shutdown completed")


class CTPConnectionManager:
    """CTP连接管理器"""
    
    def __init__(self):
        self._pools: Dict[str, CTPConnectionPool] = {}
        self._lock = threading.RLock()
    
    def create_pool(
        self,
        name: str,
        factory: Callable,
        max_connections: int = 10,
        min_connections: int = 2,
        **kwargs
    ) -> CTPConnectionPool:
        """创建连接池"""
        with self._lock:
            if name in self._pools:
                raise ValueError(f"Pool {name} already exists")
            
            pool = CTPConnectionPool(
                name=name,
                factory=factory,
                max_connections=max_connections,
                min_connections=min_connections,
                **kwargs
            )
            
            self._pools[name] = pool
            logger.info(f"Created connection pool: {name}")
            return pool
    
    def get_pool(self, name: str) -> Optional[CTPConnectionPool]:
        """获取连接池"""
        return self._pools.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接池统计信息"""
        return {
            name: pool.get_stats() 
            for name, pool in self._pools.items()
        }
    
    def shutdown_all(self):
        """关闭所有连接池"""
        with self._lock:
            for pool in self._pools.values():
                pool.shutdown()
            self._pools.clear()
        
        logger.info("All connection pools shutdown completed")


# 全局连接管理器实例
ctp_connection_manager = CTPConnectionManager()


# 导出主要组件
__all__ = [
    "CTPConnectionPool",
    "CTPConnectionManager",
    "ctp_connection_manager",
    "ConnectionStatus",
    "ConnectionInfo",
]
