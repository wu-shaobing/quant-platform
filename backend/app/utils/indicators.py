"""
技术指标计算模块
提供常用的技术指标计算功能，支持向量化计算
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional, Union
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def sma(data: Union[List[float], pd.Series, np.ndarray], period: int) -> np.ndarray:
        """
        简单移动平均线 (Simple Moving Average)
        
        Args:
            data: 价格数据
            period: 计算周期
            
        Returns:
            SMA值数组
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.values
        
        if len(data) < period:
            return np.full(len(data), np.nan)
        
        result = np.full(len(data), np.nan)
        for i in range(period - 1, len(data)):
            result[i] = np.mean(data[i - period + 1:i + 1])
        
        return result
    
    @staticmethod
    def ema(data: Union[List[float], pd.Series, np.ndarray], period: int) -> np.ndarray:
        """
        指数移动平均线 (Exponential Moving Average)
        
        Args:
            data: 价格数据
            period: 计算周期
            
        Returns:
            EMA值数组
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.values
        
        if len(data) < period:
            return np.full(len(data), np.nan)
        
        alpha = 2.0 / (period + 1)
        result = np.full(len(data), np.nan)
        
        # 第一个EMA值使用SMA
        result[period - 1] = np.mean(data[:period])
        
        # 后续EMA值
        for i in range(period, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        
        return result
    
    @staticmethod
    def macd(data: Union[List[float], pd.Series, np.ndarray], 
             fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, np.ndarray]:
        """
        MACD指标 (Moving Average Convergence Divergence)
        
        Args:
            data: 价格数据
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期
            
        Returns:
            包含MACD线、信号线、柱状图的字典
        """
        ema_fast = TechnicalIndicators.ema(data, fast_period)
        ema_slow = TechnicalIndicators.ema(data, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def rsi(data: Union[List[float], pd.Series, np.ndarray], period: int = 14) -> np.ndarray:
        """
        相对强弱指标 (Relative Strength Index)
        
        Args:
            data: 价格数据
            period: 计算周期
            
        Returns:
            RSI值数组
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.values
        
        if len(data) < period + 1:
            return np.full(len(data), np.nan)
        
        # 计算价格变化
        delta = np.diff(data)
        
        # 分离上涨和下跌
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        # 计算平均收益和损失
        avg_gains = np.full(len(delta), np.nan)
        avg_losses = np.full(len(delta), np.nan)
        
        # 初始值使用SMA
        avg_gains[period - 1] = np.mean(gains[:period])
        avg_losses[period - 1] = np.mean(losses[:period])
        
        # 后续值使用Wilder's smoothing
        for i in range(period, len(delta)):
            avg_gains[i] = (avg_gains[i - 1] * (period - 1) + gains[i]) / period
            avg_losses[i] = (avg_losses[i - 1] * (period - 1) + losses[i]) / period
        
        # 计算RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        # 添加第一个NaN值以匹配原始数据长度
        result = np.full(len(data), np.nan)
        result[period:] = rsi[period - 1:]
        
        return result
    
    @staticmethod
    def bollinger_bands(data: Union[List[float], pd.Series, np.ndarray], 
                       period: int = 20, std_dev: float = 2.0) -> Dict[str, np.ndarray]:
        """
        布林带 (Bollinger Bands)
        
        Args:
            data: 价格数据
            period: 计算周期
            std_dev: 标准差倍数
            
        Returns:
            包含上轨、中轨、下轨的字典
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.values
        
        if len(data) < period:
            return {
                "upper": np.full(len(data), np.nan),
                "middle": np.full(len(data), np.nan),
                "lower": np.full(len(data), np.nan)
            }
        
        # 中轨（移动平均线）
        middle = TechnicalIndicators.sma(data, period)
        
        # 计算标准差
        std = np.full(len(data), np.nan)
        for i in range(period - 1, len(data)):
            std[i] = np.std(data[i - period + 1:i + 1])
        
        # 上轨和下轨
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            "upper": upper,
            "middle": middle,
            "lower": lower
        }
    
    @staticmethod
    def kdj(high: Union[List[float], pd.Series, np.ndarray],
            low: Union[List[float], pd.Series, np.ndarray],
            close: Union[List[float], pd.Series, np.ndarray],
            k_period: int = 9, d_period: int = 3, j_period: int = 3) -> Dict[str, np.ndarray]:
        """
        KDJ指标 (Stochastic Oscillator)
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            k_period: K值计算周期
            d_period: D值平滑周期
            j_period: J值计算周期
            
        Returns:
            包含K、D、J值的字典
        """
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        if isinstance(high, pd.Series):
            high = high.values
        if isinstance(low, pd.Series):
            low = low.values
        if isinstance(close, pd.Series):
            close = close.values
        
        if len(high) < k_period:
            return {
                "k": np.full(len(high), np.nan),
                "d": np.full(len(high), np.nan),
                "j": np.full(len(high), np.nan)
            }
        
        # 计算RSV (Raw Stochastic Value)
        rsv = np.full(len(close), np.nan)
        for i in range(k_period - 1, len(close)):
            highest = np.max(high[i - k_period + 1:i + 1])
            lowest = np.min(low[i - k_period + 1:i + 1])
            if highest != lowest:
                rsv[i] = (close[i] - lowest) / (highest - lowest) * 100
            else:
                rsv[i] = 50  # 避免除零错误
        
        # 计算K值（RSV的移动平均）
        k = TechnicalIndicators.ema(rsv, d_period)
        
        # 计算D值（K值的移动平均）
        d = TechnicalIndicators.ema(k, d_period)
        
        # 计算J值
        j = 3 * k - 2 * d
        
        return {
            "k": k,
            "d": d,
            "j": j
        }
    
    @staticmethod
    def atr(high: Union[List[float], pd.Series, np.ndarray],
            low: Union[List[float], pd.Series, np.ndarray],
            close: Union[List[float], pd.Series, np.ndarray],
            period: int = 14) -> np.ndarray:
        """
        平均真实波幅 (Average True Range)
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            period: 计算周期
            
        Returns:
            ATR值数组
        """
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        if isinstance(high, pd.Series):
            high = high.values
        if isinstance(low, pd.Series):
            low = low.values
        if isinstance(close, pd.Series):
            close = close.values
        
        if len(high) < 2:
            return np.full(len(high), np.nan)
        
        # 计算真实波幅
        tr = np.full(len(high), np.nan)
        tr[0] = high[0] - low[0]  # 第一个值
        
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i - 1])
            tr3 = abs(low[i] - close[i - 1])
            tr[i] = max(tr1, tr2, tr3)
        
        # 计算ATR（真实波幅的移动平均）
        atr = TechnicalIndicators.ema(tr, period)
        
        return atr
    
    @staticmethod
    def cci(high: Union[List[float], pd.Series, np.ndarray],
            low: Union[List[float], pd.Series, np.ndarray],
            close: Union[List[float], pd.Series, np.ndarray],
            period: int = 14) -> np.ndarray:
        """
        顺势指标 (Commodity Channel Index)
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            period: 计算周期
            
        Returns:
            CCI值数组
        """
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        if isinstance(high, pd.Series):
            high = high.values
        if isinstance(low, pd.Series):
            low = low.values
        if isinstance(close, pd.Series):
            close = close.values
        
        if len(high) < period:
            return np.full(len(high), np.nan)
        
        # 计算典型价格
        typical_price = (high + low + close) / 3
        
        # 计算移动平均
        ma = TechnicalIndicators.sma(typical_price, period)
        
        # 计算平均偏差
        mean_deviation = np.full(len(high), np.nan)
        for i in range(period - 1, len(high)):
            deviations = np.abs(typical_price[i - period + 1:i + 1] - ma[i])
            mean_deviation[i] = np.mean(deviations)
        
        # 计算CCI
        cci = (typical_price - ma) / (0.015 * mean_deviation)
        
        return cci
    
    @staticmethod
    def williams_r(high: Union[List[float], pd.Series, np.ndarray],
                   low: Union[List[float], pd.Series, np.ndarray],
                   close: Union[List[float], pd.Series, np.ndarray],
                   period: int = 14) -> np.ndarray:
        """
        威廉指标 (Williams %R)
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            period: 计算周期
            
        Returns:
            Williams %R值数组
        """
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        if isinstance(high, pd.Series):
            high = high.values
        if isinstance(low, pd.Series):
            low = low.values
        if isinstance(close, pd.Series):
            close = close.values
        
        if len(high) < period:
            return np.full(len(high), np.nan)
        
        wr = np.full(len(high), np.nan)
        
        for i in range(period - 1, len(high)):
            highest = np.max(high[i - period + 1:i + 1])
            lowest = np.min(low[i - period + 1:i + 1])
            
            if highest != lowest:
                wr[i] = (highest - close[i]) / (highest - lowest) * (-100)
            else:
                wr[i] = -50  # 避免除零错误
        
        return wr
    
    @staticmethod
    def obv(close: Union[List[float], pd.Series, np.ndarray],
            volume: Union[List[float], pd.Series, np.ndarray]) -> np.ndarray:
        """
        能量潮指标 (On Balance Volume)
        
        Args:
            close: 收盘价数据
            volume: 成交量数据
            
        Returns:
            OBV值数组
        """
        if isinstance(close, list):
            close = np.array(close)
        if isinstance(volume, list):
            volume = np.array(volume)
        
        if isinstance(close, pd.Series):
            close = close.values
        if isinstance(volume, pd.Series):
            volume = volume.values
        
        if len(close) < 2:
            return np.full(len(close), np.nan)
        
        obv = np.full(len(close), np.nan)
        obv[0] = volume[0]
        
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif close[i] < close[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        
        return obv
    
    @staticmethod
    def support_resistance_levels(high: Union[List[float], pd.Series, np.ndarray],
                                 low: Union[List[float], pd.Series, np.ndarray],
                                 close: Union[List[float], pd.Series, np.ndarray],
                                 window: int = 20) -> Dict[str, List[float]]:
        """
        支撑阻力位计算
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            window: 计算窗口
            
        Returns:
            包含支撑位和阻力位的字典
        """
        if isinstance(high, list):
            high = np.array(high)
        if isinstance(low, list):
            low = np.array(low)
        if isinstance(close, list):
            close = np.array(close)
        
        if isinstance(high, pd.Series):
            high = high.values
        if isinstance(low, pd.Series):
            low = low.values
        if isinstance(close, pd.Series):
            close = close.values
        
        if len(high) < window * 2:
            return {"support": [], "resistance": []}
        
        support_levels = []
        resistance_levels = []
        
        # 寻找局部高点和低点
        for i in range(window, len(high) - window):
            # 检查是否为局部高点（阻力位）
            if high[i] == np.max(high[i - window:i + window + 1]):
                resistance_levels.append(float(high[i]))
            
            # 检查是否为局部低点（支撑位）
            if low[i] == np.min(low[i - window:i + window + 1]):
                support_levels.append(float(low[i]))
        
        # 去重并排序
        support_levels = sorted(list(set(support_levels)))
        resistance_levels = sorted(list(set(resistance_levels)), reverse=True)
        
        return {
            "support": support_levels[:5],  # 返回最多5个支撑位
            "resistance": resistance_levels[:5]  # 返回最多5个阻力位
        }
    
    @staticmethod
    def calculate_all_indicators(high: Union[List[float], pd.Series, np.ndarray],
                               low: Union[List[float], pd.Series, np.ndarray],
                               close: Union[List[float], pd.Series, np.ndarray],
                               volume: Union[List[float], pd.Series, np.ndarray]) -> Dict[str, Any]:
        """
        计算所有技术指标
        
        Args:
            high: 最高价数据
            low: 最低价数据
            close: 收盘价数据
            volume: 成交量数据
            
        Returns:
            包含所有指标的字典
        """
        try:
            indicators = {}
            
            # 移动平均线
            indicators["sma_5"] = TechnicalIndicators.sma(close, 5)
            indicators["sma_10"] = TechnicalIndicators.sma(close, 10)
            indicators["sma_20"] = TechnicalIndicators.sma(close, 20)
            indicators["sma_60"] = TechnicalIndicators.sma(close, 60)
            
            indicators["ema_5"] = TechnicalIndicators.ema(close, 5)
            indicators["ema_10"] = TechnicalIndicators.ema(close, 10)
            indicators["ema_20"] = TechnicalIndicators.ema(close, 20)
            indicators["ema_60"] = TechnicalIndicators.ema(close, 60)
            
            # MACD
            macd_data = TechnicalIndicators.macd(close)
            indicators.update(macd_data)
            
            # RSI
            indicators["rsi"] = TechnicalIndicators.rsi(close)
            
            # 布林带
            bb_data = TechnicalIndicators.bollinger_bands(close)
            indicators["bb_upper"] = bb_data["upper"]
            indicators["bb_middle"] = bb_data["middle"]
            indicators["bb_lower"] = bb_data["lower"]
            
            # KDJ
            kdj_data = TechnicalIndicators.kdj(high, low, close)
            indicators["kdj_k"] = kdj_data["k"]
            indicators["kdj_d"] = kdj_data["d"]
            indicators["kdj_j"] = kdj_data["j"]
            
            # ATR
            indicators["atr"] = TechnicalIndicators.atr(high, low, close)
            
            # CCI
            indicators["cci"] = TechnicalIndicators.cci(high, low, close)
            
            # Williams %R
            indicators["williams_r"] = TechnicalIndicators.williams_r(high, low, close)
            
            # OBV
            indicators["obv"] = TechnicalIndicators.obv(close, volume)
            
            # 支撑阻力位
            sr_levels = TechnicalIndicators.support_resistance_levels(high, low, close)
            indicators["support_levels"] = sr_levels["support"]
            indicators["resistance_levels"] = sr_levels["resistance"]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}


# 便捷函数
def calculate_indicators_for_kline(kline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    为K线数据计算技术指标
    
    Args:
        kline_data: K线数据列表，每个元素包含open, high, low, close, volume
        
    Returns:
        技术指标字典
    """
    if not kline_data:
        return {}
    
    # 提取OHLCV数据
    high = [float(k.get("high", 0)) for k in kline_data]
    low = [float(k.get("low", 0)) for k in kline_data]
    close = [float(k.get("close", 0)) for k in kline_data]
    volume = [float(k.get("volume", 0)) for k in kline_data]
    
    return TechnicalIndicators.calculate_all_indicators(high, low, close, volume)


def get_latest_indicator_values(indicators: Dict[str, Any]) -> Dict[str, float]:
    """
    获取最新的指标值
    
    Args:
        indicators: 指标数据字典
        
    Returns:
        最新指标值字典
    """
    latest_values = {}
    
    for name, values in indicators.items():
        if isinstance(values, (list, np.ndarray)) and len(values) > 0:
            # 获取最后一个非NaN值
            valid_values = [v for v in values if not np.isnan(v)]
            if valid_values:
                latest_values[name] = float(valid_values[-1])
        elif isinstance(values, list) and name in ["support_levels", "resistance_levels"]:
            latest_values[name] = values
    
    return latest_values 