"""
CTP指标收集器测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.monitoring.ctp_metrics import CTPMetricsCollector, CTPMetrics


class TestCTPMetricsCollector:
    """CTP指标收集器测试类"""
    
    @pytest.fixture
    def collector(self):
        """创建指标收集器实例"""
        return CTPMetricsCollector()
    
    @pytest.fixture
    def sample_metrics(self):
        """示例指标数据"""
        return CTPMetrics(
            connection_count=2,
            order_count=10,
            order_success_count=8,
            trade_count=5,
            market_data_count=1000,
            error_count=2,
            memory_usage=1024 * 1024 * 512,  # 512MB
            cpu_usage=45.5,
            last_update=datetime.now()
        )
    
    def test_metrics_initialization(self, collector):
        """测试指标初始化"""
        assert collector.metrics is not None
        assert collector.metrics.connection_count == 0
        assert collector.metrics.order_count == 0
        assert collector.metrics.trade_count == 0
        assert not collector.running
    
    @pytest.mark.asyncio
    async def test_record_connection(self, collector):
        """测试记录连接"""
        # 记录连接成功
        await collector.record_connection("trade", True, "CITIC")
        assert collector.metrics.connection_count == 1
        
        # 记录连接失败
        await collector.record_connection("md", False, "CITIC")
        assert collector.metrics.connection_count == 1  # 失败不增加计数
        assert collector.metrics.error_count == 1
    
    @pytest.mark.asyncio
    async def test_record_order(self, collector):
        """测试记录订单"""
        # 记录成功订单
        await collector.record_order("success", 0.5, "CITIC", "limit")
        assert collector.metrics.order_count == 1
        assert collector.metrics.order_success_count == 1
        
        # 记录失败订单
        await collector.record_order("error", 1.0, "CITIC", "market")
        assert collector.metrics.order_count == 2
        assert collector.metrics.order_success_count == 1
        assert collector.metrics.error_count == 1
    
    @pytest.mark.asyncio
    async def test_record_trade(self, collector):
        """测试记录交易"""
        await collector.record_trade(100.0, 10, "CITIC", "buy")
        assert collector.metrics.trade_count == 1
    
    @pytest.mark.asyncio
    async def test_record_market_data(self, collector):
        """测试记录行情数据"""
        await collector.record_market_data("tick", 0.1, "CITIC")
        assert collector.metrics.market_data_count == 1
    
    @pytest.mark.asyncio
    async def test_record_error(self, collector):
        """测试记录错误"""
        await collector.record_error("connection", "timeout", "CITIC")
        assert collector.metrics.error_count == 1
    
    @pytest.mark.asyncio
    async def test_update_system_metrics(self, collector):
        """测试更新系统指标"""
        with patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.cpu_percent') as mock_cpu:
            
            # 模拟系统指标
            mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB
            mock_cpu.return_value = 75.0
            
            await collector.update_system_metrics()
            
            assert collector.metrics.memory_usage == 1024 * 1024 * 1024
            assert collector.metrics.cpu_usage == 75.0
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, collector, sample_metrics):
        """测试获取指标摘要"""
        collector.metrics = sample_metrics
        
        summary = await collector.get_metrics_summary()
        
        assert "connection_status" in summary
        assert "order_stats" in summary
        assert "trade_count" in summary
        assert "market_data" in summary
        assert "system" in summary
        assert "errors" in summary
        assert "last_update" in summary
    
    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self, collector):
        """测试健康状态 - 健康"""
        # 设置健康的指标
        collector.metrics.connection_count = 2
        collector.metrics.order_count = 10
        collector.metrics.order_success_count = 9
        collector.metrics.error_count = 1
        collector.metrics.last_update = datetime.now()
        
        health = await collector.get_health_status()
        
        assert health["status"] == "healthy"
        assert health["connections"]["trade"] is True
        assert health["connections"]["md"] is True
        assert health["error_rate"] == 0.1
    
    @pytest.mark.asyncio
    async def test_get_health_status_unhealthy(self, collector):
        """测试健康状态 - 不健康"""
        # 设置不健康的指标
        collector.metrics.connection_count = 0
        collector.metrics.order_count = 10
        collector.metrics.order_success_count = 5
        collector.metrics.error_count = 5
        collector.metrics.last_update = datetime.now() - timedelta(minutes=10)
        
        health = await collector.get_health_status()
        
        assert health["status"] == "unhealthy"
        assert health["connections"]["trade"] is False
        assert health["connections"]["md"] is False
        assert health["error_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_start_stop_collection(self, collector):
        """测试启动和停止收集"""
        # 启动收集
        await collector.start_collection()
        assert collector.running is True
        
        # 等待一小段时间确保任务启动
        await asyncio.sleep(0.1)
        
        # 停止收集
        await collector.stop_collection()
        assert collector.running is False
    
    @pytest.mark.asyncio
    async def test_prometheus_metrics_export(self, collector):
        """测试Prometheus指标导出"""
        # 设置一些指标
        await collector.record_connection("trade", True, "CITIC")
        await collector.record_order("success", 0.5, "CITIC", "limit")
        await collector.record_trade(100.0, 10, "CITIC", "buy")
        
        # 获取Prometheus指标
        metrics_output = collector.get_prometheus_metrics()
        
        assert "ctp_connections_total" in metrics_output
        assert "ctp_orders_total" in metrics_output
        assert "ctp_trades_total" in metrics_output
        assert "ctp_memory_usage_bytes" in metrics_output
        assert "ctp_cpu_usage_percent" in metrics_output
    
    @pytest.mark.asyncio
    async def test_metrics_reset(self, collector):
        """测试指标重置"""
        # 设置一些指标
        await collector.record_order("success", 0.5, "CITIC", "limit")
        await collector.record_trade(100.0, 10, "CITIC", "buy")
        
        assert collector.metrics.order_count == 1
        assert collector.metrics.trade_count == 1
        
        # 重置指标
        await collector.reset_metrics()
        
        assert collector.metrics.order_count == 0
        assert collector.metrics.trade_count == 0
        assert collector.metrics.order_success_count == 0
        assert collector.metrics.error_count == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_metric_updates(self, collector):
        """测试并发指标更新"""
        # 创建多个并发任务
        tasks = []
        for i in range(10):
            tasks.append(collector.record_order("success", 0.1, "CITIC", "limit"))
            tasks.append(collector.record_trade(100.0, 1, "CITIC", "buy"))
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        # 验证指标正确性
        assert collector.metrics.order_count == 10
        assert collector.metrics.order_success_count == 10
        assert collector.metrics.trade_count == 10
    
    @pytest.mark.asyncio
    async def test_error_handling_in_collection(self, collector):
        """测试收集过程中的错误处理"""
        with patch.object(collector, 'update_system_metrics', side_effect=Exception("Test error")):
            # 启动收集（应该处理错误而不崩溃）
            await collector.start_collection()
            
            # 等待一小段时间
            await asyncio.sleep(0.1)
            
            # 停止收集
            await collector.stop_collection()
            
            # 验证收集器仍然可以正常工作
            assert collector.running is False
    
    def test_metrics_data_class(self):
        """测试指标数据类"""
        metrics = CTPMetrics()
        
        # 测试默认值
        assert metrics.connection_count == 0
        assert metrics.order_count == 0
        assert metrics.trade_count == 0
        assert metrics.error_count == 0
        assert metrics.memory_usage == 0
        assert metrics.cpu_usage == 0.0
        
        # 测试字典转换
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert "connection_count" in metrics_dict
        assert "last_update" in metrics_dict
    
    @pytest.mark.asyncio
    async def test_connection_uptime_tracking(self, collector):
        """测试连接运行时间跟踪"""
        # 记录连接
        await collector.record_connection("trade", True, "CITIC")
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 获取运行时间
        summary = await collector.get_metrics_summary()
        uptime = summary["connection_uptime"]
        
        assert "trade" in uptime
        assert uptime["trade"] > 0
    
    @pytest.mark.asyncio
    async def test_order_response_time_tracking(self, collector):
        """测试订单响应时间跟踪"""
        # 记录不同响应时间的订单
        await collector.record_order("success", 0.1, "CITIC", "limit")
        await collector.record_order("success", 0.5, "CITIC", "market")
        await collector.record_order("success", 1.0, "CITIC", "stop")
        
        summary = await collector.get_metrics_summary()
        order_stats = summary["order_stats"]
        
        assert "avg_response_time" in order_stats
        assert order_stats["avg_response_time"] > 0
        assert order_stats["success_rate"] == 1.0
