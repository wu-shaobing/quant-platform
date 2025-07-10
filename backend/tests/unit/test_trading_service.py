"""
交易服务单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trading_service import TradingService
from app.models.trading import Order, Position, Portfolio
from app.schemas.trading import OrderCreate, OrderUpdate, OrderSide, OrderType, OrderStatus


@pytest.mark.unit
@pytest.mark.trading
@pytest.mark.asyncio
class TestTradingService:
    """交易服务测试类"""

    @pytest.fixture
    def trading_service(self):
        """创建交易服务实例"""
        return TradingService()

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_order_create(self):
        """示例订单创建数据"""
        return OrderCreate(
            symbol="000001",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=Decimal("10.50"),
            user_id="test-user-id"
        )

    @pytest.fixture
    def sample_order_model(self):
        """示例订单模型"""
        order = Mock(spec=Order)
        order.id = "test-order-id"
        order.symbol = "000001"
        order.side = OrderSide.BUY
        order.order_type = OrderType.LIMIT
        order.quantity = 100
        order.price = Decimal("10.50")
        order.status = OrderStatus.PENDING
        order.user_id = "test-user-id"
        order.created_at = datetime.now()
        return order

    @pytest.fixture
    def sample_position_model(self):
        """示例持仓模型"""
        position = Mock(spec=Position)
        position.id = "test-position-id"
        position.symbol = "000001"
        position.quantity = 100
        position.average_price = Decimal("10.50")
        position.market_value = Decimal("1050.00")
        position.unrealized_pnl = Decimal("0.00")
        position.user_id = "test-user-id"
        return position

    async def test_create_order_success(self, trading_service, mock_db_session, sample_order_create):
        """测试成功创建订单"""
        # 模拟数据库操作
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.trading_service.Order') as mock_order_class:
            mock_order_instance = Mock()
            mock_order_instance.id = "new-order-id"
            mock_order_instance.status = OrderStatus.PENDING
            mock_order_class.return_value = mock_order_instance
            
            result = await trading_service.create_order(mock_db_session, sample_order_create)

            # 验证结果
            assert result is not None
            assert result.id == "new-order-id"
            assert result.status == OrderStatus.PENDING
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    async def test_create_order_invalid_quantity(self, trading_service, mock_db_session, sample_order_create):
        """测试创建无效数量的订单"""
        # 设置无效数量
        sample_order_create.quantity = 0

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="订单数量必须大于0"):
            await trading_service.create_order(mock_db_session, sample_order_create)

    async def test_create_order_invalid_price(self, trading_service, mock_db_session, sample_order_create):
        """测试创建无效价格的订单"""
        # 设置无效价格
        sample_order_create.price = Decimal("0")

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="限价订单价格必须大于0"):
            await trading_service.create_order(mock_db_session, sample_order_create)

    async def test_get_order_by_id_success(self, trading_service, mock_db_session, sample_order_model):
        """测试通过ID获取订单成功"""
        # 模拟数据库查询
        mock_db_session.get.return_value = sample_order_model

        # 执行测试
        result = await trading_service.get_order_by_id(mock_db_session, "test-order-id")

        # 验证结果
        assert result == sample_order_model
        mock_db_session.get.assert_called_once_with(Order, "test-order-id")

    async def test_get_order_by_id_not_found(self, trading_service, mock_db_session):
        """测试通过ID获取订单失败"""
        # 模拟订单不存在
        mock_db_session.get.return_value = None

        # 执行测试
        result = await trading_service.get_order_by_id(mock_db_session, "nonexistent-id")

        # 验证结果
        assert result is None

    async def test_update_order_status_success(self, trading_service, mock_db_session, sample_order_model):
        """测试更新订单状态成功"""
        # 模拟数据库操作
        mock_db_session.get.return_value = sample_order_model
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # 执行测试
        result = await trading_service.update_order_status(
            mock_db_session, "test-order-id", OrderStatus.FILLED
        )

        # 验证结果
        assert result == sample_order_model
        assert sample_order_model.status == OrderStatus.FILLED
        mock_db_session.commit.assert_called_once()

    async def test_update_order_status_not_found(self, trading_service, mock_db_session):
        """测试更新不存在订单的状态"""
        # 模拟订单不存在
        mock_db_session.get.return_value = None

        # 执行测试
        result = await trading_service.update_order_status(
            mock_db_session, "nonexistent-id", OrderStatus.FILLED
        )

        # 验证结果
        assert result is None

    async def test_cancel_order_success(self, trading_service, mock_db_session, sample_order_model):
        """测试取消订单成功"""
        # 设置订单状态为待处理
        sample_order_model.status = OrderStatus.PENDING
        mock_db_session.get.return_value = sample_order_model
        mock_db_session.commit = AsyncMock()

        # 执行测试
        result = await trading_service.cancel_order(mock_db_session, "test-order-id")

        # 验证结果
        assert result is True
        assert sample_order_model.status == OrderStatus.CANCELLED
        mock_db_session.commit.assert_called_once()

    async def test_cancel_order_already_filled(self, trading_service, mock_db_session, sample_order_model):
        """测试取消已成交订单"""
        # 设置订单状态为已成交
        sample_order_model.status = OrderStatus.FILLED
        mock_db_session.get.return_value = sample_order_model

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="无法取消已成交或已取消的订单"):
            await trading_service.cancel_order(mock_db_session, "test-order-id")

    async def test_get_user_orders_success(self, trading_service, mock_db_session):
        """测试获取用户订单成功"""
        # 模拟数据库查询结果
        mock_orders = [Mock(), Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_orders
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await trading_service.get_user_orders(mock_db_session, "test-user-id")

        # 验证结果
        assert result == mock_orders
        mock_db_session.execute.assert_called_once()

    async def test_get_user_positions_success(self, trading_service, mock_db_session):
        """测试获取用户持仓成功"""
        # 模拟数据库查询结果
        mock_positions = [Mock(), Mock()]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_positions
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await trading_service.get_user_positions(mock_db_session, "test-user-id")

        # 验证结果
        assert result == mock_positions
        mock_db_session.execute.assert_called_once()

    async def test_calculate_position_value(self, trading_service, sample_position_model):
        """测试计算持仓价值"""
        # 设置当前价格
        current_price = Decimal("11.00")

        # 执行测试
        with patch('app.services.trading_service.TradingService.get_current_price', return_value=current_price):
            market_value, unrealized_pnl = await trading_service.calculate_position_value(
                sample_position_model, current_price
            )

        # 验证结果
        expected_market_value = Decimal("1100.00")  # 100 * 11.00
        expected_unrealized_pnl = Decimal("50.00")  # (11.00 - 10.50) * 100
        
        assert market_value == expected_market_value
        assert unrealized_pnl == expected_unrealized_pnl

    async def test_update_position_success(self, trading_service, mock_db_session, sample_position_model):
        """测试更新持仓成功"""
        # 模拟数据库操作
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_position_model
        mock_db_session.commit = AsyncMock()

        # 执行测试
        result = await trading_service.update_position(
            mock_db_session, "test-user-id", "000001", 50, Decimal("11.00")
        )

        # 验证结果
        assert result == sample_position_model
        mock_db_session.commit.assert_called_once()

    async def test_create_new_position(self, trading_service, mock_db_session):
        """测试创建新持仓"""
        # 模拟没有现有持仓
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.trading_service.Position') as mock_position_class:
            mock_position_instance = Mock()
            mock_position_instance.id = "new-position-id"
            mock_position_class.return_value = mock_position_instance
            
            result = await trading_service.update_position(
                mock_db_session, "test-user-id", "000001", 100, Decimal("10.50")
            )

            # 验证结果
            assert result is not None
            assert result.id == "new-position-id"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    async def test_get_portfolio_summary(self, trading_service, mock_db_session):
        """测试获取投资组合摘要"""
        # 模拟持仓数据
        mock_positions = [
            Mock(symbol="000001", quantity=100, market_value=Decimal("1100.00"), unrealized_pnl=Decimal("50.00")),
            Mock(symbol="000002", quantity=200, market_value=Decimal("2200.00"), unrealized_pnl=Decimal("-100.00"))
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_positions
        mock_db_session.execute.return_value = mock_result

        # 执行测试
        result = await trading_service.get_portfolio_summary(mock_db_session, "test-user-id")

        # 验证结果
        assert result["total_market_value"] == Decimal("3300.00")
        assert result["total_unrealized_pnl"] == Decimal("-50.00")
        assert result["position_count"] == 2
        assert len(result["positions"]) == 2
