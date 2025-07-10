#!/usr/bin/env python3
"""
OWASP ZAP 安全扫描脚本
针对量化交易平台进行全面的安全测试
"""

import time
import json
import requests
from zapv2 import ZAPv2
import logging
from typing import Dict, List, Any
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, target_url: str = "http://localhost:8000", zap_proxy: str = "http://127.0.0.1:8080"):
        self.target_url = target_url
        self.zap_proxy = zap_proxy
        self.zap = ZAPv2(proxies={'http': zap_proxy, 'https': zap_proxy})
        
        # 测试用户凭据
        self.test_users = [
            {"username": "testuser1", "password": "testpass123"},
            {"username": "trader1", "password": "trader123"},
            {"username": "admin", "password": "admin123"}
        ]
        
        # 关键API端点
        self.api_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register", 
            "/api/v1/auth/profile",
            "/api/v1/trading/orders",
            "/api/v1/trading/positions",
            "/api/v1/trading/account",
            "/api/v1/market/ticks/rb2405",
            "/api/v1/ctp/status",
            "/api/v1/ctp/account",
            "/ws/market"
        ]
        
        # 敏感数据模式
        self.sensitive_patterns = [
            r"password",
            r"token",
            r"secret",
            r"key",
            r"api_key",
            r"access_token",
            r"refresh_token",
            r"session",
            r"cookie",
            r"authorization"
        ]

    def start_scan(self) -> Dict[str, Any]:
        """开始安全扫描"""
        logger.info("开始安全扫描...")
        
        scan_results = {
            "scan_start_time": datetime.now().isoformat(),
            "target_url": self.target_url,
            "spider_results": {},
            "active_scan_results": {},
            "authentication_tests": {},
            "authorization_tests": {},
            "injection_tests": {},
            "xss_tests": {},
            "csrf_tests": {},
            "security_headers_tests": {},
            "ssl_tests": {},
            "api_security_tests": {},
            "summary": {}
        }
        
        try:
            # 1. 启动ZAP代理
            self._start_zap_session()
            
            # 2. 蜘蛛爬取
            scan_results["spider_results"] = self._run_spider()
            
            # 3. 认证测试
            scan_results["authentication_tests"] = self._test_authentication()
            
            # 4. 授权测试
            scan_results["authorization_tests"] = self._test_authorization()
            
            # 5. 注入攻击测试
            scan_results["injection_tests"] = self._test_injection_attacks()
            
            # 6. XSS测试
            scan_results["xss_tests"] = self._test_xss()
            
            # 7. CSRF测试
            scan_results["csrf_tests"] = self._test_csrf()
            
            # 8. 安全头测试
            scan_results["security_headers_tests"] = self._test_security_headers()
            
            # 9. SSL/TLS测试
            scan_results["ssl_tests"] = self._test_ssl()
            
            # 10. API安全测试
            scan_results["api_security_tests"] = self._test_api_security()
            
            # 11. 主动扫描
            scan_results["active_scan_results"] = self._run_active_scan()
            
            # 12. 生成摘要
            scan_results["summary"] = self._generate_summary(scan_results)
            
            scan_results["scan_end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"扫描过程中发生错误: {e}")
            scan_results["error"] = str(e)
        
        return scan_results

    def _start_zap_session(self):
        """启动ZAP会话"""
        logger.info("启动ZAP会话...")
        
        # 创建新会话
        self.zap.core.new_session()
        
        # 设置全局排除规则
        self.zap.core.exclude_from_proxy(".*\\.js$")
        self.zap.core.exclude_from_proxy(".*\\.css$")
        self.zap.core.exclude_from_proxy(".*\\.png$")
        self.zap.core.exclude_from_proxy(".*\\.jpg$")
        
        logger.info("ZAP会话启动完成")

    def _run_spider(self) -> Dict[str, Any]:
        """运行蜘蛛爬取"""
        logger.info("开始蜘蛛爬取...")
        
        # 启动蜘蛛
        scan_id = self.zap.spider.scan(self.target_url)
        
        # 等待爬取完成
        while int(self.zap.spider.status(scan_id)) < 100:
            logger.info(f"蜘蛛爬取进度: {self.zap.spider.status(scan_id)}%")
            time.sleep(2)
        
        # 获取爬取结果
        urls = self.zap.spider.results(scan_id)
        
        logger.info(f"蜘蛛爬取完成，发现 {len(urls)} 个URL")
        
        return {
            "scan_id": scan_id,
            "urls_found": len(urls),
            "urls": urls[:50]  # 只保存前50个URL
        }

    def _test_authentication(self) -> Dict[str, Any]:
        """测试认证机制"""
        logger.info("开始认证测试...")
        
        results = {
            "weak_passwords": [],
            "brute_force_protection": {},
            "session_management": {},
            "password_policy": {}
        }
        
        # 测试弱密码
        weak_passwords = ["123456", "password", "admin", "test", ""]
        for username in ["admin", "test", "user"]:
            for password in weak_passwords:
                try:
                    response = requests.post(
                        f"{self.target_url}/api/v1/auth/login",
                        json={"username": username, "password": password},
                        timeout=5
                    )
                    if response.status_code == 200:
                        results["weak_passwords"].append({
                            "username": username,
                            "password": password,
                            "status": "VULNERABLE"
                        })
                except Exception as e:
                    logger.debug(f"认证测试错误: {e}")
        
        # 测试暴力破解保护
        results["brute_force_protection"] = self._test_brute_force_protection()
        
        # 测试会话管理
        results["session_management"] = self._test_session_management()
        
        return results

    def _test_brute_force_protection(self) -> Dict[str, Any]:
        """测试暴力破解保护"""
        logger.info("测试暴力破解保护...")
        
        # 连续尝试错误登录
        failed_attempts = 0
        for i in range(10):
            try:
                response = requests.post(
                    f"{self.target_url}/api/v1/auth/login",
                    json={"username": "testuser", "password": f"wrongpass{i}"},
                    timeout=5
                )
                if response.status_code == 401:
                    failed_attempts += 1
                elif response.status_code == 429:  # Too Many Requests
                    return {
                        "protection_enabled": True,
                        "failed_attempts_before_lockout": failed_attempts,
                        "status": "PROTECTED"
                    }
            except Exception as e:
                logger.debug(f"暴力破解测试错误: {e}")
        
        return {
            "protection_enabled": False,
            "failed_attempts": failed_attempts,
            "status": "VULNERABLE"
        }

    def _test_session_management(self) -> Dict[str, Any]:
        """测试会话管理"""
        logger.info("测试会话管理...")
        
        results = {
            "session_fixation": "UNKNOWN",
            "session_timeout": "UNKNOWN",
            "secure_cookies": "UNKNOWN"
        }
        
        try:
            # 登录获取会话
            login_response = requests.post(
                f"{self.target_url}/api/v1/auth/login",
                json=self.test_users[0],
                timeout=5
            )
            
            if login_response.status_code == 200:
                # 检查Cookie安全属性
                cookies = login_response.cookies
                for cookie in cookies:
                    if not cookie.secure:
                        results["secure_cookies"] = "VULNERABLE"
                    if not cookie.has_nonstandard_attr('HttpOnly'):
                        results["secure_cookies"] = "VULNERABLE"
                
                if results["secure_cookies"] == "UNKNOWN":
                    results["secure_cookies"] = "SECURE"
                    
        except Exception as e:
            logger.debug(f"会话管理测试错误: {e}")
        
        return results

    def _test_authorization(self) -> Dict[str, Any]:
        """测试授权机制"""
        logger.info("开始授权测试...")
        
        results = {
            "privilege_escalation": [],
            "idor": [],  # Insecure Direct Object References
            "missing_authorization": []
        }
        
        # 测试权限提升
        results["privilege_escalation"] = self._test_privilege_escalation()
        
        # 测试IDOR
        results["idor"] = self._test_idor()
        
        # 测试缺失授权
        results["missing_authorization"] = self._test_missing_authorization()
        
        return results

    def _test_privilege_escalation(self) -> List[Dict[str, Any]]:
        """测试权限提升"""
        vulnerabilities = []
        
        try:
            # 使用普通用户登录
            login_response = requests.post(
                f"{self.target_url}/api/v1/auth/login",
                json=self.test_users[0],
                timeout=5
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # 尝试访问管理员端点
                admin_endpoints = [
                    "/api/v1/admin/users",
                    "/api/v1/admin/settings",
                    "/api/v1/admin/logs"
                ]
                
                for endpoint in admin_endpoints:
                    try:
                        response = requests.get(
                            f"{self.target_url}{endpoint}",
                            headers=headers,
                            timeout=5
                        )
                        if response.status_code == 200:
                            vulnerabilities.append({
                                "endpoint": endpoint,
                                "status": "VULNERABLE",
                                "description": "普通用户可以访问管理员端点"
                            })
                    except Exception as e:
                        logger.debug(f"权限提升测试错误: {e}")
                        
        except Exception as e:
            logger.debug(f"权限提升测试错误: {e}")
        
        return vulnerabilities

    def _test_idor(self) -> List[Dict[str, Any]]:
        """测试不安全的直接对象引用"""
        vulnerabilities = []
        
        # 测试用户ID枚举
        for user_id in range(1, 10):
            try:
                response = requests.get(
                    f"{self.target_url}/api/v1/users/{user_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    vulnerabilities.append({
                        "endpoint": f"/api/v1/users/{user_id}",
                        "status": "VULNERABLE",
                        "description": "可以枚举用户信息"
                    })
            except Exception as e:
                logger.debug(f"IDOR测试错误: {e}")
        
        return vulnerabilities

    def _test_missing_authorization(self) -> List[Dict[str, Any]]:
        """测试缺失授权"""
        vulnerabilities = []
        
        # 测试未授权访问
        protected_endpoints = [
            "/api/v1/trading/orders",
            "/api/v1/trading/positions",
            "/api/v1/trading/account",
            "/api/v1/ctp/account"
        ]
        
        for endpoint in protected_endpoints:
            try:
                response = requests.get(
                    f"{self.target_url}{endpoint}",
                    timeout=5
                )
                if response.status_code == 200:
                    vulnerabilities.append({
                        "endpoint": endpoint,
                        "status": "VULNERABLE",
                        "description": "端点缺少授权检查"
                    })
            except Exception as e:
                logger.debug(f"授权测试错误: {e}")
        
        return vulnerabilities

    def _test_injection_attacks(self) -> Dict[str, Any]:
        """测试注入攻击"""
        logger.info("开始注入攻击测试...")

        results = {
            "sql_injection": [],
            "nosql_injection": [],
            "command_injection": [],
            "ldap_injection": []
        }

        # SQL注入测试载荷
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]

        # NoSQL注入测试载荷
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "this.username == this.password"}
        ]

        # 命令注入测试载荷
        command_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`id`"
        ]

        # 测试SQL注入
        results["sql_injection"] = self._test_sql_injection(sql_payloads)

        # 测试NoSQL注入
        results["nosql_injection"] = self._test_nosql_injection(nosql_payloads)

        # 测试命令注入
        results["command_injection"] = self._test_command_injection(command_payloads)

        return results

    def _test_sql_injection(self, payloads: List[str]) -> List[Dict[str, Any]]:
        """测试SQL注入"""
        vulnerabilities = []

        # 测试登录表单
        for payload in payloads:
            try:
                response = requests.post(
                    f"{self.target_url}/api/v1/auth/login",
                    json={"username": payload, "password": "test"},
                    timeout=5
                )

                # 检查错误消息是否泄露数据库信息
                if any(keyword in response.text.lower() for keyword in
                       ["sql", "mysql", "postgresql", "sqlite", "oracle", "syntax error"]):
                    vulnerabilities.append({
                        "endpoint": "/api/v1/auth/login",
                        "payload": payload,
                        "status": "VULNERABLE",
                        "description": "SQL错误信息泄露"
                    })

            except Exception as e:
                logger.debug(f"SQL注入测试错误: {e}")

        # 测试查询参数
        test_endpoints = [
            "/api/v1/market/ticks/",
            "/api/v1/trading/orders?id=",
            "/api/v1/users?search="
        ]

        for endpoint in test_endpoints:
            for payload in payloads:
                try:
                    response = requests.get(
                        f"{self.target_url}{endpoint}{payload}",
                        timeout=5
                    )

                    if any(keyword in response.text.lower() for keyword in
                           ["sql", "mysql", "postgresql", "sqlite", "syntax error"]):
                        vulnerabilities.append({
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "VULNERABLE",
                            "description": "查询参数SQL注入"
                        })

                except Exception as e:
                    logger.debug(f"SQL注入测试错误: {e}")

        return vulnerabilities

    def _test_nosql_injection(self, payloads: List[Any]) -> List[Dict[str, Any]]:
        """测试NoSQL注入"""
        vulnerabilities = []

        for payload in payloads:
            try:
                response = requests.post(
                    f"{self.target_url}/api/v1/auth/login",
                    json={"username": payload, "password": payload},
                    timeout=5
                )

                if response.status_code == 200:
                    vulnerabilities.append({
                        "endpoint": "/api/v1/auth/login",
                        "payload": str(payload),
                        "status": "VULNERABLE",
                        "description": "NoSQL注入绕过认证"
                    })

            except Exception as e:
                logger.debug(f"NoSQL注入测试错误: {e}")

        return vulnerabilities

    def _test_command_injection(self, payloads: List[str]) -> List[Dict[str, Any]]:
        """测试命令注入"""
        vulnerabilities = []

        # 测试可能执行系统命令的端点
        test_endpoints = [
            "/api/v1/system/ping",
            "/api/v1/tools/export",
            "/api/v1/admin/backup"
        ]

        for endpoint in test_endpoints:
            for payload in payloads:
                try:
                    response = requests.post(
                        f"{self.target_url}{endpoint}",
                        json={"command": payload},
                        timeout=5
                    )

                    # 检查是否有命令执行的迹象
                    if any(keyword in response.text.lower() for keyword in
                           ["root:", "uid=", "gid=", "groups=", "/bin/", "/usr/"]):
                        vulnerabilities.append({
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "VULNERABLE",
                            "description": "命令注入执行成功"
                        })

                except Exception as e:
                    logger.debug(f"命令注入测试错误: {e}")

        return vulnerabilities

    def _test_xss(self) -> Dict[str, Any]:
        """测试跨站脚本攻击"""
        logger.info("开始XSS测试...")

        results = {
            "reflected_xss": [],
            "stored_xss": [],
            "dom_xss": []
        }

        # XSS测试载荷
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]

        # 测试反射型XSS
        results["reflected_xss"] = self._test_reflected_xss(xss_payloads)

        # 测试存储型XSS
        results["stored_xss"] = self._test_stored_xss(xss_payloads)

        return results

    def _test_reflected_xss(self, payloads: List[str]) -> List[Dict[str, Any]]:
        """测试反射型XSS"""
        vulnerabilities = []

        # 测试搜索参数
        for payload in payloads:
            try:
                response = requests.get(
                    f"{self.target_url}/api/v1/search",
                    params={"q": payload},
                    timeout=5
                )

                if payload in response.text and "text/html" in response.headers.get("content-type", ""):
                    vulnerabilities.append({
                        "endpoint": "/api/v1/search",
                        "payload": payload,
                        "status": "VULNERABLE",
                        "description": "反射型XSS漏洞"
                    })

            except Exception as e:
                logger.debug(f"反射型XSS测试错误: {e}")

        return vulnerabilities

    def _test_stored_xss(self, payloads: List[str]) -> List[Dict[str, Any]]:
        """测试存储型XSS"""
        vulnerabilities = []

        # 尝试登录获取token
        try:
            login_response = requests.post(
                f"{self.target_url}/api/v1/auth/login",
                json=self.test_users[0],
                timeout=5
            )

            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}

                # 测试用户资料更新
                for payload in payloads:
                    try:
                        # 提交恶意载荷
                        requests.put(
                            f"{self.target_url}/api/v1/auth/profile",
                            json={"bio": payload},
                            headers=headers,
                            timeout=5
                        )

                        # 检查是否被存储
                        profile_response = requests.get(
                            f"{self.target_url}/api/v1/auth/profile",
                            headers=headers,
                            timeout=5
                        )

                        if payload in profile_response.text:
                            vulnerabilities.append({
                                "endpoint": "/api/v1/auth/profile",
                                "payload": payload,
                                "status": "VULNERABLE",
                                "description": "存储型XSS漏洞"
                            })

                    except Exception as e:
                        logger.debug(f"存储型XSS测试错误: {e}")

        except Exception as e:
            logger.debug(f"存储型XSS测试错误: {e}")

        return vulnerabilities

    def _test_csrf(self) -> Dict[str, Any]:
        """测试跨站请求伪造"""
        logger.info("开始CSRF测试...")

        results = {
            "csrf_protection": "UNKNOWN",
            "vulnerable_endpoints": []
        }

        try:
            # 登录获取会话
            login_response = requests.post(
                f"{self.target_url}/api/v1/auth/login",
                json=self.test_users[0],
                timeout=5
            )

            if login_response.status_code == 200:
                token = login_response.json().get("access_token")

                # 测试关键操作是否有CSRF保护
                critical_endpoints = [
                    ("/api/v1/trading/orders", "POST"),
                    ("/api/v1/auth/profile", "PUT"),
                    ("/api/v1/auth/password", "PUT")
                ]

                for endpoint, method in critical_endpoints:
                    # 不带CSRF token的请求
                    headers = {"Authorization": f"Bearer {token}"}

                    try:
                        if method == "POST":
                            response = requests.post(
                                f"{self.target_url}{endpoint}",
                                json={"test": "csrf"},
                                headers=headers,
                                timeout=5
                            )
                        elif method == "PUT":
                            response = requests.put(
                                f"{self.target_url}{endpoint}",
                                json={"test": "csrf"},
                                headers=headers,
                                timeout=5
                            )

                        # 如果请求成功，可能缺少CSRF保护
                        if response.status_code in [200, 201, 204]:
                            results["vulnerable_endpoints"].append({
                                "endpoint": endpoint,
                                "method": method,
                                "status": "VULNERABLE",
                                "description": "缺少CSRF保护"
                            })

                    except Exception as e:
                        logger.debug(f"CSRF测试错误: {e}")

        except Exception as e:
            logger.debug(f"CSRF测试错误: {e}")

        if not results["vulnerable_endpoints"]:
            results["csrf_protection"] = "PROTECTED"
        else:
            results["csrf_protection"] = "VULNERABLE"

        return results

    def _test_security_headers(self) -> Dict[str, Any]:
        """测试安全头"""
        logger.info("开始安全头测试...")

        results = {
            "missing_headers": [],
            "weak_headers": [],
            "secure_headers": []
        }

        # 必需的安全头
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # 任何值都可以
            "Content-Security-Policy": None,
            "Referrer-Policy": None
        }

        try:
            response = requests.get(f"{self.target_url}/", timeout=5)
            headers = response.headers

            for header_name, expected_value in required_headers.items():
                if header_name not in headers:
                    results["missing_headers"].append({
                        "header": header_name,
                        "status": "MISSING",
                        "description": f"缺少安全头: {header_name}"
                    })
                else:
                    header_value = headers[header_name]

                    if expected_value is None:
                        # 只要存在就行
                        results["secure_headers"].append({
                            "header": header_name,
                            "value": header_value,
                            "status": "PRESENT"
                        })
                    elif isinstance(expected_value, list):
                        # 检查是否是允许的值之一
                        if header_value not in expected_value:
                            results["weak_headers"].append({
                                "header": header_name,
                                "value": header_value,
                                "expected": expected_value,
                                "status": "WEAK"
                            })
                        else:
                            results["secure_headers"].append({
                                "header": header_name,
                                "value": header_value,
                                "status": "SECURE"
                            })
                    else:
                        # 检查精确值
                        if header_value != expected_value:
                            results["weak_headers"].append({
                                "header": header_name,
                                "value": header_value,
                                "expected": expected_value,
                                "status": "WEAK"
                            })
                        else:
                            results["secure_headers"].append({
                                "header": header_name,
                                "value": header_value,
                                "status": "SECURE"
                            })

        except Exception as e:
            logger.debug(f"安全头测试错误: {e}")

        return results

    def _test_ssl(self) -> Dict[str, Any]:
        """测试SSL/TLS配置"""
        logger.info("开始SSL/TLS测试...")

        results = {
            "ssl_enabled": False,
            "certificate_valid": False,
            "weak_ciphers": [],
            "protocol_versions": []
        }

        # 如果目标是HTTPS，测试SSL配置
        if self.target_url.startswith("https://"):
            try:
                import ssl
                import socket
                from urllib.parse import urlparse

                parsed_url = urlparse(self.target_url)
                hostname = parsed_url.hostname
                port = parsed_url.port or 443

                # 测试SSL连接
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        results["ssl_enabled"] = True
                        results["certificate_valid"] = True

                        # 获取证书信息
                        cert = ssock.getpeercert()
                        results["certificate_info"] = {
                            "subject": dict(x[0] for x in cert['subject']),
                            "issuer": dict(x[0] for x in cert['issuer']),
                            "version": cert['version'],
                            "notBefore": cert['notBefore'],
                            "notAfter": cert['notAfter']
                        }

                        # 获取协议版本
                        results["protocol_versions"].append(ssock.version())

            except Exception as e:
                logger.debug(f"SSL测试错误: {e}")
                results["ssl_enabled"] = False

        return results

    def _test_api_security(self) -> Dict[str, Any]:
        """测试API安全"""
        logger.info("开始API安全测试...")

        results = {
            "rate_limiting": {},
            "input_validation": [],
            "error_handling": [],
            "api_versioning": {}
        }

        # 测试速率限制
        results["rate_limiting"] = self._test_rate_limiting()

        # 测试输入验证
        results["input_validation"] = self._test_input_validation()

        # 测试错误处理
        results["error_handling"] = self._test_error_handling()

        # 测试API版本控制
        results["api_versioning"] = self._test_api_versioning()

        return results

    def _test_rate_limiting(self) -> Dict[str, Any]:
        """测试速率限制"""
        rate_limit_results = {
            "enabled": False,
            "endpoints_tested": [],
            "vulnerable_endpoints": []
        }

        # 测试登录端点的速率限制
        login_endpoint = f"{self.target_url}/api/v1/auth/login"

        # 快速发送多个请求
        for i in range(20):
            try:
                response = requests.post(
                    login_endpoint,
                    json={"username": "test", "password": "wrong"},
                    timeout=2
                )

                if response.status_code == 429:  # Too Many Requests
                    rate_limit_results["enabled"] = True
                    break

            except Exception as e:
                logger.debug(f"速率限制测试错误: {e}")

        if not rate_limit_results["enabled"]:
            rate_limit_results["vulnerable_endpoints"].append({
                "endpoint": "/api/v1/auth/login",
                "status": "VULNERABLE",
                "description": "登录端点缺少速率限制"
            })

        return rate_limit_results

    def _test_input_validation(self) -> List[Dict[str, Any]]:
        """测试输入验证"""
        vulnerabilities = []

        # 测试超长输入
        long_string = "A" * 10000

        try:
            response = requests.post(
                f"{self.target_url}/api/v1/auth/login",
                json={"username": long_string, "password": long_string},
                timeout=5
            )

            if response.status_code == 500:
                vulnerabilities.append({
                    "endpoint": "/api/v1/auth/login",
                    "issue": "超长输入导致服务器错误",
                    "status": "VULNERABLE"
                })

        except Exception as e:
            logger.debug(f"输入验证测试错误: {e}")

        # 测试特殊字符
        special_chars = ["<>\"'&", "null", "undefined", "NaN"]

        for char in special_chars:
            try:
                response = requests.post(
                    f"{self.target_url}/api/v1/auth/login",
                    json={"username": char, "password": char},
                    timeout=5
                )

                if response.status_code == 500:
                    vulnerabilities.append({
                        "endpoint": "/api/v1/auth/login",
                        "issue": f"特殊字符 '{char}' 导致服务器错误",
                        "status": "VULNERABLE"
                    })

            except Exception as e:
                logger.debug(f"输入验证测试错误: {e}")

        return vulnerabilities

    def _test_error_handling(self) -> List[Dict[str, Any]]:
        """测试错误处理"""
        vulnerabilities = []

        # 测试不存在的端点
        try:
            response = requests.get(f"{self.target_url}/api/v1/nonexistent", timeout=5)

            if "stack trace" in response.text.lower() or "traceback" in response.text.lower():
                vulnerabilities.append({
                    "endpoint": "/api/v1/nonexistent",
                    "issue": "错误响应泄露堆栈跟踪信息",
                    "status": "VULNERABLE"
                })

        except Exception as e:
            logger.debug(f"错误处理测试错误: {e}")

        return vulnerabilities

    def _test_api_versioning(self) -> Dict[str, Any]:
        """测试API版本控制"""
        versioning_results = {
            "versioning_scheme": "UNKNOWN",
            "deprecated_versions": [],
            "version_disclosure": False
        }

        # 测试不同版本的API
        versions = ["v1", "v2", "v3", "1.0", "2.0"]

        for version in versions:
            try:
                response = requests.get(f"{self.target_url}/api/{version}/", timeout=5)

                if response.status_code == 200:
                    versioning_results["versioning_scheme"] = "PATH_BASED"

                    # 检查是否有版本信息泄露
                    if "version" in response.text.lower():
                        versioning_results["version_disclosure"] = True

            except Exception as e:
                logger.debug(f"API版本测试错误: {e}")

        return versioning_results

    def _run_active_scan(self) -> Dict[str, Any]:
        """运行主动扫描"""
        logger.info("开始主动扫描...")

        try:
            # 启动主动扫描
            scan_id = self.zap.ascan.scan(self.target_url)

            # 等待扫描完成
            while int(self.zap.ascan.status(scan_id)) < 100:
                progress = self.zap.ascan.status(scan_id)
                logger.info(f"主动扫描进度: {progress}%")
                time.sleep(5)

            # 获取扫描结果
            alerts = self.zap.core.alerts()

            # 按风险级别分类
            high_risk = [alert for alert in alerts if alert['risk'] == 'High']
            medium_risk = [alert for alert in alerts if alert['risk'] == 'Medium']
            low_risk = [alert for alert in alerts if alert['risk'] == 'Low']
            info_risk = [alert for alert in alerts if alert['risk'] == 'Informational']

            logger.info(f"主动扫描完成，发现 {len(alerts)} 个安全问题")

            return {
                "scan_id": scan_id,
                "total_alerts": len(alerts),
                "high_risk": len(high_risk),
                "medium_risk": len(medium_risk),
                "low_risk": len(low_risk),
                "informational": len(info_risk),
                "alerts": {
                    "high": high_risk[:10],      # 只保存前10个高风险
                    "medium": medium_risk[:10],  # 只保存前10个中风险
                    "low": low_risk[:5],         # 只保存前5个低风险
                    "info": info_risk[:5]        # 只保存前5个信息级别
                }
            }

        except Exception as e:
            logger.error(f"主动扫描错误: {e}")
            return {
                "error": str(e),
                "scan_completed": False
            }

    def _generate_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成扫描摘要"""
        logger.info("生成扫描摘要...")

        summary = {
            "overall_risk": "UNKNOWN",
            "total_vulnerabilities": 0,
            "critical_issues": [],
            "recommendations": [],
            "compliance_status": {}
        }

        # 统计漏洞数量
        vuln_count = 0
        critical_issues = []

        # 认证测试结果
        auth_results = scan_results.get("authentication_tests", {})
        if auth_results.get("weak_passwords"):
            vuln_count += len(auth_results["weak_passwords"])
            critical_issues.append("发现弱密码")

        if auth_results.get("brute_force_protection", {}).get("status") == "VULNERABLE":
            vuln_count += 1
            critical_issues.append("缺少暴力破解保护")

        # 授权测试结果
        authz_results = scan_results.get("authorization_tests", {})
        if authz_results.get("privilege_escalation"):
            vuln_count += len(authz_results["privilege_escalation"])
            critical_issues.append("存在权限提升漏洞")

        if authz_results.get("idor"):
            vuln_count += len(authz_results["idor"])
            critical_issues.append("存在不安全的直接对象引用")

        # 注入攻击结果
        injection_results = scan_results.get("injection_tests", {})
        for injection_type, vulnerabilities in injection_results.items():
            if vulnerabilities:
                vuln_count += len(vulnerabilities)
                critical_issues.append(f"存在{injection_type}漏洞")

        # XSS测试结果
        xss_results = scan_results.get("xss_tests", {})
        for xss_type, vulnerabilities in xss_results.items():
            if vulnerabilities:
                vuln_count += len(vulnerabilities)
                critical_issues.append(f"存在{xss_type}漏洞")

        # CSRF测试结果
        csrf_results = scan_results.get("csrf_tests", {})
        if csrf_results.get("csrf_protection") == "VULNERABLE":
            vuln_count += len(csrf_results.get("vulnerable_endpoints", []))
            critical_issues.append("存在CSRF漏洞")

        # 安全头测试结果
        headers_results = scan_results.get("security_headers_tests", {})
        if headers_results.get("missing_headers"):
            vuln_count += len(headers_results["missing_headers"])

        # API安全测试结果
        api_results = scan_results.get("api_security_tests", {})
        if api_results.get("rate_limiting", {}).get("vulnerable_endpoints"):
            vuln_count += len(api_results["rate_limiting"]["vulnerable_endpoints"])
            critical_issues.append("API缺少速率限制")

        # 主动扫描结果
        active_scan = scan_results.get("active_scan_results", {})
        if active_scan.get("high_risk", 0) > 0:
            vuln_count += active_scan["high_risk"]
            critical_issues.append(f"发现{active_scan['high_risk']}个高风险漏洞")

        summary["total_vulnerabilities"] = vuln_count
        summary["critical_issues"] = critical_issues

        # 确定整体风险级别
        if vuln_count == 0:
            summary["overall_risk"] = "LOW"
        elif vuln_count <= 5:
            summary["overall_risk"] = "MEDIUM"
        else:
            summary["overall_risk"] = "HIGH"

        # 生成建议
        recommendations = []

        if critical_issues:
            recommendations.append("立即修复所有关键安全漏洞")

        if headers_results.get("missing_headers"):
            recommendations.append("添加缺失的安全头")

        if not scan_results.get("ssl_tests", {}).get("ssl_enabled"):
            recommendations.append("启用HTTPS加密")

        if api_results.get("rate_limiting", {}).get("vulnerable_endpoints"):
            recommendations.append("为所有API端点实施速率限制")

        recommendations.extend([
            "定期进行安全扫描",
            "实施安全代码审查",
            "建立安全监控和告警机制",
            "对开发团队进行安全培训"
        ])

        summary["recommendations"] = recommendations

        # 合规状态检查
        compliance = {
            "owasp_top10": self._check_owasp_compliance(scan_results),
            "security_headers": len(headers_results.get("missing_headers", [])) == 0,
            "authentication": len(auth_results.get("weak_passwords", [])) == 0,
            "authorization": len(authz_results.get("privilege_escalation", [])) == 0
        }

        summary["compliance_status"] = compliance

        return summary

    def _check_owasp_compliance(self, scan_results: Dict[str, Any]) -> Dict[str, bool]:
        """检查OWASP Top 10合规性"""
        owasp_compliance = {
            "A01_Broken_Access_Control": True,
            "A02_Cryptographic_Failures": True,
            "A03_Injection": True,
            "A04_Insecure_Design": True,
            "A05_Security_Misconfiguration": True,
            "A06_Vulnerable_Components": True,
            "A07_Identification_Authentication_Failures": True,
            "A08_Software_Data_Integrity_Failures": True,
            "A09_Security_Logging_Monitoring_Failures": True,
            "A10_Server_Side_Request_Forgery": True
        }

        # A01: Broken Access Control
        authz_results = scan_results.get("authorization_tests", {})
        if (authz_results.get("privilege_escalation") or
            authz_results.get("idor") or
            authz_results.get("missing_authorization")):
            owasp_compliance["A01_Broken_Access_Control"] = False

        # A03: Injection
        injection_results = scan_results.get("injection_tests", {})
        if any(injection_results.values()):
            owasp_compliance["A03_Injection"] = False

        # A05: Security Misconfiguration
        headers_results = scan_results.get("security_headers_tests", {})
        if headers_results.get("missing_headers"):
            owasp_compliance["A05_Security_Misconfiguration"] = False

        # A07: Identification and Authentication Failures
        auth_results = scan_results.get("authentication_tests", {})
        if (auth_results.get("weak_passwords") or
            auth_results.get("brute_force_protection", {}).get("status") == "VULNERABLE"):
            owasp_compliance["A07_Identification_Authentication_Failures"] = False

        return owasp_compliance


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="量化交易平台安全扫描")
    parser.add_argument("--target", default="http://localhost:8000", help="目标URL")
    parser.add_argument("--output", default="security_scan_report.json", help="输出文件")
    parser.add_argument("--zap-proxy", default="http://127.0.0.1:8080", help="ZAP代理地址")

    args = parser.parse_args()

    # 创建扫描器
    scanner = SecurityScanner(args.target, args.zap_proxy)

    # 开始扫描
    results = scanner.start_scan()

    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"扫描完成，结果已保存到 {args.output}")

    # 打印摘要
    summary = results.get("summary", {})
    print(f"\n=== 安全扫描摘要 ===")
    print(f"整体风险级别: {summary.get('overall_risk', 'UNKNOWN')}")
    print(f"发现漏洞总数: {summary.get('total_vulnerabilities', 0)}")
    print(f"关键问题: {len(summary.get('critical_issues', []))}")

    if summary.get('critical_issues'):
        print("\n关键安全问题:")
        for issue in summary['critical_issues']:
            print(f"  - {issue}")


if __name__ == "__main__":
    main()
