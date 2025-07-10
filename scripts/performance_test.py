#!/usr/bin/env python3
"""
性能测试脚本
用于运行各种性能测试和生成报告
"""

import asyncio
import json
import time
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from backend.tests.performance.test_performance_suite import (
    APIPerformanceTester,
    DatabasePerformanceTester,
    WebSocketPerformanceTester,
    MemoryProfiler
)


class PerformanceTestRunner:
    """性能测试运行器"""
    
    def __init__(self, output_dir: str = "performance_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        
    def save_results(self, test_name: str, results: dict):
        """保存测试结果"""
        self.results[test_name] = {
            "timestamp": time.time(),
            "results": results
        }
        
        # 保存到文件
        output_file = self.output_dir / f"{test_name}_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results[test_name], f, indent=2, ensure_ascii=False)
            
        print(f"结果已保存到: {output_file}")
    
    async def run_api_performance_test(self):
        """运行API性能测试"""
        print("\n" + "="*50)
        print("API性能测试")
        print("="*50)
        
        tester = APIPerformanceTester()
        
        # 基础API测试
        basic_tests = [
            {
                "name": "health_check",
                "method": "GET",
                "endpoint": "/health",
                "concurrent_users": 50,
                "requests_per_user": 100
            },
            {
                "name": "auth_login", 
                "method": "POST",
                "endpoint": "/auth/login",
                "concurrent_users": 20,
                "requests_per_user": 50,
                "payload": {
                    "email": "test@example.com",
                    "password": "testpass123"
                }
            }
        ]
        
        results = {}
        
        for test in basic_tests:
            print(f"\n执行测试: {test['name']}")
            print("-" * 30)
            
            metrics = await tester.load_test_endpoint(
                method=test["method"],
                endpoint=test["endpoint"],
                concurrent_users=test["concurrent_users"],
                requests_per_user=test["requests_per_user"],
                payload=test.get("payload")
            )
            
            stats = metrics.get_stats()
            results[test["name"]] = stats
            
            # 打印结果
            print(f"总请求数: {stats['total_requests']}")
            print(f"成功率: {stats['success_rate']}%")
            print(f"平均响应时间: {stats['avg_response_time']}ms")
            print(f"P95响应时间: {stats['p95_response_time']}ms")
            print(f"P99响应时间: {stats['p99_response_time']}ms")
            print(f"吞吐量: {stats['throughput']} req/s")
            
            # 性能评估
            if stats['success_rate'] < 95:
                print("⚠️  警告: 成功率过低")
            if stats['avg_response_time'] > 500:
                print("⚠️  警告: 平均响应时间过长")
            if stats['p95_response_time'] > 1000:
                print("⚠️  警告: P95响应时间过长")
        
        # 如果能够认证，运行交易API测试
        if await tester.authenticate():
            print("\n运行交易API测试...")
            trading_results = await tester.stress_test_trading_apis()
            
            for endpoint, metrics in trading_results.items():
                results[f"trading_{endpoint}"] = metrics.get_stats()
        
        self.save_results("api_performance", results)
        return results
    
    async def run_websocket_performance_test(self):
        """运行WebSocket性能测试"""
        print("\n" + "="*50)
        print("WebSocket性能测试")
        print("="*50)
        
        tester = WebSocketPerformanceTester()
        results = {}
        
        # 连接性能测试
        print("\n1. 连接性能测试")
        print("-" * 30)
        
        connection_tests = [10, 50, 100, 200]
        
        for concurrent_connections in connection_tests:
            print(f"测试 {concurrent_connections} 个并发连接...")
            
            try:
                connection_results = await tester.test_connection_performance(
                    concurrent_connections=concurrent_connections
                )
                
                results[f"connections_{concurrent_connections}"] = connection_results
                
                print(f"  成功连接: {connection_results['successful_connections']}")
                print(f"  失败连接: {connection_results['failed_connections']}")
                print(f"  成功率: {connection_results['success_rate']:.1f}%")
                print(f"  平均连接时间: {connection_results['avg_connection_time']:.3f}s")
                
                if connection_results['success_rate'] < 90:
                    print("  ⚠️  警告: 连接成功率过低")
                    break
                    
            except Exception as e:
                print(f"  ❌ 连接测试失败: {e}")
                break
        
        # 消息吞吐量测试
        print("\n2. 消息吞吐量测试")
        print("-" * 30)
        
        throughput_tests = [
            {"rate": 10, "duration": 5},
            {"rate": 50, "duration": 5},
            {"rate": 100, "duration": 5},
            {"rate": 500, "duration": 5}
        ]
        
        for test in throughput_tests:
            print(f"测试 {test['rate']} msg/s，持续 {test['duration']}s...")
            
            try:
                throughput_results = await tester.test_message_throughput(
                    messages_per_second=test["rate"],
                    duration=test["duration"]
                )
                
                results[f"throughput_{test['rate']}_msgs"] = throughput_results
                
                print(f"  发送消息: {throughput_results['messages_sent']}")
                print(f"  接收消息: {throughput_results['messages_received']}")
                print(f"  实际发送速率: {throughput_results['actual_send_rate']:.1f} msg/s")
                print(f"  实际接收速率: {throughput_results['actual_receive_rate']:.1f} msg/s")
                print(f"  消息丢失率: {throughput_results['message_loss_rate']:.1f}%")
                print(f"  平均延迟: {throughput_results['avg_message_latency']:.1f}ms")
                
                if throughput_results['message_loss_rate'] > 5:
                    print("  ⚠️  警告: 消息丢失率过高")
                if throughput_results['avg_message_latency'] > 100:
                    print("  ⚠️  警告: 消息延迟过高")
                    
            except Exception as e:
                print(f"  ❌ 吞吐量测试失败: {e}")
        
        self.save_results("websocket_performance", results)
        return results
    
    async def run_memory_performance_test(self):
        """运行内存性能测试"""
        print("\n" + "="*50)
        print("内存性能测试")
        print("="*50)
        
        results = {}
        
        # 基础内存使用
        print("\n1. 基础内存使用情况")
        print("-" * 30)
        
        initial_memory = MemoryProfiler.get_memory_usage()
        results["initial_memory"] = initial_memory
        
        print(f"RSS内存: {initial_memory['rss']:.1f} MB")
        print(f"VMS内存: {initial_memory['vms']:.1f} MB")
        print(f"内存占用率: {initial_memory['percent']:.1f}%")
        print(f"可用内存: {initial_memory['available']:.1f} MB")
        
        # 内存压力测试
        print("\n2. 内存压力测试")
        print("-" * 30)
        
        def memory_intensive_task():
            """内存密集型任务"""
            # 创建大量对象
            data = []
            for i in range(100000):
                data.append({
                    "id": i,
                    "data": f"test_data_{i}" * 10,
                    "numbers": list(range(100))
                })
            return len(data)
        
        memory_result = await MemoryProfiler.profile_memory_usage(memory_intensive_task)
        results["memory_stress_test"] = memory_result
        
        print(f"执行时间: {memory_result['execution_time']:.3f}s")
        print(f"内存增长: {memory_result['memory_diff']['rss']:.1f} MB")
        print(f"任务结果: {memory_result['result']} 个对象")
        
        if memory_result['memory_diff']['rss'] > 100:
            print("⚠️  警告: 内存使用增长过多")
        
        # 垃圾回收后的内存
        import gc
        gc.collect()
        
        final_memory = MemoryProfiler.get_memory_usage()
        results["final_memory"] = final_memory
        
        print(f"\n垃圾回收后RSS内存: {final_memory['rss']:.1f} MB")
        print(f"内存恢复: {initial_memory['rss'] - final_memory['rss']:.1f} MB")
        
        self.save_results("memory_performance", results)
        return results
    
    def generate_summary_report(self):
        """生成汇总报告"""
        print("\n" + "="*50)
        print("性能测试汇总报告")
        print("="*50)
        
        report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {},
            "recommendations": []
        }
        
        # API性能汇总
        if "api_performance" in self.results:
            api_results = self.results["api_performance"]["results"]
            
            avg_response_times = []
            success_rates = []
            
            for endpoint, stats in api_results.items():
                if isinstance(stats, dict) and "avg_response_time" in stats:
                    avg_response_times.append(stats["avg_response_time"])
                    success_rates.append(stats["success_rate"])
            
            if avg_response_times:
                report["summary"]["api"] = {
                    "avg_response_time": sum(avg_response_times) / len(avg_response_times),
                    "avg_success_rate": sum(success_rates) / len(success_rates),
                    "endpoints_tested": len(avg_response_times)
                }
                
                print(f"\nAPI性能:")
                print(f"  测试端点数: {len(avg_response_times)}")
                print(f"  平均响应时间: {report['summary']['api']['avg_response_time']:.1f}ms")
                print(f"  平均成功率: {report['summary']['api']['avg_success_rate']:.1f}%")
                
                # 生成建议
                if report['summary']['api']['avg_response_time'] > 300:
                    report["recommendations"].append("API响应时间较慢，建议优化数据库查询和缓存策略")
                if report['summary']['api']['avg_success_rate'] < 98:
                    report["recommendations"].append("API成功率偏低，建议检查错误处理和系统稳定性")
        
        # WebSocket性能汇总
        if "websocket_performance" in self.results:
            ws_results = self.results["websocket_performance"]["results"]
            
            # 找到最大成功连接数
            max_connections = 0
            for key, value in ws_results.items():
                if key.startswith("connections_") and isinstance(value, dict):
                    if value.get("success_rate", 0) > 90:
                        connections = int(key.split("_")[1])
                        max_connections = max(max_connections, connections)
            
            report["summary"]["websocket"] = {
                "max_stable_connections": max_connections
            }
            
            print(f"\nWebSocket性能:")
            print(f"  最大稳定连接数: {max_connections}")
            
            if max_connections < 100:
                report["recommendations"].append("WebSocket并发连接数偏低，建议优化连接池配置")
        
        # 内存性能汇总
        if "memory_performance" in self.results:
            memory_results = self.results["memory_performance"]["results"]
            
            if "memory_stress_test" in memory_results:
                memory_growth = memory_results["memory_stress_test"]["memory_diff"]["rss"]
                
                report["summary"]["memory"] = {
                    "stress_test_memory_growth": memory_growth
                }
                
                print(f"\n内存性能:")
                print(f"  压力测试内存增长: {memory_growth:.1f}MB")
                
                if memory_growth > 50:
                    report["recommendations"].append("内存使用增长较大，建议优化对象创建和垃圾回收")
        
        # 保存汇总报告
        report_file = self.output_dir / f"summary_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 打印建议
        if report["recommendations"]:
            print(f"\n优化建议:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")
        else:
            print(f"\n✅ 所有性能指标都在正常范围内!")
        
        print(f"\n汇总报告已保存到: {report_file}")
        return report


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="量化平台性能测试工具")
    parser.add_argument("--test", choices=["api", "websocket", "memory", "all"], 
                       default="all", help="要运行的测试类型")
    parser.add_argument("--output", default="performance_reports", 
                       help="输出目录")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(args.output)
    
    print("🚀 开始性能测试...")
    print(f"输出目录: {args.output}")
    
    try:
        if args.test in ["api", "all"]:
            await runner.run_api_performance_test()
        
        if args.test in ["websocket", "all"]:
            await runner.run_websocket_performance_test()
        
        if args.test in ["memory", "all"]:
            await runner.run_memory_performance_test()
        
        # 生成汇总报告
        runner.generate_summary_report()
        
        print("\n✅ 性能测试完成!")
        
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 