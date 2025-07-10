"""
CTP API测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.services.ctp_service import ctp_service
from app.core.ctp_config import CTPStatus
from app.schemas.trading import OrderRequest, OrderResponse


class TestCTPAPI:
    """CTP API测试类"""
    
    @pytest.fixture
    def client(self):
        """测试客户端fixture"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """异步测试客户端fixture"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户fixture"""
        user = Mock()
        user.id = 1
        user.username = "test_user"
        user.is_active = True
        return user
    
    @pytest.fixture
    def auth_headers(self):
        """认证头fixture"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.fixture
    def ctp_status(self):
        """CTP状态fixture"""
        status = CTPStatus()
        status.trade_connected = True
        status.md_connected = True
        status.trade_logged_in = True
        status.md_logged_in = True
        status.order_count = 10
        status.trade_count = 5
        status.subscribe_count = 3
        return status
    
    @pytest.mark.asyncio
    async def test_get_ctp_status(self, async_client, mock_user, auth_headers, ctp_status):
        """测试获取CTP状态"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'get_status', return_value=ctp_status):
            
            response = await async_client.get("/api/v1/ctp/status", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["trade_connected"] is True
            assert data["data"]["md_connected"] is True
            assert data["data"]["is_ready"] is True
            assert data["data"]["order_count"] == 10
            assert data["data"]["trade_count"] == 5
    
    @pytest.mark.asyncio
    async def test_initialize_ctp_success(self, async_client, mock_user, auth_headers, ctp_status):
        """测试初始化CTP成功"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'initialize', new_callable=AsyncMock, return_value=True), \
             patch.object(ctp_service, 'get_status', return_value=ctp_status):
            
            response = await async_client.post("/api/v1/ctp/initialize", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "CTP连接初始化成功" in data["message"]
    
    @pytest.mark.asyncio
    async def test_initialize_ctp_failure(self, async_client, mock_user, auth_headers):
        """测试初始化CTP失败"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'initialize', new_callable=AsyncMock, return_value=False):
            
            response = await async_client.post("/api/v1/ctp/initialize", headers=auth_headers)
            
            assert response.status_code == 500
            data = response.json()
            assert "CTP连接初始化失败" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_initialize_ctp_inactive_user(self, async_client, auth_headers):
        """测试未激活用户初始化CTP"""
        inactive_user = Mock()
        inactive_user.is_active = False
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=inactive_user):
            response = await async_client.post("/api/v1/ctp/initialize", headers=auth_headers)
            
            assert response.status_code == 403
            data = response.json()
            assert "用户账户未激活" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_disconnect_ctp(self, async_client, mock_user, auth_headers):
        """测试断开CTP连接"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'disconnect', new_callable=AsyncMock):
            
            response = await async_client.post("/api/v1/ctp/disconnect", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "CTP连接已断开" in data["message"]
    
    @pytest.mark.asyncio
    async def test_reconnect_ctp_success(self, async_client, mock_user, auth_headers, ctp_status):
        """测试重新连接CTP成功"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'reconnect', new_callable=AsyncMock, return_value=True), \
             patch.object(ctp_service, 'get_status', return_value=ctp_status):
            
            response = await async_client.post("/api/v1/ctp/reconnect", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "CTP重新连接成功" in data["message"]
    
    @pytest.mark.asyncio
    async def test_submit_ctp_order_success(self, async_client, mock_user, auth_headers):
        """测试提交CTP订单成功"""
        order_request = {
            "symbol": "cu2401",
            "direction": "BUY",
            "offset": "OPEN",
            "order_type": "LIMIT",
            "volume": 1,
            "price": 50000.0
        }
        
        order_response = OrderResponse(
            success=True,
            message="订单提交成功",
            data={
                "order_ref": "000000001",
                "order_id": "test-order-id",
                "symbol": "cu2401",
                "direction": "BUY",
                "price": 50000.0,
                "volume": 1,
                "status": "SUBMITTED"
            }
        )
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.ctp.get_db'), \
             patch('app.api.v1.ctp.RiskService') as mock_risk_service, \
             patch.object(ctp_service, 'submit_order', new_callable=AsyncMock, return_value=order_response), \
             patch('app.api.v1.ctp.websocket_manager') as mock_ws_manager:
            
            # 模拟风险检查通过
            mock_risk_check = Mock()
            mock_risk_check.is_valid = True
            mock_risk_service.return_value.check_order_risk = AsyncMock(return_value=mock_risk_check)
            mock_ws_manager.broadcast_to_user = AsyncMock()
            
            response = await async_client.post(
                "/api/v1/ctp/orders",
                json=order_request,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["order_ref"] == "000000001"
            assert data["data"]["symbol"] == "cu2401"
    
    @pytest.mark.asyncio
    async def test_submit_ctp_order_risk_check_failed(self, async_client, mock_user, auth_headers):
        """测试提交CTP订单风险检查失败"""
        order_request = {
            "symbol": "cu2401",
            "direction": "BUY",
            "offset": "OPEN",
            "order_type": "LIMIT",
            "volume": 1,
            "price": 50000.0
        }
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch('app.api.v1.ctp.get_db'), \
             patch('app.api.v1.ctp.RiskService') as mock_risk_service:
            
            # 模拟风险检查失败
            mock_risk_check = Mock()
            mock_risk_check.is_valid = False
            mock_risk_check.message = "资金不足"
            mock_risk_service.return_value.check_order_risk = AsyncMock(return_value=mock_risk_check)
            
            response = await async_client.post(
                "/api/v1/ctp/orders",
                json=order_request,
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "风险检查失败: 资金不足" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_cancel_ctp_order_success(self, async_client, mock_user, auth_headers):
        """测试撤销CTP订单成功"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'cancel_order', new_callable=AsyncMock, return_value=True), \
             patch('app.api.v1.ctp.websocket_manager') as mock_ws_manager:
            
            mock_ws_manager.broadcast_to_user = AsyncMock()
            
            response = await async_client.delete("/api/v1/ctp/orders/000000001", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "订单 000000001 撤销成功" in data["message"]
    
    @pytest.mark.asyncio
    async def test_cancel_ctp_order_failure(self, async_client, mock_user, auth_headers):
        """测试撤销CTP订单失败"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'cancel_order', new_callable=AsyncMock, return_value=False):
            
            response = await async_client.delete("/api/v1/ctp/orders/000000001", headers=auth_headers)
            
            assert response.status_code == 400
            data = response.json()
            assert "订单 000000001 撤销失败" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_query_ctp_orders(self, async_client, mock_user, auth_headers):
        """测试查询CTP订单"""
        mock_orders = [
            {
                "id": "order1",
                "order_ref": "000000001",
                "symbol": "cu2401",
                "direction": "0",
                "price": 50000.0,
                "volume": 1,
                "status": "4"
            },
            {
                "id": "order2",
                "order_ref": "000000002",
                "symbol": "au2312",
                "direction": "1",
                "price": 450.0,
                "volume": 2,
                "status": "1"
            }
        ]
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'query_orders', new_callable=AsyncMock, return_value=mock_orders):
            
            response = await async_client.get("/api/v1/ctp/orders", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 2
            assert len(data["data"]) == 2
            assert data["data"][0]["order_ref"] == "000000001"
            assert data["data"][1]["order_ref"] == "000000002"
    
    @pytest.mark.asyncio
    async def test_query_ctp_trades(self, async_client, mock_user, auth_headers):
        """测试查询CTP成交"""
        mock_trades = [
            {
                "id": "trade1",
                "trade_id": "T123456789",
                "order_ref": "000000001",
                "symbol": "cu2401",
                "price": 50000.0,
                "volume": 1
            }
        ]
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'query_trades', new_callable=AsyncMock, return_value=mock_trades):
            
            response = await async_client.get("/api/v1/ctp/trades", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 1
            assert data["data"][0]["trade_id"] == "T123456789"
    
    @pytest.mark.asyncio
    async def test_query_ctp_positions(self, async_client, mock_user, auth_headers):
        """测试查询CTP持仓"""
        mock_positions = [
            {
                "id": "pos1",
                "symbol": "cu2401",
                "direction": "2",
                "position": 10,
                "cost": 500000.0,
                "profit": 1000.0
            }
        ]
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'query_positions', new_callable=AsyncMock, return_value=mock_positions):
            
            response = await async_client.get("/api/v1/ctp/positions", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 1
            assert data["data"][0]["symbol"] == "cu2401"
    
    @pytest.mark.asyncio
    async def test_query_ctp_account(self, async_client, mock_user, auth_headers):
        """测试查询CTP账户"""
        mock_account = {
            "id": "acc1",
            "account_id": "123456789",
            "balance": 1000000.0,
            "available": 800000.0,
            "margin": 200000.0,
            "position_profit": 5000.0
        }
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'query_account', new_callable=AsyncMock, return_value=mock_account):
            
            response = await async_client.get("/api/v1/ctp/account", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["account_id"] == "123456789"
            assert data["data"]["balance"] == 1000000.0
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, async_client, mock_user, auth_headers):
        """测试订阅行情数据"""
        symbols = ["cu2401", "au2312"]
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'subscribe_market_data', new_callable=AsyncMock, return_value=True):
            
            response = await async_client.post(
                "/api/v1/ctp/market/subscribe",
                json=symbols,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "订阅行情成功" in data["message"]
            assert data["data"]["symbols"] == symbols
    
    @pytest.mark.asyncio
    async def test_unsubscribe_market_data(self, async_client, mock_user, auth_headers):
        """测试取消订阅行情数据"""
        symbols = ["cu2401"]
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'unsubscribe_market_data', new_callable=AsyncMock, return_value=True):
            
            response = await async_client.post(
                "/api/v1/ctp/market/unsubscribe",
                json=symbols,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "取消订阅行情成功" in data["message"]
    
    @pytest.mark.asyncio
    async def test_get_tick_data_found(self, async_client, mock_user, auth_headers):
        """测试获取行情数据（找到数据）"""
        mock_tick = {
            "symbol": "cu2401",
            "last_price": 50000.0,
            "bid_price": 49990.0,
            "ask_price": 50010.0,
            "volume": 1000,
            "timestamp": "2024-01-01T09:30:00"
        }
        
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'get_tick_data', new_callable=AsyncMock, return_value=mock_tick):
            
            response = await async_client.get("/api/v1/ctp/market/tick/cu2401", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["symbol"] == "cu2401"
            assert data["data"]["last_price"] == 50000.0
    
    @pytest.mark.asyncio
    async def test_get_tick_data_not_found(self, async_client, mock_user, auth_headers):
        """测试获取行情数据（未找到数据）"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'get_tick_data', new_callable=AsyncMock, return_value=None):
            
            response = await async_client.get("/api/v1/ctp/market/tick/cu2401", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "未找到合约 cu2401 的行情数据" in data["message"]
            assert data["data"] is None
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, async_client, mock_user, auth_headers):
        """测试API错误处理"""
        with patch('app.api.v1.ctp.get_current_active_user', return_value=mock_user), \
             patch.object(ctp_service, 'get_status', side_effect=Exception("测试错误")):
            
            response = await async_client.get("/api/v1/ctp/status", headers=auth_headers)
            
            assert response.status_code == 500
            data = response.json()
            assert "获取CTP状态失败" in data["detail"]
