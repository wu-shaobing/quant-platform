#!/usr/bin/env python3
"""
CTP性能优化脚本
用于执行数据库优化、缓存预热、索引创建等性能优化任务
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import database_manager, get_db
from app.core.cache import cache_manager
from app.core.performance_optimizer import performance_optimizer
from app.core.ctp_performance_config import (
    CTPPerformanceConfig, 
    OptimizationLevel,
    default_performance_config,
    hft_performance_config
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_database_indexes():
    """创建数据库优化索引"""
    logger.info("开始创建数据库优化索引...")
    
    try:
        async for session in get_db():
            await performance_optimizer.optimize_database_queries(session)
            break
        
        logger.info("数据库索引创建完成")
        return True
        
    except Exception as e:
        logger.error(f"创建数据库索引失败: {e}")
        return False


async def warm_cache():
    """预热缓存"""
    logger.info("开始预热缓存...")
    
    try:
        await performance_optimizer.warm_cache()
        logger.info("缓存预热完成")
        return True
        
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        return False


async def optimize_database_settings():
    """优化数据库设置"""
    logger.info("开始优化数据库设置...")
    
    try:
        async for session in get_db():
            # 更新表统计信息
            tables = ['market_data', 'ctp_orders', 'ctp_positions', 'kline_data']
            
            for table in tables:
                try:
                    from sqlalchemy import text
                    await session.execute(text(f"ANALYZE {table}"))
                    logger.info(f"表统计信息更新完成: {table}")
                except Exception as e:
                    logger.warning(f"表统计信息更新失败 {table}: {e}")
            
            await session.commit()
            break
        
        logger.info("数据库设置优化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库设置优化失败: {e}")
        return False


async def test_performance():
    """测试性能"""
    logger.info("开始性能测试...")
    
    try:
        # 获取性能报告
        report = await performance_optimizer.get_optimization_report()
        
        logger.info("性能测试结果:")
        logger.info(f"数据库查询统计: {report.get('database_optimization', {})}")
        logger.info(f"缓存统计: {report.get('cache_optimization', {})}")
        logger.info(f"系统资源: {report.get('system_resources', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        return False


async def cleanup_expired_data():
    """清理过期数据"""
    logger.info("开始清理过期数据...")
    
    try:
        # 清理过期缓存
        await performance_optimizer.memory_optimizer._cleanup_expired_cache()
        
        # 清理过期的市场数据（保留最近30天）
        async for session in get_db():
            from sqlalchemy import text
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # 删除过期的市场数据
            result = await session.execute(
                text("DELETE FROM market_data WHERE timestamp < :cutoff_date"),
                {"cutoff_date": cutoff_date}
            )
            
            deleted_count = result.rowcount
            logger.info(f"删除了 {deleted_count} 条过期市场数据")
            
            await session.commit()
            break
        
        logger.info("过期数据清理完成")
        return True
        
    except Exception as e:
        logger.error(f"清理过期数据失败: {e}")
        return False


async def full_optimization(config: CTPPerformanceConfig):
    """完整的性能优化"""
    logger.info(f"开始完整性能优化，优化级别: {config.optimization_level}")
    
    tasks = [
        ("创建数据库索引", create_database_indexes()),
        ("优化数据库设置", optimize_database_settings()),
        ("预热缓存", warm_cache()),
        ("清理过期数据", cleanup_expired_data()),
        ("性能测试", test_performance())
    ]
    
    success_count = 0
    total_count = len(tasks)
    
    for task_name, task_coro in tasks:
        logger.info(f"执行任务: {task_name}")
        try:
            success = await task_coro
            if success:
                success_count += 1
                logger.info(f"✓ {task_name} 完成")
            else:
                logger.error(f"✗ {task_name} 失败")
        except Exception as e:
            logger.error(f"✗ {task_name} 异常: {e}")
    
    logger.info(f"优化完成: {success_count}/{total_count} 任务成功")
    
    if success_count == total_count:
        logger.info("🎉 所有优化任务执行成功!")
        return True
    else:
        logger.warning(f"⚠️  有 {total_count - success_count} 个任务失败")
        return False


async def start_monitoring():
    """启动性能监控"""
    logger.info("启动性能监控...")
    
    try:
        await performance_optimizer.start_monitoring()
        logger.info("性能监控已启动")
        
        # 运行监控一段时间
        logger.info("监控运行中，按 Ctrl+C 停止...")
        try:
            while True:
                await asyncio.sleep(60)  # 每分钟输出一次状态
                report = performance_optimizer.get_performance_report()
                current_metrics = report.get('current_metrics', {})
                logger.info(f"当前性能指标: CPU={current_metrics.get('cpu_usage', 0):.1f}%, "
                           f"内存={current_metrics.get('memory_usage', 0):.1f}%, "
                           f"延迟={current_metrics.get('average_latency', 0):.3f}ms")
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在停止监控...")
            await performance_optimizer.stop_monitoring()
            logger.info("性能监控已停止")
        
        return True
        
    except Exception as e:
        logger.error(f"启动性能监控失败: {e}")
        return False


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CTP性能优化脚本")
    parser.add_argument(
        "--level", 
        choices=["low", "medium", "high", "extreme"],
        default="medium",
        help="优化级别"
    )
    parser.add_argument(
        "--task",
        choices=["full", "indexes", "cache", "database", "cleanup", "test", "monitor"],
        default="full",
        help="执行的任务"
    )
    parser.add_argument(
        "--hft",
        action="store_true",
        help="启用高频交易模式"
    )
    
    args = parser.parse_args()
    
    # 选择配置
    if args.hft:
        config = hft_performance_config
        logger.info("使用高频交易配置")
    else:
        config = CTPPerformanceConfig(
            optimization_level=OptimizationLevel(args.level)
        )
        logger.info(f"使用 {args.level} 级别配置")
    
    # 初始化数据库连接
    try:
        await database_manager.initialize()
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        return 1
    
    # 执行任务
    success = False
    
    try:
        if args.task == "full":
            success = await full_optimization(config)
        elif args.task == "indexes":
            success = await create_database_indexes()
        elif args.task == "cache":
            success = await warm_cache()
        elif args.task == "database":
            success = await optimize_database_settings()
        elif args.task == "cleanup":
            success = await cleanup_expired_data()
        elif args.task == "test":
            success = await test_performance()
        elif args.task == "monitor":
            success = await start_monitoring()
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        success = False
    
    finally:
        # 清理资源
        try:
            await database_manager.close()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
