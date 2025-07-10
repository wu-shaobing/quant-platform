"""
市场数据模型
包含行情数据、K线数据、深度数据等
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Index, Text, Boolean, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.types import GUID
from app.schemas.market import Exchange, ProductClass, Interval


class MarketType(str, Enum):
    """市场类型"""
    STOCK = "stock"          # 股票
    FUTURES = "futures"      # 期货
    OPTIONS = "options"      # 期权
    FOREX = "forex"          # 外汇
    CRYPTO = "crypto"        # 数字货币


class KLineType(str, Enum):
    """K线类型"""
    MINUTE_1 = "1m"         # 1分钟
    MINUTE_5 = "5m"         # 5分钟
    MINUTE_15 = "15m"       # 15分钟
    MINUTE_30 = "30m"       # 30分钟
    HOUR_1 = "1h"           # 1小时
    HOUR_4 = "4h"           # 4小时
    DAY_1 = "1d"            # 日线
    WEEK_1 = "1w"           # 周线
    MONTH_1 = "1M"          # 月线


class Symbol(Base):
    """交易标的基础信息"""
    __tablename__ = "symbols"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False, comment="代码")
    name = Column(String(100), nullable=False, comment="名称")
    market_type = Column(SQLEnum(MarketType), nullable=False, comment="市场类型")
    exchange = Column(String(20), nullable=False, comment="交易所")
    
    # 基础信息
    sector = Column(String(50), nullable=True, comment="行业")
    industry = Column(String(50), nullable=True, comment="细分行业")
    currency = Column(String(10), default="CNY", comment="计价货币")
    
    # 交易参数
    lot_size = Column(Integer, default=100, comment="每手股数")
    tick_size = Column(Numeric(10, 6), default=0.01, comment="最小价格变动")
    price_limit_up = Column(Numeric(10, 2), nullable=True, comment="涨停价")
    price_limit_down = Column(Numeric(10, 2), nullable=True, comment="跌停价")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_tradable = Column(Boolean, default=True, comment="是否可交易")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<Symbol(code={self.code}, name={self.name}, market_type={self.market_type})>"


class MarketData(Base):
    """实时行情数据"""
    __tablename__ = "market_data"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    
    # 价格数据
    last_price = Column(Numeric(12, 4), nullable=False, comment="最新价")
    open_price = Column(Numeric(12, 4), nullable=True, comment="开盘价")
    high_price = Column(Numeric(12, 4), nullable=True, comment="最高价")
    low_price = Column(Numeric(12, 4), nullable=True, comment="最低价")
    pre_close = Column(Numeric(12, 4), nullable=True, comment="昨收价")
    
    # 成交数据
    volume = Column(Integer, default=0, comment="成交量")
    turnover = Column(Numeric(20, 2), default=0, comment="成交额")
    
    # 买卖盘数据
    bid_price = Column(Numeric(12, 4), nullable=True, comment="买一价")
    bid_volume = Column(Integer, nullable=True, comment="买一量")
    ask_price = Column(Numeric(12, 4), nullable=True, comment="卖一价")
    ask_volume = Column(Integer, nullable=True, comment="卖一量")
    
    # 统计数据
    change = Column(Numeric(12, 4), nullable=True, comment="涨跌额")
    change_percent = Column(Numeric(8, 4), nullable=True, comment="涨跌幅")
    
    # 时间戳
    trading_date = Column(DateTime, nullable=False, comment="交易日期")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, comment="数据时间戳")

    # 索引
    __table_args__ = (
        Index('idx_market_data_symbol_time', 'symbol_code', 'timestamp'),
        Index('idx_market_data_trading_date', 'trading_date'),
    )

    @hybrid_property
    def spread(self):
        """买卖价差"""
        if self.ask_price and self.bid_price:
            return self.ask_price - self.bid_price
        return None

    def __repr__(self):
        return f"<MarketData(symbol={self.symbol_code}, price={self.last_price}, time={self.timestamp})>"


class KLineData(Base):
    """K线数据"""
    __tablename__ = "kline_data"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    kline_type = Column(SQLEnum(KLineType), nullable=False, comment="K线类型")
    
    # OHLCV数据
    open_price = Column(Numeric(12, 4), nullable=False, comment="开盘价")
    high_price = Column(Numeric(12, 4), nullable=False, comment="最高价")
    low_price = Column(Numeric(12, 4), nullable=False, comment="最低价")
    close_price = Column(Numeric(12, 4), nullable=False, comment="收盘价")
    volume = Column(Integer, default=0, comment="成交量")
    turnover = Column(Numeric(20, 2), default=0, comment="成交额")
    
    # 统计数据
    change = Column(Numeric(12, 4), nullable=True, comment="涨跌额")
    change_percent = Column(Numeric(8, 4), nullable=True, comment="涨跌幅")
    amplitude = Column(Numeric(8, 4), nullable=True, comment="振幅")
    
    # 技术指标（可选预计算）
    ma5 = Column(Numeric(12, 4), nullable=True, comment="5日均线")
    ma10 = Column(Numeric(12, 4), nullable=True, comment="10日均线")
    ma20 = Column(Numeric(12, 4), nullable=True, comment="20日均线")
    
    # 时间信息
    trading_date = Column(DateTime, nullable=False, comment="交易日期")
    period_start = Column(DateTime, nullable=False, comment="周期开始时间")
    period_end = Column(DateTime, nullable=False, comment="周期结束时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 索引
    __table_args__ = (
        Index('idx_kline_symbol_type_date', 'symbol_code', 'kline_type', 'trading_date'),
        Index('idx_kline_period_start', 'period_start'),
    )

    @hybrid_property
    def is_up(self):
        """是否上涨"""
        return self.close_price > self.open_price

    @hybrid_property
    def body_size(self):
        """实体大小"""
        return abs(self.close_price - self.open_price)

    @hybrid_property
    def upper_shadow(self):
        """上影线长度"""
        return self.high_price - max(self.open_price, self.close_price)

    @hybrid_property
    def lower_shadow(self):
        """下影线长度"""
        return min(self.open_price, self.close_price) - self.low_price

    def __repr__(self):
        return f"<KLineData(symbol={self.symbol_code}, type={self.kline_type}, date={self.trading_date})>"


class DepthData(Base):
    """深度数据（买卖盘口）"""
    __tablename__ = "depth_data"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    
    # 买盘数据（最多10档）
    bid_prices = Column(Text, nullable=True, comment="买盘价格JSON")
    bid_volumes = Column(Text, nullable=True, comment="买盘数量JSON")
    
    # 卖盘数据（最多10档）
    ask_prices = Column(Text, nullable=True, comment="卖盘价格JSON")
    ask_volumes = Column(Text, nullable=True, comment="卖盘数量JSON")
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, comment="数据时间戳")

    # 索引
    __table_args__ = (
        Index('idx_depth_symbol_time', 'symbol_code', 'timestamp'),
    )

    def __repr__(self):
        return f"<DepthData(symbol={self.symbol_code}, time={self.timestamp})>"


class TradeTick(Base):
    """逐笔成交数据"""
    __tablename__ = "trade_ticks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    
    # 成交数据
    price = Column(Numeric(12, 4), nullable=False, comment="成交价格")
    volume = Column(Integer, nullable=False, comment="成交数量")
    turnover = Column(Numeric(20, 2), nullable=False, comment="成交金额")
    
    # 买卖方向
    direction = Column(String(1), nullable=True, comment="买卖方向 B/S/N")
    
    # 时间戳
    trade_time = Column(DateTime, nullable=False, comment="成交时间")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, comment="数据时间戳")

    # 索引
    __table_args__ = (
        Index('idx_tick_symbol_time', 'symbol_code', 'trade_time'),
    )

    def __repr__(self):
        return f"<TradeTick(symbol={self.symbol_code}, price={self.price}, volume={self.volume})>"


# 注意：旧的Contract、Tick、Bar模型已被移除
# 现在使用更现代化的Symbol、MarketData、KLineData、DepthData、TradeTick模型
# 这些模型提供了更完善的功能和更好的数据结构