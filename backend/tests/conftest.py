"""
pytest配置文件
提供测试夹具和配置
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import os
import tempfile

from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.models.user import User
from app.models.trading import Order, Position, Portfolio
from app.models.strategy import Strategy
from app.models.backtest import Backtest
from app.models.market import MarketData
from app.services.market_data_service import MarketDataService
from app.schemas.market_data import TickData, KlineData, MarketDepth
from tests.utils.market_data_generator import MarketDataGenerator
from datetime import datetime, timedelta
from decimal import Decimal


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """模拟用户"""
    user = Mock(spec=User)
    user.id = "test-user-id"
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.permissions = ["read:market_data", "place:order"]
    return user


@pytest.fixture
def mock_strategy():
    """模拟策略"""
    strategy = Mock(spec=Strategy)
    strategy.id = "test-strategy-id"
    strategy.name = "Test Strategy"
    strategy.description = "Test strategy description"
    strategy.code = "# Test strategy code"
    strategy.is_active = True
    return strategy


@pytest.fixture
def mock_order():
    """模拟订单"""
    order = Mock(spec=Order)
    order.id = "test-order-id"
    order.symbol = "000001"
    order.side = "buy"
    order.quantity = 100
    order.price = 10.0
    order.status = "pending"
    return order


@pytest.fixture
def mock_market_data():
    """模拟行情数据"""
    return {
        "symbol": "000001",
        "price": 10.0,
        "volume": 1000,
        "timestamp": "2024-01-01T00:00:00Z",
        "bid": 9.99,
        "ask": 10.01,
        "high": 10.5,
        "low": 9.5,
        "open": 9.8,
        "close": 10.0
    }


@pytest.fixture
def mock_backtest_config():
    """模拟回测配置"""
    return {
        "strategy_id": "test-strategy-id",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "benchmark": "000300",
        "commission": 0.001
    }


# 行情数据测试夹具
@pytest.fixture
async def market_data_service():
    """行情数据服务实例"""
    service = MarketDataService()

    # 重置服务状态
    service.subscribed_symbols.clear()
    service.tick_callbacks.clear()
    service.kline_callbacks.clear()
    service.depth_callbacks.clear()
    service.clients.clear()
    service.client_subscriptions.clear()
    service.tick_cache.clear()
    service.kline_cache.clear()
    service.stats = {
        "tick_count": 0,
        "kline_count": 0,
        "depth_count": 0,
        "error_count": 0,
        "last_update": None
    }

    yield service

    # 清理
    await service.cleanup()


@pytest.fixture
def data_generator():
    """行情数据生成器"""
    generator = MarketDataGenerator()
    yield generator
    # 重置价格
    generator.reset_prices()


@pytest.fixture
def sample_tick_data():
    """示例Tick数据"""
    return TickData(
        symbol="rb2405",
        exchange="SHFE",
        last_price=Decimal("3850.0"),
        bid_price_1=Decimal("3849.0"),
        ask_price_1=Decimal("3851.0"),
        bid_volume_1=100,
        ask_volume_1=150,
        volume=12345,
        turnover=Decimal("47532750.0"),
        open_interest=98765,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_kline_data():
    """示例K线数据"""
    return KlineData(
        symbol="rb2405",
        exchange="SHFE",
        interval="1m",
        open_price=Decimal("3845.0"),
        high_price=Decimal("3855.0"),
        low_price=Decimal("3840.0"),
        close_price=Decimal("3850.0"),
        volume=5000,
        turnover=Decimal("19250000.0"),
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_depth_data():
    """示例深度数据"""
    return MarketDepth(
        symbol="rb2405",
        exchange="SHFE",
        bid_prices=[Decimal("3849.0"), Decimal("3848.0"), Decimal("3847.0")],
        bid_volumes=[100, 200, 150],
        ask_prices=[Decimal("3851.0"), Decimal("3852.0"), Decimal("3853.0")],
        ask_volumes=[150, 180, 120],
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.closed = False
    return mock_ws


@pytest.fixture
def test_symbols():
    """测试用合约列表"""
    return [
        "rb2405", "hc2405", "i2405", "j2405", "jm2405",  # 黑色系
        "cu2405", "al2405", "zn2405",  # 有色金属
        "au2406", "ag2406",  # 贵金属
        "c2405", "m2405", "y2405",  # 农产品
        "MA2405", "TA2405", "PF2405"  # 化工
    ]


@pytest.fixture
def batch_tick_data(data_generator, test_symbols):
    """批量Tick数据"""
    all_ticks = []
    for symbol in test_symbols[:5]:  # 使用前5个合约
        ticks = list(data_generator.generate_tick_stream(symbol, 20))
        all_ticks.extend(ticks)
    return all_ticks


@pytest.fixture
def performance_config():
    """性能测试配置"""
    return {
        "high_frequency_tick_count": 10000,
        "concurrent_client_count": 100,
        "stress_test_duration": 30,  # 秒
        "target_throughput": 5000,  # 条/秒
        "max_latency_ms": 10,
        "max_memory_growth_mb": 100
    }


@pytest.fixture
async def test_redis():
    """测试Redis连接"""
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.hset = AsyncMock()
    mock_redis.hget = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.keys = AsyncMock(return_value=[])

    yield mock_redis


# 测试标记配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests"
    )


# 测试标记
pytest_plugins = ["pytest_asyncio"]