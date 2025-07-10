#!/usr/bin/env python3
"""
种子数据生成脚本
生成测试用的市场数据、K线数据等
"""
import asyncio
import sys
import random
from datetime import datetime, timedelta, date
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

from app.core.config import get_settings
from app.models.market import Symbol, MarketData, KLineData, KLineType
from app.utils.helpers import generate_uuid, is_trading_day

settings = get_settings()


class MarketDataGenerator:
    """市场数据生成器"""
    
    def __init__(self):
        self.base_prices = {
            "000001": 12.50,  # 平安银行
            "000002": 18.30,  # 万科A
            "600000": 8.90,   # 浦发银行
            "600036": 35.60,  # 招商银行
            "600519": 1680.0, # 贵州茅台
            "000858": 155.0,  # 五粮液
            "300015": 42.80,  # 爱尔眼科
            "002415": 28.90,  # 海康威视
            "rb2501": 3450.0, # 螺纹钢
            "hc2501": 3200.0, # 热卷
            "i2501": 780.0,   # 铁矿石
            "j2501": 2100.0,  # 焦炭
            "jm2501": 1350.0, # 焦煤
            "cu2501": 72500.0, # 沪铜
            "al2501": 19800.0, # 沪铝
            "zn2501": 25200.0, # 沪锌
        }
    
    def generate_price_movement(self, base_price: float, volatility: float = 0.02) -> float:
        """生成价格变动"""
        change_percent = random.gauss(0, volatility)
        return base_price * (1 + change_percent)
    
    def generate_volume(self, symbol_code: str) -> int:
        """生成成交量"""
        if symbol_code.startswith(("rb", "hc", "i", "j", "cu", "al", "zn")):
            # 期货
            return random.randint(10000, 100000)
        else:
            # 股票
            return random.randint(100000, 5000000)
    
    def generate_kline_data(self, symbol_code: str, start_date: date, 
                          end_date: date, kline_type: KLineType) -> list:
        """生成K线数据"""
        klines = []
        base_price = self.base_prices.get(symbol_code, 100.0)
        current_price = base_price
        
        current_date = start_date
        while current_date <= end_date:
            if not is_trading_day(current_date):
                current_date += timedelta(days=1)
                continue
            
            # 生成当日数据
            if kline_type == KLineType.DAY_1:
                # 日线数据
                open_price = current_price
                high_price = open_price * random.uniform(1.0, 1.05)
                low_price = open_price * random.uniform(0.95, 1.0)
                close_price = random.uniform(low_price, high_price)
                volume = self.generate_volume(symbol_code)
                
                kline = KLineData(
                    id=generate_uuid(),
                    symbol_code=symbol_code,
                    kline_type=kline_type,
                    open_price=Decimal(str(round(open_price, 2))),
                    high_price=Decimal(str(round(high_price, 2))),
                    low_price=Decimal(str(round(low_price, 2))),
                    close_price=Decimal(str(round(close_price, 2))),
                    volume=volume,
                    turnover=Decimal(str(round(volume * close_price, 2))),
                    change=Decimal(str(round(close_price - open_price, 2))),
                    change_percent=Decimal(str(round((close_price - open_price) / open_price * 100, 2))),
                    amplitude=Decimal(str(round((high_price - low_price) / open_price * 100, 2))),
                    trading_date=datetime.combine(current_date, datetime.min.time()),
                    period_start=datetime.combine(current_date, datetime.min.time()),
                    period_end=datetime.combine(current_date, datetime.min.time().replace(hour=15))
                )
                klines.append(kline)
                current_price = close_price
            
            current_date += timedelta(days=1)
        
        return klines
    
    def generate_market_data(self, symbol_code: str) -> MarketData:
        """生成实时行情数据"""
        base_price = self.base_prices.get(symbol_code, 100.0)
        
        # 生成价格数据
        last_price = self.generate_price_movement(base_price)
        pre_close = base_price
        open_price = self.generate_price_movement(pre_close, 0.01)
        high_price = max(open_price, last_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, last_price) * random.uniform(0.98, 1.0)
        
        # 生成买卖盘
        bid_price = last_price * random.uniform(0.998, 0.9995)
        ask_price = last_price * random.uniform(1.0005, 1.002)
        
        volume = self.generate_volume(symbol_code)
        turnover = volume * last_price
        
        change = last_price - pre_close
        change_percent = (change / pre_close) * 100
        
        market_data = MarketData(
            id=generate_uuid(),
            symbol_code=symbol_code,
            last_price=Decimal(str(round(last_price, 2))),
            open_price=Decimal(str(round(open_price, 2))),
            high_price=Decimal(str(round(high_price, 2))),
            low_price=Decimal(str(round(low_price, 2))),
            pre_close=Decimal(str(round(pre_close, 2))),
            volume=volume,
            turnover=Decimal(str(round(turnover, 2))),
            bid_price=Decimal(str(round(bid_price, 2))),
            bid_volume=random.randint(100, 10000),
            ask_price=Decimal(str(round(ask_price, 2))),
            ask_volume=random.randint(100, 10000),
            change=Decimal(str(round(change, 2))),
            change_percent=Decimal(str(round(change_percent, 2))),
            trading_date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
            timestamp=datetime.now()
        )
        
        return market_data


async def generate_historical_kline_data():
    """生成历史K线数据"""
    print("Generating historical K-line data...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取所有标的
        result = await session.execute(select(Symbol))
        symbols = result.scalars().all()
        
        if not symbols:
            print("No symbols found, please run init_db.py first")
            return
        
        generator = MarketDataGenerator()
        
        # 生成最近1年的日线数据
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        total_records = 0
        
        for symbol in symbols:
            print(f"Generating K-line data for {symbol.code}...")
            
            # 检查是否已有数据
            existing_result = await session.execute(
                text("SELECT COUNT(*) FROM kline_data WHERE symbol_code = :code"),
                {"code": symbol.code}
            )
            existing_count = existing_result.scalar()
            
            if existing_count > 0:
                print(f"  ✓ K-line data already exists for {symbol.code}")
                continue
            
            # 生成日线数据
            klines = generator.generate_kline_data(
                symbol.code, start_date, end_date, KLineType.DAY_1
            )
            
            for kline in klines:
                session.add(kline)
            
            total_records += len(klines)
            print(f"  ✓ Generated {len(klines)} daily K-line records")
        
        await session.commit()
        print(f"✓ Total {total_records} K-line records generated")
    
    await engine.dispose()


async def generate_current_market_data():
    """生成当前行情数据"""
    print("Generating current market data...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取所有标的
        result = await session.execute(select(Symbol))
        symbols = result.scalars().all()
        
        if not symbols:
            print("No symbols found, please run init_db.py first")
            return
        
        generator = MarketDataGenerator()
        
        for symbol in symbols:
            print(f"Generating market data for {symbol.code}...")
            
            # 删除现有数据
            await session.execute(
                text("DELETE FROM market_data WHERE symbol_code = :code"),
                {"code": symbol.code}
            )
            
            # 生成新的行情数据
            market_data = generator.generate_market_data(symbol.code)
            session.add(market_data)
        
        await session.commit()
        print(f"✓ Market data generated for {len(symbols)} symbols")
    
    await engine.dispose()


async def update_symbol_prices():
    """更新标的价格限制"""
    print("Updating symbol price limits...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(Symbol))
        symbols = result.scalars().all()
        
        generator = MarketDataGenerator()
        
        for symbol in symbols:
            base_price = generator.base_prices.get(symbol.code, 100.0)
            
            # 计算涨跌停价格（股票10%，期货5%）
            if symbol.market_type.value == "stock":
                limit_ratio = 0.1
            else:
                limit_ratio = 0.05
            
            symbol.price_limit_up = Decimal(str(round(base_price * (1 + limit_ratio), 2)))
            symbol.price_limit_down = Decimal(str(round(base_price * (1 - limit_ratio), 2)))
        
        await session.commit()
        print(f"✓ Price limits updated for {len(symbols)} symbols")
    
    await engine.dispose()


async def main():
    """主函数"""
    print("🌱 Generating seed data for Quant Platform...")
    print("=" * 50)
    
    try:
        # 1. 更新标的价格限制
        await update_symbol_prices()
        
        # 2. 生成历史K线数据
        await generate_historical_kline_data()
        
        # 3. 生成当前行情数据
        await generate_current_market_data()
        
        print("=" * 50)
        print("✅ Seed data generation completed successfully!")
        print("\n📊 Generated Data:")
        print("   - Historical K-line data (1 year)")
        print("   - Current market data")
        print("   - Price limits for all symbols")
        print("\n🔗 You can now test the market data APIs")
        
    except Exception as e:
        print(f"❌ Seed data generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())