#!/usr/bin/env python3
"""
OWASP ZAP安全扫描配置脚本
用于CI/CD流水线中的自动化安全测试
"""

import os
import sys
import json
import time
import requests
from zapv2 import ZAPv2

class SecurityScanner:
    def __init__(self, target_url, zap_proxy='http://127.0.0.1:8080'):
        self.target_url = target_url
        self.zap_proxy = zap_proxy
        self.zap = ZAPv2(proxies={'http': zap_proxy, 'https': zap_proxy})
        
    def wait_for_zap(self, timeout=300):
        """等待ZAP启动"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.zap.core.version
                print("ZAP已启动")
                return True
            except:
                print("等待ZAP启动...")
                time.sleep(5)
        return False
    
    def configure_zap(self):
        """配置ZAP扫描参数"""
        # 设置用户代理
        self.zap.core.set_option_default_user_agent('SecurityScanner/1.0')
        
        # 配置认证
        auth_config = {
            'loginUrl': f'{self.target_url}/api/v1/auth/login',
            'loginRequestData': 'username=test_user&password=test_password',
            'usernameParameter': 'username',
            'passwordParameter': 'password'
        }
        
        # 添加认证脚本
        script_name = 'auth-script'
        script_type = 'authentication'
        script_engine = 'ECMAScript : Oracle Nashorn'
        script_content = '''
        function authenticate(helper, paramsValues, credentials) {
            var loginUrl = paramsValues.get("loginUrl");
            var loginData = paramsValues.get("loginRequestData");
            
            var msg = helper.prepareMessage();
            msg.setRequestHeader("Content-Type: application/json");
            msg.setRequestBody(loginData);
            msg.getRequestHeader().setURI(new org.apache.commons.httpclient.URI(loginUrl, false));
            msg.getRequestHeader().setMethod("POST");
            
            helper.sendAndReceive(msg);
            
            return msg;
        }
        
        function getRequiredParamsNames() {
            return ["loginUrl", "loginRequestData"];
        }
        
        function getOptionalParamsNames() {
            return [];
        }
        '''
        
        try:
            self.zap.script.load(script_name, script_type, script_engine, script_content)
            print("认证脚本已加载")
        except Exception as e:
            print(f"加载认证脚本失败: {e}")
    
    def spider_scan(self):
        """执行爬虫扫描"""
        print(f"开始爬虫扫描: {self.target_url}")
        
        # 启动爬虫
        scan_id = self.zap.spider.scan(self.target_url)
        
        # 等待爬虫完成
        while int(self.zap.spider.status(scan_id)) < 100:
            print(f"爬虫进度: {self.zap.spider.status(scan_id)}%")
            time.sleep(5)
        
        print("爬虫扫描完成")
        
        # 获取发现的URL
        urls = self.zap.spider.results(scan_id)
        print(f"发现 {len(urls)} 个URL")
        
        return urls
    
    def active_scan(self):
        """执行主动扫描"""
        print(f"开始主动扫描: {self.target_url}")
        
        # 启动主动扫描
        scan_id = self.zap.ascan.scan(self.target_url)
        
        # 等待扫描完成
        while int(self.zap.ascan.status(scan_id)) < 100:
            print(f"主动扫描进度: {self.zap.ascan.status(scan_id)}%")
            time.sleep(10)
        
        print("主动扫描完成")
        return scan_id
    
    def passive_scan(self):
        """等待被动扫描完成"""
        print("等待被动扫描完成...")
        
        while int(self.zap.pscan.records_to_scan) > 0:
            print(f"被动扫描剩余: {self.zap.pscan.records_to_scan}")
            time.sleep(5)
        
        print("被动扫描完成")
    
    def get_alerts(self):
        """获取扫描结果"""
        alerts = self.zap.core.alerts()
        
        # 按风险等级分类
        risk_levels = {'High': [], 'Medium': [], 'Low': [], 'Informational': []}
        
        for alert in alerts:
            risk = alert.get('risk', 'Informational')
            risk_levels[risk].append(alert)
        
        return risk_levels
    
    def generate_report(self, output_file='security_report.json'):
        """生成安全报告"""
        alerts = self.get_alerts()
        
        # 统计信息
        stats = {
            'total_alerts': len(self.zap.core.alerts()),
            'high_risk': len(alerts['High']),
            'medium_risk': len(alerts['Medium']),
            'low_risk': len(alerts['Low']),
            'informational': len(alerts['Informational'])
        }
        
        # 生成报告
        report = {
            'scan_target': self.target_url,
            'scan_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': stats,
            'alerts': alerts
        }
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"安全报告已保存到: {output_file}")
        return report
    
    def check_security_baseline(self, max_high=0, max_medium=5):
        """检查安全基线"""
        alerts = self.get_alerts()
        
        high_count = len(alerts['High'])
        medium_count = len(alerts['Medium'])
        
        print(f"高风险漏洞: {high_count} (最大允许: {max_high})")
        print(f"中风险漏洞: {medium_count} (最大允许: {max_medium})")
        
        if high_count > max_high:
            print(f"❌ 高风险漏洞超过阈值: {high_count} > {max_high}")
            return False
        
        if medium_count > max_medium:
            print(f"❌ 中风险漏洞超过阈值: {medium_count} > {max_medium}")
            return False
        
        print("✅ 安全基线检查通过")
        return True
    
    def run_full_scan(self):
        """执行完整安全扫描"""
        try:
            # 等待ZAP启动
            if not self.wait_for_zap():
                print("ZAP启动超时")
                return False
            
            # 配置ZAP
            self.configure_zap()
            
            # 执行爬虫扫描
            self.spider_scan()
            
            # 执行主动扫描
            self.active_scan()
            
            # 等待被动扫描完成
            self.passive_scan()
            
            # 生成报告
            report = self.generate_report()
            
            # 检查安全基线
            baseline_passed = self.check_security_baseline()
            
            return baseline_passed
            
        except Exception as e:
            print(f"扫描过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    target_url = os.getenv('TARGET_URL', 'http://localhost:8000')
    zap_proxy = os.getenv('ZAP_PROXY', 'http://127.0.0.1:8080')
    
    print(f"开始安全扫描: {target_url}")
    
    scanner = SecurityScanner(target_url, zap_proxy)
    success = scanner.run_full_scan()
    
    if success:
        print("✅ 安全扫描通过")
        sys.exit(0)
    else:
        print("❌ 安全扫描失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
