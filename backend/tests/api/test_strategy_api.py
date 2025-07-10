"""
策略API集成测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.strategy import Strategy, StrategyType, StrategyStatus, RiskLevel
from app.schemas.strategy import StrategyCreate, StrategyOptimizationRequest


@pytest.mark.integration
@pytest.mark.strategy
@pytest.mark.asyncio
class TestStrategyAPI:
    """策略API测试类"""

    @pytest.fixture
    def auth_headers(self, mock_user_token):
        """认证头部"""
        return {"Authorization": f"Bearer {mock_user_token}"}

    @pytest.fixture
    def mock_user_token(self):
        """模拟用户令牌"""
        return "mock-jwt-token"

    @pytest.fixture
    def sample_strategy_data(self):
        """示例策略数据"""
        return {
            "name": "MACD趋势策略",
            "description": "基于MACD指标的趋势跟踪策略",
            "strategy_type": "trend_following",
            "code": """
def initialize(context):
    context.symbol = '000001'
    context.fast_period = 12
    context.slow_period = 26

def handle_data(context, data):
    # MACD策略逻辑
    current_price = data.current(context.symbol, 'price')
    if current_price > context.sma_20:
        order_target_percent(context.symbol, 0.1)
    else:
        order_target_percent(context.symbol, 0)
            """,
            "parameters": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            "symbols": ["000001", "000002"],
            "timeframe": "1d",
            "risk_level": "medium",
            "max_position_size": 0.1
        }

    @pytest.fixture
    def mock_strategy_response(self):
        """模拟策略响应数据"""
        return {
            "id": "test-strategy-id",
            "name": "MACD趋势策略",
            "description": "基于MACD指标的趋势跟踪策略",
            "strategy_type": "trend_following",
            "status": "draft",
            "user_id": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    async def test_create_strategy_success(self, auth_headers, sample_strategy_data, mock_strategy_response):
        """测试成功创建策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_strategy_by_name.return_value = None  # 策略名称不存在
            mock_service.create_strategy.return_value = Mock(**mock_strategy_response)
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/",
                        json=sample_strategy_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "MACD趋势策略"
                assert data["strategy_type"] == "trend_following"
                mock_service.create_strategy.assert_called_once()

    async def test_create_strategy_duplicate_name(self, auth_headers, sample_strategy_data):
        """测试创建重复名称的策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_strategy_by_name.return_value = Mock()  # 策略名称已存在
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/",
                        json=sample_strategy_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 400
                assert "策略名称已存在" in response.json()["detail"]

    async def test_get_strategy_success(self, auth_headers, mock_strategy_response):
        """测试成功获取策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock(**mock_strategy_response)
            mock_strategy.user_id = 1
            mock_service.get_strategy_by_id.return_value = mock_strategy
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategy/test-strategy-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == "test-strategy-id"
                assert data["name"] == "MACD趋势策略"

    async def test_get_strategy_not_found(self, auth_headers):
        """测试获取不存在的策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_strategy_by_id.return_value = None
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategy/nonexistent-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 404
                assert "策略不存在" in response.json()["detail"]

    async def test_start_strategy_success(self, auth_headers):
        """测试成功启动策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_strategy.status = StrategyStatus.STOPPED
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.start_strategy.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/test-strategy-id/start",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert "策略启动成功" in data["message"]
                mock_service.start_strategy.assert_called_once_with("test-strategy-id")

    async def test_start_strategy_already_running(self, auth_headers):
        """测试启动已运行的策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_strategy.status = StrategyStatus.RUNNING
            mock_service.get_strategy_by_id.return_value = mock_strategy
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/test-strategy-id/start",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 400
                assert "策略已在运行中" in response.json()["detail"]

    async def test_stop_strategy_success(self, auth_headers):
        """测试成功停止策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_strategy.status = StrategyStatus.RUNNING
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.stop_strategy.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/test-strategy-id/stop",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert "策略停止成功" in data["message"]
                mock_service.stop_strategy.assert_called_once_with("test-strategy-id")

    async def test_update_strategy_success(self, auth_headers):
        """测试成功更新策略"""
        update_data = {
            "name": "更新的MACD策略",
            "description": "更新的策略描述",
            "parameters": {
                "fast_period": 10,
                "slow_period": 20
            }
        }
        
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_strategy.name = "更新的MACD策略"
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.update_strategy.return_value = mock_strategy
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.put(
                        "/api/v1/strategy/test-strategy-id",
                        json=update_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                mock_service.update_strategy.assert_called_once()

    async def test_delete_strategy_success(self, auth_headers):
        """测试成功删除策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.delete_strategy.return_value = True
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.delete(
                        "/api/v1/strategy/test-strategy-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert "策略删除成功" in data["message"]
                mock_service.delete_strategy.assert_called_once_with("test-strategy-id")

    async def test_get_strategy_performance(self, auth_headers):
        """测试获取策略绩效"""
        mock_performance = {
            "total_return": 0.15,
            "annual_return": 0.12,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.5,
            "win_rate": 0.65,
            "total_trades": 150
        }
        
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.get_strategy_performance.return_value = mock_performance
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategy/test-strategy-id/performance",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["total_return"] == 0.15
                assert data["sharpe_ratio"] == 1.5
                assert data["win_rate"] == 0.65

    async def test_get_strategy_signals(self, auth_headers):
        """测试获取策略信号"""
        mock_signals = [
            {
                "strategy_id": "test-strategy-id",
                "symbol": "000001",
                "signal_type": "BUY",
                "strength": 0.8,
                "price": 105.50,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.get_strategy_signals.return_value = mock_signals
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategy/test-strategy-id/signals",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["signal_type"] == "BUY"
                assert data[0]["symbol"] == "000001"

    async def test_optimize_strategy_success(self, auth_headers):
        """测试策略参数优化"""
        optimization_data = {
            "parameters": {
                "fast_period": {"min": 5, "max": 20, "step": 1},
                "slow_period": {"min": 20, "max": 50, "step": 1}
            },
            "objective": "sharpe_ratio",
            "method": "grid_search",
            "start_date": "2023-01-01",
            "end_date": "2024-01-01"
        }
        
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 1
            mock_service.get_strategy_by_id.return_value = mock_strategy
            mock_service.start_optimization.return_value = "optimization-task-id"
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/strategy/test-strategy-id/optimize",
                        json=optimization_data,
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 200
                data = response.json()
                assert data["task_id"] == "optimization-task-id"
                assert "参数优化任务已启动" in data["message"]

    async def test_unauthorized_access(self):
        """测试未授权访问"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/strategy/test-strategy-id")
        
        # 验证响应
        assert response.status_code == 401

    async def test_access_other_user_strategy(self, auth_headers):
        """测试访问其他用户的策略"""
        with patch('app.api.v1.strategy.StrategyService') as mock_service_class:
            # Mock服务实例和方法
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_strategy = Mock()
            mock_strategy.user_id = 2  # 不同的用户ID
            mock_service.get_strategy_by_id.return_value = mock_strategy
            
            # Mock用户认证
            with patch('app.api.v1.strategy.get_current_active_user') as mock_auth:
                mock_user = Mock()
                mock_user.id = 1  # 当前用户ID
                mock_auth.return_value = mock_user
                
                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.get(
                        "/api/v1/strategy/test-strategy-id",
                        headers=auth_headers
                    )
                
                # 验证响应
                assert response.status_code == 404
                assert "策略不存在" in response.json()["detail"]
