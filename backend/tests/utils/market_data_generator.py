"""
行情数据生成器
用于测试的模拟行情数据生成工具
"""
import random
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Generator, AsyncGenerator
import math

from app.schemas.market_data import TickData, KlineData, MarketDepth


class MarketDataGenerator:
    """行情数据生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.symbols = [
            "rb2405", "hc2405", "i2405", "j2405", "jm2405",  # 黑色系
            "cu2405", "al2405", "zn2405", "pb2405", "ni2405",  # 有色金属
            "au2406", "ag2406",  # 贵金属
            "c2405", "m2405", "y2405", "p2405", "a2405",  # 农产品
            "MA2405", "TA2405", "PF2405", "PP2405", "V2405"  # 化工
        ]
        
        # 基础价格配置
        self.base_prices = {
            "rb2405": Decimal("3850.0"),
            "hc2405": Decimal("3650.0"),
            "i2405": Decimal("850.0"),
            "j2405": Decimal("2450.0"),
            "jm2405": Decimal("1650.0"),
            "cu2405": Decimal("68500.0"),
            "al2405": Decimal("18500.0"),
            "zn2405": Decimal("22500.0"),
            "pb2405": Decimal("16500.0"),
            "ni2405": Decimal("125000.0"),
            "au2406": Decimal("485.0"),
            "ag2406": Decimal("5850.0"),
            "c2405": Decimal("2850.0"),
            "m2405": Decimal("3150.0"),
            "y2405": Decimal("8500.0"),
            "p2405": Decimal("3250.0"),
            "a2405": Decimal("3950.0"),
            "MA2405": Decimal("2650.0"),
            "TA2405": Decimal("5850.0"),
            "PF2405": Decimal("7250.0"),
            "PP2405": Decimal("7850.0"),
            "V2405": Decimal("6850.0")
        }
        
        # 波动率配置
        self.volatility = {
            symbol: random.uniform(0.01, 0.05) for symbol in self.symbols
        }
        
        # 当前价格状态
        self.current_prices = self.base_prices.copy()
        
        # 交易所映射
        self.exchanges = {
            "rb2405": "SHFE", "hc2405": "SHFE", "cu2405": "SHFE",
            "al2405": "SHFE", "zn2405": "SHFE", "pb2405": "SHFE",
            "ni2405": "SHFE", "au2406": "SHFE", "ag2406": "SHFE",
            "i2405": "DCE", "j2405": "DCE", "jm2405": "DCE",
            "c2405": "DCE", "m2405": "DCE", "y2405": "DCE",
            "p2405": "DCE", "a2405": "DCE", "V2405": "DCE",
            "MA2405": "CZCE", "TA2405": "CZCE", "PF2405": "CZCE",
            "PP2405": "CZCE"
        }

    def generate_tick_data(self, symbol: str, timestamp: datetime = None) -> TickData:
        """生成单个Tick数据"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.current_prices:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        # 价格随机游走
        base_price = self.current_prices[symbol]
        volatility = self.volatility[symbol]
        
        # 使用几何布朗运动模拟价格变化
        dt = 1.0 / (24 * 60 * 60)  # 1秒的时间步长
        random_factor = random.gauss(0, 1)
        price_change = float(base_price) * volatility * math.sqrt(dt) * random_factor

        new_price = base_price + Decimal(str(price_change))
        self.current_prices[symbol] = new_price
        
        # 生成买卖价差
        spread_ratio = random.uniform(0.0001, 0.001)
        spread = new_price * Decimal(str(spread_ratio))

        bid_price = new_price - spread / Decimal('2')
        ask_price = new_price + spread / Decimal('2')
        
        # 生成成交量
        base_volume = random.randint(1, 1000)
        volume_multiplier = random.uniform(0.5, 2.0)
        volume = int(base_volume * volume_multiplier)
        
        # 生成其他字段
        bid_volume = random.randint(10, 500)
        ask_volume = random.randint(10, 500)
        open_interest = random.randint(10000, 100000)
        
        return TickData(
            symbol=symbol,
            exchange=self.exchanges[symbol],
            last_price=new_price.quantize(Decimal('0.1')),
            bid_price_1=bid_price.quantize(Decimal('0.1')),
            ask_price_1=ask_price.quantize(Decimal('0.1')),
            bid_volume_1=bid_volume,
            ask_volume_1=ask_volume,
            volume=volume,
            turnover=new_price * Decimal(str(volume)),
            open_interest=open_interest,
            timestamp=timestamp
        )

    def generate_tick_stream(self, symbol: str, count: int, 
                           interval_ms: int = 100) -> Generator[TickData, None, None]:
        """生成Tick数据流"""
        start_time = datetime.now()
        
        for i in range(count):
            timestamp = start_time + timedelta(milliseconds=i * interval_ms)
            yield self.generate_tick_data(symbol, timestamp)

    async def generate_async_tick_stream(self, symbol: str, count: int,
                                       interval_ms: int = 100) -> AsyncGenerator[TickData, None]:
        """生成异步Tick数据流"""
        start_time = datetime.now()
        
        for i in range(count):
            timestamp = start_time + timedelta(milliseconds=i * interval_ms)
            tick_data = self.generate_tick_data(symbol, timestamp)
            yield tick_data
            
            # 模拟实时延迟
            await asyncio.sleep(interval_ms / 1000.0)

    def generate_multi_symbol_ticks(self, symbols: List[str], count_per_symbol: int) -> List[TickData]:
        """生成多合约Tick数据"""
        all_ticks = []
        base_time = datetime.now()
        
        for symbol in symbols:
            for i in range(count_per_symbol):
                timestamp = base_time + timedelta(milliseconds=i * 50)  # 每50ms一个tick
                tick_data = self.generate_tick_data(symbol, timestamp)
                all_ticks.append(tick_data)
        
        # 按时间排序模拟真实市场数据
        all_ticks.sort(key=lambda x: x.timestamp)
        return all_ticks

    def generate_kline_data(self, symbol: str, interval: str = "1m", 
                          timestamp: datetime = None) -> KlineData:
        """生成K线数据"""
        if timestamp is None:
            timestamp = datetime.now()
        
        base_price = self.current_prices.get(symbol, self.base_prices[symbol])
        
        # 生成OHLC价格
        volatility = self.volatility[symbol]
        price_range = base_price * Decimal(str(volatility * 10))
        
        open_price = base_price + Decimal(str(random.uniform(-float(price_range), float(price_range))))
        close_price = open_price + Decimal(str(random.uniform(-float(price_range), float(price_range))))
        
        high_price = max(open_price, close_price) + Decimal(str(random.uniform(0, float(price_range))))
        low_price = min(open_price, close_price) - Decimal(str(random.uniform(0, float(price_range))))
        
        # 生成成交量
        volume = random.randint(1000, 50000)
        avg_price = (high_price + low_price) / Decimal('2')
        turnover = avg_price * Decimal(str(volume))
        
        return KlineData(
            symbol=symbol,
            exchange=self.exchanges[symbol],
            interval=interval,
            open_price=open_price.quantize(Decimal('0.1')),
            high_price=high_price.quantize(Decimal('0.1')),
            low_price=low_price.quantize(Decimal('0.1')),
            close_price=close_price.quantize(Decimal('0.1')),
            volume=volume,
            turnover=turnover.quantize(Decimal('0.01')),
            timestamp=timestamp
        )

    def generate_market_depth(self, symbol: str, levels: int = 5,
                            timestamp: datetime = None) -> MarketDepth:
        """生成市场深度数据"""
        if timestamp is None:
            timestamp = datetime.now()
        
        base_price = self.current_prices.get(symbol, self.base_prices[symbol])
        
        # 生成买卖价格和数量
        bid_prices = []
        bid_volumes = []
        ask_prices = []
        ask_volumes = []
        
        # 买方深度
        for i in range(levels):
            price_offset = Decimal(str((i + 1) * random.uniform(0.1, 1.0)))
            bid_price = base_price - price_offset
            bid_volume = random.randint(10, 1000)
            
            bid_prices.append(bid_price.quantize(Decimal('0.1')))
            bid_volumes.append(bid_volume)
        
        # 卖方深度
        for i in range(levels):
            price_offset = Decimal(str((i + 1) * random.uniform(0.1, 1.0)))
            ask_price = base_price + price_offset
            ask_volume = random.randint(10, 1000)
            
            ask_prices.append(ask_price.quantize(Decimal('0.1')))
            ask_volumes.append(ask_volume)
        
        return MarketDepth(
            symbol=symbol,
            exchange=self.exchanges[symbol],
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            timestamp=timestamp
        )

    def generate_realistic_trading_session(self, symbols: List[str], 
                                         duration_minutes: int = 60) -> List[TickData]:
        """生成真实交易时段的数据"""
        all_ticks = []
        start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # 模拟不同时段的活跃度
        for minute in range(duration_minutes):
            current_time = start_time + timedelta(minutes=minute)
            
            # 开盘和收盘时段更活跃
            if minute < 10 or minute > duration_minutes - 10:
                tick_frequency = 20  # 每分钟20个tick
            else:
                tick_frequency = random.randint(5, 15)  # 正常时段
            
            for symbol in symbols:
                for tick_idx in range(tick_frequency):
                    tick_time = current_time + timedelta(seconds=tick_idx * (60 // tick_frequency))
                    tick_data = self.generate_tick_data(symbol, tick_time)
                    all_ticks.append(tick_data)
        
        # 按时间排序
        all_ticks.sort(key=lambda x: x.timestamp)
        return all_ticks

    def reset_prices(self):
        """重置价格到基础价格"""
        self.current_prices = self.base_prices.copy()

    def set_volatility(self, symbol: str, volatility: float):
        """设置特定合约的波动率"""
        if symbol in self.symbols:
            self.volatility[symbol] = volatility

    def get_current_price(self, symbol: str) -> Decimal:
        """获取当前价格"""
        return self.current_prices.get(symbol, self.base_prices.get(symbol))


# 便捷函数
def create_test_tick_data(symbol: str = "rb2405", count: int = 100) -> List[TickData]:
    """创建测试用的Tick数据"""
    generator = MarketDataGenerator()
    return list(generator.generate_tick_stream(symbol, count))


def create_test_kline_data(symbol: str = "rb2405", count: int = 60) -> List[KlineData]:
    """创建测试用的K线数据"""
    generator = MarketDataGenerator()
    klines = []
    base_time = datetime.now().replace(second=0, microsecond=0)
    
    for i in range(count):
        timestamp = base_time + timedelta(minutes=i)
        kline = generator.generate_kline_data(symbol, "1m", timestamp)
        klines.append(kline)
    
    return klines


async def create_realtime_tick_stream(symbol: str, duration_seconds: int = 60):
    """创建实时Tick数据流"""
    generator = MarketDataGenerator()
    end_time = datetime.now() + timedelta(seconds=duration_seconds)
    
    while datetime.now() < end_time:
        tick_data = generator.generate_tick_data(symbol)
        yield tick_data
        await asyncio.sleep(random.uniform(0.1, 0.5))  # 随机间隔
