"""
交易模型
包含订单、持仓、成交等交易相关数据
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.types import GUID


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"        # 市价单
    LIMIT = "limit"          # 限价单
    STOP = "stop"            # 止损单
    STOP_LIMIT = "stop_limit" # 止损限价单


class OrderSide(str, Enum):
    """买卖方向"""
    BUY = "buy"              # 买入
    SELL = "sell"            # 卖出


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"      # 待提交
    SUBMITTED = "submitted"  # 已提交
    PARTIAL = "partial"      # 部分成交
    FILLED = "filled"        # 全部成交
    CANCELLED = "cancelled"  # 已撤销
    REJECTED = "rejected"    # 已拒绝
    EXPIRED = "expired"      # 已过期


class PositionSide(str, Enum):
    """持仓方向"""
    LONG = "long"            # 多头
    SHORT = "short"          # 空头


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 订单基本信息
    order_id = Column(String(50), unique=True, nullable=False, index=True, comment="订单编号")
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    order_type = Column(SQLEnum(OrderType), nullable=False, comment="订单类型")
    side = Column(SQLEnum(OrderSide), nullable=False, comment="买卖方向")
    
    # 价格和数量
    quantity = Column(Integer, nullable=False, comment="委托数量")
    price = Column(Numeric(12, 4), nullable=True, comment="委托价格")
    stop_price = Column(Numeric(12, 4), nullable=True, comment="止损价格")
    
    # 成交信息
    filled_quantity = Column(Integer, default=0, comment="已成交数量")
    avg_fill_price = Column(Numeric(12, 4), nullable=True, comment="平均成交价格")
    
    # 订单状态
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, comment="订单状态")
    
    # 时间信息
    submit_time = Column(DateTime, nullable=True, comment="提交时间")
    fill_time = Column(DateTime, nullable=True, comment="成交时间")
    cancel_time = Column(DateTime, nullable=True, comment="撤销时间")
    
    # 其他信息
    commission = Column(Numeric(12, 4), default=0, comment="手续费")
    notes = Column(Text, nullable=True, comment="备注")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="orders")
    trades = relationship("Trade", back_populates="order")

    @hybrid_property
    def remaining_quantity(self):
        """剩余数量"""
        return self.quantity - self.filled_quantity

    @hybrid_property
    def fill_ratio(self):
        """成交比例"""
        if self.quantity > 0:
            return self.filled_quantity / self.quantity
        return 0

    @hybrid_property
    def is_filled(self):
        """是否完全成交"""
        return self.status == OrderStatus.FILLED

    @hybrid_property
    def is_active(self):
        """是否活跃订单"""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL]

    def __repr__(self):
        return f"<Order(id={self.order_id}, symbol={self.symbol_code}, side={self.side}, status={self.status})>"


class Trade(Base):
    """成交记录"""
    __tablename__ = "trades"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    order_id = Column(GUID(), ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 成交信息
    trade_id = Column(String(50), unique=True, nullable=False, index=True, comment="成交编号")
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    side = Column(SQLEnum(OrderSide), nullable=False, comment="买卖方向")
    
    # 价格和数量
    quantity = Column(Integer, nullable=False, comment="成交数量")
    price = Column(Numeric(12, 4), nullable=False, comment="成交价格")
    turnover = Column(Numeric(20, 2), nullable=False, comment="成交金额")
    
    # 费用
    commission = Column(Numeric(12, 4), default=0, comment="手续费")
    stamp_tax = Column(Numeric(12, 4), default=0, comment="印花税")
    transfer_fee = Column(Numeric(12, 4), default=0, comment="过户费")
    
    # 时间戳
    trade_time = Column(DateTime, nullable=False, comment="成交时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    order = relationship("Order", back_populates="trades")
    user = relationship("User", backref="trades")

    @hybrid_property
    def total_cost(self):
        """总成本（包含费用）"""
        return self.turnover + self.commission + self.stamp_tax + self.transfer_fee

    def __repr__(self):
        return f"<Trade(id={self.trade_id}, symbol={self.symbol_code}, price={self.price}, qty={self.quantity})>"


class Position(Base):
    """持仓模型"""
    __tablename__ = "positions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 持仓基本信息
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    side = Column(SQLEnum(PositionSide), nullable=False, comment="持仓方向")
    
    # 持仓数量
    quantity = Column(Integer, default=0, comment="持仓数量")
    available_quantity = Column(Integer, default=0, comment="可用数量")
    frozen_quantity = Column(Integer, default=0, comment="冻结数量")
    
    # 成本信息
    avg_cost = Column(Numeric(12, 4), default=0, comment="平均成本")
    total_cost = Column(Numeric(20, 2), default=0, comment="总成本")
    
    # 盈亏信息
    unrealized_pnl = Column(Numeric(20, 2), default=0, comment="未实现盈亏")
    realized_pnl = Column(Numeric(20, 2), default=0, comment="已实现盈亏")
    
    # 市值信息
    market_value = Column(Numeric(20, 2), default=0, comment="市值")
    last_price = Column(Numeric(12, 4), nullable=True, comment="最新价格")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="positions")

    @hybrid_property
    def total_pnl(self):
        """总盈亏"""
        return self.unrealized_pnl + self.realized_pnl

    @hybrid_property
    def pnl_ratio(self):
        """盈亏比例"""
        if self.total_cost > 0:
            return self.total_pnl / self.total_cost
        return 0

    @hybrid_property
    def is_empty(self):
        """是否空仓"""
        return self.quantity == 0

    def __repr__(self):
        return f"<Position(symbol={self.symbol_code}, side={self.side}, qty={self.quantity})>"


class Account(Base):
    """账户资金模型"""
    __tablename__ = "accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 账户基本信息
    account_id = Column(String(50), unique=True, nullable=False, index=True, comment="账户编号")
    account_name = Column(String(100), nullable=False, comment="账户名称")
    account_type = Column(String(20), default="stock", comment="账户类型")
    
    # 资金信息
    total_assets = Column(Numeric(20, 2), default=0, comment="总资产")
    available_cash = Column(Numeric(20, 2), default=0, comment="可用资金")
    frozen_cash = Column(Numeric(20, 2), default=0, comment="冻结资金")
    market_value = Column(Numeric(20, 2), default=0, comment="持仓市值")
    
    # 盈亏信息
    total_pnl = Column(Numeric(20, 2), default=0, comment="总盈亏")
    daily_pnl = Column(Numeric(20, 2), default=0, comment="当日盈亏")
    
    # 风险指标
    margin_ratio = Column(Numeric(8, 4), default=0, comment="保证金比例")
    risk_level = Column(String(10), default="low", comment="风险等级")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_tradable = Column(Boolean, default=True, comment="是否可交易")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="accounts")

    @hybrid_property
    def total_cash(self):
        """总现金"""
        return self.available_cash + self.frozen_cash

    @hybrid_property
    def position_ratio(self):
        """持仓比例"""
        if self.total_assets > 0:
            return self.market_value / self.total_assets
        return 0

    def __repr__(self):
        return f"<Account(id={self.account_id}, name={self.account_name}, assets={self.total_assets})>"


class TransactionLog(Base):
    """交易日志"""
    __tablename__ = "transaction_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 交易信息
    transaction_type = Column(String(20), nullable=False, comment="交易类型")
    symbol_code = Column(String(20), nullable=True, comment="标的代码")
    quantity = Column(Integer, nullable=True, comment="数量")
    price = Column(Numeric(12, 4), nullable=True, comment="价格")
    amount = Column(Numeric(20, 2), nullable=True, comment="金额")
    
    # 描述信息
    description = Column(Text, nullable=True, comment="描述")
    reference_id = Column(String(50), nullable=True, comment="关联ID")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="创建时间")

    # 关联关系
    user = relationship("User", backref="transaction_logs")

    def __repr__(self):
        return f"<TransactionLog(type={self.transaction_type}, amount={self.amount})>"