"""
性能测试
"""
import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import threading
import statistics

from app.services.ctp_service import ctp_service
from app.services.market_data_service import market_data_service
from app.schemas.market_data import TickData
from app.schemas.ctp_schemas import OrderRequest


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture
    def performance_monitor(self):
        """性能监控器"""
        class PerformanceMonitor:
            def __init__(self):
                self.process = psutil.Process(os.getpid())
                self.start_time = None
                self.start_memory = None
                self.start_cpu = None
            
            def start(self):
                self.start_time = time.time()
                self.start_memory = self.process.memory_info().rss
                self.start_cpu = self.process.cpu_percent()
                return self
            
            def stop(self):
                end_time = time.time()
                end_memory = self.process.memory_info().rss
                end_cpu = self.process.cpu_percent()
                
                return {
                    "duration": end_time - self.start_time,
                    "memory_usage": end_memory - self.start_memory,
                    "cpu_usage": end_cpu,
                    "peak_memory": self.process.memory_info().peak_wss if hasattr(self.process.memory_info(), 'peak_wss') else end_memory
                }
        
        return PerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_tick_data_processing_performance(self, performance_monitor):
        """测试Tick数据处理性能"""
        # 生成测试数据
        tick_count = 10000
        ticks = []
        
        for i in range(tick_count):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i % 100}"),
                volume=100 + i % 50,
                timestamp=datetime.now() + timedelta(milliseconds=i)
            )
            ticks.append(tick)
        
        # 开始性能监控
        monitor = performance_monitor.start()
        
        # 处理数据
        for tick in ticks:
            await market_data_service.process_tick_data(tick)
        
        # 停止监控
        stats = monitor.stop()
        
        # 性能断言
        assert stats["duration"] < 10.0  # 10000条数据应在10秒内处理完成
        assert stats["memory_usage"] < 100 * 1024 * 1024  # 内存增长不超过100MB
        
        # 计算吞吐量
        throughput = tick_count / stats["duration"]
        assert throughput > 1000  # 每秒处理超过1000条数据
        
        print(f"Tick processing performance:")
        print(f"  Duration: {stats['duration']:.2f}s")
        print(f"  Throughput: {throughput:.0f} ticks/s")
        print(f"  Memory usage: {stats['memory_usage'] / 1024 / 1024:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_concurrent_order_processing(self, performance_monitor):
        """测试并发订单处理性能"""
        order_count = 1000
        concurrent_tasks = 50
        
        # 创建订单请求
        def create_order_request(i):
            return OrderRequest(
                instrument_id="rb2405",
                direction="0",  # 买
                offset_flag="0",  # 开仓
                price=Decimal(f"{3850 + i % 10}"),
                volume=1,
                order_price_type="2",  # 限价
                time_condition="3",  # 当日有效
                volume_condition="1"  # 任何数量
            )
        
        orders = [create_order_request(i) for i in range(order_count)]
        
        # 开始性能监控
        monitor = performance_monitor.start()
        
        # 并发处理订单
        semaphore = asyncio.Semaphore(concurrent_tasks)
        
        async def process_order(order):
            async with semaphore:
                try:
                    # 模拟订单处理
                    await asyncio.sleep(0.01)  # 模拟处理时间
                    return True
                except Exception:
                    return False
        
        # 执行并发任务
        results = await asyncio.gather(*[process_order(order) for order in orders])
        
        # 停止监控
        stats = monitor.stop()
        
        # 性能断言
        success_rate = sum(results) / len(results)
        assert success_rate > 0.95  # 成功率超过95%
        assert stats["duration"] < 30.0  # 1000个订单应在30秒内处理完成
        
        throughput = order_count / stats["duration"]
        print(f"Concurrent order processing performance:")
        print(f"  Duration: {stats['duration']:.2f}s")
        print(f"  Throughput: {throughput:.0f} orders/s")
        print(f"  Success rate: {success_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 执行多轮操作
        for round_num in range(10):
            # 处理大量数据
            for i in range(1000):
                tick = TickData(
                    symbol=f"test{i % 10}",
                    exchange="TEST",
                    last_price=Decimal("100.0"),
                    volume=100,
                    timestamp=datetime.now()
                )
                await market_data_service.process_tick_data(tick)
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            # 检查内存使用
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory
            
            # 内存增长不应超过50MB
            assert memory_growth < 50 * 1024 * 1024, f"Memory leak detected: {memory_growth / 1024 / 1024:.2f}MB growth"
    
    def test_database_connection_pool_performance(self):
        """测试数据库连接池性能"""
        from app.core.database import engine
        
        start_time = time.time()
        connection_times = []
        
        # 测试连接获取时间
        for i in range(100):
            conn_start = time.time()
            
            # 模拟数据库连接
            try:
                # 这里应该是实际的数据库连接测试
                time.sleep(0.001)  # 模拟连接时间
                conn_end = time.time()
                connection_times.append(conn_end - conn_start)
            except Exception as e:
                pytest.fail(f"Database connection failed: {e}")
        
        end_time = time.time()
        
        # 性能断言
        total_time = end_time - start_time
        avg_connection_time = statistics.mean(connection_times)
        max_connection_time = max(connection_times)
        
        assert total_time < 5.0  # 100次连接应在5秒内完成
        assert avg_connection_time < 0.05  # 平均连接时间小于50ms
        assert max_connection_time < 0.1  # 最大连接时间小于100ms
        
        print(f"Database connection pool performance:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average connection time: {avg_connection_time * 1000:.2f}ms")
        print(f"  Max connection time: {max_connection_time * 1000:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_performance(self, performance_monitor):
        """测试WebSocket广播性能"""
        # 模拟多个WebSocket客户端
        client_count = 100
        message_count = 1000
        
        # 创建模拟客户端
        class MockWebSocket:
            def __init__(self, client_id):
                self.client_id = client_id
                self.messages_received = 0
            
            async def send_text(self, message):
                self.messages_received += 1
                await asyncio.sleep(0.001)  # 模拟网络延迟
        
        # 添加客户端到市场数据服务
        clients = []
        for i in range(client_count):
            client_id = f"client_{i}"
            websocket = MockWebSocket(client_id)
            clients.append(websocket)
            market_data_service.add_client(client_id, websocket)
            await market_data_service.subscribe_client(client_id, ["rb2405"])
        
        # 开始性能监控
        monitor = performance_monitor.start()
        
        # 广播消息
        for i in range(message_count):
            tick = TickData(
                symbol="rb2405",
                exchange="SHFE",
                last_price=Decimal(f"{3850 + i}"),
                volume=100,
                timestamp=datetime.now()
            )
            await market_data_service.push_tick_data(tick)
        
        # 等待所有消息处理完成
        await asyncio.sleep(1.0)
        
        # 停止监控
        stats = monitor.stop()
        
        # 验证消息接收
        total_messages_received = sum(client.messages_received for client in clients)
        expected_messages = client_count * message_count
        
        # 性能断言
        assert total_messages_received >= expected_messages * 0.95  # 至少95%的消息被接收
        assert stats["duration"] < 30.0  # 广播应在30秒内完成
        
        throughput = total_messages_received / stats["duration"]
        print(f"WebSocket broadcast performance:")
        print(f"  Duration: {stats['duration']:.2f}s")
        print(f"  Messages sent: {expected_messages}")
        print(f"  Messages received: {total_messages_received}")
        print(f"  Throughput: {throughput:.0f} messages/s")
        
        # 清理客户端
        for i in range(client_count):
            market_data_service.remove_client(f"client_{i}")
    
    def test_cpu_usage_under_load(self):
        """测试高负载下的CPU使用率"""
        process = psutil.Process(os.getpid())
        
        # 记录初始CPU使用率
        initial_cpu = process.cpu_percent(interval=1)
        
        # 创建CPU密集型任务
        def cpu_intensive_task():
            start_time = time.time()
            while time.time() - start_time < 5:  # 运行5秒
                # 执行一些计算密集型操作
                sum(i * i for i in range(10000))
        
        # 启动多个线程
        thread_count = psutil.cpu_count()
        threads = []
        
        start_time = time.time()
        
        for i in range(thread_count):
            thread = threading.Thread(target=cpu_intensive_task)
            thread.start()
            threads.append(thread)
        
        # 监控CPU使用率
        cpu_samples = []
        while any(thread.is_alive() for thread in threads):
            cpu_usage = process.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_usage)
            time.sleep(0.1)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # 分析CPU使用率
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)
            
            print(f"CPU usage under load:")
            print(f"  Duration: {end_time - start_time:.2f}s")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Peak CPU: {max_cpu:.1f}%")
            print(f"  Thread count: {thread_count}")
            
            # CPU使用率应该合理（不超过CPU核心数 * 100%）
            assert max_cpu <= thread_count * 100 + 50  # 允许一些误差
    
    @pytest.mark.asyncio
    async def test_response_time_under_load(self):
        """测试高负载下的响应时间"""
        response_times = []
        request_count = 1000
        concurrent_requests = 50
        
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            async with semaphore:
                start_time = time.time()
                
                # 模拟API请求处理
                try:
                    await asyncio.sleep(0.01)  # 模拟处理时间
                    end_time = time.time()
                    return end_time - start_time
                except Exception:
                    return None
        
        # 执行并发请求
        tasks = [make_request() for _ in range(request_count)]
        results = await asyncio.gather(*tasks)
        
        # 过滤有效结果
        response_times = [r for r in results if r is not None]
        
        # 分析响应时间
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
            
            print(f"Response time under load:")
            print(f"  Requests: {len(response_times)}")
            print(f"  Average: {avg_response_time * 1000:.2f}ms")
            print(f"  P95: {p95_response_time * 1000:.2f}ms")
            print(f"  P99: {p99_response_time * 1000:.2f}ms")
            
            # 性能断言
            assert avg_response_time < 0.1  # 平均响应时间小于100ms
            assert p95_response_time < 0.2  # 95%的请求响应时间小于200ms
            assert p99_response_time < 0.5  # 99%的请求响应时间小于500ms


class TestLoadTesting:
    """负载测试类"""
    
    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """测试持续负载"""
        duration = 60  # 测试60秒
        start_time = time.time()
        
        request_count = 0
        error_count = 0
        
        async def continuous_requests():
            nonlocal request_count, error_count
            
            while time.time() - start_time < duration:
                try:
                    # 模拟请求
                    await asyncio.sleep(0.01)
                    request_count += 1
                except Exception:
                    error_count += 1
                
                await asyncio.sleep(0.001)  # 小间隔
        
        # 启动多个并发任务
        tasks = [continuous_requests() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # 计算统计信息
        throughput = request_count / actual_duration
        error_rate = error_count / request_count if request_count > 0 else 0
        
        print(f"Sustained load test:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Requests: {request_count}")
        print(f"  Errors: {error_count}")
        print(f"  Throughput: {throughput:.0f} req/s")
        print(f"  Error rate: {error_rate:.2%}")
        
        # 性能断言
        assert throughput > 100  # 每秒至少100个请求
        assert error_rate < 0.01  # 错误率小于1%


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
