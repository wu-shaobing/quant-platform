"""
风险管理API集成测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.main import app
from app.schemas.trading import RiskLimitData, RiskCheckResult, OrderRequest, OrderType, OrderSide


@pytest.mark.integration
@pytest.mark.risk
@pytest.mark.asyncio
class TestRiskAPI:
    """风险管理API测试类"""

    @pytest.fixture
    def auth_headers(self, mock_user_token):
        """认证头部"""
        return {"Authorization": f"Bearer {mock_user_token}"}

    @pytest.fixture
    def admin_headers(self, mock_admin_token):
        """管理员认证头部"""
        return {"Authorization": f"Bearer {mock_admin_token}"}

    @pytest.fixture
    def mock_user_token(self):
        """模拟用户令牌"""
        return "mock-jwt-token"

    @pytest.fixture
    def mock_admin_token(self):
        """模拟管理员令牌"""
        return "mock-admin-jwt-token"

    @pytest.fixture
    def sample_risk_limits(self):
        """示例风控限制"""
        return {
            "max_position": 20000.0,
            "max_order_size": 10000.0,
            "max_daily_loss": 50000.0,
            "max_total_loss": 100000.0,
            "allowed_symbols": ["000001", "000002", "000300"],
            "forbidden_symbols": ["000003", "000004"]
        }

    @pytest.fixture
    def sample_order_request(self):
        """示例订单请求"""
        return {
            "symbol": "000001",
            "order_type": "limit",
            "side": "buy",
            "quantity": 100,
            "price": 105.50,
            "time_in_force": "GTC"
        }

    async def test_get_risk_limits_success(self, auth_headers, sample_risk_limits):
        """测试成功获取风控限制"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_risk_limits.return_value = Mock(**sample_risk_limits)
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/limits",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["max_position"] == 20000.0
                assert data["max_order_size"] == 10000.0
                assert data["max_daily_loss"] == 50000.0

    async def test_get_risk_limits_default(self, auth_headers):
        """测试获取默认风控限制"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_risk_limits.return_value = None  # 用户无自定义设置
            mock_service.get_default_risk_limits.return_value = Mock(
                max_position=10000.0,
                max_order_size=5000.0,
                max_daily_loss=30000.0,
                max_total_loss=60000.0,
                allowed_symbols=[],
                forbidden_symbols=[]
            )
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/limits",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["max_position"] == 10000.0
                assert data["max_order_size"] == 5000.0

    async def test_update_risk_limits_success(self, auth_headers, sample_risk_limits):
        """测试成功更新风控限制"""
        update_data = {
            "max_position": 30000.0,
            "max_order_size": 15000.0,
            "max_daily_loss": 60000.0,
            "max_total_loss": 120000.0,
            "allowed_symbols": ["000001", "000002"],
            "forbidden_symbols": ["000003"]
        }
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.update_user_risk_limits.return_value = Mock(**update_data)
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.put(
                        "/api/v1/risk/limits",
                        json=update_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["max_position"] == 30000.0
                assert data["max_order_size"] == 15000.0
                mock_service.update_user_risk_limits.assert_called_once()

    async def test_check_order_risk_success(self, auth_headers, sample_order_request):
        """测试订单风险检查成功"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.check_order_risk.return_value = RiskCheckResult(
                passed=True,
                message="风险检查通过",
                details={"checks": ["user_status", "fund_sufficiency", "position_limit", "order_size"]}
            )
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/risk/check-order",
                        json=sample_order_request,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["passed"] is True
                assert "风险检查通过" in data["message"]

    async def test_check_order_risk_failed(self, auth_headers, sample_order_request):
        """测试订单风险检查失败"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.check_order_risk.return_value = RiskCheckResult(
                passed=False,
                message="资金不足",
                details={"required": 10550.0, "available": 5000.0}
            )
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/risk/check-order",
                        json=sample_order_request,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["passed"] is False
                assert "资金不足" in data["message"]

    async def test_get_risk_metrics_success(self, auth_headers):
        """测试获取风险指标成功"""
        mock_metrics = {
            "portfolio_value": 100000.0,
            "var_95": 0.03,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.2,
            "beta": 1.1,
            "volatility": 0.18,
            "concentration": {
                "top_holdings": 0.25,
                "sectors": {"科技": 0.35, "金融": 0.25, "消费": 0.20}
            },
            "leverage": 1.5
        }
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.calculate_portfolio_risk.return_value = mock_metrics
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/metrics",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["portfolio_value"] == 100000.0
                assert data["var_95"] == 0.03
                assert data["concentration"]["top_holdings"] == 0.25

    async def test_get_risk_alerts_success(self, auth_headers):
        """测试获取风险预警成功"""
        mock_alerts = [
            {
                "id": 1,
                "alert_type": "position_limit",
                "severity": "high",
                "message": "持仓超限预警",
                "created_at": datetime.now().isoformat(),
                "status": "active"
            },
            {
                "id": 2,
                "alert_type": "daily_loss",
                "severity": "medium",
                "message": "日亏损接近限额",
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
        ]
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_risk_alerts.return_value = [Mock(**alert) for alert in mock_alerts]
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/alerts",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["alert_type"] == "position_limit"
                assert data[1]["severity"] == "medium"

    async def test_acknowledge_risk_alert_success(self, auth_headers):
        """测试确认风险预警成功"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_alert = Mock()
            mock_alert.user_id = 1
            mock_service.get_risk_alert_by_id.return_value = mock_alert
            mock_service.acknowledge_risk_alert.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/risk/alerts/1/acknowledge",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert "预警已确认" in data["message"]

    async def test_acknowledge_risk_alert_not_found(self, auth_headers):
        """测试确认不存在的风险预警"""
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_risk_alert_by_id.return_value = None
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/risk/alerts/999/acknowledge",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 404
                assert "预警不存在" in response.json()["detail"]

    async def test_run_risk_monitoring_success(self, auth_headers):
        """测试运行风险监控成功"""
        mock_monitoring_result = {
            "status": "completed",
            "checks": {
                "daily_loss": {"passed": True, "message": "正常"},
                "total_loss": {"passed": True, "message": "正常"},
                "position_limits": {"passed": True, "message": "正常"}
            },
            "risk_metrics": {
                "var": 0.03,
                "concentration": 0.2,
                "leverage": 1.5
            },
            "alerts_generated": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.run_risk_monitoring.return_value = mock_monitoring_result
            
            # Mock用户认证
            with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/risk/monitoring/run",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "completed"
                assert "checks" in data
                assert "risk_metrics" in data

    async def test_get_risk_statistics_admin_success(self, admin_headers):
        """测试管理员获取风险统计成功"""
        mock_statistics = {
            "total_users": 1000,
            "active_alerts": 25,
            "critical_alerts": 3,
            "risk_level_distribution": {
                "low": 600,
                "medium": 300,
                "high": 80,
                "critical": 20
            },
            "daily_violations": 5,
            "top_risk_symbols": ["000001", "000002", "000003"],
            "average_portfolio_var": 0.035
        }
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_risk_statistics.return_value = mock_statistics
            
            # Mock管理员认证
            with patch('app.api.v1.risk.get_current_admin_user') as mock_auth:
                mock_admin = Mock()
                mock_admin.id = 1
                mock_admin.is_admin = True
                mock_auth.return_value = mock_admin
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/admin/statistics",
                        headers=admin_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["total_users"] == 1000
                assert data["active_alerts"] == 25
                assert data["critical_alerts"] == 3

    async def test_get_all_risk_alerts_admin_success(self, admin_headers):
        """测试管理员获取所有风险预警成功"""
        mock_alerts = [
            {"id": 1, "user_id": 1, "alert_type": "position_limit", "severity": "high"},
            {"id": 2, "user_id": 2, "alert_type": "daily_loss", "severity": "medium"},
            {"id": 3, "user_id": 3, "alert_type": "total_loss", "severity": "critical"}
        ]
        
        with patch('app.api.v1.risk.RiskService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_all_risk_alerts.return_value = [Mock(**alert) for alert in mock_alerts]
            
            # Mock管理员认证
            with patch('app.api.v1.risk.get_current_admin_user') as mock_auth:
                mock_admin = Mock()
                mock_admin.id = 1
                mock_admin.is_admin = True
                mock_auth.return_value = mock_admin
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/risk/admin/alerts",
                        headers=admin_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["total"] == 3
                assert len(data["alerts"]) == 3
                assert data["alerts"][0]["alert_type"] == "position_limit"

    async def test_health_check(self):
        """测试健康检查"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/risk/health")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "risk"
        assert "timestamp" in data

    async def test_unauthorized_access(self):
        """测试未授权访问"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/risk/limits")
        
        # 验证响应
        assert response.status_code == 401

    async def test_non_admin_access_admin_endpoints(self, auth_headers):
        """测试非管理员访问管理员端点"""
        # Mock普通用户认证
        with patch('app.api.v1.risk.get_current_admin_user') as mock_auth:
            mock_auth.side_effect = Exception("权限不足")

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/risk/admin/statistics",
                    headers=auth_headers
                )

            # 验证响应
            assert response.status_code == 403 or response.status_code == 500

    async def test_invalid_order_request(self, auth_headers):
        """测试无效订单请求"""
        invalid_order = {
            "symbol": "",  # 空标的
            "order_type": "invalid_type",  # 无效类型
            "side": "buy",
            "quantity": -100,  # 负数量
            "price": 0,  # 零价格
            "time_in_force": "GTC"
        }

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/risk/check-order",
                json=invalid_order,
                headers=auth_headers
            )

        # 验证响应
        assert response.status_code == 422  # 验证错误

    async def test_risk_limits_validation(self, auth_headers):
        """测试风控限制验证"""
        invalid_limits = {
            "max_position": -1000.0,  # 负值
            "max_order_size": 0,  # 零值
            "max_daily_loss": -50000.0,  # 负值（应该是正值表示限额）
            "max_total_loss": -100000.0,  # 负值
            "allowed_symbols": None,
            "forbidden_symbols": None
        }

        # Mock用户认证
        with patch('app.api.v1.risk.get_current_active_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = 1
            mock_auth.return_value = mock_user

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/risk/limits",
                    json=invalid_limits,
                    headers=auth_headers
                )

            # 验证响应
            assert response.status_code == 422  # 验证错误
