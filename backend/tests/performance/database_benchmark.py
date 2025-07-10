#!/usr/bin/env python3
"""
数据库性能基准测试
针对高频交易场景的数据库性能测试
"""

import asyncio
import time
import statistics
import psutil
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import random

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.database import get_db_url
from app.models.market import MarketData, Instrument
from app.models.trading import Order, Position, Account
from app.models.ctp import CTPAccount, CTPOrder, CTPPosition

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseBenchmark:
    """数据库性能基准测试"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or get_db_url()
        self.engine = create_engine(
            self.db_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 测试数据配置
        self.test_symbols = ['rb2405', 'hc2405', 'i2405', 'j2405', 'cu2405']
        self.test_data_size = {
            'small': 1000,
            'medium': 10000,
            'large': 100000,
            'xlarge': 1000000
        }
        
        # 性能指标
        self.metrics = {
            'insert_performance': {},
            'query_performance': {},
            'update_performance': {},
            'delete_performance': {},
            'concurrent_performance': {},
            'memory_usage': {},
            'connection_pool': {}
        }

    async def run_benchmark(self) -> Dict[str, Any]:
        """运行完整的基准测试"""
        logger.info("开始数据库性能基准测试...")
        
        start_time = time.time()
        
        # 1. 插入性能测试
        logger.info("测试插入性能...")
        self.metrics['insert_performance'] = await self._test_insert_performance()
        
        # 2. 查询性能测试
        logger.info("测试查询性能...")
        self.metrics['query_performance'] = await self._test_query_performance()
        
        # 3. 更新性能测试
        logger.info("测试更新性能...")
        self.metrics['update_performance'] = await self._test_update_performance()
        
        # 4. 并发性能测试
        logger.info("测试并发性能...")
        self.metrics['concurrent_performance'] = await self._test_concurrent_performance()
        
        # 5. 内存使用测试
        logger.info("测试内存使用...")
        self.metrics['memory_usage'] = await self._test_memory_usage()
        
        # 6. 连接池性能测试
        logger.info("测试连接池性能...")
        self.metrics['connection_pool'] = await self._test_connection_pool()
        
        total_time = time.time() - start_time
        
        # 生成报告
        report = {
            'benchmark_start_time': datetime.now().isoformat(),
            'total_duration': total_time,
            'database_url': self.db_url.split('@')[1] if '@' in self.db_url else self.db_url,
            'metrics': self.metrics,
            'summary': self._generate_summary()
        }
        
        logger.info(f"基准测试完成，总耗时: {total_time:.2f}秒")
        return report

    async def _test_insert_performance(self) -> Dict[str, Any]:
        """测试插入性能"""
        results = {}
        
        for size_name, size in self.test_data_size.items():
            logger.info(f"测试{size_name}数据集插入性能 ({size}条记录)...")
            
            # 测试MarketData插入
            market_data_time = await self._benchmark_market_data_insert(size)
            
            # 测试Order插入
            order_time = await self._benchmark_order_insert(min(size, 10000))  # 订单数据不需要太多
            
            # 测试批量插入
            batch_time = await self._benchmark_batch_insert(size)
            
            results[size_name] = {
                'size': size,
                'market_data_insert': market_data_time,
                'order_insert': order_time,
                'batch_insert': batch_time,
                'throughput_tps': size / market_data_time['duration'] if market_data_time['duration'] > 0 else 0
            }
        
        return results

    async def _benchmark_market_data_insert(self, count: int) -> Dict[str, float]:
        """基准测试MarketData插入"""
        session = self.SessionLocal()
        
        try:
            # 生成测试数据
            test_data = []
            base_price = Decimal('3850.0')
            
            for i in range(count):
                symbol = random.choice(self.test_symbols)
                price_change = Decimal(str(random.uniform(-10, 10)))
                
                market_data = MarketData(
                    symbol=symbol,
                    exchange='SHFE',
                    last_price=base_price + price_change,
                    volume=random.randint(1, 1000),
                    turnover=Decimal(str(random.uniform(1000000, 10000000))),
                    open_interest=random.randint(10000, 100000),
                    timestamp=datetime.now() - timedelta(seconds=i)
                )
                test_data.append(market_data)
            
            # 测试单条插入
            start_time = time.time()
            for data in test_data[:min(100, count)]:  # 只测试前100条单条插入
                session.add(data)
                session.commit()
            single_insert_time = time.time() - start_time
            
            # 测试批量插入
            session.rollback()  # 清理之前的数据
            start_time = time.time()
            session.add_all(test_data)
            session.commit()
            batch_insert_time = time.time() - start_time
            
            return {
                'single_insert_time': single_insert_time,
                'batch_insert_time': batch_insert_time,
                'duration': batch_insert_time,
                'records_per_second': count / batch_insert_time if batch_insert_time > 0 else 0
            }
            
        finally:
            session.close()

    async def _benchmark_order_insert(self, count: int) -> Dict[str, float]:
        """基准测试Order插入"""
        session = self.SessionLocal()
        
        try:
            # 生成测试订单数据
            test_orders = []
            
            for i in range(count):
                order = Order(
                    symbol=random.choice(self.test_symbols),
                    side='buy' if random.random() > 0.5 else 'sell',
                    type='limit',
                    quantity=random.randint(1, 10),
                    price=Decimal(str(random.uniform(3800, 3900))),
                    status='pending',
                    user_id=1,  # 假设用户ID为1
                    created_at=datetime.now()
                )
                test_orders.append(order)
            
            # 批量插入订单
            start_time = time.time()
            session.add_all(test_orders)
            session.commit()
            duration = time.time() - start_time
            
            return {
                'duration': duration,
                'records_per_second': count / duration if duration > 0 else 0
            }
            
        finally:
            session.close()

    async def _benchmark_batch_insert(self, count: int) -> Dict[str, float]:
        """基准测试批量插入"""
        session = self.SessionLocal()
        
        try:
            # 使用原生SQL进行批量插入
            batch_size = 1000
            total_time = 0
            
            for i in range(0, count, batch_size):
                batch_count = min(batch_size, count - i)
                
                # 生成批量插入SQL
                values = []
                for j in range(batch_count):
                    symbol = random.choice(self.test_symbols)
                    price = 3850.0 + random.uniform(-10, 10)
                    volume = random.randint(1, 1000)
                    timestamp = datetime.now() - timedelta(seconds=i+j)
                    
                    values.append(f"('{symbol}', 'SHFE', {price}, {volume}, {random.uniform(1000000, 10000000)}, {random.randint(10000, 100000)}, '{timestamp}')")
                
                sql = f"""
                INSERT INTO market_data (symbol, exchange, last_price, volume, turnover, open_interest, timestamp)
                VALUES {','.join(values)}
                """
                
                start_time = time.time()
                session.execute(text(sql))
                session.commit()
                total_time += time.time() - start_time
            
            return {
                'duration': total_time,
                'records_per_second': count / total_time if total_time > 0 else 0
            }
            
        finally:
            session.close()

    async def _test_query_performance(self) -> Dict[str, Any]:
        """测试查询性能"""
        results = {}
        session = self.SessionLocal()
        
        try:
            # 1. 简单查询测试
            start_time = time.time()
            for _ in range(100):
                symbol = random.choice(self.test_symbols)
                session.query(MarketData).filter(MarketData.symbol == symbol).first()
            simple_query_time = time.time() - start_time
            
            # 2. 复杂查询测试
            start_time = time.time()
            for _ in range(50):
                symbol = random.choice(self.test_symbols)
                end_time = datetime.now()
                start_time_query = end_time - timedelta(hours=1)
                
                session.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timestamp >= start_time_query,
                    MarketData.timestamp <= end_time
                ).order_by(MarketData.timestamp.desc()).limit(100).all()
            complex_query_time = time.time() - start_time
            
            # 3. 聚合查询测试
            start_time = time.time()
            for _ in range(20):
                symbol = random.choice(self.test_symbols)
                session.execute(text(f"""
                    SELECT 
                        AVG(last_price) as avg_price,
                        MAX(last_price) as max_price,
                        MIN(last_price) as min_price,
                        SUM(volume) as total_volume
                    FROM market_data 
                    WHERE symbol = '{symbol}'
                    AND timestamp >= NOW() - INTERVAL '1 hour'
                """)).fetchone()
            aggregation_query_time = time.time() - start_time
            
            # 4. 连接查询测试
            start_time = time.time()
            for _ in range(30):
                session.execute(text("""
                    SELECT o.*, md.last_price
                    FROM orders o
                    LEFT JOIN market_data md ON o.symbol = md.symbol
                    WHERE o.status = 'pending'
                    ORDER BY o.created_at DESC
                    LIMIT 50
                """)).fetchall()
            join_query_time = time.time() - start_time
            
            results = {
                'simple_query': {
                    'total_time': simple_query_time,
                    'avg_time_per_query': simple_query_time / 100,
                    'queries_per_second': 100 / simple_query_time if simple_query_time > 0 else 0
                },
                'complex_query': {
                    'total_time': complex_query_time,
                    'avg_time_per_query': complex_query_time / 50,
                    'queries_per_second': 50 / complex_query_time if complex_query_time > 0 else 0
                },
                'aggregation_query': {
                    'total_time': aggregation_query_time,
                    'avg_time_per_query': aggregation_query_time / 20,
                    'queries_per_second': 20 / aggregation_query_time if aggregation_query_time > 0 else 0
                },
                'join_query': {
                    'total_time': join_query_time,
                    'avg_time_per_query': join_query_time / 30,
                    'queries_per_second': 30 / join_query_time if join_query_time > 0 else 0
                }
            }
            
        finally:
            session.close()
        
        return results

    async def _test_update_performance(self) -> Dict[str, Any]:
        """测试更新性能"""
        results = {}
        session = self.SessionLocal()
        
        try:
            # 1. 单条更新测试
            start_time = time.time()
            for _ in range(100):
                order = session.query(Order).filter(Order.status == 'pending').first()
                if order:
                    order.status = 'filled'
                    session.commit()
            single_update_time = time.time() - start_time
            
            # 2. 批量更新测试
            start_time = time.time()
            session.execute(text("""
                UPDATE orders 
                SET status = 'cancelled' 
                WHERE status = 'pending' 
                AND created_at < NOW() - INTERVAL '1 hour'
            """))
            session.commit()
            batch_update_time = time.time() - start_time
            
            results = {
                'single_update': {
                    'total_time': single_update_time,
                    'avg_time_per_update': single_update_time / 100,
                    'updates_per_second': 100 / single_update_time if single_update_time > 0 else 0
                },
                'batch_update': {
                    'total_time': batch_update_time,
                    'updates_per_second': 1 / batch_update_time if batch_update_time > 0 else 0
                }
            }
            
        finally:
            session.close()
        
        return results

    async def _test_concurrent_performance(self) -> Dict[str, Any]:
        """测试并发性能"""
        results = {}

        # 测试不同并发级别
        concurrency_levels = [1, 5, 10, 20, 50]

        for concurrency in concurrency_levels:
            logger.info(f"测试并发级别: {concurrency}")

            # 并发插入测试
            insert_time = await self._test_concurrent_inserts(concurrency, 100)

            # 并发查询测试
            query_time = await self._test_concurrent_queries(concurrency, 100)

            # 混合操作测试
            mixed_time = await self._test_concurrent_mixed_operations(concurrency, 50)

            results[f'concurrency_{concurrency}'] = {
                'concurrent_inserts': insert_time,
                'concurrent_queries': query_time,
                'mixed_operations': mixed_time
            }

        return results

    async def _test_concurrent_inserts(self, concurrency: int, operations_per_worker: int) -> Dict[str, float]:
        """测试并发插入"""
        async def insert_worker(worker_id: int):
            session = self.SessionLocal()
            try:
                start_time = time.time()
                for i in range(operations_per_worker):
                    market_data = MarketData(
                        symbol=random.choice(self.test_symbols),
                        exchange='SHFE',
                        last_price=Decimal(str(3850.0 + random.uniform(-10, 10))),
                        volume=random.randint(1, 1000),
                        turnover=Decimal(str(random.uniform(1000000, 10000000))),
                        open_interest=random.randint(10000, 100000),
                        timestamp=datetime.now()
                    )
                    session.add(market_data)
                    session.commit()
                return time.time() - start_time
            finally:
                session.close()

        # 启动并发任务
        start_time = time.time()
        tasks = [insert_worker(i) for i in range(concurrency)]
        worker_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        total_operations = concurrency * operations_per_worker

        return {
            'total_time': total_time,
            'avg_worker_time': statistics.mean(worker_times),
            'max_worker_time': max(worker_times),
            'min_worker_time': min(worker_times),
            'operations_per_second': total_operations / total_time if total_time > 0 else 0
        }

    async def _test_concurrent_queries(self, concurrency: int, operations_per_worker: int) -> Dict[str, float]:
        """测试并发查询"""
        async def query_worker(worker_id: int):
            session = self.SessionLocal()
            try:
                start_time = time.time()
                for i in range(operations_per_worker):
                    symbol = random.choice(self.test_symbols)
                    session.query(MarketData).filter(
                        MarketData.symbol == symbol
                    ).order_by(MarketData.timestamp.desc()).limit(10).all()
                return time.time() - start_time
            finally:
                session.close()

        # 启动并发任务
        start_time = time.time()
        tasks = [query_worker(i) for i in range(concurrency)]
        worker_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        total_operations = concurrency * operations_per_worker

        return {
            'total_time': total_time,
            'avg_worker_time': statistics.mean(worker_times),
            'max_worker_time': max(worker_times),
            'min_worker_time': min(worker_times),
            'operations_per_second': total_operations / total_time if total_time > 0 else 0
        }

    async def _test_concurrent_mixed_operations(self, concurrency: int, operations_per_worker: int) -> Dict[str, float]:
        """测试并发混合操作"""
        async def mixed_worker(worker_id: int):
            session = self.SessionLocal()
            try:
                start_time = time.time()
                for i in range(operations_per_worker):
                    operation = random.choice(['insert', 'query', 'update'])

                    if operation == 'insert':
                        market_data = MarketData(
                            symbol=random.choice(self.test_symbols),
                            exchange='SHFE',
                            last_price=Decimal(str(3850.0 + random.uniform(-10, 10))),
                            volume=random.randint(1, 1000),
                            turnover=Decimal(str(random.uniform(1000000, 10000000))),
                            open_interest=random.randint(10000, 100000),
                            timestamp=datetime.now()
                        )
                        session.add(market_data)
                        session.commit()

                    elif operation == 'query':
                        symbol = random.choice(self.test_symbols)
                        session.query(MarketData).filter(
                            MarketData.symbol == symbol
                        ).first()

                    elif operation == 'update':
                        order = session.query(Order).filter(Order.status == 'pending').first()
                        if order:
                            order.status = 'filled'
                            session.commit()

                return time.time() - start_time
            finally:
                session.close()

        # 启动并发任务
        start_time = time.time()
        tasks = [mixed_worker(i) for i in range(concurrency)]
        worker_times = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        total_operations = concurrency * operations_per_worker

        return {
            'total_time': total_time,
            'avg_worker_time': statistics.mean(worker_times),
            'max_worker_time': max(worker_times),
            'min_worker_time': min(worker_times),
            'operations_per_second': total_operations / total_time if total_time > 0 else 0
        }

    async def _test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        process = psutil.Process()

        # 记录初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行大量数据操作
        session = self.SessionLocal()
        try:
            # 查询大量数据
            large_result = session.query(MarketData).limit(10000).all()
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 清理数据
            del large_result

            # 等待垃圾回收
            import gc
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB

        finally:
            session.close()

        return {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': peak_memory - initial_memory,
            'memory_leak_mb': final_memory - initial_memory
        }

    async def _test_connection_pool(self) -> Dict[str, Any]:
        """测试连接池性能"""
        results = {}

        # 测试连接池获取时间
        connection_times = []

        for _ in range(100):
            start_time = time.time()
            session = self.SessionLocal()
            session.execute(text("SELECT 1"))
            session.close()
            connection_times.append(time.time() - start_time)

        # 测试连接池耗尽情况
        sessions = []
        try:
            start_time = time.time()
            # 尝试获取超过池大小的连接
            for i in range(25):  # 超过pool_size=20
                session = self.SessionLocal()
                sessions.append(session)
            pool_exhaustion_time = time.time() - start_time
        except Exception as e:
            pool_exhaustion_time = -1
            logger.warning(f"连接池测试异常: {e}")
        finally:
            for session in sessions:
                session.close()

        results = {
            'avg_connection_time': statistics.mean(connection_times),
            'max_connection_time': max(connection_times),
            'min_connection_time': min(connection_times),
            'connection_time_std': statistics.stdev(connection_times) if len(connection_times) > 1 else 0,
            'pool_exhaustion_time': pool_exhaustion_time,
            'pool_size': 20,
            'max_overflow': 30
        }

        return results

    def _generate_summary(self) -> Dict[str, Any]:
        """生成性能摘要"""
        summary = {
            'overall_performance': 'UNKNOWN',
            'bottlenecks': [],
            'recommendations': [],
            'key_metrics': {}
        }

        # 分析插入性能
        insert_metrics = self.metrics.get('insert_performance', {})
        if insert_metrics:
            large_insert = insert_metrics.get('large', {})
            if large_insert.get('throughput_tps', 0) < 1000:
                summary['bottlenecks'].append('插入性能低于1000 TPS')
                summary['recommendations'].append('优化批量插入策略')

        # 分析查询性能
        query_metrics = self.metrics.get('query_performance', {})
        if query_metrics:
            simple_query = query_metrics.get('simple_query', {})
            if simple_query.get('avg_time_per_query', 0) > 0.1:
                summary['bottlenecks'].append('简单查询平均响应时间超过100ms')
                summary['recommendations'].append('添加数据库索引')

        # 分析并发性能
        concurrent_metrics = self.metrics.get('concurrent_performance', {})
        if concurrent_metrics:
            high_concurrency = concurrent_metrics.get('concurrency_50', {})
            if high_concurrency:
                insert_ops = high_concurrency.get('concurrent_inserts', {}).get('operations_per_second', 0)
                if insert_ops < 500:
                    summary['bottlenecks'].append('高并发插入性能不足')
                    summary['recommendations'].append('优化连接池配置')

        # 分析内存使用
        memory_metrics = self.metrics.get('memory_usage', {})
        if memory_metrics:
            memory_leak = memory_metrics.get('memory_leak_mb', 0)
            if memory_leak > 50:
                summary['bottlenecks'].append('存在内存泄漏')
                summary['recommendations'].append('检查会话管理和对象生命周期')

        # 确定整体性能等级
        if len(summary['bottlenecks']) == 0:
            summary['overall_performance'] = 'EXCELLENT'
        elif len(summary['bottlenecks']) <= 2:
            summary['overall_performance'] = 'GOOD'
        elif len(summary['bottlenecks']) <= 4:
            summary['overall_performance'] = 'FAIR'
        else:
            summary['overall_performance'] = 'POOR'

        # 关键指标
        if insert_metrics and query_metrics:
            summary['key_metrics'] = {
                'max_insert_tps': max([v.get('throughput_tps', 0) for v in insert_metrics.values() if isinstance(v, dict)]),
                'avg_query_time_ms': query_metrics.get('simple_query', {}).get('avg_time_per_query', 0) * 1000,
                'max_concurrent_ops_per_sec': max([
                    v.get('concurrent_inserts', {}).get('operations_per_second', 0)
                    for v in concurrent_metrics.values() if isinstance(v, dict)
                ]) if concurrent_metrics else 0
            }

        return summary


async def main():
    """主函数"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="数据库性能基准测试")
    parser.add_argument("--db-url", help="数据库连接URL")
    parser.add_argument("--output", default="database_benchmark_report.json", help="输出文件")

    args = parser.parse_args()

    # 创建基准测试器
    benchmark = DatabaseBenchmark(args.db_url)

    # 运行测试
    results = await benchmark.run_benchmark()

    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"基准测试完成，结果已保存到 {args.output}")

    # 打印摘要
    summary = results.get('summary', {})
    print(f"\n=== 数据库性能基准测试摘要 ===")
    print(f"整体性能等级: {summary.get('overall_performance', 'UNKNOWN')}")
    print(f"发现瓶颈: {len(summary.get('bottlenecks', []))}")

    key_metrics = summary.get('key_metrics', {})
    if key_metrics:
        print(f"最大插入TPS: {key_metrics.get('max_insert_tps', 0):.2f}")
        print(f"平均查询时间: {key_metrics.get('avg_query_time_ms', 0):.2f}ms")
        print(f"最大并发操作/秒: {key_metrics.get('max_concurrent_ops_per_sec', 0):.2f}")

    if summary.get('bottlenecks'):
        print("\n性能瓶颈:")
        for bottleneck in summary['bottlenecks']:
            print(f"  - {bottleneck}")

    if summary.get('recommendations'):
        print("\n优化建议:")
        for recommendation in summary['recommendations']:
            print(f"  - {recommendation}")


if __name__ == "__main__":
    asyncio.run(main())
