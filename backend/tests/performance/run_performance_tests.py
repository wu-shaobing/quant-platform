#!/usr/bin/env python3
"""
性能和安全测试执行脚本
统一执行所有性能和安全测试
"""

import asyncio
import subprocess
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTestRunner:
    """性能测试执行器"""
    
    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.test_results = {}
        self.start_time = datetime.now()
        
        # 测试配置
        self.tests_config = {
            'k6_load_test': {
                'script': 'backend/tests/performance/k6_load_test.js',
                'command': ['k6', 'run'],
                'timeout': 600,  # 10分钟
                'enabled': True
            },
            'security_scan': {
                'script': 'backend/tests/security/zap_security_scan.py',
                'command': [sys.executable],
                'timeout': 1800,  # 30分钟
                'enabled': True
            },
            'database_benchmark': {
                'script': 'backend/tests/performance/database_benchmark.py',
                'command': [sys.executable],
                'timeout': 900,  # 15分钟
                'enabled': True
            }
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能和安全测试"""
        logger.info("开始执行性能和安全测试套件...")
        
        # 1. 检查环境
        await self._check_environment()
        
        # 2. 运行k6负载测试
        if self.tests_config['k6_load_test']['enabled']:
            logger.info("执行k6负载测试...")
            self.test_results['k6_load_test'] = await self._run_k6_test()
        
        # 3. 运行安全扫描
        if self.tests_config['security_scan']['enabled']:
            logger.info("执行安全扫描...")
            self.test_results['security_scan'] = await self._run_security_scan()
        
        # 4. 运行数据库基准测试
        if self.tests_config['database_benchmark']['enabled']:
            logger.info("执行数据库基准测试...")
            self.test_results['database_benchmark'] = await self._run_database_benchmark()
        
        # 5. 生成综合报告
        comprehensive_report = await self._generate_comprehensive_report()
        
        logger.info("所有测试执行完成")
        return comprehensive_report

    async def _check_environment(self):
        """检查测试环境"""
        logger.info("检查测试环境...")
        
        # 检查目标服务是否可用
        try:
            import requests
            response = requests.get(f"{self.target_url}/health", timeout=5)
            if response.status_code != 200:
                logger.warning(f"目标服务健康检查失败: {response.status_code}")
        except Exception as e:
            logger.warning(f"无法连接到目标服务: {e}")
        
        # 检查k6是否安装
        try:
            result = subprocess.run(['k6', 'version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"k6版本: {result.stdout.strip()}")
            else:
                logger.warning("k6未安装或不可用")
                self.tests_config['k6_load_test']['enabled'] = False
        except Exception as e:
            logger.warning(f"k6检查失败: {e}")
            self.tests_config['k6_load_test']['enabled'] = False
        
        # 检查Python依赖
        required_packages = ['requests', 'sqlalchemy', 'psutil']
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✓ {package} 已安装")
            except ImportError:
                logger.warning(f"✗ {package} 未安装")

    async def _run_k6_test(self) -> Dict[str, Any]:
        """运行k6负载测试"""
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['TARGET_URL'] = self.target_url
            
            # 执行k6测试
            cmd = self.tests_config['k6_load_test']['command'] + [
                self.tests_config['k6_load_test']['script'],
                '--out', 'json=k6_results.json'
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.tests_config['k6_load_test']['timeout'],
                env=env,
                cwd=os.getcwd()
            )
            duration = time.time() - start_time
            
            # 解析结果
            k6_results = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # 尝试解析JSON输出
            try:
                if os.path.exists('k6_results.json'):
                    with open('k6_results.json', 'r') as f:
                        k6_data = []
                        for line in f:
                            if line.strip():
                                k6_data.append(json.loads(line))
                        k6_results['detailed_metrics'] = k6_data
            except Exception as e:
                logger.warning(f"解析k6结果失败: {e}")
            
            return k6_results
            
        except subprocess.TimeoutExpired:
            logger.error("k6测试超时")
            return {'status': 'timeout', 'error': 'Test execution timeout'}
        except Exception as e:
            logger.error(f"k6测试执行失败: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _run_security_scan(self) -> Dict[str, Any]:
        """运行安全扫描"""
        try:
            cmd = self.tests_config['security_scan']['command'] + [
                self.tests_config['security_scan']['script'],
                '--target', self.target_url,
                '--output', 'security_scan_results.json'
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.tests_config['security_scan']['timeout'],
                cwd=os.getcwd()
            )
            duration = time.time() - start_time
            
            # 解析结果
            security_results = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # 尝试加载详细结果
            try:
                if os.path.exists('security_scan_results.json'):
                    with open('security_scan_results.json', 'r', encoding='utf-8') as f:
                        security_results['detailed_results'] = json.load(f)
            except Exception as e:
                logger.warning(f"解析安全扫描结果失败: {e}")
            
            return security_results
            
        except subprocess.TimeoutExpired:
            logger.error("安全扫描超时")
            return {'status': 'timeout', 'error': 'Security scan timeout'}
        except Exception as e:
            logger.error(f"安全扫描执行失败: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _run_database_benchmark(self) -> Dict[str, Any]:
        """运行数据库基准测试"""
        try:
            cmd = self.tests_config['database_benchmark']['command'] + [
                self.tests_config['database_benchmark']['script'],
                '--output', 'database_benchmark_results.json'
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.tests_config['database_benchmark']['timeout'],
                cwd=os.getcwd()
            )
            duration = time.time() - start_time
            
            # 解析结果
            db_results = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # 尝试加载详细结果
            try:
                if os.path.exists('database_benchmark_results.json'):
                    with open('database_benchmark_results.json', 'r', encoding='utf-8') as f:
                        db_results['detailed_results'] = json.load(f)
            except Exception as e:
                logger.warning(f"解析数据库基准测试结果失败: {e}")
            
            return db_results
            
        except subprocess.TimeoutExpired:
            logger.error("数据库基准测试超时")
            return {'status': 'timeout', 'error': 'Database benchmark timeout'}
        except Exception as e:
            logger.error(f"数据库基准测试执行失败: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合测试报告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # 统计测试结果
        test_summary = {
            'total_tests': len(self.test_results),
            'passed_tests': 0,
            'failed_tests': 0,
            'timeout_tests': 0,
            'error_tests': 0
        }
        
        for test_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            if status == 'completed':
                test_summary['passed_tests'] += 1
            elif status == 'failed':
                test_summary['failed_tests'] += 1
            elif status == 'timeout':
                test_summary['timeout_tests'] += 1
            else:
                test_summary['error_tests'] += 1
        
        # 生成性能摘要
        performance_summary = self._extract_performance_metrics()
        
        # 生成安全摘要
        security_summary = self._extract_security_metrics()
        
        # 综合报告
        comprehensive_report = {
            'test_execution_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'target_url': self.target_url
            },
            'test_summary': test_summary,
            'performance_summary': performance_summary,
            'security_summary': security_summary,
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
        
        # 保存综合报告
        report_filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"综合测试报告已保存到: {report_filename}")
        
        return comprehensive_report

    def _extract_performance_metrics(self) -> Dict[str, Any]:
        """提取性能指标"""
        performance_summary = {
            'load_test_status': 'unknown',
            'database_performance': 'unknown',
            'key_metrics': {}
        }
        
        # k6负载测试结果
        k6_result = self.test_results.get('k6_load_test', {})
        if k6_result.get('status') == 'completed':
            performance_summary['load_test_status'] = 'passed'
            # 从stdout中提取关键指标
            stdout = k6_result.get('stdout', '')
            if 'http_req_duration' in stdout:
                performance_summary['key_metrics']['load_test'] = 'metrics_available'
        
        # 数据库基准测试结果
        db_result = self.test_results.get('database_benchmark', {})
        if db_result.get('status') == 'completed':
            detailed_results = db_result.get('detailed_results', {})
            if detailed_results:
                summary = detailed_results.get('summary', {})
                performance_summary['database_performance'] = summary.get('overall_performance', 'unknown')
                performance_summary['key_metrics']['database'] = summary.get('key_metrics', {})
        
        return performance_summary

    def _extract_security_metrics(self) -> Dict[str, Any]:
        """提取安全指标"""
        security_summary = {
            'scan_status': 'unknown',
            'overall_risk': 'unknown',
            'vulnerabilities_found': 0,
            'critical_issues': []
        }
        
        security_result = self.test_results.get('security_scan', {})
        if security_result.get('status') == 'completed':
            detailed_results = security_result.get('detailed_results', {})
            if detailed_results:
                summary = detailed_results.get('summary', {})
                security_summary.update({
                    'scan_status': 'completed',
                    'overall_risk': summary.get('overall_risk', 'unknown'),
                    'vulnerabilities_found': summary.get('total_vulnerabilities', 0),
                    'critical_issues': summary.get('critical_issues', [])
                })
        
        return security_summary

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于测试结果生成建议
        if self.test_results.get('k6_load_test', {}).get('status') != 'completed':
            recommendations.append("负载测试未成功完成，建议检查k6安装和配置")
        
        if self.test_results.get('security_scan', {}).get('status') != 'completed':
            recommendations.append("安全扫描未成功完成，建议检查ZAP配置和网络连接")
        
        if self.test_results.get('database_benchmark', {}).get('status') != 'completed':
            recommendations.append("数据库基准测试未成功完成，建议检查数据库连接和权限")
        
        # 基于性能结果的建议
        performance_summary = self._extract_performance_metrics()
        if performance_summary.get('database_performance') in ['FAIR', 'POOR']:
            recommendations.append("数据库性能需要优化，建议检查索引和查询优化")
        
        # 基于安全结果的建议
        security_summary = self._extract_security_metrics()
        if security_summary.get('overall_risk') == 'HIGH':
            recommendations.append("发现高风险安全漏洞，建议立即修复")
        
        if not recommendations:
            recommendations.append("所有测试正常完成，系统性能和安全状况良好")
        
        return recommendations


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="性能和安全测试执行器")
    parser.add_argument("--target", default="http://localhost:8000", help="目标URL")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    
    args = parser.parse_args()
    
    # 切换到输出目录
    if args.output_dir != ".":
        os.makedirs(args.output_dir, exist_ok=True)
        os.chdir(args.output_dir)
    
    # 创建测试执行器
    runner = PerformanceTestRunner(args.target)
    
    # 运行所有测试
    try:
        results = await runner.run_all_tests()
        
        # 打印摘要
        print("\n" + "="*60)
        print("性能和安全测试执行摘要")
        print("="*60)
        
        test_summary = results.get('test_summary', {})
        print(f"总测试数: {test_summary.get('total_tests', 0)}")
        print(f"通过: {test_summary.get('passed_tests', 0)}")
        print(f"失败: {test_summary.get('failed_tests', 0)}")
        print(f"超时: {test_summary.get('timeout_tests', 0)}")
        print(f"错误: {test_summary.get('error_tests', 0)}")
        
        performance_summary = results.get('performance_summary', {})
        print(f"\n负载测试状态: {performance_summary.get('load_test_status', 'unknown')}")
        print(f"数据库性能: {performance_summary.get('database_performance', 'unknown')}")
        
        security_summary = results.get('security_summary', {})
        print(f"安全扫描状态: {security_summary.get('scan_status', 'unknown')}")
        print(f"整体风险级别: {security_summary.get('overall_risk', 'unknown')}")
        print(f"发现漏洞数: {security_summary.get('vulnerabilities_found', 0)}")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            print("\n优化建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        
        print("\n测试执行完成！")
        
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
