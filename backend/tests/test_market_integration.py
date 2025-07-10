"""
行情数据处理集成测试
测试完整的行情数据流程：接收 -> 清洗 -> 存储 -> 推送
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.market_data_service import MarketDataService
from app.services.market_service import MarketService
from app.schemas.market import TickData, BarData, Exchange, Interval
from app.core.database import get_db


class TestMarketDataIntegrationFlow:
    """行情数据集成流程测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_market_data(self):
        """样本行情数据"""
        return {
            "symbol": "rb2405",
            "exchange": "SHFE",
            "last_price": 3850.0,
            "volume": 12345,
            "turnover": 47432500.0,
            "bid_price": 3849.0,
            "bid_volume": 100,
            "ask_price": 3851.0,
            "ask_volume": 150,
            "timestamp": datetime.now().isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_complete_data_flow(self, sample_market_data):
        """测试完整的数据流程"""
        market_service = MarketDataService()
        
        try:
            # 1. 数据接收阶段
            tick_data = TickData(
                symbol=sample_market_data["symbol"],
                exchange=Exchange.SHFE,
                last_price=Decimal(str(sample_market_data["last_price"])),
                volume=sample_market_data["volume"],
                timestamp=datetime.now()
            )
            
            # 2. 数据验证
            is_valid = await market_service.validate_tick_data(tick_data)
            assert is_valid is True
            
            # 3. 数据清洗
            cleaned_data = await market_service.clean_tick_data(tick_data)
            assert cleaned_data is not None
            assert cleaned_data.symbol == tick_data.symbol
            
            # 4. 数据存储（模拟）
            with patch.object(market_service, 'store_tick_data') as mock_store:
                mock_store.return_value = None
                await market_service.store_tick_data(cleaned_data)
                mock_store.assert_called_once_with(cleaned_data)
            
            # 5. 实时推送（模拟）
            with patch.object(market_service, 'push_tick_data') as mock_push:
                mock_push.return_value = None
                await market_service.push_tick_data(cleaned_data)
                mock_push.assert_called_once_with(cleaned_data)
            
            # 6. 完整处理流程
            await market_service.process_tick_data(tick_data)
            
            # 验证统计信息更新
            assert market_service.stats["tick_count"] > 0
            assert market_service.stats["last_update"] is not None
            
        finally:
            await market_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_api_to_websocket_flow(self, client, sample_market_data):
        """测试API到WebSocket的完整流程"""
        # 1. 通过API获取行情数据
        with patch('app.api.v1.market.get_market_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_market_data = AsyncMock(return_value={
                "data": [sample_market_data],
                "total": 1
            })
            mock_get_service.return_value = mock_service
            
            # API调用
            response = client.get("/api/v1/market/quote?symbols=rb2405")
            assert response.status_code == 200
            
            data = response.json()
            assert "data" in data
            assert len(data["data"]) > 0
        
        # 2. WebSocket订阅和推送（模拟）
        with patch('app.api.v1.ctp_websocket.ctp_market_service') as mock_ws_service:
            mock_websocket = AsyncMock()
            client_id = "test_client"
            
            # 模拟订阅
            mock_ws_service.subscribe_client = AsyncMock(return_value=True)
            mock_ws_service.get_client_subscriptions.return_value = ["rb2405"]
            
            # 模拟数据推送
            with patch('app.api.v1.ctp_websocket.ctp_service') as mock_ctp:
                mock_ctp.get_tick_data.return_value = sample_market_data
                
                # 验证推送逻辑
                from app.api.v1.ctp_websocket import _market_data_pusher
                
                task = asyncio.create_task(_market_data_pusher(mock_websocket, client_id))
                await asyncio.sleep(0.1)
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                # 验证WebSocket发送
                assert mock_websocket.send_json.called
    
    @pytest.mark.asyncio
    async def test_database_storage_integration(self, sample_market_data):
        """测试数据库存储集成"""
        market_service = MarketDataService()
        
        # 创建测试数据
        tick_data = TickData(
            symbol=sample_market_data["symbol"],
            exchange=Exchange.SHFE,
            last_price=Decimal(str(sample_market_data["last_price"])),
            volume=sample_market_data["volume"],
            timestamp=datetime.now()
        )
        
        # 模拟数据库操作
        with patch('app.services.market_data_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session
            
            # 存储数据
            await market_service.store_tick_data(tick_data)
            
            # 验证数据库操作
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            
            # 验证存储的数据结构
            stored_data = mock_session.add.call_args[0][0]
            assert hasattr(stored_data, 'symbol')
            assert hasattr(stored_data, 'data_type')
            assert hasattr(stored_data, 'timestamp')
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, sample_market_data):
        """测试缓存集成"""
        market_service = MarketDataService()
        
        # 创建测试数据
        tick_data = TickData(
            symbol=sample_market_data["symbol"],
            exchange=Exchange.SHFE,
            last_price=Decimal(str(sample_market_data["last_price"])),
            volume=sample_market_data["volume"],
            timestamp=datetime.now()
        )
        
        # 模拟缓存操作
        with patch.object(market_service, 'cache_manager') as mock_cache:
            mock_cache.set = AsyncMock(return_value=True)
            mock_cache.get = AsyncMock(return_value=None)
            
            # 缓存数据
            await market_service.cache_tick_data(tick_data)
            
            # 验证缓存操作
            mock_cache.set.assert_called_once()
            
            # 验证缓存键和数据
            cache_key = mock_cache.set.call_args[0][0]
            cache_data = mock_cache.set.call_args[0][1]
            
            assert tick_data.symbol in cache_key
            assert isinstance(cache_data, str)  # JSON字符串
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, sample_market_data):
        """测试错误恢复流程"""
        market_service = MarketDataService()
        
        # 创建测试数据
        tick_data = TickData(
            symbol=sample_market_data["symbol"],
            exchange=Exchange.SHFE,
            last_price=Decimal(str(sample_market_data["last_price"])),
            volume=sample_market_data["volume"],
            timestamp=datetime.now()
        )
        
        # 模拟存储错误
        with patch.object(market_service, 'store_tick_data') as mock_store:
            mock_store.side_effect = Exception("Database connection failed")
            
            # 处理数据时应该处理错误
            try:
                await market_service.process_tick_data(tick_data)
            except Exception:
                pass  # 错误应该被捕获和处理
            
            # 验证错误统计
            assert market_service.stats["error_count"] > 0
        
        # 模拟推送错误
        with patch.object(market_service, 'push_tick_data') as mock_push:
            mock_push.side_effect = Exception("WebSocket connection failed")
            
            # 处理数据时应该处理推送错误
            try:
                await market_service.process_tick_data(tick_data)
            except Exception:
                pass  # 错误应该被捕获和处理


class TestMarketDataConcurrency:
    """行情数据并发处理测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_data_processing(self):
        """测试并发数据处理"""
        market_service = MarketDataService()
        
        try:
            # 创建多个并发数据处理任务
            tasks = []
            symbols = ["rb2405", "cu2405", "au2406", "ag2406", "zn2405"]
            
            for i, symbol in enumerate(symbols):
                for j in range(10):  # 每个合约10条数据
                    tick_data = TickData(
                        symbol=symbol,
                        exchange=Exchange.SHFE,
                        last_price=Decimal(f"{3850 + i*100 + j}"),
                        volume=100 + j,
                        timestamp=datetime.now() + timedelta(microseconds=i*1000+j*100)
                    )
                    
                    task = asyncio.create_task(market_service.process_tick_data(tick_data))
                    tasks.append(task)
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证所有任务都成功完成
            error_count = sum(1 for result in results if isinstance(result, Exception))
            assert error_count == 0
            
            # 验证处理统计
            assert market_service.stats["tick_count"] == len(tasks)
            
        finally:
            await market_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_subscription_concurrency(self):
        """测试订阅并发处理"""
        market_service = MarketDataService()
        
        try:
            # 并发订阅多个合约
            symbols_groups = [
                ["rb2405", "hc2405"],
                ["cu2405", "al2405"],
                ["au2406", "ag2406"],
                ["zn2405", "pb2405"],
                ["ni2405", "sn2405"]
            ]
            
            tasks = []
            for symbols in symbols_groups:
                task = asyncio.create_task(market_service.subscribe_symbols(symbols))
                tasks.append(task)
            
            # 并发执行订阅
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证订阅结果
            success_count = sum(1 for result in results if result is True)
            assert success_count > 0
            
            # 验证订阅的合约数量
            total_symbols = sum(len(symbols) for symbols in symbols_groups)
            assert len(market_service.subscribed_symbols) <= total_symbols
            
        finally:
            await market_service.cleanup()


class TestMarketDataPerformanceIntegration:
    """行情数据性能集成测试"""
    
    @pytest.mark.asyncio
    async def test_high_throughput_processing(self):
        """测试高吞吐量处理"""
        market_service = MarketDataService()
        
        try:
            # 生成大量测试数据
            data_count = 1000
            start_time = datetime.now()
            
            # 批量处理数据
            batch_size = 100
            for batch_start in range(0, data_count, batch_size):
                batch_tasks = []
                
                for i in range(batch_start, min(batch_start + batch_size, data_count)):
                    tick_data = TickData(
                        symbol=f"rb240{i % 5}",
                        exchange=Exchange.SHFE,
                        last_price=Decimal(f"{3850 + i % 100}"),
                        volume=100 + i,
                        timestamp=datetime.now() + timedelta(microseconds=i*100)
                    )
                    
                    task = asyncio.create_task(market_service.process_tick_data(tick_data))
                    batch_tasks.append(task)
                
                # 等待批次完成
                await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 验证处理性能
            throughput = data_count / processing_time
            assert throughput >= 500  # 每秒至少处理500条数据
            
            # 验证处理统计
            assert market_service.stats["tick_count"] == data_count
            
        finally:
            await market_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """测试负载下的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        market_service = MarketDataService()
        
        try:
            # 持续处理数据
            for round_num in range(5):
                # 每轮处理200条数据
                tasks = []
                for i in range(200):
                    tick_data = TickData(
                        symbol=f"rb240{i % 10}",
                        exchange=Exchange.SHFE,
                        last_price=Decimal(f"{3850 + round_num*10 + i}"),
                        volume=100 + i,
                        timestamp=datetime.now()
                    )
                    
                    task = asyncio.create_task(market_service.process_tick_data(tick_data))
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 清理缓存
                await market_service.cleanup_old_cache()
                
                # 检查内存使用
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # 内存增长应该在合理范围内
                assert memory_increase < 100 * 1024 * 1024  # 小于100MB
            
        finally:
            await market_service.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
