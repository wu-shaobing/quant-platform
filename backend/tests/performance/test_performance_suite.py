"""
性能测试套件
包含API性能测试、数据库性能测试、WebSocket性能测试等
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
import httpx
import websockets
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.models.trading import Order
from app.services.trading_service import TradingService
from app.services.market_service import MarketService


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = 0
        self.end_time = 0
        
    def add_response_time(self, response_time: float):
        self.response_times.append(response_time)
        
    def add_success(self):
        self.success_count += 1
        
    def add_error(self):
        self.error_count += 1
        
    def start(self):
        self.start_time = time.time()
        
    def end(self):
        self.end_time = time.time()
        
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.response_times:
            return {
                'total_requests': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'throughput': 0,
                'total_duration': self.end_time - self.start_time if self.end_time > 0 else 0
            }
            
        total_requests = len(self.response_times)
        success_rate = (self.success_count / total_requests) * 100 if total_requests > 0 else 0
        avg_response_time = statistics.mean(self.response_times)
        min_response_time = min(self.response_times)
        max_response_time = max(self.response_times)
        
        sorted_times = sorted(self.response_times)
        p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
        p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        
        duration = self.end_time - self.start_time if self.end_time > 0 else time.time() - self.start_time
        throughput = total_requests / duration if duration > 0 else 0
        
        return {
            'total_requests': total_requests,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_response_time * 1000, 2),  # ms
            'min_response_time': round(min_response_time * 1000, 2),  # ms
            'max_response_time': round(max_response_time * 1000, 2),  # ms
            'p95_response_time': round(p95_response_time * 1000, 2),  # ms
            'p99_response_time': round(p99_response_time * 1000, 2),  # ms
            'throughput': round(throughput, 2),  # requests/second
            'total_duration': round(duration, 2)  # seconds
        }


class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_headers = {}
        
    async def authenticate(self, username: str = "test@example.com", password: str = "testpass123"):
        """获取认证token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"email": username, "password": password}
            )
            if response.status_code == 200:
                token = response.json()["access_token"]
                self.auth_headers = {"Authorization": f"Bearer {token}"}
                return True
            return False
    
    async def load_test_endpoint(
        self, 
        method: str, 
        endpoint: str, 
        concurrent_users: int = 10,
        requests_per_user: int = 100,
        payload: Dict = None
    ) -> PerformanceMetrics:
        """对单个端点进行负载测试"""
        
        metrics = PerformanceMetrics()
        metrics.start()
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                try:
                    if method.upper() == "GET":
                        response = await client.get(
                            f"{self.base_url}{endpoint}",
                            headers=self.auth_headers,
                            timeout=30.0
                        )
                    elif method.upper() == "POST":
                        response = await client.post(
                            f"{self.base_url}{endpoint}",
                            json=payload,
                            headers=self.auth_headers,
                            timeout=30.0
                        )
                    elif method.upper() == "PUT":
                        response = await client.put(
                            f"{self.base_url}{endpoint}",
                            json=payload,
                            headers=self.auth_headers,
                            timeout=30.0
                        )
                    elif method.upper() == "DELETE":
                        response = await client.delete(
                            f"{self.base_url}{endpoint}",
                            headers=self.auth_headers,
                            timeout=30.0
                        )
                    
                    response_time = time.time() - start_time
                    metrics.add_response_time(response_time)
                    
                    if response.status_code < 400:
                        metrics.add_success()
                    else:
                        metrics.add_error()
                        
                except Exception as e:
                    response_time = time.time() - start_time
                    metrics.add_response_time(response_time)
                    metrics.add_error()
        
        # 创建并发任务
        tasks = []
        for user in range(concurrent_users):
            for req in range(requests_per_user):
                tasks.append(make_request())
        
        # 执行所有任务
        await asyncio.gather(*tasks)
        
        metrics.end()
        return metrics
    
    async def stress_test_trading_apis(self) -> Dict[str, PerformanceMetrics]:
        """交易API压力测试"""
        
        # 先进行认证
        await self.authenticate()
        
        test_cases = [
            {
                "name": "get_account",
                "method": "GET",
                "endpoint": "/trading/account",
                "concurrent_users": 20,
                "requests_per_user": 50
            },
            {
                "name": "get_positions",
                "method": "GET", 
                "endpoint": "/trading/positions",
                "concurrent_users": 15,
                "requests_per_user": 30
            },
            {
                "name": "get_orders",
                "method": "GET",
                "endpoint": "/trading/orders",
                "concurrent_users": 15,
                "requests_per_user": 30
            },
            {
                "name": "submit_order",
                "method": "POST",
                "endpoint": "/trading/orders",
                "concurrent_users": 10,
                "requests_per_user": 20,
                "payload": {
                    "symbol": "000001",
                    "exchange": "SSE",
                    "direction": "long",
                    "offset": "open",
                    "order_type": "limit",
                    "volume": 100,
                    "price": 10.50
                }
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"执行测试: {test_case['name']}")
            
            metrics = await self.load_test_endpoint(
                method=test_case["method"],
                endpoint=test_case["endpoint"],
                concurrent_users=test_case["concurrent_users"],
                requests_per_user=test_case["requests_per_user"],
                payload=test_case.get("payload")
            )
            
            results[test_case["name"]] = metrics
            
            # 打印结果
            stats = metrics.get_stats()
            print(f"  总请求数: {stats['total_requests']}")
            print(f"  成功率: {stats['success_rate']}%")
            print(f"  平均响应时间: {stats['avg_response_time']}ms")
            print(f"  P95响应时间: {stats['p95_response_time']}ms")
            print(f"  吞吐量: {stats['throughput']} req/s")
            print()
            
        return results


class DatabasePerformanceTester:
    """数据库性能测试器"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def test_query_performance(self) -> Dict[str, Any]:
        """测试查询性能"""
        
        results = {}
        
        # 测试用户查询
        start_time = time.time()
        for _ in range(1000):
            result = await self.db.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": "test@example.com"}
            )
            result.fetchone()
        user_query_time = time.time() - start_time
        results["user_query_1000"] = user_query_time
        
        # 测试订单查询
        start_time = time.time()
        for _ in range(500):
            result = await self.db.execute(
                text("SELECT * FROM orders WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 10"),
                {"user_id": 1}
            )
            result.fetchall()
        order_query_time = time.time() - start_time
        results["order_query_500"] = order_query_time
        
        # 测试复杂聚合查询
        start_time = time.time()
        for _ in range(100):
            result = await self.db.execute(
                text("""
                    SELECT 
                        user_id,
                        COUNT(*) as order_count,
                        SUM(volume * price) as total_amount
                    FROM orders 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY user_id
                    ORDER BY total_amount DESC
                    LIMIT 10
                """)
            )
            result.fetchall()
        aggregate_query_time = time.time() - start_time
        results["aggregate_query_100"] = aggregate_query_time
        
        # 测试批量插入
        start_time = time.time()
        orders_data = []
        for i in range(1000):
            orders_data.append({
                "user_id": 1,
                "symbol": "TEST" + str(i % 10),
                "exchange": "TEST",
                "direction": "long",
                "offset": "open", 
                "order_type": "limit",
                "volume": 100,
                "price": 10.0 + (i % 100) * 0.01,
                "status": "submitted"
            })
        
        await self.db.execute(
            text("""
                INSERT INTO orders (user_id, symbol, exchange, direction, offset, order_type, volume, price, status)
                VALUES (:user_id, :symbol, :exchange, :direction, :offset, :order_type, :volume, :price, :status)
            """),
            orders_data
        )
        await self.db.commit()
        batch_insert_time = time.time() - start_time
        results["batch_insert_1000"] = batch_insert_time
        
        return results
    
    async def test_connection_pool_performance(self) -> Dict[str, Any]:
        """测试连接池性能"""
        
        async def execute_query():
            result = await self.db.execute(text("SELECT 1"))
            return result.scalar()
        
        # 并发执行查询
        start_time = time.time()
        tasks = [execute_query() for _ in range(100)]
        await asyncio.gather(*tasks)
        concurrent_query_time = time.time() - start_time
        
        return {
            "concurrent_queries_100": concurrent_query_time,
            "avg_query_time": concurrent_query_time / 100
        }


class WebSocketPerformanceTester:
    """WebSocket性能测试器"""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        self.ws_url = ws_url
    
    async def test_connection_performance(self, concurrent_connections: int = 100) -> Dict[str, Any]:
        """测试WebSocket连接性能"""
        
        connection_times = []
        successful_connections = 0
        failed_connections = 0
        
        async def connect_and_measure():
            nonlocal successful_connections, failed_connections
            
            start_time = time.time()
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    connection_time = time.time() - start_time
                    connection_times.append(connection_time)
                    successful_connections += 1
                    
                    # 保持连接一段时间
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_connections += 1
        
        # 并发连接测试
        start_time = time.time()
        tasks = [connect_and_measure() for _ in range(concurrent_connections)]
        await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        return {
            "total_connections": concurrent_connections,
            "successful_connections": successful_connections,
            "failed_connections": failed_connections,
            "success_rate": (successful_connections / concurrent_connections) * 100,
            "avg_connection_time": statistics.mean(connection_times) if connection_times else 0,
            "max_connection_time": max(connection_times) if connection_times else 0,
            "total_time": total_time
        }
    
    async def test_message_throughput(self, messages_per_second: int = 1000, duration: int = 10) -> Dict[str, Any]:
        """测试消息吞吐量"""
        
        messages_sent = 0
        messages_received = 0
        message_times = []
        
        async def message_sender(websocket):
            nonlocal messages_sent
            
            interval = 1.0 / messages_per_second
            end_time = time.time() + duration
            
            while time.time() < end_time:
                start_time = time.time()
                
                message = {
                    "type": "ping",
                    "timestamp": start_time,
                    "data": "performance_test"
                }
                
                await websocket.send(json.dumps(message))
                messages_sent += 1
                
                # 控制发送频率
                elapsed = time.time() - start_time
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)
        
        async def message_receiver(websocket):
            nonlocal messages_received
            
            try:
                async for message in websocket:
                    receive_time = time.time()
                    data = json.loads(message)
                    
                    if "timestamp" in data:
                        message_time = receive_time - data["timestamp"]
                        message_times.append(message_time)
                    
                    messages_received += 1
                    
            except websockets.exceptions.ConnectionClosed:
                pass
        
        # 执行测试
        start_time = time.time()
        
        async with websockets.connect(self.ws_url) as websocket:
            # 并发发送和接收
            await asyncio.gather(
                message_sender(websocket),
                message_receiver(websocket)
            )
        
        total_time = time.time() - start_time
        
        return {
            "duration": duration,
            "target_messages_per_second": messages_per_second,
            "messages_sent": messages_sent,
            "messages_received": messages_received,
            "actual_send_rate": messages_sent / total_time,
            "actual_receive_rate": messages_received / total_time,
            "message_loss_rate": ((messages_sent - messages_received) / messages_sent) * 100 if messages_sent > 0 else 0,
            "avg_message_latency": statistics.mean(message_times) * 1000 if message_times else 0,  # ms
            "p95_message_latency": sorted(message_times)[int(0.95 * len(message_times))] * 1000 if message_times else 0  # ms
        }


class MemoryProfiler:
    """内存性能分析器"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """获取内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss / 1024 / 1024,  # MB
            "vms": memory_info.vms / 1024 / 1024,  # MB
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available / 1024 / 1024,  # MB
            "total": psutil.virtual_memory().total / 1024 / 1024  # MB
        }
    
    @staticmethod
    async def profile_memory_usage(func, *args, **kwargs) -> Dict[str, Any]:
        """分析函数内存使用"""
        
        # 执行垃圾回收
        import gc
        gc.collect()
        
        # 获取执行前内存
        before = MemoryProfiler.get_memory_usage()
        
        # 执行函数
        start_time = time.time()
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # 获取执行后内存
        after = MemoryProfiler.get_memory_usage()
        
        return {
            "before_memory": before,
            "after_memory": after,
            "memory_diff": {
                "rss": after["rss"] - before["rss"],
                "vms": after["vms"] - before["vms"],
                "percent": after["percent"] - before["percent"]
            },
            "execution_time": execution_time,
            "result": result
        }


# 性能测试用例

@pytest.mark.asyncio
async def test_api_performance():
    """API性能测试"""
    tester = APIPerformanceTester()
    results = await tester.stress_test_trading_apis()
    
    # 验证性能指标
    for endpoint, metrics in results.items():
        stats = metrics.get_stats()
        
        # 成功率应该大于95%
        assert stats["success_rate"] > 95, f"{endpoint} 成功率过低: {stats['success_rate']}%"
        
        # 平均响应时间应该小于500ms
        assert stats["avg_response_time"] < 500, f"{endpoint} 平均响应时间过长: {stats['avg_response_time']}ms"
        
        # P95响应时间应该小于1000ms
        assert stats["p95_response_time"] < 1000, f"{endpoint} P95响应时间过长: {stats['p95_response_time']}ms"


@pytest.mark.asyncio
async def test_database_performance():
    """数据库性能测试"""
    async for db in get_db():
        tester = DatabasePerformanceTester(db)
        
        # 查询性能测试
        query_results = await tester.test_query_performance()
        
        # 验证查询性能
        assert query_results["user_query_1000"] < 5.0, "用户查询性能过慢"
        assert query_results["order_query_500"] < 3.0, "订单查询性能过慢"
        assert query_results["aggregate_query_100"] < 10.0, "聚合查询性能过慢"
        assert query_results["batch_insert_1000"] < 5.0, "批量插入性能过慢"
        
        # 连接池性能测试
        pool_results = await tester.test_connection_pool_performance()
        assert pool_results["concurrent_queries_100"] < 2.0, "并发查询性能过慢"
        
        break


@pytest.mark.asyncio
async def test_websocket_performance():
    """WebSocket性能测试"""
    tester = WebSocketPerformanceTester()
    
    # 连接性能测试
    connection_results = await tester.test_connection_performance(concurrent_connections=50)
    assert connection_results["success_rate"] > 90, "WebSocket连接成功率过低"
    assert connection_results["avg_connection_time"] < 1.0, "WebSocket连接时间过长"
    
    # 消息吞吐量测试
    throughput_results = await tester.test_message_throughput(messages_per_second=100, duration=5)
    assert throughput_results["message_loss_rate"] < 5, "WebSocket消息丢失率过高"
    assert throughput_results["avg_message_latency"] < 100, "WebSocket消息延迟过高"


@pytest.mark.asyncio
async def test_memory_performance():
    """内存性能测试"""
    
    # 测试交易服务内存使用
    async for db in get_db():
        trading_service = TradingService(db)
        
        # 分析内存使用
        memory_result = await MemoryProfiler.profile_memory_usage(
            trading_service.get_user_orders,
            user_id=1,
            limit=1000
        )
        
        # 验证内存使用合理
        assert memory_result["memory_diff"]["rss"] < 50, "内存使用增长过多"
        
        break


if __name__ == "__main__":
    async def run_performance_tests():
        """运行性能测试"""
        
        print("=" * 50)
        print("开始性能测试")
        print("=" * 50)
        
        # API性能测试
        print("\n1. API性能测试")
        print("-" * 30)
        api_tester = APIPerformanceTester()
        api_results = await api_tester.stress_test_trading_apis()
        
        # WebSocket性能测试
        print("\n2. WebSocket性能测试")
        print("-" * 30)
        ws_tester = WebSocketPerformanceTester()
        
        connection_results = await ws_tester.test_connection_performance(50)
        print(f"连接测试 - 成功率: {connection_results['success_rate']}%, 平均连接时间: {connection_results['avg_connection_time']:.3f}s")
        
        throughput_results = await ws_tester.test_message_throughput(100, 5)
        print(f"吞吐量测试 - 发送速率: {throughput_results['actual_send_rate']:.1f} msg/s, 延迟: {throughput_results['avg_message_latency']:.1f}ms")
        
        print("\n性能测试完成!")
        print("=" * 50)
    
    # 运行测试
    asyncio.run(run_performance_tests()) 