"""
交易数据模式

定义交易相关的 Pydantic 模型，参考 vn.py 的交易数据结构设计
包括订单、成交、持仓、账户等专业交易数据模型
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .market import Exchange


class Direction(str, Enum):
    """交易方向枚举"""
    LONG = "long"       # 买入/做多
    SHORT = "short"     # 卖出/做空


class Offset(str, Enum):
    """开平仓枚举"""
    OPEN = "open"           # 开仓
    CLOSE = "close"         # 平仓
    CLOSE_TODAY = "close_today"     # 平今
    CLOSE_YESTERDAY = "close_yesterday"  # 平昨


class OrderType(str, Enum):
    """订单类型枚举"""
    LIMIT = "limit"         # 限价单
    MARKET = "market"       # 市价单
    STOP = "stop"           # 停损单
    FAK = "fak"             # 即时成交剩余撤销
    FOK = "fok"             # 全部成交或撤销


class OrderStatus(str, Enum):
    """订单状态枚举"""
    SUBMITTING = "submitting"   # 提交中
    SUBMITTED = "submitted"     # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    ALL_FILLED = "all_filled"   # 全部成交
    CANCELLED = "cancelled"     # 已撤销
    REJECTED = "rejected"       # 已拒绝


class PositionDirection(str, Enum):
    """持仓方向枚举"""
    NET = "net"     # 净持仓
    LONG = "long"   # 多头持仓
    SHORT = "short" # 空头持仓


# 订单数据模型
class OrderData(BaseModel):
    """订单数据模型"""
    order_id: str = Field(..., description="订单号")
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    direction: Direction = Field(..., description="交易方向")
    offset: Offset = Field(..., description="开平仓")
    order_type: OrderType = Field(..., description="订单类型")
    volume: float = Field(..., gt=0, description="委托数量")
    price: Optional[float] = Field(None, description="委托价格")
    status: OrderStatus = Field(..., description="订单状态")
    traded: float = Field(0, ge=0, description="成交数量")
    order_time: datetime = Field(..., description="委托时间")
    
    class Config:
        from_attributes = True


# 成交数据模型
class TradeData(BaseModel):
    """成交数据模型"""
    trade_id: str = Field(..., description="成交号")
    order_id: str = Field(..., description="订单号")
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    direction: Direction = Field(..., description="交易方向")
    offset: Offset = Field(..., description="开平仓")
    volume: float = Field(..., gt=0, description="成交数量")
    price: float = Field(..., gt=0, description="成交价格")
    trade_time: datetime = Field(..., description="成交时间")
    commission: Optional[float] = Field(None, description="手续费")
    
    class Config:
        from_attributes = True


# 持仓数据模型
class PositionData(BaseModel):
    """持仓数据模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    direction: PositionDirection = Field(..., description="持仓方向")
    volume: float = Field(..., description="持仓数量")
    frozen: float = Field(0, ge=0, description="冻结数量")
    price: float = Field(..., description="持仓均价")
    pnl: float = Field(0, description="持仓盈亏")
    yd_volume: float = Field(0, ge=0, description="昨仓数量")
    
    class Config:
        from_attributes = True


# 账户数据模型
class AccountData(BaseModel):
    """账户数据模型"""
    account_id: str = Field(..., description="账户号")
    balance: float = Field(..., description="账户余额")
    frozen: float = Field(0, ge=0, description="冻结资金")
    available: float = Field(..., description="可用资金")
    margin: float = Field(0, ge=0, description="保证金占用")
    close_profit: float = Field(0, description="平仓盈亏")
    holding_profit: float = Field(0, description="持仓盈亏")
    trading_day: str = Field(..., description="交易日")
    
    class Config:
        from_attributes = True


# 订单请求模型
class OrderRequest(BaseModel):
    """订单请求模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    direction: Direction = Field(..., description="交易方向")
    offset: Offset = Field(..., description="开平仓")
    order_type: OrderType = Field(OrderType.LIMIT, description="订单类型")
    volume: float = Field(..., gt=0, description="委托数量")
    price: Optional[float] = Field(None, description="委托价格")
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') == OrderType.LIMIT and v is None:
            raise ValueError('限价单必须指定价格')
        if v is not None and v <= 0:
            raise ValueError('价格必须大于0')
        return v


# 撤单请求模型
class CancelRequest(BaseModel):
    """撤单请求模型"""
    order_id: str = Field(..., description="订单号")
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")


# 订单修改请求模型
class ModifyRequest(BaseModel):
    """订单修改请求模型"""
    order_id: str = Field(..., description="订单号")
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    volume: Optional[float] = Field(None, gt=0, description="新的委托数量")
    price: Optional[float] = Field(None, gt=0, description="新的委托价格")


# 批量订单请求模型
class BatchOrderRequest(BaseModel):
    """批量订单请求模型"""
    orders: List[OrderRequest] = Field(..., max_items=100, description="订单列表")
    
    @validator('orders')
    def validate_orders(cls, v):
        if len(v) == 0:
            raise ValueError('订单列表不能为空')
        return v


# 条件订单模型
class ConditionalOrderRequest(BaseModel):
    """条件订单请求模型"""
    symbol: str = Field(..., description="合约代码")
    exchange: Exchange = Field(..., description="交易所")
    direction: Direction = Field(..., description="交易方向")
    offset: Offset = Field(..., description="开平仓")
    volume: float = Field(..., gt=0, description="委托数量")
    
    # 触发条件
    trigger_price: float = Field(..., gt=0, description="触发价格")
    trigger_direction: str = Field(..., description="触发方向: GTE/LTE")
    
    # 执行参数
    order_type: OrderType = Field(OrderType.LIMIT, description="订单类型")
    order_price: Optional[float] = Field(None, description="委托价格")
    
    @validator('trigger_direction')
    def validate_trigger_direction(cls, v):
        if v not in ['GTE', 'LTE']:
            raise ValueError('触发方向必须是 GTE 或 LTE')
        return v


# 查询请求模型
class OrderQueryRequest(BaseModel):
    """订单查询请求模型"""
    symbol: Optional[str] = Field(None, description="合约代码")
    exchange: Optional[Exchange] = Field(None, description="交易所")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class TradeQueryRequest(BaseModel):
    """成交查询请求模型"""
    symbol: Optional[str] = Field(None, description="合约代码")
    exchange: Optional[Exchange] = Field(None, description="交易所")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class PositionQueryRequest(BaseModel):
    """持仓查询请求模型"""
    symbol: Optional[str] = Field(None, description="合约代码")
    exchange: Optional[Exchange] = Field(None, description="交易所")
    direction: Optional[PositionDirection] = Field(None, description="持仓方向")


# 响应模型
class OrderResponse(BaseModel):
    """订单响应模型"""
    success: bool
    order_id: Optional[str] = None
    message: str
    data: Optional[OrderData] = None


class BatchOrderResponse(BaseModel):
    """批量订单响应模型"""
    success: bool
    total: int
    success_count: int
    failed_count: int
    results: List[OrderResponse]


class OrderListResponse(BaseModel):
    """订单列表响应模型"""
    orders: List[OrderData]
    total: int
    page: int
    page_size: int
    total_pages: int


class TradeListResponse(BaseModel):
    """成交列表响应模型"""
    trades: List[TradeData]
    total: int
    page: int
    page_size: int
    total_pages: int


class PositionListResponse(BaseModel):
    """持仓列表响应模型"""
    positions: List[PositionData]
    total: int
    total_pnl: float
    total_margin: float


class AccountResponse(BaseModel):
    """账户响应模型"""
    account: AccountData
    positions: List[PositionData]
    summary: Dict[str, Any]


# 交易统计模型
class TradingStatsResponse(BaseModel):
    """交易统计响应模型"""
    total_orders: int
    total_trades: int
    total_volume: float
    total_turnover: float
    win_rate: float
    profit_loss_ratio: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    daily_stats: List[Dict[str, Any]]


# 风控相关模型
class RiskLimitData(BaseModel):
    """风控限制数据模型"""
    max_position: Optional[float] = Field(None, description="最大持仓")
    max_order_size: Optional[float] = Field(None, description="最大单笔委托")
    max_daily_loss: Optional[float] = Field(None, description="最大日亏损")
    max_total_loss: Optional[float] = Field(None, description="最大总亏损")
    allowed_symbols: Optional[List[str]] = Field(None, description="允许交易的合约")
    forbidden_symbols: Optional[List[str]] = Field(None, description="禁止交易的合约")


class RiskCheckResult(BaseModel):
    """风控检查结果模型"""
    passed: bool
    message: str
    details: Dict[str, Any] = {}


# WebSocket交易消息模型
class TradingMessage(BaseModel):
    """交易WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class OrderUpdateMessage(TradingMessage):
    """订单更新消息"""
    type: str = "order_update"
    data: OrderData


class TradeUpdateMessage(TradingMessage):
    """成交更新消息"""
    type: str = "trade_update"
    data: TradeData


class PositionUpdateMessage(TradingMessage):
    """持仓更新消息"""
    type: str = "position_update"
    data: PositionData


class AccountUpdateMessage(TradingMessage):
    """账户更新消息"""
    type: str = "account_update"
    data: AccountData


# 通用WebSocket消息模型（别名）
WebSocketMessage = TradingMessage