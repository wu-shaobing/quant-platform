"""
交易服务模块 - 实现完整的交易流程和订单状态机
"""
import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, update
from sqlalchemy.orm import selectinload

from app.models.trading import Order, Trade, Position, Account
from app.schemas.trading import (
    OrderRequest, OrderData, TradeData, PositionData, AccountData,
    OrderStatus, Direction, Offset
)
from app.utils.exceptions import DataNotFoundError

logger = logging.getLogger(__name__)


class OrderStateMachine:
    """订单状态机"""

    # 状态转换映射
    VALID_TRANSITIONS = {
        OrderStatus.SUBMITTING: [OrderStatus.SUBMITTED, OrderStatus.REJECTED],
        OrderStatus.SUBMITTED: [OrderStatus.PARTIAL_FILLED, OrderStatus.ALL_FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED],
        OrderStatus.PARTIAL_FILLED: [OrderStatus.ALL_FILLED, OrderStatus.CANCELLED],
        OrderStatus.ALL_FILLED: [],  # 终态
        OrderStatus.CANCELLED: [],   # 终态
        OrderStatus.REJECTED: []     # 终态
    }

    @classmethod
    def can_transition(cls, from_status: OrderStatus, to_status: OrderStatus) -> bool:
        """检查状态转换是否有效"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, [])

    @classmethod
    def is_final_status(cls, status: OrderStatus) -> bool:
        """检查是否为终态"""
        return len(cls.VALID_TRANSITIONS.get(status, [])) == 0

    @classmethod
    def is_active_status(cls, status: OrderStatus) -> bool:
        """检查是否为活跃状态"""
        return status in [OrderStatus.PENDING, OrderStatus.SUBMITTING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]


class TradingService:
    """交易服务类 - 实现完整的交易流程"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._order_locks = {}  # 订单锁，防止并发修改
        self._position_locks = {}  # 持仓锁

    async def _get_order_lock(self, order_id: str) -> asyncio.Lock:
        """获取订单锁"""
        if order_id not in self._order_locks:
            self._order_locks[order_id] = asyncio.Lock()
        return self._order_locks[order_id]

    async def _get_position_lock(self, user_id: int, symbol: str) -> asyncio.Lock:
        """获取持仓锁"""
        key = f"{user_id}_{symbol}"
        if key not in self._position_locks:
            self._position_locks[key] = asyncio.Lock()
        return self._position_locks[key]

    async def submit_order(self, user_id: int, order_request: OrderRequest) -> Dict[str, Any]:
        """提交订单 - 完整流程"""
        try:
            # 1. 风险检查
            await self._validate_order_request(user_id, order_request)

            # 2. 创建订单对象
            order = Order(
                user_id=user_id,
                symbol=order_request.symbol,
                exchange=order_request.exchange,
                direction=order_request.direction,
                offset=order_request.offset,
                order_type=order_request.order_type,
                volume=order_request.volume,
                price=order_request.price,
                status=OrderStatus.PENDING,
                traded=0.0,
                order_time=datetime.now()
            )

            # 3. 保存到数据库
            self.db.add(order)
            await self.db.commit()
            await self.db.refresh(order)

            # 4. 异步提交到CTP
            asyncio.create_task(self._submit_to_ctp(order))

            return {
                "success": True,
                "order_id": order.order_id,
                "message": "订单提交成功",
                "data": order
            }

        except Exception as e:
            logger.error(f"订单提交失败: {e}")
            return {
                "success": False,
                "message": f"订单提交失败: {str(e)}"
            }

    async def _validate_order_request(self, user_id: int, order_request: OrderRequest):
        """验证订单请求"""
        # 检查账户资金
        account = await self.get_account(user_id)
        if not account:
            raise ValueError("账户不存在")

        # 检查资金充足性
        if order_request.direction == Direction.BUY:
            required_margin = order_request.volume * order_request.price * 0.1  # 假设10%保证金
            if account.available_cash < required_margin:
                raise ValueError("资金不足")

        # 检查持仓限制
        if order_request.offset in [Offset.CLOSE, Offset.CLOSE_TODAY, Offset.CLOSE_YESTERDAY]:
            position = await self._get_position(user_id, order_request.symbol, order_request.direction)
            if not position or position.volume < order_request.volume:
                raise ValueError("持仓不足")

    async def _submit_to_ctp(self, order: Order):
        """异步提交订单到CTP"""
        try:
            # 更新状态为提交中
            await self._update_order_status(order.order_id, OrderStatus.SUBMITTING)

            # 模拟CTP提交过程
            await asyncio.sleep(0.1)  # 模拟网络延迟

            # 模拟成功率90%
            import random
            if random.random() > 0.1:
                await self._update_order_status(order.order_id, OrderStatus.SUBMITTED)
                logger.info(f"订单 {order.order_id} 提交成功")

                # 模拟部分成交
                if random.random() > 0.7:  # 30%概率立即成交
                    await asyncio.sleep(0.5)
                    await self._simulate_trade(order)
            else:
                await self._update_order_status(order.order_id, OrderStatus.REJECTED, "市场拒绝")
                logger.warning(f"订单 {order.order_id} 被拒绝")

        except Exception as e:
            logger.error(f"CTP提交失败: {e}")
            await self._update_order_status(order.order_id, OrderStatus.REJECTED, str(e))

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """撤销订单"""
        try:
            async with await self._get_order_lock(order_id):
                # 查找订单
                result = await self.db.execute(
                    select(Order).where(Order.order_id == order_id)
                )
                order = result.scalar_one_or_none()

                if not order:
                    return {"success": False, "message": "订单不存在"}

                # 检查订单状态
                if not OrderStateMachine.can_transition(order.status, OrderStatus.CANCELLED):
                    return {"success": False, "message": f"订单状态 {order.status} 不允许撤销"}

                # 更新订单状态
                await self._update_order_status(order_id, OrderStatus.CANCELLED)

                return {"success": True, "message": "撤单成功"}

        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return {"success": False, "message": f"撤单失败: {str(e)}"}

    async def _update_order_status(self, order_id: str, new_status: OrderStatus, message: str = None):
        """更新订单状态"""
        async with await self._get_order_lock(order_id):
            result = await self.db.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError(f"订单 {order_id} 不存在")

            # 检查状态转换是否有效
            if not OrderStateMachine.can_transition(order.status, new_status):
                raise ValueError(f"无效的状态转换: {order.status} -> {new_status}")

            # 更新状态
            order.status = new_status
            if message:
                order.status_msg = message
            order.update_time = datetime.now()

            await self.db.commit()
            logger.info(f"订单 {order_id} 状态更新: {order.status} -> {new_status}")

            return order

    async def _simulate_trade(self, order: Order):
        """模拟成交"""
        import random

        # 随机成交数量（部分或全部）
        trade_volume = min(order.volume - order.traded,
                          random.uniform(0.3, 1.0) * (order.volume - order.traded))

        if trade_volume > 0:
            await self.process_trade({
                'trade_id': f"T{uuid.uuid4().hex[:8]}",
                'order_id': order.order_id,
                'user_id': order.user_id,
                'symbol': order.symbol,
                'exchange': order.exchange,
                'direction': order.direction,
                'offset': order.offset,
                'volume': trade_volume,
                'price': order.price,
                'trade_time': datetime.now(),
                'commission': trade_volume * order.price * 0.0003  # 0.03%手续费
            })

    async def process_trade(self, trade_data: dict) -> Trade:
        """处理成交回报"""
        try:
            async with await self._get_order_lock(trade_data['order_id']):
                # 创建成交记录
                trade = Trade(
                    trade_id=trade_data['trade_id'],
                    order_id=trade_data['order_id'],
                    user_id=trade_data['user_id'],
                    symbol=trade_data['symbol'],
                    exchange=trade_data['exchange'],
                    direction=trade_data['direction'],
                    offset=trade_data['offset'],
                    volume=trade_data['volume'],
                    price=trade_data['price'],
                    trade_time=trade_data.get('trade_time', datetime.now()),
                    commission=trade_data.get('commission', 0.0)
                )

                self.db.add(trade)

                # 更新订单状态
                order = await self.get_order_by_id(trade_data['order_id'])
                if order:
                    order.traded += trade_data['volume']
                    if order.traded >= order.volume:
                        await self._update_order_status(order.order_id, OrderStatus.ALL_FILLED)
                    else:
                        await self._update_order_status(order.order_id, OrderStatus.PARTIAL_FILLED)

                # 更新持仓
                await self._update_position_from_trade(trade_data)

                await self.db.commit()
                logger.info(f"成交处理完成: {trade_data['trade_id']}")

                return trade

        except Exception as e:
            logger.error(f"成交处理失败: {e}")
            raise

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """根据ID获取订单"""
        result = await self.db.execute(
            select(Order).where(Order.order_id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_orders(
        self, 
        user_id: int, 
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """查询订单列表"""
        query = select(Order).where(Order.user_id == user_id)
        
        if symbol:
            query = query.where(Order.symbol == symbol)
        if status:
            query = query.where(Order.status == status)
            
        query = query.offset(skip).limit(limit).order_by(desc(Order.order_time))
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        # 如果没有订单记录，创建一些模拟订单
        if not orders and skip == 0:
            mock_orders = [
                Order(
                    user_id=user_id,
                    order_id=f"DEMO_{i}",
                    symbol="IF2501",
                    exchange="CFFEX",
                    direction=Direction.BUY if i % 2 == 0 else Direction.SELL,
                    offset=Offset.OPEN,
                    order_type="LIMIT",
                    volume=1,
                    price=4200.0 + i * 10,
                    status=OrderStatus.ALL_FILLED if i < 2 else OrderStatus.SUBMITTED,
                    traded=1 if i < 2 else 0,
                    order_time=datetime.now(),
                    update_time=datetime.now()
                )
                for i in range(5)
            ]
            
            for order in mock_orders:
                self.db.add(order)
            await self.db.commit()
            
            orders = mock_orders
        
        return orders
    
    async def get_trades(
        self,
        user_id: int,
        symbol: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Trade]:
        """查询成交记录"""
        query = select(Trade).where(Trade.user_id == user_id)
        
        if symbol:
            query = query.where(Trade.symbol == symbol)
            
        query = query.offset(skip).limit(limit).order_by(desc(Trade.trade_time))
        
        result = await self.db.execute(query)
        trades = result.scalars().all()
        
        # 如果没有成交记录，创建一些模拟成交
        if not trades and skip == 0:
            mock_trades = [
                Trade(
                    user_id=user_id,
                    trade_id=f"TRADE_{i}",
                    order_id=f"DEMO_{i}",
                    symbol="IF2501",
                    exchange="CFFEX",
                    direction=Direction.BUY if i % 2 == 0 else Direction.SELL,
                    offset=Offset.OPEN,
                    volume=1,
                    price=4200.0 + i * 5,
                    commission=5.0,
                    trade_time=datetime.now()
                )
                for i in range(3)
            ]
            
            for trade in mock_trades:
                self.db.add(trade)
            await self.db.commit()
            
            trades = mock_trades
        
        return trades
    
    async def get_positions(
        self,
        user_id: int,
        symbol: Optional[str] = None
    ) -> List[Position]:
        """查询持仓"""
        query = select(Position).where(Position.user_id == user_id)
        
        if symbol:
            query = query.where(Position.symbol == symbol)
            
        result = await self.db.execute(query)
        positions = result.scalars().all()
        
        # 如果没有持仓记录，创建一些模拟持仓
        if not positions:
            mock_positions = [
                Position(
                    user_id=user_id,
                    symbol="IF2501",
                    exchange="CFFEX",
                    direction=Direction.BUY,
                    volume=2,
                    avg_price=4180.0,
                    market_price=4200.0,
                    profit_loss=400.0,
                    margin=83600.0,
                    today_volume=1,
                    yesterday_volume=1,
                    frozen_volume=0,
                    last_update_time=datetime.now()
                ),
                Position(
                    user_id=user_id,
                    symbol="IC2501",
                    exchange="CFFEX",
                    direction=Direction.SELL,
                    volume=1,
                    avg_price=6850.0,
                    market_price=6820.0,
                    profit_loss=300.0,
                    margin=68200.0,
                    today_volume=0,
                    yesterday_volume=1,
                    frozen_volume=0,
                    last_update_time=datetime.now()
                )
            ]
            
            for position in mock_positions:
                self.db.add(position)
            await self.db.commit()
            
            positions = mock_positions
        
        return positions
    
    async def get_account(self, user_id: int) -> Optional[Account]:
        """获取账户信息"""
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        account = result.scalar_one_or_none()
        
        # 如果没有账户记录，创建一个模拟账户
        if not account:
            account = Account(
                user_id=user_id,
                account_id=f"DEMO_{user_id}",
                broker_id="DEMO",
                total_asset=1000000.0,  # 100万模拟资金
                available_cash=800000.0,  # 80万可用资金
                frozen_cash=0.0,
                total_market_value=200000.0,  # 20万持仓市值
                total_profit_loss=5000.0,  # 5千盈亏
                day_profit_loss=1200.0,  # 当日盈亏1200
                commission=50.0,  # 手续费50
                margin_used=200000.0,  # 占用保证金20万
                risk_ratio=0.2,  # 风险度20%
                currency="CNY",
                status="ACTIVE",
                last_update_time=datetime.now()
            )
            self.db.add(account)
            await self.db.commit()
            await self.db.refresh(account)
        
        return account

    # 风险管理方法
    async def calculate_portfolio_risk(self, user_id: int) -> Dict[str, Any]:
        """计算投资组合风险"""
        positions = await self.get_positions(user_id)
        account = await self.get_account(user_id)

        if not account:
            return {"error": "账户不存在"}

        total_market_value = sum(abs(pos.volume * pos.price) for pos in positions)
        leverage = total_market_value / account.total_assets if account.total_assets > 0 else 0

        return {
            "total_market_value": total_market_value,
            "leverage": leverage,
            "position_count": len(positions),
            "max_single_position": max((abs(pos.volume * pos.price) for pos in positions), default=0),
            "concentration_risk": max((abs(pos.volume * pos.price) / total_market_value for pos in positions), default=0) if total_market_value > 0 else 0
        }

    async def get_trading_summary(self, user_id: int, date_from: datetime = None) -> Dict[str, Any]:
        """获取交易汇总"""
        query = select(Trade).where(Trade.user_id == user_id)

        if date_from:
            query = query.where(Trade.trade_time >= date_from)

        result = await self.db.execute(query)
        trades = result.scalars().all()

        if not trades:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "total_turnover": 0,
                "total_commission": 0,
                "avg_price": 0
            }

        total_volume = sum(trade.volume for trade in trades)
        total_turnover = sum(trade.volume * trade.price for trade in trades)
        total_commission = sum(trade.commission for trade in trades)

        return {
            "total_trades": len(trades),
            "total_volume": total_volume,
            "total_turnover": total_turnover,
            "total_commission": total_commission,
            "avg_price": total_turnover / total_volume if total_volume > 0 else 0
        }

    async def _update_position_from_trade(self, trade_data: dict):
        """根据成交更新持仓"""
        user_id = trade_data['user_id']
        symbol = trade_data['symbol']

        async with await self._get_position_lock(user_id, symbol):
            # 查找现有持仓
            result = await self.db.execute(
                select(Position).where(
                    and_(
                        Position.user_id == user_id,
                        Position.symbol == symbol
                    )
                )
            )
            position = result.scalar_one_or_none()

            volume_change = trade_data['volume']
            price = trade_data['price']

            # 根据开平仓和买卖方向计算持仓变化
            if trade_data['offset'] == Offset.OPEN:
                # 开仓
                if trade_data['direction'] == Direction.BUY:
                    volume_change = volume_change  # 多头持仓增加
                else:
                    volume_change = -volume_change  # 空头持仓增加
            else:
                # 平仓
                if trade_data['direction'] == Direction.BUY:
                    volume_change = volume_change  # 买入平空，空头持仓减少
                else:
                    volume_change = -volume_change  # 卖出平多，多头持仓减少

            if not position:
                # 创建新持仓
                position = Position(
                    user_id=user_id,
                    symbol=symbol,
                    volume=volume_change,
                    price=price,
                    pnl=0.0,
                    direction=Direction.BUY if volume_change > 0 else Direction.SELL
                )
                self.db.add(position)
            else:
                # 更新现有持仓
                if position.volume == 0:
                    # 新开仓
                    position.volume = volume_change
                    position.price = price
                    position.direction = Direction.BUY if volume_change > 0 else Direction.SELL
                else:
                    # 计算新的平均成本
                    if (position.volume > 0 and volume_change > 0) or (position.volume < 0 and volume_change < 0):
                        # 同向加仓
                        total_cost = abs(position.volume) * position.price + abs(volume_change) * price
                        position.volume += volume_change
                        if position.volume != 0:
                            position.price = total_cost / abs(position.volume)
                    else:
                        # 反向平仓
                        position.volume += volume_change
                        if position.volume == 0:
                            position.price = 0
                        elif position.volume * (position.volume - volume_change) < 0:
                            # 反向开仓
                            position.price = price
                            position.direction = Direction.BUY if position.volume > 0 else Direction.SELL

                # 更新方向
                if position.volume > 0:
                    position.direction = Direction.BUY
                elif position.volume < 0:
                    position.direction = Direction.SELL

            # 计算未实现盈亏（需要当前市价）
            # 这里简化处理，实际应该获取实时行情
            position.pnl = 0.0

            return position

    async def _get_position(self, user_id: int, symbol: str, direction: Direction = None) -> Optional[Position]:
        """获取持仓"""
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.symbol == symbol
            )
        )

        if direction:
            query = query.where(Position.direction == direction)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()