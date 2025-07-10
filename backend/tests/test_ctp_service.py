"""
CTP服务测试
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.ctp_service import CTPService, CTPMarketDataService
from app.core.ctp_config import CTPConfig, CTPStatus, CTPError
from app.schemas.trading import OrderRequest
from app.models.ctp_models import CTPOrder, CTPTrade, CTPPosition, CTPAccount


class TestCTPService:
    """CTP服务测试类"""
    
    @pytest.fixture
    def ctp_config(self):
        """CTP配置fixture"""
        return CTPConfig(
            broker_id="9999",
            user_id="test_user",
            password="test_password",
            trade_front="tcp://180.168.146.187:10130",
            md_front="tcp://180.168.146.187:10131"
        )
    
    @pytest.fixture
    def ctp_service(self, ctp_config):
        """CTP服务fixture"""
        return CTPService(ctp_config)
    
    @pytest.fixture
    def order_request(self):
        """订单请求fixture"""
        return OrderRequest(
            symbol="cu2401",
            direction="BUY",
            offset="OPEN",
            order_type="LIMIT",
            volume=1,
            price=50000.0
        )
    
    def test_ctp_service_initialization(self, ctp_service):
        """测试CTP服务初始化"""
        assert ctp_service.config.broker_id == "9999"
        assert ctp_service.config.user_id == "test_user"
        assert ctp_service.status.trade_connected is False
        assert ctp_service.status.md_connected is False
        assert len(ctp_service.callbacks) == 6
        assert ctp_service.orders == {}
        assert ctp_service.trades == {}
        assert ctp_service.positions == {}
        assert ctp_service.ticks == {}
    
    def test_validate_config(self, ctp_service):
        """测试配置验证"""
        # 正常配置
        assert ctp_service._validate_config() is True
        
        # 缺少必要字段
        ctp_service.config.broker_id = ""
        assert ctp_service._validate_config() is False
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, ctp_service):
        """测试初始化成功"""
        with patch.object(ctp_service, '_validate_config', return_value=True), \
             patch('app.services.ctp_service.get_db') as mock_get_db:
            
            mock_get_db.return_value = Mock()
            
            result = await ctp_service.initialize()
            
            assert result is True
            assert ctp_service.status.trade_connected is True
            assert ctp_service.status.md_connected is True
            assert ctp_service.status.trade_logged_in is True
            assert ctp_service.status.md_logged_in is True
            assert ctp_service.status.is_ready is True
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, ctp_service):
        """测试初始化失败"""
        with patch.object(ctp_service, '_validate_config', return_value=False):
            result = await ctp_service.initialize()
            
            assert result is False
            assert ctp_service.status.error_count > 0
            assert ctp_service.status.last_error is not None
    
    @pytest.mark.asyncio
    async def test_submit_order_success(self, ctp_service, order_request):
        """测试提交订单成功"""
        # 模拟初始化完成
        ctp_service.status.trade_connected = True
        ctp_service.status.trade_logged_in = True
        
        with patch('app.services.ctp_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value = mock_session
            ctp_service._db_session = mock_session
            
            # 模拟数据库操作
            mock_session.add = Mock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            result = await ctp_service.submit_order(order_request, user_id=1)
            
            assert result.success is True
            assert "order_ref" in result.data
            assert result.data["symbol"] == "cu2401"
            assert result.data["direction"] == "BUY"
            assert result.data["price"] == 50000.0
            assert result.data["volume"] == 1
            assert ctp_service.status.order_count == 1
    
    @pytest.mark.asyncio
    async def test_submit_order_not_ready(self, ctp_service, order_request):
        """测试交易接口未就绪时提交订单"""
        ctp_service.status.trade_connected = False
        
        with pytest.raises(CTPError) as exc_info:
            await ctp_service.submit_order(order_request, user_id=1)
        
        assert "交易接口未就绪" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, ctp_service):
        """测试撤销订单成功"""
        ctp_service.status.trade_connected = True
        ctp_service.status.trade_logged_in = True
        
        with patch('app.services.ctp_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value = mock_session
            ctp_service._db_session = mock_session
            
            # 模拟查找订单
            mock_order = Mock()
            mock_order.id = "test-order-id"
            mock_order.order_ref = "000000001"
            
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_order
            mock_session.execute.return_value = mock_result
            
            result = await ctp_service.cancel_order("000000001", user_id=1)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, ctp_service):
        """测试撤销不存在的订单"""
        ctp_service.status.trade_connected = True
        ctp_service.status.trade_logged_in = True
        
        with patch('app.services.ctp_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value = mock_session
            ctp_service._db_session = mock_session
            
            # 模拟订单不存在
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            with pytest.raises(CTPError) as exc_info:
                await ctp_service.cancel_order("000000001", user_id=1)
            
            assert "订单不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_query_orders(self, ctp_service):
        """测试查询订单"""
        with patch('app.services.ctp_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value = mock_session
            ctp_service._db_session = mock_session
            
            # 模拟订单数据
            mock_order = Mock()
            mock_order.id = "test-order-id"
            mock_order.order_ref = "000000001"
            mock_order.instrument_id = "cu2401"
            mock_order.exchange_id = "SHFE"
            mock_order.direction = "0"
            mock_order.offset_flag = "0"
            mock_order.limit_price = Decimal("50000.0")
            mock_order.volume_total_original = 1
            mock_order.volume_traded = 0
            mock_order.volume_total = 1
            mock_order.order_status = "4"
            mock_order.insert_time = "09:30:00"
            mock_order.created_at = None
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_order]
            mock_session.execute.return_value = mock_result
            
            orders = await ctp_service.query_orders(user_id=1)
            
            assert len(orders) == 1
            assert orders[0]["id"] == "test-order-id"
            assert orders[0]["order_ref"] == "000000001"
            assert orders[0]["symbol"] == "cu2401"
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, ctp_service):
        """测试订阅行情数据"""
        ctp_service.status.md_connected = True
        ctp_service.status.md_logged_in = True
        
        symbols = ["cu2401", "au2312"]
        result = await ctp_service.subscribe_market_data(symbols)
        
        assert result is True
        assert ctp_service.status.subscribe_count == 2
        assert "cu2401" in ctp_service.ticks
        assert "au2312" in ctp_service.ticks
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data_limit_exceeded(self, ctp_service):
        """测试订阅数量超过限制"""
        ctp_service.status.md_connected = True
        ctp_service.status.md_logged_in = True
        
        # 创建超过限制的订阅列表
        symbols = [f"symbol{i}" for i in range(ctp_service.config.max_subscribe_count + 1)]
        
        with pytest.raises(CTPError) as exc_info:
            await ctp_service.subscribe_market_data(symbols)
        
        assert "订阅数量超过限制" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_unsubscribe_market_data(self, ctp_service):
        """测试取消订阅行情数据"""
        ctp_service.status.md_connected = True
        ctp_service.status.md_logged_in = True
        
        # 先订阅
        symbols = ["cu2401", "au2312"]
        await ctp_service.subscribe_market_data(symbols)
        
        # 取消订阅
        result = await ctp_service.unsubscribe_market_data(["cu2401"])
        
        assert result is True
        assert ctp_service.status.subscribe_count == 1
        assert "cu2401" not in ctp_service.ticks
        assert "au2312" in ctp_service.ticks
    
    @pytest.mark.asyncio
    async def test_get_tick_data(self, ctp_service):
        """测试获取行情数据"""
        # 模拟行情数据
        tick_data = {
            "symbol": "cu2401",
            "last_price": 50000.0,
            "bid_price": 49990.0,
            "ask_price": 50010.0,
            "volume": 1000
        }
        ctp_service.ticks["cu2401"] = tick_data
        
        result = await ctp_service.get_tick_data("cu2401")
        
        assert result == tick_data
        assert result["symbol"] == "cu2401"
        assert result["last_price"] == 50000.0
    
    @pytest.mark.asyncio
    async def test_disconnect(self, ctp_service):
        """测试断开连接"""
        # 设置初始状态
        ctp_service._trade_connected = True
        ctp_service._md_connected = True
        ctp_service.status.trade_connected = True
        ctp_service.status.md_connected = True
        ctp_service.orders["test"] = {}
        ctp_service.ticks["cu2401"] = {}
        
        with patch('app.services.ctp_service.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_session.close = AsyncMock()
            ctp_service._db_session = mock_session
            
            await ctp_service.disconnect()
            
            assert ctp_service._trade_connected is False
            assert ctp_service._md_connected is False
            assert ctp_service.status.trade_connected is False
            assert ctp_service.status.md_connected is False
            assert len(ctp_service.orders) == 0
            assert len(ctp_service.ticks) == 0
    
    @pytest.mark.asyncio
    async def test_reconnect(self, ctp_service):
        """测试重新连接"""
        with patch.object(ctp_service, 'disconnect', new_callable=AsyncMock) as mock_disconnect, \
             patch.object(ctp_service, 'initialize', new_callable=AsyncMock, return_value=True) as mock_init:
            
            result = await ctp_service.reconnect()
            
            assert result is True
            mock_disconnect.assert_called_once()
            mock_init.assert_called_once()
    
    def test_get_exchange_id(self, ctp_service):
        """测试获取交易所代码"""
        assert ctp_service._get_exchange_id("cu2401") == "SHFE"
        assert ctp_service._get_exchange_id("c2401") == "DCE"
        assert ctp_service._get_exchange_id("CF401") == "CZCE"
        assert ctp_service._get_exchange_id("unknown") == "SHFE"  # 默认
    
    def test_convert_direction(self, ctp_service):
        """测试转换交易方向"""
        assert ctp_service._convert_direction("BUY") == "0"
        assert ctp_service._convert_direction("LONG") == "0"
        assert ctp_service._convert_direction("SELL") == "1"
        assert ctp_service._convert_direction("SHORT") == "1"
    
    def test_convert_offset(self, ctp_service):
        """测试转换开平标志"""
        assert ctp_service._convert_offset("OPEN") == "0"
        assert ctp_service._convert_offset("CLOSE") == "1"
        assert ctp_service._convert_offset("CLOSE_TODAY") == "3"
        assert ctp_service._convert_offset("CLOSE_YESTERDAY") == "4"
        assert ctp_service._convert_offset("UNKNOWN") == "0"  # 默认
    
    def test_convert_order_type(self, ctp_service):
        """测试转换订单类型"""
        assert ctp_service._convert_order_type("LIMIT") == "2"
        assert ctp_service._convert_order_type("MARKET") == "1"
        assert ctp_service._convert_order_type("STOP") == "3"
        assert ctp_service._convert_order_type("UNKNOWN") == "2"  # 默认
    
    def test_callback_management(self, ctp_service):
        """测试回调函数管理"""
        callback_func = Mock()
        
        # 添加回调
        ctp_service.add_callback('on_tick', callback_func)
        assert callback_func in ctp_service.callbacks['on_tick']
        
        # 移除回调
        ctp_service.remove_callback('on_tick', callback_func)
        assert callback_func not in ctp_service.callbacks['on_tick']


class TestCTPMarketDataService:
    """CTP行情数据服务测试类"""
    
    @pytest.fixture
    def ctp_service(self):
        """CTP服务fixture"""
        return Mock()
    
    @pytest.fixture
    def market_service(self, ctp_service):
        """行情服务fixture"""
        return CTPMarketDataService(ctp_service)
    
    @pytest.mark.asyncio
    async def test_subscribe(self, market_service):
        """测试客户端订阅行情"""
        market_service.ctp_service.subscribe_market_data = AsyncMock()
        
        await market_service.subscribe("client1", ["cu2401", "au2312"])
        
        assert "client1" in market_service.client_subscriptions
        assert "cu2401" in market_service.client_subscriptions["client1"]
        assert "au2312" in market_service.client_subscriptions["client1"]
        assert "cu2401" in market_service.subscribers
        assert "au2312" in market_service.subscribers
        assert "client1" in market_service.subscribers["cu2401"]
        assert "client1" in market_service.subscribers["au2312"]
        
        market_service.ctp_service.subscribe_market_data.assert_called_once_with(["cu2401", "au2312"])
    
    @pytest.mark.asyncio
    async def test_subscribe_existing_symbol(self, market_service):
        """测试订阅已存在的合约"""
        market_service.ctp_service.subscribe_market_data = AsyncMock()
        
        # 第一个客户端订阅
        await market_service.subscribe("client1", ["cu2401"])
        
        # 第二个客户端订阅相同合约
        await market_service.subscribe("client2", ["cu2401"])
        
        assert "client1" in market_service.subscribers["cu2401"]
        assert "client2" in market_service.subscribers["cu2401"]
        
        # 只应该调用一次CTP订阅（第一次）
        market_service.ctp_service.subscribe_market_data.assert_called_once_with(["cu2401"])
    
    @pytest.mark.asyncio
    async def test_unsubscribe_specific_symbols(self, market_service):
        """测试取消订阅指定合约"""
        market_service.ctp_service.subscribe_market_data = AsyncMock()
        market_service.ctp_service.unsubscribe_market_data = AsyncMock()
        
        # 先订阅
        await market_service.subscribe("client1", ["cu2401", "au2312"])
        
        # 取消订阅部分合约
        await market_service.unsubscribe("client1", ["cu2401"])
        
        assert "cu2401" not in market_service.client_subscriptions["client1"]
        assert "au2312" in market_service.client_subscriptions["client1"]
        assert "cu2401" not in market_service.subscribers
        assert "au2312" in market_service.subscribers
        
        market_service.ctp_service.unsubscribe_market_data.assert_called_once_with(["cu2401"])
    
    @pytest.mark.asyncio
    async def test_unsubscribe_all_symbols(self, market_service):
        """测试取消订阅所有合约"""
        market_service.ctp_service.subscribe_market_data = AsyncMock()
        market_service.ctp_service.unsubscribe_market_data = AsyncMock()
        
        # 先订阅
        await market_service.subscribe("client1", ["cu2401", "au2312"])
        
        # 取消所有订阅
        await market_service.unsubscribe("client1")
        
        assert "client1" not in market_service.client_subscriptions
        assert "cu2401" not in market_service.subscribers
        assert "au2312" not in market_service.subscribers
        
        market_service.ctp_service.unsubscribe_market_data.assert_called_once_with(["cu2401", "au2312"])
    
    def test_get_subscribers(self, market_service):
        """测试获取合约订阅客户端"""
        market_service.subscribers["cu2401"] = {"client1", "client2"}
        
        subscribers = market_service.get_subscribers("cu2401")
        assert subscribers == {"client1", "client2"}
        
        subscribers = market_service.get_subscribers("nonexistent")
        assert subscribers == set()
    
    def test_get_client_subscriptions(self, market_service):
        """测试获取客户端订阅合约"""
        market_service.client_subscriptions["client1"] = {"cu2401", "au2312"}
        
        subscriptions = market_service.get_client_subscriptions("client1")
        assert subscriptions == {"cu2401", "au2312"}
        
        subscriptions = market_service.get_client_subscriptions("nonexistent")
        assert subscriptions == set()
