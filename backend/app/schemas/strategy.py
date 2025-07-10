"""
策略数据模式

定义策略相关的 Pydantic 模型，参考 Qlib 的策略数据结构设计
包括策略定义、策略参数、策略运行状态等模型
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class StrategyType(str, Enum):
    """策略类型枚举"""
    CTA = "cta"                 # CTA策略
    ARBITRAGE = "arbitrage"     # 套利策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    MOMENTUM = "momentum"       # 动量策略
    PAIRS_TRADING = "pairs_trading"    # 配对交易
    MARKET_MAKING = "market_making"    # 做市策略
    ALPHA = "alpha"            # Alpha策略
    CUSTOM = "custom"          # 自定义策略


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    INACTIVE = "inactive"       # 未激活
    ACTIVE = "active"          # 运行中
    PAUSED = "paused"          # 已暂停
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 错误状态


class FrequencyType(str, Enum):
    """运行频率枚举"""
    TICK = "tick"              # 逐笔
    MINUTE = "minute"          # 分钟级
    HOUR = "hour"              # 小时级
    DAILY = "daily"            # 日级
    WEEKLY = "weekly"          # 周级


class SignalType(str, Enum):
    """信号类型枚举"""
    BUY = "buy"                # 买入信号
    SELL = "sell"              # 卖出信号
    HOLD = "hold"              # 持有信号
    CLOSE = "close"            # 平仓信号


# 策略基础模型
class StrategyBase(BaseModel):
    """策略基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, max_length=500, description="策略描述")
    strategy_type: StrategyType = Field(..., description="策略类型")
    frequency: FrequencyType = Field(..., description="运行频率")
    symbols: List[str] = Field(..., min_items=1, description="交易标的列表")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('至少需要指定一个交易标的')
        return v


# 策略创建模型
class StrategyCreate(StrategyBase):
    """策略创建模型"""
    code: str = Field(..., description="策略代码")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    risk_limits: Dict[str, float] = Field(default_factory=dict, description="风控限制")
    
    @validator('code')
    def validate_code(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('策略代码不能为空')
        return v


# 策略更新模型
class StrategyUpdate(BaseModel):
    """策略更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    code: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    risk_limits: Optional[Dict[str, float]] = None
    symbols: Optional[List[str]] = None
    status: Optional[StrategyStatus] = None


# 策略响应模型
class StrategyResponse(StrategyBase):
    """策略响应模型"""
    id: int
    user_id: int
    status: StrategyStatus
    parameters: Dict[str, Any]
    risk_limits: Dict[str, float]
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # 运行统计
    total_runs: int = 0
    success_runs: int = 0
    error_runs: int = 0
    
    class Config:
        from_attributes = True


# 策略详情响应模型
class StrategyDetailResponse(StrategyResponse):
    """策略详情响应模型"""
    code: str
    performance_metrics: Dict[str, Any] = {}
    recent_signals: List[Dict[str, Any]] = []
    recent_trades: List[Dict[str, Any]] = []


# 策略列表响应模型
class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    strategies: List[StrategyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# 策略参数模型
class StrategyParameter(BaseModel):
    """策略参数模型"""
    name: str = Field(..., description="参数名称")
    value: Union[int, float, str, bool] = Field(..., description="参数值")
    param_type: str = Field(..., description="参数类型")
    description: Optional[str] = Field(None, description="参数描述")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    options: Optional[List[str]] = Field(None, description="可选值列表")


# 策略信号模型
class StrategySignal(BaseModel):
    """策略信号模型"""
    strategy_id: int = Field(..., description="策略ID")
    symbol: str = Field(..., description="交易标的")
    signal_type: SignalType = Field(..., description="信号类型")
    strength: float = Field(..., ge=0, le=1, description="信号强度")
    price: Optional[float] = Field(None, description="信号价格")
    volume: Optional[float] = Field(None, description="建议数量")
    timestamp: datetime = Field(..., description="信号时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="信号元数据")
    
    class Config:
        from_attributes = True


# 策略运行日志模型
class StrategyLog(BaseModel):
    """策略运行日志模型"""
    strategy_id: int = Field(..., description="策略ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    timestamp: datetime = Field(..., description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="日志元数据")
    
    class Config:
        from_attributes = True


# 策略性能指标模型
class StrategyPerformance(BaseModel):
    """策略性能指标模型"""
    strategy_id: int = Field(..., description="策略ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    
    # 收益指标
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[float] = Field(None, description="卡玛比率")
    
    # 交易指标
    total_trades: int = Field(..., description="总交易次数")
    win_trades: int = Field(..., description="盈利交易次数")
    lose_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率")
    profit_loss_ratio: float = Field(..., description="盈亏比")
    
    # 风险指标
    volatility: float = Field(..., description="波动率")
    var_95: Optional[float] = Field(None, description="95% VaR")
    var_99: Optional[float] = Field(None, description="99% VaR")
    
    class Config:
        from_attributes = True


# 策略查询请求模型
class StrategyQueryRequest(BaseModel):
    """策略查询请求模型"""
    strategy_type: Optional[StrategyType] = Field(None, description="策略类型")
    status: Optional[StrategyStatus] = Field(None, description="策略状态")
    frequency: Optional[FrequencyType] = Field(None, description="运行频率")
    symbol: Optional[str] = Field(None, description="交易标的")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


# 策略控制请求模型
class StrategyControlRequest(BaseModel):
    """策略控制请求模型"""
    action: str = Field(..., description="控制动作: start/stop/pause/resume")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['start', 'stop', 'pause', 'resume']
        if v not in valid_actions:
            raise ValueError(f'无效的控制动作: {v}')
        return v


# 策略回测请求模型
class BacktestRequest(BaseModel):
    """策略回测请求模型"""
    strategy_id: int = Field(..., description="策略ID")
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    initial_capital: float = Field(1000000, gt=0, description="初始资金")
    benchmark: Optional[str] = Field(None, description="基准标的")
    commission_rate: Optional[float] = Field(0.0003, description="手续费率")
    slippage_rate: Optional[float] = Field(0.0001, description="滑点率")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v


# 策略优化请求模型
class StrategyOptimizationRequest(BaseModel):
    """策略优化请求模型"""
    strategy_id: int = Field(..., description="策略ID")
    parameters: Dict[str, Dict[str, Any]] = Field(..., description="参数优化范围")
    optimization_target: str = Field("sharpe_ratio", description="优化目标")
    max_iterations: int = Field(100, ge=1, le=1000, description="最大迭代次数")
    
    @validator('parameters')
    def validate_parameters(cls, v):
        for param_name, param_config in v.items():
            if 'min' not in param_config or 'max' not in param_config:
                raise ValueError(f'参数 {param_name} 必须指定 min 和 max 值')
        return v


# 策略模板模型
class StrategyTemplate(BaseModel):
    """策略模板模型"""
    id: int
    name: str
    description: str
    strategy_type: StrategyType
    template_code: str
    default_parameters: Dict[str, Any]
    parameter_schema: List[StrategyParameter]
    tags: List[str] = []
    is_public: bool = True
    created_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 策略模板列表响应模型
class StrategyTemplateListResponse(BaseModel):
    """策略模板列表响应模型"""
    templates: List[StrategyTemplate]
    total: int
    page: int
    page_size: int
    total_pages: int


# 策略统计响应模型
class StrategyStatsResponse(BaseModel):
    """策略统计响应模型"""
    total_strategies: int
    active_strategies: int
    paused_strategies: int
    stopped_strategies: int
    error_strategies: int
    strategy_type_distribution: Dict[str, int]
    performance_summary: Dict[str, float]
    top_performers: List[Dict[str, Any]]


# WebSocket策略消息模型
class StrategyMessage(BaseModel):
    """策略WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    strategy_id: int = Field(..., description="策略ID")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class StrategySignalMessage(StrategyMessage):
    """策略信号消息"""
    type: str = "strategy_signal"
    data: StrategySignal


class StrategyStatusMessage(StrategyMessage):
    """策略状态消息"""
    type: str = "strategy_status"
    status: StrategyStatus


class StrategyLogMessage(StrategyMessage):
    """策略日志消息"""
    type: str = "strategy_log"
    data: StrategyLog