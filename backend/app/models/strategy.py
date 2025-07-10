"""
策略模型
包含策略定义、参数、运行状态等
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


class StrategyType(str, Enum):
    """策略类型"""
    TREND_FOLLOWING = "trend_following"    # 趋势跟踪
    MEAN_REVERSION = "mean_reversion"      # 均值回归
    ARBITRAGE = "arbitrage"                # 套利
    MOMENTUM = "momentum"                  # 动量
    GRID = "grid"                          # 网格
    CUSTOM = "custom"                      # 自定义


class StrategyStatus(str, Enum):
    """策略状态"""
    DRAFT = "draft"                        # 草稿
    TESTING = "testing"                    # 测试中
    RUNNING = "running"                    # 运行中
    PAUSED = "paused"                      # 暂停
    STOPPED = "stopped"                    # 已停止
    ERROR = "error"                        # 错误


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"                            # 低风险
    MEDIUM = "medium"                      # 中等风险
    HIGH = "high"                          # 高风险
    EXTREME = "extreme"                    # 极高风险


class Strategy(Base):
    """策略模型"""
    __tablename__ = "strategies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 策略基本信息
    name = Column(String(100), nullable=False, comment="策略名称")
    description = Column(Text, nullable=True, comment="策略描述")
    strategy_type = Column(SQLEnum(StrategyType), nullable=False, comment="策略类型")
    version = Column(String(20), default="1.0.0", comment="版本号")
    
    # 策略代码
    code = Column(Text, nullable=True, comment="策略代码")
    entry_rules = Column(JSON, nullable=True, comment="入场规则JSON")
    exit_rules = Column(JSON, nullable=True, comment="出场规则JSON")
    parameters = Column(JSON, nullable=True, comment="策略参数JSON")
    
    # 适用标的
    symbols = Column(JSON, nullable=True, comment="适用标的列表")
    timeframe = Column(String(10), default="1d", comment="时间周期")
    
    # 风险控制
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM, comment="风险等级")
    max_position_size = Column(Numeric(8, 4), default=0.1, comment="最大仓位比例")
    stop_loss = Column(Numeric(8, 4), nullable=True, comment="止损比例")
    take_profit = Column(Numeric(8, 4), nullable=True, comment="止盈比例")
    
    # 运行状态
    status = Column(SQLEnum(StrategyStatus), default=StrategyStatus.DRAFT, comment="策略状态")
    is_public = Column(Boolean, default=False, comment="是否公开")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    
    # 性能指标
    total_return = Column(Numeric(12, 4), default=0, comment="总收益率")
    annual_return = Column(Numeric(12, 4), default=0, comment="年化收益率")
    sharpe_ratio = Column(Numeric(8, 4), default=0, comment="夏普比率")
    max_drawdown = Column(Numeric(8, 4), default=0, comment="最大回撤")
    win_rate = Column(Numeric(8, 4), default=0, comment="胜率")
    
    # 统计信息
    total_trades = Column(Integer, default=0, comment="总交易次数")
    profitable_trades = Column(Integer, default=0, comment="盈利交易次数")
    avg_trade_return = Column(Numeric(8, 4), default=0, comment="平均交易收益")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    last_run_at = Column(DateTime, nullable=True, comment="最后运行时间")

    # 关联关系
    user = relationship("User", backref="strategies")
    instances = relationship("StrategyInstance", back_populates="strategy")
    backtests = relationship("BacktestResult", back_populates="strategy")

    @hybrid_property
    def loss_rate(self):
        """亏损率"""
        return 1 - self.win_rate if self.win_rate else 0

    @hybrid_property
    def profit_factor(self):
        """盈利因子"""
        if self.total_trades > 0 and self.profitable_trades > 0:
            losing_trades = self.total_trades - self.profitable_trades
            if losing_trades > 0:
                avg_profit = self.avg_trade_return * self.profitable_trades
                avg_loss = abs(self.avg_trade_return) * losing_trades
                return avg_profit / avg_loss if avg_loss > 0 else 0
        return 0

    def __repr__(self):
        return f"<Strategy(name={self.name}, type={self.strategy_type}, status={self.status})>"


class StrategyInstance(Base):
    """策略实例（运行中的策略）"""
    __tablename__ = "strategy_instances"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    strategy_id = Column(GUID(), ForeignKey("strategies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 实例信息
    instance_name = Column(String(100), nullable=False, comment="实例名称")
    account_id = Column(String(50), nullable=False, comment="交易账户")
    
    # 运行参数
    initial_capital = Column(Numeric(20, 2), nullable=False, comment="初始资金")
    current_capital = Column(Numeric(20, 2), nullable=False, comment="当前资金")
    position_size = Column(Numeric(8, 4), default=0.1, comment="仓位大小")
    
    # 运行状态
    status = Column(SQLEnum(StrategyStatus), default=StrategyStatus.STOPPED, comment="运行状态")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    
    # 实时性能
    current_return = Column(Numeric(12, 4), default=0, comment="当前收益率")
    current_drawdown = Column(Numeric(8, 4), default=0, comment="当前回撤")
    trades_today = Column(Integer, default=0, comment="今日交易次数")
    
    # 配置信息
    config = Column(JSON, nullable=True, comment="实例配置JSON")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系
    strategy = relationship("Strategy", back_populates="instances")
    user = relationship("User", backref="strategy_instances")
    signals = relationship("StrategySignal", back_populates="instance")

    @hybrid_property
    def total_pnl(self):
        """总盈亏"""
        return self.current_capital - self.initial_capital

    @hybrid_property
    def is_running(self):
        """是否运行中"""
        return self.status == StrategyStatus.RUNNING

    def __repr__(self):
        return f"<StrategyInstance(name={self.instance_name}, status={self.status})>"


class StrategySignal(Base):
    """策略信号"""
    __tablename__ = "strategy_signals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    instance_id = Column(GUID(), ForeignKey("strategy_instances.id"), nullable=False, index=True)
    
    # 信号信息
    symbol_code = Column(String(20), nullable=False, index=True, comment="标的代码")
    signal_type = Column(String(20), nullable=False, comment="信号类型")
    action = Column(String(10), nullable=False, comment="操作动作")
    
    # 价格信息
    price = Column(Numeric(12, 4), nullable=False, comment="信号价格")
    quantity = Column(Integer, nullable=False, comment="建议数量")
    confidence = Column(Numeric(4, 2), default=1.0, comment="信号置信度")
    
    # 信号详情
    reason = Column(Text, nullable=True, comment="信号原因")
    indicators = Column(JSON, nullable=True, comment="技术指标JSON")
    
    # 执行状态
    is_executed = Column(Boolean, default=False, comment="是否已执行")
    order_id = Column(String(50), nullable=True, comment="关联订单ID")
    
    # 时间戳
    signal_time = Column(DateTime, nullable=False, comment="信号时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    instance = relationship("StrategyInstance", back_populates="signals")

    def __repr__(self):
        return f"<StrategySignal(symbol={self.symbol_code}, action={self.action}, price={self.price})>"


class StrategyPerformance(Base):
    """策略性能记录"""
    __tablename__ = "strategy_performance"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    instance_id = Column(GUID(), ForeignKey("strategy_instances.id"), nullable=False, index=True)
    
    # 日期
    date = Column(DateTime, nullable=False, index=True, comment="日期")
    
    # 资金状况
    total_value = Column(Numeric(20, 2), nullable=False, comment="总价值")
    cash = Column(Numeric(20, 2), nullable=False, comment="现金")
    position_value = Column(Numeric(20, 2), nullable=False, comment="持仓价值")
    
    # 收益指标
    daily_return = Column(Numeric(8, 4), default=0, comment="日收益率")
    cumulative_return = Column(Numeric(12, 4), default=0, comment="累计收益率")
    drawdown = Column(Numeric(8, 4), default=0, comment="回撤")
    
    # 交易统计
    trades_count = Column(Integer, default=0, comment="交易次数")
    winning_trades = Column(Integer, default=0, comment="盈利交易")
    losing_trades = Column(Integer, default=0, comment="亏损交易")
    
    # 风险指标
    volatility = Column(Numeric(8, 4), default=0, comment="波动率")
    var = Column(Numeric(8, 4), default=0, comment="风险价值")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    instance = relationship("StrategyInstance", backref="performance_records")

    def __repr__(self):
        return f"<StrategyPerformance(date={self.date}, return={self.daily_return})>"


class StrategyTemplate(Base):
    """策略模板"""
    __tablename__ = "strategy_templates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    
    # 模板信息
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    category = Column(String(50), nullable=False, comment="模板分类")
    strategy_type = Column(SQLEnum(StrategyType), nullable=False, comment="策略类型")
    
    # 模板代码
    template_code = Column(Text, nullable=False, comment="模板代码")
    default_parameters = Column(JSON, nullable=True, comment="默认参数JSON")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Numeric(3, 2), default=0, comment="评分")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_featured = Column(Boolean, default=False, comment="是否推荐")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<StrategyTemplate(name={self.name}, type={self.strategy_type})>"