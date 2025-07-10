"""
回测API集成测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.main import app
from app.models.backtest import BacktestTask, BacktestStatus, BacktestType
from app.schemas.backtest import BacktestCreate, RebalanceFrequency, BenchmarkType


@pytest.mark.integration
@pytest.mark.backtest
@pytest.mark.asyncio
class TestBacktestAPI:
    """回测API测试类"""

    @pytest.fixture
    def auth_headers(self, mock_user_token):
        """认证头部"""
        return {"Authorization": f"Bearer {mock_user_token}"}

    @pytest.fixture
    def mock_user_token(self):
        """模拟用户令牌"""
        return "mock-jwt-token"

    @pytest.fixture
    def sample_backtest_data(self):
        """示例回测数据"""
        return {
            "name": "MACD策略回测",
            "description": "基于MACD指标的趋势跟踪策略回测",
            "strategy_id": "test-strategy-id",
            "start_date": "2023-01-01T00:00:00",
            "end_date": "2023-12-31T23:59:59",
            "initial_capital": 100000.00,
            "symbols": ["000001", "000002", "000300"],
            "benchmark": "000300",
            "commission_rate": 0.0003,
            "slippage_rate": 0.001,
            "min_commission": 5.0,
            "rebalance_frequency": "daily",
            "max_position_size": 0.2,
            "max_leverage": 1.0,
            "stop_loss": 0.05,
            "take_profit": 0.15,
            "max_drawdown_limit": 0.1,
            "parameters": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        }

    @pytest.fixture
    def mock_backtest_response(self):
        """模拟回测响应数据"""
        return {
            "id": "test-backtest-id",
            "name": "MACD策略回测",
            "description": "基于MACD指标的趋势跟踪策略回测",
            "strategy_id": "test-strategy-id",
            "user_id": 1,
            "status": "pending",
            "start_date": "2023-01-01T00:00:00",
            "end_date": "2023-12-31T23:59:59",
            "initial_capital": 100000.00,
            "symbols": ["000001", "000002", "000300"],
            "benchmark": "000300",
            "commission_rate": 0.0003,
            "slippage_rate": 0.001,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "progress": 0.0
        }

    async def test_create_backtest_success(self, auth_headers, sample_backtest_data, mock_backtest_response):
        """测试成功创建回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.create_backtest.return_value = Mock(**mock_backtest_response)
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/backtest/",
                        json=sample_backtest_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "MACD策略回测"
                assert data["strategy_id"] == "test-strategy-id"
                assert data["status"] == "pending"
                mock_service.create_backtest.assert_called_once()

    async def test_create_backtest_invalid_date_range(self, auth_headers, sample_backtest_data):
        """测试创建回测时日期范围无效"""
        # 设置无效的日期范围
        invalid_data = sample_backtest_data.copy()
        invalid_data["start_date"] = "2023-12-31T00:00:00"
        invalid_data["end_date"] = "2023-01-01T00:00:00"
        
        # Mock用户认证
        with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = 1
            mock_auth.return_value = mock_user
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/backtest/",
                    json=invalid_data,
                    headers=auth_headers
                )
            
            # 验证响应
            assert response.status_code == 400
            assert "回测开始日期必须早于结束日期" in response.json()["detail"]

    async def test_create_backtest_invalid_capital(self, auth_headers, sample_backtest_data):
        """测试创建回测时初始资金无效"""
        # 设置无效的初始资金
        invalid_data = sample_backtest_data.copy()
        invalid_data["initial_capital"] = 0
        
        # Mock用户认证
        with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = 1
            mock_auth.return_value = mock_user
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/backtest/",
                    json=invalid_data,
                    headers=auth_headers
                )
            
            # 验证响应
            assert response.status_code == 400
            assert "初始资金必须大于0" in response.json()["detail"]

    async def test_get_backtest_success(self, auth_headers, mock_backtest_response):
        """测试成功获取回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock(**mock_backtest_response)
            mock_backtest.user_id = 1
            mock_service.get_backtest_by_id.return_value = mock_backtest
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/backtest/test-backtest-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "test-backtest-id"
                assert data["name"] == "MACD策略回测"

    async def test_get_backtest_not_found(self, auth_headers):
        """测试获取不存在的回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_backtest_by_id.return_value = None
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/backtest/nonexistent-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 404
                assert "回测不存在" in response.json()["detail"]

    async def test_start_backtest_success(self, auth_headers):
        """测试成功启动回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 1
            mock_backtest.status = BacktestStatus.PENDING
            mock_service.get_backtest_by_id.return_value = mock_backtest
            mock_service.start_backtest.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                # Mock后台任务
                with patch('app.api.v1.backtest.BackgroundTasks') as mock_bg_tasks:
                    mock_bg_tasks_instance = Mock()
                    mock_bg_tasks.return_value = mock_bg_tasks_instance
                    
                    async with AsyncClient(app=app, base_url="http://test") as client:
                        response = await client.post(
                            "/api/v1/backtest/test-backtest-id/start",
                            headers=auth_headers
                        )
                    
                    # 验证响应
                    assert response.status_code == 200
                    data = response.json()
                    assert "回测已启动" in data["message"]

    async def test_start_backtest_already_running(self, auth_headers):
        """测试启动已运行的回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 1
            mock_backtest.status = BacktestStatus.RUNNING
            mock_service.get_backtest_by_id.return_value = mock_backtest
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/backtest/test-backtest-id/start",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 400
                assert "回测已在运行中" in response.json()["detail"]

    async def test_stop_backtest_success(self, auth_headers):
        """测试成功停止回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 1
            mock_backtest.status = BacktestStatus.RUNNING
            mock_service.get_backtest_by_id.return_value = mock_backtest
            mock_service.stop_backtest.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/backtest/test-backtest-id/stop",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert "回测已停止" in data["message"]

    async def test_get_backtest_result(self, auth_headers):
        """测试获取回测结果"""
        mock_result = {
            "id": "test-result-id",
            "backtest_id": "test-backtest-id",
            "total_return": 0.15,
            "annual_return": 0.12,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.5,
            "win_rate": 0.65,
            "total_trades": 150,
            "profit_loss_ratio": 1.8,
            "volatility": 0.15,
            "beta": 0.9,
            "alpha": 0.03
        }
        
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 1
            mock_service.get_backtest_by_id.return_value = mock_backtest
            mock_service.get_backtest_result.return_value = Mock(**mock_result)
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/backtest/test-backtest-id/result",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["total_return"] == 0.15
                assert data["sharpe_ratio"] == 1.5
                assert data["win_rate"] == 0.65

    async def test_get_user_backtests(self, auth_headers):
        """测试获取用户回测列表"""
        mock_backtests = [
            {"id": "backtest-1", "name": "策略1回测", "status": "completed"},
            {"id": "backtest-2", "name": "策略2回测", "status": "running"},
            {"id": "backtest-3", "name": "策略3回测", "status": "pending"}
        ]
        
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_user_backtests.return_value = [Mock(**bt) for bt in mock_backtests]
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/backtest/",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 3
                assert data[0]["name"] == "策略1回测"

    async def test_analyze_backtest(self, auth_headers):
        """测试分析回测结果"""
        analysis_request = {
            "analysis_type": "performance",
            "metrics": ["sharpe_ratio", "max_drawdown", "win_rate"],
            "chart_types": ["equity_curve", "drawdown_curve"]
        }
        
        mock_analysis_result = {
            "analysis_type": "performance",
            "metrics": {
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.08,
                "win_rate": 0.65
            },
            "charts": [
                {"type": "equity_curve", "data": []},
                {"type": "drawdown_curve", "data": []}
            ],
            "insights": [
                "策略表现良好，夏普比率为1.5",
                "最大回撤控制在8%以内"
            ]
        }
        
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 1
            mock_service.get_backtest_by_id.return_value = mock_backtest
            mock_service.analyze_backtest.return_value = mock_analysis_result
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/backtest/test-backtest-id/analyze",
                        json=analysis_request,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["analysis_type"] == "performance"
                assert "metrics" in data
                assert "charts" in data
                assert "insights" in data

    async def test_unauthorized_access(self):
        """测试未授权访问"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/backtest/test-backtest-id")
        
        # 验证响应
        assert response.status_code == 401

    async def test_access_other_user_backtest(self, auth_headers):
        """测试访问其他用户的回测"""
        with patch('app.api.v1.backtest.BacktestService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_backtest = Mock()
            mock_backtest.user_id = 2  # 不同的用户ID
            mock_service.get_backtest_by_id.return_value = mock_backtest
            
            # Mock用户认证
            with patch('app.api.v1.backtest.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1  # 当前用户ID
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/backtest/test-backtest-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 404
                assert "回测不存在" in response.json()["detail"]
