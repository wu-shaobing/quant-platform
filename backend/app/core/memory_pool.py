"""
内存池管理器
针对高频交易优化的内存管理系统
"""
import asyncio
import logging
import threading
import weakref
from collections import deque
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PoolStats:
    """内存池统计信息"""
    pool_name: str
    total_objects: int
    available_objects: int
    in_use_objects: int
    created_count: int
    recycled_count: int
    hit_rate: float
    last_reset: datetime


class ObjectPool(Generic[T]):
    """通用对象池"""
    
    def __init__(
        self, 
        factory: callable, 
        reset_func: Optional[callable] = None,
        max_size: int = 1000,
        name: str = "ObjectPool"
    ):
        self.factory = factory
        self.reset_func = reset_func
        self.max_size = max_size
        self.name = name
        
        self._pool = deque()
        self._lock = threading.RLock()
        self._created_count = 0
        self._recycled_count = 0
        self._in_use = weakref.WeakSet()
        
        # 预创建一些对象
        self._warm_up(min(50, max_size // 10))
    
    def _warm_up(self, count: int):
        """预热对象池"""
        for _ in range(count):
            if len(self._pool) < self.max_size:
                obj = self.factory()
                self._pool.append(obj)
                self._created_count += 1
    
    def acquire(self) -> T:
        """获取对象"""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self._recycled_count += 1
            else:
                obj = self.factory()
                self._created_count += 1
            
            self._in_use.add(obj)
            return obj
    
    def release(self, obj: T):
        """释放对象"""
        with self._lock:
            if obj in self._in_use:
                self._in_use.discard(obj)
                
                if len(self._pool) < self.max_size:
                    # 重置对象状态
                    if self.reset_func:
                        self.reset_func(obj)
                    
                    self._pool.append(obj)
    
    def get_stats(self) -> PoolStats:
        """获取池统计信息"""
        with self._lock:
            total_objects = len(self._pool) + len(self._in_use)
            hit_rate = (
                self._recycled_count / max(self._created_count, 1) * 100
                if self._created_count > 0 else 0
            )
            
            return PoolStats(
                pool_name=self.name,
                total_objects=total_objects,
                available_objects=len(self._pool),
                in_use_objects=len(self._in_use),
                created_count=self._created_count,
                recycled_count=self._recycled_count,
                hit_rate=hit_rate,
                last_reset=datetime.now()
            )
    
    def clear(self):
        """清空对象池"""
        with self._lock:
            self._pool.clear()
            self._in_use.clear()


class CTPDataPool:
    """CTP数据对象池"""
    
    def __init__(self):
        # 订单数据池
        self.order_pool = ObjectPool(
            factory=lambda: {
                "user_id": 0,
                "order_ref": "",
                "instrument_id": "",
                "direction": "",
                "offset_flag": "",
                "limit_price": 0.0,
                "volume": 0,
                "status": "",
                "timestamp": None
            },
            reset_func=self._reset_order_data,
            max_size=5000,
            name="CTPOrderPool"
        )
        
        # 成交数据池
        self.trade_pool = ObjectPool(
            factory=lambda: {
                "user_id": 0,
                "trade_id": "",
                "order_ref": "",
                "instrument_id": "",
                "direction": "",
                "offset_flag": "",
                "price": 0.0,
                "volume": 0,
                "trade_time": "",
                "timestamp": None
            },
            reset_func=self._reset_trade_data,
            max_size=10000,
            name="CTPTradePool"
        )
        
        # 行情数据池
        self.market_data_pool = ObjectPool(
            factory=lambda: {
                "instrument_id": "",
                "last_price": 0.0,
                "bid_price": 0.0,
                "ask_price": 0.0,
                "bid_volume": 0,
                "ask_volume": 0,
                "volume": 0,
                "turnover": 0.0,
                "open_interest": 0,
                "update_time": "",
                "timestamp": None
            },
            reset_func=self._reset_market_data,
            max_size=2000,
            name="CTPMarketDataPool"
        )
        
        # 持仓数据池
        self.position_pool = ObjectPool(
            factory=lambda: {
                "user_id": 0,
                "instrument_id": "",
                "direction": "",
                "position": 0,
                "avg_price": 0.0,
                "margin": 0.0,
                "profit": 0.0,
                "timestamp": None
            },
            reset_func=self._reset_position_data,
            max_size=1000,
            name="CTPPositionPool"
        )
        
        # 字符串缓冲池
        self.string_buffer_pool = ObjectPool(
            factory=lambda: bytearray(1024),
            reset_func=lambda buf: buf.clear(),
            max_size=500,
            name="StringBufferPool"
        )
        
        # 列表缓冲池
        self.list_buffer_pool = ObjectPool(
            factory=list,
            reset_func=lambda lst: lst.clear(),
            max_size=1000,
            name="ListBufferPool"
        )
    
    def _reset_order_data(self, data: dict):
        """重置订单数据"""
        data.update({
            "user_id": 0,
            "order_ref": "",
            "instrument_id": "",
            "direction": "",
            "offset_flag": "",
            "limit_price": 0.0,
            "volume": 0,
            "status": "",
            "timestamp": None
        })
    
    def _reset_trade_data(self, data: dict):
        """重置成交数据"""
        data.update({
            "user_id": 0,
            "trade_id": "",
            "order_ref": "",
            "instrument_id": "",
            "direction": "",
            "offset_flag": "",
            "price": 0.0,
            "volume": 0,
            "trade_time": "",
            "timestamp": None
        })
    
    def _reset_market_data(self, data: dict):
        """重置行情数据"""
        data.update({
            "instrument_id": "",
            "last_price": 0.0,
            "bid_price": 0.0,
            "ask_price": 0.0,
            "bid_volume": 0,
            "ask_volume": 0,
            "volume": 0,
            "turnover": 0.0,
            "open_interest": 0,
            "update_time": "",
            "timestamp": None
        })
    
    def _reset_position_data(self, data: dict):
        """重置持仓数据"""
        data.update({
            "user_id": 0,
            "instrument_id": "",
            "direction": "",
            "position": 0,
            "avg_price": 0.0,
            "margin": 0.0,
            "profit": 0.0,
            "timestamp": None
        })
    
    def get_order_data(self) -> dict:
        """获取订单数据对象"""
        return self.order_pool.acquire()
    
    def release_order_data(self, data: dict):
        """释放订单数据对象"""
        self.order_pool.release(data)
    
    def get_trade_data(self) -> dict:
        """获取成交数据对象"""
        return self.trade_pool.acquire()
    
    def release_trade_data(self, data: dict):
        """释放成交数据对象"""
        self.trade_pool.release(data)
    
    def get_market_data(self) -> dict:
        """获取行情数据对象"""
        return self.market_data_pool.acquire()
    
    def release_market_data(self, data: dict):
        """释放行情数据对象"""
        self.market_data_pool.release(data)
    
    def get_position_data(self) -> dict:
        """获取持仓数据对象"""
        return self.position_pool.acquire()
    
    def release_position_data(self, data: dict):
        """释放持仓数据对象"""
        self.position_pool.release(data)
    
    def get_string_buffer(self) -> bytearray:
        """获取字符串缓冲区"""
        return self.string_buffer_pool.acquire()
    
    def release_string_buffer(self, buffer: bytearray):
        """释放字符串缓冲区"""
        self.string_buffer_pool.release(buffer)
    
    def get_list_buffer(self) -> list:
        """获取列表缓冲区"""
        return self.list_buffer_pool.acquire()
    
    def release_list_buffer(self, buffer: list):
        """释放列表缓冲区"""
        self.list_buffer_pool.release(buffer)
    
    def get_all_stats(self) -> List[PoolStats]:
        """获取所有池的统计信息"""
        return [
            self.order_pool.get_stats(),
            self.trade_pool.get_stats(),
            self.market_data_pool.get_stats(),
            self.position_pool.get_stats(),
            self.string_buffer_pool.get_stats(),
            self.list_buffer_pool.get_stats(),
        ]
    
    def clear_all_pools(self):
        """清空所有对象池"""
        self.order_pool.clear()
        self.trade_pool.clear()
        self.market_data_pool.clear()
        self.position_pool.clear()
        self.string_buffer_pool.clear()
        self.list_buffer_pool.clear()


# 全局CTP数据池实例
ctp_data_pool = CTPDataPool()


# 上下文管理器
class PooledObject:
    """池化对象上下文管理器"""
    
    def __init__(self, pool: ObjectPool, obj: Any):
        self.pool = pool
        self.obj = obj
    
    def __enter__(self):
        return self.obj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.release(self.obj)


# 便捷函数
def get_pooled_order_data():
    """获取池化的订单数据"""
    obj = ctp_data_pool.get_order_data()
    return PooledObject(ctp_data_pool.order_pool, obj)


def get_pooled_trade_data():
    """获取池化的成交数据"""
    obj = ctp_data_pool.get_trade_data()
    return PooledObject(ctp_data_pool.trade_pool, obj)


def get_pooled_market_data():
    """获取池化的行情数据"""
    obj = ctp_data_pool.get_market_data()
    return PooledObject(ctp_data_pool.market_data_pool, obj)


# 导出主要组件
__all__ = [
    "ObjectPool",
    "CTPDataPool", 
    "ctp_data_pool",
    "PoolStats",
    "PooledObject",
    "get_pooled_order_data",
    "get_pooled_trade_data", 
    "get_pooled_market_data",
]
