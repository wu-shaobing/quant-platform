#!/usr/bin/env python3
"""
简单的监控系统测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_monitoring_imports():
    """测试监控模块导入"""
    try:
        print("🔍 测试监控模块导入...")
        
        # 测试指标收集器导入
        from app.monitoring.ctp_metrics import CTPMetricsCollector
        print("✅ CTPMetricsCollector 导入成功")
        
        # 测试告警管理器导入
        from app.monitoring.ctp_alerts import CTPAlertManager
        print("✅ CTPAlertManager 导入成功")
        
        # 测试启动模块导入
        from app.monitoring.startup import start_monitoring_services, stop_monitoring_services
        print("✅ 监控启动模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

async def test_metrics_collector():
    """测试指标收集器基本功能"""
    try:
        print("\n🔍 测试指标收集器...")
        
        from app.monitoring.ctp_metrics import CTPMetricsCollector
        
        # 创建收集器实例
        collector = CTPMetricsCollector()
        print("✅ 指标收集器创建成功")
        
        # 测试记录连接
        await collector.record_connection("trade", True, "simnow")
        print("✅ 连接记录成功")
        
        # 测试记录订单
        await collector.record_order("buy", "open", "IF2501", 100, 4500.0)
        print("✅ 订单记录成功")
        
        # 测试获取指标摘要
        summary = await collector.get_metrics_summary()
        print(f"✅ 指标摘要获取成功: {len(summary)} 项指标")
        
        return True
    except Exception as e:
        print(f"❌ 指标收集器测试失败: {e}")
        return False

async def test_alert_manager():
    """测试告警管理器基本功能"""
    try:
        print("\n🔍 测试告警管理器...")
        
        from app.monitoring.ctp_alerts import CTPAlertManager
        
        # 创建告警管理器实例
        alert_manager = CTPAlertManager()
        print("✅ 告警管理器创建成功")
        
        # 测试创建告警
        alert_id = await alert_manager.create_alert(
            title="测试告警",
            description="这是一个测试告警",
            level="warning",
            source="test"
        )
        print(f"✅ 告警创建成功: {alert_id}")
        
        # 测试获取告警列表
        alerts = await alert_manager.get_alerts()
        print(f"✅ 告警列表获取成功: {len(alerts)} 个告警")
        
        return True
    except Exception as e:
        print(f"❌ 告警管理器测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始监控系统简单测试\n")
    
    # 测试导入
    import_success = await test_monitoring_imports()
    if not import_success:
        print("\n❌ 导入测试失败，退出")
        return False
    
    # 测试指标收集器
    metrics_success = await test_metrics_collector()
    if not metrics_success:
        print("\n❌ 指标收集器测试失败")
    
    # 测试告警管理器
    alert_success = await test_alert_manager()
    if not alert_success:
        print("\n❌ 告警管理器测试失败")
    
    # 总结
    print(f"\n📊 测试结果:")
    print(f"   导入测试: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f"   指标收集器: {'✅ 通过' if metrics_success else '❌ 失败'}")
    print(f"   告警管理器: {'✅ 通过' if alert_success else '❌ 失败'}")
    
    overall_success = import_success and metrics_success and alert_success
    print(f"\n🎯 总体结果: {'✅ 所有测试通过' if overall_success else '❌ 部分测试失败'}")
    
    return overall_success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        sys.exit(1)
