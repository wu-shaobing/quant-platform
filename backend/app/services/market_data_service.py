"""
行情数据处理服务
"""
import asyncio
import logging
import json
import gzip
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Set, Optional, Callable, Any
from collections import defaultdict, deque
import threading

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update

from app.core.database import get_db
from app.models.market import MarketData
from app.schemas.market_data import TickData, KlineData, MarketDepth
from app.services.ctp_service import ctp_service

logger = logging.getLogger(__name__)


class MarketDataService:
    """行情数据处理服务"""
    
    def __init__(self):
        self.subscribed_symbols: Set[str] = set()
        self.tick_callbacks: List[Callable] = []
        self.kline_callbacks: List[Callable] = []
        self.depth_callbacks: List[Callable] = []
        
        # WebSocket客户端管理
        self.clients: Dict[str, Any] = {}
        self.client_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # 数据缓存
        self.tick_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.kline_cache: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=100)))
        
        # 性能统计
        self.stats = {
            "tick_count": 0,
            "kline_count": 0,
            "error_count": 0,
            "last_update": None
        }
        
        # 数据清洗配置
        self.cleaning_rules = {
            "min_price": Decimal("0.01"),
            "max_price": Decimal("100000.0"),
            "min_volume": 0,
            "max_volume": 1000000
        }
        
        self._running = False
        self._lock = asyncio.Lock()
    
    async def start(self):
        """启动服务"""
        self._running = True
        logger.info("Market data service started")
    
    async def stop(self):
        """停止服务"""
        self._running = False
        await self.cleanup()
        logger.info("Market data service stopped")
    
    async def cleanup(self):
        """清理资源"""
        self.clients.clear()
        self.client_subscriptions.clear()
        self.tick_cache.clear()
        self.kline_cache.clear()
    
    # 订阅管理
    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        """订阅行情数据"""
        try:
            async with self._lock:
                # 验证合约代码
                valid_symbols = []
                for symbol in symbols:
                    if await self._validate_symbol(symbol):
                        valid_symbols.append(symbol)
                        self.subscribed_symbols.add(symbol)
                
                if valid_symbols:
                    # 调用CTP服务订阅
                    result = await ctp_service.subscribe_market_data(valid_symbols)
                    if result:
                        logger.info(f"Subscribed to symbols: {valid_symbols}")
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to subscribe symbols: {e}")
            self.stats["error_count"] += 1
            return False
    
    async def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """取消订阅行情数据"""
        try:
            async with self._lock:
                symbols_to_unsubscribe = []
                for symbol in symbols:
                    if symbol in self.subscribed_symbols:
                        self.subscribed_symbols.remove(symbol)
                        symbols_to_unsubscribe.append(symbol)
                
                if symbols_to_unsubscribe:
                    # 调用CTP服务取消订阅
                    result = await ctp_service.unsubscribe_market_data(symbols_to_unsubscribe)
                    if result:
                        logger.info(f"Unsubscribed from symbols: {symbols_to_unsubscribe}")
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe symbols: {e}")
            self.stats["error_count"] += 1
            return False
    
    async def _validate_symbol(self, symbol: str) -> bool:
        """验证合约代码"""
        if not symbol or len(symbol) < 2:
            return False
        
        # 这里可以添加更复杂的验证逻辑
        # 比如检查合约是否存在于数据库中
        return True
    
    # 数据处理
    async def process_tick_data(self, tick_data: TickData):
        """处理Tick数据"""
        try:
            # 数据验证
            if not await self.validate_tick_data(tick_data):
                return
            
            # 数据清洗
            cleaned_data = await self.clean_tick_data(tick_data)
            if not cleaned_data:
                return
            
            # 缓存数据
            self.tick_cache[tick_data.symbol].append(cleaned_data)
            
            # 存储数据
            await self.store_tick_data(cleaned_data)
            
            # 实时推送
            await self.push_tick_data(cleaned_data)
            
            # 触发回调
            for callback in self.tick_callbacks:
                try:
                    callback(cleaned_data)
                except Exception as e:
                    logger.warning(f"Tick callback error: {e}")
            
            # 更新统计
            self.stats["tick_count"] += 1
            self.stats["last_update"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to process tick data: {e}")
            self.stats["error_count"] += 1
    
    async def validate_tick_data(self, tick_data: TickData) -> bool:
        """验证Tick数据"""
        if not tick_data.symbol:
            raise ValueError("Symbol cannot be empty")
        
        if tick_data.last_price <= 0:
            raise ValueError("Last price must be positive")
        
        if tick_data.volume < 0:
            raise ValueError("Volume cannot be negative")
        
        return True
    
    async def clean_tick_data(self, tick_data: TickData) -> Optional[TickData]:
        """清洗Tick数据"""
        # 价格范围检查
        if (tick_data.last_price < self.cleaning_rules["min_price"] or 
            tick_data.last_price > self.cleaning_rules["max_price"]):
            logger.warning(f"Price out of range: {tick_data.last_price}")
            return None
        
        # 成交量检查
        if (tick_data.volume < self.cleaning_rules["min_volume"] or 
            tick_data.volume > self.cleaning_rules["max_volume"]):
            logger.warning(f"Volume out of range: {tick_data.volume}")
            return None
        
        # 时间戳检查
        now = datetime.now()
        if tick_data.timestamp > now + timedelta(minutes=1):
            logger.warning(f"Future timestamp: {tick_data.timestamp}")
            tick_data.timestamp = now
        
        return tick_data
    
    async def store_tick_data(self, tick_data: TickData):
        """存储Tick数据到数据库"""
        try:
            async with get_db() as session:
                market_data = MarketData(
                    symbol=tick_data.symbol,
                    exchange=tick_data.exchange,
                    data_type="tick",
                    timestamp=tick_data.timestamp,
                    data=tick_data.dict()
                )
                session.add(market_data)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store tick data: {e}")
            raise
    
    # K线生成
    async def generate_klines(self, tick_data_list: List[TickData], interval: str) -> List[KlineData]:
        """从Tick数据生成K线"""
        if not tick_data_list:
            return []
        
        klines = []
        symbol = tick_data_list[0].symbol
        exchange = tick_data_list[0].exchange
        
        # 按时间间隔分组
        interval_seconds = self._parse_interval(interval)
        groups = self._group_ticks_by_interval(tick_data_list, interval_seconds)
        
        for timestamp, ticks in groups.items():
            if not ticks:
                continue
            
            # 计算OHLCV
            open_price = ticks[0].last_price
            close_price = ticks[-1].last_price
            high_price = max(tick.last_price for tick in ticks)
            low_price = min(tick.last_price for tick in ticks)
            volume = sum(tick.volume for tick in ticks)
            turnover = sum(tick.turnover or Decimal("0") for tick in ticks)
            
            kline = KlineData(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                turnover=turnover
            )
            
            klines.append(kline)
        
        return klines
    
    def _parse_interval(self, interval: str) -> int:
        """解析时间间隔为秒数"""
        if interval.endswith('s'):
            return int(interval[:-1])
        elif interval.endswith('m'):
            return int(interval[:-1]) * 60
        elif interval.endswith('h'):
            return int(interval[:-1]) * 3600
        elif interval.endswith('d'):
            return int(interval[:-1]) * 86400
        else:
            return 60  # 默认1分钟
    
    def _group_ticks_by_interval(self, ticks: List[TickData], interval_seconds: int) -> Dict[datetime, List[TickData]]:
        """按时间间隔分组Tick数据"""
        groups = defaultdict(list)
        
        for tick in ticks:
            # 计算时间间隔的开始时间
            timestamp = tick.timestamp
            interval_start = datetime(
                timestamp.year, timestamp.month, timestamp.day,
                timestamp.hour, timestamp.minute // (interval_seconds // 60) * (interval_seconds // 60)
            )
            groups[interval_start].append(tick)
        
        return dict(groups)
    
    # 市场深度处理
    async def process_market_depth(self, depth_data: MarketDepth) -> bool:
        """处理市场深度数据"""
        try:
            # 验证深度数据
            if not depth_data.symbol or not depth_data.bids or not depth_data.asks:
                return False
            
            # 存储深度数据
            await self.store_market_depth(depth_data)
            
            # 实时推送
            await self.push_market_depth(depth_data)
            
            # 触发回调
            for callback in self.depth_callbacks:
                try:
                    callback(depth_data)
                except Exception as e:
                    logger.warning(f"Depth callback error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process market depth: {e}")
            return False
    
    async def store_market_depth(self, depth_data: MarketDepth):
        """存储市场深度数据"""
        try:
            async with get_db() as session:
                market_data = MarketData(
                    symbol=depth_data.symbol,
                    exchange=depth_data.exchange,
                    data_type="depth",
                    timestamp=depth_data.timestamp,
                    data=depth_data.dict()
                )
                session.add(market_data)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store market depth: {e}")
            raise
    
    # WebSocket客户端管理
    def add_client(self, client_id: str, websocket):
        """添加WebSocket客户端"""
        self.clients[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def remove_client(self, client_id: str):
        """移除WebSocket客户端"""
        if client_id in self.clients:
            del self.clients[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_client(self, client_id: str, symbols: List[str]):
        """客户端订阅行情"""
        if client_id not in self.clients:
            return False
        
        self.client_subscriptions[client_id].update(symbols)
        
        # 如果是新的合约，需要订阅
        new_symbols = [s for s in symbols if s not in self.subscribed_symbols]
        if new_symbols:
            await self.subscribe_symbols(new_symbols)
        
        return True
    
    async def push_tick_data(self, tick_data: TickData):
        """推送Tick数据到订阅的客户端"""
        message = {
            "type": "tick",
            "data": tick_data.dict()
        }
        
        await self._broadcast_to_subscribers(tick_data.symbol, message)
    
    async def push_market_depth(self, depth_data: MarketDepth):
        """推送市场深度数据到订阅的客户端"""
        message = {
            "type": "depth",
            "data": depth_data.dict()
        }
        
        await self._broadcast_to_subscribers(depth_data.symbol, message)
    
    async def _broadcast_to_subscribers(self, symbol: str, message: dict):
        """向订阅指定合约的客户端广播消息"""
        message_str = json.dumps(message, default=str)
        
        for client_id, websocket in self.clients.items():
            if symbol in self.client_subscriptions[client_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.warning(f"Failed to send message to client {client_id}: {e}")
                    # 移除断开的客户端
                    self.remove_client(client_id)
    
    # 数据压缩
    async def compress_tick_data(self, tick_data_list: List[TickData]) -> List[TickData]:
        """压缩Tick数据（去重、合并等）"""
        if not tick_data_list:
            return []
        
        # 按时间排序
        sorted_ticks = sorted(tick_data_list, key=lambda x: x.timestamp)
        
        # 去重（相同时间戳的数据只保留最后一个）
        unique_ticks = {}
        for tick in sorted_ticks:
            key = (tick.symbol, tick.timestamp.replace(microsecond=0))
            unique_ticks[key] = tick
        
        return list(unique_ticks.values())
    
    # 回调管理
    def add_tick_callback(self, callback: Callable):
        """添加Tick数据回调"""
        self.tick_callbacks.append(callback)
    
    def add_kline_callback(self, callback: Callable):
        """添加K线数据回调"""
        self.kline_callbacks.append(callback)
    
    def add_depth_callback(self, callback: Callable):
        """添加深度数据回调"""
        self.depth_callbacks.append(callback)
    
    # 统计信息
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "subscribed_symbols": list(self.subscribed_symbols),
            "client_count": len(self.clients),
            "cache_size": {
                symbol: len(cache) for symbol, cache in self.tick_cache.items()
            }
        }


# 全局行情数据服务实例
market_data_service = MarketDataService()
