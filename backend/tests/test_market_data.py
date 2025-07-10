"""
行情数据处理测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
import json

from app.services.market_data_service import MarketDataService
from app.models.market_data import MarketData, Instrument
from app.schemas.market_data import TickData, KlineData, MarketDepth
from app.core.database import get_db


class TestMarketDataService:
    """行情数据服务测试"""
    
    @pytest.fixture
    async def market_service(self):
        """创建行情数据服务实例"""
        service = MarketDataService()
        yield service
        await service.cleanup()
    
    @pytest.fixture
    def sample_tick_data(self):
        """示例Tick数据"""
        return TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("3850.0"),
            volume=12345,
            turnover=Decimal("47432500.0"),
            open_interest=98765,
            bid_price_1=Decimal("3849.0"),
            bid_volume_1=100,
            ask_price_1=Decimal("3851.0"),
            ask_volume_1=150,
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
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, market_service, sample_tick_data):
        """测试订阅行情数据"""
        # 模拟订阅
        symbols = ["rb2405", "hc2405"]
        result = await market_service.subscribe_symbols(symbols)
        
        assert result is True
        assert market_service.subscribed_symbols == set(symbols)
    
    @pytest.mark.asyncio
    async def test_unsubscribe_market_data(self, market_service):
        """测试取消订阅行情数据"""
        # 先订阅
        symbols = ["rb2405", "hc2405"]
        await market_service.subscribe_symbols(symbols)
        
        # 取消订阅
        result = await market_service.unsubscribe_symbols(["rb2405"])
        
        assert result is True
        assert market_service.subscribed_symbols == {"hc2405"}
    
    @pytest.mark.asyncio
    async def test_process_tick_data(self, market_service, sample_tick_data):
        """测试处理Tick数据"""
        # 模拟数据处理回调
        processed_data = []
        
        def on_tick(data):
            processed_data.append(data)
        
        market_service.add_tick_callback(on_tick)
        
        # 处理Tick数据
        await market_service.process_tick_data(sample_tick_data)
        
        assert len(processed_data) == 1
        assert processed_data[0].symbol == sample_tick_data.symbol
        assert processed_data[0].last_price == sample_tick_data.last_price
    
    @pytest.mark.asyncio
    async def test_data_validation(self, market_service):
        """测试数据验证"""
        # 无效的Tick数据
        invalid_tick = TickData(
            symbol="",  # 空符号
            exchange="SHFE",
            last_price=Decimal("-100.0"),  # 负价格
            volume=-1,  # 负成交量
            timestamp=datetime.now()
        )
        
        with pytest.raises(ValueError):
            await market_service.validate_tick_data(invalid_tick)
    
    @pytest.mark.asyncio
    async def test_data_storage(self, market_service, sample_tick_data):
        """测试数据存储"""
        with patch('app.core.database.get_db') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # 存储Tick数据
            await market_service.store_tick_data(sample_tick_data)
            
            # 验证数据库操作
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_real_time_push(self, market_service, sample_tick_data):
        """测试实时数据推送"""
        # 模拟WebSocket连接
        mock_websocket = AsyncMock()
        client_id = "test_client_1"
        
        # 添加客户端
        market_service.add_client(client_id, mock_websocket)
        
        # 订阅数据
        await market_service.subscribe_client(client_id, ["rb2405"])
        
        # 推送数据
        await market_service.push_tick_data(sample_tick_data)
        
        # 验证推送
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "tick"
        assert sent_data["data"]["symbol"] == sample_tick_data.symbol
    
    @pytest.mark.asyncio
    async def test_data_cleaning(self, market_service):
        """测试数据清洗"""
        # 异常数据
        dirty_tick = TickData(
            symbol="rb2405",
            exchange="SHFE",
            last_price=Decimal("0.0"),  # 异常价格
            volume=0,
            timestamp=datetime.now()
        )
        
        # 清洗数据
        cleaned_data = await market_service.clean_tick_data(dirty_tick)
        
        # 验证清洗结果
        assert cleaned_data is None or cleaned_data.last_price > 0
    
    @pytest.mark.asyncio
    async def test_kline_generation(self, market_service, sample_tick_data):
        """测试K线生成"""
        # 模拟多个Tick数据
        ticks = []
        base_time = datetime.now().replace(second=0, microsecond=0)
        
        for i in range(10):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=100 * (i + 1),
                timestamp=base_time + timedelta(seconds=i * 6)
            )
            ticks.append(tick)
        
        # 生成K线
        klines = await market_service.generate_klines(ticks, "1m")
        
        assert len(klines) > 0
        assert klines[0].symbol == "rb2405"
        assert klines[0].interval == "1m"
    
    @pytest.mark.asyncio
    async def test_market_depth_processing(self, market_service):
        """测试市场深度数据处理"""
        depth_data = MarketDepth(
            symbol="rb2405",
            exchange="SHFE",
            bids=[
                {"price": Decimal("3849.0"), "volume": 100},
                {"price": Decimal("3848.0"), "volume": 200},
            ],
            asks=[
                {"price": Decimal("3851.0"), "volume": 150},
                {"price": Decimal("3852.0"), "volume": 250},
            ],
            timestamp=datetime.now()
        )
        
        # 处理深度数据
        result = await market_service.process_market_depth(depth_data)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_data_compression(self, market_service, sample_tick_data):
        """测试数据压缩"""
        # 生成大量数据
        tick_data_list = []
        for i in range(1000):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i % 10}"),
                volume=100,
                timestamp=datetime.now() + timedelta(seconds=i)
            )
            tick_data_list.append(tick)
        
        # 压缩数据
        compressed_data = await market_service.compress_tick_data(tick_data_list)
        
        assert len(compressed_data) < len(tick_data_list)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, market_service):
        """测试错误处理"""
        # 模拟网络错误
        with patch.object(market_service, 'ctp_service') as mock_ctp:
            mock_ctp.subscribe_market_data.side_effect = Exception("Network error")
            
            # 订阅应该处理错误
            result = await market_service.subscribe_symbols(["rb2405"])
            assert result is False
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, market_service, sample_tick_data):
        """测试性能监控"""
        # 处理大量数据
        start_time = datetime.now()
        
        for i in range(100):
            await market_service.process_tick_data(sample_tick_data)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 验证处理性能
        assert processing_time < 1.0  # 100条数据应在1秒内处理完成
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, market_service):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 处理大量数据
        for i in range(1000):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=100,
                timestamp=datetime.now()
            )
            await market_service.process_tick_data(tick)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024


class TestMarketDataIntegration:
    """行情数据集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self):
        """测试端到端数据流"""
        market_service = MarketDataService()
        
        try:
            # 1. 订阅行情
            symbols = ["rb2405"]
            await market_service.subscribe_symbols(symbols)
            
            # 2. 模拟接收数据
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=100,
                timestamp=datetime.now()
            )
            
            # 3. 处理数据
            await market_service.process_tick_data(tick_data)
            
            # 4. 验证数据存储
            # 这里应该检查数据库中的数据
            
            # 5. 验证实时推送
            # 这里应该检查WebSocket推送
            
            assert True  # 如果没有异常，测试通过
            
        finally:
            await market_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """测试并发处理"""
        market_service = MarketDataService()
        
        try:
            # 创建多个并发任务
            tasks = []
            for i in range(10):
                tick_data = TickData(
                    symbol=f"rb240{i % 5}",
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i}"),
                    volume=100,
                    timestamp=datetime.now()
                )
                task = asyncio.create_task(market_service.process_tick_data(tick_data))
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证没有异常
            for result in results:
                assert not isinstance(result, Exception)
                
        finally:
            await market_service.cleanup()


class TestMarketDataAPI:
    """行情数据API测试"""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_api(self):
        """测试获取实时行情API"""
        from app.api.v1.market import get_realtime_quote
        from app.services.market_service import MarketService

        # 模拟市场服务
        mock_market_service = Mock(spec=MarketService)
        mock_market_service.get_market_data = AsyncMock(return_value={
            "data": [{
                "symbol": "rb2405",
                "last_price": 3850.0,
                "volume": 12345,
                "timestamp": datetime.now().isoformat()
            }]
        })

        # 测试API调用
        result = await get_realtime_quote(
            symbols="rb2405",
            market_service=mock_market_service
        )

        assert "data" in result
        assert len(result["data"]) > 0
        assert result["data"][0]["symbol"] == "rb2405"

    @pytest.mark.asyncio
    async def test_get_kline_data_api(self):
        """测试获取K线数据API"""
        from app.api.v1.market import get_bar_data
        from app.schemas.market import MarketDataRequest

        # 创建请求对象
        request = MarketDataRequest(
            symbol="rb2405",
            interval="1m",
            limit=100
        )

        # 模拟市场服务
        mock_market_service = Mock()
        mock_market_service.get_bar_data = AsyncMock(return_value=[
            {
                "timestamp": datetime.now(),
                "open": 3845.0,
                "high": 3855.0,
                "low": 3840.0,
                "close": 3850.0,
                "volume": 1000
            }
        ])

        # 测试API调用
        result = await get_bar_data(
            symbol="rb2405",
            request=request,
            market_service=mock_market_service
        )

        assert "data" in result
        assert result["symbol"] == "rb2405"
        assert result["interval"] == "1m"


class TestMarketDataWebSocket:
    """行情数据WebSocket测试"""

    @pytest.mark.asyncio
    async def test_websocket_subscription(self):
        """测试WebSocket订阅"""
        from app.api.v1.ctp_websocket import handle_market_subscription

        # 模拟WebSocket连接
        mock_websocket = AsyncMock()
        mock_websocket.receive_json = AsyncMock(return_value={
            "action": "subscribe",
            "symbols": ["rb2405", "cu2405"]
        })

        # 模拟订阅处理
        with patch('app.api.v1.ctp_websocket.ctp_market_service') as mock_service:
            mock_service.subscribe_client = AsyncMock(return_value=True)

            # 处理订阅请求
            await handle_market_subscription(mock_websocket, "test_client")

            # 验证订阅调用
            mock_service.subscribe_client.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_data_push(self):
        """测试WebSocket数据推送"""
        from app.api.v1.ctp_websocket import _market_data_pusher

        # 模拟WebSocket连接
        mock_websocket = AsyncMock()
        client_id = "test_client_001"

        with patch('app.api.v1.ctp_websocket.ctp_market_service') as mock_market_service:
            with patch('app.api.v1.ctp_websocket.ctp_service') as mock_ctp_service:
                # 模拟订阅数据
                mock_market_service.get_client_subscriptions.return_value = ["rb2405"]
                mock_ctp_service.get_tick_data.return_value = {
                    "symbol": "rb2405",
                    "last_price": 3850.0,
                    "volume": 12345,
                    "timestamp": datetime.now().isoformat()
                }

                # 创建推送任务
                task = asyncio.create_task(_market_data_pusher(mock_websocket, client_id))

                # 运行一小段时间
                await asyncio.sleep(0.1)
                task.cancel()

                try:
                    await task
                except asyncio.CancelledError:
                    pass

                # 验证数据推送
                assert mock_websocket.send_json.called

                # 验证推送的数据格式
                call_args = mock_websocket.send_json.call_args_list
                if call_args:
                    sent_data = call_args[0][0][0]
                    assert "type" in sent_data
                    assert "symbol" in sent_data
                    assert "data" in sent_data


class TestMarketDataCaching:
    """行情数据缓存测试"""

    @pytest.mark.asyncio
    async def test_redis_cache_operations(self):
        """测试Redis缓存操作"""
        from app.services.market_data_service import MarketDataService

        market_service = MarketDataService()

        # 模拟Redis操作
        with patch.object(market_service, 'cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)

            # 测试缓存设置
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal("3850.0"),
                volume=100,
                timestamp=datetime.now()
            )

            await market_service.cache_tick_data(tick_data)

            # 验证缓存操作
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """测试缓存过期"""
        from app.services.market_data_service import MarketDataService

        market_service = MarketDataService()

        # 模拟过期的缓存数据
        with patch.object(market_service, 'cache_manager') as mock_cache:
            # 返回过期数据
            expired_data = {
                "symbol": "rb2405",
                "last_price": 3850.0,
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()
            }
            mock_cache.get = AsyncMock(return_value=json.dumps(expired_data))

            # 获取缓存数据
            result = await market_service.get_cached_tick_data("rb2405")

            # 过期数据应该被忽略
            assert result is None or result["timestamp"] != expired_data["timestamp"]


class TestMarketDataPerformance:
    """行情数据性能测试"""

    @pytest.mark.asyncio
    async def test_high_frequency_data_processing(self):
        """测试高频数据处理性能"""
        from app.services.market_data_service import MarketDataService

        market_service = MarketDataService()

        # 生成大量高频数据
        tick_data_list = []
        for i in range(1000):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + (i % 10)}"),
                volume=100,
                timestamp=datetime.now() + timedelta(microseconds=i*1000)
            )
            tick_data_list.append(tick)

        # 测试处理性能
        start_time = datetime.now()

        # 批量处理数据
        tasks = []
        for tick in tick_data_list:
            task = asyncio.create_task(market_service.process_tick_data(tick))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证处理性能（1000条数据应在2秒内处理完成）
        assert processing_time < 2.0

        # 验证处理速度（每秒至少500条）
        throughput = len(tick_data_list) / processing_time
        assert throughput >= 500

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """测试内存使用效率"""
        import psutil
        import os

        from app.services.market_data_service import MarketDataService

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        market_service = MarketDataService()

        # 处理大量数据
        for batch in range(10):
            tick_data_list = []
            for i in range(100):
                tick = TickData(
                    symbol=f"rb240{i % 5}",
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i}"),
                    volume=100,
                    timestamp=datetime.now()
                )
                tick_data_list.append(tick)

            # 批量处理
            for tick in tick_data_list:
                await market_service.process_tick_data(tick)

            # 清理缓存
            await market_service.cleanup_old_cache()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（小于50MB）
        assert memory_increase < 50 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
