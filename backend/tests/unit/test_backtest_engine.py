"""
回测引擎核心功能测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.backtest_engine import BacktestEngine, BacktestConfig, BacktestResult
from app.models.strategy import Strategy
from app.models.market import MarketData
from app.schemas.backtest import RebalanceFrequency


class MockBacktestEngine(BacktestEngine):
    """模拟回测引擎用于测试"""
    
    def __init__(self, config: BacktestConfig):
        super().__init__(config)
        self.trades = []
        self.positions = {}
        self.portfolio_value = config.initial_capital
        self.daily_returns = []
        
    async def load_historical_data(self, symbols: list, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """加载历史数据"""
        # 生成模拟历史数据
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        data_list = []
        
        for symbol in symbols:
            np.random.seed(42)  # 确保可重现
            base_price = 100.0
            
            for date in date_range:
                # 生成模拟价格数据
                price_change = np.random.normal(0.001, 0.02)
                base_price *= (1 + price_change)
                
                data_list.append({
                    'date': date,
                    'symbol': symbol,
                    'open': base_price * 0.999,
                    'high': base_price * 1.01,
                    'low': base_price * 0.99,
                    'close': base_price,
                    'volume': np.random.randint(10000, 100000)
                })
        
        return pd.DataFrame(data_list)
    
    async def execute_strategy(self, data: pd.DataFrame, strategy: Strategy) -> list:
        """执行策略"""
        signals = []
        
        # 简单的MACD策略逻辑
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            # 计算MACD
            exp1 = symbol_data['close'].ewm(span=12).mean()
            exp2 = symbol_data['close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            
            # 生成交易信号
            for i in range(1, len(symbol_data)):
                if macd.iloc[i] > signal_line.iloc[i] and macd.iloc[i-1] <= signal_line.iloc[i-1]:
                    # 买入信号
                    signals.append({
                        'date': symbol_data.iloc[i]['date'],
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': symbol_data.iloc[i]['close'],
                        'quantity': 100
                    })
                elif macd.iloc[i] < signal_line.iloc[i] and macd.iloc[i-1] >= signal_line.iloc[i-1]:
                    # 卖出信号
                    signals.append({
                        'date': symbol_data.iloc[i]['date'],
                        'symbol': symbol,
                        'action': 'SELL',
                        'price': symbol_data.iloc[i]['close'],
                        'quantity': 100
                    })
        
        return signals
    
    async def calculate_performance_metrics(self, trades: list, daily_returns: list) -> dict:
        """计算绩效指标"""
        if not daily_returns:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        returns_series = pd.Series(daily_returns)
        
        # 计算基本指标
        total_return = (1 + returns_series).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns_series)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 计算最大回撤
        cumulative_returns = (1 + returns_series).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 计算胜率
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        total_trades = len(trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'volatility': float(volatility),
            'win_rate': float(win_rate),
            'total_trades': total_trades
        }


@pytest.mark.unit
@pytest.mark.backtest
@pytest.mark.asyncio
class TestBacktestEngine:
    """回测引擎测试类"""

    @pytest.fixture
    def backtest_config(self):
        """回测配置"""
        return BacktestConfig(
            strategy_id="test-strategy-id",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 3, 31),
            initial_capital=Decimal("100000.00"),
            symbols=["000001", "000002"],
            benchmark="000300",
            commission_rate=Decimal("0.0003"),
            slippage_rate=Decimal("0.001"),
            rebalance_frequency=RebalanceFrequency.DAILY
        )

    @pytest.fixture
    def mock_strategy(self):
        """模拟策略"""
        strategy = Mock(spec=Strategy)
        strategy.id = "test-strategy-id"
        strategy.name = "MACD策略"
        strategy.parameters = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
        return strategy

    @pytest.fixture
    def backtest_engine(self, backtest_config):
        """创建回测引擎实例"""
        return MockBacktestEngine(backtest_config)

    async def test_backtest_engine_initialization(self, backtest_engine, backtest_config):
        """测试回测引擎初始化"""
        assert backtest_engine.config == backtest_config
        assert backtest_engine.portfolio_value == backtest_config.initial_capital
        assert backtest_engine.trades == []
        assert backtest_engine.positions == {}

    async def test_load_historical_data(self, backtest_engine):
        """测试加载历史数据"""
        # 执行测试
        data = await backtest_engine.load_historical_data(
            symbols=["000001", "000002"],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )
        
        # 验证结果
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert 'symbol' in data.columns
        assert 'date' in data.columns
        assert 'close' in data.columns
        assert set(data['symbol'].unique()) == {"000001", "000002"}

    async def test_execute_strategy(self, backtest_engine, mock_strategy):
        """测试执行策略"""
        # 准备历史数据
        data = await backtest_engine.load_historical_data(
            symbols=["000001"],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 28)
        )
        
        # 执行测试
        signals = await backtest_engine.execute_strategy(data, mock_strategy)
        
        # 验证结果
        assert isinstance(signals, list)
        for signal in signals:
            assert 'date' in signal
            assert 'symbol' in signal
            assert 'action' in signal
            assert signal['action'] in ['BUY', 'SELL']
            assert 'price' in signal
            assert 'quantity' in signal

    async def test_calculate_performance_metrics_empty_data(self, backtest_engine):
        """测试空数据的绩效指标计算"""
        # 执行测试
        metrics = await backtest_engine.calculate_performance_metrics([], [])
        
        # 验证结果
        assert metrics['total_return'] == 0.0
        assert metrics['annual_return'] == 0.0
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['max_drawdown'] == 0.0
        assert metrics['win_rate'] == 0.0
        assert metrics['total_trades'] == 0

    async def test_calculate_performance_metrics_with_data(self, backtest_engine):
        """测试有数据的绩效指标计算"""
        # 准备测试数据
        trades = [
            {'pnl': 100.0, 'date': datetime(2023, 1, 1)},
            {'pnl': -50.0, 'date': datetime(2023, 1, 2)},
            {'pnl': 200.0, 'date': datetime(2023, 1, 3)},
            {'pnl': -30.0, 'date': datetime(2023, 1, 4)},
            {'pnl': 150.0, 'date': datetime(2023, 1, 5)}
        ]
        
        daily_returns = [0.01, -0.005, 0.02, -0.003, 0.015]
        
        # 执行测试
        metrics = await backtest_engine.calculate_performance_metrics(trades, daily_returns)
        
        # 验证结果
        assert isinstance(metrics, dict)
        assert 'total_return' in metrics
        assert 'annual_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'volatility' in metrics
        assert 'win_rate' in metrics
        assert 'total_trades' in metrics
        
        assert metrics['total_trades'] == 5
        assert 0 <= metrics['win_rate'] <= 1
        assert metrics['total_return'] > 0  # 正收益

    async def test_backtest_run_complete_workflow(self, backtest_engine, mock_strategy):
        """测试完整回测流程"""
        # 执行完整回测
        with patch.object(backtest_engine, 'load_historical_data') as mock_load_data:
            # Mock历史数据
            mock_data = pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=30),
                'symbol': ['000001'] * 30,
                'open': range(100, 130),
                'high': range(101, 131),
                'low': range(99, 129),
                'close': range(100, 130),
                'volume': [10000] * 30
            })
            mock_load_data.return_value = mock_data
            
            # 执行回测
            result = await backtest_engine.run_backtest(mock_strategy)
            
            # 验证结果
            assert isinstance(result, dict)
            assert 'performance_metrics' in result
            assert 'trades' in result
            assert 'daily_returns' in result

    async def test_backtest_commission_calculation(self, backtest_engine):
        """测试手续费计算"""
        # 测试数据
        trade_value = Decimal("10000.00")
        commission_rate = Decimal("0.0003")
        
        # 计算手续费
        commission = backtest_engine.calculate_commission(trade_value, commission_rate)
        
        # 验证结果
        expected_commission = trade_value * commission_rate
        assert commission == expected_commission

    async def test_backtest_slippage_calculation(self, backtest_engine):
        """测试滑点计算"""
        # 测试数据
        price = Decimal("100.00")
        slippage_rate = Decimal("0.001")
        
        # 计算买入滑点
        buy_price = backtest_engine.calculate_slippage_price(price, slippage_rate, "BUY")
        assert buy_price > price
        
        # 计算卖出滑点
        sell_price = backtest_engine.calculate_slippage_price(price, slippage_rate, "SELL")
        assert sell_price < price

    async def test_backtest_position_management(self, backtest_engine):
        """测试持仓管理"""
        # 初始化持仓
        symbol = "000001"
        quantity = 100
        price = Decimal("100.00")
        
        # 开仓
        backtest_engine.update_position(symbol, quantity, price, "BUY")
        assert symbol in backtest_engine.positions
        assert backtest_engine.positions[symbol]['quantity'] == quantity
        
        # 加仓
        backtest_engine.update_position(symbol, 50, Decimal("105.00"), "BUY")
        assert backtest_engine.positions[symbol]['quantity'] == 150
        
        # 减仓
        backtest_engine.update_position(symbol, 30, Decimal("110.00"), "SELL")
        assert backtest_engine.positions[symbol]['quantity'] == 120

    async def test_backtest_risk_management(self, backtest_engine):
        """测试风险管理"""
        # 测试最大持仓限制
        max_position_size = Decimal("0.2")  # 20%
        portfolio_value = Decimal("100000.00")
        trade_value = Decimal("25000.00")  # 25%
        
        # 检查是否超过限制
        is_valid = backtest_engine.check_position_limit(trade_value, portfolio_value, max_position_size)
        assert is_valid is False  # 应该超过限制
        
        # 测试合理的交易金额
        trade_value = Decimal("15000.00")  # 15%
        is_valid = backtest_engine.check_position_limit(trade_value, portfolio_value, max_position_size)
        assert is_valid is True  # 应该在限制内

    async def test_backtest_benchmark_comparison(self, backtest_engine):
        """测试基准比较"""
        # 准备策略收益和基准收益
        strategy_returns = [0.01, -0.005, 0.02, -0.003, 0.015]
        benchmark_returns = [0.008, -0.002, 0.015, -0.001, 0.012]
        
        # 计算相对绩效
        relative_performance = backtest_engine.calculate_relative_performance(
            strategy_returns, benchmark_returns
        )
        
        # 验证结果
        assert isinstance(relative_performance, dict)
        assert 'alpha' in relative_performance
        assert 'beta' in relative_performance
        assert 'information_ratio' in relative_performance
        assert 'tracking_error' in relative_performance

    async def test_backtest_error_handling(self, backtest_engine, mock_strategy):
        """测试错误处理"""
        # 测试无效数据处理
        with patch.object(backtest_engine, 'load_historical_data', side_effect=Exception("数据加载失败")):
            with pytest.raises(Exception, match="数据加载失败"):
                await backtest_engine.run_backtest(mock_strategy)

    async def test_backtest_progress_reporting(self, backtest_engine, mock_strategy):
        """测试进度报告"""
        progress_updates = []
        
        def progress_callback(progress: float, message: str):
            progress_updates.append((progress, message))
        
        # 设置进度回调
        backtest_engine.set_progress_callback(progress_callback)
        
        # 模拟回测进度
        await backtest_engine.report_progress(0.5, "处理中...")
        
        # 验证进度更新
        assert len(progress_updates) == 1
        assert progress_updates[0][0] == 0.5
        assert progress_updates[0][1] == "处理中..."
