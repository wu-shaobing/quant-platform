"""
CTP交易接口数据模型
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class CTPOrderStatus(str, Enum):
    """CTP订单状态"""
    UNKNOWN = "0"           # 未知
    ALL_TRADED = "1"        # 全部成交
    PART_TRADED_QUEUEING = "2"  # 部分成交还在队列中
    PART_TRADED_NOT_QUEUEING = "3"  # 部分成交不在队列中
    NO_TRADE_QUEUEING = "4"     # 未成交还在队列中
    NO_TRADE_NOT_QUEUEING = "5"  # 未成交不在队列中
    CANCELED = "6"          # 撤单
    TOUCHED = "7"           # 触发
    ERROR = "8"             # 错误


class CTPDirection(str, Enum):
    """CTP买卖方向"""
    BUY = "0"   # 买
    SELL = "1"  # 卖


class CTPOffsetFlag(str, Enum):
    """CTP开平标志"""
    OPEN = "0"          # 开仓
    CLOSE = "1"         # 平仓
    FORCE_CLOSE = "2"   # 强平
    CLOSE_TODAY = "3"   # 平今
    CLOSE_YESTERDAY = "4"  # 平昨
    FORCE_OFF = "5"     # 强减
    LOCAL_FORCE_CLOSE = "6"  # 本地强平


class CTPOrder(Base):
    """CTP订单表"""
    __tablename__ = "ctp_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    user_id = Column(Integer, nullable=False, comment="用户ID")
    order_ref = Column(String(13), nullable=False, comment="报单引用")
    order_sys_id = Column(String(21), nullable=True, comment="报单编号")
    
    # 合约信息
    instrument_id = Column(String(31), nullable=False, comment="合约代码")
    exchange_id = Column(String(9), nullable=True, comment="交易所代码")
    
    # 订单信息
    direction = Column(String(1), nullable=False, comment="买卖方向")
    offset_flag = Column(String(1), nullable=False, comment="开平标志")
    order_price_type = Column(String(1), nullable=False, comment="报单价格条件")
    limit_price = Column(Numeric(15, 4), nullable=False, comment="价格")
    volume_total_original = Column(Integer, nullable=False, comment="数量")
    time_condition = Column(String(1), nullable=False, comment="有效期类型")
    volume_condition = Column(String(1), nullable=False, comment="成交量类型")
    min_volume = Column(Integer, nullable=False, default=1, comment="最小成交量")
    contingent_condition = Column(String(1), nullable=False, default="1", comment="触发条件")
    stop_price = Column(Numeric(15, 4), nullable=False, default=0, comment="止损价")
    force_close_reason = Column(String(1), nullable=False, default="0", comment="强平原因")
    is_auto_suspend = Column(Boolean, nullable=False, default=False, comment="自动挂起标志")
    
    # 状态信息
    order_status = Column(String(1), nullable=False, default=CTPOrderStatus.UNKNOWN, comment="报单状态")
    volume_traded = Column(Integer, nullable=False, default=0, comment="今成交数量")
    volume_total = Column(Integer, nullable=False, comment="剩余数量")
    
    # 时间信息
    insert_date = Column(String(9), nullable=True, comment="报单日期")
    insert_time = Column(String(9), nullable=True, comment="委托时间")
    active_time = Column(String(9), nullable=True, comment="激活时间")
    suspend_time = Column(String(9), nullable=True, comment="挂起时间")
    update_time = Column(String(9), nullable=True, comment="最后修改时间")
    cancel_time = Column(String(9), nullable=True, comment="撤销时间")
    
    # 其他信息
    front_id = Column(Integer, nullable=True, comment="前置编号")
    session_id = Column(Integer, nullable=True, comment="会话编号")
    user_product_info = Column(String(11), nullable=True, comment="用户端产品信息")
    status_msg = Column(String(81), nullable=True, comment="状态信息")
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_ctp_orders_user_id', 'user_id'),
        Index('idx_ctp_orders_order_ref', 'order_ref'),
        Index('idx_ctp_orders_order_sys_id', 'order_sys_id'),
        Index('idx_ctp_orders_instrument_id', 'instrument_id'),
        Index('idx_ctp_orders_status', 'order_status'),
        Index('idx_ctp_orders_created_at', 'created_at'),
    )


class CTPTrade(Base):
    """CTP成交表"""
    __tablename__ = "ctp_trades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    user_id = Column(Integer, nullable=False, comment="用户ID")
    trade_id = Column(String(21), nullable=False, unique=True, comment="成交编号")
    order_ref = Column(String(13), nullable=False, comment="报单引用")
    order_sys_id = Column(String(21), nullable=True, comment="报单编号")
    
    # 合约信息
    instrument_id = Column(String(31), nullable=False, comment="合约代码")
    exchange_id = Column(String(9), nullable=True, comment="交易所代码")
    
    # 成交信息
    direction = Column(String(1), nullable=False, comment="买卖方向")
    offset_flag = Column(String(1), nullable=False, comment="开平标志")
    price = Column(Numeric(15, 4), nullable=False, comment="价格")
    volume = Column(Integer, nullable=False, comment="数量")
    
    # 时间信息
    trade_date = Column(String(9), nullable=True, comment="成交日期")
    trade_time = Column(String(9), nullable=True, comment="成交时间")
    
    # 其他信息
    trader_id = Column(String(21), nullable=True, comment="交易所交易员代码")
    order_local_id = Column(String(13), nullable=True, comment="本地报单编号")
    clearing_part_id = Column(String(11), nullable=True, comment="结算会员编号")
    business_unit = Column(String(21), nullable=True, comment="业务单元")
    sequence_no = Column(Integer, nullable=True, comment="序号")
    trading_day = Column(String(9), nullable=True, comment="交易日")
    settlement_id = Column(Integer, nullable=True, comment="结算编号")
    broker_order_seq = Column(Integer, nullable=True, comment="经纪公司报单编号")
    trade_source = Column(String(1), nullable=True, comment="成交来源")
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_ctp_trades_user_id', 'user_id'),
        Index('idx_ctp_trades_trade_id', 'trade_id'),
        Index('idx_ctp_trades_order_ref', 'order_ref'),
        Index('idx_ctp_trades_instrument_id', 'instrument_id'),
        Index('idx_ctp_trades_created_at', 'created_at'),
    )


class CTPPosition(Base):
    """CTP持仓表"""
    __tablename__ = "ctp_positions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    user_id = Column(Integer, nullable=False, comment="用户ID")
    instrument_id = Column(String(31), nullable=False, comment="合约代码")
    position_direction = Column(String(1), nullable=False, comment="持仓方向")
    hedge_flag = Column(String(1), nullable=False, default="1", comment="投机套保标志")
    position_date = Column(String(1), nullable=False, comment="持仓日期")
    
    # 持仓数量
    yd_position = Column(Integer, nullable=False, default=0, comment="上日持仓")
    position = Column(Integer, nullable=False, default=0, comment="今日持仓")
    long_frozen = Column(Integer, nullable=False, default=0, comment="多头冻结")
    short_frozen = Column(Integer, nullable=False, default=0, comment="空头冻结")
    long_frozen_amount = Column(Numeric(15, 4), nullable=False, default=0, comment="开仓冻结金额")
    short_frozen_amount = Column(Numeric(15, 4), nullable=False, default=0, comment="开仓冻结金额")
    yd_long_frozen = Column(Integer, nullable=False, default=0, comment="昨日多头冻结")
    yd_short_frozen = Column(Integer, nullable=False, default=0, comment="昨日空头冻结")
    
    # 成本信息
    position_cost = Column(Numeric(15, 4), nullable=False, default=0, comment="持仓成本")
    pre_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="上次占用的保证金")
    use_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="占用的保证金")
    frozen_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的保证金")
    frozen_cash = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的资金")
    frozen_commission = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的手续费")
    cash_in = Column(Numeric(15, 4), nullable=False, default=0, comment="资金差额")
    commission = Column(Numeric(15, 4), nullable=False, default=0, comment="手续费")
    
    # 盈亏信息
    close_profit = Column(Numeric(15, 4), nullable=False, default=0, comment="平仓盈亏")
    position_profit = Column(Numeric(15, 4), nullable=False, default=0, comment="持仓盈亏")
    pre_settlement_price = Column(Numeric(15, 4), nullable=False, default=0, comment="上次结算价")
    settlement_price = Column(Numeric(15, 4), nullable=False, default=0, comment="本次结算价")
    
    # 其他信息
    trading_day = Column(String(9), nullable=True, comment="交易日")
    settlement_id = Column(Integer, nullable=True, comment="结算编号")
    open_cost = Column(Numeric(15, 4), nullable=False, default=0, comment="开仓成本")
    exchange_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="交易所保证金")
    combine_position = Column(Integer, nullable=False, default=0, comment="组合成交形成的持仓")
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_ctp_positions_user_id', 'user_id'),
        Index('idx_ctp_positions_instrument_id', 'instrument_id'),
        Index('idx_ctp_positions_direction', 'position_direction'),
        Index('idx_ctp_positions_created_at', 'created_at'),
    )


class CTPAccount(Base):
    """CTP账户资金表"""
    __tablename__ = "ctp_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 基础信息
    user_id = Column(Integer, nullable=False, comment="用户ID")
    broker_id = Column(String(11), nullable=False, comment="经纪公司代码")
    account_id = Column(String(13), nullable=False, comment="投资者帐号")
    
    # 资金信息
    pre_mortgage = Column(Numeric(15, 4), nullable=False, default=0, comment="上次质押金额")
    pre_credit = Column(Numeric(15, 4), nullable=False, default=0, comment="上次信用额度")
    pre_deposit = Column(Numeric(15, 4), nullable=False, default=0, comment="上次存款额")
    pre_balance = Column(Numeric(15, 4), nullable=False, default=0, comment="上次结算准备金")
    pre_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="上次占用的保证金")
    interest_base = Column(Numeric(15, 4), nullable=False, default=0, comment="利息基数")
    interest = Column(Numeric(15, 4), nullable=False, default=0, comment="利息收入")
    deposit = Column(Numeric(15, 4), nullable=False, default=0, comment="入金金额")
    withdraw = Column(Numeric(15, 4), nullable=False, default=0, comment="出金金额")
    frozen_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的保证金")
    frozen_cash = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的资金")
    frozen_commission = Column(Numeric(15, 4), nullable=False, default=0, comment="冻结的手续费")
    curr_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="当前保证金总额")
    cash_in = Column(Numeric(15, 4), nullable=False, default=0, comment="资金差额")
    commission = Column(Numeric(15, 4), nullable=False, default=0, comment="手续费")
    close_profit = Column(Numeric(15, 4), nullable=False, default=0, comment="平仓盈亏")
    position_profit = Column(Numeric(15, 4), nullable=False, default=0, comment="持仓盈亏")
    balance = Column(Numeric(15, 4), nullable=False, default=0, comment="期货结算准备金")
    available = Column(Numeric(15, 4), nullable=False, default=0, comment="可用资金")
    withdraw_quota = Column(Numeric(15, 4), nullable=False, default=0, comment="可取资金")
    reserve = Column(Numeric(15, 4), nullable=False, default=0, comment="基本准备金")
    trading_day = Column(String(9), nullable=True, comment="交易日")
    settlement_id = Column(Integer, nullable=True, comment="结算编号")
    credit = Column(Numeric(15, 4), nullable=False, default=0, comment="信用额度")
    mortgage = Column(Numeric(15, 4), nullable=False, default=0, comment="质押金额")
    exchange_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="交易所保证金")
    delivery_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="投资者交割保证金")
    exchange_delivery_margin = Column(Numeric(15, 4), nullable=False, default=0, comment="交易所交割保证金")
    reserve_balance = Column(Numeric(15, 4), nullable=False, default=0, comment="保底期货结算准备金")
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_ctp_accounts_user_id', 'user_id'),
        Index('idx_ctp_accounts_broker_id', 'broker_id'),
        Index('idx_ctp_accounts_account_id', 'account_id'),
        Index('idx_ctp_accounts_created_at', 'created_at'),
    )
