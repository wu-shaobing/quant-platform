"""
风险管理服务单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.risk_service import RiskService
from app.schemas.trading import (
    OrderRequest, RiskCheckResult, RiskLimitData,
    OrderType, OrderSide
)
from app.models.trading import Trade, Position, Account
from app.models.user import User, UserStatus
from app.core.exceptions import DataNotFoundError


@pytest.mark.unit
@pytest.mark.risk
@pytest.mark.asyncio
class TestRiskService:
    """风险管理服务测试类"""

    @pytest.fixture
    def risk_service(self, mock_db_session):
        """创建风险服务实例"""
        return RiskService(mock_db_session)

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_order_request(self):
        """示例订单请求"""
        return OrderRequest(
            symbol="000001",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=100,
            price=Decimal("105.50"),
            time_in_force="GTC"
        )

    @pytest.fixture
    def sample_user(self):
        """示例用户"""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.status = UserStatus.ACTIVE
        user.is_active = True
        return user

    @pytest.fixture
    def sample_account(self):
        """示例账户"""
        account = Mock(spec=Account)
        account.id = 1
        account.user_id = 1
        account.account_type = "stock"
        account.total_assets = Decimal("100000.00")
        account.available_cash = Decimal("50000.00")
        account.frozen_cash = Decimal("5000.00")
        account.market_value = Decimal("45000.00")
        account.total_pnl = Decimal("0.00")
        account.daily_pnl = Decimal("0.00")
        account.margin_ratio = Decimal("0.5")
        account.risk_level = "medium"
        account.is_active = True
        account.is_tradable = True
        return account

    async def test_check_order_risk_success(self, risk_service, sample_order_request, sample_user, sample_account):
        """测试订单风险检查成功"""
        # Mock各项检查都通过
        risk_service._check_user_status = AsyncMock(return_value=RiskCheckResult(True, "用户状态正常"))
        risk_service._check_fund_sufficiency = AsyncMock(return_value=RiskCheckResult(True, "资金充足"))
        risk_service._check_position_limit = AsyncMock(return_value=RiskCheckResult(True, "持仓限制检查通过"))
        risk_service._check_order_size_limit = AsyncMock(return_value=RiskCheckResult(True, "委托大小检查通过"))

        # 执行测试
        result = await risk_service.check_order_risk(1, sample_order_request)

        # 验证结果
        assert result.passed is True
        assert "风险检查通过" in result.message

    async def test_check_order_risk_user_status_fail(self, risk_service, sample_order_request):
        """测试用户状态检查失败"""
        # Mock用户状态检查失败
        risk_service._check_user_status = AsyncMock(
            return_value=RiskCheckResult(False, "用户状态异常")
        )

        # 执行测试
        result = await risk_service.check_order_risk(1, sample_order_request)

        # 验证结果
        assert result.passed is False
        assert result.message == "用户状态异常"

    async def test_check_user_status_active(self, risk_service, sample_user):
        """测试活跃用户状态检查"""
        # Mock数据库查询
        risk_service.db.get.return_value = sample_user

        # 执行测试
        result = await risk_service._check_user_status(1)

        # 验证结果
        assert result.passed is True
        assert "用户状态正常" in result.message

    async def test_check_user_status_inactive(self, risk_service):
        """测试非活跃用户状态检查"""
        # Mock非活跃用户
        inactive_user = Mock(spec=User)
        inactive_user.status = UserStatus.INACTIVE
        inactive_user.is_active = False
        risk_service.db.get.return_value = inactive_user

        # 执行测试
        result = await risk_service._check_user_status(1)

        # 验证结果
        assert result.passed is False
        assert "用户状态异常" in result.message

    async def test_check_user_status_not_found(self, risk_service):
        """测试用户不存在"""
        # Mock用户不存在
        risk_service.db.get.return_value = None

        # 执行测试
        result = await risk_service._check_user_status(1)

        # 验证结果
        assert result.passed is False
        assert "用户不存在" in result.message

    async def test_check_fund_sufficiency_success(self, risk_service, sample_order_request, sample_account):
        """测试资金充足性检查成功"""
        # Mock账户查询
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_account
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service._check_fund_sufficiency(1, sample_order_request)

        # 验证结果
        assert result.passed is True
        assert "资金充足" in result.message

    async def test_check_fund_sufficiency_insufficient(self, risk_service, sample_order_request):
        """测试资金不足"""
        # Mock资金不足的账户
        poor_account = Mock(spec=Account)
        poor_account.available_cash = Decimal("1000.00")  # 资金不足
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = poor_account
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service._check_fund_sufficiency(1, sample_order_request)

        # 验证结果
        assert result.passed is False
        assert "资金不足" in result.message

    async def test_check_fund_sufficiency_no_account(self, risk_service, sample_order_request):
        """测试账户不存在"""
        # Mock账户不存在
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service._check_fund_sufficiency(1, sample_order_request)

        # 验证结果
        assert result.passed is False
        assert "账户不存在" in result.message

    async def test_check_position_limit_success(self, risk_service, sample_order_request):
        """测试持仓限制检查成功"""
        # Mock持仓查询 - 无持仓
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        risk_service.db.execute.return_value = mock_result

        # Mock限制获取
        risk_service._get_max_position_limit = AsyncMock(return_value=Decimal("20000.00"))

        # 执行测试
        result = await risk_service._check_position_limit(1, sample_order_request)

        # 验证结果
        assert result.passed is True
        assert "持仓限制检查通过" in result.message

    async def test_check_position_limit_exceeded(self, risk_service, sample_order_request):
        """测试持仓限制超限"""
        # Mock现有持仓
        existing_position = Mock(spec=Position)
        existing_position.quantity = 1000  # 已有大量持仓
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_position
        risk_service.db.execute.return_value = mock_result

        # Mock较小的限制
        risk_service._get_max_position_limit = AsyncMock(return_value=Decimal("500.00"))

        # 执行测试
        result = await risk_service._check_position_limit(1, sample_order_request)

        # 验证结果
        assert result.passed is False
        assert "持仓超限" in result.message

    async def test_check_order_size_limit_success(self, risk_service, sample_order_request):
        """测试委托大小限制检查成功"""
        # Mock限制获取
        risk_service._get_max_order_size_limit = AsyncMock(return_value=Decimal("50000.00"))

        # 执行测试
        result = await risk_service._check_order_size_limit(1, sample_order_request)

        # 验证结果
        assert result.passed is True
        assert "委托大小检查通过" in result.message

    async def test_check_order_size_limit_exceeded(self, risk_service, sample_order_request):
        """测试委托大小超限"""
        # Mock较小的限制
        risk_service._get_max_order_size_limit = AsyncMock(return_value=Decimal("5000.00"))

        # 执行测试
        result = await risk_service._check_order_size_limit(1, sample_order_request)

        # 验证结果
        assert result.passed is False
        assert "委托金额超限" in result.message

    async def test_check_symbol_restriction_allowed(self, risk_service):
        """测试标的限制检查 - 允许交易"""
        # Mock允许的标的列表
        risk_service._get_allowed_symbols = AsyncMock(return_value=["000001", "000002"])
        risk_service._get_forbidden_symbols = AsyncMock(return_value=["000003"])

        # 执行测试
        result = await risk_service._check_symbol_restriction(1, "000001")

        # 验证结果
        assert result.passed is True
        assert "标的检查通过" in result.message

    async def test_check_symbol_restriction_forbidden(self, risk_service):
        """测试标的限制检查 - 禁止交易"""
        # Mock禁止的标的列表
        risk_service._get_allowed_symbols = AsyncMock(return_value=[])
        risk_service._get_forbidden_symbols = AsyncMock(return_value=["000001"])

        # 执行测试
        result = await risk_service._check_symbol_restriction(1, "000001")

        # 验证结果
        assert result.passed is False
        assert "禁止交易该标的" in result.message

    async def test_check_daily_loss_limit_success(self, risk_service):
        """测试日亏损限制检查成功"""
        # Mock今日盈亏查询 - 盈利
        mock_result = Mock()
        mock_result.scalar.return_value = Decimal("1000.00")  # 盈利
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service.check_daily_loss_limit(1)

        # 验证结果
        assert result.passed is True
        assert "日亏损检查通过" in result.message

    async def test_check_daily_loss_limit_exceeded(self, risk_service):
        """测试日亏损限制超限"""
        # Mock今日盈亏查询 - 大额亏损
        mock_result = Mock()
        mock_result.scalar.return_value = Decimal("-60000.00")  # 大额亏损
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service.check_daily_loss_limit(1)

        # 验证结果
        assert result.passed is False
        assert "日亏损超限" in result.message

    async def test_check_total_loss_limit_success(self, risk_service):
        """测试总亏损限制检查成功"""
        # Mock总盈亏查询 - 盈利
        mock_result = Mock()
        mock_result.scalar.return_value = Decimal("5000.00")  # 盈利
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service.check_total_loss_limit(1)

        # 验证结果
        assert result.passed is True
        assert "总亏损检查通过" in result.message

    async def test_check_total_loss_limit_exceeded(self, risk_service):
        """测试总亏损限制超限"""
        # Mock总盈亏查询 - 大额亏损
        mock_result = Mock()
        mock_result.scalar.return_value = Decimal("-120000.00")  # 大额亏损
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        result = await risk_service.check_total_loss_limit(1)

        # 验证结果
        assert result.passed is False
        assert "总亏损超限" in result.message

    async def test_get_risk_limits(self, risk_service):
        """测试获取风控限制"""
        # Mock各项限制获取
        risk_service._get_max_position_limit = AsyncMock(return_value=Decimal("20000.00"))
        risk_service._get_max_order_size_limit = AsyncMock(return_value=Decimal("10000.00"))
        risk_service._get_forbidden_symbols = AsyncMock(return_value=["000003"])

        # 执行测试
        result = await risk_service.get_risk_limits(1)

        # 验证结果
        assert isinstance(result, RiskLimitData)
        assert result.max_position == Decimal("20000.00")
        assert result.max_order_size == Decimal("10000.00")
        assert result.max_daily_loss == 50000.0
        assert result.max_total_loss == 100000.0
        assert "000003" in result.forbidden_symbols

    async def test_update_risk_limits(self, risk_service):
        """测试更新风控限制"""
        # 准备更新数据
        new_limits = RiskLimitData(
            max_position=Decimal("30000.00"),
            max_order_size=Decimal("15000.00"),
            max_daily_loss=60000.0,
            max_total_loss=120000.0,
            allowed_symbols=["000001", "000002"],
            forbidden_symbols=["000003", "000004"]
        )

        # 执行测试
        result = await risk_service.update_risk_limits(1, new_limits)

        # 验证结果
        assert isinstance(result, RiskLimitData)
        assert result.max_position == Decimal("30000.00")
        assert result.max_order_size == Decimal("15000.00")
        assert result.max_daily_loss == 60000.0

    async def test_calculate_order_value(self, risk_service, sample_order_request):
        """测试计算订单价值"""
        # 执行测试
        order_value = risk_service._calculate_order_value(sample_order_request)

        # 验证结果
        expected_value = sample_order_request.quantity * sample_order_request.price
        assert order_value == expected_value

    async def test_get_user_positions(self, risk_service):
        """测试获取用户持仓"""
        # Mock持仓查询
        mock_positions = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_positions
        risk_service.db.execute.return_value = mock_result

        # 执行测试
        positions = await risk_service.get_user_positions(1)

        # 验证结果
        assert positions == mock_positions
        risk_service.db.execute.assert_called_once()

    async def test_calculate_portfolio_risk(self, risk_service):
        """测试计算投资组合风险"""
        # Mock持仓和账户数据
        mock_positions = [
            Mock(symbol="000001", quantity=100, market_value=Decimal("10000")),
            Mock(symbol="000002", quantity=200, market_value=Decimal("20000"))
        ]
        mock_account = Mock(total_assets=Decimal("100000"))

        risk_service.get_user_positions = AsyncMock(return_value=mock_positions)
        risk_service.db.get.return_value = mock_account

        # 执行测试
        risk_metrics = await risk_service.calculate_portfolio_risk(1)

        # 验证结果
        assert isinstance(risk_metrics, dict)
        assert "total_value" in risk_metrics
        assert "concentration" in risk_metrics
        assert "var" in risk_metrics

    async def test_risk_alert_creation(self, risk_service):
        """测试风险预警创建"""
        # 准备预警数据
        alert_data = {
            "user_id": 1,
            "alert_type": "position_limit",
            "severity": "high",
            "message": "持仓超限预警",
            "details": {"symbol": "000001", "current": 15000, "limit": 10000}
        }

        # Mock数据库操作
        risk_service.db.add = Mock()
        risk_service.db.commit = AsyncMock()

        # 执行测试
        with patch('app.services.risk_service.RiskAlert') as mock_alert_class:
            mock_alert_instance = Mock()
            mock_alert_class.return_value = mock_alert_instance
            
            result = await risk_service.create_risk_alert(alert_data)

            # 验证结果
            assert result is not None
            risk_service.db.add.assert_called_once()
            risk_service.db.commit.assert_called_once()

    async def test_risk_monitoring_workflow(self, risk_service):
        """测试风险监控工作流"""
        # Mock各项检查
        risk_service.check_daily_loss_limit = AsyncMock(return_value=RiskCheckResult(True, "正常"))
        risk_service.check_total_loss_limit = AsyncMock(return_value=RiskCheckResult(True, "正常"))
        risk_service.calculate_portfolio_risk = AsyncMock(return_value={"var": 0.03, "concentration": 0.2})

        # 执行测试
        monitoring_result = await risk_service.run_risk_monitoring(1)

        # 验证结果
        assert isinstance(monitoring_result, dict)
        assert "status" in monitoring_result
        assert "checks" in monitoring_result
        assert "risk_metrics" in monitoring_result
