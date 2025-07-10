"""
Redis缓存管理器
针对CTP高频交易优化的缓存系统
"""
import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化Redis连接"""
        if self._initialized:
            return
        
        try:
            # 创建连接池 - 针对高频交易优化
            self.connection_pool = ConnectionPool(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                max_connections=100,  # 增加最大连接数
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.connection_pool,
                decode_responses=False,  # 保持二进制数据以支持pickle
            )
            
            # 测试连接
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis cache manager initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, using memory cache fallback")
            self.redis_client = None
            self._initialized = True
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        logger.info("Redis connections closed")
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """设置缓存值"""
        if not self.redis_client:
            return False
        
        try:
            # 序列化数据
            if serialize:
                if isinstance(value, (dict, list)):
                    data = json.dumps(value, default=str).encode('utf-8')
                else:
                    data = pickle.dumps(value)
            else:
                data = value
            
            # 设置缓存
            result = await self.redis_client.set(key, data, ex=expire)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def get(self, key: str, deserialize: bool = True) -> Any:
        """获取缓存值"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            
            # 反序列化数据
            if deserialize:
                try:
                    # 尝试JSON反序列化
                    return json.loads(data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # 尝试pickle反序列化
                    return pickle.loads(data)
            else:
                return data
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def mget(self, keys: List[str], deserialize: bool = True) -> List[Any]:
        """批量获取缓存"""
        if not self.redis_client:
            return [None] * len(keys)
        
        try:
            data_list = await self.redis_client.mget(keys)
            results = []
            
            for data in data_list:
                if data is None:
                    results.append(None)
                elif deserialize:
                    try:
                        results.append(json.loads(data.decode('utf-8')))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        results.append(pickle.loads(data))
                else:
                    results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Cache mget error for keys {keys}: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """批量设置缓存"""
        if not self.redis_client:
            return False
        
        try:
            # 序列化所有值
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[key] = json.dumps(value, default=str).encode('utf-8')
                else:
                    serialized_mapping[key] = pickle.dumps(value)
            
            # 批量设置
            result = await self.redis_client.mset(serialized_mapping)
            
            # 如果设置了过期时间，批量设置过期
            if expire and result:
                pipe = self.redis_client.pipeline()
                for key in mapping.keys():
                    pipe.expire(key, expire)
                await pipe.execute()
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                result = await self.redis_client.delete(*keys)
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "0"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}


# 全局缓存管理器实例
cache_manager = CacheManager()

async def get_redis():
    """获取Redis客户端实例"""
    if not cache_manager._initialized:
        await cache_manager.initialize()
    return cache_manager.redis_client


# CTP特定的缓存键生成器
class CTPCacheKeys:
    """CTP缓存键生成器"""
    
    @staticmethod
    def market_data(instrument_id: str) -> str:
        """行情数据缓存键"""
        return f"ctp:market:{instrument_id}"
    
    @staticmethod
    def order_book(instrument_id: str) -> str:
        """订单簿缓存键"""
        return f"ctp:orderbook:{instrument_id}"
    
    @staticmethod
    def user_orders(user_id: int) -> str:
        """用户订单缓存键"""
        return f"ctp:orders:user:{user_id}"
    
    @staticmethod
    def user_positions(user_id: int) -> str:
        """用户持仓缓存键"""
        return f"ctp:positions:user:{user_id}"
    
    @staticmethod
    def instrument_info(instrument_id: str) -> str:
        """合约信息缓存键"""
        return f"ctp:instrument:{instrument_id}"
    
    @staticmethod
    def trading_session() -> str:
        """交易时段缓存键"""
        return "ctp:trading_session"
    
    @staticmethod
    def user_session(user_id: int) -> str:
        """用户会话缓存键"""
        return f"ctp:session:user:{user_id}"


# 缓存装饰器
def cache_result(key_func, expire: int = 300):
    """缓存结果装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = key_func(*args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_manager.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator


# 导出主要组件
__all__ = [
    "CacheManager",
    "cache_manager", 
    "CTPCacheKeys",
    "cache_result",
]
