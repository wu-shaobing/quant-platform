"""
行情数据集成测试
测试行情数据处理的完整流程和系统集成
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.market_data_service import MarketDataService
from app.schemas.market_data import TickData, KlineData, MarketDepth
from app.models.market import MarketData, KlineData as KlineModel, DepthData
from app.core.database import get_db
from app.core.cache import get_redis
from app.api.v1.ctp_websocket import CTPWebSocketManager

from tests.utils.market_data_generator import MarketDataGenerator, create_test_tick_data


class TestMarketDataEndToEnd:
    """端到端行情数据处理测试"""
    
    @pytest.fixture
    async def market_service(self):
        """创建行情数据服务实例"""
        service = MarketDataService()
        yield service
        await service.cleanup()
    
    @pytest.fixture
    def mock_database(self):
        """模拟数据库"""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        return mock_session
    
    @pytest.fixture
    def mock_redis(self):
        """模拟Redis"""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.publish = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.expire = AsyncMock()
        return mock_redis

    @pytest.mark.asyncio
    async def test_complete_data_pipeline(self, market_service, mock_database, mock_redis):
        """测试完整的数据处理管道"""
        # 模拟数据库和Redis
        with patch('app.core.database.get_db') as mock_get_db:
            with patch('app.core.cache.get_redis', return_value=mock_redis):
                mock_get_db.return_value.__aenter__.return_value = mock_database
                
                # 创建测试数据
                generator = MarketDataGenerator()
                test_ticks = list(generator.generate_tick_stream("rb2405", 10))
                
                # 添加数据处理回调
                processed_ticks = []
                
                def on_tick_processed(tick_data):
                    processed_ticks.append(tick_data)
                
                market_service.add_tick_callback(on_tick_processed)
                
                # 处理数据流
                for tick_data in test_ticks:
                    await market_service.process_tick_data(tick_data)
                
                # 验证数据处理
                assert len(processed_ticks) == len(test_ticks)
                
                # 验证数据库存储
                assert mock_database.add.call_count == len(test_ticks)
                assert mock_database.commit.call_count == len(test_ticks)
                
                # 验证Redis缓存
                assert mock_redis.set.call_count >= len(test_ticks)

    @pytest.mark.asyncio
    async def test_websocket_integration(self, market_service):
        """测试WebSocket集成"""
        # 创建模拟WebSocket客户端
        mock_clients = {}
        for i in range(5):
            client_id = f"client_{i}"
            mock_ws = AsyncMock()
            mock_clients[client_id] = mock_ws
            market_service.add_client(client_id, mock_ws)
            market_service.subscribe_client_symbols(client_id, ["rb2405", "hc2405"])
        
        # 生成测试数据
        generator = MarketDataGenerator()
        test_symbols = ["rb2405", "hc2405", "i2405"]
        
        for symbol in test_symbols:
            tick_data = generator.generate_tick_data(symbol)
            await market_service.broadcast_tick_data(tick_data)
        
        # 验证WebSocket推送
        for client_id, mock_ws in mock_clients.items():
            # 每个客户端应该收到rb2405和hc2405的数据，但不包括i2405
            call_count = mock_ws.send_json.call_count
            assert call_count == 2  # rb2405 + hc2405

    @pytest.mark.asyncio
    async def test_ctp_websocket_integration(self, market_service):
        """测试CTP WebSocket集成"""
        # 创建CTP WebSocket管理器
        ctp_manager = CTPWebSocketManager()
        
        # 模拟CTP连接
        with patch.object(ctp_manager, 'connect_ctp') as mock_connect:
            with patch.object(ctp_manager, 'subscribe_market_data') as mock_subscribe:
                mock_connect.return_value = True
                mock_subscribe.return_value = True
                
                # 连接CTP
                connected = await ctp_manager.connect_ctp()
                assert connected
                
                # 订阅行情
                symbols = ["rb2405", "hc2405"]
                subscribed = await ctp_manager.subscribe_market_data(symbols)
                assert subscribed
                
                # 模拟接收CTP数据
                ctp_tick_data = {
                    "InstrumentID": "rb2405",
                    "LastPrice": 3850.0,
                    "Volume": 12345,
                    "Turnover": 47432500.0,
                    "BidPrice1": 3849.0,
                    "AskPrice1": 3851.0,
                    "BidVolume1": 100,
                    "AskVolume1": 150,
                    "UpdateTime": "09:30:00",
                    "UpdateMillisec": 500
                }
                
                # 处理CTP数据
                await ctp_manager._on_tick_callback(ctp_tick_data)
                
                # 验证数据转换和处理
                assert market_service.stats["tick_count"] > 0

    @pytest.mark.asyncio
    async def test_multi_exchange_data_handling(self, market_service):
        """测试多交易所数据处理"""
        # 创建不同交易所的数据
        generator = MarketDataGenerator()
        
        # 上期所数据
        shfe_symbols = ["rb2405", "cu2405", "au2406"]
        # 大商所数据
        dce_symbols = ["i2405", "j2405", "c2405"]
        # 郑商所数据
        czce_symbols = ["MA2405", "TA2405", "PF2405"]
        
        all_symbols = shfe_symbols + dce_symbols + czce_symbols
        processed_data = {}
        
        # 处理各交易所数据
        for symbol in all_symbols:
            tick_data = generator.generate_tick_data(symbol)
            await market_service.process_tick_data(tick_data)
            processed_data[symbol] = tick_data
        
        # 验证不同交易所数据都被正确处理
        assert len(processed_data) == len(all_symbols)
        
        # 验证交易所分类
        for symbol in shfe_symbols:
            assert processed_data[symbol].exchange == "SHFE"
        for symbol in dce_symbols:
            assert processed_data[symbol].exchange == "DCE"
        for symbol in czce_symbols:
            assert processed_data[symbol].exchange == "CZCE"

    @pytest.mark.asyncio
    async def test_data_consistency_across_components(self, market_service, mock_database, mock_redis):
        """测试组件间数据一致性"""
        with patch('app.core.database.get_db') as mock_get_db:
            with patch('app.core.cache.get_redis', return_value=mock_redis):
                mock_get_db.return_value.__aenter__.return_value = mock_database
                
                # 创建测试数据
                generator = MarketDataGenerator()
                tick_data = generator.generate_tick_data("rb2405")
                
                # 处理数据
                await market_service.process_tick_data(tick_data)
                
                # 验证数据库存储的数据
                db_call_args = mock_database.add.call_args[0][0]
                assert isinstance(db_call_args, MarketData)
                assert db_call_args.symbol == tick_data.symbol
                assert db_call_args.last_price == tick_data.last_price
                
                # 验证Redis缓存的数据
                redis_call_args = mock_redis.set.call_args
                cached_key = redis_call_args[0][0]
                cached_data = json.loads(redis_call_args[0][1])
                
                assert "tick:" in cached_key
                assert cached_data["symbol"] == tick_data.symbol
                assert Decimal(cached_data["last_price"]) == tick_data.last_price

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, market_service):
        """测试集成环境下的错误处理"""
        # 模拟数据库连接错误
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            generator = MarketDataGenerator()
            tick_data = generator.generate_tick_data("rb2405")
            
            # 处理应该继续，即使数据库失败
            try:
                await market_service.process_tick_data(tick_data)
            except Exception as e:
                # 错误应该被记录但不应该中断处理
                assert "Database connection failed" in str(e)
            
            # 验证错误统计
            assert market_service.stats["error_count"] > 0

    @pytest.mark.asyncio
    async def test_performance_under_realistic_load(self, market_service):
        """测试真实负载下的性能"""
        # 模拟真实交易时段的数据量
        generator = MarketDataGenerator()
        symbols = ["rb2405", "hc2405", "i2405", "j2405", "cu2405"]
        
        # 生成1小时的交易数据
        all_ticks = generator.generate_realistic_trading_session(symbols, 60)
        
        # 添加多个WebSocket客户端
        for i in range(10):
            client_id = f"client_{i}"
            mock_ws = AsyncMock()
            market_service.add_client(client_id, mock_ws)
            market_service.subscribe_client_symbols(client_id, symbols)
        
        # 处理数据
        start_time = datetime.now()
        
        with patch('app.core.database.get_db') as mock_get_db:
            with patch('app.core.cache.get_redis') as mock_get_redis:
                mock_session = AsyncMock()
                mock_redis = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_session
                mock_get_redis.return_value = mock_redis
                
                for tick_data in all_ticks:
                    await market_service.process_tick_data(tick_data)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 性能验证
        throughput = len(all_ticks) / processing_time
        print(f"处理 {len(all_ticks)} 条真实负载数据，耗时 {processing_time:.2f} 秒")
        print(f"吞吐量: {throughput:.0f} 条/秒")
        
        assert throughput > 1000  # 应该能处理每秒1000条以上
        assert processing_time < 60  # 1小时数据应在1分钟内处理完

    @pytest.mark.asyncio
    async def test_data_recovery_after_failure(self, market_service):
        """测试故障后的数据恢复"""
        generator = MarketDataGenerator()
        
        # 正常处理一些数据
        for i in range(10):
            tick_data = generator.generate_tick_data("rb2405")
            await market_service.process_tick_data(tick_data)
        
        initial_count = market_service.stats["tick_count"]
        
        # 模拟系统故障
        with patch.object(market_service, 'store_tick_data') as mock_store:
            mock_store.side_effect = Exception("System failure")
            
            # 尝试处理更多数据（应该失败）
            for i in range(5):
                tick_data = generator.generate_tick_data("rb2405")
                try:
                    await market_service.process_tick_data(tick_data)
                except Exception:
                    pass  # 预期的错误
        
        # 恢复正常
        # 继续处理数据
        for i in range(10):
            tick_data = generator.generate_tick_data("rb2405")
            await market_service.process_tick_data(tick_data)
        
        # 验证恢复后的处理
        final_count = market_service.stats["tick_count"]
        assert final_count > initial_count  # 应该继续增长

    @pytest.mark.asyncio
    async def test_concurrent_client_management(self, market_service):
        """测试并发客户端管理"""
        # 并发添加客户端
        async def add_clients(start_idx, count):
            for i in range(count):
                client_id = f"client_{start_idx + i}"
                mock_ws = AsyncMock()
                market_service.add_client(client_id, mock_ws)
                market_service.subscribe_client_symbols(client_id, ["rb2405"])
        
        # 并发添加100个客户端
        tasks = [add_clients(i * 20, 20) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # 验证客户端数量
        assert len(market_service.clients) == 100
        
        # 并发广播数据
        generator = MarketDataGenerator()
        broadcast_tasks = []
        
        for i in range(10):
            tick_data = generator.generate_tick_data("rb2405")
            task = market_service.broadcast_tick_data(tick_data)
            broadcast_tasks.append(task)
        
        await asyncio.gather(*broadcast_tasks)
        
        # 验证所有客户端都收到了数据
        for client_id, mock_ws in market_service.clients.items():
            assert mock_ws.send_json.call_count > 0
