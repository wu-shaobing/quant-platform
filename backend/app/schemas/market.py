"""
市场数据模式

定义市场行情相关的 Pydantic 模型，参考 vn.py 的数据结构设计
包括行情数据、K线数据、盘口数据等专业金融数据模型
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum


class Exchange(str, Enum):
    """交易所枚举"""
    SHFE = "SHFE"      # 上海期货交易所
    DCE = "DCE"        # 大连商品交易所
    CZCE = "CZCE"      # 郑州商品交易所
    INE = "INE"        # 上海国际能源交易中心
    CFFEX = "CFFEX"    # 中国金融期货交易所
    SSE = "SSE"        # 上海证券交易所
    SZSE = "SZSE"      # 深圳证券交易所
    BSE = "BSE"        # 北京证券交易所


class ProductClass(str, Enum):
    """产品类型枚举"""
    EQUITY = "equity"           # 股票
    FUTURES = "futures"         # 期货
    OPTIONS = "options"         # 期权
    INDEX = "index"            # 指数
    FOREX = "forex"            # 外汇
    CRYPTO = "crypto"          # 数字货币
    BOND = "bond"              # 债券
    FUND = "fund"              # 基金


class Interval(str, Enum):
    """K线周期枚举"""
    TICK = "tick"
    MINUTE = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


# 基础合约信息
class ContractData(BaseModel):
    """合约数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    name: str = Field(..., description="合约名称")
    product_class: ProductClass = Field(..., description="产品类型")
    size: float = Field(..., description="合约乘数")
    price_tick: float = Field(..., description="最小变动价位")
    min_volume: float = Field(1.0, description="最小交易量")
    max_volume: Optional[float] = Field(None, description="最大交易量")
    margin_rate: Optional[float] = Field(None, description="保证金比例")
    commission_rate: Optional[float] = Field(None, description="手续费率")
    is_active: bool = Field(True, description="是否活跃")
    
    class Config:
        from_attributes = True


# 实时行情数据
class TickData(BaseModel):
    """Tick行情数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    timestamp: datetime = Field(..., description="时间戳")
    
    # 价格信息
    last_price: Optional[float] = Field(None, description="最新价")
    open_price: Optional[float] = Field(None, description="开盘价")
    high_price: Optional[float] = Field(None, description="最高价")
    low_price: Optional[float] = Field(None, description="最低价")
    pre_close: Optional[float] = Field(None, description="前收盘价")
    
    # 成交信息
    volume: Optional[float] = Field(None, description="成交量")
    turnover: Optional[float] = Field(None, description="成交额")
    open_interest: Optional[float] = Field(None, description="持仓量")
    
    # 买卖盘信息 (5档)
    bid_price_1: Optional[float] = Field(None, description="买一价")
    bid_volume_1: Optional[float] = Field(None, description="买一量")
    bid_price_2: Optional[float] = Field(None, description="买二价")
    bid_volume_2: Optional[float] = Field(None, description="买二量")
    bid_price_3: Optional[float] = Field(None, description="买三价")
    bid_volume_3: Optional[float] = Field(None, description="买三量")
    bid_price_4: Optional[float] = Field(None, description="买四价")
    bid_volume_4: Optional[float] = Field(None, description="买四量")
    bid_price_5: Optional[float] = Field(None, description="买五价")
    bid_volume_5: Optional[float] = Field(None, description="买五量")
    
    ask_price_1: Optional[float] = Field(None, description="卖一价")
    ask_volume_1: Optional[float] = Field(None, description="卖一量")
    ask_price_2: Optional[float] = Field(None, description="卖二价")
    ask_volume_2: Optional[float] = Field(None, description="卖二量")
    ask_price_3: Optional[float] = Field(None, description="卖三价")
    ask_volume_3: Optional[float] = Field(None, description="卖三量")
    ask_price_4: Optional[float] = Field(None, description="卖四价")
    ask_volume_4: Optional[float] = Field(None, description="卖四量")
    ask_price_5: Optional[float] = Field(None, description="卖五价")
    ask_volume_5: Optional[float] = Field(None, description="卖五量")
    
    class Config:
        from_attributes = True


# K线数据
class BarData(BaseModel):
    """K线数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    timestamp: datetime = Field(..., description="时间戳")
    interval: Interval = Field(..., description="K线周期")
    
    # OHLCV数据
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    turnover: Optional[float] = Field(None, description="成交额")
    open_interest: Optional[float] = Field(None, description="持仓量")
    
    class Config:
        from_attributes = True


# 盘口数据
class DepthData(BaseModel):
    """盘口深度数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    timestamp: datetime = Field(..., description="时间戳")
    
    bids: List[List[float]] = Field(..., description="买盘 [[价格, 数量], ...]")
    asks: List[List[float]] = Field(..., description="卖盘 [[价格, 数量], ...]")
    
    @validator('bids', 'asks')
    def validate_depth(cls, v):
        for item in v:
            if len(item) != 2:
                raise ValueError('盘口数据格式错误，应为 [价格, 数量]')
            if item[0] <= 0 or item[1] <= 0:
                raise ValueError('价格和数量必须大于0')
        return v


# 市场统计数据
class MarketStatsData(BaseModel):
    """市场统计数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    trade_date: date = Field(..., description="交易日期")
    
    # 价格统计
    open_price: Optional[float] = Field(None, description="开盘价")
    high_price: Optional[float] = Field(None, description="最高价")
    low_price: Optional[float] = Field(None, description="最低价")
    close_price: Optional[float] = Field(None, description="收盘价")
    pre_close: Optional[float] = Field(None, description="前收盘价")
    
    # 成交统计
    volume: Optional[float] = Field(None, description="成交量")
    turnover: Optional[float] = Field(None, description="成交额")
    open_interest: Optional[float] = Field(None, description="持仓量")
    
    # 涨跌统计
    change: Optional[float] = Field(None, description="涨跌额")
    pct_change: Optional[float] = Field(None, description="涨跌幅")
    
    # 振幅和换手
    amplitude: Optional[float] = Field(None, description="振幅")
    turnover_rate: Optional[float] = Field(None, description="换手率")


# 行情订阅请求
class SubscribeRequest(BaseModel):
    """行情订阅请求模型"""
    symbols: List[str] = Field(..., description="合约代码列表")
    data_types: List[str] = Field(["tick"], description="数据类型列表")
    
    @validator('data_types')
    def validate_data_types(cls, v):
        valid_types = ["tick", "depth", "kline"]
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f'无效的数据类型: {data_type}')
        return v


# 行情查询请求
class MarketDataRequest(BaseModel):
    """行情数据请求模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Optional[Exchange] = Field(None, description="交易所")
    interval: Optional[Interval] = Field(Interval.DAILY, description="K线周期")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    limit: Optional[int] = Field(1000, ge=1, le=10000, description="数据条数限制")


# 市场搜索请求
class MarketSearchRequest(BaseModel):
    """市场搜索请求模型"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    exchange: Optional[Exchange] = Field(None, description="交易所筛选")
    product_class: Optional[ProductClass] = Field(None, description="产品类型筛选")
    is_active: Optional[bool] = Field(True, description="是否只显示活跃合约")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


# 响应模型
class TickDataResponse(BaseModel):
    """Tick数据响应模型"""
    data: List[TickData]
    total: int
    symbol: str
    exchange: str


class BarDataResponse(BaseModel):
    """K线数据响应模型"""
    data: List[BarData]
    total: int
    symbol: str
    exchange: str
    interval: str


class ContractListResponse(BaseModel):
    """合约列表响应模型"""
    contracts: List[ContractData]
    total: int
    page: int
    page_size: int
    total_pages: int


class MarketOverviewResponse(BaseModel):
    """市场概览响应模型"""
    total_contracts: int
    active_contracts: int
    total_volume: float
    total_turnover: float
    top_gainers: List[Dict[str, Any]]
    top_losers: List[Dict[str, Any]]
    most_active: List[Dict[str, Any]]


# WebSocket消息模型
class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class MarketDataMessage(WebSocketMessage):
    """行情数据WebSocket消息"""
    type: str = "market_data"
    data: Union[TickData, BarData, DepthData]


class SubscriptionMessage(WebSocketMessage):
    """订阅消息"""
    type: str = "subscription"
    action: str = Field(..., description="订阅动作: subscribe/unsubscribe")
    symbols: List[str] = Field(..., description="合约代码列表")
    data_types: List[str] = Field(["tick"], description="数据类型列表")