"""
回测服务单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.backtest_service import BacktestService
from app.models.backtest import BacktestTask, BacktestResult, BacktestStatus, BacktestType
from app.schemas.backtest import (
    BacktestCreate, BacktestUpdate, BacktestAnalysisRequest,
    BacktestOptimizationConfig, RebalanceFrequency, BenchmarkType
)
from app.core.exceptions import DataNotFoundError


@pytest.mark.unit
@pytest.mark.backtest
@pytest.mark.asyncio
class TestBacktestService:
    """回测服务测试类"""

    @pytest.fixture
    def backtest_service(self, mock_db_session):
        """创建回测服务实例"""
        return BacktestService(mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_backtest_create(self):
        """示例回测创建数据"""
        return BacktestCreate(
            name="MACD策略回测",
            description="基于MACD指标的趋势跟踪策略回测",
            strategy_id="test-strategy-id",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=Decimal("100000.00"),
            symbols=["000001", "000002", "000300"],
            benchmark="000300",
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.001"),
            rebalance_frequency=RebalanceFrequency.DAILY,
            max_position_size=Decimal("0.2"),
            parameters={
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        )

    @pytest.fixture
    def sample_backtest_model(self):
        """示例回测模型"""
        backtest = Mock(spec=BacktestTask)
        backtest.id = "test-backtest-id"
        backtest.user_id = 1
        backtest.strategy_id = "test-strategy-id"
        backtest.name = "MACD策略回测"
        backtest.description = "基于MACD指标的趋势跟踪策略回测"
        backtest.status = BacktestStatus.PENDING
        backtest.start_date = datetime(2023, 1, 1)
        backtest.end_date = datetime(2023, 12, 31)
        backtest.initial_capital = Decimal("100000.00")
        backtest.symbols = ["000001", "000002", "000300"]
        backtest.benchmark = "000300"
        backtest.commission_rate = Decimal("0.0003")
        backtest.slippage_rate = Decimal("0.001")
        backtest.created_at = datetime.now()
        backtest.updated_at = datetime.now()
        return backtest

    @pytest.fixture
    def sample_backtest_result(self):
        """示例回测结果"""
        return {
            "total_return": 0.15,
            "annual_return": 0.12,
            "max_drawdown": -0.08,
            "sharpe_ratio": 1.5,
            "win_rate": 0.65,
            "total_trades": 150,
            "profit_loss_ratio": 1.8,
            "volatility": 0.15,
            "beta": 0.9,
            "alpha": 0.03,
            "information_ratio": 0.8,
            "calmar_ratio": 1.2
        }

    async def test_create_backtest_success(self, backtest_service, sample_backtest_create):
        """测试成功创建回测"""
        # Mock数据库操作
        backtest_service.db.add = Mock()
        backtest_service.db.commit = AsyncMock()
        backtest_service.db.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.backtest_service.BacktestTask') as mock_backtest_class:
            mock_backtest_instance = Mock()
            mock_backtest_instance.id = "new-backtest-id"
            mock_backtest_class.return_value = mock_backtest_instance
            
            result = await backtest_service.create_backtest(1, sample_backtest_create)

            # 验证结果
            assert result is not None
            assert result.id == "new-backtest-id"
            backtest_service.db.add.assert_called_once()
            backtest_service.db.commit.assert_called_once()

    async def test_get_backtest_by_id_success(self, backtest_service, sample_backtest_model):
        """测试通过ID获取回测成功"""
        # Mock数据库查询
        backtest_service.db.get.return_value = sample_backtest_model

        # 执行测试
        result = await backtest_service.get_backtest_by_id("test-backtest-id")

        # 验证结果
        assert result == sample_backtest_model
        backtest_service.db.get.assert_called_once_with(BacktestTask, "test-backtest-id")

    async def test_get_backtest_by_id_not_found(self, backtest_service):
        """测试通过ID获取回测失败"""
        # Mock回测不存在
        backtest_service.db.get.return_value = None

        # 执行测试
        result = await backtest_service.get_backtest_by_id("nonexistent-id")

        # 验证结果
        assert result is None

    async def test_start_backtest_success(self, backtest_service, sample_backtest_model):
        """测试启动回测成功"""
        # 设置回测状态为待运行
        sample_backtest_model.status = BacktestStatus.PENDING
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        result = await backtest_service.start_backtest("test-backtest-id")

        # 验证结果
        assert result is True
        assert sample_backtest_model.status == BacktestStatus.RUNNING
        assert sample_backtest_model.started_at is not None
        backtest_service.db.commit.assert_called_once()

    async def test_start_backtest_not_found(self, backtest_service):
        """测试启动不存在的回测"""
        # Mock回测不存在
        backtest_service.db.get.return_value = None

        # 执行测试并验证异常
        with pytest.raises(DataNotFoundError, match="回测不存在"):
            await backtest_service.start_backtest("nonexistent-id")

    async def test_stop_backtest_success(self, backtest_service, sample_backtest_model):
        """测试停止回测成功"""
        # 设置回测状态为运行中
        sample_backtest_model.status = BacktestStatus.RUNNING
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        result = await backtest_service.stop_backtest("test-backtest-id")

        # 验证结果
        assert result is True
        assert sample_backtest_model.status == BacktestStatus.STOPPED
        backtest_service.db.commit.assert_called_once()

    async def test_update_backtest_success(self, backtest_service, sample_backtest_model):
        """测试更新回测成功"""
        # 准备更新数据
        backtest_update = BacktestUpdate(
            name="更新的MACD策略回测",
            description="更新的回测描述",
            parameters={"fast_period": 10, "slow_period": 20}
        )
        
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        result = await backtest_service.update_backtest("test-backtest-id", backtest_update)

        # 验证结果
        assert result == sample_backtest_model
        assert sample_backtest_model.name == "更新的MACD策略回测"
        assert sample_backtest_model.description == "更新的回测描述"
        backtest_service.db.commit.assert_called_once()

    async def test_delete_backtest_success(self, backtest_service, sample_backtest_model):
        """测试删除回测成功"""
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.delete = Mock()
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        result = await backtest_service.delete_backtest("test-backtest-id")

        # 验证结果
        assert result is True
        backtest_service.db.delete.assert_called_once_with(sample_backtest_model)
        backtest_service.db.commit.assert_called_once()

    async def test_complete_backtest_success(self, backtest_service, sample_backtest_model, sample_backtest_result):
        """测试完成回测成功"""
        # 设置回测状态为运行中
        sample_backtest_model.status = BacktestStatus.RUNNING
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.add = Mock()
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        with patch('app.services.backtest_service.BacktestResult') as mock_result_class:
            mock_result_instance = Mock()
            mock_result_class.return_value = mock_result_instance
            
            result = await backtest_service.complete_backtest("test-backtest-id", sample_backtest_result)

            # 验证结果
            assert result is True
            assert sample_backtest_model.status == BacktestStatus.COMPLETED
            assert sample_backtest_model.completed_at is not None
            backtest_service.db.add.assert_called_once()
            backtest_service.db.commit.assert_called_once()

    async def test_run_backtest_task_success(self, backtest_service, sample_backtest_model):
        """测试运行回测任务成功"""
        # Mock相关方法
        backtest_service.start_backtest = AsyncMock(return_value=True)
        backtest_service.complete_backtest = AsyncMock(return_value=True)

        # 执行测试
        with patch('asyncio.sleep', new_callable=AsyncMock):  # 跳过睡眠
            await backtest_service.run_backtest_task("test-backtest-id")

        # 验证方法调用
        backtest_service.start_backtest.assert_called_once_with("test-backtest-id")
        backtest_service.complete_backtest.assert_called_once()

    async def test_run_backtest_task_failure(self, backtest_service, sample_backtest_model):
        """测试运行回测任务失败"""
        # Mock方法抛出异常
        backtest_service.start_backtest = AsyncMock(side_effect=Exception("回测失败"))
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        await backtest_service.run_backtest_task("test-backtest-id")

        # 验证失败处理
        assert sample_backtest_model.status == BacktestStatus.FAILED
        assert sample_backtest_model.error_message == "回测失败"
        backtest_service.db.commit.assert_called()

    async def test_get_user_backtests(self, backtest_service):
        """测试获取用户回测列表"""
        # Mock数据库查询结果
        mock_backtests = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_backtests
        backtest_service.db.execute.return_value = mock_result

        # 执行测试
        result = await backtest_service.get_user_backtests(1)

        # 验证结果
        assert result == mock_backtests
        backtest_service.db.execute.assert_called_once()

    async def test_get_backtest_result(self, backtest_service):
        """测试获取回测结果"""
        # Mock回测结果
        mock_result = Mock(spec=BacktestResult)
        mock_result.total_return = Decimal("0.15")
        mock_result.sharpe_ratio = Decimal("1.5")
        mock_result.max_drawdown = Decimal("-0.08")
        
        mock_query_result = Mock()
        mock_query_result.scalar_one_or_none.return_value = mock_result
        backtest_service.db.execute.return_value = mock_query_result

        # 执行测试
        result = await backtest_service.get_backtest_result("test-backtest-id")

        # 验证结果
        assert result == mock_result
        backtest_service.db.execute.assert_called_once()

    async def test_analyze_backtest(self, backtest_service):
        """测试分析回测结果"""
        # 准备分析请求
        analysis_request = BacktestAnalysisRequest(
            analysis_type="performance",
            metrics=["sharpe_ratio", "max_drawdown", "win_rate"],
            chart_types=["equity_curve", "drawdown_curve"]
        )

        # 执行测试
        result = await backtest_service.analyze_backtest("test-backtest-id", analysis_request)

        # 验证结果
        assert isinstance(result, dict)
        assert "analysis_type" in result
        assert "metrics" in result
        assert "charts" in result
        assert "insights" in result
        assert result["analysis_type"] == "performance"

    async def test_start_optimization_task(self, backtest_service):
        """测试启动参数优化任务"""
        # 准备优化配置
        optimization_config = BacktestOptimizationConfig(
            parameters={
                "fast_period": {"min": 5, "max": 20, "step": 1},
                "slow_period": {"min": 20, "max": 50, "step": 1}
            },
            objective="sharpe_ratio",
            method="grid_search",
            max_iterations=100
        )

        # 执行测试
        with patch('uuid.uuid4', return_value="mock-task-id"):
            result = await backtest_service.start_optimization_task("test-backtest-id", optimization_config)

        # 验证结果
        assert isinstance(result, str)
        assert result == "mock-task-id"

    async def test_get_backtest_comparison(self, backtest_service):
        """测试获取回测比较"""
        # Mock比较结果
        mock_comparison = {
            "backtests": ["backtest-1", "backtest-2"],
            "metrics_comparison": {
                "total_return": [0.15, 0.12],
                "sharpe_ratio": [1.5, 1.2],
                "max_drawdown": [-0.08, -0.10]
            },
            "charts": {
                "equity_curves": [],
                "drawdown_curves": []
            }
        }

        # Mock数据库查询
        mock_results = [Mock(), Mock()]
        mock_query_result = Mock()
        mock_query_result.scalars.return_value.all.return_value = mock_results
        backtest_service.db.execute.return_value = mock_query_result

        # 执行测试
        result = await backtest_service.get_backtest_comparison(["backtest-1", "backtest-2"])

        # 验证结果
        assert isinstance(result, dict)
        backtest_service.db.execute.assert_called()

    async def test_validate_backtest_parameters(self, backtest_service, sample_backtest_create):
        """测试回测参数验证"""
        # 测试有效参数
        is_valid, error_message = await backtest_service.validate_backtest_parameters(sample_backtest_create)
        assert is_valid is True
        assert error_message is None

        # 测试无效日期范围
        invalid_backtest = sample_backtest_create.copy()
        invalid_backtest.start_date = datetime(2023, 12, 31)
        invalid_backtest.end_date = datetime(2023, 1, 1)
        
        is_valid, error_message = await backtest_service.validate_backtest_parameters(invalid_backtest)
        assert is_valid is False
        assert "开始日期必须早于结束日期" in error_message

        # 测试无效初始资金
        invalid_backtest = sample_backtest_create.copy()
        invalid_backtest.initial_capital = Decimal("0")
        
        is_valid, error_message = await backtest_service.validate_backtest_parameters(invalid_backtest)
        assert is_valid is False
        assert "初始资金必须大于0" in error_message

    async def test_calculate_performance_metrics(self, backtest_service):
        """测试计算绩效指标"""
        # 准备模拟交易数据
        trades_data = [
            {"date": "2023-01-01", "return": 0.01},
            {"date": "2023-01-02", "return": -0.005},
            {"date": "2023-01-03", "return": 0.02},
            {"date": "2023-01-04", "return": -0.01},
            {"date": "2023-01-05", "return": 0.015}
        ]

        # 执行测试
        metrics = await backtest_service.calculate_performance_metrics(trades_data)

        # 验证结果
        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
        assert "volatility" in metrics

    async def test_generate_backtest_report(self, backtest_service, sample_backtest_result):
        """测试生成回测报告"""
        # Mock回测结果
        mock_backtest = Mock()
        mock_backtest.name = "MACD策略回测"
        mock_backtest.start_date = datetime(2023, 1, 1)
        mock_backtest.end_date = datetime(2023, 12, 31)

        backtest_service.db.get.return_value = mock_backtest

        # 执行测试
        report = await backtest_service.generate_backtest_report("test-backtest-id")

        # 验证结果
        assert isinstance(report, dict)
        assert "backtest_info" in report
        assert "performance_summary" in report
        assert "risk_analysis" in report
        assert "trade_analysis" in report

    async def test_backtest_data_validation(self, backtest_service):
        """测试回测数据验证"""
        # 测试空标的列表
        invalid_data = {
            "symbols": [],
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 12, 31),
            "initial_capital": Decimal("100000")
        }

        is_valid, error = await backtest_service.validate_backtest_data(invalid_data)
        assert is_valid is False
        assert "标的列表不能为空" in error

    async def test_backtest_progress_tracking(self, backtest_service, sample_backtest_model):
        """测试回测进度跟踪"""
        # Mock进度更新
        backtest_service.db.get.return_value = sample_backtest_model
        backtest_service.db.commit = AsyncMock()

        # 执行测试
        await backtest_service.update_backtest_progress("test-backtest-id", 0.5, "处理中...")

        # 验证结果
        assert sample_backtest_model.progress == 0.5
        assert sample_backtest_model.status_message == "处理中..."
        backtest_service.db.commit.assert_called_once()
