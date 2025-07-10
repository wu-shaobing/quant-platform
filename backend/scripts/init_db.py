#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表结构并插入基础数据
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import Base
from app.models.user import User
from app.models.market import Symbol, MarketType
from app.models.trading import Account
from app.models.strategy import Strategy, StrategyStatus
from app.models.backtest import BacktestResult
from app.core.security import SecurityManager
from app.utils.helpers import generate_uuid

settings = get_settings()


async def create_tables():
    """创建所有数据库表"""
    print("Creating database tables...")
    
    # 强制使用SQLite进行开发
    db_url = "sqlite+aiosqlite:///./quant_dev.db"
    engine = create_async_engine(
        db_url,
        echo=True if settings.DEBUG else False
    )
    
    async with engine.begin() as conn:
        # 删除所有表（谨慎使用）
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✓ Database tables created successfully")


async def create_admin_user():
    """创建管理员用户"""
    print("Creating admin user...")
    
    db_url = "sqlite+aiosqlite:///./quant_dev.db"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 检查是否已存在管理员
        result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE email = :email"),
            {"email": "admin@quantplatform.com"}
        )
        count = result.scalar()
        
        if count == 0:
            admin_user = User(
                username="admin",
                email="admin@quantplatform.com",
                full_name="系统管理员",
                hashed_password=SecurityManager().hash_password("admin123456"),
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            session.add(admin_user)
            
            await session.flush()  # 确保admin_user.id被生成
            
            # 创建管理员账户
            admin_account = Account(
                id=generate_uuid(),
                user_id=admin_user.id,
                account_id="ADMIN001",
                account_name="管理员账户",
                total_assets=1000000.0,
                available_cash=1000000.0,
                frozen_cash=0.0,
                account_type="demo"
            )
            session.add(admin_account)
            
            await session.commit()
            print("✓ Admin user created: admin@quantplatform.com / admin123456")
        else:
            print("✓ Admin user already exists")
    
    await engine.dispose()


async def create_sample_symbols():
    """创建示例交易标的"""
    print("Creating sample symbols...")
    
    db_url = "sqlite+aiosqlite:///./quant_dev.db"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 检查是否已有数据
        result = await session.execute(text("SELECT COUNT(*) FROM symbols"))
        count = result.scalar()
        
        if count == 0:
            # 股票示例
            stock_symbols = [
                ("000001", "平安银行", "SZSE", "金融", "银行"),
                ("000002", "万科A", "SZSE", "房地产", "房地产开发"),
                ("600000", "浦发银行", "SSE", "金融", "银行"),
                ("600036", "招商银行", "SSE", "金融", "银行"),
                ("600519", "贵州茅台", "SSE", "消费", "白酒"),
                ("000858", "五粮液", "SZSE", "消费", "白酒"),
                ("300015", "爱尔眼科", "SZSE", "医疗", "医疗服务"),
                ("002415", "海康威视", "SZSE", "科技", "安防设备"),
            ]
            
            for code, name, exchange, sector, industry in stock_symbols:
                symbol = Symbol(
                    id=generate_uuid(),
                    code=code,
                    name=name,
                    market_type=MarketType.STOCK,
                    exchange=exchange,
                    sector=sector,
                    industry=industry,
                    currency="CNY",
                    lot_size=100,
                    tick_size=0.01,
                    is_active=True,
                    is_tradable=True
                )
                session.add(symbol)
            
            # 期货示例
            futures_symbols = [
                ("rb2501", "螺纹钢2501", "SHFE", "黑色金属", "建材"),
                ("hc2501", "热卷2501", "SHFE", "黑色金属", "建材"),
                ("i2501", "铁矿石2501", "DCE", "黑色金属", "原材料"),
                ("j2501", "焦炭2501", "DCE", "能源", "焦炭"),
                ("jm2501", "焦煤2501", "DCE", "能源", "焦煤"),
                ("cu2501", "沪铜2501", "SHFE", "有色金属", "铜"),
                ("al2501", "沪铝2501", "SHFE", "有色金属", "铝"),
                ("zn2501", "沪锌2501", "SHFE", "有色金属", "锌"),
            ]
            
            for code, name, exchange, sector, industry in futures_symbols:
                symbol = Symbol(
                    id=generate_uuid(),
                    code=code,
                    name=name,
                    market_type=MarketType.FUTURES,
                    exchange=exchange,
                    sector=sector,
                    industry=industry,
                    currency="CNY",
                    lot_size=1,
                    tick_size=1.0,
                    is_active=True,
                    is_tradable=True
                )
                session.add(symbol)
            
            await session.commit()
            print(f"✓ Created {len(stock_symbols) + len(futures_symbols)} sample symbols")
        else:
            print("✓ Sample symbols already exist")
    
    await engine.dispose()


async def create_sample_strategies():
    """创建示例策略"""
    print("Creating sample strategies...")
    
    db_url = "sqlite+aiosqlite:///./quant_dev.db"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 获取管理员用户ID
        result = await session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": "admin@quantplatform.com"}
        )
        admin_id = result.scalar()
        
        if admin_id:
            # 检查是否已有策略
            result = await session.execute(text("SELECT COUNT(*) FROM strategies"))
            count = result.scalar()
            
            if count == 0:
                strategies = [
                    {
                        "name": "双均线策略",
                        "description": "基于5日和20日移动平均线的经典趋势跟踪策略",
                        "code": """
def strategy_logic(data):
    # 计算移动平均线
    data['ma5'] = data['close'].rolling(5).mean()
    data['ma20'] = data['close'].rolling(20).mean()
    
    # 生成交易信号
    data['signal'] = 0
    data.loc[data['ma5'] > data['ma20'], 'signal'] = 1  # 买入信号
    data.loc[data['ma5'] < data['ma20'], 'signal'] = -1  # 卖出信号
    
    return data
""",
                        "parameters": {
                            "short_period": 5,
                            "long_period": 20,
                            "stop_loss": 0.05,
                            "take_profit": 0.1
                        }
                    },
                    {
                        "name": "RSI均值回归策略",
                        "description": "基于RSI指标的均值回归策略，在超买超卖区域进行反向操作",
                        "code": """
def strategy_logic(data):
    # 计算RSI
    data['rsi'] = calculate_rsi(data['close'], 14)
    
    # 生成交易信号
    data['signal'] = 0
    data.loc[data['rsi'] < 30, 'signal'] = 1   # 超卖买入
    data.loc[data['rsi'] > 70, 'signal'] = -1  # 超买卖出
    
    return data
""",
                        "parameters": {
                            "rsi_period": 14,
                            "oversold_level": 30,
                            "overbought_level": 70,
                            "position_size": 0.1
                        }
                    },
                    {
                        "name": "布林带突破策略",
                        "description": "基于布林带的突破策略，在价格突破上下轨时进行交易",
                        "code": """
def strategy_logic(data):
    # 计算布林带
    data['bb_upper'], data['bb_middle'], data['bb_lower'] = calculate_bollinger_bands(data['close'], 20, 2)
    
    # 生成交易信号
    data['signal'] = 0
    data.loc[data['close'] > data['bb_upper'], 'signal'] = 1   # 突破上轨买入
    data.loc[data['close'] < data['bb_lower'], 'signal'] = -1  # 跌破下轨卖出
    
    return data
""",
                        "parameters": {
                            "bb_period": 20,
                            "bb_std": 2.0,
                            "breakout_threshold": 0.01,
                            "max_position": 0.2
                        }
                    }
                ]
                
                for strategy_data in strategies:
                    strategy = Strategy(
                        id=generate_uuid(),
                        user_id=admin_id,
                        name=strategy_data["name"],
                        description=strategy_data["description"],
                        code=strategy_data["code"],
                        parameters=strategy_data["parameters"],
                        status=StrategyStatus.DRAFT,
                        is_active=True
                    )
                    session.add(strategy)
                
                await session.commit()
                print(f"✓ Created {len(strategies)} sample strategies")
            else:
                print("✓ Sample strategies already exist")
        else:
            print("✗ Admin user not found, skipping strategy creation")
    
    await engine.dispose()


async def create_indexes():
    """创建数据库索引"""
    print("Creating database indexes...")
    
    db_url = "sqlite+aiosqlite:///./quant_dev.db"
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        # 市场数据索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp 
            ON market_data(symbol_code, timestamp DESC)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_kline_data_symbol_type_date 
            ON kline_data(symbol_code, kline_type, trading_date DESC)
        """))
        
        # 交易数据索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_orders_user_status 
            ON orders(user_id, status, submit_time DESC)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_trades_user_time 
            ON trades(user_id, trade_time DESC)
        """))
        
        # 策略数据索引
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_strategies_user_status 
            ON strategies(user_id, status, created_at DESC)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy 
            ON backtest_results(strategy_id, created_at DESC)
        """))
    
    await engine.dispose()
    print("✓ Database indexes created successfully")


async def main():
    """主函数"""
    print("🚀 Initializing Quant Platform Database...")
    print("=" * 50)
    
    try:
        # 1. 创建表结构
        await create_tables()
        
        # 2. 创建索引
        await create_indexes()
        
        # 3. 创建管理员用户
        await create_admin_user()
        
        # 4. 创建示例数据
        await create_sample_symbols()
        await create_sample_strategies()
        
        print("=" * 50)
        print("✅ Database initialization completed successfully!")
        print("\n📋 Default Login Credentials:")
        print("   Email: admin@quantplatform.com")
        print("   Password: admin123456")
        print("\n🔗 API Documentation: http://localhost:8000/docs")
        print("🔗 Health Check: http://localhost:8000/health")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())