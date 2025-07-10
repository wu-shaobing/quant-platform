"""
策略服务单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.strategy_service import StrategyService
from app.models.strategy import Strategy, StrategyType, StrategyStatus, RiskLevel
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyOptimizationRequest,
    ValidationResult
)
from app.core.exceptions import DataNotFoundError


@pytest.mark.unit
@pytest.mark.strategy
@pytest.mark.asyncio
class TestStrategyService:
    """策略服务测试类"""

    @pytest.fixture
    def strategy_service(self, mock_db_session):
        """创建策略服务实例"""
        return StrategyService(mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_strategy_create(self):
        """示例策略创建数据"""
        return StrategyCreate(
            name="MACD策略",
            description="基于MACD指标的趋势跟踪策略",
            strategy_type=StrategyType.TREND_FOLLOWING,
            code="""
def initialize(context):
    context.symbol = '000001'
    
def handle_data(context, data):
    # MACD策略逻辑
    pass
            """,
            parameters={
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            },
            symbols=["000001", "000002"],
            timeframe="1d",
            risk_level=RiskLevel.MEDIUM,
            max_position_size=Decimal("0.1")
        )

    @pytest.fixture
    def sample_strategy_model(self):
        """示例策略模型"""
        strategy = Mock(spec=Strategy)
        strategy.id = "test-strategy-id"
        strategy.user_id = 1
        strategy.name = "MACD策略"
        strategy.description = "基于MACD指标的趋势跟踪策略"
        strategy.strategy_type = StrategyType.TREND_FOLLOWING
        strategy.status = StrategyStatus.DRAFT
        strategy.code = "def initialize(context): pass"
        strategy.parameters = {"fast_period": 12, "slow_period": 26}
        strategy.symbols = ["000001", "000002"]
        strategy.risk_level = RiskLevel.MEDIUM
        strategy.created_at = datetime.now()
        strategy.updated_at = datetime.now()
        return strategy

    async def test_create_strategy_success(self, strategy_service, sample_strategy_create):
        """测试成功创建策略"""
        # Mock数据库操作
        strategy_service.db.add = Mock()
        strategy_service.db.commit = AsyncMock()
        strategy_service.db.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.strategy_service.Strategy') as mock_strategy_class:
            mock_strategy_instance = Mock()
            mock_strategy_instance.id = "new-strategy-id"
            mock_strategy_class.return_value = mock_strategy_instance
            
            result = await strategy_service.create_strategy(1, sample_strategy_create)

            # 验证结果
            assert result is not None
            assert result.id == "new-strategy-id"
            strategy_service.db.add.assert_called_once()
            strategy_service.db.commit.assert_called_once()

    async def test_get_strategy_by_id_success(self, strategy_service, sample_strategy_model):
        """测试通过ID获取策略成功"""
        # Mock数据库查询
        strategy_service.db.get.return_value = sample_strategy_model

        # 执行测试
        result = await strategy_service.get_strategy_by_id("test-strategy-id")

        # 验证结果
        assert result == sample_strategy_model
        strategy_service.db.get.assert_called_once_with(Strategy, "test-strategy-id")

    async def test_get_strategy_by_id_not_found(self, strategy_service):
        """测试通过ID获取策略失败"""
        # Mock策略不存在
        strategy_service.db.get.return_value = None

        # 执行测试
        result = await strategy_service.get_strategy_by_id("nonexistent-id")

        # 验证结果
        assert result is None

    async def test_start_strategy_success(self, strategy_service, sample_strategy_model):
        """测试启动策略成功"""
        # 设置策略状态为已停止
        sample_strategy_model.status = StrategyStatus.STOPPED
        strategy_service.db.get.return_value = sample_strategy_model
        strategy_service.db.commit = AsyncMock()

        # 执行测试
        result = await strategy_service.start_strategy("test-strategy-id")

        # 验证结果
        assert result is True
        assert sample_strategy_model.status == StrategyStatus.ACTIVE
        assert sample_strategy_model.last_run is not None
        strategy_service.db.commit.assert_called_once()

    async def test_start_strategy_not_found(self, strategy_service):
        """测试启动不存在的策略"""
        # Mock策略不存在
        strategy_service.db.get.return_value = None

        # 执行测试并验证异常
        with pytest.raises(DataNotFoundError, match="策略不存在"):
            await strategy_service.start_strategy("nonexistent-id")

    async def test_stop_strategy_success(self, strategy_service, sample_strategy_model):
        """测试停止策略成功"""
        # 设置策略状态为运行中
        sample_strategy_model.status = StrategyStatus.ACTIVE
        strategy_service.db.get.return_value = sample_strategy_model
        strategy_service.db.commit = AsyncMock()

        # 执行测试
        result = await strategy_service.stop_strategy("test-strategy-id")

        # 验证结果
        assert result is True
        assert sample_strategy_model.status == StrategyStatus.STOPPED
        strategy_service.db.commit.assert_called_once()

    async def test_update_strategy_success(self, strategy_service, sample_strategy_model):
        """测试更新策略成功"""
        # 准备更新数据
        strategy_update = StrategyUpdate(
            name="更新的MACD策略",
            description="更新的策略描述",
            parameters={"fast_period": 10, "slow_period": 20}
        )
        
        strategy_service.db.get.return_value = sample_strategy_model
        strategy_service.db.commit = AsyncMock()

        # 执行测试
        result = await strategy_service.update_strategy("test-strategy-id", strategy_update)

        # 验证结果
        assert result == sample_strategy_model
        assert sample_strategy_model.name == "更新的MACD策略"
        assert sample_strategy_model.description == "更新的策略描述"
        strategy_service.db.commit.assert_called_once()

    async def test_delete_strategy_success(self, strategy_service, sample_strategy_model):
        """测试删除策略成功"""
        strategy_service.db.get.return_value = sample_strategy_model
        strategy_service.db.delete = Mock()
        strategy_service.db.commit = AsyncMock()

        # 执行测试
        result = await strategy_service.delete_strategy("test-strategy-id")

        # 验证结果
        assert result is True
        strategy_service.db.delete.assert_called_once_with(sample_strategy_model)
        strategy_service.db.commit.assert_called_once()

    async def test_validate_strategy_code_success(self, strategy_service):
        """测试策略代码验证成功"""
        valid_code = """
def initialize(context):
    context.symbol = '000001'

def handle_data(context, data):
    current_price = data.current(context.symbol, 'price')
    if current_price > 100:
        order_target_percent(context.symbol, 0.1)
"""

        # 执行测试
        result = await strategy_service.validate_strategy_code(valid_code)

        # 验证结果
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.error_message is None

    async def test_validate_strategy_code_syntax_error(self, strategy_service):
        """测试策略代码语法错误"""
        invalid_code = """
def initialize(context):
    context.symbol = '000001'
    # 语法错误：缺少冒号
    if True
        pass
"""

        # 执行测试
        result = await strategy_service.validate_strategy_code(invalid_code)

        # 验证结果
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert "语法错误" in result.error_message

    async def test_get_strategy_performance(self, strategy_service):
        """测试获取策略绩效"""
        # 执行测试
        result = await strategy_service.get_strategy_performance(
            "test-strategy-id",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )

        # 验证结果
        assert isinstance(result, dict)
        assert "total_return" in result
        assert "annual_return" in result
        assert "max_drawdown" in result
        assert "sharpe_ratio" in result
        assert "win_rate" in result
        assert "total_trades" in result

    async def test_get_strategy_signals(self, strategy_service):
        """测试获取策略信号"""
        # 执行测试
        result = await strategy_service.get_strategy_signals(
            "test-strategy-id",
            signal_type="BUY",
            start_time=datetime.now() - timedelta(hours=24),
            end_time=datetime.now(),
            limit=50
        )

        # 验证结果
        assert isinstance(result, list)

    async def test_get_strategy_logs(self, strategy_service):
        """测试获取策略日志"""
        # 执行测试
        result = await strategy_service.get_strategy_logs(
            "test-strategy-id",
            level="INFO",
            start_time=datetime.now() - timedelta(hours=24),
            end_time=datetime.now(),
            limit=100
        )

        # 验证结果
        assert isinstance(result, list)

    async def test_start_optimization(self, strategy_service):
        """测试启动策略参数优化"""
        # 准备优化请求
        optimization_request = StrategyOptimizationRequest(
            parameters={
                "fast_period": {"min": 5, "max": 20, "step": 1},
                "slow_period": {"min": 20, "max": 50, "step": 1}
            },
            objective="sharpe_ratio",
            method="grid_search",
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now()
        )

        # 执行测试
        with patch('uuid.uuid4', return_value="mock-task-id"):
            result = await strategy_service.start_optimization("test-strategy-id", optimization_request)

        # 验证结果
        assert isinstance(result, str)
        assert result == "mock-task-id"

    async def test_get_user_strategies(self, strategy_service):
        """测试获取用户策略列表"""
        # Mock数据库查询结果
        mock_strategies = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_strategies
        strategy_service.db.execute.return_value = mock_result

        # 执行测试
        result = await strategy_service.get_user_strategies(1)

        # 验证结果
        assert result == mock_strategies
        strategy_service.db.execute.assert_called_once()

    async def test_get_strategy_by_name(self, strategy_service, sample_strategy_model):
        """测试通过名称获取策略"""
        # Mock数据库查询
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_strategy_model
        strategy_service.db.execute.return_value = mock_result

        # 执行测试
        result = await strategy_service.get_strategy_by_name(1, "MACD策略")

        # 验证结果
        assert result == sample_strategy_model
        strategy_service.db.execute.assert_called_once()

    async def test_clone_strategy_success(self, strategy_service, sample_strategy_model):
        """测试克隆策略成功"""
        strategy_service.db.get.return_value = sample_strategy_model
        strategy_service.db.add = Mock()
        strategy_service.db.commit = AsyncMock()
        strategy_service.db.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.strategy_service.Strategy') as mock_strategy_class:
            mock_cloned_strategy = Mock()
            mock_cloned_strategy.id = "cloned-strategy-id"
            mock_strategy_class.return_value = mock_cloned_strategy
            
            result = await strategy_service.clone_strategy("test-strategy-id", "克隆的MACD策略")

            # 验证结果
            assert result is not None
            assert result.id == "cloned-strategy-id"
            strategy_service.db.add.assert_called_once()
            strategy_service.db.commit.assert_called_once()

    async def test_get_strategy_templates(self, strategy_service):
        """测试获取策略模板"""
        # Mock数据库查询结果
        mock_templates = [Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_templates
        strategy_service.db.execute.return_value = mock_result

        # 执行测试
        result = await strategy_service.get_strategy_templates()

        # 验证结果
        assert result == mock_templates
        strategy_service.db.execute.assert_called_once()
