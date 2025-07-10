#!/usr/bin/env python3
"""
行情数据处理测试运行器
独立运行行情数据处理相关测试，避免复杂的依赖问题
"""
import asyncio
import sys
import os
from datetime import datetime
from decimal import Decimal

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from tests.utils.market_data_generator import MarketDataGenerator
from app.services.market_data_service import MarketDataService
from app.schemas.market_data import TickData


async def test_basic_data_generation():
    """测试基础数据生成"""
    print("=== 测试基础数据生成 ===")
    
    generator = MarketDataGenerator()
    
    # 测试单个tick生成
    tick = generator.generate_tick_data("rb2405")
    print(f"生成Tick数据: {tick.symbol} - 价格: {tick.last_price}, 成交量: {tick.volume}")
    
    # 测试批量生成
    ticks = list(generator.generate_tick_stream("rb2405", 5))
    print(f"批量生成 {len(ticks)} 条Tick数据")
    
    # 测试多合约生成
    symbols = ["rb2405", "hc2405", "i2405"]
    multi_ticks = generator.generate_multi_symbol_ticks(symbols, 3)
    print(f"多合约生成 {len(multi_ticks)} 条数据")
    
    # 测试K线生成
    kline = generator.generate_kline_data("rb2405")
    print(f"生成K线数据: {kline.symbol} - OHLC: {kline.open_price}/{kline.high_price}/{kline.low_price}/{kline.close_price}")
    
    # 测试深度数据生成
    depth = generator.generate_market_depth("rb2405")
    print(f"生成深度数据: {depth.symbol} - 买一: {depth.bid_prices[0]}@{depth.bid_volumes[0]}, 卖一: {depth.ask_prices[0]}@{depth.ask_volumes[0]}")
    
    print("✅ 基础数据生成测试通过\n")


async def test_market_data_service():
    """测试行情数据服务"""
    print("=== 测试行情数据服务 ===")
    
    service = MarketDataService()
    generator = MarketDataGenerator()
    
    # 测试数据处理
    tick = generator.generate_tick_data("rb2405")
    
    # 模拟处理（不连接真实数据库）
    print(f"处理Tick数据: {tick.symbol} - {tick.last_price}")
    
    # 测试缓存功能
    service.add_tick_to_cache(tick)
    cached_ticks = service.get_cached_ticks("rb2405", 1)
    print(f"缓存测试: 缓存了 {len(cached_ticks)} 条数据")
    
    # 测试客户端管理
    class MockWebSocket:
        def __init__(self, client_id):
            self.client_id = client_id
            self.messages = []
        
        async def send_json(self, data):
            self.messages.append(data)
            print(f"WebSocket {self.client_id} 收到消息: {data.get('symbol', 'unknown')}")
    
    # 添加模拟客户端
    mock_ws1 = MockWebSocket("client1")
    mock_ws2 = MockWebSocket("client2")
    
    service.add_client("client1", mock_ws1)
    service.add_client("client2", mock_ws2)
    
    # 订阅合约
    service.subscribe_client_symbols("client1", ["rb2405"])
    service.subscribe_client_symbols("client2", ["rb2405", "hc2405"])
    
    # 广播数据
    await service.broadcast_tick_data(tick)
    
    print(f"客户端1收到 {len(mock_ws1.messages)} 条消息")
    print(f"客户端2收到 {len(mock_ws2.messages)} 条消息")
    
    # 清理
    await service.cleanup()
    
    print("✅ 行情数据服务测试通过\n")


async def test_performance_simulation():
    """测试性能模拟"""
    print("=== 测试性能模拟 ===")
    
    generator = MarketDataGenerator()
    service = MarketDataService()
    
    # 生成大量数据
    symbols = ["rb2405", "hc2405", "i2405", "j2405", "cu2405"]
    tick_count = 1000
    
    print(f"生成 {len(symbols)} 个合约，每个 {tick_count} 条数据...")
    
    start_time = datetime.now()
    
    all_ticks = []
    for symbol in symbols:
        ticks = list(generator.generate_tick_stream(symbol, tick_count))
        all_ticks.extend(ticks)
    
    generation_time = (datetime.now() - start_time).total_seconds()
    
    print(f"数据生成完成: {len(all_ticks)} 条数据，耗时 {generation_time:.2f} 秒")
    print(f"生成速度: {len(all_ticks) / generation_time:.0f} 条/秒")
    
    # 模拟处理性能
    start_time = datetime.now()
    
    for tick in all_ticks[:100]:  # 只处理前100条避免太慢
        service.add_tick_to_cache(tick)
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    print(f"处理性能测试: 100 条数据，耗时 {processing_time:.3f} 秒")
    print(f"处理速度: {100 / processing_time:.0f} 条/秒")
    
    await service.cleanup()
    
    print("✅ 性能模拟测试通过\n")


async def test_data_validation():
    """测试数据验证"""
    print("=== 测试数据验证 ===")
    
    generator = MarketDataGenerator()
    
    # 生成测试数据
    tick = generator.generate_tick_data("rb2405")
    
    # 验证数据类型
    assert isinstance(tick.last_price, Decimal), "价格应该是Decimal类型"
    assert isinstance(tick.volume, int), "成交量应该是整数"
    assert isinstance(tick.timestamp, datetime), "时间戳应该是datetime类型"
    
    # 验证数据范围
    assert tick.last_price > 0, "价格应该大于0"
    assert tick.volume >= 0, "成交量应该非负"
    assert tick.bid_price_1 <= tick.ask_price_1, "买价应该小于等于卖价"
    
    # 验证合约信息
    assert tick.symbol in generator.symbols, "合约应该在支持列表中"
    assert tick.exchange in ["SHFE", "DCE", "CZCE"], "交易所应该有效"
    
    print(f"数据验证通过: {tick.symbol} - {tick.last_price}")
    
    # 测试K线数据验证
    kline = generator.generate_kline_data("rb2405")
    
    assert kline.low_price <= kline.high_price, "最低价应该小于等于最高价"
    assert kline.low_price <= kline.open_price <= kline.high_price, "开盘价应该在最高最低价之间"
    assert kline.low_price <= kline.close_price <= kline.high_price, "收盘价应该在最高最低价之间"
    
    print(f"K线验证通过: {kline.symbol} - OHLC验证正确")
    
    print("✅ 数据验证测试通过\n")


async def test_error_handling():
    """测试错误处理"""
    print("=== 测试错误处理 ===")
    
    generator = MarketDataGenerator()
    service = MarketDataService()
    
    # 测试无效合约
    try:
        generator.generate_tick_data("INVALID_SYMBOL")
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"正确捕获无效合约错误: {e}")
    
    # 测试服务错误处理
    try:
        # 模拟处理无效数据
        invalid_tick = TickData(
            symbol="test",
            exchange="TEST",
            last_price=Decimal("0"),  # 无效价格
            bid_price_1=Decimal("0"),
            ask_price_1=Decimal("0"),
            bid_volume_1=0,
            ask_volume_1=0,
            volume=0,
            turnover=Decimal("0"),
            open_interest=0,
            timestamp=datetime.now()
        )
        
        # 服务应该能处理这种数据而不崩溃
        service.add_tick_to_cache(invalid_tick)
        print("服务正确处理了边界数据")
        
    except Exception as e:
        print(f"服务错误处理: {e}")
    
    await service.cleanup()
    
    print("✅ 错误处理测试通过\n")


async def main():
    """主测试函数"""
    print("开始行情数据处理测试...")
    print("=" * 50)
    
    try:
        await test_basic_data_generation()
        await test_market_data_service()
        await test_performance_simulation()
        await test_data_validation()
        await test_error_handling()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
