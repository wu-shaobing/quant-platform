"""
回测数据模式

定义回测相关的 Pydantic 模型，参考 Qlib 和 Lean 的回测数据结构设计
包括回测配置、回测结果、性能分析等模型
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class BacktestStatus(str, Enum):
    """回测状态枚举"""
    PENDING = "pending"         # 等待中
    RUNNING = "running"         # 运行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"     # 已取消


class RebalanceFrequency(str, Enum):
    """调仓频率枚举"""
    DAILY = "daily"            # 每日
    WEEKLY = "weekly"          # 每周
    MONTHLY = "monthly"        # 每月
    QUARTERLY = "quarterly"    # 每季度
    YEARLY = "yearly"          # 每年


class BenchmarkType(str, Enum):
    """基准类型枚举"""
    INDEX = "index"            # 指数基准
    SYMBOL = "symbol"          # 单一标的基准
    CUSTOM = "custom"          # 自定义基准


# 回测配置基础模型
class BacktestConfigBase(BaseModel):
    """回测配置基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="回测名称")
    description: Optional[str] = Field(None, max_length=500, description="回测描述")
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    initial_capital: float = Field(1000000, gt=0, description="初始资金")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v


# 回测创建请求模型
class BacktestCreate(BacktestConfigBase):
    """回测创建请求模型"""
    strategy_id: int = Field(..., description="策略ID")
    symbols: List[str] = Field(..., min_items=1, description="交易标的列表")
    benchmark: Optional[str] = Field(None, description="基准标的")
    
    # 交易成本设置
    commission_rate: float = Field(0.0003, ge=0, le=0.01, description="手续费率")
    slippage_rate: float = Field(0.0001, ge=0, le=0.01, description="滑点率")
    min_commission: float = Field(5.0, ge=0, description="最小手续费")
    
    # 回测参数
    rebalance_frequency: RebalanceFrequency = Field(RebalanceFrequency.DAILY, description="调仓频率")
    max_position_size: Optional[float] = Field(None, ge=0, le=1, description="最大持仓比例")
    max_leverage: float = Field(1.0, ge=0.1, le=10, description="最大杠杆")
    
    # 风控设置
    stop_loss: Optional[float] = Field(None, ge=0, le=1, description="止损比例")
    take_profit: Optional[float] = Field(None, ge=0, description="止盈比例")
    max_drawdown_limit: Optional[float] = Field(None, ge=0, le=1, description="最大回撤限制")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('至少需要指定一个交易标的')
        return v


# 回测更新模型
class BacktestUpdate(BaseModel):
    """回测更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[BacktestStatus] = None


# 回测响应模型
class BacktestResponse(BacktestConfigBase):
    """回测响应模型"""
    id: int
    strategy_id: int
    user_id: int
    status: BacktestStatus
    symbols: List[str]
    benchmark: Optional[str] = None
    
    # 交易成本设置
    commission_rate: float
    slippage_rate: float
    min_commission: float
    
    # 回测参数
    rebalance_frequency: RebalanceFrequency
    max_position_size: Optional[float] = None
    max_leverage: float
    
    # 风控设置
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_drawdown_limit: Optional[float] = None
    
    # 时间信息
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 进度信息
    progress: float = 0.0
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


# 回测结果模型
class BacktestResult(BaseModel):
    """回测结果模型"""
    backtest_id: int = Field(..., description="回测ID")
    
    # 基础统计
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    benchmark_return: Optional[float] = Field(None, description="基准收益率")
    alpha: Optional[float] = Field(None, description="超额收益")
    beta: Optional[float] = Field(None, description="贝塔值")
    
    # 风险指标
    volatility: float = Field(..., description="收益波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[float] = Field(None, description="卡玛比率")
    information_ratio: Optional[float] = Field(None, description="信息比率")
    
    # 交易统计
    total_trades: int = Field(..., description="总交易次数")
    win_trades: int = Field(..., description="盈利交易次数")
    lose_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率")
    profit_loss_ratio: float = Field(..., description="盈亏比")
    avg_win: float = Field(..., description="平均盈利")
    avg_loss: float = Field(..., description="平均亏损")
    
    # 持仓统计
    avg_position_hold_days: float = Field(..., description="平均持仓天数")
    max_position_hold_days: int = Field(..., description="最长持仓天数")
    turnover_rate: float = Field(..., description="换手率")
    
    # 成本统计
    total_commission: float = Field(..., description="总手续费")
    total_slippage: float = Field(..., description="总滑点成本")
    
    class Config:
        from_attributes = True


# 回测详情响应模型
class BacktestDetailResponse(BacktestResponse):
    """回测详情响应模型"""
    result: Optional[BacktestResult] = None
    daily_returns: List[Dict[str, Any]] = []
    positions: List[Dict[str, Any]] = []
    trades: List[Dict[str, Any]] = []
    drawdown_periods: List[Dict[str, Any]] = []


# 回测列表响应模型
class BacktestListResponse(BaseModel):
    """回测列表响应模型"""
    backtests: List[BacktestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# 回测查询请求模型
class BacktestQueryRequest(BaseModel):
    """回测查询请求模型"""
    strategy_id: Optional[int] = Field(None, description="策略ID")
    status: Optional[BacktestStatus] = Field(None, description="回测状态")
    start_date_after: Optional[date] = Field(None, description="开始日期之后")
    start_date_before: Optional[date] = Field(None, description="开始日期之前")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


# 回测日收益数据模型
class DailyReturnData(BaseModel):
    """回测日收益数据模型"""
    record_date: date = Field(..., description="日期")
    portfolio_value: float = Field(..., description="组合价值")
    daily_return: float = Field(..., description="日收益率")
    cumulative_return: float = Field(..., description="累计收益率")
    benchmark_return: Optional[float] = Field(None, description="基准日收益率")
    benchmark_cumulative: Optional[float] = Field(None, description="基准累计收益率")
    drawdown: float = Field(..., description="回撤")
    positions_count: int = Field(..., description="持仓数量")
    
    class Config:
        from_attributes = True


# 回测持仓数据模型
class BacktestPositionData(BaseModel):
    """回测持仓数据模型"""
    record_date: date = Field(..., description="日期")
    symbol: str = Field(..., description="合约代码")
    volume: float = Field(..., description="持仓数量")
    price: float = Field(..., description="持仓价格")
    pnl: float = Field(..., description="持仓盈亏")
    
    class Config:
        from_attributes = True


# 回测交易数据模型
class BacktestTradeData(BaseModel):
    """回测交易数据模型"""
    trade_date: date = Field(..., description="交易日期")
    symbol: str = Field(..., description="标的代码")
    side: str = Field(..., description="交易方向")
    quantity: float = Field(..., description="交易数量")
    price: float = Field(..., description="交易价格")
    amount: float = Field(..., description="交易金额")
    commission: float = Field(..., description="手续费")
    slippage: float = Field(..., description="滑点成本")
    
    class Config:
        from_attributes = True


# 回测分析请求模型
class BacktestAnalysisRequest(BaseModel):
    """回测分析请求模型"""
    backtest_ids: List[int] = Field(..., min_items=1, max_items=10, description="回测ID列表")
    analysis_type: str = Field(..., description="分析类型")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        valid_types = ['comparison', 'correlation', 'attribution', 'risk_analysis']
        if v not in valid_types:
            raise ValueError(f'无效的分析类型: {v}')
        return v


# 回测比较结果模型
class BacktestComparisonResult(BaseModel):
    """回测比较结果模型"""
    backtest_summaries: List[Dict[str, Any]] = Field(..., description="回测摘要列表")
    comparison_metrics: Dict[str, List[float]] = Field(..., description="对比指标")
    correlation_matrix: List[List[float]] = Field(..., description="相关性矩阵")
    risk_return_chart: Dict[str, Any] = Field(..., description="风险收益图数据")


# 回测优化配置模型
class BacktestOptimizationConfig(BaseModel):
    """回测优化配置模型"""
    strategy_id: int = Field(..., description="策略ID")
    parameter_ranges: Dict[str, Dict[str, Any]] = Field(..., description="参数范围")
    optimization_target: str = Field("sharpe_ratio", description="优化目标")
    optimization_method: str = Field("grid_search", description="优化方法")
    max_iterations: int = Field(100, ge=1, le=1000, description="最大迭代次数")
    
    # 回测基础配置
    start_date: date = Field(..., description="回测开始日期")
    end_date: date = Field(..., description="回测结束日期")
    initial_capital: float = Field(1000000, gt=0, description="初始资金")
    symbols: List[str] = Field(..., min_items=1, description="交易标的列表")
    
    @validator('optimization_method')
    def validate_optimization_method(cls, v):
        valid_methods = ['grid_search', 'random_search', 'bayesian', 'genetic']
        if v not in valid_methods:
            raise ValueError(f'无效的优化方法: {v}')
        return v


# 回测优化结果模型
class BacktestOptimizationResult(BaseModel):
    """回测优化结果模型"""
    optimization_id: int = Field(..., description="优化ID")
    best_parameters: Dict[str, Any] = Field(..., description="最优参数")
    best_score: float = Field(..., description="最优得分")
    all_results: List[Dict[str, Any]] = Field(..., description="所有结果")
    parameter_importance: Dict[str, float] = Field(..., description="参数重要性")
    optimization_history: List[Dict[str, Any]] = Field(..., description="优化历史")


# 回测报告模型
class BacktestReport(BaseModel):
    """回测报告模型"""
    backtest_id: int = Field(..., description="回测ID")
    report_type: str = Field(..., description="报告类型")
    
    # 执行摘要
    executive_summary: Dict[str, Any] = Field(..., description="执行摘要")
    
    # 详细分析
    performance_analysis: Dict[str, Any] = Field(..., description="绩效分析")
    risk_analysis: Dict[str, Any] = Field(..., description="风险分析")
    trade_analysis: Dict[str, Any] = Field(..., description="交易分析")
    
    # 图表数据
    charts: Dict[str, Any] = Field(..., description="图表数据")
    
    # 生成信息
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    generated_by: int = Field(..., description="生成者ID")


# 回测统计响应模型
class BacktestStatsResponse(BaseModel):
    """回测统计响应模型"""
    total_backtests: int
    completed_backtests: int
    running_backtests: int
    failed_backtests: int
    avg_return: float
    avg_sharpe_ratio: float
    best_performers: List[Dict[str, Any]]
    recent_backtests: List[Dict[str, Any]]


# WebSocket回测消息模型
class BacktestMessage(BaseModel):
    """回测WebSocket消息模型"""
    type: str = Field(..., description="消息类型")
    backtest_id: int = Field(..., description="回测ID")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class BacktestProgressMessage(BacktestMessage):
    """回测进度消息"""
    type: str = "backtest_progress"
    progress: float = Field(..., ge=0, le=1, description="进度百分比")
    status: BacktestStatus = Field(..., description="当前状态")


class BacktestCompleteMessage(BacktestMessage):
    """回测完成消息"""
    type: str = "backtest_complete"
    result: BacktestResult = Field(..., description="回测结果")


class BacktestErrorMessage(BacktestMessage):
    """回测错误消息"""
    type: str = "backtest_error"
    error: str = Field(..., description="错误信息")