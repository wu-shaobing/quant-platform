"""
行情数据处理模块综合测试
包含数据接收、清洗、存储、实时推送的完整测试覆盖
"""
import pytest
import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from collections import deque
import uuid

from app.services.market_data_service import MarketDataService
from app.schemas.market_data import (
    TickData, 
    KlineData, 
    MarketDepth,
    MarketDataConfig,
    SubscribeRequest
)
from app.models.market import MarketData, KlineData as KlineModel, DepthData
from app.core.database import get_db
from app.core.cache import get_redis


class TestMarketDataProcessing:
    """行情数据处理核心功能测试"""
    
    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        service = MarketDataService()
        # 重置状态
        service.subscribed_symbols.clear()
        service.tick_callbacks.clear()
        service.kline_callbacks.clear()
        service.depth_callbacks.clear()
        service.clients.clear()
        service.client_subscriptions.clear()
        service.tick_cache.clear()
        service.kline_cache.clear()
        service.stats = {
            "tick_count": 0,
            "kline_count": 0,
            "error_count": 0,
            "last_update": None
        }
        return service
    
    @pytest.fixture
    def sample_tick_data(self):
        """示例Tick数据"""
        return TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            bid_price_1=Decimal("3849.0"),
            ask_price_1=Decimal("3851.0"),
            bid_volume_1=100,
            ask_volume_1=150,
            volume=12345,
            turnover=Decimal("47532750.0"),
            open_interest=98765,
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def sample_kline_data(self):
        """示例K线数据"""
        return KlineData(
            symbol="rb2405",
            exchange="SHFE",
            interval="1m",
            open_price=Decimal("3845.0"),
            high_price=Decimal("3855.0"),
            low_price=Decimal("3840.0"),
            close_price=Decimal("3850.0"),
            volume=5000,
            turnover=Decimal("19250000.0"),
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def sample_depth_data(self):
        """示例深度数据"""
        return MarketDepth(
            symbol="rb2405",
            exchange="SHFE",
            bid_prices=[Decimal("3849.0"), Decimal("3848.0"), Decimal("3847.0")],
            bid_volumes=[100, 200, 150],
            ask_prices=[Decimal("3851.0"), Decimal("3852.0"), Decimal("3853.0")],
            ask_volumes=[150, 180, 120],
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.publish = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.hget = AsyncMock()
        mock_redis.expire = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    # 数据接收测试
    @pytest.mark.asyncio
    async def test_data_reception_basic(self, market_service, sample_tick_data):
        """测试基本数据接收功能"""
        # 添加回调函数
        received_data = []
        
        def on_tick(data):
            received_data.append(data)
        
        market_service.add_tick_callback(on_tick)
        
        # 处理数据
        await market_service.process_tick_data(sample_tick_data)
        
        # 验证数据接收
        assert len(received_data) == 1
        assert received_data[0].symbol == sample_tick_data.symbol
        assert received_data[0].last_price == sample_tick_data.last_price
        
        # 验证统计信息更新
        assert market_service.stats["tick_count"] == 1
        assert market_service.stats["last_update"] is not None

    @pytest.mark.asyncio
    async def test_data_reception_batch(self, market_service):
        """测试批量数据接收"""
        # 创建批量数据
        tick_data_list = []
        for i in range(100):
            tick_data = TickData(
                symbol=f"rb240{i % 5}",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=1000 + i,
                timestamp=datetime.now()
            )
            tick_data_list.append(tick_data)
        
        # 批量处理
        start_time = datetime.now()
        for tick_data in tick_data_list:
            await market_service.process_tick_data(tick_data)
        end_time = datetime.now()
        
        # 验证处理性能
        processing_time = (end_time - start_time).total_seconds()
        assert processing_time < 1.0  # 100条数据应在1秒内处理完成
        assert market_service.stats["tick_count"] == 100

    @pytest.mark.asyncio
    async def test_data_reception_concurrent(self, market_service):
        """测试并发数据接收"""
        # 创建并发任务
        async def process_data(symbol_suffix):
            for i in range(10):
                tick_data = TickData(
                    symbol=f"rb{symbol_suffix}",
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i}"),
                    volume=1000 + i,
                    timestamp=datetime.now()
                )
                await market_service.process_tick_data(tick_data)
        
        # 并发执行
        tasks = [process_data(f"240{i}") for i in range(5)]
        await asyncio.gather(*tasks)
        
        # 验证并发处理结果
        assert market_service.stats["tick_count"] == 50

    # 数据清洗测试
    @pytest.mark.asyncio
    async def test_data_cleaning_invalid_price(self, market_service):
        """测试无效价格数据清洗"""
        # 创建无效价格数据
        invalid_tick = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("-100.0"),  # 负价格
            volume=1000,
            timestamp=datetime.now()
        )
        
        # 处理数据
        result = await market_service.clean_tick_data(invalid_tick)
        
        # 验证清洗结果
        assert result is None or result.last_price >= market_service.cleaning_rules["min_price"]

    @pytest.mark.asyncio
    async def test_data_cleaning_invalid_volume(self, market_service):
        """测试无效成交量数据清洗"""
        # 创建无效成交量数据
        invalid_tick = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=-1000,  # 负成交量
            timestamp=datetime.now()
        )
        
        # 处理数据
        result = await market_service.clean_tick_data(invalid_tick)
        
        # 验证清洗结果
        assert result is None or result.volume >= market_service.cleaning_rules["min_volume"]

    @pytest.mark.asyncio
    async def test_data_cleaning_extreme_values(self, market_service):
        """测试极值数据清洗"""
        # 创建极值数据
        extreme_tick = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("999999.0"),  # 极高价格
            volume=2000000,  # 极大成交量
            timestamp=datetime.now()
        )
        
        # 处理数据
        result = await market_service.clean_tick_data(extreme_tick)
        
        # 验证清洗结果
        if result:
            assert result.last_price <= market_service.cleaning_rules["max_price"]
            assert result.volume <= market_service.cleaning_rules["max_volume"]

    @pytest.mark.asyncio
    async def test_data_cleaning_timestamp_validation(self, market_service):
        """测试时间戳验证"""
        # 创建未来时间戳数据
        future_tick = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now() + timedelta(hours=1)  # 未来时间
        )
        
        # 处理数据
        result = await market_service.clean_tick_data(future_tick)
        
        # 验证时间戳修正
        if result:
            assert result.timestamp <= datetime.now()

    # 数据存储测试
    @pytest.mark.asyncio
    async def test_data_storage_tick(self, market_service, sample_tick_data):
        """测试Tick数据存储"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session
            
            # 存储数据
            await market_service.store_tick_data(sample_tick_data)
            
            # 验证数据库操作
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_storage_kline(self, market_service, sample_kline_data):
        """测试K线数据存储"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session
            
            # 存储数据
            await market_service.store_kline_data(sample_kline_data)
            
            # 验证数据库操作
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_storage_depth(self, market_service, sample_depth_data):
        """测试深度数据存储"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session
            
            # 存储数据
            await market_service.store_market_depth(sample_depth_data)
            
            # 验证数据库操作
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_storage_error_handling(self, market_service, sample_tick_data):
        """测试数据存储错误处理"""
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.commit.side_effect = Exception("Database error")
            mock_get_db.return_value.__aenter__.return_value = mock_session
            
            # 存储数据应该处理异常
            with pytest.raises(Exception):
                await market_service.store_tick_data(sample_tick_data)
            
            # 验证错误统计
            assert market_service.stats["error_count"] > 0


class TestMarketDataCaching:
    """行情数据缓存测试"""

    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.fixture
    def mock_redis(self):
        """模拟Redis客户端"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.delete = AsyncMock()
        mock_redis.publish = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.hget = AsyncMock()
        mock_redis.expire = AsyncMock()
        return mock_redis

    @pytest.mark.asyncio
    async def test_tick_cache_storage(self, market_service):
        """测试Tick数据缓存存储"""
        tick_data = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now()
        )

        # 添加到缓存
        market_service.add_tick_to_cache(tick_data)

        # 验证缓存
        cached_data = market_service.get_cached_ticks("rb2405")
        assert len(cached_data) == 1
        assert cached_data[0].symbol == "rb2405"

    @pytest.mark.asyncio
    async def test_tick_cache_limit(self, market_service):
        """测试Tick缓存大小限制"""
        # 添加超过限制的数据
        for i in range(1200):  # 超过默认1000的限制
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=1000 + i,
                timestamp=datetime.now()
            )
            market_service.add_tick_to_cache(tick_data)

        # 验证缓存大小限制
        cached_data = market_service.get_cached_ticks("rb2405")
        assert len(cached_data) <= 1000

    @pytest.mark.asyncio
    async def test_kline_cache_storage(self, market_service):
        """测试K线数据缓存存储"""
        kline_data = KlineData(
            symbol="rb2405",
            exchange="SHFE",
            interval="1m",
            open_price=Decimal("3845.0"),
            high_price=Decimal("3855.0"),
            low_price=Decimal("3840.0"),
            close_price=Decimal("3850.0"),
            volume=5000,
            timestamp=datetime.now()
        )

        # 添加到缓存
        market_service.add_kline_to_cache(kline_data)

        # 验证缓存
        cached_data = market_service.get_cached_klines("rb2405", "1m")
        assert len(cached_data) == 1
        assert cached_data[0].symbol == "rb2405"

    @pytest.mark.asyncio
    async def test_redis_cache_integration(self, market_service, mock_redis):
        """测试Redis缓存集成"""
        with patch('app.core.cache.get_redis', return_value=mock_redis):
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=1000,
                timestamp=datetime.now()
            )

            # 缓存到Redis
            await market_service.cache_tick_to_redis(tick_data)

            # 验证Redis操作
            mock_redis.set.assert_called_once()
            mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_retrieval(self, market_service, mock_redis):
        """测试缓存数据检索"""
        # 模拟Redis返回数据
        cached_data = {
            "symbol": "rb2405",
            "last_price": "3850.0",
            "volume": 1000,
            "timestamp": datetime.now().isoformat()
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        with patch('app.core.cache.get_redis', return_value=mock_redis):
            # 从缓存获取数据
            result = await market_service.get_tick_from_redis("rb2405")

            # 验证检索结果
            assert result is not None
            assert result["symbol"] == "rb2405"

    @pytest.mark.asyncio
    async def test_cache_expiration(self, market_service, mock_redis):
        """测试缓存过期机制"""
        with patch('app.core.cache.get_redis', return_value=mock_redis):
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=1000,
                timestamp=datetime.now()
            )

            # 设置缓存
            await market_service.cache_tick_to_redis(tick_data, expire_seconds=10)

            # 验证过期时间设置
            mock_redis.expire.assert_called_with("tick:rb2405", 10)


class TestMarketDataWebSocket:
    """行情数据WebSocket推送测试"""

    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.fixture
    def mock_websocket(self):
        """模拟WebSocket连接"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    @pytest.mark.asyncio
    async def test_websocket_client_management(self, market_service, mock_websocket):
        """测试WebSocket客户端管理"""
        client_id = "test_client_001"

        # 添加客户端
        market_service.add_client(client_id, mock_websocket)

        # 验证客户端添加
        assert client_id in market_service.clients
        assert market_service.clients[client_id] == mock_websocket

    @pytest.mark.asyncio
    async def test_websocket_subscription(self, market_service, mock_websocket):
        """测试WebSocket订阅管理"""
        client_id = "test_client_001"
        symbols = ["rb2405", "hc2405"]

        # 添加客户端
        market_service.add_client(client_id, mock_websocket)

        # 订阅合约
        market_service.subscribe_client_symbols(client_id, symbols)

        # 验证订阅
        subscribed = market_service.get_client_subscriptions(client_id)
        assert subscribed == set(symbols)

    @pytest.mark.asyncio
    async def test_websocket_data_push(self, market_service, mock_websocket):
        """测试WebSocket数据推送"""
        client_id = "test_client_001"

        # 添加客户端并订阅
        market_service.add_client(client_id, mock_websocket)
        market_service.subscribe_client_symbols(client_id, ["rb2405"])

        # 创建行情数据
        tick_data = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now()
        )

        # 推送数据
        await market_service.broadcast_tick_data(tick_data)

        # 验证推送
        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_selective_push(self, market_service):
        """测试WebSocket选择性推送"""
        # 创建多个客户端
        clients = {}
        for i in range(3):
            client_id = f"client_{i}"
            mock_ws = AsyncMock()
            clients[client_id] = mock_ws
            market_service.add_client(client_id, mock_ws)

        # 不同客户端订阅不同合约
        market_service.subscribe_client_symbols("client_0", ["rb2405"])
        market_service.subscribe_client_symbols("client_1", ["hc2405"])
        market_service.subscribe_client_symbols("client_2", ["rb2405", "hc2405"])

        # 推送rb2405数据
        tick_data = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now()
        )

        await market_service.broadcast_tick_data(tick_data)

        # 验证选择性推送
        clients["client_0"]["send_json"].assert_called_once()  # 订阅了rb2405
        clients["client_1"]["send_json"].assert_not_called()   # 没有订阅rb2405
        clients["client_2"]["send_json"].assert_called_once()  # 订阅了rb2405

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, market_service, mock_websocket):
        """测试WebSocket错误处理"""
        client_id = "test_client_001"

        # 模拟发送错误
        mock_websocket.send_json.side_effect = Exception("Connection lost")

        # 添加客户端
        market_service.add_client(client_id, mock_websocket)
        market_service.subscribe_client_symbols(client_id, ["rb2405"])

        # 推送数据
        tick_data = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now()
        )

        # 推送应该处理错误
        await market_service.broadcast_tick_data(tick_data)

        # 验证错误处理（客户端应该被移除）
        assert client_id not in market_service.clients

    @pytest.mark.asyncio
    async def test_websocket_client_cleanup(self, market_service, mock_websocket):
        """测试WebSocket客户端清理"""
        client_id = "test_client_001"

        # 添加客户端并订阅
        market_service.add_client(client_id, mock_websocket)
        market_service.subscribe_client_symbols(client_id, ["rb2405"])

        # 移除客户端
        market_service.remove_client(client_id)

        # 验证清理
        assert client_id not in market_service.clients
        assert client_id not in market_service.client_subscriptions


class TestMarketDataPerformance:
    """行情数据性能测试"""

    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.mark.asyncio
    async def test_high_frequency_data_processing(self, market_service):
        """测试高频数据处理性能"""
        # 创建高频数据
        tick_count = 10000
        symbols = [f"rb240{i % 10}" for i in range(10)]

        start_time = datetime.now()

        # 处理高频数据
        for i in range(tick_count):
            tick_data = TickData(
                symbol=symbols[i % len(symbols)],
                exchange="SHFE",
                last_price=Decimal(f"{3850 + (i % 100)}"),
                volume=1000 + i,
                timestamp=datetime.now()
            )
            await market_service.process_tick_data(tick_data)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证性能指标
        throughput = tick_count / processing_time
        assert throughput > 1000  # 每秒处理超过1000条数据
        assert processing_time < 10  # 总处理时间小于10秒

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, market_service):
        """测试内存使用优化"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # 处理大量数据
        for i in range(5000):
            tick_data = TickData(
                symbol=f"rb240{i % 5}",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=1000 + i,
                timestamp=datetime.now()
            )
            await market_service.process_tick_data(tick_data)

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # 验证内存使用合理
        assert memory_increase < 100  # 内存增长小于100MB

    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, market_service):
        """测试并发处理性能"""
        async def process_symbol_data(symbol, count):
            for i in range(count):
                tick_data = TickData(
                    symbol=symbol,
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i}"),
                    volume=1000 + i,
                    timestamp=datetime.now()
                )
                await market_service.process_tick_data(tick_data)

        # 并发处理多个合约
        symbols = [f"rb240{i}" for i in range(10)]
        start_time = datetime.now()

        tasks = [process_symbol_data(symbol, 500) for symbol in symbols]
        await asyncio.gather(*tasks)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证并发性能
        total_ticks = len(symbols) * 500
        throughput = total_ticks / processing_time
        assert throughput > 2000  # 并发处理提升性能

    @pytest.mark.asyncio
    async def test_cache_performance(self, market_service):
        """测试缓存性能"""
        symbol = "rb2405"

        # 预填充缓存
        for i in range(1000):
            tick_data = TickData(
                symbol=symbol,
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=1000 + i,
                timestamp=datetime.now()
            )
            market_service.add_tick_to_cache(tick_data)

        # 测试缓存检索性能
        start_time = datetime.now()

        for _ in range(1000):
            cached_data = market_service.get_cached_ticks(symbol)
            assert len(cached_data) > 0

        end_time = datetime.now()
        retrieval_time = (end_time - start_time).total_seconds()

        # 验证缓存性能
        assert retrieval_time < 0.1  # 1000次检索小于0.1秒


class TestMarketDataIntegration:
    """行情数据集成测试"""

    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self, market_service):
        """测试端到端数据流"""
        # 模拟完整数据流：接收 -> 清洗 -> 存储 -> 缓存 -> 推送

        # 1. 数据接收
        tick_data = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=1000,
            timestamp=datetime.now()
        )

        # 2. 添加回调验证数据流
        processed_data = []
        stored_data = []
        cached_data = []
        pushed_data = []

        def on_tick_processed(data):
            processed_data.append(data)

        def on_tick_stored(data):
            stored_data.append(data)

        def on_tick_cached(data):
            cached_data.append(data)

        def on_tick_pushed(data):
            pushed_data.append(data)

        market_service.add_tick_callback(on_tick_processed)

        # 3. 处理数据
        with patch.object(market_service, 'store_tick_data') as mock_store:
            with patch.object(market_service, 'cache_tick_to_redis') as mock_cache:
                with patch.object(market_service, 'broadcast_tick_data') as mock_push:

                    await market_service.process_tick_data(tick_data)

                    # 验证数据流各个环节
                    assert len(processed_data) == 1
                    mock_store.assert_called_once()
                    mock_cache.assert_called_once()
                    mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_symbol_integration(self, market_service):
        """测试多合约集成处理"""
        symbols = ["rb2405", "hc2405", "i2405", "j2405", "jm2405"]

        # 模拟多合约数据同时到达
        tasks = []
        for symbol in symbols:
            for i in range(10):
                tick_data = TickData(
                    symbol=symbol,
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i}"),
                    volume=1000 + i,
                    timestamp=datetime.now()
                )
                tasks.append(market_service.process_tick_data(tick_data))

        # 并发处理
        await asyncio.gather(*tasks)

        # 验证处理结果
        assert market_service.stats["tick_count"] == len(symbols) * 10

        # 验证每个合约都有缓存数据
        for symbol in symbols:
            cached_ticks = market_service.get_cached_ticks(symbol)
            assert len(cached_ticks) == 10

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, market_service):
        """测试错误恢复集成"""
        # 模拟各种错误场景

        # 1. 数据库错误
        with patch('app.core.database.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.commit.side_effect = Exception("Database error")
            mock_get_db.return_value.__aenter__.return_value = mock_session

            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=1000,
                timestamp=datetime.now()
            )

            # 处理应该继续，即使存储失败
            try:
                await market_service.process_tick_data(tick_data)
            except Exception:
                pass  # 错误应该被处理

            # 验证错误统计
            assert market_service.stats["error_count"] > 0

    @pytest.mark.asyncio
    async def test_real_time_latency(self, market_service):
        """测试实时延迟"""
        # 模拟实时数据处理延迟测试
        latencies = []

        async def measure_latency():
            start_time = datetime.now()

            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=1000,
                timestamp=start_time
            )

            await market_service.process_tick_data(tick_data)

            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000  # 毫秒
            latencies.append(latency)

        # 测试100次延迟
        for _ in range(100):
            await measure_latency()

        # 验证延迟指标
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        assert avg_latency < 10  # 平均延迟小于10毫秒
        assert max_latency < 50  # 最大延迟小于50毫秒
