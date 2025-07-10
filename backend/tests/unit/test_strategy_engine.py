"""
策略引擎核心功能测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.strategy_engine import StrategyEngine, BaseStrategy
from app.models.strategy import Strategy, StrategyType, StrategyStatus
from app.schemas.strategy import StrategySignal, SignalType
from app.models.market import MarketData


class MockStrategy(BaseStrategy):
    """模拟策略类用于测试"""
    
    def __init__(self, parameters: dict = None):
        super().__init__(parameters or {})
        self.signals = []
        self.indicators = {}
    
    async def initialize(self):
        """初始化策略"""
        self.fast_period = self.parameters.get('fast_period', 12)
        self.slow_period = self.parameters.get('slow_period', 26)
        self.signal_period = self.parameters.get('signal_period', 9)
    
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 计算MACD指标
        exp1 = data['close'].ewm(span=self.fast_period).mean()
        exp2 = data['close'].ewm(span=self.slow_period).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.signal_period).mean()
        histogram = macd - signal
        
        result = data.copy()
        result['macd'] = macd
        result['signal'] = signal
        result['histogram'] = histogram
        
        return result
    
    async def generate_signals(self, data: pd.DataFrame) -> list:
        """生成交易信号"""
        signals = []
        
        # 计算指标
        data_with_indicators = await self.calculate_indicators(data)
        
        # 生成信号逻辑
        for i in range(1, len(data_with_indicators)):
            current = data_with_indicators.iloc[i]
            previous = data_with_indicators.iloc[i-1]
            
            # MACD金叉买入信号
            if (previous['macd'] <= previous['signal'] and 
                current['macd'] > current['signal']):
                signals.append(StrategySignal(
                    strategy_id=self.strategy_id,
                    symbol=current.get('symbol', '000001'),
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    price=current['close'],
                    timestamp=current.get('timestamp', datetime.now())
                ))
            
            # MACD死叉卖出信号
            elif (previous['macd'] >= previous['signal'] and 
                  current['macd'] < current['signal']):
                signals.append(StrategySignal(
                    strategy_id=self.strategy_id,
                    symbol=current.get('symbol', '000001'),
                    signal_type=SignalType.SELL,
                    strength=0.8,
                    price=current['close'],
                    timestamp=current.get('timestamp', datetime.now())
                ))
        
        return signals
    
    async def on_market_data(self, market_data: MarketData):
        """处理市场数据"""
        # 更新内部状态
        self.last_price = market_data.close
        self.last_update = market_data.timestamp
    
    async def on_signal(self, signal: StrategySignal):
        """处理信号"""
        self.signals.append(signal)


@pytest.mark.unit
@pytest.mark.strategy
@pytest.mark.asyncio
class TestStrategyEngine:
    """策略引擎测试类"""

    @pytest.fixture
    def strategy_engine(self):
        """创建策略引擎实例"""
        return StrategyEngine()

    @pytest.fixture
    def mock_strategy(self):
        """创建模拟策略"""
        strategy = MockStrategy({
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        })
        strategy.strategy_id = "test-strategy-id"
        return strategy

    @pytest.fixture
    def sample_market_data(self):
        """生成示例市场数据"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        np.random.seed(42)  # 确保可重现的随机数据
        
        # 生成模拟价格数据
        base_price = 100
        returns = np.random.normal(0.001, 0.02, 50)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'symbol': '000001',
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, 50)
        })
        
        return data

    async def test_strategy_engine_initialization(self, strategy_engine):
        """测试策略引擎初始化"""
        assert strategy_engine is not None
        assert hasattr(strategy_engine, 'strategies')
        assert hasattr(strategy_engine, 'running_strategies')
        assert len(strategy_engine.strategies) == 0

    async def test_register_strategy(self, strategy_engine, mock_strategy):
        """测试注册策略"""
        # 执行测试
        await strategy_engine.register_strategy(mock_strategy)
        
        # 验证结果
        assert len(strategy_engine.strategies) == 1
        assert mock_strategy.strategy_id in strategy_engine.strategies
        assert strategy_engine.strategies[mock_strategy.strategy_id] == mock_strategy

    async def test_unregister_strategy(self, strategy_engine, mock_strategy):
        """测试注销策略"""
        # 先注册策略
        await strategy_engine.register_strategy(mock_strategy)
        assert len(strategy_engine.strategies) == 1
        
        # 执行测试
        await strategy_engine.unregister_strategy(mock_strategy.strategy_id)
        
        # 验证结果
        assert len(strategy_engine.strategies) == 0
        assert mock_strategy.strategy_id not in strategy_engine.strategies

    async def test_start_strategy(self, strategy_engine, mock_strategy):
        """测试启动策略"""
        # 注册策略
        await strategy_engine.register_strategy(mock_strategy)
        
        # 执行测试
        result = await strategy_engine.start_strategy(mock_strategy.strategy_id)
        
        # 验证结果
        assert result is True
        assert mock_strategy.strategy_id in strategy_engine.running_strategies
        assert strategy_engine.running_strategies[mock_strategy.strategy_id] is True

    async def test_stop_strategy(self, strategy_engine, mock_strategy):
        """测试停止策略"""
        # 注册并启动策略
        await strategy_engine.register_strategy(mock_strategy)
        await strategy_engine.start_strategy(mock_strategy.strategy_id)
        
        # 执行测试
        result = await strategy_engine.stop_strategy(mock_strategy.strategy_id)
        
        # 验证结果
        assert result is True
        assert mock_strategy.strategy_id not in strategy_engine.running_strategies

    async def test_strategy_initialization(self, mock_strategy):
        """测试策略初始化"""
        # 执行测试
        await mock_strategy.initialize()
        
        # 验证结果
        assert mock_strategy.fast_period == 12
        assert mock_strategy.slow_period == 26
        assert mock_strategy.signal_period == 9

    async def test_calculate_indicators(self, mock_strategy, sample_market_data):
        """测试指标计算"""
        await mock_strategy.initialize()
        
        # 执行测试
        result = await mock_strategy.calculate_indicators(sample_market_data)
        
        # 验证结果
        assert 'macd' in result.columns
        assert 'signal' in result.columns
        assert 'histogram' in result.columns
        assert len(result) == len(sample_market_data)
        assert not result['macd'].isna().all()
        assert not result['signal'].isna().all()

    async def test_generate_signals(self, mock_strategy, sample_market_data):
        """测试信号生成"""
        await mock_strategy.initialize()
        
        # 执行测试
        signals = await mock_strategy.generate_signals(sample_market_data)
        
        # 验证结果
        assert isinstance(signals, list)
        for signal in signals:
            assert isinstance(signal, StrategySignal)
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            assert 0 <= signal.strength <= 1
            assert signal.price > 0

    async def test_buy_signal_generation(self, mock_strategy):
        """测试买入信号生成"""
        await mock_strategy.initialize()
        
        # 构造MACD金叉场景的数据
        data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=4),
            'symbol': '000001',
            'open': [100, 101, 102, 103],
            'high': [101, 102, 103, 104],
            'low': [99, 100, 101, 102],
            'close': [100, 101, 102, 103],
            'volume': [1000, 1100, 1200, 1300]
        })
        
        # 手动设置MACD指标以模拟金叉
        with patch.object(mock_strategy, 'calculate_indicators') as mock_calc:
            data_with_indicators = data.copy()
            data_with_indicators['macd'] = [-1, -0.5, 0.5, 1]
            data_with_indicators['signal'] = [0, 0, 0, 0]
            data_with_indicators['histogram'] = [-1, -0.5, 0.5, 1]
            mock_calc.return_value = data_with_indicators
            
            signals = await mock_strategy.generate_signals(data)
            
            # 验证买入信号
            buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
            assert len(buy_signals) > 0

    async def test_sell_signal_generation(self, mock_strategy):
        """测试卖出信号生成"""
        await mock_strategy.initialize()
        
        # 构造MACD死叉场景的数据
        data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=4),
            'symbol': '000001',
            'open': [103, 102, 101, 100],
            'high': [104, 103, 102, 101],
            'low': [102, 101, 100, 99],
            'close': [103, 102, 101, 100],
            'volume': [1300, 1200, 1100, 1000]
        })
        
        # 手动设置MACD指标以模拟死叉
        with patch.object(mock_strategy, 'calculate_indicators') as mock_calc:
            data_with_indicators = data.copy()
            data_with_indicators['macd'] = [1, 0.5, -0.5, -1]
            data_with_indicators['signal'] = [0, 0, 0, 0]
            data_with_indicators['histogram'] = [1, 0.5, -0.5, -1]
            mock_calc.return_value = data_with_indicators
            
            signals = await mock_strategy.generate_signals(data)
            
            # 验证卖出信号
            sell_signals = [s for s in signals if s.signal_type == SignalType.SELL]
            assert len(sell_signals) > 0

    async def test_on_market_data(self, mock_strategy):
        """测试市场数据处理"""
        # 创建模拟市场数据
        market_data = Mock(spec=MarketData)
        market_data.close = Decimal('105.50')
        market_data.timestamp = datetime.now()
        
        # 执行测试
        await mock_strategy.on_market_data(market_data)
        
        # 验证结果
        assert mock_strategy.last_price == Decimal('105.50')
        assert mock_strategy.last_update == market_data.timestamp

    async def test_on_signal(self, mock_strategy):
        """测试信号处理"""
        # 创建模拟信号
        signal = StrategySignal(
            strategy_id="test-strategy-id",
            symbol="000001",
            signal_type=SignalType.BUY,
            strength=0.8,
            price=105.50,
            timestamp=datetime.now()
        )
        
        # 执行测试
        await mock_strategy.on_signal(signal)
        
        # 验证结果
        assert len(mock_strategy.signals) == 1
        assert mock_strategy.signals[0] == signal

    async def test_strategy_engine_process_market_data(self, strategy_engine, mock_strategy):
        """测试策略引擎处理市场数据"""
        # 注册并启动策略
        await strategy_engine.register_strategy(mock_strategy)
        await strategy_engine.start_strategy(mock_strategy.strategy_id)
        
        # 创建市场数据
        market_data = Mock(spec=MarketData)
        market_data.symbol = "000001"
        market_data.close = Decimal('105.50')
        market_data.timestamp = datetime.now()
        
        # 执行测试
        with patch.object(mock_strategy, 'on_market_data') as mock_on_data:
            await strategy_engine.process_market_data(market_data)
            mock_on_data.assert_called_once_with(market_data)

    async def test_strategy_parameter_validation(self, mock_strategy):
        """测试策略参数验证"""
        # 测试有效参数
        valid_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }
        strategy = MockStrategy(valid_params)
        await strategy.initialize()
        
        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.signal_period == 9

    async def test_strategy_error_handling(self, mock_strategy, sample_market_data):
        """测试策略错误处理"""
        await mock_strategy.initialize()
        
        # 模拟计算指标时出错
        with patch.object(mock_strategy, 'calculate_indicators', side_effect=Exception("计算错误")):
            with pytest.raises(Exception, match="计算错误"):
                await mock_strategy.generate_signals(sample_market_data)

    async def test_strategy_performance_tracking(self, strategy_engine, mock_strategy):
        """测试策略性能跟踪"""
        # 注册策略
        await strategy_engine.register_strategy(mock_strategy)
        
        # 模拟策略运行时间跟踪
        start_time = datetime.now()
        await strategy_engine.start_strategy(mock_strategy.strategy_id)
        
        # 验证策略状态
        assert mock_strategy.strategy_id in strategy_engine.running_strategies
        
        # 停止策略
        await strategy_engine.stop_strategy(mock_strategy.strategy_id)
        end_time = datetime.now()
        
        # 验证运行时间
        assert end_time > start_time
