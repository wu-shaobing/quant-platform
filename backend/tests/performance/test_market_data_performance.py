"""
行情数据处理性能测试
专门测试高频数据处理、并发性能和系统负载
"""
import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import concurrent.futures
from typing import List, Dict

from app.services.market_data_service import MarketDataService
from app.schemas.market_data import TickData, KlineData, MarketDepth


class TestMarketDataThroughput:
    """行情数据吞吐量测试"""
    
    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.mark.asyncio
    async def test_tick_processing_throughput(self, market_service):
        """测试Tick数据处理吞吐量"""
        tick_count = 50000
        symbols = [f"rb240{i}" for i in range(1, 13)]  # 12个合约
        
        # 生成测试数据
        test_data = []
        for i in range(tick_count):
            tick_data = TickData(
                symbol=symbols[i % len(symbols)],
                exchange="SHFE",
                last_price=Decimal(f"{3850 + (i % 1000) * 0.1}"),
                bid_price_1=Decimal(f"{3849 + (i % 1000) * 0.1}"),
                ask_price_1=Decimal(f"{3851 + (i % 1000) * 0.1}"),
                bid_volume_1=100 + (i % 500),
                ask_volume_1=150 + (i % 500),
                volume=10000 + i,
                turnover=Decimal(f"{38500000 + i * 1000}"),
                open_interest=50000 + i,
                timestamp=datetime.now() + timedelta(microseconds=i)
            )
            test_data.append(tick_data)
        
        # 性能测试
        start_time = time.perf_counter()
        
        for tick_data in test_data:
            await market_service.process_tick_data(tick_data)
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # 计算性能指标
        throughput = tick_count / processing_time
        latency_per_tick = (processing_time / tick_count) * 1000  # 毫秒
        
        print(f"处理 {tick_count} 条Tick数据:")
        print(f"总耗时: {processing_time:.2f} 秒")
        print(f"吞吐量: {throughput:.0f} 条/秒")
        print(f"平均延迟: {latency_per_tick:.3f} 毫秒/条")
        
        # 性能断言
        assert throughput >= 10000, f"吞吐量 {throughput:.0f} 条/秒 低于预期 10000 条/秒"
        assert latency_per_tick <= 0.1, f"平均延迟 {latency_per_tick:.3f} 毫秒 高于预期 0.1 毫秒"

    @pytest.mark.asyncio
    async def test_concurrent_symbol_processing(self, market_service):
        """测试并发合约处理性能"""
        symbols = [f"rb240{i}" for i in range(1, 21)]  # 20个合约
        ticks_per_symbol = 2000
        
        async def process_symbol_ticks(symbol: str):
            """处理单个合约的Tick数据"""
            start_time = time.perf_counter()
            
            for i in range(ticks_per_symbol):
                tick_data = TickData(
                    symbol=symbol,
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i * 0.1}"),
                    volume=10000 + i,
                    timestamp=datetime.now()
                )
                await market_service.process_tick_data(tick_data)
            
            end_time = time.perf_counter()
            return end_time - start_time
        
        # 并发处理
        start_time = time.perf_counter()
        
        tasks = [process_symbol_ticks(symbol) for symbol in symbols]
        processing_times = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # 计算性能指标
        total_ticks = len(symbols) * ticks_per_symbol
        overall_throughput = total_ticks / total_time
        avg_symbol_time = statistics.mean(processing_times)
        
        print(f"并发处理 {len(symbols)} 个合约，每个 {ticks_per_symbol} 条数据:")
        print(f"总耗时: {total_time:.2f} 秒")
        print(f"整体吞吐量: {overall_throughput:.0f} 条/秒")
        print(f"平均单合约处理时间: {avg_symbol_time:.2f} 秒")
        
        # 性能断言
        assert overall_throughput >= 15000, f"并发吞吐量 {overall_throughput:.0f} 条/秒 低于预期"
        assert total_time <= 10, f"总处理时间 {total_time:.2f} 秒 超过预期"

    @pytest.mark.asyncio
    async def test_kline_generation_performance(self, market_service):
        """测试K线生成性能"""
        symbol = "rb2405"
        tick_count = 10000
        
        # 生成连续的Tick数据用于K线合成
        base_time = datetime.now().replace(second=0, microsecond=0)
        
        start_time = time.perf_counter()
        
        for i in range(tick_count):
            tick_data = TickData(
                symbol=symbol,
                exchange="SHFE",
                last_price=Decimal(f"{3850 + (i % 100) * 0.1}"),
                volume=10000 + i,
                timestamp=base_time + timedelta(seconds=i // 100)  # 每100个tick一秒
            )
            await market_service.process_tick_data(tick_data)
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # 检查生成的K线数据
        cached_klines = market_service.get_cached_klines(symbol, "1m")
        
        print(f"处理 {tick_count} 条Tick数据生成K线:")
        print(f"耗时: {processing_time:.2f} 秒")
        print(f"生成K线数量: {len(cached_klines)}")
        print(f"K线生成效率: {len(cached_klines) / processing_time:.1f} 条K线/秒")
        
        # 性能断言
        assert processing_time <= 5, f"K线生成耗时 {processing_time:.2f} 秒 超过预期"
        assert len(cached_klines) > 0, "未生成K线数据"

    @pytest.mark.asyncio
    async def test_websocket_broadcast_performance(self, market_service):
        """测试WebSocket广播性能"""
        # 创建多个模拟客户端
        client_count = 1000
        clients = {}
        
        for i in range(client_count):
            client_id = f"client_{i}"
            mock_ws = AsyncMock()
            clients[client_id] = mock_ws
            market_service.add_client(client_id, mock_ws)
            market_service.subscribe_client_symbols(client_id, ["rb2405"])
        
        # 测试广播性能
        tick_count = 1000
        start_time = time.perf_counter()
        
        for i in range(tick_count):
            tick_data = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i * 0.1}"),
                volume=10000 + i,
                timestamp=datetime.now()
            )
            await market_service.broadcast_tick_data(tick_data)
        
        end_time = time.perf_counter()
        broadcast_time = end_time - start_time
        
        # 计算性能指标
        total_messages = tick_count * client_count
        message_rate = total_messages / broadcast_time
        
        print(f"向 {client_count} 个客户端广播 {tick_count} 条数据:")
        print(f"总消息数: {total_messages}")
        print(f"广播耗时: {broadcast_time:.2f} 秒")
        print(f"消息发送速率: {message_rate:.0f} 消息/秒")
        
        # 性能断言
        assert broadcast_time <= 10, f"广播耗时 {broadcast_time:.2f} 秒 超过预期"
        assert message_rate >= 50000, f"消息发送速率 {message_rate:.0f} 消息/秒 低于预期"


class TestMarketDataStressTest:
    """行情数据压力测试"""
    
    @pytest.fixture
    def market_service(self):
        """创建行情数据服务实例"""
        return MarketDataService()

    @pytest.mark.asyncio
    async def test_sustained_high_load(self, market_service):
        """测试持续高负载处理"""
        duration_seconds = 30  # 持续30秒
        target_tps = 5000  # 目标每秒5000条
        
        symbols = [f"rb240{i}" for i in range(1, 11)]
        processed_count = 0
        start_time = time.perf_counter()
        end_time = start_time + duration_seconds
        
        async def data_generator():
            """数据生成器"""
            nonlocal processed_count
            i = 0
            while time.perf_counter() < end_time:
                tick_data = TickData(
                    symbol=symbols[i % len(symbols)],
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + (i % 1000) * 0.1}"),
                    volume=10000 + i,
                    timestamp=datetime.now()
                )
                await market_service.process_tick_data(tick_data)
                processed_count += 1
                i += 1
                
                # 控制发送速率
                if i % 100 == 0:
                    await asyncio.sleep(0.01)
        
        # 运行压力测试
        await data_generator()
        
        actual_duration = time.perf_counter() - start_time
        actual_tps = processed_count / actual_duration
        
        print(f"持续高负载测试 ({duration_seconds} 秒):")
        print(f"实际运行时间: {actual_duration:.2f} 秒")
        print(f"处理数据量: {processed_count} 条")
        print(f"实际TPS: {actual_tps:.0f} 条/秒")
        print(f"目标TPS: {target_tps} 条/秒")
        
        # 性能断言
        assert actual_tps >= target_tps * 0.8, f"实际TPS {actual_tps:.0f} 低于目标的80%"
        assert market_service.stats["error_count"] == 0, "压力测试期间出现错误"

    @pytest.mark.asyncio
    async def test_memory_stability_under_load(self, market_service):
        """测试高负载下的内存稳定性"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 处理大量数据
            data_count = 100000
            symbols = [f"rb240{i}" for i in range(1, 21)]
            
            for i in range(data_count):
                tick_data = TickData(
                    symbol=symbols[i % len(symbols)],
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i * 0.001}"),
                    volume=10000 + i,
                    timestamp=datetime.now()
                )
                await market_service.process_tick_data(tick_data)
                
                # 每1000条检查一次内存
                if i % 1000 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - initial_memory
                    
                    # 内存增长不应超过500MB
                    assert memory_growth < 500, f"内存增长 {memory_growth:.1f}MB 过大"
            
            final_memory = process.memory_info().rss / 1024 / 1024
            total_growth = final_memory - initial_memory
            
            print(f"内存稳定性测试 (处理 {data_count} 条数据):")
            print(f"初始内存: {initial_memory:.1f} MB")
            print(f"最终内存: {final_memory:.1f} MB")
            print(f"内存增长: {total_growth:.1f} MB")
            
            # 内存增长应该在合理范围内
            assert total_growth < 200, f"总内存增长 {total_growth:.1f}MB 超过预期"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")

    @pytest.mark.asyncio
    async def test_error_recovery_under_stress(self, market_service):
        """测试压力下的错误恢复能力"""
        error_injection_rate = 0.1  # 10%的错误率
        total_data_count = 10000
        
        with patch.object(market_service, 'store_tick_data') as mock_store:
            # 模拟间歇性存储错误
            call_count = 0
            
            async def store_with_errors(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % int(1 / error_injection_rate) == 0:
                    raise Exception("Simulated storage error")
                return True
            
            mock_store.side_effect = store_with_errors
            
            # 处理数据
            successful_count = 0
            error_count = 0
            
            for i in range(total_data_count):
                tick_data = TickData(
                    symbol="rb2405",
                    exchange="SHFE",
                    last_price=Decimal(f"{3850 + i * 0.1}"),
                    volume=10000 + i,
                    timestamp=datetime.now()
                )
                
                try:
                    await market_service.process_tick_data(tick_data)
                    successful_count += 1
                except Exception:
                    error_count += 1
            
            success_rate = successful_count / total_data_count
            
            print(f"错误恢复测试 (处理 {total_data_count} 条数据):")
            print(f"成功处理: {successful_count} 条")
            print(f"错误数量: {error_count} 条")
            print(f"成功率: {success_rate:.1%}")
            
            # 即使有错误，成功率也应该很高
            assert success_rate >= 0.85, f"成功率 {success_rate:.1%} 低于预期"
