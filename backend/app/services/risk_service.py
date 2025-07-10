# 风控服务
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.trading import Order, Trade, Position, Account
from app.models.user import User
from app.schemas.trading import (
    OrderRequest, RiskLimitData, RiskCheckResult, 
    OrderStatus, Direction, Offset
)
from app.utils.exceptions import DataNotFoundError


class RiskService:
    """风控服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_order_risk(
        self, 
        user_id: int, 
        order_request: OrderRequest
    ) -> RiskCheckResult:
        """检查订单风险"""
        
        # 1. 检查用户状态
        user_check = await self._check_user_status(user_id)
        if not user_check.passed:
            return user_check
        
        # 2. 检查资金充足性
        fund_check = await self._check_fund_sufficiency(user_id, order_request)
        if not fund_check.passed:
            return fund_check
        
        # 3. 检查持仓限制
        position_check = await self._check_position_limit(user_id, order_request)
        if not position_check.passed:
            return position_check
        
        # 4. 检查单笔委托限制
        order_size_check = await self._check_order_size_limit(user_id, order_request)
        if not order_size_check.passed:
            return order_size_check
        
        # 5. 检查日交易限制
        daily_limit_check = await self._check_daily_trading_limit(user_id, order_request)
        if not daily_limit_check.passed:
            return daily_limit_check
        
        # 6. 检查禁止交易合约
        symbol_check = await self._check_forbidden_symbols(user_id, order_request.symbol)
        if not symbol_check.passed:
            return symbol_check
        
        return RiskCheckResult(passed=True, message="风控检查通过")
    
    async def _check_user_status(self, user_id: int) -> RiskCheckResult:
        """检查用户状态"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return RiskCheckResult(passed=False, message="用户不存在")
        
        if not user.is_active:
            return RiskCheckResult(passed=False, message="用户账户已禁用")
        
        # TODO: 检查用户是否有交易权限
        
        return RiskCheckResult(passed=True, message="用户状态正常")
    
    async def _check_fund_sufficiency(
        self, 
        user_id: int, 
        order_request: OrderRequest
    ) -> RiskCheckResult:
        """检查资金充足性"""
        # 获取账户信息
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            return RiskCheckResult(passed=False, message="账户信息不存在")
        
        # 计算所需保证金（简化计算）
        required_margin = self._calculate_required_margin(order_request)
        
        if account.available < required_margin:
            return RiskCheckResult(
                passed=False, 
                message=f"资金不足，可用资金: {account.available}, 所需保证金: {required_margin}"
            )
        
        return RiskCheckResult(passed=True, message="资金充足")
    
    async def _check_position_limit(
        self, 
        user_id: int, 
        order_request: OrderRequest
    ) -> RiskCheckResult:
        """检查持仓限制"""
        # 获取当前持仓
        result = await self.db.execute(
            select(Position).where(
                and_(
                    Position.user_id == user_id,
                    Position.symbol == order_request.symbol
                )
            )
        )
        positions = result.scalars().all()
        
        current_volume = sum(pos.volume for pos in positions)
        
        # 计算开仓后的持仓量
        if order_request.offset == Offset.OPEN:
            new_volume = current_volume + order_request.volume
        else:
            new_volume = max(0, current_volume - order_request.volume)
        
        # 获取持仓限制（这里使用默认值，实际应该从配置中获取）
        max_position = await self._get_max_position_limit(user_id, order_request.symbol)
        
        if new_volume > max_position:
            return RiskCheckResult(
                passed=False,
                message=f"持仓超限，当前持仓: {current_volume}, 最大持仓: {max_position}"
            )
        
        return RiskCheckResult(passed=True, message="持仓检查通过")
    
    async def _check_order_size_limit(
        self, 
        user_id: int, 
        order_request: OrderRequest
    ) -> RiskCheckResult:
        """检查单笔委托限制"""
        max_order_size = await self._get_max_order_size_limit(user_id, order_request.symbol)
        
        if order_request.volume > max_order_size:
            return RiskCheckResult(
                passed=False,
                message=f"单笔委托超限，委托量: {order_request.volume}, 最大委托: {max_order_size}"
            )
        
        return RiskCheckResult(passed=True, message="单笔委托检查通过")
    
    async def _check_daily_trading_limit(
        self, 
        user_id: int, 
        order_request: OrderRequest
    ) -> RiskCheckResult:
        """检查日交易限制"""
        today = date.today()
        
        # 查询今日交易量
        result = await self.db.execute(
            select(func.sum(Trade.volume)).where(
                and_(
                    Trade.user_id == user_id,
                    Trade.symbol == order_request.symbol,
                    func.date(Trade.trade_time) == today
                )
            )
        )
        daily_volume = result.scalar() or 0
        
        # 获取日交易限制
        max_daily_volume = await self._get_max_daily_volume_limit(user_id, order_request.symbol)
        
        if daily_volume + order_request.volume > max_daily_volume:
            return RiskCheckResult(
                passed=False,
                message=f"日交易量超限，今日已交易: {daily_volume}, 最大日交易量: {max_daily_volume}"
            )
        
        return RiskCheckResult(passed=True, message="日交易限制检查通过")
    
    async def _check_forbidden_symbols(
        self, 
        user_id: int, 
        symbol: str
    ) -> RiskCheckResult:
        """检查禁止交易合约"""
        forbidden_symbols = await self._get_forbidden_symbols(user_id)
        
        if symbol in forbidden_symbols:
            return RiskCheckResult(passed=False, message=f"合约 {symbol} 被禁止交易")
        
        return RiskCheckResult(passed=True, message="合约检查通过")
    
    def _calculate_required_margin(self, order_request: OrderRequest) -> float:
        """计算所需保证金（简化版本）"""
        # 这里使用简化的保证金计算
        # 实际应该根据合约规格、保证金率等计算
        if order_request.price:
            return order_request.volume * order_request.price * 0.1  # 假设10%保证金率
        else:
            return order_request.volume * 100 * 0.1  # 市价单使用估算价格
    
    async def _get_max_position_limit(self, user_id: int, symbol: str) -> float:
        """获取最大持仓限制"""
        # 这里返回默认值，实际应该从数据库或配置中获取
        return 1000.0
    
    async def _get_max_order_size_limit(self, user_id: int, symbol: str) -> float:
        """获取最大单笔委托限制"""
        # 这里返回默认值，实际应该从数据库或配置中获取
        return 100.0
    
    async def _get_max_daily_volume_limit(self, user_id: int, symbol: str) -> float:
        """获取最大日交易量限制"""
        # 这里返回默认值，实际应该从数据库或配置中获取
        return 10000.0
    
    async def _get_forbidden_symbols(self, user_id: int) -> List[str]:
        """获取禁止交易的合约列表"""
        # 这里返回空列表，实际应该从数据库或配置中获取
        return []
    
    async def get_risk_limits(self, user_id: int) -> RiskLimitData:
        """获取风控限制"""
        return RiskLimitData(
            max_position=await self._get_max_position_limit(user_id, ""),
            max_order_size=await self._get_max_order_size_limit(user_id, ""),
            max_daily_loss=50000.0,  # 默认值
            max_total_loss=100000.0,  # 默认值
            allowed_symbols=[],
            forbidden_symbols=await self._get_forbidden_symbols(user_id)
        )
    
    async def update_risk_limits(
        self, 
        user_id: int, 
        risk_limits: RiskLimitData
    ) -> RiskLimitData:
        """更新风控限制"""
        # TODO: 实现风控限制的数据库存储和更新
        # 这里暂时返回传入的数据
        return risk_limits
    
    async def check_daily_loss_limit(self, user_id: int) -> RiskCheckResult:
        """检查日亏损限制"""
        today = date.today()
        
        # 计算今日盈亏
        result = await self.db.execute(
            select(func.sum(Trade.volume * Trade.price)).where(
                and_(
                    Trade.user_id == user_id,
                    func.date(Trade.trade_time) == today
                )
            )
        )
        daily_pnl = result.scalar() or 0
        
        max_daily_loss = 50000.0  # 默认值，应该从配置获取
        
        if daily_pnl < -max_daily_loss:
            return RiskCheckResult(passed=False, message=f"日亏损超限: {abs(daily_pnl)}")
        
        return RiskCheckResult(passed=True, message="日亏损检查通过")
    
    async def check_total_loss_limit(self, user_id: int) -> RiskCheckResult:
        """检查总亏损限制"""
        # 计算总盈亏
        result = await self.db.execute(
            select(func.sum(Trade.volume * Trade.price)).where(
                Trade.user_id == user_id
            )
        )
        total_pnl = result.scalar() or 0
        
        max_total_loss = 100000.0  # 默认值，应该从配置获取
        
        if total_pnl < -max_total_loss:
            return RiskCheckResult(False, f"总亏损超限: {abs(total_pnl)}")
        
        return RiskCheckResult(True, "总亏损检查通过")