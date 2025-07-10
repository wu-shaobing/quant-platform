"""
回测模型
包含回测任务、结果、性能分析等
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, ForeignKey, Text, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.types import GUID


class BacktestStatus(str, Enum):
    """回测状态"""
    PENDING = "pending"        # 待运行
    RUNNING = "running"        # 运行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消


class BacktestType(str, Enum):
    """回测类型"""
    FULL = "full"              # 完整回测
    ROLLING = "rolling"        # 滚动回测
    WALK_FORWARD = "walk_forward"  # 步进回测
    MONTE_CARLO = "monte_carlo"    # 蒙特卡洛


class BacktestTask(Base):
    """回测任务"""
    __tablename__ = "backtest_tasks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(GUID(), ForeignKey("strategies.id"), nullable=False, index=True)
    
    # 任务基本信息
    name = Column(String(100), nullable=False, comment="回测名称")
    description = Column(Text, nullable=True, comment="回测描述")
    backtest_type = Column(SQLEnum(BacktestType), default=BacktestType.FULL, comment="回测类型")
    
    # 回测参数
    start_date = Column(DateTime, nullable=False, comment="开始日期")
    end_date = Column(DateTime, nullable=False, comment="结束日期")
    initial_capital = Column(Numeric(20, 2), nullable=False, comment="初始资金")
    symbols = Column(JSON, nullable=True, comment="回测标的列表")
    
    # 回测配置
    commission_rate = Column(Numeric(6, 4), default=0.0003, comment="手续费率")
    slippage = Column(Numeric(6, 4), default=0.001, comment="滑点")
    benchmark = Column(String(20), nullable=True, comment="基准指数")
    
    # 风险参数
    max_position_size = Column(Numeric(8, 4), default=1.0, comment="最大仓位比例")
    stop_loss = Column(Numeric(8, 4), nullable=True, comment="止损比例")
    take_profit = Column(Numeric(8, 4), nullable=True, comment="止盈比例")
    
    # 任务状态
    status = Column(SQLEnum(BacktestStatus), default=BacktestStatus.PENDING, comment="任务状态")
    progress = Column(Numeric(5, 2), default=0, comment="进度百分比")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间信息
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    duration = Column(Integer, nullable=True, comment="运行时长(秒)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="backtest_tasks")
    strategy = relationship("Strategy", backref="backtest_tasks")
    result = relationship("BacktestResult", back_populates="task", uselist=False)

    @hybrid_property
    def is_completed(self):
        """是否完成"""
        return self.status == BacktestStatus.COMPLETED

    @hybrid_property
    def is_running(self):
        """是否运行中"""
        return self.status == BacktestStatus.RUNNING

    def __repr__(self):
        return f"<BacktestTask(name={self.name}, status={self.status}, progress={self.progress}%)>"


class BacktestResult(Base):
    """回测结果"""
    __tablename__ = "backtest_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    task_id = Column(GUID(), ForeignKey("backtest_tasks.id"), nullable=False, index=True)
    strategy_id = Column(GUID(), ForeignKey("strategies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 基本统计
    total_trades = Column(Integer, default=0, comment="总交易次数")
    winning_trades = Column(Integer, default=0, comment="盈利交易次数")
    losing_trades = Column(Integer, default=0, comment="亏损交易次数")
    
    # 收益指标
    total_return = Column(Numeric(12, 4), default=0, comment="总收益率")
    annual_return = Column(Numeric(12, 4), default=0, comment="年化收益率")
    cumulative_return = Column(Numeric(12, 4), default=0, comment="累计收益率")
    
    # 风险指标
    max_drawdown = Column(Numeric(8, 4), default=0, comment="最大回撤")
    volatility = Column(Numeric(8, 4), default=0, comment="波动率")
    sharpe_ratio = Column(Numeric(8, 4), default=0, comment="夏普比率")
    sortino_ratio = Column(Numeric(8, 4), default=0, comment="索提诺比率")
    calmar_ratio = Column(Numeric(8, 4), default=0, comment="卡玛比率")
    
    # 胜率统计
    win_rate = Column(Numeric(8, 4), default=0, comment="胜率")
    profit_factor = Column(Numeric(8, 4), default=0, comment="盈利因子")
    avg_win = Column(Numeric(12, 4), default=0, comment="平均盈利")
    avg_loss = Column(Numeric(12, 4), default=0, comment="平均亏损")
    largest_win = Column(Numeric(12, 4), default=0, comment="最大盈利")
    largest_loss = Column(Numeric(12, 4), default=0, comment="最大亏损")
    
    # 基准比较
    benchmark_return = Column(Numeric(12, 4), default=0, comment="基准收益率")
    alpha = Column(Numeric(8, 4), default=0, comment="阿尔法")
    beta = Column(Numeric(8, 4), default=0, comment="贝塔")
    information_ratio = Column(Numeric(8, 4), default=0, comment="信息比率")
    
    # 资金曲线
    equity_curve = Column(JSON, nullable=True, comment="资金曲线JSON")
    drawdown_curve = Column(JSON, nullable=True, comment="回撤曲线JSON")
    
    # 详细数据
    trades_data = Column(JSON, nullable=True, comment="交易记录JSON")
    daily_returns = Column(JSON, nullable=True, comment="日收益率JSON")
    positions_data = Column(JSON, nullable=True, comment="持仓记录JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    task = relationship("BacktestTask", back_populates="result")
    strategy = relationship("Strategy", back_populates="backtests")
    user = relationship("User", backref="backtest_results")

    @hybrid_property
    def loss_rate(self):
        """亏损率"""
        return 1 - self.win_rate if self.win_rate else 0

    @hybrid_property
    def avg_trade_return(self):
        """平均交易收益"""
        if self.total_trades > 0:
            return (self.avg_win * self.winning_trades + self.avg_loss * self.losing_trades) / self.total_trades
        return 0

    @hybrid_property
    def risk_return_ratio(self):
        """风险收益比"""
        if self.volatility > 0:
            return self.annual_return / self.volatility
        return 0

    def __repr__(self):
        return f"<BacktestResult(total_return={self.total_return}, sharpe={self.sharpe_ratio})>"


class BacktestTrade(Base):
    """回测交易记录"""
    __tablename__ = "backtest_trades"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    result_id = Column(GUID(), ForeignKey("backtest_results.id"), nullable=False, index=True)
    
    # 交易信息
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    side = Column(String(10), nullable=False, comment="买卖方向")
    
    # 开仓信息
    entry_date = Column(DateTime, nullable=False, comment="开仓日期")
    entry_price = Column(Numeric(12, 4), nullable=False, comment="开仓价格")
    entry_quantity = Column(Integer, nullable=False, comment="开仓数量")
    
    # 平仓信息
    exit_date = Column(DateTime, nullable=True, comment="平仓日期")
    exit_price = Column(Numeric(12, 4), nullable=True, comment="平仓价格")
    exit_quantity = Column(Integer, nullable=True, comment="平仓数量")
    
    # 盈亏信息
    pnl = Column(Numeric(12, 4), default=0, comment="盈亏金额")
    pnl_percent = Column(Numeric(8, 4), default=0, comment="盈亏比例")
    commission = Column(Numeric(12, 4), default=0, comment="手续费")
    
    # 持仓时间
    holding_days = Column(Integer, nullable=True, comment="持仓天数")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    result = relationship("BacktestResult", backref="trades")

    @hybrid_property
    def is_profitable(self):
        """是否盈利"""
        return self.pnl > 0

    @hybrid_property
    def net_pnl(self):
        """净盈亏"""
        return self.pnl - self.commission

    def __repr__(self):
        return f"<BacktestTrade(symbol={self.symbol_code}, pnl={self.pnl})>"


class BacktestMetrics(Base):
    """回测指标详情"""
    __tablename__ = "backtest_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    result_id = Column(GUID(), ForeignKey("backtest_results.id"), nullable=False, index=True)
    
    # 收益相关指标
    cagr = Column(Numeric(8, 4), default=0, comment="复合年增长率")
    total_return_pct = Column(Numeric(8, 4), default=0, comment="总收益率百分比")
    
    # 风险相关指标
    max_drawdown_pct = Column(Numeric(8, 4), default=0, comment="最大回撤百分比")
    max_drawdown_duration = Column(Integer, default=0, comment="最大回撤持续天数")
    var_95 = Column(Numeric(8, 4), default=0, comment="95%风险价值")
    cvar_95 = Column(Numeric(8, 4), default=0, comment="95%条件风险价值")
    
    # 比率指标
    sharpe_ratio_annual = Column(Numeric(8, 4), default=0, comment="年化夏普比率")
    sortino_ratio_annual = Column(Numeric(8, 4), default=0, comment="年化索提诺比率")
    omega_ratio = Column(Numeric(8, 4), default=0, comment="欧米茄比率")
    
    # 交易统计
    avg_trade_duration = Column(Numeric(8, 2), default=0, comment="平均交易持续天数")
    trade_frequency = Column(Numeric(8, 2), default=0, comment="交易频率(次/年)")
    turnover_rate = Column(Numeric(8, 4), default=0, comment="换手率")
    
    # 稳定性指标
    stability = Column(Numeric(8, 4), default=0, comment="稳定性")
    tail_ratio = Column(Numeric(8, 4), default=0, comment="尾部比率")
    skewness = Column(Numeric(8, 4), default=0, comment="偏度")
    kurtosis = Column(Numeric(8, 4), default=0, comment="峰度")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    result = relationship("BacktestResult", backref="metrics")

    def __repr__(self):
        return f"<BacktestMetrics(cagr={self.cagr}, max_dd={self.max_drawdown_pct})>"


class BacktestComparison(Base):
    """回测对比"""
    __tablename__ = "backtest_comparisons"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 对比信息
    name = Column(String(100), nullable=False, comment="对比名称")
    description = Column(Text, nullable=True, comment="对比描述")
    
    # 对比的回测结果ID列表
    result_ids = Column(JSON, nullable=False, comment="回测结果ID列表")
    
    # 对比分析结果
    comparison_data = Column(JSON, nullable=True, comment="对比分析数据JSON")
    ranking = Column(JSON, nullable=True, comment="排名数据JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    user = relationship("User", backref="backtest_comparisons")

    def __repr__(self):
        return f"<BacktestComparison(name={self.name})>"